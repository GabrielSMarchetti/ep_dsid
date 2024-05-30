import socket
import threading
from src.messages import MessageBuilder, MessageDecoder, OperationType, MessageArguments
from src.commands import CommandFactory, ICommand, CommandType, CommandMode


class NodeServer:
    def __init__(self, address, port, neighbours, key_value, should_run_flag, message_builder: MessageBuilder) -> None:
        self.address = address
        self.port = port
        self.origin = f"{self.address}:{self.port}"
        self.neighbours = []
        self.message_builder = message_builder
        self.__initialize_neighbours(neighbours)
        self.key_value = {}
        self.__initialize_key_val(key_value)
        self.flooding_messages_seen = {}
        self.bp_search_info = {}
        self.stats_counter = {
            CommandMode.FL.value: 0,
            CommandMode.RW.value: 0,
            CommandMode.BP.value: 0
        }
        self.stats_mean = {
            CommandMode.FL.value: [0, 0],
            CommandMode.RW.value: [0, 0],
            CommandMode.BP.value: [0, 0]
        }
        self.should_run_flag = should_run_flag
        pass

    def __initialize_key_val(self, key_value):
        if key_value == '':
            return
        with open(key_value, 'r') as file:
            for line in file.readlines():
                key, value = line.strip().split(' ')
                self.key_value[key] = value

    def __initialize_neighbours(self, neighbours):
        with open(neighbours, 'r') as file:
            neighbours_adresses = [x.strip() for x in file.readlines()]
        for neighbour in neighbours_adresses:
            message = (self.message_builder
                       .build_operation(OperationType.HELLO)
                       .build_origin(self.origin)
                       .get_message())
            command: ICommand = CommandFactory.create_command(
                CommandType.HELLO)
            command.execute_as_sender(self, message, neighbour)
            if command.success:
                self.neighbours.append(neighbour)
        self.message_builder.restart_seq_count()

    def execute_client_command(self, command: ICommand, arguments: dict, target=None):
        message = (self.message_builder
                   .build_origin(self.origin)
                   .build_operation(OperationType[command.command])
                   .build_arguments(arguments)
                   .get_message())
        result = command.execute_as_sender(self, message, target)
        if command.success and command.command == CommandType.SEARCH.value:
            print(f'Valor encontrado: {result}')

    def initialize_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1)
        self.socket.bind((self.address, int(self.port)))
        self.socket.listen()
        self.running_threads = []
        while self.should_run_flag:
            try:
                conn, address = self.socket.accept()
                request_thread = threading.Thread(target=self.handle_request,
                                                  args=(conn,))
                request_thread.start()
                self.running_threads.append(request_thread)
            except TimeoutError:
                continue
        for thread in self.running_threads:
            if thread.is_alive():
                thread.join()
        self.socket.close()

    def handle_request(self, conn: socket.socket):
        data = conn.recv(1024)
        if not data:
            return
        self.handle_received_message(data, conn)
        conn.close()

    def handle_received_message(self, message, conn: socket.socket):
        decoded_message = MessageDecoder.decode(message)
        operation = decoded_message['OPERATION']
        message = (self.message_builder
                   .build_arguments(decoded_message['ARGUMENTS'], operation == OperationType.VAL.value)
                   .build_operation(OperationType[operation])
                   .build_origin(decoded_message['ORIGIN'])
                   .build_seq_number(decoded_message['SEQNO'])
                   .build_ttl(decoded_message['TTL'])
                   .get_message(False))
        print(f'Mensagem recebida: {message}')
        command = CommandFactory.create_command(
            CommandType[operation], CommandMode[message.get_argument_val(MessageArguments.MODE)])
        result = command.execute_as_receiver(self, message)
        if operation == OperationType.SEARCH.value and command.success:
            val_command = CommandFactory.create_command(CommandType.VAL)
            arguments = {
                MessageArguments.MODE.value: message.get_argument_val(MessageArguments.MODE),
                MessageArguments.KEY.value: message.get_argument_val(MessageArguments.KEY),
                MessageArguments.VALUE.value: result,
                MessageArguments.HOP_COUNT.value: message.get_argument_val(
                    MessageArguments.HOP_COUNT)
            }
            val_message = (self.message_builder
                           .build_origin(self.origin)
                           .build_operation(OperationType.VAL)
                           .build_arguments(arguments, 1)
                           .get_message())
            val_command.execute_as_sender(self, val_message, message.origin)

    def list_neighbours(self):
        for index, neighbour in enumerate(self.neighbours):
            print(f"\t[{index}] {neighbour.replace(':', ' ')}")

    def increment_stats_counter(self, mode: CommandMode):
        self.stats_counter[mode.value] += 1

    def update_stats_mean(self, mode: CommandMode, val):
        self.stats_mean[mode.value][0] += int(val)
        self.stats_mean[mode.value][1] += 1

    @classmethod
    def print_sending_message(cls, message, target):
        print(f'Encaminhando mensagem {str(message)} para {target}')

    @classmethod
    def print_message_successfully_sent(cls, message):
        print(f'\tEnvio feito com sucesso: {str(message)}')

    def send_message_to_target(self, message, target):
        self.print_sending_message(message, target)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address, port = target.split(':')
        s.connect((address, int(port)))
        s.send(bytes(str(message).encode()))
        s.close()
        self.print_message_successfully_sent(message)

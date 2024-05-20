import socket
import threading
from src.messages import MessageFactory, MessageDecoder
from src.commands import CommandFactory, ICommand


class NodeServer:
    def __init__(self, address, port, neighbours, key_value, should_run_flag, message_factory: MessageFactory) -> None:
        self.address = address
        self.port = int(port)
        self.neighbours = []
        self.message_factory = message_factory
        self.__initialize_neighbours(neighbours)
        # self.key_value = self.__extract_key_value()
        self.should_run_flag = should_run_flag
        self.messages_seen = {}
        pass

    def __initialize_neighbours(self, neighbours):
        with open(neighbours, 'r') as file:
            neighbours_adresses = [x.strip() for x in file.readlines()]
        for neighbour in neighbours_adresses:
            message = self.message_factory.create_origin_message('HELLO')
            command: ICommand = CommandFactory.create_command('HELLO')
            command.execute_as_sender(message, neighbour)
            if command.success:
                self.neighbours.append(neighbour)
        self.message_factory.restart_seq_count()

    def execute_client_command(self, command: ICommand, target):
        message = self.message_factory.create_origin_message(command.command)
        command.execute_as_sender(message, target)

    def initialize_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1)
        self.socket.bind((self.address, self.port))
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

    def handle_received_message(self, message, conn):
        decoded_message = MessageDecoder.decode(message)
        operation = decoded_message['OPERATION']
        message = self.message_factory.create_received_message(
            decoded_message['ORIGIN'],
            decoded_message['SEQNO'],
            decoded_message['TTL'],
            decoded_message['OPERATION'],
            decoded_message['ARGUMENTS']
        )
        print(f'Mensagem recebida: {message}')
        command = CommandFactory.create_command(operation)
        command.execute_as_receiver(self, message)

    def list_neighbours(self):
        for index, neighbour in enumerate(self.neighbours):
            print(f"\t[{index}] {neighbour.replace(':', ' ')}")

from src.messages import Message, MessageArguments, OperationType
import random
from enum import Enum
import copy


class CommandType(Enum):
    HELLO = "HELLO"
    BYE = "BYE"
    SEARCH = "SEARCH"
    VAL = "VAL"


class CommandMode(Enum):
    DEFAULT = ''
    FL = 'FL'
    RW = 'RW'
    BP = 'BP'


class ICommand:

    def __init__(self) -> None:
        self.success = True
        self.command = ''
        pass

    def execute_as_sender(self, node, message: Message, target=None):
        raise NotImplementedError

    def execute_as_receiver(self, node, message: Message, target=None):
        raise NotImplementedError


class CommandFactory:
    @classmethod
    def create_command(cls, command_type: CommandType, command_mode: CommandMode = CommandMode.DEFAULT) -> ICommand:
        mode_val = command_mode.value
        if command_type == CommandType.HELLO:
            return HelloCommand()
        if command_type == CommandType.BYE:
            return ByeCommand()
        if command_type == CommandType.VAL:
            return ValCommand(mode_val)
        if command_type == CommandType.SEARCH:
            return SearchCommand(mode_val)
        raise NotImplementedError


class HelloCommand(ICommand):

    def __init__(self) -> None:
        super().__init__()
        self.command = 'HELLO'

    def execute_as_sender(self, node, message: Message, target):
        try:
            node.send_message_to_target(message, target)
        except:
            print('Erro ao conectar!')
            self.success = False

    def execute_as_receiver(self, node, message: Message, target=None):
        origin = message.origin
        if origin in node.neighbours:
            print(f'\tVizinho ja esta na tabela: {origin}')
        else:
            print(f'\tAdicionando vizinho na tabela: {origin}')
            node.neighbours.append(origin)


class ByeCommand(ICommand):
    def __init__(self) -> None:
        super().__init__()
        self.command = 'BYE'

    def execute_as_sender(self, node, message: Message, target):
        try:
            node.send_message_to_target(message, target)
        except:
            print('Erro ao conectar!')
            self.success = False

    def execute_as_receiver(self, node, message: Message, target=None):
        origin = message.origin
        node.neighbours.remove(origin)
        print(f'Removendo vizinho da tabela {origin}')


class ValCommand(ICommand):
    def __init__(self, mode) -> None:
        super().__init__()
        self.mode = mode
        self.command = 'VAL'

    def execute_as_sender(self, node, message: Message, target=None):
        node.send_message_to_target(message, target)

    def execute_as_receiver(self, node, message: Message, target=None):
        print('\tValor encontrado!')
        key = message.get_argument_val(MessageArguments.KEY)
        value = message.get_argument_val(MessageArguments.VALUE)
        print(f'\t\tchave: {key} valor: {value}')
        node.update_stats_mean(CommandMode[message.get_argument_val(MessageArguments.MODE)],
                               message.get_argument_val(MessageArguments.HOP_COUNT))


class SearchCommand(ICommand):

    def __init__(self, mode) -> None:
        super().__init__()
        self.mode = mode
        self.command = 'SEARCH'

    def execute_as_sender(self, node, message: Message, target=None):
        search_key = message.get_argument_val(MessageArguments.KEY)
        if search_key in node.key_value.keys():
            print('\tChave encontrada!')
            return node.key_value[search_key]
        self.success = False

        if self.mode == CommandMode.FL.value:
            for neighbour in node.neighbours:
                node.send_message_to_target(message, neighbour)
            return

        if self.mode == CommandMode.RW.value:
            if not len(node.neighbours) - 1 >= 0:
                return
            next_neighbour_index = random.randint(0, len(node.neighbours) - 1)
            node.send_message_to_target(
                message, node.neighbours[next_neighbour_index])
            return

        if self.mode == CommandMode.BP.value:
            bp_key = f"{message.origin}:{message.seq_number}"
            node.bp_search_info[bp_key] = {}
            node.bp_search_info[bp_key]['mother'] = node.origin
            node.bp_search_info[bp_key]['neighbours'] = node.neighbours.copy()
            if not len(node.neighbours) - 1 >= 0:
                return
            next_neighbour_index = random.randint(0, len(node.neighbours) - 1)
            active_neighbour = node.neighbours[next_neighbour_index]
            node.bp_search_info[bp_key]['neighbours'].remove(active_neighbour)
            node.bp_search_info[bp_key]['active'] = active_neighbour
            node.send_message_to_target(
                message, active_neighbour)
            return

    def execute_as_receiver(self, node, message: Message, target=None):

        if self.mode == CommandMode.FL.value:
            return self.fl_search_receiver_procedure(node, message)

        if self.mode == CommandMode.RW.value:
            return self.rw_search_receiver_procedure(node, message)

        if self.mode == CommandMode.BP.value:
            return self.bp_search_receiver_procedure(node, message)

    def fl_search_receiver_procedure(self, node, message):
        node.increment_stats_counter(CommandMode.FL)
        if self.validate_message_seen(node, message):
            self.success = False
            return
        node.flooding_messages_seen[message.origin].append(
            message.seq_number)
        search_key = message.get_argument_val(MessageArguments.KEY)
        if search_key in node.key_value.keys():
            print('\tChave encontrada!')
            return node.key_value[search_key]
        self.success = False
        node_neighbours = node.neighbours.copy()
        self.remove_last_hop_port(node_neighbours, message.get_argument_val(
            MessageArguments.LAST_HOP_PORT))
        if not node_neighbours:
            return
        new_message = self.get_updated_message(node, message)
        if not new_message.ttl > 0:
            return
        for neighbour in node_neighbours:
            node.send_message_to_target(new_message, neighbour)
        return

    def rw_search_receiver_procedure(self, node, message):
        node.increment_stats_counter(CommandMode.RW)
        search_key = message.get_argument_val(MessageArguments.KEY)
        if search_key in node.key_value.keys():
            print('\tChave encontrada!')
            return node.key_value[search_key]
        self.success = False
        new_message = self.get_updated_message(node, message)
        if not new_message.ttl > 0:
            return
        node_neighbours = node.neighbours.copy()
        if len(node_neighbours) == 1:
            node.send_message_to_target(new_message, node_neighbours[0])
            return
        self.remove_last_hop_port(node_neighbours, message.get_argument_val(
            MessageArguments.LAST_HOP_PORT
        ))
        next_neighbour_index = random.randint(0, len(node_neighbours) - 1)
        node.send_message_to_target(
            new_message, node_neighbours[next_neighbour_index])
        return

    def bp_search_receiver_procedure(self, node, message: Message):
        node.increment_stats_counter(CommandMode.BP)
        search_key = message.get_argument_val(MessageArguments.KEY)
        if search_key in node.key_value.keys():
            print('\tChave encontrada!')
            return node.key_value[search_key]
        self.success = False
        new_message = self.get_updated_message(node, message)
        if not new_message.ttl > 0:
            return
        bp_key = f"{message.origin}:{message.seq_number}"
        if bp_key not in node.bp_search_info.keys():
            self.initialize_bp_receiver_dict(node, message, bp_key)

        if self.has_bp_ended(node, message, bp_key):
            print(
                f"BP: Nao foi possivel localizar a chave {message.get_argument_val(MessageArguments.KEY)}")
            return

        if self.bp_is_cycle(node, message, bp_key):
            print("BP: ciclo detectado, devolvendo a mensagem...")
            sender = f"{node.address}:{message.get_argument_val(MessageArguments.LAST_HOP_PORT)}"
            if sender in node.bp_search_info[bp_key]['neighbours']:
                node.bp_search_info[bp_key]['neighbours'].remove(sender)
            node.send_message_to_target(
                new_message, f"{node.address}:{message.get_argument_val(MessageArguments.LAST_HOP_PORT)}")
            return

        if self.bp_is_neighbours_empty(node, bp_key):
            print("BP: nenhum vizinho encontrou a chave, retrocedendo...")
            node.send_message_to_target(
                new_message, node.bp_search_info[bp_key]['mother'])
            return

        next_active_index = random.randint(
            0, len(node.bp_search_info[bp_key]['neighbours']) - 1)
        active_neighbour = node.bp_search_info[bp_key]['neighbours'][next_active_index]
        node.bp_search_info[bp_key]['neighbours'].remove(active_neighbour)
        node.bp_search_info[bp_key]['active'] = active_neighbour
        node.send_message_to_target(new_message, active_neighbour)
        return

    def has_bp_ended(self, node, message: Message, bp_key):
        is_node_own_mother = node.bp_search_info[bp_key]['mother'] == node.origin
        is_neighbours_empty = self.bp_is_neighbours_empty(
            node, bp_key)
        is_message_from_active = (node.bp_search_info[bp_key]['active']
                                  == f"{node.address}:{message.get_argument_val(MessageArguments.LAST_HOP_PORT)}")
        return is_node_own_mother and is_neighbours_empty and is_message_from_active

    def bp_is_cycle(self, node, message: Message, bp_key):
        sender = f"{node.address}:{message.get_argument_val(MessageArguments.LAST_HOP_PORT)}"
        active_node = node.bp_search_info[bp_key]['active']
        return active_node not in ['', sender]

    def bp_is_neighbours_empty(self, node, bp_key):
        return len(node.bp_search_info[bp_key]['neighbours']) == 0

    def initialize_bp_receiver_dict(self, node, message, bp_key):
        node.bp_search_info[bp_key] = {}
        node.bp_search_info[bp_key][
            'mother'] = f"{node.address}:{message.get_argument_val(MessageArguments.LAST_HOP_PORT)}"
        node.bp_search_info[bp_key]['neighbours'] = node.neighbours.copy()
        node.bp_search_info[bp_key]['neighbours'].remove(
            node.bp_search_info[bp_key]['mother'])
        node.bp_search_info[bp_key]['active'] = ''

    def remove_last_hop_port(self, neighbours_list: list, last_hop_port):
        for neighbour in neighbours_list:
            if neighbour.split(':')[1] == last_hop_port:
                neighbours_list.remove(neighbour)
                break

    def get_updated_message(self, node, old_message: Message, new_operation_type: OperationType = None):
        new_message = copy.deepcopy(old_message)
        new_message.set_argument_val(
            MessageArguments.LAST_HOP_PORT, node.port)
        new_message.set_argument_val(MessageArguments.HOP_COUNT,
                                     str(int(new_message.get_argument_val(MessageArguments.HOP_COUNT)) + 1))
        (node.message_builder
         .build_origin(new_message.origin)
         .build_ttl(new_message.ttl - 1)
         .build_seq_number(new_message.seq_number)
         .build_arguments(new_message.arguments))
        if new_operation_type:
            node.message_builder.build_operation(new_operation_type)
        else:
            node.message_builder.build_operation(
                OperationType[new_message.operation])
        new_message = node.message_builder.get_message(False)
        return new_message

    def validate_message_seen(self, node, message):
        if message.origin in node.flooding_messages_seen.keys():
            if message.seq_number in node.flooding_messages_seen[message.origin]:
                return True
            return False
        node.flooding_messages_seen[message.origin] = []
        return False

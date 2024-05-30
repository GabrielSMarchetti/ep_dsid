from src.node import NodeServer
from src.commands import CommandFactory, CommandType, CommandMode
from src.messages import MessageArguments
import sys


class Client:
    def __init__(self, server: NodeServer) -> None:
        self.server = server
        pass

    def run(self):
        display_message = """
Escolha o comando
    [0] Listar vizinhos
    [1] HELLO
    [2] SEARCH (flooding)
    [3] SEARCH (random walk)
    [4] SEARCH (busca em profundidade)
    [5] Estatisticas
    [6] Alterar valor padrao de TTL
    [9] Sair    
        """
        while True:
            command = input(display_message)
            self.send_command(command)

    def send_command(self, command):
        match command:

            case '0':
                self.server.list_neighbours()

            case '1':
                print('Escolha o vizinho:')
                print(
                    f'\tHa {str(len(self.server.neighbours))} vizinhos na tabela:')
                self.server.list_neighbours()
                if len(self.server.neighbours) > 0:
                    neighbour_index = int(input())
                    command = CommandFactory.create_command(CommandType.HELLO)
                    self.server.execute_client_command(
                        command, {}, self.server.neighbours[neighbour_index])

            case '2':
                key = input('Digite a chave a ser buscada\n')
                command_mode = CommandMode.FL
                self.start_search_command(command_mode, key)

            case '3':
                key = input('Digite a chave a ser buscada\n')
                command_mode = CommandMode.RW
                self.start_search_command(command_mode, key)

            case '4':
                key = input('Digite a chave a ser buscada\n')
                command_mode = CommandMode.BP
                self.start_search_command(command_mode, key)

            case '5':
                print('Estatisticas')
                print(
                    f'\tTotal de mensagens de flooding vistas: {self.server.stats_counter[CommandMode.FL.value]}')
                print(
                    f'\tTotal de mensagens de busca em profundidade vistas: {self.server.stats_counter[CommandMode.RW.value]}')
                print(
                    f'\tTotal de mensagens de busca em profundidade vistas: {self.server.stats_counter[CommandMode.BP.value]}')
                fl_mean_list = self.server.stats_mean[CommandMode.FL.value]
                fl_mean_val = fl_mean_list[0] / \
                    fl_mean_list[1] if fl_mean_list[1] != 0 else 0
                print(
                    f'\tMedia de saltos ate encontrar destino por flooding: {fl_mean_val}')
                rw_mean_list = self.server.stats_mean[CommandMode.RW.value]
                rw_mean_val = rw_mean_list[0] / \
                    rw_mean_list[1] if rw_mean_list[1] != 0 else 0
                print(
                    f'\tMedia de saltos ate encontrar destino por random walk: {rw_mean_val}')
                bp_mean_list = self.server.stats_mean[CommandMode.BP.value]
                bp_mean_val = bp_mean_list[0] / \
                    bp_mean_list[1] if bp_mean_list[1] != 0 else 0
                print(
                    f'\tMedia de saltos ate encontrar destino por busca em profundidade: {bp_mean_val}')

            case '6':
                new_ttl = input('Digite novo valor de TTL\n')
                self.server.message_builder.set_ttl(int(new_ttl))

            case '9':
                command = CommandFactory.create_command(CommandType.BYE)
                print('Saindo...')
                for neighbour in self.server.neighbours:
                    self.server.execute_client_command(
                        command, {}, neighbour)
                self.server.should_run_flag = False
                sys.exit()

    def start_search_command(self, command_mode: CommandMode, key):
        arguments = {
            MessageArguments.MODE.value: command_mode.value,
            MessageArguments.LAST_HOP_PORT.value: str(self.server.port),
            MessageArguments.KEY.value: key,
            MessageArguments.HOP_COUNT.value: 1
        }
        command = CommandFactory.create_command(CommandType.SEARCH,
                                                command_mode)
        self.server.execute_client_command(command, arguments)

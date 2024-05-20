from src.node import NodeServer
from src.commands import CommandFactory
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
                    command = CommandFactory.create_command('HELLO')
                    self.server.execute_client_command(
                        command, self.server.neighbours[neighbour_index])

            case '6':
                new_ttl = input('Digite novo valor de TTL')
                self.server.message_factory.set_ttl(int(new_ttl))

            case '9':
                command = CommandFactory.create_command('BYE')
                print('Saindo...')
                for neighbour in self.server.neighbours:
                    self.server.execute_client_command(command,
                                                       neighbour)
                    self.server.should_run_flag = False
                sys.exit()

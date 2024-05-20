from src.messages import IMessage, HelloMessage
import socket


class ICommand:

    def __init__(self) -> None:
        self.success = True
        self.command = ''
        pass

    def execute_as_sender(self, message: IMessage, target):
        raise NotImplementedError

    def execute_as_receiver(self, node, message: IMessage, target=None):
        raise NotImplementedError

    @classmethod
    def print_sending_message(cls, message, target):
        print(f'Encaminhando mensagem {str(message)} para {target}')

    @classmethod
    def print_message_successfully_sent(cls, message):
        print(f'\tEnvio feito com sucesso: {str(message)}')


class CommandFactory:
    @classmethod
    def create_command(cls, command_type) -> ICommand:
        if command_type == "HELLO":
            return HelloCommand()
        if command_type == "BYE":
            return ByeCommand()
        raise NotImplementedError


class HelloCommand(ICommand):

    def __init__(self) -> None:
        super().__init__()
        self.command = 'HELLO'

    def execute_as_sender(self, message: HelloMessage, target):
        ICommand.print_sending_message(message, target)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            address, port = target.split(':')
            s.connect((address, int(port)))
            s.send(bytes(str(message).encode()))
            s.close()
            ICommand.print_message_successfully_sent(message)
        except:
            print('Erro ao conectar!')
            self.success = False

    def execute_as_receiver(self, node, message: IMessage, target=None):
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

    def execute_as_sender(self, message: IMessage, target):
        ICommand.print_sending_message(message, target)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            address, port = target.split(':')
            s.connect((address, int(port)))
            s.send(bytes(str(message).encode()))
            s.close()
            ICommand.print_message_successfully_sent(message)
        except:
            print('Erro ao conectar!')
            self.success = False

    def execute_as_receiver(self, node, message: IMessage, target=None):
        origin = message.origin
        node.neighbours.remove(origin)
        print(f'Removendo vizinho da tabela {origin}')

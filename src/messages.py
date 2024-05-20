class MessageDecoder:
    @classmethod
    def decode(cls, message: bytes):
        message_args = message.decode().replace('"', '').split(' ')
        message_properties = {
            'ORIGIN': message_args[0],
            'SEQNO': message_args[1],
            'TTL': message_args[2],
            'OPERATION': message_args[3],
        }
        message_properties['ARGUMENTS'] = ''
        if len(message_args) > 4:
            message_properties['ARGUMENTS'] = message_args[4:]
        return message_properties


class MessageFactory:
    def __init__(self, origin, seq_number=0, ttl=100, arguments=[]) -> None:
        self.origin = origin
        self.seq_number = seq_number
        self.ttl = ttl
        self.arguments = arguments
        pass

    def set_ttl(self, ttl):
        self.ttl = ttl

    def create_origin_message(self, message_type):
        self.seq_number += 1
        if message_type == 'HELLO':
            return HelloMessage(self.origin, self.seq_number, 1, self.arguments)
        if message_type == 'SEARCH':
            return SearchMessage(self.origin, self.seq_number, self.ttl, self.arguments)
        if message_type == 'VAL':
            return ValMessage(self.origin, self.seq_number, self.ttl, self.arguments)
        if message_type == 'BYE':
            return ByeMessage(self.origin, self.seq_number, self.ttl, self.arguments)
        raise NotImplementedError

    def create_received_message(self, origin, seq_number, ttl, operation, arguments):
        if operation == 'SEARCH':
            return SearchMessage(origin, seq_number, ttl, arguments)
        if operation == 'VAL':
            return ValMessage(origin, seq_number, ttl, arguments)
        if operation == 'HELLO':
            return HelloMessage(origin, seq_number, ttl, arguments)
        if operation == 'BYE':
            return ByeMessage(origin, seq_number, ttl, arguments)
        raise NotImplementedError

    def restart_seq_count(self):
        self.seq_number = 0


class IMessage:
    def __init__(self, origin, seq_number, ttl, arguments) -> None:
        self.origin = origin
        self.seq_number = seq_number
        self.ttl = ttl
        self.operation = ''
        self.arguments = arguments
        self._set_message_arguments(arguments)

    def _set_message_arguments(self, arguments: str):
        raise NotImplementedError

    def get_argument_val(self, argument_key):
        raise NotImplementedError

    def __str__(self) -> str:
        if len(self.arguments) > 0:
            return f'"{self.origin} {str(self.seq_number)} {str(self.ttl)} {self.operation} {" ".join(self.arguments)}"'
        return f'"{self.origin} {str(self.seq_number)} {str(self.ttl)} {self.operation}"'


class HelloMessage(IMessage):
    def __init__(self, origin, seq_number, ttl, arguments) -> None:
        super().__init__(origin, seq_number, ttl, arguments)
        self.operation = 'HELLO'

    def _set_message_arguments(self, arguments: str):
        return

    def get_argument_val(self, argument_key):
        print('HELLO Message does not have arguments')


class ByeMessage(IMessage):
    def __init__(self, origin, seq_number, ttl, arguments) -> None:
        super().__init__(origin, seq_number, ttl, arguments)
        self.operation = 'BYE'

    def _set_message_arguments(self, arguments: str):
        return

    def get_argument_val(self, argument_key):
        print('BYE message does not have arguments')


class SearchMessage(IMessage):
    def __init__(self, origin, seq_number, ttl, arguments) -> None:
        super().__init__(origin, seq_number, ttl, arguments)
        self.operation = 'SEARCH'

    def _set_message_arguments(self, arguments: str):
        args = arguments.split(' ')
        self.arguments = {
            'MODE': args[0],
            'LAST_HOP_PORT': args[1],
            'KEY': args[2],
            'HOP_COUNT': args[3]
        }

    def get_argument_val(self, argument_key):
        if not argument_key in self.arguments.keys():
            print(f'{argument_key} not in message arguments')
            raise KeyError
        return self.arguments[argument_key]


class ValMessage(IMessage):
    def __init__(self, origin, seq_number, ttl, arguments) -> None:
        super().__init__(origin, seq_number, ttl, arguments)
        self.operation = 'VAL'

    def _set_message_arguments(self, arguments: str):
        args = arguments.split(' ')
        self.arguments = {
            'MODE': args[0],
            'LAST_HOP_PORT': args[1],
            'KEY': args[2],
            'HOP_COUNT': args[3]
        }

    def get_argument_val(self, argument_key):
        if not argument_key in self.arguments.keys():
            print(f'{argument_key} not in message arguments')
            raise KeyError
        return self.arguments[argument_key]

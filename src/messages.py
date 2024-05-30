from enum import Enum


class OperationType(Enum):
    HELLO = "HELLO"
    SEARCH = "SEARCH"
    VAL = "VAL"
    BYE = "BYE"


class MessageArguments(Enum):
    MODE = 'MODE'
    LAST_HOP_PORT = 'LAST_HOP_PORT'
    KEY = 'KEY'
    HOP_COUNT = 'HOP_COUNT'
    VALUE = 'VALUE'


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
        message_properties['ARGUMENTS'] = ['DEFAULT', '', '', '']
        if len(message_args) > 4:
            message_properties['ARGUMENTS'] = message_args[4:]
        return message_properties


class MessageBuilder:
    def __init__(self) -> None:
        self.seq_number = 1
        self.ttl = 100
        self.__initialize_new_message()
        pass

    def __initialize_new_message(self):
        self.current_message = UnfinishedMessage(
            seq_number=self.seq_number, ttl=self.ttl)

    def set_ttl(self, ttl):
        self.ttl = ttl
        self.build_ttl(ttl)

    def restart_seq_count(self):
        self.seq_number = 1
        self.build_seq_number(self.seq_number)

    def build_ttl(self, ttl):
        self.current_message.ttl = int(ttl)
        return self

    def build_seq_number(self, seq_number):
        self.current_message.seq_number = int(seq_number)
        return self

    def build_origin(self, origin):
        self.current_message.origin = origin
        return self

    def build_operation(self, operation_type: OperationType):
        self.current_message.operation = operation_type.value
        return self

    def build_arguments(self, arguments: list | dict, is_val_message=0):
        if isinstance(arguments, dict):
            self.current_message.arguments = arguments
            return self
        if len(arguments) == 0:
            self.current_message.arguments = ''
            return self
        if len(arguments) != 4:
            print("Arguments list may have more/less arguments than needed")
            return self
        if not is_val_message:
            self.current_message.arguments = {
                MessageArguments.MODE.value: arguments[0],
                MessageArguments.LAST_HOP_PORT.value: arguments[1],
                MessageArguments.KEY.value: arguments[2],
                MessageArguments.HOP_COUNT.value: arguments[3]
            }
        else:
            self.current_message.arguments = {
                MessageArguments.MODE.value: arguments[0],
                MessageArguments.KEY.value: arguments[1],
                MessageArguments.VALUE.value: arguments[2],
                MessageArguments.HOP_COUNT.value: arguments[3]
            }
        return self

    def get_message(self, increment_seq_number=True):
        if not self.current_message.check_for_finished():
            raise UnfinishedMessageException()
        current_message = self.current_message
        returned_message = Message(current_message.origin, current_message.seq_number,
                                   current_message.ttl, current_message.operation,
                                   current_message.arguments)
        self.__initialize_new_message()
        self.seq_number += increment_seq_number
        return returned_message


class Message:
    def __init__(self, origin, seq_number, ttl, operation, arguments: dict) -> None:
        self.origin = origin
        self.seq_number = seq_number
        self.ttl = ttl
        self.operation = operation
        self.arguments = arguments

    def get_argument_val(self, argument_key: MessageArguments):
        if argument_key.value in self.arguments.keys():
            return self.arguments[argument_key.value]
        return "DEFAULT"

    def set_argument_val(self, argument_key: MessageArguments, val):
        if argument_key.value in self.arguments.keys():
            self.arguments[argument_key.value] = val

    def __str__(self) -> str:
        if len(self.arguments) > 0 and self.get_argument_val(MessageArguments.MODE) != 'DEFAULT':
            return f'"{self.origin} {str(self.seq_number)} {str(self.ttl)} {self.operation} {" ".join([str(x) for x in self.arguments.values()])}"'
        return f'"{self.origin} {str(self.seq_number)} {str(self.ttl)} {self.operation}"'


class UnfinishedMessage(Message):
    def __init__(self, seq_number, ttl) -> None:
        super().__init__('', seq_number, ttl, '', '')

    def check_for_finished(self):
        if not all([self.origin, self.operation]):
            return False
        if not self.operation in [OperationType.HELLO.value, OperationType.BYE.value] and self.arguments == '':
            return False
        return True


class UnfinishedMessageException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.message = 'Message fields should be filled before message creation'

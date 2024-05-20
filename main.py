import sys
import threading
from src.client import Client
from src.node import NodeServer
from src.messages import MessageFactory
import threading


def main():
    arguments = sys.argv
    origin = arguments[1]
    address, port = origin.split(':')
    message_factory = MessageFactory(origin)
    server = NodeServer(address, port, arguments[2],
                        [], True, message_factory)
    client = Client(server)
    server_thread = threading.Thread(target=server.initialize_socket)
    client_thread = threading.Thread(target=client.run)
    running_threads = [server_thread, client_thread]
    for thread in running_threads:
        thread.start()

    for thread in running_threads:
        thread.join()


if __name__ == '__main__':
    main()

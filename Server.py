import socket
import sys
import os
import select
from threading import Thread

CMD = {
    'getdir': 1,
    'makeroom': 2,
}


class Server:
    HOSTNAME = "localhost"
    UDP_PORT = 30001

    BUFFER_SIZE = 1024

    ENCODING = 'utf-8'

    running_threads = []
    
    def __init__(self):
        self.create_listen_sockets()
        self.process_connections()
    
    def create_listen_sockets(self):
        try:
            # Create UDP socket
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_socket.bind((Server.HOSTNAME, Server.UDP_PORT))
            self.udp_socket.setblocking(False)
            print("Listening on port {} ( UDP )".format(Server.UDP_PORT))
            
        except Exception as msg:
            print(msg)
            exit(1)

    def process_connections(self):
        inputs = [self.udp_socket]
        outputs = []

        readable, writeble, _ = select.select(inputs, outputs, inputs)

        for client in readable:
            if client == self.udp_socket:
                self.udp_socket_handler()
    
    def udp_socket_handler(self):
        recv_tuple = self.udp_socket.recvfrom(Server.BUFFER_SIZE)
        recv_bytes = recv_tuple[0].decode(Server.ENCODING)
        client_address = recv_tuple[1]

        cmd = recv_bytes[0]
        if cmd == CMD['getdir']:
            self.getDir(client_address)
        elif cmd == CMD['makeroom']:
            # input = cmd<space>name<space>ip_addr<space>port
            self.makeRoom(recv_bytes[1:])
        
    def makeRoom(self, room_info):
        room_info = room_info.split(" ")

        name = room_info[0]
        ip_addr = room_info[1]
        port = room_info[2]

        new_thread = Thread(target=self.room_thread, args=(name, ip_addr, port))
        new_thread.start()

        self.running_threads.append(name)
    
    def room_thread(self, arg):
        connected_clients = []

        # Make socket for room
        print("Making socket for {}".format(arg[0]))
        try:
            # Create UDP socket
            room_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            room_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            room_socket.bind((arg[1],arg[2]))
            room_socket.setblocking(False)
            print("Room: {}, Listening on port {} ( TCP )".format(arg[0], arg[2]))
        except Exception as msg:
            print(msg)
            exit(1)
        
        while True:
            # Listen for incoming client connections to the room
            try:
                new_connection = room_socket.recvfrom(Server.BUFFER_SIZE)  
                new_client_addr = new_connection[1]

                # This is a new client, add them to the connected_clients list and move on
                if new_client_addr not in connected_clients:
                    print("Welcome {} to the chat room!".format(new_connection[1]))
                    connected_clients.append(new_connection[1])
                else:
                    # This is a pre-existing client
                    client_msg = new_connection[0]
                    
                    for client in connected_clients:
                        if client is not new_client_addr:
                            # Distribute client message to other clients in room
                            room_socket.sendto(client_msg, client)

            except socket.error as msg:
                # Nothing coming into this room, keep going until something does
                pass

    
    def getDir(self, address):
        path = os.path.dirname(os.path.abspath(__file__))
        file_list = os.listdir(path)

        pkt = ""
        for file in file_list:
            pkt += "(%s, %s)\t - %s".format(room_name, address, file)
        



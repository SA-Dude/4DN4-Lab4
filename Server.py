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

        readable, writeble, exec = select.select(inputs, outputs, inputs)

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
    
    def room_thread(arg):
        # Make socket for room
        print("Making '%s' socket")
        try:
            x = 10
        except Exception as msg:
            print(msg)
            exit(1)

    
    # def getDir(self, address):
    #     path = os.path.dirname(os.path.abspath(__file__))
    #     file_list = os.listdir(path)

    #     pkt = ""
    #     for file in file_list:
    #         pkt += "(%s, %s)\t - %s".format(room_name, address, file)
        



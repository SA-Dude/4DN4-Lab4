import socket
import sys
import os
import struct
from threading import Thread

CMD = {
    'getdir': 1,
    'makeroom': 2,
    'deleteroom': 3,
    'bye': 4,
}


class Server:
    HOSTNAME = "localhost"
    TCP_PORT = 30000

    BUFFER_SIZE = 1024
    BACKLOG = 5
    MSG_ENCODING = 'utf-8'

    running_threads = []
    
    def __init__(self):
        self.create_listen_sockets()
        self.process_connections()
    
    def create_listen_sockets(self):
        try:
            # Create TCP socket
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_socket.bind((Server.HOSTNAME, Server.TCP_PORT))
            self.tcp_socket.listen(Server.BACKLOG)
            print("Listening on port {} ( TCP )".format(Server.TCP_PORT))
        except Exception as msg:
            print(msg)
            exit(1)

    def process_connections(self):
        while True:
            try:
                connection, client_address = self.tcp_socket.accept()
                print("Received connected from {}".format(client_address))

                thread = Thread(target=self.tcp_socket_handler, args=(connection, client_address))
                thread.start()
            except socket.error as _:
                pass
    
    def tcp_socket_handler(self, connection, client_address):
        print("New client thread started...")

        while True:
            recv_bytes = connection.recv(Server.BUFFER_SIZE)

            cmd = recv_bytes[0]
            
            if cmd == CMD['getdir']:
                self.getDir(connection, client_address)
            elif cmd == CMD['makeroom']:
                # input = cmd<space>name<space>ip_addr<space>port
                self.makeRoom(recv_bytes[1:].decode(Server.MSG_ENCODING))
            elif cmd == CMD['deleteroom']:
                self.deleteRoom(recv_bytes[1:].decode(Server.MSG_ENCODING))
            elif cmd == CMD['bye']:
                print("Client closing connection")
                break
    
    def deleteRoom(self, room_name):
        new_list = []
        for room in self.running_threads:
            if room[0] != room_name:
                new_list.append(room)
        
        self.running_threads = new_list
    
    def getDir(self, connection, client_address):
        # Generate packet to send back to client
        pkt = ""

        pkt += "---Current Chat Rooms---\n"
        for entry in self.running_threads:
            pkt += entry[0] + ":" + entry[1] + "," + entry[2] + "\n"
        
        bytesToSend = pkt.encode(Server.MSG_ENCODING)
        connection.send(bytesToSend)
        print("Sent Directory Back to Client: {}".format(client_address))
        
    def makeRoom(self, room_info):
        room_info = room_info.split(" ")

        name = room_info[0]
        ip_addr = room_info[1]
        port = room_info[2]

        new_thread = Thread(target=self.room_thread, args=(name, ip_addr, int(port)))
        new_thread.start()

        self.running_threads.append((name, ip_addr, port))
    
    def room_thread(self, name, ip_addr, port):
        connected_clients = []

        # Make socket for room
        print("Making socket for {}".format(name))
        try:
            # Create UDP socket
            group = socket.inet_aton(ip_addr)
            mreq = struct.pack('4sL', group, socket.INADDR_ANY)

            room_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            room_socket.bind(('', port))
            room_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            print("Room: {}, Listening on port {}:{} ( Multicast UDP )".format(name, ip_addr, port))
        except Exception as msg:
            print(msg)
            exit(1)
        
        while True:
            # Listen for incoming client connections to the room
            try:
                client_msg, new_client_addr = room_socket.recvfrom(Server.BUFFER_SIZE)  

                # This is a new client, add them to the connected_clients list and move on
                if new_client_addr not in connected_clients:
                    print("Welcome {} to the chat room!".format(new_client_addr))
                    connected_clients.append(new_client_addr)
                else:
                    # This is a pre-existing client                    
                    for client in connected_clients:
                        if client is not new_client_addr:
                            # Distribute client message to other clients in room
                            room_socket.sendto(client_msg, client)

            except socket.error as msg:
                # Nothing coming into this room, keep going until something does
                pass
        

if __name__ == "__main__":
    s = Server()

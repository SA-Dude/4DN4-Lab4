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

CMD_FIELD_LEN            = 1 # 1 byte commands sent from the client.
SOCKET_TIMEOUT           = 10

########################################################################
# recv_bytes frontend to recv
########################################################################

# Call recv to read bytecount_target bytes from the socket. Return a
# status (True or False) and the received butes (in the former case).
def recv_bytes(sock, bytecount_target):
    # Be sure to timeout the socket if we are given the wrong
    # information.
    sock.settimeout(SOCKET_TIMEOUT)
    try:
        byte_recv_count = 0 # total received bytes
        recv_bytes = b''    # complete received message
        while byte_recv_count < bytecount_target:
            # Ask the socket for the remaining byte count.
            new_bytes = sock.recv(bytecount_target-byte_recv_count)
            # If ever the other end closes on us before we are done,
            # give up and return a False status with zero bytes.
            if not new_bytes:
                return(False, b'')
            byte_recv_count += len(new_bytes)
            recv_bytes += new_bytes
        # Turn off the socket timeout if we finish correctly.
        sock.settimeout(None)
        return (True, recv_bytes)
    # If the socket times out, something went wrong. Return a False
    # status.
    except socket.timeout:
        sock.settimeout(None)
        print("recv_bytes: Recv socket timeout!")
        return (False, b'')

class Client:
    HOSTNAME = "localhost"
    TCP_PORT = 30000

    RECV_BUFFER_SIZE = 1024
    MSG_ENCODING = 'utf-8'

    running_rooms = []
    
    def __init__(self):
        self.USER_NAME = "Admin"
        self.process_inputs()
    
    def process_inputs(self):
        while True:
            self.cmd = input("Enter your command: ")

            if self.cmd[:7].lower() == "connect":
                self.create_tcp_sockets()
                self.connect_to_server()
                self.connected_to_server()
            elif self.cmd[:4].lower() == "name":
                self.changeName(self.cmd[5:])
            elif self.cmd[:4].lower() == "chat":
                self.create_udp_sockets()
                self.enterChatMode(self.cmd[5:])
            
    def create_tcp_sockets(self):
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except Exception as msg:
            print(msg)
            exit(1)
    
    def create_udp_sockets(self):
        try:
            ttl = struct.pack('b', 1)
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.settimeout(0.2)
            self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        except Exception as msg:
            print(msg)
            exit(1)
    
    def connect_to_server(self):
        try:
            self.tcp_socket.connect((Client.HOSTNAME, Client.TCP_PORT))
        except Exception as msg:
            print(msg)
            exit(1)
        print("Connected to TCP port {}".format(Client.TCP_PORT))
    
    def connected_to_server(self):
        while True:
            connected_cmd = input("(Connected to Server) >> ")

            if connected_cmd[:6].lower() == "getdir":
                self.getDir_cmd()
            elif connected_cmd[:8].lower() == "makeroom":
                self.makeRoom_cmd(connected_cmd[9:])
            elif connected_cmd[:10].lower() == "deleteroom":
                self.deleteRoom(connected_cmd[11:])
            elif connected_cmd[:3].lower() == "bye":
                print("Closing Connection to Server...")
                self.bye_cmd()
                self.tcp_socket.close()
                break
    
    def getDir_cmd(self):
        # Send cmd to Server
        message = CMD['getdir'].to_bytes(CMD_FIELD_LEN, byteorder='big')
        self.tcp_socket.sendall(message)
        print("Sent {} to Server".format(message))

        # Wait for the response fron Server
        recvd_bytes = self.tcp_socket.recv(Client.RECV_BUFFER_SIZE)

        if len(recvd_bytes) == 0:
            print("Closing server connection ... ")
            self.tcp_socket.close()
            sys.exit(1)
        
        recvd_bytes = recvd_bytes.decode(Client.MSG_ENCODING)
        print(recvd_bytes)

        dir = recvd_bytes.split("\n")[1:]
        for line in dir:
            if line:
                info = line.split(":")
                address = info[1].split(",")
                self.running_rooms.append((info[0], address[0], address[1]))
    
    def makeRoom_cmd(self, data):
        cmd = CMD['makeroom'].to_bytes(CMD_FIELD_LEN, byteorder='big')
        room_info = data.encode(Client.MSG_ENCODING)
        pkt = cmd + room_info

        self.tcp_socket.sendall(pkt)
        print("Sent {} to Server".format(pkt))
    
    def bye_cmd(self):
        cmd = CMD['bye'].to_bytes(CMD_FIELD_LEN, byteorder='big')
        self.tcp_socket.sendall(cmd)

        print("Sent {} to Sever".format(cmd))
    
    def deleteRoom(self, data):
        cmd = CMD['deleteroom'].to_bytes(CMD_FIELD_LEN, byteorder='big')
        room_info = data.encode(Client.MSG_ENCODING)
        pkt = cmd + room_info

        self.tcp_socket.sendall(pkt)
        print("Sent {} to Server".format(pkt))
    
    def changeName(self, new_name):
        self.USER_NAME = new_name
    
    def enterChatMode(self, room_name):
        print("Entering Chat Mode")
        ip_addr = None
        port = None

        for room in self.running_rooms:
            if room[0] == room_name:
                ip_addr = room[1]
                port = int(room[2])
                break
        
        if ip_addr is None or port is None:
            print("{}: Not an Active Room".format(room_name))
            return
        else:
            room_address = (ip_addr, port)
        
        while True:
            client_msg = "{}: ".format(self.USER_NAME)
            client_msg += input(">> ")
            self.udp_socket.sendto(client_msg.encode(Client.MSG_ENCODING), room_address)

            try:
                # Try and receive any messages broadcasted in the room
                incoming_msg, room_addr = self.udp_socket.recvfrom(Client.RECV_BUFFER_SIZE)
                print(incoming_msg)
            except socket.error as _:
                pass
      

if __name__ == "__main__":
    s = Client()

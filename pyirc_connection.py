#!/usr/bin/env python

import socket
from gi.repository import GLib

class PyIRC:

    def __init__(self):
        self.connected = False
    
    def connect(self, TCP_ADDR, TCP_PORT):
        self.connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection_socket.connect((socket.gethostbyname(TCP_ADDR), TCP_PORT))
        self.connected = True
        
    
    def send_msg(self, msg):
        if self.connected == False:
            raise Exception("Tried to send message while not being connected to any sever.")
        
        self.connection_socket.send(bytes(msg+"\n", 'UTF-8'))
        
    def parse_messages(self, my_callback):
        BUFFER_SIZE = 1024
        readbuffer=""
        
        while 1:
            readbuffer = readbuffer + self.connection_socket.recv(BUFFER_SIZE).decode("utf-8")
            temp = str.split(readbuffer, "\n")
            readbuffer = temp.pop( )

            for line in temp:
                tokens=str.rstrip(line)
                tokens=str.split(tokens)

                if(tokens[0]=="PING"):
                    self.send_msg("PONG " + str(tokens[1]) + "\r\n")
                else:
                    GLib.idle_add(my_callback,line)
            

    def disconnect(self):
        self.connection_socket.close()
        self.connected = False






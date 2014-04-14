#!/usr/bin/env python

import socket
from gi.repository import GLib

class PyIRC:

    def __init__(self):
        self.connected = False
        self.dc_callback = None

    def is_connected(self):
        return self.connected
    
    def connect(self, TCP_ADDR, TCP_PORT):
        self.connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = True

        try:
            self.connection_socket.connect((socket.gethostbyname(TCP_ADDR), TCP_PORT))
        except Exception as e:
            print("Something's wrong with %s. Exception type is %s" % (address, e))
            self.connected = False
        
    def send_msg(self, msg):
        if self.connected == False:
            raise Exception("Tried to send message while not being connected to any sever.")
        
        self.connection_socket.send(bytes(msg+"\n", 'UTF-8'))
        
    def parse_messages(self, my_callback):
        BUFFER_SIZE = 4096
        readbuffer=""
        
        while 1:
            try:
                cur_data = self.connection_socket.recv(BUFFER_SIZE)
            except Exception as e:
                print(str(e))
                self.connected = False
                break;
            
            readbuffer = readbuffer + cur_data.decode("utf-8")
            temp = str.split(readbuffer, "\n")
            readbuffer = temp.pop( )

            for line in temp:
                tokens=str.rstrip(line)
                tokens=str.split(tokens)

                if(tokens[0]=="PING"):
                    self.send_msg("PONG " + str(tokens[1]) + "\r\n")
                else:
                    GLib.idle_add(my_callback,line, priority = GLib.PRIORITY_HIGH )
            

    def disconnect(self):
        self.connection_socket.close()
        self.connected = False






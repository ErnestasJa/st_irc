#!/usr/bin/env python

from gi.repository import Gtk
from gi.repository import GLib
from pyirc_connection import PyIRC

try:    
    import thread 
except ImportError:
    import _thread as thread #Py3K changed it.
    
import threading


GLib.threads_init()

class Task:
    def __init__(self, my_task, my_cb):
       self.function = my_task
       self.my_cb = my_cb

    def _start(self):
        self._stopped = False
        self.function(self.my_cb)

    def start(self):
        threading.Thread(target=self._start).start()

    def stop(self):
        self._stopped = True

### Our main window
class PyIRC_Application:

    def __init__(self):

        self.builder = Gtk.Builder()
        self.builder.add_from_file("pyirc_interface.glade")
        
        self.window = self.builder.get_object("window1")        
        self.connection_dialog = self.builder.get_object("connection_dialog")
        
        self.textview = self.builder.get_object("textview1")
        self.textbuffer = self.textview.get_buffer();
        self.entry          = self.builder.get_object("entry1")
        self.connect_btn    = self.builder.get_object("connect_btn")
        self.disconnect_btn = self.builder.get_object("disconnect_btn")
        self.cd_connect_btn = self.builder.get_object("cd_connect_btn")
        self.cd_cancel_btn  = self.builder.get_object("cd_cancel_btn")
        self.send_btn = self.builder.get_object("send_btn")
        
        self.window.connect("delete-event", Gtk.main_quit)
        self.connection_dialog.connect("delete-event", self.on_cd_cancel_btn_clicked)
        self.connect_btn.connect("activate", self.on_connect_btn_clicked)
        self.disconnect_btn.connect("activate", self.on_disconnect_btn_clicked)
        self.send_btn.connect("clicked", self.on_send_btn_clicked)
        self.cd_connect_btn.connect("clicked", self.on_cd_connect_btn_clicked)
        self.cd_cancel_btn.connect("clicked", self.on_cd_cancel_btn_clicked)
        
        ## create irc connection object
        self.irc = PyIRC()
        self.window.show_all()


    def on_msg(self, msg):
        my_text = self.textbuffer.get_text(self.textbuffer.get_start_iter(),self.textbuffer.get_end_iter(),True)
        self.textbuffer.set_text(my_text + msg + "\n")
            
    def on_connect_btn_clicked(self, widget):
        self.connection_dialog.show_all();

    def on_send_btn_clicked(self, widget):
        if self.irc.connected:
            self.irc.send_msg(self.entry.get_text())
            self.entry.set_text("")
            
    def on_disconnect_btn_clicked(self, widget):
        if self.irc.connected:
            self.irc.disconnect()
        
    def on_cd_connect_btn_clicked(self, widget):
        if self.irc.connected:
            self.irc.disconnect();
            
        server = self.builder.get_object("cd_server_entry").get_text()
        nick = self.builder.get_object("cd_nickname_entry").get_text()
        password = self.builder.get_object("cd_password_entry").get_text()

        #TCP_ADDR = 'irc.twitch.tv'
        TCP_PORT = 6667
        self.irc.connect(server,TCP_PORT)
        self.irc_task = Task(self.irc.parse_messages,self.on_msg)
        self.irc_task.start()

        self.irc.send_msg("PASS " + password)
        self.irc.send_msg("NICK " + nick)
        self.connection_dialog.hide()    

    def on_cd_cancel_btn_clicked(self, widget):
            self.connection_dialog.hide()

app = PyIRC_Application()
Gtk.main()

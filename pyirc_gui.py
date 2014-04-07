#!/usr/bin/env python

import re
import pickle
from gi.repository import Gtk
from gi.repository import Gdk
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
       self.thread = None

    def _start(self):
        
        self.function(self.my_cb)

    def start(self):
        self._stopped = False
        self.thread = threading.Thread(target=self._start)
        self.thread.start()

    def stop(self):
        self.thread.join()
        self._stopped = True

### Our main window
class PyIRC_Application:

    def __init__(self):

        self.builder = Gtk.Builder()
        self.builder.add_from_file("pyirc_interface.glade")
        self.nick = ""

        #windows
        self.window = self.builder.get_object("window1")
        self.connection_dialog = self.builder.get_object("connection_dialog")
        self.join_channel_dialog = self.builder.get_object("join_channel_dialog")

        #elements
        self.channels_notebook  = self.builder.get_object("channels_notebook")
        self.textview           = self.builder.get_object("textview1")
        self.text_scroll_window = self.builder.get_object("text_scroll_window")
        self.entry              = self.builder.get_object("entry1")
        self.connect_btn        = self.builder.get_object("connect_btn")
        self.join_channel_btn   = self.builder.get_object("join_channel_btn")
        self.disconnect_btn     = self.builder.get_object("disconnect_btn")
        self.cd_save_btn        = self.builder.get_object("cd_save_btn")
        self.cd_connect_btn     = self.builder.get_object("cd_connect_btn")
        self.cd_cancel_btn      = self.builder.get_object("cd_cancel_btn")
        self.cj_join_btn        = self.builder.get_object("cj_join_btn")
        self.cj_cancel_btn      = self.builder.get_object("cj_cancel_btn")
        self.send_btn           = self.builder.get_object("send_btn")

        #signals
        self.window.connect("delete-event", Gtk.main_quit)
        self.channels_notebook.connect("switch-page", self.on_switch_channel)
        self.connect_btn.connect("activate", self.on_connect_btn_clicked)
        self.join_channel_btn.connect("activate", self.on_join_channel_btn_clicked)
        self.disconnect_btn.connect("activate", self.on_disconnect_btn_clicked)
        self.send_btn.connect("clicked", self.on_send_btn_clicked)
        self.cd_save_btn.connect("clicked", self.on_cd_save_btn_clicked)
        self.cd_connect_btn.connect("clicked", self.on_cd_connect_btn_clicked)
        self.cd_cancel_btn.connect("clicked", self.on_cd_cancel_btn_clicked)
        self.cj_join_btn.connect("clicked", self.on_cj_join_btn_clicked)
        self.cj_cancel_btn.connect("clicked", self.on_cj_cancel_btn_clicked)
        self.entry.connect("key-press-event", self.on_entry_key_pressed_enter)

        #Notebook stuff
        self.textbuffers = {}

        #create irc connection object
        self.irc = PyIRC()
        self.irc_task = None

        # show main window
        self.load_saved_con_info()
        self.window.show_all()

    def on_delete_event(self, widget, event, data =None):
        if self.irc.connected:
            self.irc_task.stop()
            self.irc.disconect()
            
        Gtk.main_quit()

    def on_msg(self, msg):
        prog = re.compile("^(:(?P<prefix>\S+) )?(?P<command>\S+)( (?!:)(?P<params>.+?))?( :(?P<trail>.+))?$")
        groups = prog.match(msg)

        output = ""

        print(msg)

        if (groups.group('command') is not None) and (groups.group('params') is not None) and (groups.group('command') == "PRIVMSG"):
            nick = groups.group('prefix').partition('!')[0]
            output = nick + ": " + groups.group('trail')
            channel = groups.group('params')
            
            if(self.channels_notebook.get_current_page()!=-1):
                page = self.channels_notebook.get_nth_page(self.channels_notebook.get_current_page())
                active_channel = self.channels_notebook.get_tab_label_text(page).strip()
                if channel == active_channel:
                    self.textview.scroll_to_iter(self.textview.get_buffer().get_end_iter(),0.0,False,0,0)
                    
            self.echo_msg(channel,output)
            

    def on_switch_channel(self, widget, page, page_number, data = None):
        name = self.channels_notebook.get_tab_label_text(page).strip()
        if name in self.textbuffers:
            self.textview.set_buffer(self.textbuffers[name])
        

    def on_connect_btn_clicked(self, widget):
        self.connection_dialog.show_all();

    def on_join_channel_btn_clicked(self, widget):
        if self.irc.connected:
            self.join_channel_dialog.show_all();

    def echo_msg(self, channel, msg):
        if channel in self.textbuffers:
            buf = self.textbuffers[channel]
            buf.insert(buf.get_end_iter(),msg+"\n")

    def evaluate_entry_box(self):
        if self.irc.connected:
            text = self.entry.get_text()

            page_num = self.channels_notebook.get_current_page()

            if page_num == -1 :
                print("Not in channel.")
                return

            page = self.channels_notebook.get_nth_page(page_num)
            channel = self.channels_notebook.get_tab_label_text(page).strip()

            self.irc.send_msg("PRIVMSG " + channel + " :" + text)
            self.echo_msg(channel,"> "+self.nick+": "+text)
            self.entry.set_text("")

    def on_send_btn_clicked(self, widget):
        self.evaluate_entry_box()

    def on_entry_key_pressed_enter(self, widget, ev, data=None):
        if ev.keyval == Gdk.KEY_Return:
            self.evaluate_entry_box()

    def on_disconnect_btn_clicked(self, widget):
        if self.irc.connected:
            self.irc.disconnect()
    
    def on_cd_save_btn_clicked(self, widget):
        info = {}
        info['server']=self.builder.get_object("cd_server_entry").get_text()
        info['nick']=self.builder.get_object("cd_nickname_entry").get_text()
        info['password']=self.builder.get_object("cd_password_entry").get_text()

        with open('con_info.dat', 'wb') as handle:
            pickle.dump(info, handle)

    def load_saved_con_info(self):
        with open('con_info.dat', 'rb') as handle:
            info = pickle.loads(handle.read())
            self.builder.get_object("cd_server_entry").set_text(info['server'])
            self.builder.get_object("cd_nickname_entry").set_text(info['nick'])
            self.builder.get_object("cd_password_entry").set_text(info['password'])

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
        self.nick = nick
        self.connection_dialog.hide()

    def on_cd_cancel_btn_clicked(self, widget):
        self.connection_dialog.hide()

    def on_cj_join_btn_clicked(self, widget):
        channel_name = self.builder.get_object("cj_channel_name_entry").get_text().strip()
        self.irc.send_msg("JOIN " + channel_name)
        self.textbuffers[channel_name]=Gtk.TextBuffer()
        self.join_channel_dialog.hide();
        self.channels_notebook.insert_page(Gtk.Frame(),Gtk.Label(channel_name),0)
        self.channels_notebook.show_all()

    def on_cj_cancel_btn_clicked(self, widget):
        self.join_channel_dialog.hide();

app = PyIRC_Application()
Gtk.main()

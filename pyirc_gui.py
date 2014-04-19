#!/usr/bin/env python

import re
import pickle
from gi.repository import Gtk, Gdk, GLib, Pango

from pyirc_connection import PyIRC
import pyirc_tools

try:
    import thread
except ImportError:
    import _thread as thread #Py3K changed it.

import threading


GLib.threads_init()

class Channel:
    def __init__(self, name):
        self.users = Gtk.ListStore(str)
        self.chat_log = Gtk.TextBuffer()
        self.bold_tag = self.chat_log.create_tag("b", weight=Pango.Weight.BOLD)
        self.name = name

        self.info = {}
        
    def echo(self, message, *tags):
        self.chat_log.insert_with_tags(self.chat_log.get_end_iter(),message+"\n",*tags)

    def echo_no_newline(self, message, *tags):
        self.chat_log.insert_with_tags(self.chat_log.get_end_iter(),message,*tags)

    def add_user(self, user):
        self.users.append(user)

    def get_bold_tag(self):
        return self.bold_tag

    def remove_user(self, user):
        for row in self.users:
            if row[0] == user[0]:
                self.users.remove(row.iter)
                break

    def clear_users(self):
        self.users.clear()
    

class Task:
    def __init__(self, my_task, *args, **kw_args):
       self.function = my_task
       self.args = args
       self.kw_args = kw_args
       self.thread = None

    def _start(self, *args, **kw_args):
        self.function(*args, **kw_args)

    def start(self):
        self._stopped = False
        self.thread = threading.Thread(target=self._start, args = self.args, kwargs = self.kw_args)
        self.thread.start()

    def stop(self):
        self.thread.join()
        self._stopped = True

### Our main window
class PyIRC_Application:

    def __init__(self):
        self.kps = KappaStats(self)
        self.refresh_task = None

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
        self.exit_btn           = self.builder.get_object("exit_btn")
        self.cd_save_btn        = self.builder.get_object("cd_save_btn")
        self.cd_connect_btn     = self.builder.get_object("cd_connect_btn")
        self.cd_cancel_btn      = self.builder.get_object("cd_cancel_btn")
        self.cj_join_btn        = self.builder.get_object("cj_join_btn")
        self.cj_cancel_btn      = self.builder.get_object("cj_cancel_btn")
        self.send_btn           = self.builder.get_object("send_btn")
        self.user_list          = self.builder.get_object("user_list")

        self.channel_info_textview    = self.builder.get_object("channel_info_textview")
        self.channel_info_textview.get_buffer().create_tag("b", weight=Pango.Weight.BOLD)
        self.refresh_channel_info_btn = self.builder.get_object("refresh_channel_info_btn")

        #signals
        self.window.connect("delete-event", Gtk.main_quit)
        self.channels_notebook.connect_after("switch-page", self.on_switch_channel)
        self.connect_btn.connect("activate", self.on_connect_btn_clicked)
        self.join_channel_btn.connect("activate", self.on_join_channel_btn_clicked)
        self.disconnect_btn.connect("activate", self.on_disconnect_btn_clicked)
        self.exit_btn.connect("activate", self.on_exit_btn_clicked)
        self.send_btn.connect("clicked", self.on_send_btn_clicked)
        self.cd_save_btn.connect("clicked", self.on_cd_save_btn_clicked)
        self.cd_connect_btn.connect("clicked", self.on_cd_connect_btn_clicked)
        self.cd_cancel_btn.connect("clicked", self.on_cd_cancel_btn_clicked)
        self.cj_join_btn.connect("clicked", self.on_cj_join_btn_clicked)
        self.cj_cancel_btn.connect("clicked", self.on_cj_cancel_btn_clicked)
        self.entry.connect("key-press-event", self.on_entry_key_pressed_enter)

        self.refresh_channel_info_btn.connect("clicked",  self.on_refresh_channel_info_btn_clicked)

        #Channels
        self.channels = {}

        #create irc connection object
        self.irc = PyIRC()
        self.irc_task = None

        # show main window
        self.load_saved_con_info()
        self.window.show_all()
        self.parse_user_list_cmd_re = re.compile("^(?P<name>\S+) = (?P<channel>\S+)$")

    def get_active_channel(self):
        page = self.channels_notebook.get_nth_page(self.channels_notebook.get_current_page())
        if page == -1:
            return None
        else:
            active_channel = self.channels_notebook.get_tab_label_text(page).strip()

            if active_channel in self.channels:
                return self.channels[active_channel]
            else:
                return None

    def on_delete_event(self, widget, event, data =None):
        if self.irc.connected:
            self.irc_task.stop()
            self.irc.disconect()
            
        Gtk.main_quit()

    def on_msg(self, groups):

        #print(msg)
        
        output = ""

        if (groups.group('command') is not None) and (groups.group('params') is not None):
            if groups.group('command') == "PRIVMSG":
                nick = groups.group('prefix').partition('!')[0]
                channel = groups.group('params')
                
                if(self.channels_notebook.get_current_page()!=-1):
                    page = self.channels_notebook.get_nth_page(self.channels_notebook.get_current_page())
                    active_channel = self.channels_notebook.get_tab_label_text(page).strip()
                    if channel == active_channel:
                        self.textview.scroll_to_iter(self.textview.get_buffer().get_end_iter(),0.0,False,0,0)
                        
                if channel in self.channels:
                    ch = self.channels[channel]
                    ch.echo_no_newline(nick,ch.get_bold_tag())
                    ch.echo(": " + groups.group('trail'))
                    self.kps.on_message(nick,channel,groups.group('trail'))

            elif groups.group('command') == "353":
                match = self.parse_user_list_cmd_re.match(groups.group('params'))
                ch_name = match.group('channel')
                ch = self.channels[ch_name]

                users = groups.group('trail').split()
                
                for usr in users:
                    ch.add_user([usr])

            elif groups.group('command') == "JOIN":
                nick = groups.group('prefix').partition('!')[0]
                ch_name = groups.group('params').strip()
                ch = self.channels[ch_name]
                
                ch.add_user([nick])

            elif groups.group('command') == "PART":
                nick = groups.group('prefix').partition('!')[0]
                ch_name = groups.group('params').strip()
                ch = self.channels[ch_name]
                
                ch.remove_user([nick])

        return False;
                          

    def on_switch_channel(self, widget, page, page_number, data = None):
        name = self.channels_notebook.get_tab_label_text(page).strip()
        if name in self.channels:
            self.textview.set_buffer(self.channels[name].chat_log)
            self.user_list.set_model(self.channels[name].users)
            self.start_refresh()
        

    def on_connect_btn_clicked(self, widget):
        if self.irc.is_connected():
            parent = None
            md = Gtk.MessageDialog(parent, 0, Gtk.MessageType.WARNING,Gtk.ButtonsType.CLOSE,
                "Can't connect to more than one server.\nPlease first disconnect.")
            md.run()
            md.destroy()
            return
            
        self.connection_dialog.show_all();

    def on_disconnect_btn_clicked(self, widget):
        if self.irc.connected:
            self.channels = {}
            while self.channels_notebook.get_current_page() != -1:
                self.channels_notebook.remove_page(self.channels_notebook.get_current_page())
            self.channels_notebook.show_all()
            self.irc.disconnect()

            self.textview.set_buffer(Gtk.TextBuffer())
            self.user_list.set_model(Gtk.ListStore(str))

    def on_exit_btn_clicked(self, widget):
        if self.irc.connected:
            self.channels = {}
            while self.channels_notebook.get_current_page() != -1:
                self.channels_notebook.remove_page(self.channels_notebook.get_current_page())
            self.channels_notebook.show_all()
            self.irc.disconnect()

            self.textview.set_buffer(Gtk.TextBuffer())
            self.user_list.set_model(Gtk.ListStore(str))

    def on_join_channel_btn_clicked(self, widget):
        if self.irc.is_connected():
            self.join_channel_dialog.show_all();
        else:
            parent = None
            md = Gtk.MessageDialog(parent, 0, Gtk.MessageType.WARNING,Gtk.ButtonsType.CLOSE,
                "Can't join a channel while not connected to server.\nPlease connect to a server first.")
            md.run()
            md.destroy()
            return

    def evaluate_entry_box(self):
        if self.irc.connected:
            text = self.entry.get_text()

            page_num = self.channels_notebook.get_current_page()

            if page_num == -1 :
                return

            page = self.channels_notebook.get_nth_page(page_num)
            channel = self.channels_notebook.get_tab_label_text(page).strip()

            if channel in self.channels:
                self.channels[channel].echo("> "+self.nick+": "+text)

            self.irc.send_msg("PRIVMSG " + channel + " :" + text)
            self.entry.set_text("")

    def on_send_btn_clicked(self, widget):
        self.evaluate_entry_box()

    def on_entry_key_pressed_enter(self, widget, ev, data=None):
        if ev.keyval == Gdk.KEY_Return:
            self.evaluate_entry_box()
    
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
        self.channels[channel_name]=Channel(channel_name)
        self.join_channel_dialog.hide();
        self.channels_notebook.insert_page(Gtk.Frame(),Gtk.Label(channel_name),0)
        self.channels_notebook.show_all()

    def on_cj_cancel_btn_clicked(self, widget):
        self.join_channel_dialog.hide();

    def start_refresh(self):
        tb = self.channel_info_textview.get_buffer()
        tb.delete(tb.get_start_iter(),tb.get_end_iter())
        
        if self.get_active_channel() is not None and self.refresh_task is None:
            self.refresh_task = Task(pyirc_tools.PyIRC_Twitch_Channel_Status_Parser,self.get_active_channel().name,self.on_refresh_channel_info)
            self.refresh_task.start()

    def on_refresh_channel_info_btn_clicked(self, widget):
        self.start_refresh()
        print("refreshing")

    def on_refresh_channel_info(self, channel, data):
        if self.refresh_task is not None :
            self.refresh_task.stop()
            self.refresh_task = None
            
            tb = self.channel_info_textview.get_buffer()
            tb.insert_with_tags_by_name(tb.get_end_iter(), "Channel : ", "b")
            tb.insert(tb.get_end_iter(), channel + "\n")
            
            tb.insert_with_tags_by_name(tb.get_end_iter(), "Status : ", "b")
            tb.insert(tb.get_end_iter(), ("Offline" if data["stream"]==None else "Online") + "\n")

            if data["stream"]!=None :
                tb.insert_with_tags_by_name(tb.get_end_iter(), "Game : ", "b")
                tb.insert(tb.get_end_iter(), data["stream"]["game"] + "\n")

                tb.insert_with_tags_by_name(tb.get_end_iter(), "Title : ", "b")
                tb.insert(tb.get_end_iter(), data["stream"]["channel"]["status"] + "\n")
            
        else:
            print("Refresh task is None.")
        print("done refreshing")


class KappaStats:
    def __init__(self, irc_app):
        self.kappa_count = 0
        self.irc_app = irc_app
        self.kappa_re = re.compile("(?=((^|\s)Kappa(\s|$)))")
        
    def on_message(self, user, channel, msg):
        if msg.strip() == "!kpc":
            ch = self.irc_app.channels[channel]
            ch.echo("<<<<<<<<<<<<<<<<<<<<<<<<<  Counting Kappas  >>>>>>>>>>>>>>>>>>>")
            self.irc_app.irc.send_msg("PRIVMSG " + channel + " :Current kappa count: " + str(self.kappa_count))
        
        
        self.kappa_count += len(self.kappa_re.findall(msg))

app = PyIRC_Application()
Gtk.main( )

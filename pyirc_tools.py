#!/usr/bin/env python

from gi.repository import GLib
import urllib.request
import json


def PyIRC_Twitch_Channel_Status_Parser(channel, callback):

    try:
        req = urllib.request.Request(url='https://api.twitch.tv/kraken/streams/'+channel[1:], headers= {'Accept' : 'application/vnd.twitchtv.v3+json'})
        f = urllib.request.urlopen(req)
    except urllib.request.URLError as e:
        print(str(e))
        return False
    
    response = json.loads(f.read().decode())
    GLib.idle_add(callback,channel,response)
    
    return False







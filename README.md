About
======
ST_IRC is a simple twitch irc client written in python, using gtk3 for gui
ST_IRC is meant only to be used to connect to single irc network (such as Twitch.tv)

Usage
======
Install python 3.x, install gtk3 packages, download scripts, run pyirc_guy.py
Password for twitch.tv can aquired from: https://twitchapps.com/tmi

Hopefully it should run without too much trouble

Features
======
* Join twitch.tv irc network
* Join twitch.tv irc channel
* User list
* Send, receive chat messages
* Save conection information

Missing features
======
* Leave channel

Known bugs
======
* Exit button in menu does nothing
* Leave channel
* Uncommonly occuring error on _decode("utf-8")_
* IRC connection tread not closing properly on exit.
* Duplicate user nick entry for client in user list
* Client UI freezing in high trafic channels (20k~ users) when receiving many JOIN, PART messages

Not planned features
======
These features are not planned to be implement due to the time and or other things it will take for them to be implemented.
* Emoticons
* Plugin system (probably most usefull for chat bots)

Connection window
======
![ScreenShot](http://puu.sh/89Ckd)

Channel join window
======
![ScreenShot](http://puu.sh/89Cnh.png)

Some casual twitch chatting
======
![ScreenShot](http://puu.sh/89BkU)

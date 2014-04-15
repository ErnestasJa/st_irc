About
======
ST_IRC is a simple twitch irc client written in python, using gtk3 for gui.
ST_IRC is meant only to be used to connect to single irc network (such as Twitch.tv)

Usage
======
Install python 3.x, install gtk3 packages, download scripts, run pyirc_guy.py. Password for twitch.tv can aquired from: https://twitchapps.com/tmi

Hopefully it should run without too much trouble

Features
======
* Join twitch.tv irc network
* Join twitch.tv irc channel
* User list
* Send, receive chat messages
* Save conection information
* Automatic chat scrolling after getting new message
* Nick name highlighting
* Channel status, game query

Planned features
======
The list might get longer in future.
* Leave channel

Not planned features
======
These features are not planned to be implement due to the time and or other things it will take for them to be implemented.
* Emoticons
* Plugin system (probably most usefull for chat bots)

Known bugs
======
* Exit button in menu does nothing
* Leave channel
* Uncommonly occuring error on _decode("utf-8")_
* IRC connection thread not closing properly on exit.
* Duplicate client user nick name entry in user list.



Connection window
======
![ScreenShot](http://puu.sh/89Ckd)

Channel join window
======
![ScreenShot](http://puu.sh/89Cnh.png)

Some casual twitch chatting
======
![ScreenShot](http://puu.sh/89BkU)

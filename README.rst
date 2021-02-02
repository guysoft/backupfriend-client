BackupFriend Client
===================

BackupFriend is a tool that lets you place a RaspberryPi with a hard drive in your friends house or family, or a server. And lets you sync your folders tracking history changes.
It uses a backend located here: https://github.com/guysoft/BackupFriend-docker . And a RaspsberryPi distro that holds this backend here: https://github.com/guysoft/BackupFriendPi

This repository is the graphical Desktop application.

Requiremnets:
 - SSH
 -  rdiff-backup
 
 
Screenshots
===========

.. image:: https://raw.githubusercontent.com/guysoft/backupfriend-client/master/media/backfriend-client-screenshot.png
.. :scale: 25https://raw.githubusercontent.com/guysoft/backupfriend-client/master/media/backfriend-client-screenshot.png %
.. :alt: Main window

Build and develop
=================

1. Clone this repo::

    git clone https://github.com/guysoft/backupfriend-client.git
 

2. Install requirements::

    cd backupfriend-client
    pip3 install requirements.txt

3. Run: ::

    python3 src/backupfriend-client.py


Windows note:
 - You will need rdiff-backup executable from here: https://github.com/rdiff-backup/rdiff-backup/releases/tag/v2.0.5
 - You need ssh from here: http://www.mls-software.com/opensshd.html

Atribution:
Icon by: Freepik: https://www.flaticon.com/authors/freepik

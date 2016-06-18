# PlasmaBot: A Superior Discord Bot.

PlasmaBot is a Discord music bot written in [Python](https://www.python.org "Python homepage"). Forked from [MusicBot](https://github.com/SexualRhinoceros/MusicBot "by SexualRhinoceros"), Plasma Bot is a vast extension that is currently in development.  Plasma Bot adds new modules in addition to music including Moderator Functions and Autoreply, with new modules being added as development progresses.

### How do I set it up?
(These tutorials are currently hosted on [SexualRhinocerous's Repo](https://github.com/SexualRhinoceros/MusicBot) as installation has not changed at all as of this point.

- [Windows Tutorial](https://github.com/SexualRhinoceros/MusicBot/wiki/Installation-guide-for-Windows-7-and-up "Windows instructions")
- [Linux Tutorial](https://github.com/SexualRhinoceros/MusicBot/wiki/Installation-guide-for-Ubuntu-14.04-and-other-versions "Linux instructions")
- [Docker Tutorial](https://github.com/SexualRhinoceros/MusicBot/wiki/Installation-guide-for-Docker)
- [OSX Tutorial](https://github.com/SexualRhinoceros/MusicBot/wiki/Installation-guide-for-OSX)

### Commands

Classic Commands are listed [here](https://github.com/SexualRhinoceros/MusicBot/wiki/Commands-list "Commands list").
New commands are being added as development progresses, but changes currently include:

 - {>}invite - replaces {>}joinserver and provides a bot invite link when using a bot account
 - {>}say [message] - bot will respond the message back as a reply to the message author
 - {>}tts [message] - with sufficient permissions, bot will /tts the message to the local channel
 - {>}purge [#] - replaces >clean, in progress to delete more than just bot messages.
 
Future Commands will include:

 - {>}kick [UserMention] - kicks a user from the current server
 - {>}ban [UserMention] - bans a user from the current server
 - {>}mute [text | voice | Default: all] [channel | Default: server] [UserMention] - mutes a user in the given server or channel
 
 - {>}addAR [message] - adds an autoreply to the current server
 - {>}addGlobalAR [message] - adds an autoreply to the global table
 
 - {>}giveRole [userMention] [roleName] - gives a role to a mentioned user
 - {>}removeRole [userMention] [roleName] - removes a role from a mentioned user

 - {>}setTGChannel [channelMention | ChannelID] [telegramURL] - links a telegram channel to a giving Discord Channel
 - {>}unlinkTGChannel - unlinks the currentChannel from TG, or the server from TG if only 1 TG channel
 
More improvement ideas to come!

### Configuration

The main configuration file is `config/options.ini`, and is included with the default bot configuration.  If this file is deleted, a backup is provided as `example_options.ini` which can be copied and renamed to `options.ini` to restore default values.

### Great, now how do I use it?
Download the bot, set up/install the dependencies, and run `run.py` with python (or `runbot.bat`/`run.sh` for non-terminal use)  Read the Instalation Tutorials for more information or in case of confusion.

If you have any errors, read the FAQ [here](https://github.com/SexualRhinoceros/MusicBot/wiki/FAQ "Wiki"). If that didn't help, you can ask for assistance on the discord help server. Is is recommended to take screenshots so the developers can see errors.

[Development / Help Server](https://discord.gg/011Vbr8fyWLZw8Obg "Discord link")

### FAQ

Some frequently asked questions are listed on the wiki [here](https://github.com/SexualRhinoceros/MusicBot/wiki/FAQ "Wiki").

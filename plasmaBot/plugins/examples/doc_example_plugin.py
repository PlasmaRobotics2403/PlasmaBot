from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response
import discord

from plasmaBot import exceptions

import logging
log = logging.getLogger('discord')

class EXAMPLECOMMAND(PBPlugin):
    name = 'Example Command, Do Not Use' #A Fancy Name to be Associated with the Plugin
    globality = 'all' #The Globality of the Plugin (WIP).  Either string 'all', string 'optional', or a list [] with a list item for the different server IDs it will run on (manual plugin)
    help_exclude = False #whether or not to exclude commands in this plugin from the help command

    def __init__(self, plasmaBot): #anything you need ran on plugin load, load it here.
        super().__init__(plasmaBot)

    async def cmd_examplecommand(self, desired_arguments_passed_here): #args can be any args from the list at the bottom of the page, which will return the item as shown below.  Any args not in this list will read from words sent after the messages, split by spaces, from left to right. These args can be set as optional by asigning them a default value if not present.
        """
        Usage:
            {command_prefix}command_key (required arguments have parenthesis) [optional_arguments have brackets]

        A string about how the plugin works

        help_exclude modifier_strings_modify_functionality help_exclude_excludes_command_from_help_list
        """ #This docstring must be here for the help command to work.  Command Modifier Strings modify the command's effect in the rest of the bot.  Bot will not error out if they do not exist.
        #do stuff here
        return Response('message string or variable to send to the channel where the message was sent', reply=True, delete_after=15) #reply = True if you want the message to reply to the original message author, delete_after is the time until bot's message will be auto-deleted, 0 means never delete (although don't do this unless necesary as it is a config feature to delete messages or not) OPTIONAL ARGUMENTS: (1) return Response(send_help=True) will send the command's help message, and can be used in combination with help_message='Error Message to Be included' to include an Error Message in with the Help Response. (2) return Response(permissions_error=True) returns the default Permissions Error message to the channel.

    async def on_message(message, message_type, message_context): # plugins have access to all bot events.  Only exception to normall formating is the requirement of message_type, message_contextm and auth_perms in on_message which supply the sender of the message [owner, self, bot (other bot), or user] as a string or the place where it was sent ([server, direct] as a string for server channels vs direct messages as well as the permissions level for the message author)
        pass #replace this with your code if you want to use the bot-event

##################################################
# Possible command-function arguments:

# ['message'] = message (the message object, on which everything else is based, simpply for ease of programming and ease of reading)

# ['channel'] = message.channel (the channel object)

# ['author'] = message.author (the author object)

# ['server'] = message.server (the server object) (returns None if is a private_channel (DM))

# ['user_mentions'] = list(map(message.server.get_member, message.raw_mentions)) (an array of users mentioned in the message, from left to right)

# ['channel_mentions'] = list(map(message.server.get_channel, message.raw_channel_mentions)) (an array of channels mentioned in the message, from left to right)

# ['voice_channel'] = message.server.me.voice_channel (the voice channel that the bot is currently in)

# ['message_type'] = message_type (Who sent the message.  'owner' if sent by the bot owner (via config), 'self' if sent by the bot, 'bot' if sent by another bot account, or 'user' if sent by anyone else)

# ['message_context'] = message_context ('server' if message was sent in a server channel, or 'direct' if sent in over a DM)

# ['leftover_args'] = args (the message without the command, split by spaces in a list)
###################################################

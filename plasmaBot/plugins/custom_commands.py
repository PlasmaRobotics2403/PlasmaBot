from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response
import discord

from plasmaBot import exceptions

import logging
log = logging.getLogger('discord')


class dbt_custom_commands_server_instance(object):
    def __init__(self):
        self.columns = ["COMMAND_KEY", "RESPONSE"]
        self.datatypes = ["TEXT PRIMARY KEY NOT NULL", "TEXT"]
        self.seed = []


class CustomCommands(PBPlugin):
    name = 'Custom Commands'
    globality = 'all'
    help_exclude = False

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)

        self.pl_config = PBPluginConfig(plasmaBot, 'custom_commands.ini', 'CUSTOM COMMANDS', {'Files':[['commands_db_location', 'The location of the Custom Commands database', 'data/custom_commands']]})

        self.commands_db = sq.Connect(self.pl_config.commands_db_location)

    async def cmd_custom(self, server, leftover_args):
        """
        Usage:
            {command_prefix}custom [modifier]

        List Custom Commands.  Moderators: Modify Server's Custom Commands
        """
        if not leftover_args:
            return Response('Listing Custom Commands', reply=True, delete_after=45)
        else:
            return Response('DEFAULT_EXAMPLE_MESSAGE.  PROGRAMMER FORGOT TO CHANGE DEFAULTS', reply=True, delete_after=45)

    async def on_message(self, message, message_type, message_context):
        pass #delete this event if you aren't going to use it.

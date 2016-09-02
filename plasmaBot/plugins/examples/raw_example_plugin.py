from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response
import discord

from plasmaBot import exceptions

import logging
log = logging.getLogger('discord')

class EXAMPLECOMMAND(PBPlugin):
    name = 'Example Command, Do Not Use'
    globality = 'all'
    help_exclude = False

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)

    async def cmd_examplecommand(self, desired_arguments_passed_here):
        """
        Usage:
            {command_prefix}command_key (required arguments have parenthesis) [optional_arguments have brackets]

        A string about how the plugin works

        command_modifier_strings help_exclude _is_a_string_and_excludes_this_commmand_from_help remove_last_two_lines_if_no_modifiers
        """

        #command runs here

        return Response('DEFAULT_EXAMPLE_MESSAGE.  PROGRAMMER FORGOT TO CHANGE DEFAULTS', reply=True, delete_after=45)

    async def on_message(self, message, message_type, message_context):
        pass #delete this event if you aren't going to use it.

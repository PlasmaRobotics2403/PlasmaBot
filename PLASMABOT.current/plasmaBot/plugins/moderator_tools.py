from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response
import discord

from plasmaBot import exceptions

import logging
log = logging.getLogger('discord')

class ModeratorTools(PBPlugin):
    name = 'Moderation Tools'
    globality = 'choice'

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)

    def cmd_prune(self, message, channel, user_mentions, leftover_args):
        if not self.bot.user.bot:
            messages = self.bot.get_messages(channel)

        if leftover_args[0].isdigit():
            if self.bot.user.bot:
                purge_num = min(int(leftover_args[0]), 1000)
                if number < 1:
                    return Response('Can not clear {} messages!'.format(number), reply=True, delete_after=10)

            else:

        elif leftover_args[0] == 'commands':
            if self.bot.user.bot:

            else:

        elif user_mentions:
            if self.bot.user.bot:

            else:

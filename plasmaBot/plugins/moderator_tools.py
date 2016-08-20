from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response
import discord

from plasmaBot import exceptions

import logging
log = logging.getLogger('discord')

class ModeratorTools(PBPlugin):
    name = 'Moderation Tools'
    globality = 'choice'
    help_exclude = True

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)

    def cmd_prune(self, message_context, message, channel, user_mentions, leftover_args):
        if message_context == 'server':
            if not self.bot.user.bot:
                messages = self.bot.get_messages(channel)

            if leftover_args[0].isdigit():
                if channel.permissions_for(server.me).manage_messages:
                    if self.bot.user.bot:
                        purge_num = min(int(leftover_args[0]), 99)
                        if purge_num < 1:
                            return Response('Can not clear {} messages!'.format(number), reply=True, delete_after=10)
                        else:
                            deleted_messages = await self.bot.purge_from(
                                message.channel,
                                limit=purge_num+1
                            )
                            return Response('{} Messages cleared from {}'.format(len(deleted_messages), channel.mention), reply=True, delete_after=10)
                    else:
                        deleted = 0
                        async for entry in self.bot.logs_from(channel, purge_num + 1):
                            await self.bot.delete_message(entry)
                            await asyncio.sleep(0.21) #1.21 gigawatts!  oh wait, only 0.21...  and seconds, not gigawats... :(
                            deleted += 1

                        return Response('{} Messages cleared from {}'.format(deleted, channel.mention))
                else:
                    if self.bot.config.debug:
                        print('[PB][PRUNE] Bot Needs Manage Messages Permission to Delete Messages')
                    return Response('ERROR: `Bot Needs Manage Messages Permission to Prune Messages`')

            elif leftover_args[0] == 'commands':
                if self.bot.user.bot:

                else:

            elif user_mentions:
                if self.bot.user.bot:

                else:
        else:
            return Response('Cannot Prune Messages in a Direct Message')

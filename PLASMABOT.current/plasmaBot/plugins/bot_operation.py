from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response
import discord

from plasmaBot import exceptions

import logging
log = logging.getLogger('discord')

class BotOperation(PBPlugin):
    name = 'Bot Operation Tools'
    requirements = None
    is_global = True

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)

    async def cmd_ping(self):
        """
        Usage:
            {command_prefix}ping

        Test the operation of the bot and plugin systems.
        """
        return Response('pong!', reply=True, delete_after=10)

    async def cmd_invite(self, message, message_type, server_link=None):
        """
        Usage:
            {command_prefix}invite [server_link if not bot]

        Invite the bot to a server!  Or, get the invite link if using a bot account.
        """

        if self.bot.config.allow_invites or message_type=='owner':
            if self.bot.user.bot:
                app_info = await self.bot.application_info()
                join_url = discord.utils.oauth_url(app_info.id) + '&permissions=66321471'

                return Response('Invite {} to your server! See: {}'.format(
                    self.bot.config.bot_name,
                    join_url
                ), reply=True, delete_after=30)

            try:
                if server_link:
                    await self.bot.accept_invite(server_link)
                    return Response(':thumbsup: Joined Server!', reply=True, delete_after=30)

            except:
                raise exceptions.CommandError('Invalid URL provided:\n{}\n'.format(server_link), expire_in=30)
        else:
            return Response(
                '{} is not currently accepting server invitations!'.format(self.bot.config.bot_name),
                reply=True, delete_after=30
            )

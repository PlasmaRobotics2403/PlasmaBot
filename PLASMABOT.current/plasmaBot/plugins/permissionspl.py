from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response
import discord

from plasmaBot import exceptions

import logging
log = logging.getLogger('discord')

class PermissionsPl(PBPlugin):
    name = 'Permissions'
    globality = 'all'
    help_exclude = True

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)

    async def cmd_perms(self, author, channel, server, mentioned_user, user_mentions):
        """
        Usage:
            {command_prefix}perms (@Mentioned_User) [@AnotherMentionedUser] [@YetAnotherUser] ...

        Get the permissions of a mentioned user or users
        """

        for user in user_mentions:
            perms = await self.bot.permissions.check_permissions(user, channel, server)

            if perms == 100:
                perms_message = '{} is my Owner'.format(user.mention)
            elif perms == 50:
                perms_message = '{} is a Server Administrator'.format(user.mention)
            elif perms == 45:
                perms_message = '{} holds this server\'s Administrator Role'.format(user.mention)
            elif perms == 35 and user.id == self.bot.user.id:
                perms_message = 'I am {}!'.format(self.bot.config.bot_name)
            elif perms == 35:
                perms_message = '{} holds this server\'s Moderator Role'.format(user.mention)
            elif perms == 25:
                perms_message = '{} holds this server\'s Helper Role'.format(user.mention)
            elif perms == 10:
                perms_message = '{} is a Standard User on this Server'.format(user.mention)
            elif perms == 9:
                perms_message = '{} is a Standard User on this Server.  However, Server Specific Permissions have not yet been set up on this Server'.format(user.mention)
            elif perms == 5:
                perms_message = '{} is a Standard User in this Direct Message'.format(user.mention)
            elif perms == 0:
                perms_message = '{} is a Blacklisted User on this Server'.format(user.mention)
            else:
                perms_message = '{} has permissions level {}'.format(user.mention, perms)

            perms_message = author.mention + ', ' + perms_message

            await self.bot.safe_send_message(
                channel, perms_message,
                expire_in=30 if self.bot.config.delete_messages else 0,
                also_delete=message if self.bot.config.delete_invoking else None
            )

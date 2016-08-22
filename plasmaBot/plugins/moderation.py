from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response
import discord

from plasmaBot import exceptions

import logging
log = logging.getLogger('discord')

class Moderation(PBPlugin):
    name = 'Moderation'
    globality = 'all'
    help_exclude = False

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)

    async def cmd_kick2(self, author):
        """
        Usage:
            {command_prefix}kick (UserMention) [UserMention2] [UserMention3]...

        Kick a given User or set of Users

        help_exclude
        """
        self.bot.kick(author)



    async def cmd_kick(self, auth_perms, user_mentions):
        """
        Usage:
            {command_prefix}kick (UserMention) [UserMention2] [UserMention3]...

        Kick a given User or set of Users

        help_exclude
        """
        if auth_perms >= 25:

            response = 'Sucessfully kicked '
            fail = []

            for user in user_mentions:
                try:
                    self.bot.kick(user)
                    del user_mentions[0]

                    if len(user_mentions) == 0:
                        response += user.mention + '.'
                    else:
                        response += user.mention + ' & '
                except:
                    fail += [user]
                    del user_mentions[0]

            if len(fail) != 0:
                response += ' Failed to kick '

                for user in fail:
                    del fail[0]
                    if len(fail) == 0:
                        response += user.mention + '.'
                    else:
                        response += user.mention + ' & '

            return Response(response, reply=True, delete_after=15)

        else:
            return Response(permissions_error=True)

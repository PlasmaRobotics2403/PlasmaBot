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

    async def cmd_kick(self, message, auth_perms, user_mentions):
        """
        Usage:
            {command_prefix}kick (UserMention) [UserMention2] [UserMention3]...

        Kick a given User or set of Users

        help_exclude
        """
        if auth_perms >= 25:

            users_to_kick = user_mentions
            response = ''
            num_users = len(users_to_kick)
            user_number = 0
            perms_error = []
            success_message = 'Successfully Kicked '

            for user in users_to_kick:

                user_permissions = await self.bot.permissions.check_permissions(user, message.channel, message.server)

                if user_permissions >= auth_perms:
                    perms_error = perms_error + [user]
                else:
                    try:
                        user_number = user_number + 1

                        await self.bot.kick(user)

                        if user_number != num_users:
                            success_message += user.mention + ' & '
                        else:
                            success_message += user.mention
                    except:
                        pass

            num_fail = len(perms_error)

            if num_fail < num_users:
                response = success_message
                response += '.'

            if num_fail >=1 and num_fail < num_users:
                response += " "

            if num_fail >= 1:
                response += 'Insufficient Permissions to kick '
                fail_number = 0

                for user in perms_error:
                    fail_number = fail_number + 1

                    if fail_number != num_fail:
                        response += user.mention + ' & '
                    else:
                        response += user.mention

                response += "."

            return Response(response, reply=True, delete_after=15)

        else:
            return Response(permissions_error=True)


    async def cmd_ban(self, message, auth_perms, user_mentions):
        """
        Usage:
            {command_prefix}ban (UserMention) [UserMention2] [UserMention3]...

        Ban a given User or set of Users

        help_exclude
        """
        if auth_perms >= 35:

            users_to_ban = user_mentions
            response = ''
            num_users = len(users_to_ban)
            user_number = 0
            perms_error = []
            success_message = 'Successfully Banned '

            for user in users_to_ban:

                user_permissions = await self.bot.permissions.check_permissions(user, message.channel, message.server)

                if user_permissions >= auth_perms:
                    perms_error = perms_error + [user]
                else:
                    try:
                        user_number = user_number + 1

                        await self.bot.ban(user)

                        if user_number != num_users:
                            success_message += user.mention + ' & '
                        else:
                            success_message += user.mention
                    except:
                        pass

            num_fail = len(perms_error)

            if num_fail < num_users:
                response = success_message
                response += '.'

            if num_fail >=1 and num_fail < num_users:
                response += " "

            if num_fail >= 1:
                response += 'Insufficient Permissions to ban '
                fail_number = 0

                for user in perms_error:
                    fail_number = fail_number + 1

                    if fail_number != num_fail:
                        response += user.mention + ' & '
                    else:
                        response += user.mention

                response += "."

            return Response(response, reply=True, delete_after=15)

        else:
            return Response(permissions_error=True)


    async def cmd_unban(self, message, server, auth_perms, user_mentions, leftover_args):
        """
        Usage:
            {command_prefix}unban (UserMention | Username) [UserMention] [UserName]...

        UnBan a User or Set of Users

        help_exclude
        """
        if auth_perms >= 35:
            try:
                ban_list = self.bot.get_bans(server)
            except discord.Forbidden:
                return Response(permissions_error=True)

            ban_name_list = []

            for user in ban_list:
                ban_name_list = ban_name_list + [user.name]

            for user in user_mentions:
                while user.mention in leftover_args: leftover_args.remove(user.mention) 



        else:
            return Response(permissions_error=True)

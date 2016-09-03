from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response, PBPluginConfig
import discord

from SQLiteHelper import SQLiteHelper as sq

from plasmaBot import exceptions

import logging
log = logging.getLogger('discord')


class dbt_moderation_settings(object):
    def __init__(self):
        self.columns = ["SERVER_ID", "PRESERVE_OVERRIDES", "SOFT_MUTE"]
        self.datatypes = ["TEXT PRIMARY KEY NOT NULL", "TEXT", "TEXT"]
        self.seed = []


class dbt_moderation_roles(object):
    def __init__(self):
        self.columns = ["SERVER_ID", "ROLE_MUTE", "ROLE_DEAFEN"]
        self.datatypes = ["TEXT PRIMARY KEY NOT NULL", "TEXT", "TEXT"]
        self.seed = []


class Moderation(PBPlugin):
    name = 'Moderation'
    globality = 'all'
    help_exclude = False

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)

        self.toggles = ['preserve_overrides', 'soft_mute']

        self.pl_config = PBPluginConfig(plasmaBot, 'moderation.ini', 'MODERATION', {'Files':[['moderation_db', 'The location of the moderation database', 'data/moderation']]})

        self.moderation_db = sq.Connect(self.pl_config.moderation_db)

        if not self.moderation_db.table('s_preferences').tableExists():
            initiation_glob = dbt_moderation_settings()
            self.moderation_db.table('s_preferences').init(initiation_glob)

        if not self.moderation_db.table('s_roles').tableExists():
            initiation_glob = dbt_moderation_roles()
            self.moderation_db.table('s_roles').init(initiation_glob)


    async def toggle(self, server, key):

        #Get Server Data

        moderation_settings = self.moderation_db.table('s_preferences').select("SERVER_ID", "PRESERVE_OVERRIDES", "SOFT_MUTE").where("SERVER_ID").equals(server.id).execute()

        SERVER_ID = None
        PRESERVE_OVERRIDES = None
        SOFT_MUTE = None

        for server_instance in moderation_settings:
            SERVER_ID = server_instance[0]
            PRESERVE_OVERRIDES = server_instance[1]
            SOFT_MUTE = server_instance[2]

            print(SERVER_ID)
            print(PRESERVE_OVERRIDES)
            print(SOFT_MUTE)

        try:
            server_id = int(SERVER_ID)
        except:
            server_id = None

        if isinstance( server_id, int ):
            if not (PRESERVE_OVERRIDES == 'true' or PRESERVE_OVERRIDES == 'false'):
                self.moderation_db.table('s_preferences').update("PRESERVE_OVERRIDES").setTo('true').where("SERVER_ID").equals(server.id).execute()

            if not (SOFT_MUTE == 'true' or SOFT_MUTE == 'false'):
                self.moderation_db.table('s_preferences').update("SOFT_MUTE").setTo('true').where("SERVER_ID").equals(server.id).execute()
        else:
            self.moderation_db.table('s_preferences').insert(server.id, "true", "true").into("SERVER_ID", "PRESERVE_OVERRIDES", "SOFT_MUTE")

        #Handle Keys

        if key == "preserve_overrides":

            #Invert values and save in db

            if PRESERVE_OVERRIDES == 'true':
                PRESERVE_OVERRIDES = 'false'
            elif PRESERVE_OVERRIDES == 'false':
                PRESERVE_OVERRIDES = 'true'
            else:
                PRESERVE_OVERRIDES = None

            if PRESERVE_OVERRIDES == None:
                PRESERVE_OVERRIDES = 'true'
            else:
                self.moderation_db.table('s_preferences').update("PRESERVE_OVERRIDES").setTo(PRESERVE_OVERRIDES).where("SERVER_ID").equals(server.id).execute()

            return ['SUCCESS', PRESERVE_OVERRIDES]

        elif key == 'soft_mute':

            #Invert values and sasve in db

            if SOFT_MUTE == 'true':
                SOFT_MUTE = 'false'
            elif SOFT_MUTE == 'false':
                SOFT_MUTE = 'true'
            else:
                SOFT_MUTE = None

            if SOFT_MUTE == None:
                SOFT_MUTE = 'true'
            else:
                self.moderation_db.table('s_preferences').update("SOFT_MUTE").setTo(SOFT_MUTE).where("SERVER_ID").equals(server.id).execute()

            return ['SUCCESS', SOFT_MUTE]

        else:
            return 'ERROR'


    async def get_key(self, server, key):

        #Get Server Data

        moderation_settings = self.moderation_db.table('s_preferences').select("SERVER_ID", "PRESERVE_OVERRIDES", "SOFT_MUTE").where("SERVER_ID").equals(server.id).execute()

        SERVER_ID = None
        PRESERVE_OVERRIDES = None
        SOFT_MUTE = None

        for server_instance in moderation_settings:
            SERVER_ID = server_instance[0]
            PRESERVE_OVERRIDES = server_instance[1]
            SOFT_MUTE = server_instance[2]

        try:
            server_id = int(SERVER_ID)
        except:
            server_id = None

        if isinstance( server_id, int ):
            if not (PRESERVE_OVERRIDES == 'true' or PRESERVE_OVERRIDES == 'false'):
                self.moderation_db.table('s_preferences').update("PRESERVE_OVERRIDES").setTo('true').where("SERVER_ID").equals(server.id).execute()

            if not (SOFT_MUTE == 'true' or SOFT_MUTE == 'false'):
                self.moderation_db.table('s_preferences').update("SOFT_MUTE").setTo('true').where("SERVER_ID").equals(server.id).execute()
        else:
            self.moderation_db.table('s_preferences').insert(server.id, "true", "true").into("SERVER_ID", "PRESERVE_OVERRIDES", "SOFT_MUTE")

        #Pull Key

        if key == "preserve_overrides":

            if PRESERVE_OVERRIDES == 'true':
                PRESERVE_OVERRIDES = True
            elif PRESERVE_OVERRIDES == 'false':
                PRESERVE_OVERRIDES = False
            else:
                PRESERVE_OVERRIDES = True

            return PRESERVE_OVERRIDES


        elif key == "soft_mute":

            if SOFT_MUTE == 'true':
                SOFT_MUTE = True
            elif SOFT_MUTE == 'false':
                SOFT_MUTE = False
            else:
                SOFT_MUTE = True

            return SOFT_MUTE

        else:
            return 'ERROR'


    async def setup_roles(self, server, channel): #check if bot has permissions to manage roles
        server_roles = server.roles

        self_member = server.get_member(self.bot.user.id)
        top_role = self_member.top_role
        bot_position = top_role.position

        permissions = channel.permissions_for(self_member)
        manage_roles = permissions.manage_roles

        if not manage_roles:
            return ['Error']
        else:
            mute_role = None
            defen_role = None

            server_role_entry = self.moderation_db.table('s_roles').select("SERVER_ID", "ROLE_MUTE", "ROLE_DEAFEN").where("SERVER_ID").equals(server.id).execute()


    async def cmd_kick(self, message, auth_perms, user_mentions):
        """
        Usage:
            {command_prefix}kick (UserMention) [UserMention2] [UserMention3]...

        Kick a given User or set of Users

        help_exclude
        """
        if auth_perms >= 25:

            if not user_mentions:
                return Response(send_help=True)

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

            if not user_mentions:
                return Response(send_help=True)

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

            if not user_mentions or not leftover_args:
                return Response(send_help=True)

            try:
                ban_list = await self.bot.get_bans(server)
            except discord.Forbidden:
                return Response(permissions_error=True)

            not_unbanned_list = []
            unbanned_list = []

            for user in user_mentions:
                while user.mention in leftover_args: leftover_args.remove(user.mention)

                if user in ban_list:
                    try:
                        await self.bot.unban(server, user)
                        unbanned_list = unbanned_list + [user]
                    except:
                        not_unbanned_list = not_unbanned_list + [user]
                else:
                    not_unbanned_list = not_unbanned_list + [user]

            for user in ban_list:
                if user.name in leftover_args:
                    leftover_args.remove(user.name)

                    try:
                        await self.bot.unban(server, user)
                        unbanned_list = unbanned_list + [user]
                    except:
                        not_unbanned_list = not_unbanned_list + [user]
                else:
                    pass

            response = ''
            ubl_len = len(unbanned_list)
            nbl_len = len(not_unbanned_list)
            la_len = len(leftover_args)

            if ubl_len == 0 and nbl_len == 0 and la_len == 0:
                response = 'ERROR Handling Unbans'

            if ubl_len >= 1:
                response = 'Successfully Unbanned '

                ubl_check = 0

                for user in unbanned_list:
                    ubl_check += 1

                    if ubl_check != ubl_len:
                        response += user.mention + ' & '
                    else:
                        response += user.mention

                response += '. '

            if nbl_len >= 1 or la_len >= 1:
                response = 'Failed to Unban '

                nbl_check = 0
                la_check = 0

                for user in not_unbanned_list:
                    nbl_check += 1

                    if nbl_check != nbl_len or la_len >= 1:
                        response += user.mention + ' & '
                    else:
                        response += user.mention

                for string in leftover_args:
                    la_check += 1

                    if la_check != la_len:
                        response += string + ' & '
                    else:
                        response += string

                response += '.'

            return Response(response, reply=False, delete_after=10)

        else:
            return Response(permissions_error=True)


    async def cmd_mute(self, message, server, auth_perms, user_mentions):
        """
        Usage:
            {command_prefix}mute (UserMention) [UserMention] [UserMention]...

        Mute a user or set of users

        help_exclude
        """
        if auth_perms >= 25:

            if not user_mentions:
                return Response(send_help=True)

            server_preserve_overrides = await self.get_key(server, 'preserve_overrides')

            channel_list = server.channels

            user_count = len(user_mentions)
            check_count = 0

            response = 'Muted '

            for user in user_mentions:
                user_permissions = await self.bot.permissions.check_permissions(user, message.channel, message.server)

                if user_permissions >= auth_perms:
                    return Response(permissions_error=True)

                check_count += 1

                for channel in channel_list:
                    try:
                        if not server_preserve_overrides == True:
                            overwrite = channel.overwrites_for(user)
                        else:
                            overwrite = discord.PermissionOverwrite()

                        overwrite.send_messages = False
                        await self.bot.edit_channel_permissions(channel, user, overwrite)
                    except:
                        self.bot.safe_send_message(message.channel, 'Error muting {} in {}'.format(user.mention, channel.mention), expire_in=10)

                if check_count != user_count:
                    response += user.mention + ' & '
                else:
                    response += user.mention

            response += '.'

            return Response(response, reply=False, delete_after=10)

        else:
            return Response(permissions_error=True)

    async def cmd_unmute(self, message, server, auth_perms, user_mentions):
        """
        Usage:
            {command_prefix}unmute (UserMention) [UserMention] [UserMention]...

        Unmute a user or set of users

        help_exclude
        """
        if auth_perms >= 25:

            if not user_mentions:
                return Response(send_help=True)

            server_preserve_overrides = await self.get_key(server, 'preserve_overrides')

            channel_list = server.channels
            user_count = len(user_mentions)
            check_count = 0

            response = 'Unmuted '

            for user in user_mentions:
                user_permissions = await self.bot.permissions.check_permissions(user, message.channel, message.server)

                if user_permissions >= auth_perms:
                    return Response(permissions_error=True)

                check_count += 1

                for channel in channel_list:
                    try:
                        if not server_preserve_overrides == True:
                            overwrite = channel.overwrites_for(user)
                        else:
                            overwrite = discord.PermissionOverwrite()

                        overwrite.send_messages = None
                        await self.bot.edit_channel_permissions(channel, user, overwrite)
                    except:
                        self.bot.safe_send_message(message.channel, 'Error unmuting {} in {}'.format(user.mention, channel.mention), expire_in=10)

                if check_count != user_count:
                    response += user.mention + ' & '
                else:
                    response += user.mention

            response += '.'

            return Response(response, reply=False, delete_after=10)

        else:
            return Response(permissions_error=True)


    async def cmd_deafen(self, message, server, auth_perms, user_mentions):
        """
        Usage:
            {command_prefix}deafen (UserMention) [UserMention] [UserMention]...

        Deafen a user or set of users

        help_exclude
        """
        if auth_perms >= 35:

            if not user_mentions:
                return Response(send_help=True)

            server_preserve_overrides = await self.get_key(server, 'preserve_overrides')

            channel_list = server.channels

            user_count = len(user_mentions)
            check_count = 0

            response = 'Deafened '

            for user in user_mentions:
                user_permissions = await self.bot.permissions.check_permissions(user, message.channel, message.server)

                if user_permissions >= auth_perms:
                    return Response(permissions_error=True)

                check_count += 1

                for channel in channel_list:
                    try:
                        if not server_preserve_overrides == True:
                            overwrite = channel.overwrites_for(user)
                        else:
                            overwrite = discord.PermissionOverwrite()

                        overwrite.send_messages = False
                        overwrite.read_messages = False
                        await self.bot.edit_channel_permissions(channel, user, overwrite)
                    except:
                        self.bot.safe_send_message(message.channel, 'Error deafening {} in {}'.format(user.mention, channel.mention), expire_in=10)

                if check_count != user_count:
                    response += user.mention + ' & '
                else:
                    response += user.mention

            response += '.'

            return Response(response, reply=False, delete_after=10)

        else:
            return Response(permissions_error=True)


    async def cmd_undeafen(self, message, server, auth_perms, user_mentions):
        """
        Usage:
            {command_prefix}undeafen (UserMention) [UserMention] [UserMention]...

        Undeafen a user or set of users

        help_exclude
        """
        if auth_perms >= 35:

            if not user_mentions:
                return Response(send_help=True)

            server_preserve_overrides = await self.get_key(server, 'preserve_overrides')

            channel_list = server.channels
            user_count = len(user_mentions)
            check_count = 0

            response = 'Undeafened '

            for user in user_mentions:
                user_permissions = await self.bot.permissions.check_permissions(user, message.channel, message.server)

                if user_permissions >= auth_perms:
                    return Response(permissions_error=True)

                check_count += 1

                for channel in channel_list:
                    try:
                        if not server_preserve_overrides == True:
                            overwrite = channel.overwrites_for(user)
                        else:
                            overwrite = discord.PermissionOverwrite()

                        overwrite.send_messages = None
                        overwrite.read_messages = None
                        await self.bot.edit_channel_permissions(channel, user, overwrite)
                    except:
                        self.bot.safe_send_message(message.channel, 'Error Undeafened {} in {}'.format(user.mention, channel.mention), expire_in=10)

                if check_count != user_count:
                    response += user.mention + ' & '
                else:
                    response += user.mention

            response += '.'

            return Response(response, reply=False, delete_after=10)

        else:
            return Response(permissions_error=True)




    async def on_server_join(self, server):
        moderation_settings = self.moderation_db.table('s_preferences').select("SERVER_ID", "PRESERVE_OVERRIDES", "SOFT_MUTE").where("SERVER_ID").equals(server.id).execute()

        SERVER_ID = None
        PRESERVE_OVERRIDES = None
        SOFT_MUTE = None

        for server_instance in moderation_settings:
            SERVER_ID = server_instance[0]
            PRESERVE_OVERRIDES = server_instance[1]
            SOFT_MUTE = server_instance[2]

        try:
            server_id = int(SERVER_ID)
        except:
            server_id = None

        if isinstance( server_id, int ):
            if not (PRESERVE_OVERRIDES == 'true' or PRESERVE_OVERRIDES == 'false'):
                self.moderation_db.table('s_preferences').update("PRESERVE_OVERRIDES").setTo('true').where("SERVER_ID").equals(server.id).execute()

            if not (SOFT_MUTE == 'true' or SOFT_MUTE == 'false'):
                self.moderation_db.table('s_preferences').update("SOFT_MUTE").setTo('true').where("SERVER_ID").equals(server.id).execute()
        else:
            self.moderation_db.table('s_preferences').insert(server.id, "true", "true").into("SERVER_ID", "PRESERVE_OVERRIDES", "SOFT_MUTE")

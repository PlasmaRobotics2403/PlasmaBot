from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response, PBPluginConfig
import discord
import asyncio

from SQLiteHelper import SQLiteHelper as sq

from plasmaBot import exceptions

import logging
log = logging.getLogger('discord')


# Database Default Classes
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
    help_exclude = True

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)

        self.toggles = ['preserve_overrides', 'soft_mute']

        self.pl_config = PBPluginConfig(plasmaBot, 'moderation.ini', 'MODERATION', {'Files':[['moderation_db_location', 'The location of the moderation database', 'data/moderation']]})

        self.moderation_db = sq.Connect(self.pl_config.moderation_db_location)

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
                self.moderation_db.table('s_preferences').update("SOFT_MUTE").setTo('false').where("SERVER_ID").equals(server.id).execute()
        else:
            self.moderation_db.table('s_preferences').insert(server.id, "true", "false").into("SERVER_ID", "PRESERVE_OVERRIDES", "SOFT_MUTE")

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
                SOFT_MUTE = 'false'
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
                self.moderation_db.table('s_preferences').update("SOFT_MUTE").setTo('false').where("SERVER_ID").equals(server.id).execute()
        else:
            self.moderation_db.table('s_preferences').insert(server.id, "true", "false").into("SERVER_ID", "PRESERVE_OVERRIDES", "SOFT_MUTE")

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
                SOFT_MUTE = False

            return SOFT_MUTE

        else:
            return 'ERROR'


    async def get_roles(self, server):
        server_roles = server.roles

        self_member = server.get_member(self.bot.user.id)
        top_role = self_member.top_role
        role_position = top_role.position

        permissions = server.get_channel(server.id).permissions_for(self_member)
        manage_roles = permissions.manage_roles

        m_overwrite = discord.PermissionOverwrite()
        m_overwrite.send_messages = False
        d_overwrite = discord.PermissionOverwrite()
        d_overwrite.send_messages = False
        d_overwrite.read_messages = False

        if not manage_roles:
            return [None, None]
        else:
            mute_role = None
            defen_role = None

            server_role_entry = self.moderation_db.table('s_roles').select("ROLE_MUTE", "ROLE_DEAFEN").where("SERVER_ID").equals(server.id).execute()

            everyone_permissions = None
            role_mute = 'DNE'
            role_deafen = 'DNE'
            role_return = [None, None, manage_roles]

            for server_entry in server_role_entry:
                role_mute = server_entry[0]
                role_deafen = server_entry[1]

            if role_mute and role_deafen:
                for role in server.roles:
                    if role.position == 0:
                        everyone_permissions = role.permissions

                    if role.id == role_mute:
                        role_return[0] = role

                    if role.id == role_deafen:
                        role_return[1] = role


            if role_return[0] and role_return[1]:
                return role_return

            if role_mute == 'DNE' and role_deafen == 'DNE':
                assign_db = True
            else:
                assign_db = False

            if role_return[0] == None:
                mute_perms = everyone_permissions
                mute_perms.send_messages = False

                role_return[0] = await self.bot.create_role(server, name='PB-Muted', mentionable=False, permissions=mute_perms)
                await self.bot.move_role(server, role_return[0], role_position)

                if not assign_db:
                    self.moderation_db.table('s_roles').update("ROLE_MUTE").setTo(role_return[0].id).where("SERVER_ID").equals(server.id).execute()

                for channel in server.channels:
                    await self.bot.edit_channel_permissions(channel, role_return[0], overwrite=m_overwrite)

            if role_return[1] == None:
                deafen_perms = everyone_permissions
                deafen_perms.send_messages = False
                deafen_perms.read_messages = False

                role_return[1] = await self.bot.create_role(server, name='PB-Deafened', mentionable=False, permissions=deafen_perms)
                await self.bot.move_role(server, role_return[1], role_position)

                if not assign_db:
                    self.moderation_db.table('s_roles').update("ROLE_DEAFEN").setTo(role_return[1].id).where("SERVER_ID").equals(server.id).execute()

                for channel in server.channels:
                    await self.bot.edit_channel_permissions(channel, role_return[1], overwrite=d_overwrite)

            if assign_db:
                self.moderation_db.table('s_roles').insert(server.id, role_return[0].id, role_return[1].id).into("SERVER_ID", "ROLE_MUTE", "ROLE_DEAFEN")

            return role_return


    # Plugin Commands

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
            server_soft_mute = await self.get_key(server, 'soft_mute')

            user_count = len(user_mentions)
            check_count = 0

            response = 'Muted '

            if server_soft_mute:
                server_roles = await self.get_roles(server)

                if server_roles[0] == None and server_roles[1] == None:
                    return Response(permissions_error=True)

                mute_role = server_roles[0]

            for user in user_mentions:
                user_permissions = await self.bot.permissions.check_permissions(user, message.channel, message.server)

                if user_permissions >= auth_perms:
                    return Response(permissions_error=True)

                check_count += 1

                if server_soft_mute:

                    if not server_roles[2]:
                        return Response(permissions_error=True)

                    await self.bot.add_roles(user, mute_role)

                else:
                    for channel in server.channels:
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
            server_soft_mute = await self.get_key(server, 'soft_mute')

            user_count = len(user_mentions)
            check_count = 0

            response = 'Unmuted '

            if server_soft_mute:
                server_roles = await self.get_roles(server)

                if server_roles[0] == None and server_roles[1] == None:
                    return Response(permissions_error=True)

                mute_role = server_roles[0]

            for user in user_mentions:
                user_permissions = await self.bot.permissions.check_permissions(user, message.channel, message.server)

                if user_permissions >= auth_perms:
                    return Response(permissions_error=True)

                check_count += 1

                if server_soft_mute:

                    if not server_roles[2]:
                        return Response(permissions_error=True)

                    await self.bot.remove_roles(user, mute_role)

                else:
                    for channel in server.channels:
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
            server_soft_mute = await self.get_key(server, 'soft_mute')

            user_count = len(user_mentions)
            check_count = 0

            response = 'Deafened '

            if server_soft_mute:
                server_roles = await self.get_roles(server)

                if server_roles[0] == None and server_roles[1] == None:
                    return Response(permissions_error=True)

                deafen_role = server_roles[1]

            for user in user_mentions:
                user_permissions = await self.bot.permissions.check_permissions(user, message.channel, message.server)

                if user_permissions >= auth_perms:
                    return Response(permissions_error=True)

                check_count += 1

                if server_soft_mute:

                    if not server_roles[2]:
                        return Response(permissions_error=True)

                    await self.bot.add_roles(user, deafen_role)

                else:
                    for channel in server.channels:
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
            server_soft_mute = await self.get_key(server, 'soft_mute')

            user_count = len(user_mentions)
            check_count = 0

            response = 'Undeafened '

            if server_soft_mute:
                server_roles = await self.get_roles(server)

                if server_roles[0] == None and server_roles[1] == None:
                    return Response(permissions_error=True)

                deafen_role = server_roles[1]

            for user in user_mentions:
                user_permissions = await self.bot.permissions.check_permissions(user, message.channel, message.server)

                if user_permissions >= auth_perms:
                    return Response(permissions_error=True)

                check_count += 1

                if server_soft_mute:

                    if not server_roles[2]:
                        return Response(permissions_error=True)

                    await self.bot.remove_roles(user, deafen_role)

                else:
                    for channel in server.channels:
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


    async def cmd_prune(self, message, channel, server, bot_member, author, auth_perms, user_mentions, prune_number=50, prune_type=None):
        """
        Usage:
            {command_prefix}prune (number) [Prune Type]

        Prunes (number) Messages from the chat

        help_exclude
        """
        if auth_perms >= 35:

            # Check if prune_number is a number
            try:
                float(prune_number)
                prune_number = min(int(prune_number) + 1, 1000) # Set prune_number to 1000 if greater than 1000.  Add 1 to the number to counteract the initiation message
            except:
                return Response("The number of messages to prune must be a number.", reply=True, delete_after=15)

            delete_invokes = True
            manage_messages = channel.permissions_for(bot_member).manage_messages

            def is_bot_command(possible_command_fire):
                if possible_command_fire.content.strip().startswith(self.bot.config.prefix):

                    possible_command_handler, *args = possible_command_fire.content.strip().split()
                    possible_command_handler = possible_command_handler[len(self.bot.config.prefix):].lower().strip()

                    possible_command_info = self.bot.plugin_db.table('commands').select("PLUGIN_NAME").where("COMMAND_KEY").equals(possible_command_handler).execute()

                    possible_plugin_name = None

                    for possible_command in possible_command_info:
                        possible_plugin_name = possible_command[0]

                    if possible_plugin_name:
                        return True
                    else:
                        return False
                elif possible_command_fire.author == bot_member:
                    return True
                else:
                    return False

            def check(check_message): # Modify this function to provide more than just bot messages.
                if prune_type == None or prune_type == 'all':
                    if manage_messages:
                        return True
                    else:
                        if prune_type == 'all':
                            return Response(permissions_error=True)
                        else:
                            if not self.bot.user.bot:
                                if check_message.author == self.bot.user:
                                    return True
                                else:
                                    return False
                            else:
                                return Response(permissions_error=True)
                elif prune_type == 'commands':
                    return is_bot_command(check_message)
                elif user_mentions:
                    if check_message.author in user_mentions:
                        return True
                    else:
                        return False
                else:
                    return False

            if self.bot.user.bot:
                if manage_messages:
                    deleted = await self.bot.purge_from(channel, check=check, limit=prune_number)

                    num_messages = len(deleted)

                    if check(message):
                        num_messages += -1

                    if num_messages <= 1:
                        message_suffix = ''
                    else:
                        message_suffix = 's'

                    return Response('Pruned {} message{}.'.format(num_messages, message_suffix), delete_after=5)
                else:
                    return Response(permissions_error=True)

            deleted = 0
            async for entry in self.bot.logs_from(channel, prune_number, before=message):
                should_delete = check(entry)

                if should_delete:
                    await self.bot.safe_delete_message(entry)
                    deleted += 1
                    await asyncio.sleep(0.21)

                if check(message):
                    deleted += -1

                if deleted <= 1:
                    message_suffix = ''
                else:
                    message_suffix = 's'

            return Response('Purged {} message{}.'.format(deleted, message_suffix), delete_after=55)
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

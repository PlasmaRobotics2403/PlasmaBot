from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response
import discord

import copy

from plasmaBot import exceptions

import logging
log = logging.getLogger('discord')

class DefaultPlugin(PBPlugin):
    name = 'Default Bot Operation'
    globality = 'all'
    help_exclude = False

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)

    async def cmd_help(self, help_command=None):
        """
        Usage:
            {command_prefix}help [command]

        Get a List of Bot Commands, or get help about a given Command.
        """
        if help_command:
            help_command = help_command.lower().strip()
            raw_commands_return = self.bot.plugin_db.table('commands').select("PLUGIN_NAME", "COMMAND_USAGE", "COMMAND_DESCRIPTION").where("COMMAND_KEY").equals(help_command).execute()

            cmd_plugin = ''
            cmd_usage = ''
            cmd_description = ''

            for command_data in raw_commands_return:
                cmd_plugin = command_data[0]
                cmd_usage = command_data[1]
                cmd_description = command_data[2]

            if cmd_plugin == '':
                return

            raw_plugin_return = self.bot.plugin_db.table('plugins').select("FANCY_NAME").where("PLUGIN_NAME").equals(cmd_plugin).execute()
            for item in raw_plugin_return:
                cmd_plugin = item[0]

            help_response = '```Usage for ' + self.bot.config.prefix + help_command
            help_response += ' (' + cmd_plugin + '):'
            help_response += '\n     '
            help_response += cmd_usage + '\n\n'
            help_response += cmd_description + '```'

        else:
            plugins_commands_dict = {}
            raw_commands_return = self.bot.plugin_db.table('commands').select("COMMAND_KEY", "PLUGIN_NAME", "COMMAND_DESCRIPTION", "HELP_EXCLUDE").execute()

            for command in raw_commands_return:
                command_key = command[0]
                plugin = command[1]
                description = command[2]
                exclude = command[3]

                if not exclude == "YES":
                    cmd_entry = command_key + ": " + description
                    if not plugin in plugins_commands_dict:
                        plugins_commands_dict[plugin] = [cmd_entry]
                    else:
                        plugins_commands_dict[plugin] = plugins_commands_dict[plugin] + [cmd_entry]

            help_response = "**{}'s Commands:**```\n".format(self.bot.config.bot_name)

            for plugin, commands in plugins_commands_dict.items():
                raw_plugin_return = self.bot.plugin_db.table('plugins').select("FANCY_NAME").where("PLUGIN_NAME").equals(plugin).execute()

                for item in raw_plugin_return:
                    fancy_name = item[0]

                help_response = help_response + fancy_name + '\n'

                for command in commands:
                    help_response = help_response + ' • ' + self.bot.config.prefix + command + '\n'

            help_response = help_response + '```'

        return Response(help_response, reply=False, delete_after=60)

    async def cmd_setperms(self, message, channel, server, author, auth_perms, raw_role_mentions):
        """
        Usage:
            {command_prefix}setperms (Administrator_Rank_Mention) (Moderator_Rank_Mention) (Helper_Rank_Mention) (Blacklisted_Rank_Mention)

        Sets the Permissions Ranks for the Server.  Author must have the Manage Server Permission.

        help_exclude
        """

        if channel.permissions_for(author).manage_server or auth_perms >= 100:
            if len(raw_role_mentions) == 4:
                admin_role_id = raw_role_mentions[0]
                mod_role_id = raw_role_mentions[1]
                helper_role_id = raw_role_mentions[2]
                black_role_id = raw_role_mentions[3]

                self.bot.permissions.set_server_permissions(server, admin_role_id, mod_role_id, helper_role_id, black_role_id)

                return Response("Server Permissions Ranks have been updated succesfully! :+1:\n\n_Administrator Role_: <@&{}>\n_Moderator Role_: <@&{}>\n_Helper Role_: <@&{}>\n_Blacklisted Role_: <@&{}>".format(admin_role_id, mod_role_id, helper_role_id, black_role_id))
            else:
                return Response(
                    send_help=True,
                    help_message='Invalid Number of Ranks Mentioned' if role_mentions else None)
        else:
            return Response("You must have the Manage Server Permission in order to set Server Permissions", reply=True, delete_after=45)

    async def cmd_perms(self, author, channel, server, user_mentions):
        """
        Usage:
            {command_prefix}perms (@Mentioned_User) [@AnotherMentionedUser] [@YetAnotherUser] ...

        Get the permissions of a mentioned user or users.

        help_exclude
        """
        if user_mentions:
            for user in user_mentions:
                perms = await self.bot.permissions.check_permissions(user, channel, server)

                if perms == 100:
                    perms_message = '{} is my Owner'.format(user.mention)
                elif perms == 50:
                    perms_message = '{} is a Server Administrator'.format(user.mention)
                elif perms == 45:
                    perms_message = '{} holds this server\'s Administrator Role'.format(user.mention)
                elif perms == 30 and user.id == self.bot.user.id:
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
        else:
            return Response(send_help=True)

    async def cmd_ping(self):
        """
        Usage:
            {command_prefix}ping

        Test the operation of the bot and plugin systems.
        """
        return Response('pong!', reply=True, delete_after=10)

    async def cmd_invite(self, message, auth_perms, server_link=None):
        """
        Usage:
            {command_prefix}invite [server_link if not bot]

        Invite the bot or get it's Invite Link!
        """

        if self.bot.config.allow_invites or auth_perms >= 100:
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

    async def cmd_id(self, author, user_mentions):
        """
        Usage:
            {command_prefix}id

        Get's a User's ID
        """
        if not user_mentions:
            return Response('your ID is `{}`'.format(author.id), reply=True, delete_after=30)
        else:
            user = user_mentions[0]
            return Response("<@{0}>'s ID is `{0}`".format(user.id), reply=False, delete_after=30)

    async def cmd_say(self, channel, message, author, auth_perms, message_context, leftover_args):
        """
        Usage:
            {command_prefix}say (message)

        Bot will respond with your Message
        """
        silent = False
        sticky = False
        delete = False

        if auth_perms >= 100:
            if 'silent' in leftover_args or 'sticky' in leftover_args or 'delete' in leftover_args:
                if message_context == 'direct':
                    srange = range(0,1)
                else:
                    srange = range(0,2)
                for keycheck in srange:
                    leftover_args = leftover_args + ['']
                    if leftover_args[0] == 'delete' and not message_context == 'direct':
                        delete = True
                        del leftover_args[0]
                    if leftover_args[0] == 'silent':
                        silent = True
                        del leftover_args[0]
                    if leftover_args[0] == 'sticky':
                        sticky = True
                        del leftover_args[0]

        message_to_send = ''
        for message_segment in leftover_args:
            message_to_send += message_segment + ' '

        if delete:
            await self.bot.safe_delete_message(message)
        else:
            pass

        if leftover_args[0] == '':
            return

        if not silent:
            message_to_send = '<@{}>, '.format(author.id) + message_to_send
        else:
            pass

        await self.bot.safe_send_message(
            channel, message_to_send,
            expire_in=15 if not sticky else 0)

    async def cmd_sudo(self, message, channel, server, auth_perms, user_mentions, leftover_args):
        """
        Usage:
            {command_prefix}sudo (user_mention) (command_sequence_to_be_ran)

        Run a command as another user.  Requires Owner Permissions (100)

        help_exclude
        """
        if auth_perms >= 35:
            if user_mentions:
                sudo_user = user_mentions[0]
                sudo_perms = await self.bot.permissions.check_permissions(sudo_user, channel, server)
                if auth_perms > sudo_perms or auth_perms >= 100:
                    if leftover_args[0] == sudo_user.mention:
                        sudo_string = self.bot.config.prefix + 'sudo '
                        sudo_string += sudo_user.mention
                        sudo_length = len(sudo_string)
                        sudo_message = copy.copy(message)
                        sudo_message.content = message.content[sudo_length:].strip()
                        sudo_message.author = sudo_user
                        del sudo_message.mentions[0]
                        del sudo_message.raw_mentions[0]

                        await self.bot.on_message(sudo_message)
                        return
                else:
                    return Response(permissions_error=True)
            else:
                return Response(send_help=True)
        else:
            return Response(permissions_error=True)

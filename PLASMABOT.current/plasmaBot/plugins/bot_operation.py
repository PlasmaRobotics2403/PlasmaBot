from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response
import discord

from plasmaBot import exceptions

import logging
log = logging.getLogger('discord')

class BotOperation(PBPlugin):
    name = 'Standard Commands'
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

            plugin = ''
            usage = ''
            description = ''

            for command in raw_commands_return:
                plugin = command[0]
                usage = command[1]
                description = command[2]

            if plugin == '':
                return

            help_response = 'Usage for _'
            help_response += self.bot.config.prefix + help_command
            help_response += '_:\n     ' + usage + '\n\n'
            help_response += description

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

        Invite the bot or get it's Invite Link!
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

    async def cmd_type(self, server, user_mentions):
        """
        Usage:
            {command_prefix}type

        Get's the type of the server.id object
        """
        return Response('server.id is type {}'.format(type(server.id)), reply=True, delete_after=30)

    async def cmd_say(self, channel, message, author, message_type, leftover_args):
        """
        Usage:
            {command_prefix}say (message)

        Bot will respond with your Message
        """
        silent = False
        sticky = False
        delete = False

        if message_type == 'owner':
            if 'silent' in leftover_args or 'sticky' in leftover_args or 'delete' in leftover_args:
                for keycheck in range(1,3):
                    if leftover_args[0] == 'delete':
                        print('tdelete')
                        delete = True
                        del leftover_args[0]
                    if leftover_args[0] == 'silent':
                        print('tsilent')
                        silent = True
                        del leftover_args[0]
                    if leftover_args[0] == 'sticky':
                        print('tstick')
                        sticky = True
                        del leftover_args[0]

        message_to_send = ''
        for message_segment in leftover_args:
            message_to_send += message_segment + ' '

        if not sticky:
            print('not sticky')
        else:
            print('sticky')

        if delete:
            print('deleted')
            await self.bot.safe_delete_message(message)
        else:
            pass

        if not silent:
            print('not silent')
            message_to_send = '<@{}>, '.format(author.id) + message_to_send
        else:
            print('silent')

        await self.bot.safe_send_message(
            channel, message_to_send,
            expire_in=15 if not sticky else 0)

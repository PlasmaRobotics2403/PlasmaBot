import os
import sys
import time
import shutil
import traceback
import logging
import asyncio

import discord

from SQLiteHelper import SQLiteHelper as sq

from . import exceptions

from plasmaBot.config import Config, ConfigDefaults
from plasmaBot.permissions import Permissions
from plasmaBot.plugin import PBPluginManager, Response, PBPluginMeta, PBPlugin

from plasmaBot.defaults.database_tables import dbt_plugins, dbt_commands, dbt_server

from plasmaBot.plugins.bot_operation import BotOperation
from plasmaBot.plugins.TBA import TBAPlugin
from plasmaBot.plugins.moderation import Moderation

# Logging setup
logger = logging.getLogger('discord')

class PlasmaBot(discord.Client):
    def __init__(self, shutdown_operator):
        super().__init__()

        self.version = '3.0.3-BETA-1'
        self.shutdown_state = shutdown_operator

        print('--------------------------------------------------------\n')
        print('[PB] Loading PlasmaBot Configuration...\n')

        self.config = Config()

        self.permissions = Permissions(self.config.permissions_db, self)

        print("[PB][CONFIG] Currently Running PlasmaBot v{0}".format(self.version))
        print('[PB][CONFIG] Name is ({})'.format(self.config.bot_name))
        print('[PB][CONFIG] Prefix is ({})\n'.format(self.config.prefix))

        self.message_list = {}

        self.plugin_db = sq.Connect(self.config.plugin_db)
        self.plugin_db_connection = self.plugin_db.getConn()
        self.plugin_db_cursor = self.plugin_db_connection.cursor()

        # Kill old instances of Plugin and Command Tables, to repopulate based on currently enabled plugins
        self.plugin_db_cursor.execute('DROP TABLE IF EXISTS plugins')
        self.plugin_db_cursor.execute('DROP TABLE IF EXISTS commands')

        # Set Up Plugin and Command Databases
        table_raw_plugins = dbt_plugins()
        self.plugin_db.table('plugins').init(table_raw_plugins)
        table_raw_cmd = dbt_commands()
        self.plugin_db.table('commands').init(table_raw_cmd)

        if not self.plugin_db.table('servers').tableExists():
            table_raw_servers = dbt_server()
            self.plugin_db.table('servers').init(table_raw_servers)

        # Load Plugins, and add their commands and information to self.plugin_db
        self.plugin_manager = PBPluginManager(self)
        self.plugin_manager.load_all()

    def run(self):
        try:
            self.loop.run_until_complete(self.start(*self.config.auth))
        except discord.errors.LoginFailure:

            raise exceptions.HelpfulError(
                "Bot cannot login, bad credentials.",
                "Fix your Email or Password or Token in the options file.  "
                "Remember that each field should be on their own line.")

    def shutdown(self):
        try:
            self.loop.run_until_complete(self.logout())
        except: # Can be ignored
            pass

        self.plugin_db_connection.close()

        pending = asyncio.Task.all_tasks()
        gathered = asyncio.gather(*pending)

        try:
            gathered.cancel()
            self.loop.run_until_complete(gathered)
            gathered.exception()
        except: # Can be ignored
            pass

    async def get_plugins(self, server=None):
        plugins = await self.plugin_manager.get_all(server)
        return plugins

    async def on_ready(self):
        print("\n\nConnected!\n")

        if len(self.servers) < 16:
            print("Current Servers:")
            [print(" - " + server.name) for server in self.servers]
            print()
        else:
            print("Currently on {} servers".format(len(self.servers)))


        if '{server_count}' in self.config.bot_game:
            self.config.bot_game_compiled = self.config.bot_game.replace('{server_count}', str(len(self.servers)))

        self.game = discord.Game(name=self.config.bot_game_compiled, url='https://www.twitch.tv/discordapp', type=1)
        await self.change_status(self.game)

        enabled_plugins = await self.get_plugins()
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_ready())

    async def on_server_join(self, server):
        if self.config.debug:
            print('[PB][SERVER] Joined {} ({})'.format(
                server.name,
                server.owner.name
            ))

        s_owner = ''
        server_permissions_return = self.permissions.perm_db.table('servers').select("OWNER_ID").where("SERVER_ID").equals(server.id).execute()
        for row in server_permissions_return:
            s_owner = row[0]

        server_welcome_message = 'Hello {}!\n\n'.format(server.owner.mention)
        server_welcome_message += 'I am {}, a Discord Moderation and Utility Bot!\n'.format(self.config.bot_name)
        server_welcome_message += 'I work like most bots, although there are some things that you should probably know when setting me up on your server.  My command prefix is {}, and you can use `{}help` to get a list of publically available commands on your server.\n\n'.format(self.config.prefix, self.config.prefix)
        server_welcome_message += 'There are also many commands that require advanced permissions on your server.'

        if s_owner == '':
            server_welcome_message += ' These advanced permissions need to be set up on your server through the use of the `{}setperms` command, which can only be used by the server owner or a holder of the Administrator Permission.  To use the `{}setperms` command, four roles must be set up on your server.  Those include an \'Administrator\' Role, a \'Moderator\' Role, a \'Helper\' Role, and a \'Blacklisted\' Role.  These roles can be named anything you want, but must have `@Mention` turned on, as they will be activated via the `{}setperms` command via mentioning each role as seen below:\n'.format(self.config.prefix, self.config.prefix, self.config.prefix)
            server_welcome_message += '    `{}setperms @AdministratorRole @ModeratorRole @HelperRole @BlacklistedRole`\n'.format(self.config.prefix)
            server_welcome_message += ' This will give holders of these roles access to certain higher-level commands such as `{}kick`.'.format(self.config.prefix)
        elif self.config.debug:
            server_welcome_message += 'These have already been set up on this server.  To change or modify the defined roles, use `{}help setperms` or check the original message!'.format(self.config.prefix)

        server_welcome_message_part_2 = '_Higher Level Commands List:_\n```'
        server_welcome_message_part_2 += 'Helper+:\n • {prefix}kick [list_of_user_mentions]\n • {prefix}mute [list_of_user_mentions]\n • {prefix}unmute [list_of_user_mentions]\nModerator+: • {prefix}ban [list_of_user_mentions]\n • {prefix}unban [list_of_user_names]\n • {prefix}deafen [list_of_user_mentions]\n • {prefix}undeafen [list_of_user_mentions]\n'.format(prefix=self.config.prefix)
        server_welcome_message_part_2 += '```'

        await self.safe_send_message(server.owner, server_welcome_message)
        await self.safe_send_message(server.owner, server_welcome_message_part_2)

        if '{server_count}' in self.config.bot_game:
            self.config.bot_game_compiled = self.config.bot_game.replace('{server_count}', str(len(self.servers)))
            self.game = discord.Game(name=self.config.bot_game_compiled, url='https://www.twitch.tv/discordapp', type=1)
            await self.change_status(self.game)

        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_server_join(server))

    async def on_server_remove(self, server):
        if self.config.debug:
            print('[PB][SERVER] Left {} ({})'.format(
                server.name,
                server.owner.name
            ))

        if '{server_count}' in self.config.bot_game:
            self.config.bot_game_compiled = self.config.bot_game.replace('{server_count}', str(len(self.servers)))
            self.game = discord.Game(name=self.config.bot_game_compiled, url='https://www.twitch.tv/discordapp', type=1)
            await self.change_status(self.game)

        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_server_remove(server))

    def get_messages(self, channelID):
        if not str(channelID) in self.message_list:
            self.message_list[str(channelID)] = []
        else:
            return self.message_list[str(channelID)]

    def store_messages(self, channelID, message):
        if not  str(channelID) in self.message_list:
            self.message_list[str(channelID)] = []

        message_list = [message] + self.get_messages(channelID)

        self.message_list[str(channelID)] = message_list

    async def _wait_delete_msg(self, message, delay):
        await asyncio.sleep(delay)
        await self.safe_delete_message(message)

    async def safe_send_message(self, dest, content, *, tts=False, expire_in=0, also_delete=None):
        msg = None
        try:
            msg = await self.send_message(dest, content, tts=tts)

            if msg and expire_in:
                asyncio.ensure_future(self._wait_delete_msg(msg, expire_in))

            if also_delete and isinstance(also_delete, discord.Message):
                asyncio.ensure_future(self._wait_delete_msg(also_delete, expire_in))

        except discord.Forbidden:
            if self.config.debug:
                print('[PB][PERMISSIONS] Cannot send message to {0}, no permission'.format(dest.name))

        except discord.NotFound:
            if self.config.debug:
                print('[PB][CHANNEL] Cannot send message to {0}, channel does not exist'.format(dest.name))

        return msg

    async def safe_delete_message(self, message):
        try:
            return await self.delete_message(message)

        except discord.Forbidden:
            if self.config.debug:
                print('[PB][PERMISSIONS] Cannot delete message "{0}", no permission'.format(message.clean_content))

        except discord.NotFound:
            if self.config.debug:
                print('[PB][CHANNEL] Cannot send message to {0}, channel does not exist'.format(message.clean_content))

    async def safe_edit_message(self, message, new, *, send_if_fail=False):
        try:
            return await self.edit_message(message, new)

        except discord.NotFound:
            if send_if_fail:
                if self.config.debug:
                    print('[PB][EDIT] Cannot Edit Message "{0}", sending instead'.format(message.clean_content))
                return await self.safe_send_message(message.channel, new)
            else:
                if self.config.debug:
                    print('[PB][EDIT] Cannot Edit Message "{0}", message not found'.format(message.clean_content))

    async def send_typing(self, destination):
        try:
            return await super().send_typing(destination)
        except discord.Forbidden:
            if self.config.debug_mode:
                print("[PB][PERMISSIONS] Could not send typing to %s, no permssion" % destination)

    async def on_message(self, message):

        auth_perms = await self.permissions.check_permissions(message.author, message.channel, None)

        message_type = None

        if message.author.id == self.user.id:
            message_type = 'self'
        elif auth_perms >= 100:
            message_type = 'owner'
        elif message.author.bot:
            message_type = 'bot'
        else:
            message_type = 'user'

        message_context = None
        message_location = " | "

        if message.server:
            message_context = 'server'
            message_location += message.server.name + " #" + message.channel.name
        else:
            message_context = 'direct'
            message_location += "Direct Message"

        if message.content.strip().startswith(self.config.prefix):
            message_is_command = True
            cmd_message = '[COMMAND]'
            if auth_perms == 0:
                cmd_message += '[BLACKLISTED]'
        else:
            message_is_command = False
            cmd_message = ''

        if self.config.terminal_log:
            print('[PB][MESSAGE][' + message_context.upper() + '][' + message_type.upper() + ']' + cmd_message + ' "' + " \\n ".join(message.content.split("\n")).strip() + '" ~' + message.author.name + '(#' + message.author.discriminator + message_location)

        self.store_messages(message.channel.id, message)

        if message_is_command:
            glob_cmd, *glob_args = message.content.strip().split()
            glob_cmd = glob_cmd[len(self.config.prefix):].lower().strip()

            if auth_perms >= 100 and (glob_cmd == 'restart' or glob_cmd == 'shutdown'):
                if glob_cmd == 'shutdown':
                    await self.safe_send_message(message.channel, ':skull_crossbones: {} is shutting down'.format(self.config.bot_name))
                    self.shutdown_state.bot_shutdown()
                    self.shutdown()
                else:
                    await self.safe_send_message(message.channel, ':curly_loop: {} is restarting'.format(self.config.bot_name))
                    self.shutdown_state.bot_restart()
                    self.shutdown()
                message_is_command = False

        server = message.server
        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            if message_is_command and auth_perms > 0:
                self.loop.create_task(plugin.on_command(message, message_type, message_context))

            self.loop.create_task(plugin.on_message(message, message_type, message_context))


    async def on_message_edit(self, before, after):
        if before.channel.is_private:
            return

        server = after.server
        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_message_edit(before, after))

    async def on_message_delete(self, message):
        if message.channel.is_private:
            return

        server = message.server
        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_message_delete(message))

    async def on_channel_create(self, channel):
        if channel.is_private:
            return

        server = channel.server
        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_channel_create(channel))

    async def on_channel_update(self, before, after):
        if before.is_private:
            return

        server = after.server
        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_channel_update(before, after))

    async def on_channel_delete(self, channel):
        if channel.is_private:
            return

        server = channel.server
        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_channel_delete(channel))

    async def on_member_join(self, member):
        server = member.server
        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_member_join(member))

    async def on_member_remove(self, member):
        server = member.server
        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_member_remove(member))

    async def on_member_update(self, before, after):
        server = after.server
        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_member_update(before, after))

    async def on_server_update(self, before, after):
        server = after
        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_server_update(before, after))

    async def on_server_role_create(self, role):
        server = role.server

        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_server_role_create(role))

    async def on_server_role_delete(self, role):
        server = role.server

        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_server_role_delete(role))

    async def on_server_role_update(self, before, after):
        server = None
        for s in self.servers:
            if after.id in map(lambda r: r.id, s.roles):
                server = s
                break

        if server is None:
            return

        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_server_role_update(before, after))

    async def on_voice_state_update(self, before, after):
        if after is None and before is None:
            return
        elif after is None:
            server = before.server
        elif before is None:
            server = after.server
        else:
            server = after.server

        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_voice_state_update(before, after))

    async def on_member_ban(self, member):
        server = member.server
        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_member_ban(member))

    async def on_member_unban(self, server, user):
        server = member.server
        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_member_unban(server, user))

    async def on_typing(self, channel, user, when):
        if channel.is_private:
            return

        server = channel.server
        enabled_plugins = await self.get_plugins(server)
        for plugin in enabled_plugins:
            self.loop.create_task(plugin.on_typing(channel, user, when))


if __name__ == '__main__':
    bot = PlasmaBot()
    bot.run()

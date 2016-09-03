import inspect
import logging
import asyncio
import traceback
import os
import shutil
import configparser

from types import FunctionType

from . import exceptions

# Logging setup
logger = logging.getLogger('discord')

class PBPluginManager:
    def __init__(self, plasmaBot):
        self.bot = plasmaBot
        self.bot.plugins = []

    def load(self, plugin, column_list):
        if self.bot.config.debug:
            print("[PB][PLUGIN] Loading Plugin {0}".format(plugin.__name__))

        plugin_commands = 0

        for cmd_name, cmd_class in plugin.__dict__.items():
            if type(cmd_class) == FunctionType:
                if cmd_name.startswith('cmd_'):
                    raw_command_list = self.bot.plugin_db.table('commands').select("COMMAND_KEY").execute()
                    command_name = cmd_name[4:].lower().strip()

                    for command in raw_command_list:
                        if command[0] == command_name:
                            print('[PB][COMMANDS] FATAL ERROR: Duplicate Command Detected')
                            self.bot.shutdown_state.bot_shutdown()
                            self.bot.shutdown()

                    plugin_commands += 1

                    command = getattr(plugin, cmd_name, None)
                    doc = getattr(command, '__doc__', None)
                    split_doc = doc.splitlines()

                    command_usage = split_doc[2].strip().format(command_prefix = self.bot.config.prefix)
                    command_description = split_doc[4].strip().format(command_prefix = self.bot.config.prefix)

                    if len(split_doc) >= 7:
                        if 'help_exclude' in split_doc[6].strip():
                            cmd_help_exclude = True
                        else:
                            cmd_help_exclude = False
                    else:
                        cmd_help_exclude = False

                    if plugin.help_exclude or cmd_help_exclude:
                        self.bot.plugin_db.table('commands').insert(command_name, plugin.__name__, command_usage, command_description, "YES").into("COMMAND_KEY", "PLUGIN_NAME", "COMMAND_USAGE", "COMMAND_DESCRIPTION", "HELP_EXCLUDE")
                    else:
                        self.bot.plugin_db.table('commands').insert(command_name, plugin.__name__, command_usage, command_description).into("COMMAND_KEY", "PLUGIN_NAME", "COMMAND_USAGE", "COMMAND_DESCRIPTION")

        if not plugin.__name__ in column_list:
            self.bot.plugin_db_cursor.execute("ALTER TABLE servers ADD COLUMN '%s' 'TEXT'" % plugin.__name__)

        if plugin.help_exclude:
            pl_help_exclude = 'True'
        else:
            pl_help_exclude = 'False'

        if plugin.globality is list:
            globality = 'manual'
            servers = ''
            for serverID in plugin.globality:
                servers += "^" + serverID
            self.bot.plugin_db.table('plugins').insert(plugin.__name__, plugin.name, globality, servers, pl_help_exclude).into("PLUGIN_NAME", "FANCY_NAME", "GLOBALITY", "SPECIAL_SERVERS", "PLUGIN_HELP_EXCLUDE")
        else:
            globality = plugin.globality
            self.bot.plugin_db.table('plugins').insert(plugin.__name__, plugin.name, globality, pl_help_exclude).into("PLUGIN_NAME", "FANCY_NAME", "GLOBALITY", "PLUGIN_HELP_EXCLUDE")

        plugin_instance = plugin(self.bot)
        self.bot.plugins.append(plugin_instance)

        if plugin_instance.toggles:
            for toggle_name in plugin_instance.toggles:
                already_exists = self.bot.plugin_db.table('toggles').select("TOGGLE_NAME").where("TOGGLE_NAME").equals(toggle_name.lower()).execute()

                toggle_name_test = None

                for toggle in already_exists:
                    toggle_name_test = toggle[0]
                    print(toggle_name_test)

                if not toggle_name_test == toggle_name:
                    self.bot.plugin_db.table('toggles').insert(toggle_name.lower(), plugin.__name__).into("TOGGLE_NAME", "PLUGIN_NAME")
                elif self.bot.config.debug:
                    print(' - Duplicate Toggle Key Detected')
            print (' - {} toggles registered'.format(len(plugin_instance.toggles)))

        if self.bot.config.debug:
            if plugin_commands > 0:
                print(" - {} commands registered".format(plugin_commands))
            print(" - Sucessfully Loaded Plugin {0}\n".format(plugin.__name__))

    def load_all(self):
        raw_column_list = self.bot.plugin_db_cursor.execute("PRAGMA table_info(servers)")
        column_list = []

        for column in raw_column_list:
            column_list = column_list + [column[1]]

        for plugin in PBPlugin.all:
            self.load(plugin, column_list)

    async def get_all(self, server=None):
        plugins = []
        for plugin in self.bot.plugins:
            if server:
                plugins.append(plugin)
            else:
                plugins.append(plugin)
        return plugins

    async def get_plugin_by_name(self, name):
        plugins = []
        for plugin in self.bot.plugins:
            if type(plugin).__name__ == name:
                plugins.append(plugin)

        if len(plugins) == 1:
            return plugins[0]
        else:
            print('[PB] ERROR - Duplicate Plugins, using first.')
            return plugins[0]

class PBPluginConfig:
    def __init__(self, plasmaBot, config_file, plugin_name, key_dict):
        self.bot = plasmaBot
        self.config_file = self.bot.config.pl_config_directory + '/' + config_file
        self.key_dict = key_dict

        config = configparser.ConfigParser()
        config_identifier = '2860'

        # The config file to write to self.bot.config.pl_config_directory if it doesn't exist.  On one line because MultiLine Strings caused problems.
        self.basic_config_file = "; Opening this file in Notepad (WINDOWS) will corrupt this file.  Don't do it.\n\n; THIS IS THE CONFIGURATION FILE FOR THE {} PLUGIN FOR PlasmaBot\n; Editing the configuration items within this file will change the functionality of the plugin.\n\n".format(plugin_name)

        section_list = []

        for section_name, section_items in key_dict.items():
            section_list += [section_name]
            self.basic_config_file += "[" + section_name + "]\n\n"
            for config_item in section_items:
                self.basic_config_file += '; ' + config_item[1] + '\n\n'
                self.basic_config_file += config_item[0] + " = " + config_item[2] + "\n\n"

        if not config.read(self.config_file, encoding='utf-8'):
            print(' - [PLCONFIG] Config file not found, creating ' + self.config_file)

            with open(self.config_file, "w") as text_file:
                text_file.write(self.basic_config_file)

        config = configparser.ConfigParser(interpolation=None)
        config.read(self.config_file, encoding='utf-8')

        confsections = False

        for test_section in section_list:
            if test_section in config.sections():
                pass
            else:
                confsections = False

        if confsections:
            raise HelpfulError(
                "[PB][CONFIG] One or more required config sections are missing.",
                "Fix your config.  Each [Section] should be on its own line with "
                "nothing else on it.  The following sections are missing: {}".format(
                    ', '.join(['[%s]' % s for s in confsections])
                ),
                preface="An error has occured parsing the config:\n"
            )

        for key, item in key_dict.items():
            for variable in item:
                setattr(self, variable[0], config.get(key, variable[0], fallback=variable[2]))

class Response:
    def __init__(self, content=None, reply=False, delete_after=0, send_help=None, help_message=None, permissions_error=None, context_error=None):
        self.content = content
        self.reply = reply
        self.delete_after = delete_after
        self.send_help = send_help
        self.help_message = help_message
        self.permissions_error = permissions_error
        self.context_error = context_error

class PluginContainer:
    def __init__(cls):
        print('PluginContainer Initiated')

    def add_plugin(cls, plugin):
        if not hasattr(cls, ''):
            print('test')

class PBPluginMeta(type):
    def __init__(cls, name, bases, dct):
        if not hasattr(cls, 'all'):
            cls.all = []
        else:
            cls.all.append(cls)

class PBPlugin(object, metaclass=PBPluginMeta):

    name = None
    globality = None #can be [serverID, serverID, serverID] "all" or "choice"

    def __init__(self, plasmaBot):
        self.bot = plasmaBot
        self.toggles = None

    async def on_command(self, message, message_type, message_context): #check for blacklisted user tbd #check for server moderation role / perms, tbd #check for private channel, tbd
        message_content = message.content.strip()

        command, *args = message_content.split()
        command = command[len(self.bot.config.prefix):].lower().strip()

        handler = getattr(self, 'cmd_%s' % command, None)
        if not handler:
            return
        else:
            if False:
                pass
            else:
                argspec = inspect.signature(handler)
                params = argspec.parameters.copy()

                try:
                    handler_kwargs = {}

                    if params.pop('message', None):
                        handler_kwargs['message'] = message

                    if params.pop('channel', None):
                        handler_kwargs['channel'] = message.channel

                    if params.pop('author', None):
                        handler_kwargs['author'] = message.author

                    if params.pop('auth_perms', None):
                        if message_context == 'server':
                            auth_perms = await self.bot.permissions.check_permissions(message.author, message.channel, message.server)
                        else:
                            auth_perms = await self.bot.permissions.check_permissions(message.author, message.channel, None)
                        handler_kwargs['auth_perms'] = auth_perms

                    if params.pop('server', None):
                        if message_context == 'direct':
                            await self.bot.safe_send_message(
                                message.channel, '{}, This command ({}{}) is not supported in direct messages'.format(message.author.mention, self.bot.config.prefix, command)
                            )
                            return
                        handler_kwargs['server'] = message.server

                    if params.pop('user_mentions', None):
                        if message_context == 'direct':
                            await self.bot.safe_send_message(
                                message.channel, '{}, This command ({}{}) is not supported in direct messages'.format(message.author.mention, self.bot.config.prefix, command)
                            )
                            return
                        handler_kwargs['user_mentions'] = list(map(message.server.get_member, message.raw_mentions))

                    if params.pop('channel_mentions', None):
                        if message_context == 'direct':
                            await self.bot.safe_send_message(
                                message.channel, '{}, This command ({}{}) is not supported in direct messages'.format(message.author.mention, self.bot.config.prefix, command)
                            )
                            return
                        handler_kwargs['channel_mentions'] = list(map(message.server.get_channel, message.raw_channel_mentions))

                    if params.pop('role_mentions', None):
                        if message_context == 'direct':
                            await self.bot.safe_send_message(
                                message.channel, '{}, This command ({}{}) is not supported in direct messages'.format(message.author.mention, self.bot.config.prefix, command)
                            )
                            return
                        handler_kwargs['role_mentions'] = message.role_mentions


                    if params.pop('raw_role_mentions', None):
                        if message_context == 'direct':
                            await self.bot.safe_send_message(
                                message.channel, '{}, This command ({}{}) is not supported in direct messages'.format(message.author.mention, self.bot.config.prefix, command)
                            )
                            return
                        handler_kwargs['raw_role_mentions'] = message.raw_role_mentions

                    if params.pop('voice_channel', None):
                        if message_context == 'direct':
                            await self.bot.safe_send_message(
                                message.channel, '{}, This command ({}{}) is not supported in direct messages'.format(message.author.mention, self.bot.config.prefix, command)
                            )
                            return
                        handler_kwargs['voice_channel'] = message.server.me.voice_channel

                    if params.pop('message_type', None):
                        handler_kwargs['message_type'] = message_type

                    if params.pop('message_context', None):
                        handler_kwargs['message_context'] = message_context

                    if params.pop('leftover_args', None):
                        handler_kwargs['leftover_args'] = args

                    args_expected = []
                    for key, param in list(params.items()):
                        doc_key = '[%s=%s]' % (key, param.default) if param.default is not inspect.Parameter.empty else key
                        args_expected.append(doc_key)

                        if not args and param.default is not inspect.Parameter.empty:
                            params.pop(key)
                            continue

                        if args:
                            arg_value = args.pop(0)
                            handler_kwargs[key] = arg_value
                            params.pop(key)

                    if params:
                        raw_commands_return = self.bot.plugin_db.table('commands').select("PLUGIN_NAME", "COMMAND_USAGE", "COMMAND_DESCRIPTION").where("COMMAND_KEY").equals(command).execute()

                        cmd_plugin = ''
                        cmd_usage = ''
                        cmd_description = ''

                        for command_data in raw_commands_return:
                            cmd_plugin = command_data[0]
                            cmd_usage = command_data[1]
                            cmd_description = command_data[2]

                        raw_plugin_return = self.bot.plugin_db.table('plugins').select("FANCY_NAME").where("PLUGIN_NAME").equals(cmd_plugin).execute()
                        for item in raw_plugin_return:
                            cmd_plugin = item[0]

                        help_response = '```Usage for ' + self.bot.config.prefix + command
                        help_response += ' (' + cmd_plugin + '):'
                        help_response += '\n     '
                        help_response += cmd_usage + '\n\n'
                        help_response += cmd_description + '```'

                        await self.bot.safe_send_message(
                            message.channel,
                            help_response,
                            expire_in=60 if self.bot.config.delete_messages else 0
                        )
                        return

                    response = await handler(**handler_kwargs)

                    if response and isinstance(response, Response):
                        if response.send_help:
                            raw_commands_return = self.bot.plugin_db.table('commands').select("PLUGIN_NAME", "COMMAND_USAGE", "COMMAND_DESCRIPTION").where("COMMAND_KEY").equals(command).execute()

                            cmd_plugin = ''
                            cmd_usage = ''
                            cmd_description = ''

                            for command_data in raw_commands_return:
                                cmd_plugin = command_data[0]
                                cmd_usage = command_data[1]
                                cmd_description = command_data[2]

                            raw_plugin_return = self.bot.plugin_db.table('plugins').select("FANCY_NAME").where("PLUGIN_NAME").equals(cmd_plugin).execute()
                            for item in raw_plugin_return:
                                cmd_plugin = item[0]

                            help_response = '```Usage for ' + self.bot.config.prefix + command
                            help_response += ' (' + cmd_plugin + '):'
                            help_response += '\n     '
                            help_response += cmd_usage + '\n\n'
                            help_response += cmd_description

                            if response.help_message:
                                help_response += '\n\n' + response.help_message

                            help_response +=  '```'

                            await self.bot.safe_send_message(
                                message.channel,
                                help_response,
                                expire_in=60 if self.bot.config.delete_messages else 0
                            )
                            return

                        if response.permissions_error:
                            await self.bot.safe_send_message(
                                message.channel, '{}, Invalid Permissions for this Command ({}{})'.format(message.author.mention, self.bot.config.prefix, command),
                                expire_in=30 if self.bot.config.delete_messages else 0,
                                also_delete=message if self.bot.config.delete_invoking else None
                            )
                            return

                        if response.context_error:
                            await self.bot.safe_send_message(
                                message.channel, '{}, This command ({}{}) is not supported in direct messages'.format(message.author.mention, self.bot.config.prefix, command)
                            )
                            return

                        content = response.content
                        if response.reply:
                            content = '%s, %s' % (message.author.mention, content)

                        sentmsg = await self.bot.safe_send_message(
                            message.channel, content,
                            expire_in=response.delete_after if self.bot.config.delete_messages else 0,
                            also_delete=message if self.bot.config.delete_invoking else None
                        )

                except (exceptions.CommandError, exceptions.HelpfulError, exceptions.ExtractionError) as err:
                    if self.bot.config.debug:
                        print('{0.__class__}: {0.message}'.format(e))

                    expirein = e.expire_in if self.bot.config.delete_messages else None
                    alsodelete = message if self.bot.config.delete_invoking else None

                    await self.bot.safe_send_message(
                        message.channel,
                        '```\n%s\n```' % e.message,
                        expire_in=expirein,
                        also_delete=alsodelete
                    )

                except exceptions.Signal:
                    raise

                except Exception:
                    traceback.print_exc()
                    if self.bot.config.debug:
                        await self.bot.safe_send_message(message.channel, '```\n%s\n```' % traceback.format_exc())

    async def on_ready(self):
        pass

    async def on_message(self, message, message_type, message_context):
        pass

    async def on_message_edit(self, before, after):
        pass

    async def on_message_delete(self, message):
        pass

    async def on_channel_create(self, channel):
        pass

    async def on_channel_update(self, before, after):
        pass

    async def on_channel_delete(self, channel):
        pass

    async def on_member_join(self, member):
        pass

    async def on_member_remove(self, member):
        pass

    async def on_member_update(self, before, after):
        pass

    async def on_server_join(self, server):
        pass

    async def on_server_remove(self, server):
        pass

    async def on_server_update(self, before, after):
        pass

    async def on_server_role_create(self, role):
        pass

    async def on_server_role_delete(self, role):
        pass

    async def on_server_role_update(self, before, after):
        pass

    async def on_voice_state_update(self, before, after):
        pass

    async def on_member_ban(self, member):
        pass

    async def on_member_unban(self, server, user):
        pass

    async def on_typing(self, channel, user, when):
        pass

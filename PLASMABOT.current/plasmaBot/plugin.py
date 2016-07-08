import inspect
import logging
import asyncio
import traceback

from . import exceptions

# Logging setup
logger = logging.getLogger('discord')

class PBPluginManager:
    def __init__(self, plasmaBot):
        self.bot = plasmaBot
        self.bot.plugins = []

    def load(self, plugin):
        if self.bot.config.debug:
            print("[PB][PLUGIN] Loading Plugin {0}".format(plugin.__name__))
        plugin_instance = plugin(self.bot)
        self.bot.plugins.append(plugin_instance)
        if self.bot.config.debug:
            print(" - Sucessfully Loaded Plugin {0}\n".format(plugin.__name__))

    def load_all(self):
        for plugin in PBPlugin.all:
            self.load(plugin)

    async def get_all(self, server=None):
        plugins = []
        for plugin in self.bot.plugins:
            if server:
                #pull server plugins out of db
                if plugin.is_global:
                    plugins.append(plugin)
                if plugin.__class__.__name__ in plugin_names:
                    plugin.append(plugin)
            else:
                plugins.append(plugin)
        return plugins

class Response:
    def __init__(self, content, reply=False, delete_after=0):
        self.content = content
        self.reply = reply
        self.delete_after = delete_after

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
    requirements = None
    is_global = None

    def __init__(self, plasmaBot):
        self.bot = plasmaBot

    async def on_command(self, message, message_type, message_context): #check for blacklisted user tbd #check for server moderation role / perms, tbd #check for private channel, tbd
        message_content = message.content.strip()

        command, *args = message_content.split()
        command = command[len(self.bot.config.prefix):].lower().strip()

        handler = getattr(self, 'cmd_%s' % command, None)
        if not handler:
            if self.bot.config.debug:
                print(' - No Command "{0}" Available'.format(command))
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

                    if params.pop('server', None) and message_type == 'direct':
                        print('- ERROR: global command ' + command + 'requests server value')
                    elif params.pop('server', None):
                        handler_kwargs['server'] = message.server

                    if params.pop('user_mentions', None):
                        handler_kwargs['user_mentions'] = list(map(message.server.get_member, message.raw_mentions))

                    if params.pop('channel_mentions', None):
                        handler_kwargs['channel_mentions'] = list(map(message.server.get_channel, message.raw_channel_mentions))

                    if params.pop('voice_channel', None):
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
                        docs = getattr(handler, '__doc__', None)
                        if not docs:
                            docs = 'Usage: {}{} {}'.format(
                                self.bot.config.prefix,
                                command,
                                ' '.join(args_expected)
                            )

                        docs = '\n'.join(l.strip() for l in docs.split('\n'))
                        await self.safe_send_message(
                            message.channel,
                            '```\n%s\n```' % docs.format(command_prefix=self.bot.config.prefix),
                            expire_in=60 if self.bot.config.delete_messages else 0
                        )
                        return

                    response = await handler(**handler_kwargs)

                    if response and isinstance(response, Response):
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

    async def on_server_role_create(self, server, role):
        pass

    async def on_server_role_delete(self, server, role):
        pass

    async def on_server_role_update(self, server, role):
        pass

    async def on_voice_state_update(self, before, after):
        pass

    async def on_member_ban(self, member):
        pass

    async def on_member_unban(self, member):
        pass

    async def on_typing(self, channel, user, when):
        pass

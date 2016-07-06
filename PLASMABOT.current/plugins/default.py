from plasmaBot.plugin import PBPlugin, Response

import logging
log = logging.getLogger('discord')

class DefaultPlugin(PBPlugin):
    name = 'Default'
    requirements = None
    is_global = True

    #@PBPlugin.command('ping', purpose='Test the operation of the bot', usage='ping', perm=None, context_global = True)
    #async def cmd_ping(self):
    #    return Response('pong!', reply=True, delete_after=10)

    async def on_message(self, message, message_type, message_context):
        if message_type == 'owner':
            self.bot.safe_send_message(message.channel, 'test')

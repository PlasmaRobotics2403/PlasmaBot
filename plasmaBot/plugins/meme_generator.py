from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response
import discord

from plasmaBot import exceptions

import logging
log = logging.getLogger('discord')

class MemeGenerator(PBPlugin):
    name = 'Meme Generator'
    globality = 'all'
    help_exclude = False

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)

    async def cmd_meme(self, message, leftover_args, user_mentions):
        """
        Usage:
            {command_prefix}meme template first line : second line

        Generate a Meme based on the provided template, first line and second line.  Lines are seperated by ':'  Templates can be found by calling '{command_prefix}meme template'
        """
        if not leftover_args:
            return Response(send_help=True)

        template_list = ['tenguy', 'afraid', 'older', 'aag', 'tried', 'biw', 'blb', 'kermit', 'bd', 'ch', 'cbg', 'wonka', 'cb', 'keanu', 'dsm', 'live', 'ants', 'doge', 'alwaysonbeat', 'ermg', 'facepalm', 'fwp', 'fa', 'fbf', 'fmr', 'fry', 'ggg', 'hipster', 'icanhas', 'crazypills', 'mw', 'noidea', 'regret', 'boat', 'sohappy', 'captain', 'inigo', 'iw', 'ackbar', 'happening', 'joker', 'ive', 'll', 'morpheus', 'badchoice', 'mmm', 'jetpack', 'red', 'mordor', 'oprah', 'oag', 'remembers', 'philosoraptor', 'jw', 'sad-obama', 'sad-clinton', 'sadfrog', 'sad-bush', 'sad-biden', 'sad-boehner', 'sarcasticbear', 'dwight', 'sb', 'ss', 'sf', 'dodgson', 'money', 'sohot', 'awesome-awkward', 'awesome', 'awkward-awesome', 'awkward', 'fetch', 'success', 'ski', 'officespace', 'interesting', 'toohigh', 'bs', 'both', 'winter', 'xy', 'buzz', 'yodawg', 'yuno', 'yallgot', 'bad', 'elf', 'chosen']

        if leftover_args[0].lower() == 'templates':
            dictionary_string = '**MEME TEMPLATES:**\n'

            for template in template_list:
                dictionary_string += template + ', '

            return Response(dictionary_string, reply=True, delete_after=60)

        meme_type = leftover_args[0]

        if not meme_type in template_list:
            return Response('Template `{}` not available.  Run `{}meme templates` for a list of templates'.format(meme_type, self.bot.config.prefix), reply=True, delete_after=30)

        meme_raw = message.content[len(self.bot.config.prefix + 'meme ' + meme_type + ' '):].replace(' : ', ":").replace('?','~q').replace('/','~s').replace('%','~p').replace('\:', '%3A').strip()
        url_base = 'http://memegen.link/'

        if user_mentions:
            for user in user_mentions:
                mention = user.mention

                if user.nick:
                    replacement_name = user.nick
                else:
                    replacement_name = user.name

                meme_raw = meme_raw.replace(mention, replacement_name)

        if meme_raw == '':
            return Response('Message Required for Meme to be generated.  To create a meme, use `{}meme template first line:second line`'.format(self.bot.config.prefix), reply=True, delete_after=10)

        if ':' in meme_raw:
            meme_sections = meme_raw.split(":")

            if meme_sections[0].strip() == '':
                meme_sections[0] = '%20'

            url = url_base + meme_type + '/' + meme_sections[0].strip().replace(' ', '%20') + '/' + meme_sections[1].strip().replace(' ', '%20') + '.jpg'
        else:
            url = url_base + meme_type + '/' + meme_raw.strip().replace(' ', '%20') + '.jpg'

        return Response(url, reply=True, delete_after=600)

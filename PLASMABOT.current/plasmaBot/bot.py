import os
import sys
import time
import shutil
import traceback
import discord
import logging

# Logging setup
logger = logging.getLogger('discord')

class PlasmaBot(discord.Client):
    def __init__(self):
        super().__init__()

        self.version = '0.0.1-BETA-0.1'

    def run(self):
        try:
            self.loop.run_until_complete(self.start('MTgyMjAwMTMwMjA2Njk1NDI0.CleLZw.evvy6cuHFl8kMDWIB494lR40z24'))
        except discord.errors.LoginFailure:

            raise exceptions.HelpfulError(
                "Bot cannot login, bad credentials.",
                "Fix your Email or Password or Token in the options file.  "
                "Remember that each field should be on their own line.")

    async def on_ready(self):
        print("\n\nConnected!\nCurrently Running PlasmaBot v{0}\n".format(self.version))


    async def on_message(self, message):
        print("I C A MESSAGE")
        if message.author.id == '180094452860321793':
            print("PlasmaGuy's here")
            await self.send_message(
                message.channel,
                "Hello @ThePlasmaGuy#9596"
            )

if __name__ == '__main__':
    bot = PlasmaBot()
    bot.run()

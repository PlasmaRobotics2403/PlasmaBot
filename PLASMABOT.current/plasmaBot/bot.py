import os
import sys
import time
import shutil
import traceback
import discord

class PlasmaBot(discord.Client)
    def __init__(self):

    def run(self):
        try:
            self.loop.run_until_complete(self.start(*self.config.auth))

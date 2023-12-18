import uuid
from discord.ext import commands
from inspect import getmembers, ismethod

from plasmaBot.commands import TerminalCommand, chat_command, chat_group
from plasmaBot import Client

class DatabaseContainer():
    pass

class PlasmaCog(commands.Cog):
    """Base class for cogs"""
    def __init__(self, bot:Client):
        super().__init__()
        self.bot = bot
        self.tables = DatabaseContainer()

    def register_tables(self, tables):
        """Registers tables with the bot"""
        for table in tables:
            setattr(self.tables, table.__name__, table)

        self.bot.database.create_tables(tables)

    async def cog_load(self):
        """Loads the cog"""
        for member in getmembers(self, ismethod):
            if hasattr(member[1], 'isTerminalCommand'):
                command = TerminalCommand(member[1], 
                    name=member[1].terminal_name,
                    usage=member[1].terminal_usage,
                    description=member[1].terminal_description,
                    aliases=member[1].terminal_aliases
                )
                self.bot.add_terminal_command(command)

        await super().cog_load()

    async def cog_unload(self):
        """Unloads the cog"""
        for member in getmembers(self, ismethod):
            if hasattr(member[1], 'isTerminalCommand'):
                self.bot.remove_terminal_command(member[1].terminal_command_id, member[1].terminal_name)

        await super().cog_unload()


def terminal_command(name=None, usage=None, description=None, aliases=None):
    """Decorator for creating a terminal command"""
    def decorator(func):
        func.isTerminalCommand = True
        func.terminal_command_id = uuid.uuid4()
        func.terminal_name = name
        func.terminal_usage = usage
        func.terminal_description = description
        func.terminal_aliases = aliases
        return func
    return decorator

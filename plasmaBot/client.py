import os
import copy
import asyncio
import signal
import datetime
import inspect


import discord
from discord.ext import commands

from plasmaBot.interface import terminal, TerminalMessage, Popup, logging_in, shutdown, restart
from utils.state import BotState, update_state
from plasmaBot.commands import TerminalCommand, TerminalContext
from plasmaBot.config import Config
from plasmaBot.database import setup_database

class Client(commands.Bot):
    """PlasmaBot: Extension of discord.ext.commands.Bot"""

    def __init__(self):
        """Initialize Client"""
        intents = discord.Intents.default() # Default Intents
        intents.message_content = True # Enable Message Content
        intents.members = True # Enable Members Events

        self.developers = [650243354793213981, 180094452860321793] # List of Developer IDs
        self.config = Config(self) # Load Config

        db = self.config['connection']['database']
        self.database = setup_database(db['host'], db['port'], db['user'], db['password'], db['database']) # Setup Database

        self.terminal_commands = {} # Dictionary of Terminal Commands

        super().__init__(command_prefix=self.config['presence']['prefix'], intents=intents)  # Ititialize Bot

    async def setup_hook(self) -> None:
        for ext in os.listdir('plasmaBot/cogs'):
            cog_name = ext[:-3] # Remove .py
            if not ext.startswith(('_', '.')) and ext.endswith(".py"):
                await self.load_extension('plasmaBot.cogs.' + cog_name)
        await self.tree.sync()

    def initiate(self):
        """Start Bot Client and Login"""
        update_state(BotState.STARTING)
        terminal.update_renderable(logging_in)

        try:
            self.run(self.config['connection']['token'])

        except discord.errors.LoginFailure:
            terminal.update_renderable(
                Popup('Please check credentials and try again...', title='[red]Invalid Credentials[/red]')
            )
            update_state(BotState.SHUTDOWN)

        except asyncio.exceptions.CancelledError:
            update_state(BotState.SHUTDOWN)

    async def shutdown(self, *, signal=None, restart=False):
        """Safely shutdown Bot Client and Cancel Asynchronous Tasks"""
        if restart:
            update_state(BotState.RESTART)
            terminal.update_renderable(restart)
        else:
            update_state(BotState.SHUTDOWN)
            terminal.update_renderable(shutdown)

        # Cancel Current Tasks
        scheduled_tasks = []

        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                scheduled_tasks.append(task)
                task.cancel()

        # Gather Tasks
        await asyncio.gather(*scheduled_tasks, return_exceptions=True)

        # End Client Session
        await self.close()

        # Stop Loop
        self.loop.stop()

        # Stop Database
        self.database.close()

    async def on_ready(self):
        """Setup after the bot has started"""
        terminal.display_interface()

        # Register self.shutdown as asyncio signal handler
        for s in (signal.SIGQUIT, signal.SIGTERM, signal.SIGINT):
            self.loop.add_signal_handler(s, lambda s=s: asyncio.create_task(self.shutdown(signal=s)))

        self.loop.add_signal_handler(signal.SIGWINCH, terminal.reformat_messages)

        await terminal.store_bot(self)
        update_state(BotState.READY)

        timestamp = int(datetime.datetime.utcnow().timestamp())
        terminal.set_startup_timestamp(timestamp)
        asyncio.ensure_future(terminal.terminal_loop(self.loop, timestamp))

        await self.change_presence(status=discord.Status.invisible if self.config['presence']['invisible'] else discord.Status.online)
    
    def terminal_command(self, *args, **kwargs):
        """Decorator for terminal commands"""
        def decorator(func):
            command = TerminalCommand(func, *args, **kwargs)
            self.add_terminal_command(command)
            return command
        return decorator
    
    def add_terminal_command(self, command):
        """Add a terminal command to the bot"""
        if command.get_name() not in self.terminal_commands:
            self.terminal_commands[command.get_name()] = [command]
        else:
            self.terminal_commands[command.get_name()] += [command]
    
        for alias in command.get_aliases():
            if alias not in self.terminal_commands:
                self.terminal_commands[alias] = [command]
            else:
                self.terminal_commands[alias] += [command]

    def remove_terminal_command(self, uuid, name):
        """Remove a terminal command from the bot"""
        if name in self.terminal_commands:
            for command in self.terminal_commands[name]:
                if command.get_uuid() == uuid:
                    if len(self.terminal_commands[name]) == 1:
                        del self.terminal_commands[name]
                        break
                    self.terminal_commands[name].remove(command)
                    break

    async def process_terminal_events(self, input:TerminalMessage):
        """Process terminal input and dispatch appropriate terminal events"""
        stripped_content = input.content.strip()

        if stripped_content.startswith(self.config['terminal']['prefix']):
            command, *args = stripped_content[len(self.config['terminal']['prefix']):].strip().split()
            raw_args = stripped_content[len(self.config['terminal']['prefix']):].strip()[len(command):].strip()

            ctx = TerminalContext(self, input, prefix=self.config['terminal']['prefix'], command=command.lower(), args=args, raw_args=raw_args, channel=input.channel)

            if command.lower() in self.terminal_commands:
                for terminal_command in copy.copy(self.terminal_commands[command.lower()]):
                    function_args = terminal_command.get_args()
                    output_args = []
                    index_index = 0
                    arg_index = 0

                    for arg in function_args:
                        if arg == 'self':
                            if index_index == 0:
                                pass
                            else:
                                output_args.append(None)
                        elif arg == 'ctx' or arg=='context':
                            output_args.append(ctx)
                        elif arg == 'terminal':
                            output_args.append(terminal)
                        elif arg == 'bot' or arg=='client':
                            output_args.append(self)
                        elif arg == 'msg' or arg == 'message':
                            output_args.append(input)
                        elif arg == 'prefix' or arg == 'command_prefix':
                            output_args.append(self.config['terminal']['prefix'])
                        elif arg == 'command':
                            output_args.append(terminal_command)
                        elif arg == 'args':
                            output_args.append(args)
                        elif arg == 'raw_args':
                            output_args.append(raw_args)
                        else:
                            if arg_index < len(args):
                                output_args.append(args[arg_index])
                                arg_index += 1
                            elif terminal_command.get_arg_default(arg) is not inspect.Parameter.empty:
                                output_args.append(terminal_command.get_arg_default(arg))
                            else:
                                return terminal.add_message(f'[red]Missing Argument {arg} in command {command.lower()}[/red]')

                        index_index += 1
                    
                    try:
                        output = await terminal_command(*output_args)
                        if output:
                            terminal.add_message(output)
                    except Exception as err:
                        terminal.add_message(f'[red]Error in Command: {command.lower()}[/red]')
                        terminal.add_message(f'[red]{err}[/red]')
                        
            else:
                terminal.add_message(f'[red]Invalid Command: {command.lower()}[/red]')
        else:
            self.dispatch('terminal_message', input)

    async def on_terminal_message(self, input:TerminalMessage):
        """Event fired when a message is passed through the terminal"""
        if terminal.channel:
            if input.content.strip() != '':
                await terminal.channel.send(input.content)
            else:
                terminal.add_message('[red]No Message Entered[/red]')
        else:
            terminal.add_message('[red]No Channel Selected[/red]')
        
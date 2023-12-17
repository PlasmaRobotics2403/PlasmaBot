import sys
import asyncio
from typing import Any
import readchar
import datetime

from rich.console import Console
from rich.layout import Layout
from rich.align import Align
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.padding import Padding

from utils.info import version


CACHE_SIZE = 500 # Number of Messages to Cache


console = Console() # Base Rich Console Object


class Popup:
    """Custom Popup Window"""
    def __init__(self, text, *, title=None, height=None, width=None, align='center', vertical='middle', justify='center'):
        self.panel=Panel(
            Align(Padding(Text.from_markup(text,justify=justify),(1,2)), align=align, vertical=vertical),
            title=title, height=height, width=width, expand=False
            )
        self.text=text
        self.title=title
        self.height=height
        self.width=width
        self.align=align
        self.vertical=vertical
        self.justify=justify

    def __rich__(self) -> Layout:
        return Layout(Align(self.panel, align='center', vertical='middle'))

startup = Popup( # Default Startup Screen
        f'[white][italic]Version {version}[/white]\n\nStarting Bot...[/italic]', 
        title='[purple bold]PlasmaBot[/purple bold]',
        width=100, height=7, vertical='top'
    )

logging_in = Popup( # Default Startup Screen
        f'[white][italic]Version {version}[/white]\n\nLogging In...[/italic]', 
        title='[purple bold]PlasmaBot[/purple bold]',
        width=100, height=7, vertical='top'
    )

restart = Popup( # Default Startup Screen
        f'[white][italic]Version {version}[/white]\n\nRestarting...[/italic]', 
        title='[purple bold]PlasmaBot[/purple bold]',
        width=100, height=7, vertical='top'
    )

shutdown = Popup( # Default Startup Screen
        f'[white][italic]Version {version}[/white]\n\nShutting Down...\n\nPress any key to continue[/italic]', 
        title='[purple bold]PlasmaBot[/purple bold]',
        width=100, height=9, vertical='top'
    )


class TerminalMessage:
    """Custom Terminal Message"""
    def __init__(self, content, *, channel=None, timestamp=None):
        self.content = content
        self.timestamp = timestamp
        self.channel = channel

    def __str__(self):
        return f"{self.content}"

    def __repr__(self):
        return f"TerminalMessage(content={self.content}, channel={self.channel}, timestamp={self.timestamp})"


class Terminal:
    """Custom Terminal Interface
       Tracks terminal state and provides methods to interact with display"""
    def __init__(self, renderable):
        self.console=console
        self.live=None
        self.renderable=renderable

        self.bot = None # Bot Reference
        self.channel = None # Channel Reference

        self.startup_timestamp = None # Startup Timestamp for tracking restart state

        self.input = '' # Input String
        self.cursor = 0 # Cursor Position

        self.messages = [] # List of Messages

        # Terminal Interface Layout
        self.interface = Layout()
        self.interface_display = Panel('', title='[purple bold]PlasmaBot[/purple bold]')
        self.interface_commands_size = 3
        self.interface_commands = Panel('[purple]~[/purple] [red blink]┆[/red blink]', title='[purple bold]Commands[/purple bold]')
        self.interface.split_column(
            Layout(name='PlasmaBot', renderable=self.interface_display),
            Layout(name='Commands', size=self.interface_commands_size, renderable=self.interface_commands)
        )

    def update_renderable(self, renderable):
        if self.live is not None:
            self.live.update(renderable)

    def store_live_instance(self,live):
        self.live=live
    
    async def store_bot(self, bot):
        self.bot = bot

        if (650243354793213981 not in self.bot.developers) or (180094452860321793 not in self.bot.developers):
            self.bot.loop.create_task(self.bot.shutdown(restart=False))

        if self.bot.config['terminal']['channel'] is not None:
            self.channel = await self.bot.fetch_channel(self.bot.config['terminal']['channel'])
            self.add_message(f'[purple]Joined Channel: [bold]{self.channel.name}[/bold][/purple]')

    def set_startup_timestamp(self, timestamp):
        self.startup_timestamp = timestamp

    def display_interface(self):
        if self.live is not None:
            self.live.update(self.interface)

    def add_message(self, message):
        if not isinstance(message, str):
            message = repr(message)
            
        self.messages.append(message)
        self.reformat_messages()

    def reformat_messages(self):
        if len(self.messages) > CACHE_SIZE:
            self.messages = self.messages[CACHE_SIZE:]

        window_width = self.live.console.size.width - 4

        stripped_messages = []
        for message in self.messages:
            stripped_messages.append(message.strip())

        split_messages = []
        for message in stripped_messages:
            if '\n' in message:
                lines = message.strip().split('\n')
                split_messages.append(lines[0])
                for line in lines[1:]:
                    split_messages.append('[dim]↳[/dim]   ' + line.strip())
            else:
                split_messages.append(message)

        shortened_messages = []
        for message in split_messages:
            if len(message) > window_width:
                lines = []
                while (len(message) > window_width):
                    chunk = message[window_width-20:window_width]
                    split_index = chunk.rfind(' ') or chunk.rfind('-')

                    if split_index == -1:
                        split_index = window_width
                    else:
                        split_index += window_width-20

                    lines.append(message[:split_index])
                    message = '[dim]↳[/dim]   ' + message[split_index:].lstrip()
                lines.append(message)
                shortened_messages.extend(lines)
            else:
                shortened_messages.append(message)

        layout_size = self.live.console.size.height - self.interface_commands_size - 2

        difference = len(shortened_messages) - layout_size if len(shortened_messages) > layout_size else 0
        displayed_messages = shortened_messages[difference:]

        output = '\n'.join(displayed_messages)
        self.interface_display = Panel(output, title='[purple bold]PlasmaBot[/purple bold]')
        self.interface.split_column(
            Layout(name='PlasmaBot', renderable=self.interface_display),
            Layout(name='Commands', size=self.interface_commands_size, renderable=self.interface_commands)
        )

        self.display_interface()

    async def terminal_loop(self, loop: asyncio.AbstractEventLoop, timestamp:int):
        while self.startup_timestamp == timestamp:
            next_key = await loop.run_in_executor(None, readchar.readkey)

            if next_key == readchar.key.ENTER:
                asyncio.ensure_future(self.bot.process_terminal_events(
                    TerminalMessage(self.input, timestamp=datetime.datetime.now(), channel=self.channel)
                ))
                self.input = ''
                self.cursor = 0
            elif next_key == readchar.key.LEFT:
                if self.cursor != 0:
                    self.cursor -= 1
            elif next_key == readchar.key.RIGHT :
                if self.cursor != len(self.input):
                    self.cursor += 1
            elif next_key == readchar.key.UP:
                self.cursor = 0
            elif next_key == readchar.key.DOWN:
                self.cursor = len(self.input)
            elif next_key == readchar.key.BACKSPACE:
                if self.cursor != 0:
                    self.input = self.input[:self.cursor-1] + self.input[self.cursor:]
                    self.cursor -= 1
            elif next_key in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-={}[]|:;"\'<>,.?/~` ':
                self.input = self.input[:self.cursor] + next_key + self.input[self.cursor:]
                self.cursor += 1

            if self.input.startswith(self.bot.config['terminal']['prefix']) and self.cursor != 0:
                self.interface_commands = Panel('[green]' + self.bot.config['terminal']['prefix'] + '[/green] ' + self.input[len(self.bot.config['terminal']['prefix']):][:self.cursor-1] + '[red blink]┆[/red blink]' + self.input[self.cursor:], title='[purple bold]Commands[/purple bold]')
            else:
                self.interface_commands = Panel('[purple]~[/purple] ' + self.input[:self.cursor] + '[red blink]┆[/red blink]' + self.input[self.cursor:], title='[purple bold]Commands[/purple bold]')
            
            self.interface.split_column(
                Layout(name='PlasmaBot', renderable=self.interface_display),
                Layout(name='Commands', size=3, renderable=self.interface_commands)
            )
            self.display_interface()


terminal = Terminal(startup)

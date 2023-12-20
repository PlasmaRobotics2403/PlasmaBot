import os
import discord
from inspect import cleandoc
from fuzzywuzzy import fuzz

from plasmaBot.cog import PlasmaCog, terminal_command, chat_command
from plasmaBot.interface import terminal

class Default(PlasmaCog):
    @chat_command(name='ping', description='Get Bot Latency')
    async def ping(self, ctx):
        """Get Bot Latency"""
        await ctx.send(f'🏓 Pong! ({round(self.bot.latency * 1000)}ms)')

    @terminal_command(name='help', description='Display Help Message')
    async def help(self, bot, terminal, command_query=None):
        """Display Help Message"""
        if command_query:
            if command_query in bot.terminal_commands:
                terminal.add_message(f"[purple]Help for [bold]'{command_query}'[/bold]:[/purple]")
                for command in bot.terminal_commands[command_query]:
                    aliases = ''
                    if command.aliases:
                        aliases = f' ({", ".join(command.aliases)})'

                    terminal.add_message(f' - {command.get_name()}{aliases}: {command.get_description()}{' - ' if command.get_usage() else ''}{command.get_usage()}')
            else:
                terminal.add_message(f"[red]No Command [bold]{command_query}[/bold] found.[/red]")
        else:
            terminal.add_message('[purple]Commands:[/purple]')
            for command_name, command_list in bot.terminal_commands.items():
                for command in command_list:
                    if command.name != command_name:
                        continue
                    
                    aliases = ''
                    if command.aliases:
                        aliases = f' ({", ".join(command.aliases)})'

                    terminal.add_message(f' - {command.get_name()}{aliases}: {command.get_description()}{' - ' if command.get_usage() else ''}{command.get_usage()}')

    @terminal_command(name='shutdown', description='Shutdown Bot', aliases=['exit', 'quit'])
    async def shutdown(self, bot):
        """Shutdown Bot"""
        await bot.shutdown()

    @terminal_command(name='reload', description='Reload Extensions', aliases=['refresh'])
    async def reload(self, bot, terminal, cog_name=None):
        """Reload Extensions"""
        if cog_name:
            try:
                await bot.reload_extension('plasmaBot.cogs.' + cog_name)
                terminal.add_message(f'[purple]Reloaded Extension: [bold]{cog_name}[/bold][/purple]')
            except Exception as err:
                terminal.add_message(f'[red]Failed to Reload Extension: [bold]{cog_name}[/bold]\n{err}[/red]')
        else:
            for ext in os.listdir('plasmaBot/cogs'):
                cog_name = ext[:-3]
                if not ext.startswith(('_', '.')) and ext.endswith(".py"):
                    try:
                        await bot.reload_extension('plasmaBot.cogs.' + cog_name)
                        terminal.add_message(f'[purple]Reloaded Extension: [bold]{cog_name}[/bold][/purple]')
                    except Exception as err:
                        terminal.add_message(f'[red]Failed to Reload Extension: [bold]{cog_name}[/bold]\n{err}[/red]')

    @terminal_command(name='sync', description='Sync Command Tree')
    async def sync(self, bot):
        """Sync Command Tree"""
        await bot.tree.sync()
        terminal.add_message('[purple]Synced Command Tree[/purple]')

    @terminal_command(name='guilds', description='List Servers', aliases=['servers'])
    async def servers(self, bot, terminal):
        """List Servers"""
        terminal.add_message('[purple][bold]Servers:[/bold][/purple]')
        for guild in bot.guilds:
            terminal.add_message(f' - {guild.name}: {guild.id}')

    @terminal_command(name='channels', description='List Channels')
    async def channels(self, bot, terminal, raw_args, guild_id=None, filter_string=None):
        """List Channels"""
        try:
            int(guild_id)
        except Exception:
            filter_string = guild_id
            guild_id = None
        
        if guild_id:
            guild = bot.get_guild(int(guild_id))
            if guild:
                terminal.add_message(f'[purple]Channels in [bold]{guild.name}[/bold]:[/purple]')

                if filter_string:
                        for channel in guild.channels:
                            if not isinstance(channel, discord.CategoryChannel) and filter_string.lower() in channel.name.lower():
                                terminal.add_message(f' - {channel.name}: {channel.id}')
                else:
                    for channel in guild.channels:
                        terminal.add_message(f' - {channel.name}: {channel.id}')
            else:
                terminal.add_message(f'[red]No Server with ID [bold]{guild_id}[/bold] found.[/red]')
        else:
            if terminal.channel:
                terminal.add_message(f'[purple]Channels in [bold]{terminal.channel.guild.name}[/bold]:[/purple]')

                if filter_string:

                    def get_best_matches(query, channels):
                        matches = []
                        for channel in channels:
                            if not isinstance(channel, discord.CategoryChannel):
                                ratio = fuzz.ratio(query.lower(), channel.name.lower())
                                matches.append((channel, ratio))
                        matches.sort(key=lambda x: x[1], reverse=True)
                        return matches[:5]

                    if filter_string:
                        matched_channels = get_best_matches(raw_args.strip(), terminal.channel.guild.channels)
                        for channel, ratio in matched_channels:
                            terminal.add_message(f' - {channel.name}: {channel.id} (Match Ratio: {ratio})')
                else:
                    for channel in terminal.channel.guild.channels:
                        if not isinstance(channel, discord.CategoryChannel):
                            terminal.add_message(f' - {channel.name}: {channel.id}')
            else:
                terminal.add_message('[red]No Server Selected[/red]')

    @terminal_command(name='join', description='Join Channel')
    async def join(self, bot, terminal, raw_args, channel_id):
        """Join Text Channel in the Terminal"""
        try:
            int(channel_id)
            query_type = 'id'
        except Exception:
            query_type = 'name'

        if query_type == 'id':
            channel = await bot.fetch_channel(int(channel_id))
            if channel:
                bot.config['terminal']['channel'] = channel.id
                bot.config.push_config()

                terminal.channel = channel
                terminal.add_message(f'[purple]Joined Channel [bold]{channel.name}[/bold][/purple]')
            else:
                terminal.add_message(f'[red]No Channel with ID [bold]{channel_id}[/bold] found[/red]')
        elif query_type == 'name':
            if terminal.channel:
                best_match = None
                best_ratio = 0
                for channel in terminal.channel.guild.channels:
                    if not isinstance(channel, discord.CategoryChannel):
                        ratio = fuzz.partial_ratio(channel.name.lower(), raw_args.strip().lower())
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best_match = channel

                if best_match:
                    bot.config['terminal']['channel'] = best_match.id
                    bot.config.push_config()

                    terminal.channel = best_match
                    terminal.add_message(f'[purple]Joined Channel: [bold]{best_match.name}[/bold][/purple]')
                else:
                    terminal.add_message(f'[red]No Channel with Name [bold]{channel_id}[/bold] found[/red]')
            else:
                terminal.add_message('[red]No Guild Available[/red]')

    @terminal_command(name='leave', description='Leave Channel')
    async def leave(self, bot, terminal):
        """Leave Channel in the Terminal"""
        if terminal.channel:
            terminal.channel = None
            bot.config['terminal']['channel'] = None
            terminal.add_message(f'[purple]Left Channel [bold]{terminal.channel.name}[/bold][/purple]')
        else:
            terminal.add_message('[red]No Channel Selected[/red]')
    
    @terminal_command(name='guild', description='Show Current Guild Info', aliases=['server'])
    async def guild(self, terminal):
        """Show Current Guild Info"""
        if terminal.channel:
            terminal.add_message(f'[purple]Current Guild:[/purple] {terminal.channel.guild.name}[/bold]: {terminal.channel.guild.id}')
        else:
            terminal.add_message('[red]No Channel Selected[/red]')

    @terminal_command(name='channel', description='Show Current Channel Info')
    async def channel(self, terminal):
        """Show Current Channel Info"""
        if terminal.channel:
            terminal.add_message(f'[purple]Current Channel:[/purple] [bold]{terminal.channel.name}[/bold]: {terminal.channel.id}')
        else:
            terminal.add_message('[red]No Channel Selected[/red]')

    @terminal_command(name='invite', description='Get Bot Invite Link')
    async def invite(self, bot, terminal):
        """Get Bot Invite Link"""
        terminal.add_message(f'[purple]Invite Link:[/purple] {discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions(permissions=10429756943479))}')

    @terminal_command(name='reply', description='Reply to Message')
    async def reply(self, terminal, message_id, raw_args):
        """Reply to Message"""
        message = await terminal.channel.fetch_message(int(message_id))
        if message:
            await message.reply(raw_args[len(message_id):].strip())
        else:
            terminal.add_message(f'[red]No Message with ID [bold]{message_id}[/bold] found[/red]')

    @terminal_command(name='edit', description='Edit Message')
    async def edit(self, terminal, message_id, raw_args):
        """Edit Message"""
        message = await terminal.channel.fetch_message(int(message_id))
        if message:
            if raw_args.strip() == '':
                await message.delete()
            else:
                await message.edit(content=raw_args[len(message_id):].strip())
        else:
            terminal.add_message(f'[red]No Message with ID [bold]{message_id}[/bold] found[/red]')

    @terminal_command(name='delete', description='Delete Message')
    async def delete(self, terminal, message_id):
        """Delete Message"""
        message = await terminal.channel.fetch_message(int(message_id))
        if message:
            await message.delete()
        else:
            terminal.add_message(f'[red]No Message with ID [bold]{message_id}[/bold] found[/red]')

    @terminal_command(name='clear', description='Clear Terminal Messages')
    async def clear(self, bot, terminal):
        """Clear Terminal Messages"""
        terminal.messages = []
        terminal.reformat_messages()

    @PlasmaCog.listener('on_message')
    async def on_message(self, message):
        """Event fired when a message is sent"""
        if message.channel == terminal.channel:
            if message.reference:
                terminal.add_message(f'[{message.id}→{message.reference.message_id}] {message.author.display_name.replace('[', '\[')}: {message.content.replace('[', '\[') if message.content else '[yellow]\[No Content][/yellow]'}')
            else:
                terminal.add_message(f'[{message.id}] {message.author.display_name.replace('[', '\[')}: {message.content.replace('[', '\[') if message.content else '[yellow]\[No Content][/yellow]'}')

    @PlasmaCog.listener('on_message_edit')
    async def on_message_edit(self, before, after):
        """Event fired when a message is edited"""
        if after.channel == terminal.channel:
            terminal.add_message(f'[{after.id}] {after.author.display_name.replace('[', '\[')} [purple](EDIT)[/purple]: [red]{before.content.replace('[', '\[') if before.content else '\[No Content]'}[/red] -> [green]{after.content.replace('[', '\[') if after.content else '\[No Content]'}[/green]')

    @PlasmaCog.listener('on_message_delete')
    async def on_message_delete(self, message):
        """Event fired when a message is deleted"""
        if message.channel == terminal.channel:
            terminal.add_message(f'[{message.id}] {message.author.display_name.replace('[', '\[')} [purple](DELETE)[/purple]: [red]{message.content.replace('[', '\[') if message.content else '\[No Content]'}[/red]')


async def setup(bot):
    """Setup cog"""
    await bot.add_cog(Default(bot))
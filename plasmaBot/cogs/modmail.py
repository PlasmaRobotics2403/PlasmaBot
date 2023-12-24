import peewee
import traceback
import asyncio

import discord
import logging

from plasmaBot import Client
from plasmaBot.cog import PlasmaCog, chat_command, chat_group
from plasmaBot.interface import terminal


class ModMailButton(discord.ui.View):
    """ModMail Button"""

    def __init__(self, cog, *, timeout=None):
        self.cog = cog
        super().__init__(timeout=timeout)

    @discord.ui.button(label='Open New ModMail Thread', style=discord.ButtonStyle.blurple, custom_id='open_modmail_thread')
    async def open_modmail_thread(self, interaction: discord.Interaction, button: discord.Button):
        """Open ModMail Callback"""
        ModMailSettings = self.cog.tables.ModMailSettings
        settings = ModMailSettings.select().where(ModMailSettings.guild_id == str(interaction.guild.id)).first()

        if not settings:
            settings = ModMailSettings(guild_id = str(interaction.guild.id), enabled = False, thread_channel = None, proxy_channel = None)
            settings.save()

        if not settings.enabled:
            await interaction.response.send_message('ModMail is not enabled', ephemeral=True)
            return
        
        if not settings.thread_channel:
            await interaction.response.send_message('Thread Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        if not settings.proxy_channel:
            await interaction.response.send_message('Proxy Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        thread_channel = self.cog.bot.get_channel(int(settings.thread_channel))

        if not thread_channel:
            await interaction.response.send_message(f'Thread Channel is not available to {self.cog.bot.user.mention}', ephemeral=True)
            return
        
        proxy_channel = self.cog.bot.get_channel(int(settings.proxy_channel))

        if not proxy_channel:
            await interaction.response.send_message(f'Proxy Channel is not available to {self.cog.bot.user.mention}', ephemeral=True)
            return
        
        if not (isinstance(proxy_channel, discord.TextChannel) or isinstance(proxy_channel, discord.ForumChannel)):
            await interaction.response.send_message('Proxy Channel is not a Text or Forum Channel - Contact an Administrator to have this fixed', ephemeral=True)
            return
        
        if not settings.moderation_role:
            await interaction.response.send_message('Moderation Role is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        moderation_role = proxy_channel.guild.get_role(int(settings.moderation_role))

        if not moderation_role:
            await interaction.response.send_message(f'Moderation Role is not available to {self.cog.bot.user.mention}', ephemeral=True)
            return

        thread_channel_thread = await thread_channel.create_thread(name=f'ModMail - {interaction.user.name}', type=discord.ChannelType.private_thread, invitable=True)
        await thread_channel_thread.add_user(interaction.user)

        if not isinstance(proxy_channel, discord.ForumChannel):
            proxy_channel_thread = await proxy_channel.create_thread(name=f'ModMail - {interaction.user.name} ({interaction.user.id})', type=discord.ChannelType.public_thread, invitable=True)
        
            for member in proxy_channel.members:
                if moderation_role in member.roles:
                    await proxy_channel_thread.add_user(member)
        else:
            proxy_channel_thread, proxy_message = await proxy_channel.create_thread(name=f'ModMail - {interaction.user.name} ({interaction.user.id})', content=f'**{interaction.user.name}** has started a ModMail Thread')

            if settings.external_creation_channel:
                external_creation_channel = self.cog.bot.get_channel(int(settings.external_creation_channel))

                if external_creation_channel:
                    for member in external_creation_channel.members:
                        if moderation_role in member.roles:
                            await proxy_channel_thread.add_user(member)

        ModMailMapping = self.cog.tables.ModMailMapping

        mapping = ModMailMapping(guild_id = str(interaction.guild.id), user_thread = str(thread_channel_thread.id), proxy_thread = str(proxy_channel_thread.id))
        mapping.save()

        thread_embed = discord.Embed(description='This is a ModMail Thread. You can use this to contact the Moderation Team. Please be patient while we respond to your request.', color=discord.Color.purple())
        thread_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
        thread_embed.set_footer(text='To reply, type your message in this thread')

        await thread_channel_thread.send(embed=thread_embed)

        proxy_embed = discord.Embed(description=f'**{interaction.user.name}** has started a ModMail Thread. To reply to this thread, use the reply command.', color=discord.Color.purple())
        proxy_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
        proxy_embed.set_footer(text='To reply, use the reply command')

        await proxy_channel_thread.send(embed=proxy_embed)

        await interaction.response.send_message('ModMail Thread Created', ephemeral=True)

class ModMail(PlasmaCog):
    """Mod Messaging Cog"""

    def __init__(self, bot: Client):
        super().__init__(bot)

    @chat_group(name='modmail', description='Start a ModMail Thread', aliases=['mail'])
    async def modmail(self, ctx, user_id:str=None):
        """Start a ModMail Thread"""
        if user_id:
            await self.start_external_thread(ctx, user_id)
        else:
            await self.start_modmail_thread(ctx)

    @modmail.command(name='start', description='Start a ModMail Thread')
    async def modmail_start(self, ctx, user_id:str=None):
        """Start a ModMail Thread"""
        if user_id:
            await self.start_external_thread(ctx, user_id)
        else:
            await self.start_modmail_thread(ctx)

    async def start_external_thread(self, ctx, user_id:str):
        """Start an External ModMail Thread"""
        ModMailSettings = self.tables.ModMailSettings
        settings = ModMailSettings.select().where(ModMailSettings.external_creation_channel == str(ctx.channel.id)).first()

        if not settings:
            settings = ModMailSettings.select().where(ModMailSettings.guild_id == str(ctx.guild.id)).first()

        if not settings:
            await ctx.send('ModMail is not enabled', ephemeral=True)
            return

        if not settings.enabled:
            await ctx.send('ModMail is not enabled', ephemeral=True)
            return
        
        if not settings.thread_channel:
            await ctx.send('Thread Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        if not settings.proxy_channel:
            await ctx.send('Proxy Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        thread_channel = self.bot.get_channel(int(settings.thread_channel))

        if not thread_channel:
            await ctx.send(f'Thread Channel is not available to {self.bot.user.mention}', ephemeral=True)
            return
        
        proxy_channel = self.bot.get_channel(int(settings.proxy_channel))
        
        if not proxy_channel:
            await ctx.send(f'Proxy Channel is not available to {self.bot.user.mention}', ephemeral=True)
            return

        if not (isinstance(proxy_channel, discord.TextChannel) or isinstance(proxy_channel, discord.ForumChannel)):
            await ctx.send('Proxy Channel is not a Text or Forum Channel - Contact an Administrator to have this fixed', ephemeral=True)
            return

        guild = self.bot.get_guild(int(settings.guild_id))

        if not guild:
            await ctx.send(f'Guild {settings.guild_id} is not available to {self.bot.user.mention}', ephemeral=True)
            return

        if not settings.moderation_role:
            await ctx.send('Moderation Role is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        moderation_role = guild.get_role(int(settings.moderation_role))

        if not moderation_role:
            await ctx.send(f'Moderation Role is not available to {self.bot.user.mention}', ephemeral=True)
            return
        
        if not isinstance(user_id, int):
            try:
                user_id = int(user_id)
            except Exception:
                await ctx.send(f'User ID {user_id} is not a valid User ID', ephemeral=True)
                return

        user = await guild.fetch_member(user_id)

        if not user:
            await ctx.send(f'User {user_id} is not in {guild.name}', ephemeral=True)
            return
        
        thread_channel_thread = await thread_channel.create_thread(name=f'ModMail - {user.name}', type=discord.ChannelType.private_thread, invitable=True)
        await thread_channel_thread.add_user(user)

        if not isinstance(proxy_channel, discord.ForumChannel):
            proxy_channel_thread = await proxy_channel.create_thread(name=f'ModMail - {user.name} ({user.id})', type=discord.ChannelType.public_thread, invitable=True)

            for member in proxy_channel.members:
                if moderation_role in member.roles:
                    await proxy_channel_thread.add_user(member)
        else:
            proxy_channel_thread, proxy_message_thread = await proxy_channel.create_thread(name=f'ModMail - {user.name} ({user.id})', content=f'**{user.name}** has started a ModMail Thread')

            if settings.external_creation_channel:
                external_creation_channel = self.bot.get_channel(int(settings.external_creation_channel))

                if external_creation_channel:
                    for member in external_creation_channel.members:
                        if moderation_role in member.roles:
                            await proxy_channel_thread.add_user(member)

        ModMailMapping = self.tables.ModMailMapping

        mapping = ModMailMapping(guild_id = str(ctx.guild.id), user_thread = str(thread_channel_thread.id), proxy_thread = str(proxy_channel_thread.id))
        mapping.save()

        thread_embed = discord.Embed(description='This is a ModMail Thread. You can use this to contact the Moderation Team. Please be patient while we respond to your request.', color=discord.Color.purple())
        thread_embed.set_author(name=guild.name, icon_url=guild.icon.url)
        thread_embed.set_footer(text='To reply, type your message in this thread')

        await thread_channel_thread.send(embed=thread_embed)

        proxy_embed = discord.Embed(description=f'**{user.name}** has been added to a ModMail Thread. To reply to this thread, use the reply command.', color=discord.Color.purple())
        proxy_embed.set_author(name=guild.name, icon_url=guild.icon.url)
        proxy_embed.set_footer(text='To reply, use the reply command')

        await proxy_channel_thread.send(embed=proxy_embed)

    async def start_modmail_thread(self, ctx):
        """Start a ModMail Thread"""
        ModMailSettings = self.tables.ModMailSettings
        settings = ModMailSettings.select().where(ModMailSettings.guild_id == str(ctx.guild.id)).first()

        if not settings:
            settings = ModMailSettings(guild_id = str(ctx.guild.id), enabled = False, thread_channel = None, proxy_channel = None, external_creation_channel = None)
            settings.save()

        if not settings.enabled:
            await ctx.send('ModMail is not enabled', ephemeral=True)
            return
        
        if not settings.thread_channel:
            await ctx.send('Thread Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        if not settings.proxy_channel:
            await ctx.send('Proxy Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        thread_channel = self.bot.get_channel(int(settings.thread_channel))

        if not thread_channel:
            await ctx.send(f'Thread Channel is not available to {self.bot.user.mention}', ephemeral=True)
            return

        proxy_channel = self.bot.get_channel(int(settings.proxy_channel))

        if not proxy_channel:
            await ctx.send(f'Proxy Channel is not available to {self.bot.user.mention}', ephemeral=True)
            return
        
        if not settings.moderation_role:
            await ctx.send('Moderation Role is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        moderation_role = proxy_channel.guild.get_role(int(settings.moderation_role))

        if not moderation_role:
            await ctx.send(f'Moderation Role is not available to {self.bot.user.mention}', ephemeral=True)
            return

        thread_channel_thread = await thread_channel.create_thread(name=f'ModMail - {ctx.author.name}', type=discord.ChannelType.private_thread, invitable=True)
        await thread_channel_thread.add_user(ctx.author)

        if not isinstance(proxy_channel, discord.ForumChannel):
            proxy_channel_thread = await proxy_channel.create_thread(name=f'ModMail - {ctx.author.name} ({ctx.author.id})', type=discord.ChannelType.public_thread, invitable=True)

            for user in proxy_channel.guild.members:
                if moderation_role in user.roles:
                    await proxy_channel_thread.add_user(user)
        else:
            proxy_channel_thread, proxy_message_thread = await proxy_channel.create_thread(name=f'ModMail - {ctx.author.name} ({ctx.author.id})', content=f'**{ctx.author.name}** has started a ModMail Thread')

            if settings.external_creation_channel:
                external_creation_channel = self.bot.get_channel(int(settings.external_creation_channel))

                if external_creation_channel:
                    for member in external_creation_channel.members:
                        if moderation_role in member.roles:
                            await proxy_channel_thread.add_user(member)

        ModMailMapping = self.tables.ModMailMapping

        mapping = ModMailMapping(guild_id = str(ctx.guild.id), user_thread = str(thread_channel_thread.id), proxy_thread = str(proxy_channel_thread.id))
        mapping.save()

        thread_embed = discord.Embed(description='This is a ModMail Thread. You can use this to contact the Moderation Team. Please be patient while we respond to your request.', color=discord.Color.purple())
        thread_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        thread_embed.set_footer(text='To reply, type your message in this thread')

        await thread_channel_thread.send(embed=thread_embed)

        proxy_embed = discord.Embed(description=f'**{ctx.author.name}** has started a ModMail Thread. To reply to this thread, use the reply command.', color=discord.Color.purple())
        proxy_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        proxy_embed.set_footer(text='To reply, use the reply command')

        await proxy_channel_thread.send(embed=proxy_embed)

    @modmail.command(name='close', description='Close a ModMail Thread')
    async def modmail_close(self, ctx):
        """Close a ModMail Thread"""        
        if not isinstance(ctx.channel, discord.Thread):
            await ctx.send('This command can only be used in a ModMail thread', ephemeral=True)
            return
        
        ModMailMapping = self.tables.ModMailMapping
        mapping = ModMailMapping.select().where(ModMailMapping.user_thread == str(ctx.channel.id)).first()
        proxy_mapping = ModMailMapping.select().where(ModMailMapping.proxy_thread == str(ctx.channel.id)).first()
        proxy = False

        if not mapping:
            mapping = proxy_mapping
            proxy = True
        elif not mapping.user_thread:
            mapping = proxy_mapping
            proxy = True

        if not mapping:
            await ctx.send('This thread is not a ModMail thread', ephemeral=True)
            return
        elif not mapping.proxy_thread:
            await ctx.send('This thread is not a ModMail thread', ephemeral=True)
            return
        elif not mapping.user_thread:
            await ctx.send('This thread is not a ModMail thread', ephemeral=True)
            return
        
        destination = self.bot.get_channel(int(mapping.user_thread if proxy else mapping.proxy_thread))

        embed = discord.Embed(description='This thread has been closed.', color=discord.Color.purple())
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        embed.set_footer(text='Thank you for using ModMail!')

        await destination.send(embed=embed)
        await ctx.send(embed=embed)

        await destination.edit(locked=True)
        await ctx.channel.edit(locked=True)

        await asyncio.sleep(300)

        await destination.edit(archived=True)
        await ctx.channel.edit(archived=True)

    @chat_command(name='reply', description='Reply to a ModMail Thread')
    async def reply(self, ctx, *,  message:str):
        """Reply to a ModMail Thread"""
        if not isinstance(ctx.channel, discord.Thread):
            await ctx.send('This command can only be used in a ModMail thread', ephemeral=True)
            return
        
        ModMailMapping = self.tables.ModMailMapping
        mapping = ModMailMapping.select().where(ModMailMapping.user_thread == str(ctx.channel.id)).first()
        proxy_mapping = ModMailMapping.select().where(ModMailMapping.proxy_thread == str(ctx.channel.id)).first()
        proxy = False

        if not mapping:
            mapping = proxy_mapping
            proxy = True
        elif not mapping.user_thread:
            mapping = proxy_mapping
            proxy = True

        if not mapping:
            await ctx.send('This thread is not a ModMail thread', ephemeral=True)
            return
        elif not mapping.proxy_thread:
            await ctx.send('This thread is not a ModMail thread', ephemeral=True)
            return
        elif not mapping.user_thread:
            await ctx.send('This thread is not a ModMail thread', ephemeral=True)
            return
        
        destination = self.bot.get_channel(int(mapping.user_thread if proxy else mapping.proxy_thread))

        origin_files = []
        destination_files = []

        for attachment in ctx.message.attachments:
            origin_files.append(await attachment.to_file())
            destination_files.append(await attachment.to_file())

        embed_origin = discord.Embed(description=message, color=discord.Color.purple())
        embed_origin.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed_origin.set_footer(text='To reply, type your message in this thread' if not proxy else 'To reply, use the reply command')

        embed_destination = discord.Embed(description=message, color=discord.Color.purple())
        embed_destination.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed_destination.set_footer(text='To reply, type your message in this thread' if proxy else 'To reply, use the reply command')

        if not ctx.interaction:
            await ctx.message.delete()

        await destination.send(embed=embed_destination, files=destination_files)
        await ctx.send(embed=embed_origin, files=origin_files)

    @chat_group(name='config_modmail', description='Configure ModMail Settings')
    async def config_modmail(self, ctx):
        """Configure ModMail Settings"""
        await self.config_modmail_list_settings(ctx)

    @config_modmail.command(name='create_button', description='Create a ModMail Button')
    async def config_modmail_create_button(self, ctx):
        """Create ModMail Button"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        ModMailSettings = self.tables.ModMailSettings
        settings = ModMailSettings.select().where(ModMailSettings.guild_id == str(ctx.guild.id)).first()
        
        if not settings:
            settings = ModMailSettings(guild_id = str(ctx.guild.id), enabled = False, thread_channel = None, proxy_channel = None, external_creation_channel = None)
            settings.save()

        if not settings.enabled:
            await ctx.send('ModMail is not enabled', ephemeral=True)
            return
        
        await ctx.send('Creating Modmail Button', ephemeral=True)
        await ctx.channel.send('Click to open a ModMail Thread', view=ModMailButton(self))
        
    @config_modmail.command(name='toggle', description='Toggle ModMail')
    async def config_modmail_toggle(self, ctx):
        """Toggle ModMail"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return

        ModMailSettings = self.tables.ModMailSettings
        settings = ModMailSettings.select().where(ModMailSettings.guild_id == str(ctx.guild.id)).first()

        if not settings:
            settings = ModMailSettings(guild_id = str(ctx.guild.id), enabled = True, thread_channel = None, proxy_channel = None, external_creation_channel = None)
            settings.save()
        else:
            settings.enabled = not settings.enabled
            settings.save()

        await ctx.send(f'ModMail is now {"Enabled" if settings.enabled else "Disabled"}', ephemeral=True)

    @config_modmail.command(name='set_moderation_role', description='Set the ModMail Moderation Role')
    async def config_modmail_set_moderation_role(self, ctx, role_id:str):
        """Set the ModMail Moderation Role"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        ModMailSettings = self.tables.ModMailSettings
        settings = ModMailSettings.select().where(ModMailSettings.guild_id == str(ctx.guild.id)).first()

        if not settings:
            settings = ModMailSettings(guild_id = str(ctx.guild.id), enabled = False, thread_channel = None, proxy_channel = None, external_creation_channel = None)
            settings.save()

        if not settings.enabled:
            await ctx.send('ModMail is not enabled', ephemeral=True)
            return
        
        if not settings.proxy_channel:
            await ctx.send('Proxy Channel is not set.', ephemeral=True)
            return
        
        proxy_channel = self.bot.get_channel(int(settings.proxy_channel))

        if not proxy_channel:
            await ctx.send(f'Proxy Channel is not available to {self.bot.user.mention}', ephemeral=True)
            return
        
        role = proxy_channel.guild.get_role(int(role_id))

        if not role:
            await ctx.send(f'Role not available to {self.bot.user.mention}', ephemeral=True)
            return
        
        settings.moderation_role = str(role.id)
        settings.save()

        await ctx.send(f'Moderation Role set to {role.name} in {proxy_channel.guild.name}', ephemeral=True)
        
    @config_modmail.command(name='set_thread_channel', description='Set the ModMail Thread Channel')
    async def config_modmail_set_thread_channel(self, ctx, channel:discord.TextChannel):
        """Set the ModMail Thread Channel"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return

        if channel not in ctx.guild.channels:
            await ctx.send(f'{channel.mention} is not in **{ctx.guild.name}**', ephemeral=True)
            return
        
        ModMailSettings = self.tables.ModMailSettings
        settings = ModMailSettings.select().where(ModMailSettings.guild_id == str(ctx.guild.id)).first()

        if not settings:
            settings = ModMailSettings(guild_id = str(ctx.guild.id), enabled = False, thread_channel = None, proxy_channel = None, external_creation_channel = None)
            settings.save()

        if not settings.enabled:
            await ctx.send('ModMail is not enabled', ephemeral=True)
            return
        
        settings.thread_channel = str(channel.id)
        settings.save()

        await ctx.send(f'Thread Channel set to {channel.mention}', ephemeral=True)
        
    @config_modmail.command(name='set_proxy_channel', description='Set the ModMail Proxy Channel')
    async def config_modmail_set_proxy_channel(self, ctx, channel_id:str):
        """Set the ModMail Proxy Channel"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        ModMailSettings = self.tables.ModMailSettings
        settings = ModMailSettings.select().where(ModMailSettings.guild_id == str(ctx.guild.id)).first()

        if not settings:
            settings = ModMailSettings(guild_id = str(ctx.guild.id), enabled = False, thread_channel = None, proxy_channel = None, external_creation_channel = None)
            settings.save()

        if not settings.enabled:
            await ctx.send('ModMail is not enabled', ephemeral=True)
            return
        
        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            await ctx.send(f'Channel not available to {self.bot.user.mention}', ephemeral=True)
            return
        
        if not (isinstance(channel, discord.TextChannel) or isinstance(channel, discord.ForumChannel)):
            await ctx.send(f'{channel.mention} is not a Text or Forum Channel', ephemeral=True)
            return
        
        settings.proxy_channel = str(channel.id)
        settings.save()

        await ctx.send(f'Proxy Channel set to {channel.mention}', ephemeral=True)

    @config_modmail.command(name='set_external_channel', description='Set the ModMail External Creation Channel')
    async def config_modmail_set_external_channel(self, ctx, channel_id:str):
        """Set the ModMail External Creation Channel"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        ModMailSettings = self.tables.ModMailSettings
        settings = ModMailSettings.select().where(ModMailSettings.guild_id == str(ctx.guild.id)).first()

        if not settings:
            settings = ModMailSettings(guild_id = str(ctx.guild.id), enabled = False, thread_channel = None, proxy_channel = None, external_creation_channel = None)
            settings.save()

        if not settings.enabled:
            await ctx.send('ModMail is not enabled', ephemeral=True)
            return
        
        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            await ctx.send(f'Channel not available to {self.bot.user.mention}', ephemeral=True)
            return
        
        if not isinstance(channel, discord.TextChannel):
            await ctx.send(f'{channel.mention} is not a Text Channel', ephemeral=True)
            return
        
        settings.external_creation_channel = str(channel.id)
        settings.save()

        await ctx.send(f'External Creation Channel set to {channel.mention}', ephemeral=True)

    @config_modmail.command(name='list_settings', description='List ModMail Settings')
    async def config_modmail_list_settings(self, ctx):
        """List ModMail Settings""" 
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return

        ModMailSettings = self.tables.ModMailSettings
        settings = ModMailSettings.select().where(ModMailSettings.guild_id == str(ctx.guild.id)).first()

        if not settings:
            settings = ModMailSettings(guild_id = str(ctx.guild.id), enabled = False, thread_channel = None, proxy_channel = None, external_creation_channel = None)
            settings.save()

        embed = discord.Embed(description=f"**ModMail is {'Enabled' if settings.enabled else 'Disabled'}**\n\n**Thread Channel:** {self.bot.get_channel(int(settings.thread_channel)).mention if settings.thread_channel else 'None'}\n**Proxy Channel:** {self.bot.get_channel(int(settings.proxy_channel)).mention if settings.proxy_channel else 'None'}\n**External Creation Channel:** {self.bot.get_channel(int(settings.external_creation_channel)).mention if settings.external_creation_channel else 'None'}\n**Moderation Role:** {self.bot.get_guild(int(settings.guild_id)).get_role(int(settings.moderation_role)).mention if settings.moderation_role else 'None'}", color=discord.Color.purple())
        embed.set_author(name=f"{ctx.guild.name}", icon_url=ctx.guild.icon.url)
        embed.set_footer(text='ModMail Settings')

        await ctx.send(embed=embed, ephemeral=True)

    @PlasmaCog.listener()
    async def on_message(self, message):
        """Event fired when a message is sent"""
        if message.author.bot:
            return

        if not isinstance(message.channel, discord.Thread):
            return
        
        if message.content.strip().startswith(self.bot.config['presence']['prefix']):
            return
        
        ModMailMapping = self.tables.ModMailMapping
        mapping = ModMailMapping.select().where(ModMailMapping.user_thread == str(message.channel.id)).first()
        proxy_mapping = ModMailMapping.select().where(ModMailMapping.proxy_thread == str(message.channel.id)).first()
        proxy = False

        if not mapping:
            mapping = proxy_mapping
            proxy = True
        elif not mapping.user_thread:
            mapping = proxy_mapping
            proxy = True

        if not mapping:
            return
        elif not mapping.proxy_thread:
            return
        elif not mapping.user_thread:
            return
        
        if proxy:
            return

        destination = self.bot.get_channel(int(mapping.proxy_thread))

        origin_files = []
        destination_files = []

        for attachment in message.attachments:
            origin_files.append(await attachment.to_file())
            destination_files.append(await attachment.to_file())

        embed_origin = discord.Embed(description=message.content, color=discord.Color.purple())
        embed_origin.set_author(name=message.author.name, icon_url=message.author.avatar.url)
        embed_origin.set_footer(text='To reply, type your message in this thread')

        embed_destination = discord.Embed(description=message.content, color=discord.Color.purple())
        embed_destination.set_author(name=message.author.name, icon_url=message.author.avatar.url)
        embed_destination.set_footer(text='To reply, use the reply command')

        await message.delete()
        await message.channel.send(embed=embed_origin, files=origin_files)
        await destination.send(embed=embed_destination, files=destination_files)
            

async def setup(bot):
    new_cog = ModMail(bot)

    class ModMailSettings(bot.database.base_model):
        """Represents a Guild's ModMail Settings"""
        db_id = peewee.AutoField(primary_key=True)
        guild_id = peewee.TextField()
        enabled = peewee.BooleanField(default=True)
        moderation_role = peewee.TextField(null=True)
        thread_channel = peewee.TextField(null=True)
        proxy_channel = peewee.TextField(null=True)
        external_creation_channel = peewee.TextField(null=True)

    class ModMailMapping(bot.database.base_model):
        """Represents a ModMail Thread"""
        db_id = peewee.AutoField(primary_key=True)
        guild_id = peewee.TextField()
        user_thread = peewee.TextField()
        proxy_thread = peewee.TextField()

    new_cog.register_tables(
        [
            ModMailSettings,
            ModMailMapping
        ]
    )

    await bot.add_cog(new_cog)
    bot.add_view(ModMailButton(new_cog))
    
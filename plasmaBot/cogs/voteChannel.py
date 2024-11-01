import peewee
import asyncio

import discord

from plasmaBot import Client
from plasmaBot.cog import PlasmaCog, chat_group
from plasmaBot.database import aio_first

from discord.ext.commands import guild_only


class VoterCommunicationModal(discord.ui.Modal):
    """Voter Communication Modal"""

    # Define the Components of the Modal
    subject = discord.ui.TextInput(
        label='Subject', 
        required=True, 
        custom_id='vcm_subject', 
        placeholder='VoteChannel Subject', 
        max_length=100
    )
    message = discord.ui.TextInput(
        label='Message', 
        required=True, 
        custom_id='vcm_message', 
        placeholder='First Message', 
        style=discord.TextStyle.paragraph
    )

    def __init__(self, cog, user, *, timeout=None, is_moderator=False):
        self.cog = cog

        super().__init__(title='New Approval Thread', timeout=timeout)

    async def on_submit(self, interaction: discord.Interaction):
        """Submit Callback"""
        subject_value = self.subject.value
        message_value = self.message.value

        await self.cog.start_approval_thread(interaction, subject=subject_value, message=message_value, additionalUsers=[])
        

class VoterCommunicationButton(discord.ui.View):
    """Voter Communication Button"""

    def __init__(self, cog, *, timeout=None):
        self.cog = cog
        super().__init__(timeout=timeout)

    @discord.ui.button(label='Create Approval Thread', style=discord.ButtonStyle.blurple, custom_id='create_approval_thread')
    async def open_votechannel_modal(self, interaction: discord.Interaction, button: discord.Button):
        """Create Approval Thread Callback"""
        VoteChannelSettings = self.cog.tables.VoteChannelSettings
        settings = await aio_first(VoteChannelSettings.select().where(VoteChannelSettings.channel_id == str(interaction.channel.id)))

        if not settings:
            settings = VoteChannelSettings(channel_id = str(interaction.channel.id))
            await settings.aio_save()

        if not settings.enabled:
            await interaction.response.send_message('This Channel does not have Voting enabled', ephemeral=True)
            return
        
        if not settings.proxy_channel:
            await interaction.response.send_message('Proxy Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        proxy_channel = self.cog.bot.get_channel(int(settings.proxy_channel))

        if not proxy_channel:
            await interaction.response.send_message(f'Proxy Channel is not available to {self.cog.bot.user.mention}', ephemeral=True)
            return
        
        if not (isinstance(proxy_channel, discord.TextChannel) or isinstance(proxy_channel, discord.ForumChannel)):
            await interaction.response.send_message('Proxy Channel is not a Text or Forum Channel. Contact an Administrator to have this fixed', ephemeral=True)
            return
        
        if not settings.moderation_role:
            await interaction.response.send_message('Moderation Role is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        moderation_role = proxy_channel.guild.get_role(int(settings.moderation_role))

        if not moderation_role:
            await interaction.response.send_message(f'Moderation Role is not available to {self.cog.bot.user.mention}', ephemeral=True)
            return
        
        await interaction.response.send_modal(
            VoterCommunicationModal(
                self.cog, 
                interaction.user, 
                is_moderator=(interaction.user.guild_permissions.manage_messages or interaction.user.id in self.bot.developers)
            )
        )

class VoteChannels(PlasmaCog):
    """Mod Messaging Cog"""

    def __init__(self, bot: Client):
        super().__init__(bot)

    @chat_group(name='approvals', description='Approval Commands')
    @guild_only()
    async def approvals(self, ctx):
        """Approval Commands"""
        pass

    async def start_approval_thread(self, interaction: discord.Interaction, subject: str = None, message: str = None, *, additionalUsers: list = []):
        """Create a Approval Thread"""

        VoteChannelSettings = self.tables.VoteChannelSettings
        settings = await aio_first(VoteChannelSettings.select().where(VoteChannelSettings.channel_id == str(interaction.channel.id)))

        if not settings:
            settings = VoteChannelSettings(channel_id = str(interaction.channel.id))
            await settings.aio_save()
        
        if not settings.enabled:
            await interaction.response.send_message('This is not a Vote Channel', ephemeral=True)
            return False
        
        if not settings.proxy_channel:
            await interaction.response.send_message('Proxy Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return False
        
        proxy_channel = self.bot.get_channel(int(settings.proxy_channel))

        if not proxy_channel:
            await interaction.response.send_message(f'Proxy Channel is not available to {self.bot.user.mention}', ephemeral=True)
            return False
        
        if not (isinstance(proxy_channel, discord.TextChannel) or isinstance(proxy_channel, discord.ForumChannel)):
            await interaction.response.send_message('Proxy Channel is not a Text or Forum Channel. Contact an Administrator to have this fixed', ephemeral=True)
            return False
        
        if not settings.moderation_role:
            await interaction.response.send_message('Moderation Role is not set. Contact an Administrator to set this up.', ephemeral=True)
            return False
        
        moderation_role = proxy_channel.guild.get_role(int(settings.moderation_role))

        if not moderation_role:
            await interaction.response.send_message(f'Moderation Role is not available to {self.bot.user.mention}', ephemeral=True)
            return False
        
        thread_channel_thread = await interaction.channel.create_thread(name=f'Option Approval ({interaction.user.name}): {subject}', type=discord.ChannelType.private_thread, invitable=True)
        await thread_channel_thread.add_user(interaction.user)

        for user in additionalUsers:
            if not user == interaction.user:
                await thread_channel_thread.add_user(user)

        if not isinstance(proxy_channel, discord.ForumChannel):
            proxy_channel_thread = await proxy_channel.create_thread(name=f'Option Approval ({interaction.user.name} - {interaction.user.id}): {subject}', type=discord.ChannelType.public_thread, invitable=True)
            
            for member in proxy_channel.members:
                if moderation_role in member.roles:
                    await proxy_channel_thread.add_user(member)
        else:
            proxy_channel_thread, proxy_message = await proxy_channel.create_thread(name=f'Option Approval ({interaction.user.name} - {interaction.user.id}): {subject}', content=f'**{interaction.user.name}** has started a VoteChannel Thread')

            for member in proxy_channel.guild.members:
                if moderation_role in member.roles:
                    await proxy_channel_thread.add_user(member)

        VoteChannelMapping = self.tables.VoteChannelMapping

        mapping = VoteChannelMapping(guild_id = str(interaction.guild.id), user_thread = str(thread_channel_thread.id), proxy_thread = str(proxy_channel_thread.id))
        await mapping.aio_save()

        thread_embed = discord.Embed(description='This is an Approval Thread. You can use this to submit an option for voting. Please be patient while we respond to your request.', color=discord.Color.purple())
        thread_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
        thread_embed.set_footer(text='To reply, type your message in this thread')

        await thread_channel_thread.send(embed=thread_embed)

        proxy_embed = discord.Embed(description=f'**{interaction.user.name}** has started a VoteChannel Thread. To reply to this thread, use the `/approvals reply` command.', color=discord.Color.purple())
        proxy_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
        proxy_embed.set_footer(text='To reply, use the `/approvals reply` command')

        await proxy_channel_thread.send(embed=proxy_embed)

        first_message_embed_origin = discord.Embed(description=message, color=discord.Color.purple())
        first_message_embed_origin.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
        first_message_embed_origin.set_footer(text='To reply, type your message in this thread')

        await thread_channel_thread.send(embed=first_message_embed_origin)

        first_message_embed_destination = discord.Embed(description=message, color=discord.Color.purple())
        first_message_embed_destination.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
        first_message_embed_destination.set_footer(text='To reply, use the `/approvals reply` command')

        await proxy_channel_thread.send(embed=first_message_embed_destination)

        await interaction.response.send_message(f'Approval Thread Created! See <#{thread_channel_thread.id}>', ephemeral=True)

    @approvals.command(name='close', description='Close an Approval Thread')
    async def votechannel_close(self, ctx):
        """Close a VoteChannel Thread"""        
        if not isinstance(ctx.channel, discord.Thread):
            await ctx.send('This command can only be used in an Approval thread', ephemeral=True)
            return
        
        VoteChannelMapping = self.tables.VoteChannelMapping
        mapping = await aio_first(VoteChannelMapping.select().where(VoteChannelMapping.user_thread == str(ctx.channel.id)))
        proxy_mapping = await aio_first(VoteChannelMapping.select().where(VoteChannelMapping.proxy_thread == str(ctx.channel.id)))
        proxy = False

        if not mapping:
            mapping = proxy_mapping
            proxy = True
        elif not mapping.user_thread:
            mapping = proxy_mapping
            proxy = True

        if not mapping:
            await ctx.send('This thread is not an Approval thread', ephemeral=True)
            return
        
        if not mapping.proxy_thread:
            await ctx.send('This thread is not an Approval thread', ephemeral=True)
            return
        elif not mapping.user_thread:
            await ctx.send('This thread is not an Approval thread', ephemeral=True)
            return
        
        destination = self.bot.get_channel(int(mapping.user_thread if proxy else mapping.proxy_thread))

        embed = discord.Embed(description='This thread has been closed.', color=discord.Color.purple())
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        embed.set_footer(text='Thank you for suggesting an option!')

        await destination.send(embed=embed)
        await ctx.send(embed=embed)

        await destination.edit(locked=True)
        await ctx.channel.edit(locked=True)

        await asyncio.sleep(300)

        await destination.edit(archived=True)
        await ctx.channel.edit(archived=True)

    @approvals.command(name='reply', description='Reply to an Approval Thread')
    async def reply(self, ctx, *,  message:str):
        """Reply to an Approval Thread"""
        if not isinstance(ctx.channel, discord.Thread):
            await ctx.send('This command can only be used in an Approval thread', ephemeral=True)
            return
        
        VoteChannelMapping = self.tables.VoteChannelMapping
        mapping = await aio_first(VoteChannelMapping.select().where(VoteChannelMapping.user_thread == str(ctx.channel.id)))
        proxy_mapping = await aio_first(VoteChannelMapping.select().where(VoteChannelMapping.proxy_thread == str(ctx.channel.id)))
        proxy = False

        if not mapping:
            mapping = proxy_mapping
            proxy = True
        elif not mapping.user_thread:
            mapping = proxy_mapping
            proxy = True

        if not mapping:
            await ctx.send('This thread is not an Approval thread', ephemeral=True)
            return
        
        if not mapping.proxy_thread:
            await ctx.send('This thread is not an Approval thread', ephemeral=True)
            return
        elif not mapping.user_thread:
            await ctx.send('This thread is not an Approval thread', ephemeral=True)
            return
        
        destination = self.bot.get_channel(int(mapping.user_thread if proxy else mapping.proxy_thread))

        origin_files = []
        destination_files = []

        for attachment in ctx.message.attachments:
            origin_files.append(await attachment.to_file())
            destination_files.append(await attachment.to_file())

        embed_origin = discord.Embed(description=message, color=discord.Color.purple())
        embed_origin.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed_origin.set_footer(text='To reply, type your message in this thread' if not proxy else 'To reply, use the `/approvals reply` command')

        embed_destination = discord.Embed(description=message, color=discord.Color.purple())
        embed_destination.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed_destination.set_footer(text='To reply, type your message in this thread' if proxy else 'To reply, use the `/approvals reply` command')

        if not ctx.interaction:
            await ctx.message.delete()

        await destination.send(embed=embed_destination, files=destination_files)
        await ctx.send(embed=embed_origin, files=origin_files)

    @chat_group(name='config_vote_channel', description='Configure Vote Channel Settings')
    @guild_only()
    async def config_vote_channel(self, ctx):
        """Configure VoteChannel Settings"""
        await self.config_vote_channel_list_settings(ctx)
        
    @config_vote_channel.command(name='toggle', description='Toggle Vote Channel')
    async def config_vote_channel_toggle(self, ctx):
        """Toggle Vote Channel"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return

        VoteChannelSettings = self.tables.VoteChannelSettings
        settings = await aio_first(VoteChannelSettings.select().where(VoteChannelSettings.channel_id == str(ctx.channel.id)))

        if not settings:
            settings = VoteChannelSettings(channel_id = str(ctx.channel.id))
            await settings.aio_save()
        else:
            settings.enabled = not settings.enabled
            await settings.aio_save()

        await ctx.send(f'Voting is now {"Enabled" if settings.enabled else "Disabled"}', ephemeral=True)

    @config_vote_channel.command(name='toggle_approval', description='Toggle Vote Channel Approval Requirement')
    async def config_vote_channel_toggle_approval(self, ctx):
        """Toggle Vote Channel Approval Requirement"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return

        VoteChannelSettings = self.tables.VoteChannelSettings
        settings = await aio_first(VoteChannelSettings.select().where(VoteChannelSettings.channel_id == str(ctx.channel.id)))

        if not settings:
            settings = VoteChannelSettings(channel_id = str(ctx.channel.id))
            await settings.aio_save()

        if not settings.enabled:
            await ctx.send('This is not a Vote Channel', ephemeral=True)
            return
        
        settings.require_approval = not settings.require_approval
        await settings.aio_save()

        await ctx.send(f'Approval Requirement is now {"Enabled" if settings.require_approval else "Disabled"}', ephemeral=True)

    @config_vote_channel.command(name='toggle_vote_buttons', description='Toggle Vote Channel Vote Buttons')
    async def config_vote_channel_toggle_vote_buttons(self, ctx):
        """Toggle Vote Channel Vote Buttons"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return

        VoteChannelSettings = self.tables.VoteChannelSettings
        settings = await aio_first(VoteChannelSettings.select().where(VoteChannelSettings.channel_id == str(ctx.channel.id)))

        if not settings:
            settings = VoteChannelSettings(channel_id = str(ctx.channel.id))
            await settings.aio_save()

        if not settings.enabled:
            await ctx.send('This is not a Vote Channel', ephemeral=True)
            return
        
        settings.add_vote_buttons = not settings.add_vote_buttons
        await settings.aio_save()

        await ctx.send(f'Vote Buttons are now {"Enabled" if settings.add_vote_buttons else "Disabled"}', ephemeral=True)

    @config_vote_channel.command(name='set_moderation_role', description='Set the Vote Channel Moderation Role')
    async def config_vote_channel_set_moderation_role(self, ctx, role_id:str):
        """Set the Vote Channel Moderation Role"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        VoteChannelSettings = self.tables.VoteChannelSettings
        settings = await aio_first(VoteChannelSettings.select().where(VoteChannelSettings.channel_id == str(ctx.channel.id)))

        if not settings:
            settings = VoteChannelSettings(channel_id = str(ctx.channel.id))
            await settings.aio_save()

        if not settings.enabled:
            await ctx.send('This is not a Vote Channel', ephemeral=True)
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
        await settings.aio_save()

        await ctx.send(f'Moderation Role set to {role.name} in {proxy_channel.guild.name}', ephemeral=True)
        
    @config_vote_channel.command(name='set_proxy_channel', description='Set the Vote Channel Proxy Channel')
    async def config_vote_channel_set_proxy_channel(self, ctx, channel_id:str):
        """Set the Vote Channel Proxy Channel"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        VoteChannelSettings = self.tables.VoteChannelSettings
        settings = await aio_first(VoteChannelSettings.select().where(VoteChannelSettings.channel_id == str(ctx.channel.id)))

        if not settings:
            settings = VoteChannelSettings(channel_id = str(ctx.channel.id))
            await settings.aio_save()

        if not settings.enabled:
            await ctx.send('This is not a Vote Channel', ephemeral=True)
            return
        
        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            await ctx.send(f'Channel not available to {self.bot.user.mention}', ephemeral=True)
            return
        
        if not (isinstance(channel, discord.TextChannel) or isinstance(channel, discord.ForumChannel)):
            await ctx.send(f'{channel.mention} is not a Text or Forum Channel', ephemeral=True)
            return
        
        settings.proxy_channel = str(channel.id)
        await settings.aio_save()

        await ctx.send(f'Proxy Channel set to {channel.mention}', ephemeral=True)

    @config_vote_channel.command(name='list_settings', description='List Vote Channel Settings')
    async def config_vote_channel_list_settings(self, ctx):
        """List Vote Channel Settings""" 
        try:
            if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
                await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
                return

            VoteChannelSettings = self.tables.VoteChannelSettings
            settings = await aio_first(VoteChannelSettings.select().where(VoteChannelSettings.channel_id == str(ctx.channel.id)))

            if not settings:
                settings = VoteChannelSettings(channel_id = str(ctx.channel.id))
                await settings.aio_save()

            if not settings.enabled:
                embed = discord.Embed(description='**Voting is Disabled for this Channel**', color=discord.Color.purple())
                embed.set_author(name=f"{ctx.guild.name}", icon_url=ctx.guild.icon.url)
                embed.set_footer(text='Vote Channel Settings')
            else:
                embed = discord.Embed(description=f"**Voting is Enabled for this channel**\n\n**Require Approval:** {settings.require_approval}\n**Add Vote Buttons:** {settings.add_vote_buttons}\n**Proxy Channel:** {self.bot.get_channel(int(settings.proxy_channel)).mention if settings.proxy_channel else 'None'}\n**Moderation Role**: {settings.moderation_role}", color=discord.Color.purple())
                embed.set_author(name=f"{ctx.guild.name}", icon_url=ctx.guild.icon.url)
                embed.set_footer(text='Vote Channel Settings')

            await ctx.send(embed=embed, ephemeral=True)
        except Exception:
            import traceback
            await ctx.send(traceback.format_exc(), ephemeral=True)

    @PlasmaCog.listener()
    async def on_message(self, message):
        """Event fired when a message is sent"""
        if message.author.bot:
            return
        
        if message.content.strip().startswith(self.bot.config['presence']['prefix']):
            return

        VoteChannelSettings = self.tables.VoteChannelSettings
        settings = await aio_first(VoteChannelSettings.select().where(VoteChannelSettings.channel_id == str(message.channel.id)))

        if settings:
            if settings.enabled and settings.add_vote_buttons:
                await message.add_reaction('👍')
                await message.add_reaction('👎')
                await message.add_reaction('🤷')

            if settings.enabled and settings.require_approval:
                try:
                    last_approval_message = await message.channel.fetch_message(settings.last_approval_message)
                    await last_approval_message.delete()
                except:
                    pass

                new_approval_message = await message.channel.send('Want to submit an option for voting?', view=VoterCommunicationButton(self))
                
                settings.last_approval_message = str(new_approval_message.id)
                await settings.aio_save()            

        if not isinstance(message.channel, discord.Thread):
            return
        
        VoteChannelMapping = self.tables.VoteChannelMapping
        mapping = await aio_first(VoteChannelMapping.select().where(VoteChannelMapping.user_thread == str(message.channel.id)))
        proxy_mapping = await aio_first(VoteChannelMapping.select().where(VoteChannelMapping.proxy_thread == str(message.channel.id)))
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
        embed_destination.set_footer(text='To reply, use the `/approvals reply` command')

        await message.delete()
        await message.channel.send(embed=embed_origin, files=origin_files)
        await destination.send(embed=embed_destination, files=destination_files)
            

async def setup(bot):
    new_cog = VoteChannels(bot)

    class VoteChannelSettings(bot.database.base_model):
        """Represents a Guild's Vote Channel Settings"""
        db_id = peewee.AutoField(primary_key=True)
        channel_id = peewee.TextField()
        enabled = peewee.BooleanField(default=False)
        require_approval = peewee.BooleanField(default=False)
        last_approval_message = peewee.TextField(null=True)
        add_vote_buttons = peewee.BooleanField(default=False)
        moderation_role = peewee.TextField(null=True)
        proxy_channel = peewee.TextField(null=True)

    class VoteChannelMapping(bot.database.base_model):
        """Represents an Approval Thread"""
        db_id = peewee.AutoField(primary_key=True)
        channel_id = peewee.TextField()
        user_thread = peewee.TextField()
        proxy_thread = peewee.TextField()

    new_cog.register_tables(
        [
            VoteChannelSettings,
            VoteChannelMapping
        ]
    )

    await bot.add_cog(new_cog)
    bot.add_view(VoterCommunicationButton(new_cog))
    
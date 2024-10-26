import re
import peewee

import discord

from plasmaBot import Client
from plasmaBot.cog import PlasmaCog, chat_group


class AutoResponseVoter(discord.ui.View):
    """AutoResponse Voter Module"""

    def __init__(self, cog: PlasmaCog, settings, message: discord.Message, triggeringUser: discord.Member, *, timeout=43200):
        self.cog = cog
        self.settings = settings
        self.message = message
        self.triggeringUser = triggeringUser

        self.users = set()

        super().__init__(timeout=timeout)

    async def on_timeout(self):
        """Timeout Callback"""
        await self.message.edit(view=None)
        self.stop()

    @discord.ui.button(label='Not Relevant?', style=discord.ButtonStyle.primary)
    async def onClick(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Submit Callback"""
        self.users.add(interaction.user)

        if len(self.users) >= self.settings.removalVoteThreshold or interaction.user == self.triggeringUser:
            await self.message.delete()
            await interaction.response.send_message(f'Thanks for your feedback! This message has been deleted.', ephemeral=True)
            return
        else:
            await interaction.response.send_message(f'Thanks for your feedback! This message will be deleted if it hits the deletion threshold.', ephemeral=True)


class AutoResponseEditModal(discord.ui.Modal):
    """AutoResponse Edit Modal"""

    def __init__(self, cog: PlasmaCog, settings, hotword:str='', response:str='', *, timeout=None):
        self.cog = cog
        self.settings = settings
        self.hotword = hotword
        self.response = response

        self.hotwordItem = discord.ui.TextInput(
            custom_id = 'autoresponse_hotword',
            label = 'HotWord',
            placeholder = 'Enter HotWord',
            required = True,
            default = self.hotword
        )

        self.responseItem = discord.ui.TextInput(
            custom_id = 'autoresponse_response',
            label = 'Response',
            placeholder = 'Enter Response',
            required = True,
            default = self.response,
            style = discord.TextStyle.paragraph
        )

        super().__init__(title='Edit AutoResponse', timeout=timeout)

        self.add_item(self.hotwordItem)
        self.add_item(self.responseItem)

    async def on_submit(self, interaction: discord.Interaction):
        """Submit Callback"""
        hotword = self.hotwordItem.value
        response = self.responseItem.value

        AutoResponseEntry = self.cog.tables.AutoResponseEntry
        entry = AutoResponseEntry.select().where(AutoResponseEntry.guild_id == self.settings.guild_id, AutoResponseEntry.hotword_regex == hotword).first()

        if not entry:
            entry = AutoResponseEntry(
                guild_id = self.settings.guild_id,
                hotword_regex = hotword,
                response = response
            )
            entry.save()

            await interaction.response.send_message('AutoResponse Entry Created', ephemeral=True)
            return
        
        entry.response = response
        entry.save()

        await interaction.response.send_message('AutoResponse Entry Updated', ephemeral=True)


class AutoResponseEditView(discord.ui.View):
    """AutoResponse Edit View"""

    def __init__(self, cog: PlasmaCog, settings, message: discord.Message, triggeringUser: discord.Member, hotword:str='', response:str='', *, timeout=30):
        self.cog = cog
        self.settings = settings
        self.message = message
        self.triggeringUser = triggeringUser
        self.hotword = hotword
        self.response = response

        super().__init__(timeout=timeout)

    async def on_timeout(self):
        """Timeout Callback"""
        await self.message.delete()
        self.stop()

    @discord.ui.button(label='Edit Entry', style=discord.ButtonStyle.primary)
    async def onClick(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Submit Callback"""
        if not interaction.user == self.triggeringUser:
            await interaction.response.send_message('You are not authorized to use this button.', ephemeral=True)
            return
        
        await interaction.response.send_modal(
            AutoResponseEditModal(
                self.cog,
                self.settings,
                self.hotword,
                self.response
            )
        )

        await self.message.delete()
        self.stop()


class AutoResponse(PlasmaCog):
    """Automatic HotWord Response System"""

    def __init__(self, bot: Client):
        super().__init__(bot)

    @chat_group(name='config_autoresponse', description='Configure AutoResponse Settings', fallback='list_settings')
    async def config_autoresponse(self, ctx):
        """Configure AutoResponse Settings"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        AutoResponseSettings = self.tables.AutoReponseSettings
        settings = AutoResponseSettings.get_or_none(guild_id=ctx.guild.id)

        if not settings:
            settings = AutoResponseSettings(
                guild_id= str(ctx.guild.id)
            )
            settings.save()

        if not settings.enabled:
            embed = discord.Embed(description='**AutoResponse is Disabled**', color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            embed.set_footer(text='AutoResponse Settings')
        else:
            embed = discord.Embed(
                description=f'**AutoResponse is Enabled**\n\n**Removal Vote Threshold:** {str(settings.removalVoteThreshold)}\n**Cooldown:** {str(settings.cooldown)}',
                color=discord.Color.purple()
            )
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            embed.set_footer(text='AutoResponse Settings')

        await ctx.send(embed=embed, ephemeral=True)

    @config_autoresponse.command(name='toggle', description='Toggle AutoResponse')
    async def toggle(self, ctx):
        """Toggle AutoResponse"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return

        AutoResponseSettings = self.tables.AutoReponseSettings
        settings = AutoResponseSettings.get_or_none(guild_id=ctx.guild.id)

        if not settings:
            settings = AutoResponseSettings(
                guild_id= str(ctx.guild.id)
            )
            settings.save()

        settings.enabled = not settings.enabled
        settings.save()

        await ctx.send(f'AutoResponse is now {"Enabled" if settings.enabled else "Disabled"}', ephemeral=True)

    @config_autoresponse.command(name='set_threshold', description='Set Removal Vote Threshold')
    async def set_threshold(self, ctx, threshold: int):
        """Set Removal Vote Threshold"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return

        AutoResponseSettings = self.tables.AutoReponseSettings
        settings = AutoResponseSettings.get_or_none(guild_id=ctx.guild.id)

        if not settings:
            settings = AutoResponseSettings(
                guild_id= str(ctx.guild.id)
            )
            settings.save()

        settings.removalVoteThreshold = threshold
        settings.save()

        await ctx.send(f'Removal Vote Threshold set to {threshold}', ephemeral=True)

    @config_autoresponse.command(name='list_responses', description='List AutoResponse Entries')
    async def list_responses(self, ctx):
        """List AutoResponse Entries"""
        AutoResponseEntry = self.tables.AutoResponseEntry
        entries = AutoResponseEntry.select().where(AutoResponseEntry.guild_id == ctx.guild.id)

        AutoResponseSettings = self.tables.AutoReponseSettings
        settings = AutoResponseSettings.get_or_none(guild_id=ctx.guild.id)

        if not settings:
            settings = AutoResponseSettings(
                guild_id= str(ctx.guild.id)
            )
            settings.save()

        if not settings.enabled:
            await ctx.send('AutoResponse is Disabled', ephemeral=True)

        if not entries:
            await ctx.send('No AutoResponse Entries found', ephemeral=True)
            return

        embed = discord.Embed(title='AutoResponse Entries', color=discord.Color.purple())
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)

        for entry in entries:
            embed.add_field(name=f'{entry.db_id}: {entry.hotword_regex}', value=entry.response, inline=False)

        await ctx.send(embed=embed, ephemeral=True)

    @config_autoresponse.command(name='set_cooldown', description='Set AutoResponse Cooldown')
    async def set_cooldown(self, ctx, cooldown:int):
        """Set AutoResponse Cooldown"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return

        AutoResponseSettings = self.tables.AutoReponseSettings
        settings = AutoResponseSettings.get_or_none(guild_id=ctx.guild.id)

        if not settings:
            settings = AutoResponseSettings(
                guild_id= str(ctx.guild.id)
            )
            settings.save()

        settings.cooldown = cooldown
        settings.save()

        await ctx.send(f'AutoResponse Cooldown set to {cooldown}', ephemeral=True)

    @config_autoresponse.command(name='add_response', description='Add AutoResponse Entry')
    async def add_response(self, ctx, hotword_regex:str, *, response:str=''):
        """Add AutoResponse Entry"""

        if not (ctx.author.guild_permissions.manage_guild or ctx.author in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        AutoResponseSettings = self.tables.AutoReponseSettings
        settings = AutoResponseSettings.get_or_none(guild_id=ctx.guild.id)

        if not settings:
            settings = AutoResponseSettings(
                guild_id= str(ctx.guild.id)
            )
            settings.save()

        if not settings.enabled:
            await ctx.send('AutoResponse is Disabled', ephemeral=True)

        AutoResponseEntry = self.tables.AutoResponseEntry
        entry = AutoResponseEntry.select().where(AutoResponseEntry.guild_id == ctx.guild.id, AutoResponseEntry.hotword_regex == hotword_regex).first()

        if entry:
            await ctx.send(f'AutoResponse Entry already exists as #{entry.db_id}', ephemeral=True)
            return

        if ctx.interaction:
            await ctx.interaction.response.send_modal(
                AutoResponseEditModal(
                    self,
                    settings,
                    hotword_regex,
                    response
                )
            )
        else:
            message = await ctx.send('Click below to edit this entry.', ephemeral=True)
            view = AutoResponseEditView(self, settings, message, ctx.author, hotword_regex, entry.response if entry else response)
            await message.edit(view=view)

    @config_autoresponse.command(name='remove_response', description='Remove AutoResponse Entry')
    async def remove_response(self, ctx, entry_id:int):
        """Remove AutoResponse Entry"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return

        AutoResponseEntry = self.tables.AutoResponseEntry
        entry = AutoResponseEntry.select().where(AutoResponseEntry.guild_id == ctx.guild.id, AutoResponseEntry.entry_id == entry_id).first()

        if not entry:
            await ctx.send('AutoResponse Entry not found', ephemeral=True)
            return

        entry.delete_instance()
        await ctx.send('AutoResponse Entry Removed', ephemeral=True)

    @config_autoresponse.command(name='edit_response', description='Edit AutoResponse Entry')
    async def edit_response(self, ctx, entry_id:int):
        """Edit AutoResponse Entry"""

        if not (ctx.author.guild_permissions.manage_guild or ctx.author in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        AutoResponseSettings = self.tables.AutoReponseSettings
        settings = AutoResponseSettings.get_or_none(guild_id=ctx.guild.id)

        if not settings:
            settings = AutoResponseSettings(
                guild_id= str(ctx.guild.id)
            )
            settings.save()

        if not settings.enabled:
            await ctx.send('AutoResponse is Disabled', ephemeral=True)

        AutoResponseEntry = self.tables.AutoResponseEntry
        entry = AutoResponseEntry.select().where(AutoResponseEntry.guild_id == ctx.guild.id, AutoResponseEntry.db_id == entry_id).first()

        if not entry:
            await ctx.send(f'AutoResponse Entry does not exist.', ephemeral=True)
            return

        if ctx.interaction:
            await ctx.interaction.response.send_modal(
                AutoResponseEditModal(
                    self,
                    settings,
                    entry.hotword_regex,
                    entry.response
                )
            )
        else:
            message = await ctx.send('Click below to edit this entry.', ephemeral=True)
            view = AutoResponseEditView(self, settings, message, ctx.author, entry.hotword_regex, entry.response)
            await message.edit(view=view)

    @config_autoresponse.command(name='add_channel_limit', description='Add Channel Limit to AutoResponse Entry')
    async def add_channel_limit(self, ctx, entry_id:int, channel:discord.TextChannel):
        """Add Channel Limit to AutoResponse Entry"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return

        AutoResponseEntry = self.tables.AutoResponseEntry
        entry = AutoResponseEntry.select().where(AutoResponseEntry.guild_id == ctx.guild.id, AutoResponseEntry.db_id == entry_id).first()

        if not entry:
            await ctx.send('AutoResponse Entry not found', ephemeral=True)
            return

        AutoResponseEntryChannelLimit = self.tables.AutoResponseEntryChannelLimit
        limit = AutoResponseEntryChannelLimit.select().where(AutoResponseEntryChannelLimit.entry == entry, AutoResponseEntryChannelLimit.channel_id == channel.id).first()

        if limit:
            await ctx.send('Channel Limit already exists', ephemeral=True)
            return

        limit = AutoResponseEntryChannelLimit(
            entry=entry,
            channel_id=channel.id
        )
        limit.save()

        await ctx.send('Channel Limit Added', ephemeral=True)

    @config_autoresponse.command(name='remove_channel_limit', description='Remove Channel Limit from AutoResponse Entry')
    async def remove_channel_limit(self, ctx, entry_id:int, channel:discord.TextChannel):
        """Remove Channel Limit from AutoResponse Entry"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return

        AutoResponseEntry = self.tables.AutoResponseEntry
        entry = AutoResponseEntry.select().where(AutoResponseEntry.guild_id == ctx.guild.id, AutoResponseEntry.db_id==entry_id).first()

        if not entry:
            await ctx.send('AutoResponse Entry not found', ephemeral=True)
            return

        AutoResponseEntryChannelLimit = self.tables.AutoResponseEntryChannelLimit
        limit = AutoResponseEntryChannelLimit.select().where(AutoResponseEntryChannelLimit.entry == entry, AutoResponseEntryChannelLimit.channel_id == channel.id).first()

        if not limit:
            await ctx.send('Channel Limit not found', ephemeral=True)
            return

        limit.delete_instance()
        await ctx.send('Channel Limit Removed', ephemeral=True)

    @PlasmaCog.listener()
    async def on_message(self, message):
        """Listen for Hotword Triggers and Respond Appropriately"""
        # Ignore bots
        if message.author.bot:
            return
        
        # Ignore DMs
        if not message.guild:
            return
        
        # Ignore commands
        if message.content.strip().startswith(self.bot.config['presence']['prefix']):
            return

        # Ignore if no settings
        AutoResponseSettings = self.tables.AutoReponseSettings
        settings = AutoResponseSettings.get_or_none(guild_id=message.guild.id)

        if not settings or not settings.enabled:
            return

        # Check for Hotword Triggers
        AutoResponseEntry = self.tables.AutoResponseEntry
        entries = AutoResponseEntry.select().where(AutoResponseEntry.guild_id == message.guild.id)

        for entry in entries:
            pattern = re.compile(entry.hotword_regex)
            if pattern.search(message.content):
                if entry.channel_limits:
                    if not message.channel.id in [limit.channel_id for limit in entry.channel_limits]:
                        continue

                if settings.cooldown:
                    if entry.last_sent and (message.created_at - entry.last_sent).total_seconds() < settings.cooldown:
                        continue

                entry.last_sent = message.created_at
                entry.save()

                new_message = await message.reply(entry.response)
                view = AutoResponseVoter(self, settings, new_message, message.author)
                await new_message.edit(view=view)
                return


async def setup(bot):
    """Setup cog"""
    new_cog = AutoResponse(bot)

    class AutoReponseSettings(bot.database.base_model):
        """Represents a Guild's AutoResponse Settings"""
        db_id = peewee.AutoField(primary_key=True)
        guild_id = peewee.TextField()
        enabled = peewee.BooleanField(default=False)
        removalVoteThreshold = peewee.IntegerField(default=5)
        cooldown = peewee.IntegerField(default=0)

    class AutoResponseEntry(bot.database.base_model):
        """Represents a Guild's AutoResponse Entry"""
        db_id = peewee.AutoField(primary_key=True)
        guild_id = peewee.TextField()
        hotword_regex = peewee.TextField()
        response = peewee.TextField()
        last_sent = peewee.DateTimeField()

    class AutoResponseEntryChannelLimit(bot.database.base_model):
        """Represents a Channel Limit for a Guild's AutoResponse Entry"""
        db_id = peewee.AutoField(primary_key=True)
        channel_id = peewee.TextField(null=True)
        entry = peewee.ForeignKeyField(AutoResponseEntry, backref='channel_limits')

    new_cog.register_tables(
        [
            AutoReponseSettings,
            AutoResponseEntry,
            AutoResponseEntryChannelLimit
        ]
    )

    await bot.add_cog(new_cog)
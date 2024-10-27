import peewee
import aiohttp

from datetime import datetime, timedelta, timezone

import discord
from discord.ext import tasks

from plasmaBot import Client
from plasmaBot.cog import PlasmaCog, chat_group


class WhisperLogReply(discord.ui.View):
    """Reply View for Whisper Logs"""

    def __init__(self, cog: PlasmaCog):
        self.cog = cog
        super().__init__(timeout=None)

    @discord.ui.button(label='Whisper at this User', style=discord.ButtonStyle.primary, custom_id='whisper_log_reply')
    async def reply(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Reply Callback"""

        WhisperMessage = self.cog.tables.WhisperMessage
        whisper_message = WhisperMessage.select().where(WhisperMessage.log_message_id==interaction.message.id).first()

        if not whisper_message:
            await interaction.response.send_message('This Whisper does not exist in the database.', ephemeral=True)
            return
        
        guild = self.cog.bot.get_guild(int(whisper_message.origin_guild_id))

        if not guild:
            await interaction.response.send_message('The Origin Server for this Whisper is no longer available.', ephemeral=True)
            return
        
        WhisperSettings = self.cog.tables.WhisperSettings
        settings = WhisperSettings.select().where(WhisperSettings.guild_id==whisper_message.origin_guild_id).first()

        if not settings:
            settings = WhisperSettings(
                guild_id = whisper_message.origin_guild_id, 
                enabled = False,
                confirm_moderation = True, 
                log_channel = None, 
                backup_inbox_channel = None
            )

        if not settings.enabled:
            await interaction.response.send_message('Whispering is no longer enabled for the origin Server.', ephemeral=True)
            return

        if not settings.log_channel:
            await interaction.response.send_message('Whisper Log Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        logChannel = self.cog.bot.get_channel(int(settings.log_channel))

        if not logChannel:
            await interaction.response.send_message('Whisper Log Channel is invalid or unaccessible. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        if not settings.backup_inbox_channel:
            await interaction.response.send_message('Whisper Backup Inbox Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        backupInboxChannel = self.cog.bot.get_channel(int(settings.backup_inbox_channel))

        if not backupInboxChannel:
            await interaction.response.send_message('Whisper Backup Inbox Channel is invalid or unaccessible. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        target = guild.get_member(int(whisper_message.user_id))
        origin_user = interaction.user

        if not target:
            await interaction.response.send_message('The Origin User for this Whisper is no longer available.', ephemeral=True)
            return
        
        WhisperBlock = self.cog.tables.WhisperBlock
        whisper_block_check = WhisperBlock.select().where(WhisperBlock.user_id==str(origin_user.id), WhisperBlock.blocked_user_id==str(target.id)).first()

        if whisper_block_check and not target.guild_permissions.manage_messages:
            blocked_embed = discord.Embed(
                title='Blocked User',
                description='You have blocked this User. You cannot Whisper them.',
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=blocked_embed, ephemeral=True)
            return
        
        whisper_block_check_blocked_by = WhisperBlock.select().where(WhisperBlock.user_id==str(target.id), WhisperBlock.blocked_user_id==str(origin_user.id)).first()

        if whisper_block_check_blocked_by and not origin_user.guild_permissions.manage_messages:
            blocked_by_embed = discord.Embed(
                title='Blocked User',
                description='This User has blocked you. You cannot Whisper them.',
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=blocked_by_embed, ephemeral=True)
            return
        
        await self.cog.startWhisper(interaction, settings, origin_user, target, '')
        

class WhisperTargetReply(discord.ui.View):
    """Reply View for Whisper Targets"""

    def __init__(self, cog: PlasmaCog):
        self.cog = cog
        super().__init__(timeout=None)

    @discord.ui.button(label='Reply', style=discord.ButtonStyle.primary, custom_id='whisper_target_reply')
    async def reply(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Reply Callback"""
        WhisperMessage = self.cog.tables.WhisperMessage
        whisper_message = WhisperMessage.select().where(WhisperMessage.inbox_message_id==interaction.message.id).first()

        if not whisper_message:
            await interaction.response.send_message('This Whisper does not exist in the database.', ephemeral=True)
            return
        
        guild = self.cog.bot.get_guild(int(whisper_message.origin_guild_id))

        if not guild:
            await interaction.response.send_message('The Origin Server for this Whisper is no longer available.', ephemeral=True)
            return
        
        WhisperSettings = self.cog.tables.WhisperSettings
        settings = WhisperSettings.select().where(WhisperSettings.guild_id==whisper_message.origin_guild_id).first()

        if not settings:
            settings = WhisperSettings(
                guild_id = whisper_message.origin_guild_id, 
                enabled = False,
                confirm_moderation = True, 
                log_channel = None, 
                backup_inbox_channel = None
            )

        if not settings.enabled:
            await interaction.response.send_message('Whispering is no longer enabled for the origin Server.', ephemeral=True)
            return

        if not settings.log_channel:
            await interaction.response.send_message('Whisper Log Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        logChannel = self.cog.bot.get_channel(int(settings.log_channel))

        if not logChannel:
            await interaction.response.send_message('Whisper Log Channel is invalid or unaccessible. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        if not settings.backup_inbox_channel:
            await interaction.response.send_message('Whisper Backup Inbox Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        backupInboxChannel = self.cog.bot.get_channel(int(settings.backup_inbox_channel))

        if not backupInboxChannel:
            await interaction.response.send_message('Whisper Backup Inbox Channel is invalid or unaccessible. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        target = guild.get_member(int(whisper_message.user_id))
        origin_user = guild.get_member(int(whisper_message.target_id))

        if not target:
            await interaction.response.send_message('The Origin User for this Whisper is no longer available.', ephemeral=True)
            return
        
        WhisperBlock = self.cog.tables.WhisperBlock
        whisper_block_check = WhisperBlock.select().where(WhisperBlock.user_id==str(origin_user.id), WhisperBlock.blocked_user_id==str(target.id)).first()

        if whisper_block_check and not target.guild_permissions.manage_messages:
            blocked_embed = discord.Embed(
                title='Blocked User',
                description='You have blocked this User. You cannot Whisper them.',
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=blocked_embed, ephemeral=True)
            return
        
        whisper_block_check_blocked_by = WhisperBlock.select().where(WhisperBlock.user_id==str(target.id), WhisperBlock.blocked_user_id==str(origin_user.id)).first()

        if whisper_block_check_blocked_by and not origin_user.guild_permissions.manage_messages:
            blocked_by_embed = discord.Embed(
                title='Blocked User',
                description='This User has blocked you. You cannot Whisper them.',
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=blocked_by_embed, ephemeral=True)
            return
        
        await self.cog.startWhisper(interaction, settings, origin_user, target, '')


class WhisperModal(discord.ui.Modal):
    """Whisper Creation Modal"""

    def __init__(self, cog: PlasmaCog, settings, origin_user: discord.Member, target: discord.Member, whisper_message: str, *, timeout=None):
        self.cog = cog
        self.settings = settings
        self.origin_user = origin_user
        self.target = target

        self.messageItem = discord.ui.TextInput(
            custom_id='whisper_message',
            label='Message',
            required=True,
            default=whisper_message,
            style=discord.TextStyle.paragraph
        )

        super().__init__(title=f'Whisper to {self.target}', timeout=timeout)

        self.add_item(self.messageItem)

    async def on_submit(self, interaction: discord.Interaction):
        """Submit Callback"""
        target = self.target
        message = self.messageItem.value

        if not message or message.strip() == '':
            return await interaction.response.send_message('You must provide a message.', ephemeral=True)
        
        await self.cog.sendWhisper(interaction, self.settings, self.origin_user, target, message)


class ModerationWhisperConfirmation(discord.ui.View):
    """Confirmation View for Moderation Whispers"""

    def __init__(self, cog: PlasmaCog, settings, message: discord.Message, origin_user: discord.Member, target: discord.Member, whisper_message: str, *, timeout=30):
        self.cog = cog
        self.settings = settings
        self.origin_user = origin_user
        self.target = target
        self.message = message
        self.whisper_message = whisper_message
        self.thank_you = discord.Embed(title='Thank You!', description='Future Moderation Communication should be handled through ModMail.', color=discord.Color.purple())
        super().__init__(timeout=timeout)

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirmation Callback"""
        await self.cog.startWhisper(interaction, self.settings, self.origin_user, self.target, self.whisper_message)
        await self.message.edit(embed=self.thank_you, view=None)
        self.stop()

    async def on_timeout(self):
        """Timeout Callback"""
        await self.message.edit(embed=self.thank_you, view=None)
        self.stop()


class Whisper(PlasmaCog):
    """Interuser Moderated Communication Platform"""

    def __init__(self, bot: Client):
        super().__init__(bot)
        self.whisper_context_menu = discord.app_commands.ContextMenu(
            name='Whisper',
            callback = self.whisperContextMenu,
            type = discord.AppCommandType.user
        )
        self.bot.tree.add_command(self.whisper_context_menu)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.whisper_context_menu)

    async def whisperContextMenu(self, interaction: discord.Interaction, target: discord.Member):
        """Whisper Context Menu Command"""
        if not interaction.guild:
            await interaction.response.send_message('Whisper Initiation is only available in Servers.', ephemeral=True)
            return

        WhisperSettings = self.tables.WhisperSettings
        settings = WhisperSettings.select().where(WhisperSettings.guild_id == interaction.guild.id).first()

        if not settings:
            settings = WhisperSettings(
                guild_id = str(interaction.guild.id), 
                enabled = False,
                confirm_moderation = True, 
                log_channel = None, 
                backup_inbox_channel = None
            )
            settings.save()

        if not settings.enabled:
            await interaction.response.send_message('Whispering is not enabled', ephemeral=True)
            return
        
        if not settings.log_channel:
            await interaction.response.send_message('Whisper Log Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        logChannel = self.bot.get_channel(int(settings.log_channel))

        if not logChannel:
            await interaction.response.send_message('Whisper Log Channel is invalid or unaccessible. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        if not settings.backup_inbox_channel:
            await interaction.response.send_message('Whisper Backup Inbox Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        backupInboxChannel = self.bot.get_channel(int(settings.backup_inbox_channel))

        if not backupInboxChannel:
            await interaction.response.send_message('Whisper Backup Inbox Channel is invalid or unaccessible. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        WhisperBlock = self.tables.WhisperBlock
        whisper_block_check = WhisperBlock.select().where(WhisperBlock.user_id==str(interaction.user.id), WhisperBlock.blocked_user_id==str(target.id)).first()

        if whisper_block_check and not target.guild_permissions.manage_messages:
            blocked_embed = discord.Embed(
                title='Blocked User',
                description='You have blocked this User. You cannot Whisper them.',
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=blocked_embed, ephemeral=True)
            return
        
        whisper_block_check_blocked_by = WhisperBlock.select().where(WhisperBlock.user_id==str(target.id), WhisperBlock.blocked_user_id==str(interaction.user.id)).first()

        if whisper_block_check_blocked_by and not interaction.user.guild_permissions.manage_messages:
            blocked_by_embed = discord.Embed(
                title='Blocked User',
                description='This User has blocked you. You cannot Whisper them.',
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=blocked_by_embed, ephemeral=True)
            return
        
        if settings.confirm_moderation and target.guild_permissions.manage_messages:
            embed = discord.Embed(title='Moderator Whisper Confirmation', description='You are attempting to Whisper a Moderator. Moderation communication is handled through ModMail. Are you sure you want to proceed?', color=discord.Color.purple())
            embed.set_footer(text='Please confirm to continue, or disregard to cancel.')
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
            sent_confirmation_message = await interaction.original_response()
            view = ModerationWhisperConfirmation(self, settings, sent_confirmation_message, interaction.user, target, '')
            await sent_confirmation_message.edit(view=view)
        else:
            await self.startWhisper(interaction, settings, interaction.user, target, '')

    @chat_group(name='whisper', description='Send a Whisper to a User', fallback='send')
    async def whisper(self, ctx, target: discord.Member, *, message: str=None):
        """Send a Whisper to a User"""
        if not ctx.guild:
            await ctx.send('Whisper Initiation is only available in Servers.', ephemeral=True)
            return

        if not ctx.interaction:
            await ctx.send('Whispering is only available as a Slash Command. Please use `/whisper` instead.')
            return

        WhisperSettings = self.tables.WhisperSettings
        settings = WhisperSettings.select().where(WhisperSettings.guild_id == ctx.guild.id).first()

        if not settings:
            settings = WhisperSettings(
                guild_id = str(ctx.guild.id), 
                enabled = False,
                confirm_moderation = True, 
                log_channel = None, 
                backup_inbox_channel = None
            )
            settings.save()

        if not settings.enabled:
            await ctx.send('Whispering is not enabled', ephemeral=True)
            return
        
        if not settings.log_channel:
            await ctx.send('Whisper Log Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        logChannel = self.bot.get_channel(int(settings.log_channel))

        if not logChannel:
            await ctx.send('Whisper Log Channel is invalid or unaccessible. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        if not settings.backup_inbox_channel:
            await ctx.send('Whisper Backup Inbox Channel is not set. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        backupInboxChannel = self.bot.get_channel(int(settings.backup_inbox_channel))

        if not backupInboxChannel:
            await ctx.send('Whisper Backup Inbox Channel is invalid or unaccessible. Contact an Administrator to set this up.', ephemeral=True)
            return
        
        if target is None:
            await ctx.send('Please specify a User to Whisper to.')
            return
        
        WhisperBlock = self.tables.WhisperBlock
        whisper_block_check = WhisperBlock.select().where(WhisperBlock.user_id==str(ctx.author.id), WhisperBlock.blocked_user_id==str(target.id)).first()

        if whisper_block_check and not target.guild_permissions.manage_messages:
            blocked_embed = discord.Embed(
                title='Blocked User',
                description='You have blocked this User. You cannot Whisper them.',
                color=discord.Color.red()
            )
            await ctx.send(embed=blocked_embed, ephemeral=True)
            return
        
        whisper_block_check_blocked_by = WhisperBlock.select().where(WhisperBlock.user_id==str(target.id), WhisperBlock.blocked_user_id==str(ctx.author.id)).first()

        if whisper_block_check_blocked_by and not ctx.author.guild_permissions.manage_messages:
            blocked_by_embed = discord.Embed(
                title='Blocked User',
                description='This User has blocked you. You cannot Whisper them.',
                color=discord.Color.red()
            )
            await ctx.send(embed=blocked_by_embed, ephemeral=True)
            return

        if settings.confirm_moderation and target.guild_permissions.manage_messages:
            embed = discord.Embed(title='Moderator Whisper Confirmation', description='You are attempting to Whisper a Moderator. Moderation communication is handled through ModMail. Are you sure you want to proceed?', color=discord.Color.purple())
            embed.set_footer(text='Please confirm to continue, or disregard to cancel.')
            sent_confirmation_message = await ctx.send(
                embed=embed,
                ephemeral=True
            )
            view = ModerationWhisperConfirmation(self, settings, sent_confirmation_message, ctx.author, target, message)
            await sent_confirmation_message.edit(view=view)
        else:
            await self.startWhisper(ctx.interaction, settings, ctx.author, target, message)

    async def startWhisper(self, interaction, settings, origin_user, target, message):
        """Open the Whisper Modal"""
        if target == origin_user:
            await interaction.response.send_message('You cannot Whisper yourself.', ephemeral=True)
            return

        await interaction.response.send_modal(
            WhisperModal(
                self,
                settings,
                origin_user,
                target,
                message
            )
        )

    async def sendWhisper(self, interaction, settings, origin_user, target, message):
        """Send a Whisper to the Target User and Log it"""
        targetWhisperEmbed = discord.Embed(description=message, color=discord.Color.purple())
        targetWhisperEmbed.set_author(name=f'{origin_user.display_name} ({origin_user.name})', icon_url=origin_user.avatar.url)
        targetWhisperEmbed.set_footer(text=origin_user.guild.name, icon_url=origin_user.guild.icon.url)

        logWhisperEmbed = discord.Embed(description=message, color=discord.Color.purple())
        logWhisperEmbed.set_author(name=f'{origin_user.display_name} ({origin_user.name}) → {target.display_name} ({target.name})', icon_url=origin_user.avatar.url)
        logWhisperEmbed.set_footer(text=origin_user.guild.name, icon_url=origin_user.guild.icon.url)

        whisperLogChannel = self.bot.get_channel(int(settings.log_channel))

        if not whisperLogChannel:
            await interaction.response.send_message(
                'Whisper Log Channel is invalid or unaccessible. Contact an Administrator to set this up.',
                ephemeral=True
            )
            return
        
        logSent = await whisperLogChannel.send(embed=logWhisperEmbed, view=WhisperLogReply(self))

        if not logSent:
            await interaction.response.send_message(
                'Whisper failed to send. There was an error logging this whisper for Moderation. Please contact an Administrator.',
                ephemeral=True
            )
            return

        targetSent = await target.send(embed=targetWhisperEmbed, view=WhisperTargetReply(self))

        if not targetSent:
            whisperBackupChannel = self.bot.get_channel(int(settings.backup_inbox_channel))

            if not whisperBackupChannel:
                await interaction.response.send_message(
                    f'Whisper failed to send. This is probably because {target.display_name} has DMs disabled or has {self.bot.mention} blocked. I was unable to notify them about this issue.',
                    ephemeral=True
                )
                return
            
            await whisperBackupChannel.send(
                f'{target.mention}: You have recieved a Whisper from {origin_user.mention}. However, I was unable to deliver it to you. This is likely because you have DMs disabled for this server or have {self.bot.mention} blocked. Please resolve this issue to recieve future Whispers.'
            )
            await interaction.response.send_message(
                f'Whisper Failed to Send. This is probably because {target.display_name} has DMs disabled or has {self.bot.mention} blocked. They have been notified of this issue.',
                ephemeral=True
            )
            return

        WhisperMessage = self.tables.WhisperMessage

        newWhisper = WhisperMessage(
            origin_guild_id = str(origin_user.guild.id),
            user_id = str(origin_user.id),
            target_id = str(target.id),
            timestamp = datetime.now(),
            inbox_message_id = targetSent.id,
            log_message_id = logSent.id
        )

        newWhisper.save()

        await interaction.response.send_message('Whisper Sent!', ephemeral=True)

    @whisper.command(name='block', description='Block a User from Whispering you')
    async def block(self, ctx, target: discord.Member):
        """Block a User from Whispering you"""
        WhisperBlock = self.tables.WhisperBlock
        whisper_block_check = WhisperBlock.select().where(WhisperBlock.user_id==str(ctx.author.id), WhisperBlock.blocked_user_id==str(target.id)).first()

        if whisper_block_check:
            await ctx.send('You have already blocked this User from Whispering you.')
            return
        
        newBlock = WhisperBlock(
            user_id = str(ctx.author.id),
            blocked_user_id = str(target.id)
        )

        newBlock.save()

        await ctx.send(f'You have blocked {target.display_name} from Whispering you.')

    @whisper.command(name='unblock', description='Unblock a User from Whispering you')
    async def unblock(self, ctx, target: discord.Member):
        """Unblock a User from Whispering you"""
        WhisperBlock = self.tables.WhisperBlock
        whisper_block_check = WhisperBlock.select().where(WhisperBlock.user_id==str(ctx.author.id), WhisperBlock.blocked_user_id==str(target.id)).first()

        if not whisper_block_check:
            await ctx.send('You have not blocked this User from Whispering you.')
            return
        
        whisper_block_check.delete_instance()

        await ctx.send(f'You have unblocked {target.display_name} from Whispering you.')

    @chat_group(name='config_whisper', description='Configure Whisper Settings', fallback='list_settings')
    async def config_whisper(self, ctx):
        """Configure Whisper Settings"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        WhisperSettings = self.tables.WhisperSettings
        settings = WhisperSettings.select().where(WhisperSettings.guild_id == ctx.guild.id).first()

        if not settings:
            settings = WhisperSettings(
                guild_id = str(ctx.guild.id), 
                enabled = False,
                confirm_moderation = True, 
                log_channel = None, 
                backup_inbox_channel = None
            )
            settings.save()

        if not settings.enabled:
            embed = discord.Embed(description='**Whispering is Disabled**', color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            embed.set_footer(text='Whisper Settings')
        else:
            embed = discord.Embed(
                description=f'**Whispering is Enabled**\n\n**Confirm Moderation:** {str(settings.confirm_moderation).capitalize()}\n**Log Channel:** {ctx.guild.get_channel(int(settings.log_channel)).mention if settings.log_channel else "None"}\n**Backup Inbox Channel:** {ctx.guild.get_channel(int(settings.backup_inbox_channel)).mention if settings.backup_inbox_channel else "None"}\n**Disable DMs:** {str(settings.disable_dms).capitalize()}', 
                color=discord.Color.purple()
            )
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            embed.set_footer(text='Whisper Settings')

        await ctx.send(embed=embed, ephemeral=True)

    @config_whisper.command(name='toggle', description='Toggle Whispering')
    async def toggle(self, ctx):
        """Toggle Whispering"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        WhisperSettings = self.tables.WhisperSettings
        settings = WhisperSettings.select().where(WhisperSettings.guild_id == ctx.guild.id).first()

        if not settings:
            settings = WhisperSettings(
                guild_id = str(ctx.guild.id), 
                enabled = False,
                confirm_moderation = True, 
                log_channel = None, 
                backup_inbox_channel = None
            )
            settings.save()

        settings.enabled = not settings.enabled
        settings.save()

        await ctx.send(f'Whispering is now {"Enabled" if settings.enabled else "Disabled"}', ephemeral=True)

    @config_whisper.command(name='confirm_moderation', description='Toggle Moderation Confirmation')
    async def confirm_moderation(self, ctx):
        """Toggle Moderation Confirmation"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        WhisperSettings = self.tables.WhisperSettings
        settings = WhisperSettings.select().where(WhisperSettings.guild_id == ctx.guild.id).first()

        if not settings:
            settings = WhisperSettings(
                guild_id = str(ctx.guild.id), 
                enabled = False,
                confirm_moderation = True, 
                log_channel = None, 
                backup_inbox_channel = None
            )
            settings.save()

        settings.confirm_moderation = not settings.confirm_moderation
        settings.save()

        await ctx.send(f'Moderation Confirmation is now {"Enabled" if settings.confirm_moderation else "Disabled"}', ephemeral=True)

    @config_whisper.command(name='log_channel', description='Set the Whisper Log Channel')
    async def log_channel(self, ctx, channel: discord.TextChannel):
        """Set the Whisper Log Channel"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        WhisperSettings = self.tables.WhisperSettings
        settings = WhisperSettings.select().where(WhisperSettings.guild_id == ctx.guild.id).first()

        if not settings:
            settings = WhisperSettings(
                guild_id = str(ctx.guild.id), 
                enabled = False,
                confirm_moderation = True, 
                log_channel = None, 
                backup_inbox_channel = None
            )
            settings.save()

        settings.log_channel = str(channel.id)
        settings.save()

        await ctx.send(f'Whisper Log Channel set to {channel.mention}', ephemeral=True)

    @config_whisper.command(name='backup_inbox_channel', description='Set the Whisper Backup Inbox Channel')
    async def backup_inbox_channel(self, ctx, channel: discord.TextChannel):
        """Set the Whisper Backup Inbox Channel"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        WhisperSettings = self.tables.WhisperSettings
        settings = WhisperSettings.select().where(WhisperSettings.guild_id == ctx.guild.id).first()

        if not settings:
            settings = WhisperSettings(
                guild_id = str(ctx.guild.id), 
                enabled = False,
                confirm_moderation = True, 
                log_channel = None, 
                backup_inbox_channel = None
            )
            settings.save()

        settings.backup_inbox_channel = str(channel.id)
        settings.save()

        await ctx.send(f'Whisper Backup Inbox Channel set to {channel.mention}', ephemeral=True)

    @config_whisper.command(name='disable_dms', description='Toggle Disabling DMs on this Server')
    async def disable_dms(self, ctx):
        """Toggle Disabling DMs on this Server"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        WhisperSettings = self.tables.WhisperSettings
        settings = WhisperSettings.select().where(WhisperSettings.guild_id == ctx.guild.id).first()

        if not settings:
            settings = WhisperSettings(
                guild_id = str(ctx.guild.id), 
                enabled = False,
                confirm_moderation = True, 
                log_channel = None, 
                backup_inbox_channel = None
            )
            settings.save()

        if not settings.enabled:
            await ctx.send('Whispering is not enabled', ephemeral=True)
            return

        if not settings.log_channel:
            await ctx.send('Whisper Log Channel is not set. Please set this up.', ephemeral=True)

        logChannel = self.bot.get_channel(int(settings.log_channel))

        if not logChannel:
            await ctx.send('Whisper Log Channel is not accessible. Please confirm this setting is correct.', ephemeral=True)

        settings.disable_dms = not settings.disable_dms
        settings.save()

        disableUntil = datetime.now(timezone.utc) + timedelta(days=1)
        payload = {
            "invites_disabled_until": None,
            "dms_disabled_until": disableUntil.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if settings.disable_dms else None
        }
        headers = {
            'Authorization': f'Bot {self.bot.config['connection']['token']}',
            'Content-Type': 'application/json'
        }

        await ctx.defer(ephemeral=True)

        async with aiohttp.ClientSession() as session:
            endpoint = f'https://discord.com/api/v9/guilds/{settings.guild_id}/incident-actions'

            async with session.put(endpoint, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    await ctx.send(f'Disabling DMs is now {"Enabled" if settings.disable_dms else "Disabled"}', ephemeral=True)
                else:
                    await ctx.send(f"Error: {response.status}", ephemeral=True)

    @tasks.loop(minutes=1440)
    async def disableDMs(self):
        """Disable DMs for configured Servers"""
        disableUntil = datetime.now(timezone.utc) + timedelta(days=1)
        payload = {
            "invites_disabled_until": None,
            "dms_disabled_until": disableUntil.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }
        headers = {
            'Authorization': f'Bot {self.bot.config['connection']['token']}',
            'Content-Type': 'application/json'
        }

        WhisperSettings = self.tables.WhisperSettings
        serverSettings = WhisperSettings.select().where(WhisperSettings.enabled == True, WhisperSettings.disable_dms == True)

        async with aiohttp.ClientSession() as session:
            for settings in serverSettings:
                if not settings.log_channel:
                    continue

                logChannel = self.bot.get_channel(int(settings.log_channel))

                if not logChannel:
                    continue

                endpoint = f'https://discord.com/api/v9/guilds/{settings.guild_id}/incident-actions'

                async with session.put(endpoint, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        await logChannel.send(f"Received data: {data}")
                    else:
                        await logChannel.send(f"Error: {response.status}")


async def setup(bot):
    new_cog = Whisper(bot)

    class WhisperSettings(bot.database.base_model):
        """Represents a Guild's Whisper Settings"""
        db_id = peewee.AutoField(primary_key=True)
        guild_id = peewee.TextField()
        enabled = peewee.BooleanField(default=False)
        confirm_moderation = peewee.BooleanField(default=True)
        log_channel = peewee.TextField(null=True)
        backup_inbox_channel = peewee.TextField(null=True)
        disable_dms = peewee.BooleanField(default=False)

    class WhisperBlock(bot.database.base_model):
        """Represents a User's Block List Item"""
        db_id = peewee.AutoField(primary_key=True)
        user_id = peewee.TextField()
        blocked_user_id = peewee.TextField()

    class WhisperMessage(bot.database.base_model):
        """Represents a Whisper Message"""
        db_id = peewee.AutoField(primary_key=True)
        origin_guild_id = peewee.TextField()
        user_id = peewee.TextField()
        target_id = peewee.TextField()
        timestamp = peewee.DateTimeField()
        inbox_message_id = peewee.TextField()
        log_message_id = peewee.TextField()

    new_cog.register_tables(
        [
            WhisperSettings,
            WhisperBlock,
            WhisperMessage
        ]
    )

    await bot.add_cog(new_cog)
    bot.add_view(WhisperLogReply(new_cog))
    bot.add_view(WhisperTargetReply(new_cog))
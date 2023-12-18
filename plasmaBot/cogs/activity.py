import peewee
import datetime
import random

import discord
from discord.ext.commands import guild_only

from plasmaBot.cog import PlasmaCog, terminal_command, chat_command
from plasmaBot.interface import terminal

class Activity(PlasmaCog):
    """Activity Tracking Cog"""
    def __init__(self, bot):
        self.bot = bot
        super().__init__(bot)

    @chat_command(name='xp', description='View your XP')
    @guild_only()
    async def xp(self, ctx, member:discord.Member=None):
        """View your XP"""
        ActivityStatus = self.tables.ActivityStatus

        if member is None:
            activity_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(ctx.author.id), ActivityStatus.guild_id == str(ctx.guild.id)).first()

            if activity_profile is None:
                await ctx.send('You have no XP')
            else:
                await ctx.send(f'You have {activity_profile.current_xp} XP')
        else:
            activity_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(member.id), ActivityStatus.guild_id == str(ctx.guild.id)).first()

            if activity_profile is None:
                await ctx.send(f'{member.display_name} has no XP')
            else:
                await ctx.send(f'{member.display_name} has {activity_profile.current_xp} XP')

    @chat_command(name='activity', description='View your activity')
    @guild_only()
    async def activity(self, ctx, member:discord.Member=None):
        """View your activity"""
        ActivityPoint = self.tables.ActivityPoint

        if member is None:
            activity_points = ActivityPoint.select().where(ActivityPoint.user_id == str(ctx.author.id), ActivityPoint.guild_id == str(ctx.guild.id))

            if len(activity_points) == 0:
                await ctx.send('You have no activity')
            else:
                await ctx.send(f'You have an activity score of {len(activity_points)}')
        else:
            activity_points = ActivityPoint.select().where(ActivityPoint.user_id == str(member.id), ActivityPoint.guild_id == str(ctx.guild.id))

            if len(activity_points) == 0:
                await ctx.send(f'{member.display_name} has no activity')
            else:
                await ctx.send(f'{member.display_name} has an activity score of {len(activity_points)}')

    @chat_command(name='afk', description='Set your AFK Status')
    @guild_only()
    async def afk(self, ctx, *, message:str=''):
        """Set your AFK Status"""
        ActivityStatus = self.tables.ActivityStatus
        activity_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(ctx.author.id), ActivityStatus.guild_id == str(ctx.guild.id)).first()

        if activity_profile is None:
            activity_profile = ActivityStatus(user_id=str(ctx.author.id), user_nick=ctx.author.display_name, guild_id=str(ctx.guild.id), current_xp=0, total_xp = 0, last_activity=datetime.datetime.now(), afk=True, afk_message=message)
            activity_profile.save()
        else:
            activity_profile.afk = True
            activity_profile.afk_message = message
            activity_profile.save()

        await ctx.send(f':sparkles: {ctx.author.display_name} is now AFK {': ' + message if message else ''} :sparkles:')

    @PlasmaCog.listener()
    async def on_member_update(self, before, after):
        """Update User Nickname"""
        if before.nick != after.nick:
            ActivityStatus = self.tables.ActivityStatus
            activity_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(after.id), ActivityStatus.guild_id == str(after.guild.id)).first()

            if activity_profile is not None:
                activity_profile.user_nick = after.display_name
                activity_profile.save()

    @PlasmaCog.listener()
    async def on_message(self, message):
        """Update XP and Activity"""
        # Ignore bots
        if message.author.bot:
            return
        
        # Ignore DMs
        if not message.guild:
            return
        
        # Get the user's XP
        ActivityStatus = self.tables.ActivityStatus
        activity_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(message.author.id), ActivityStatus.guild_id == str(message.guild.id)).first()

        # Update XP
        random_xp = random.gauss(10, 1.5)

        if activity_profile is None:
            activity_profile = ActivityStatus(user_id=str(message.author.id), user_nick=message.author.display_name, guild_id=str(message.guild.id), current_xp=random_xp, total_xp = random_xp, last_activity=message.created_at.replace(tzinfo=None))
            activity_profile.save()

            # Log message event
            message_log = self.tables.ActivityPoint(user_id=str(message.author.id), guild_id=str(message.guild.id), timestamp=message.created_at.replace(tzinfo=None))
            message_log.save()
        elif (message.created_at.replace(tzinfo=None) - activity_profile.last_activity).total_seconds() >= 60:
            activity_profile.current_xp += random_xp
            activity_profile.total_xp += random_xp
            activity_profile.last_activity = message.created_at
            activity_profile.save()

            # Log message event
            message_log = self.tables.ActivityPoint(user_id=str(message.author.id), guild_id=str(message.guild.id), timestamp=message.created_at.replace(tzinfo=None))
            message_log.save()

        # Check for AFK status
        if activity_profile is not None:
            if activity_profile.afk and (not message.content.lower().strip().startswith(self.bot.config['presence']['prefix'] + 'afk')):
                activity_profile.afk = False
                activity_profile.afk_message = ''
                activity_profile.save()

                await message.channel.send(f':sparkles: {message.author.display_name} is no longer AFK :sparkles:')    

        # Check for mention AFK status
        if message.mentions:
            for mention in message.mentions:
                mention_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(mention.id), ActivityStatus.guild_id == str(message.guild.id)).first()

                if mention_profile is not None:
                    if mention_profile.afk:
                        await message.channel.send(f':sparkles: {mention.display_name} is AFK{': ' + mention_profile.afk_message if mention_profile.afk_message else ''} :sparkles:')
                


async def setup(bot):
    """Setup cog"""
    new_cog = Activity(bot)
    await bot.add_cog(new_cog)

    class ActivityStatus(bot.database.base_model):
        db_id = peewee.AutoField(primary_key=True)
        user_id = peewee.TextField()
        user_nick = peewee.TextField()
        guild_id = peewee.TextField()
        current_xp = peewee.BigIntegerField(default=0)
        total_xp = peewee.BigIntegerField(default=0)
        last_activity = peewee.DateTimeField(datetime.datetime.now)
        afk = peewee.BooleanField(default=False)
        afk_message = peewee.TextField(default='')

    class ActivityPoint(bot.database.base_model):
        db_id = peewee.AutoField(primary_key=True)
        user_id = peewee.TextField()
        guild_id = peewee.TextField()
        timestamp = peewee.DateTimeField(datetime.datetime.now)

    new_cog.register_tables([ActivityStatus, ActivityPoint])
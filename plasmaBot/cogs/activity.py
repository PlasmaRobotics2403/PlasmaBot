import peewee
import datetime
import random
import asyncio

import discord
from discord.ext.commands import guild_only, check, has_permissions

from plasmaBot.cog import PlasmaCog, chat_command, chat_group
from plasmaBot.interface import terminal
from plasmaBot.pagination import Pagination


class Activity(PlasmaCog):
    """Activity Tracking Cog"""
    def __init__(self, bot):
        self.guild_settings = {}
        super().__init__(bot)

    async def get_guild_settings(self, guild):
        """Get Guild Settings"""
        if str(guild.id) in self.guild_settings:
            guild_settings = self.guild_settings[str(guild.id)]
        else:
            ActivitySettings = self.tables.ActivitySettings
            guild_settings = ActivitySettings.select().where(ActivitySettings.guild_id == str(guild.id)).first()

            if guild_settings is None:
                guild_settings = ActivitySettings(guild_id=str(guild.id))
                guild_settings.save()

            self.guild_settings[str(guild.id)] = guild_settings

        return guild_settings

    @chat_command(name='xp', description='View your XP')
    @guild_only()
    async def xp(self, ctx, member:discord.Member=None):
        """View your XP"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityStatus = self.tables.ActivityStatus

        if member is None:
            activity_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(ctx.author.id), ActivityStatus.guild_id == str(ctx.guild.id)).first()

            if activity_profile is None:
                embed = discord.Embed(description="Current XP: 0 XP", color=discord.Color.purple())
            else:
                embed = discord.Embed(description=f"Current XP: {activity_profile.current_xp} XP", color=discord.Color.purple())

            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        else:
            activity_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(member.id), ActivityStatus.guild_id == str(ctx.guild.id)).first()

            if activity_profile is None:
                embed = discord.Embed(description="Current XP: 0 XP", color=discord.Color.purple())
            else:
                embed = discord.Embed(description=f"Current XP: {activity_profile.current_xp} XP", color=discord.Color.purple())

            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)

        await ctx.send(embed=embed, ephemeral=True)

    @chat_group(name='activity', description='View your activity')
    @guild_only()
    async def activity(self, ctx, member:discord.Member=None):
        """View your activity"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint
        activity_points = ActivityPoint.select().where(ActivityPoint.user_id == str(member.id if member else ctx.author.id), ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.utcnow() + datetime.timedelta(days=-30))
        embed = await self.generate_activity_embed(ctx, activity_points, member if member else ctx.author, 'Monthly')
        await ctx.send(embed=embed, ephemeral=True)

    @activity.command(name='yearly', description='View your Yearly activity', aliases=['year'])
    async def activity_yearly(self, ctx, member:discord.Member=None):
        """View your activity"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint
        activity_points = ActivityPoint.select().where(ActivityPoint.user_id == str(member.id if member else ctx.author.id), ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.utcnow() + datetime.timedelta(days=-365))
        embed = await self.generate_activity_embed(ctx, activity_points, member if member else ctx.author, 'Yearly')
        await ctx.send(embed=embed, ephemeral=True)

    @activity.command(name='monthly', description='View your Monthly activity', aliases=['month'])
    async def activity_monthly(self, ctx, member:discord.Member=None):
        """View your activity"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint
        activity_points = ActivityPoint.select().where(ActivityPoint.user_id == str(member.id if member else ctx.author.id), ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.utcnow() + datetime.timedelta(days=-30))
        embed = await self.generate_activity_embed(ctx, activity_points, member if member else ctx.author, 'Monthly')
        await ctx.send(embed=embed, ephemeral=True)

    @activity.command(name='daily', description='View your Daily activity', aliases=['day'])
    async def activity_daily(self, ctx, member:discord.Member=None):
        """View your activity"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint
        activity_points = ActivityPoint.select().where(ActivityPoint.user_id == str(member.id if member else ctx.author.id), ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.utcnow() + datetime.timedelta(days=-1))
        embed = await self.generate_activity_embed(ctx, activity_points, member if member else ctx.author, 'Daily')
        await ctx.send(embed=embed, ephemeral=True)

    @activity.command(name='hourly', description='View your Hourly activity', aliases=['hour'])
    async def activity_hourly(self, ctx, member:discord.Member=None):
        """View your activity"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint
        activity_points = ActivityPoint.select().where(ActivityPoint.user_id == str(member.id if member else ctx.author.id), ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.utcnow() + datetime.timedelta(hours=-1))
        embed = await self.generate_activity_embed(ctx, activity_points, member if member else ctx.author, 'Hourly')
        await ctx.send(embed=embed, ephemeral=True)

    @activity.command(name='all', description='View your All-Time activity', aliases=['all-time', 'alltime'])
    async def activity_alltime(self, ctx, member:discord.Member=None):
        """View your activity"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint
        activity_points = ActivityPoint.select().where(ActivityPoint.user_id == str(member.id if member else ctx.author.id), ActivityPoint.guild_id == str(ctx.guild.id))
        embed = await self.generate_activity_embed(ctx, activity_points, member if member else ctx.author, 'All-Time')
        await ctx.send(embed=embed, ephemeral=True)

    async def generate_activity_embed(self, ctx, activity_points, member:discord.Member, period:str):
        """Generate Activity Embed"""
        embed = discord.Embed(description=f"Activity Points: {len(activity_points)} AP", color=discord.Color.purple())
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.set_footer(text=f'{period} Activity')
        return embed

    @chat_group(name='rank', description='View your rank')
    @guild_only()
    async def rank(self, ctx, member:discord.Member=None):
        """View your Monthly Rank"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.utcnow() + datetime.timedelta(days=-30)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())
        
        await ctx.send(embed=await self.get_rank(activity_points, member if member else ctx.author, 'Monthly'), ephemeral=True)

    @rank.command(name='daily', description='View your Daily Rank', aliases=['day'])
    async def rank_daily(self, ctx, member:discord.Member=None):
        """View your Daily Rank"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.utcnow() + datetime.timedelta(days=-1)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())
        
        await ctx.send(embed=await self.get_rank(activity_points, member if member else ctx.author, 'Daily'))

    @rank.command(name='hourly', description='View your Hourly Rank', aliases=['hour'], ephemeral=True)
    async def rank_hourly(self, ctx, member:discord.Member=None):
        """View your Hourly Rank"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.utcnow() + datetime.timedelta(hours=-1)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())
        
        await ctx.send(embed=await self.get_rank(activity_points, member if member else ctx.author, 'Hourly'))
    
    @rank.command(name='monthly', description='View your Monthly Rank', aliases=['month'], ephemeral=True)
    async def rank_monthly(self, ctx, member:discord.Member=None):
        """View your Monthly Rank"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.utcnow() + datetime.timedelta(days=-30)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())
        
        await ctx.send(embed=await self.get_rank(activity_points, member if member else ctx.author, 'Monthly'))

    @rank.command(name='yearly', description='View your Yearly Rank', aliases=['year'], ephemeral=True)
    async def rank_yearly(self, ctx, member:discord.Member=None):
        """View your Yearly Rank"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.utcnow() + datetime.timedelta(days=-365)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())
        
        await ctx.send(embed=await self.get_rank(activity_points, member if member else ctx.author, 'Yearly'))

    @rank.command(name='all', description='View your All-Time Rank', aliases=['all-time', 'alltime'])
    async def rank_alltime(self, ctx, member:discord.Member=None):
        """View your All-Time Rank"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())
        
        await ctx.send(embed=await self.get_rank(activity_points, member if member else ctx.author, 'All-Time'), ephemeral=True)

    async def get_rank(self, activity_points, member:discord.Member, period:str):
        index = 1
        pointObj = None

        for point in activity_points:
            if point.user_id == str(member.id):
                pointObj = point
                break
            else:
                index += 1

        embed = discord.Embed(description=f"#{index} of {len(activity_points)} in this server ({pointObj.ct} AP)", color=discord.Color.purple())
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.set_footer(text=f'{period} Rank')

        return embed

    @chat_group(name='leaderboard', description='View the Activity Leaderboard')
    @guild_only()
    async def leaderboard(self, ctx):
        """View the Activity Leaderboard"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.utcnow() + datetime.timedelta(days=-30)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())

        await self.generate_leaderboard(ctx, activity_points, 'Monthly')

    @leaderboard.command(name='daily', description='View the Daily Leaderboard', aliases=['day'])
    async def leaderboard_daily(self, ctx):
        """View the Daily Leaderboard"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.utcnow() + datetime.timedelta(days=-1)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())

        await self.generate_leaderboard(ctx, activity_points, 'Daily')

    @leaderboard.command(name='hourly', description='View the Hourly Leaderboard', aliases=['hour'])
    async def leaderboard_hourly(self, ctx):
        """View the Hourly Leaderboard"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.utcnow() + datetime.timedelta(hours=-1)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())

        await self.generate_leaderboard(ctx, activity_points, 'Hourly')

    @leaderboard.command(name='monthly', description='View the Monthly Leaderboard', aliases=['month'])
    async def leaderboard_monthly(self, ctx):
        """View the Monthly Leaderboard"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.utcnow() + datetime.timedelta(days=-30)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())

        await self.generate_leaderboard(ctx, activity_points, 'Monthly')

    @leaderboard.command(name='yearly', description='View the Yearly Leaderboard', aliases=['year'])
    async def leaderboard_yearly(self, ctx):
        """View the Yearly Leaderboard"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.utcnow() + datetime.timedelta(days=-365)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())

        await self.generate_leaderboard(ctx, activity_points, 'Yearly')

    @leaderboard.command(name='all', description='View the All-Time Leaderboard', aliases=['all-time', 'alltime'])
    async def leaderboard_allTime(self, ctx):
        """View the All-Time Leaderboard"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityPoint = self.tables.ActivityPoint

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())

        await self.generate_leaderboard(ctx, activity_points, 'All-Time')

    async def generate_leaderboard(self, ctx, activity_points, title):
        ActivityStatus = self.tables.ActivityStatus

        if len(activity_points) == 0:
            embed = discord.Embed(
                title=f"{title} Rankings in {ctx.guild.name}", 
                description="No Activity Rankings for this guild yet...", 
                color=discord.Color.purple()
            )
            await ctx.send(embed=embed)
        else:
            def get_page(page):
                lower = page * 15
                upper = (page + 1) * 15
                slice = activity_points[lower:upper]

                embed_content = ''

                for point in slice:
                    activity_profile = ActivityStatus.select().where(ActivityStatus.user_id == point.user_id, ActivityStatus.guild_id == str(ctx.guild.id)).first()
                    
                    if activity_profile is None:
                        member = ctx.guild.get_member(int(point.user_id))

                        if member:
                            user_nick = member.display_name
                        else:
                            user_nick = f'User {point.user_id}'
                    else:
                        user_nick = activity_profile.user_nick

                    lower += 1
                    embed_content += f'**#{lower}: {user_nick}** ({point.ct} AP)\n'

                embed = discord.Embed(title=f"{title} Rankings in {ctx.guild.name}", description=embed_content, color=discord.Color.purple())
                embed.set_footer(text=f'Page {page + 1} of {len(activity_points) // 15 + 1}')

                return embed, len(activity_points) // 15 + 1
        
            pagination = Pagination(ctx.author, ctx, get_page, timeout=60)
            await pagination.navigate()

    @chat_group(name='config_activity', description='Configure Activity Settings')
    @guild_only()
    async def config_activity(self, ctx):
        """Configure Activity Settings"""
        pass

    @config_activity.command(name='disable_channel', description='Disable XP in a channel')
    async def config_activity_disable_channel(self, ctx, channel:discord.TextChannel=None):
        """Mark a channel as XP/AP Disabled"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return

        ActivityDisabledChannel = self.tables.ActivityDisabledChannel

        # Default to current channel
        if channel is None:
            channel = ctx.channel

        # Check that channel is in guild
        if channel.guild != ctx.guild:
            await ctx.send('You can only disable XP/AP in this server\'s channels', ephemeral=True)
            return

        # Pull channel status
        channel_disabled = ActivityDisabledChannel.select().where(ActivityDisabledChannel.guild_id == str(ctx.guild.id), ActivityDisabledChannel.channel_id == str(channel.id)).first()

        # Disable channel if not already disabled
        if channel_disabled is None:
            channel_disabled = ActivityDisabledChannel(guild_id=str(ctx.guild.id), channel_id=str(channel.id))
            channel_disabled.save()

            await ctx.send(f'{channel.mention} is now XP/AP Disabled', ephemeral=True)
        else:
            await ctx.send(f'{channel.mention} is already XP/AP Disabled', ephemeral=True)

    @config_activity.command(name='enable_channel', description='Re-enable XP in a channel')
    async def config_activity_enable_channel(self, ctx, channel:discord.TextChannel=None):
        """Re-enable XP/AP in a channel"""

        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        ActivityDisabledChannel = self.tables.ActivityDisabledChannel

        # Default to current channel
        if channel is None:
            channel = ctx.channel

        # Check that channel is in guild
        if channel.guild != ctx.guild:
            await ctx.send('You can only enable XP/AP in this server\'s channels', ephemeral=True)
            return

        # Pull channel status
        channel_disabled = ActivityDisabledChannel.select().where(ActivityDisabledChannel.guild_id == str(ctx.guild.id), ActivityDisabledChannel.channel_id == str(channel.id)).first()

        # Enable channel if not already enabled
        if channel_disabled is not None:
            channel_disabled.delete_instance()

            await ctx.send(f'{channel.mention} is now XP/AP Enabled', ephemeral=True)
        else:
            await ctx.send(f'{channel.mention} is already XP/AP Enabled', ephemeral=True)

    @config_activity.command(name='set_xp_distribution', description='Configure XP Settings')
    @check(has_permissions(manage_guild=True))
    async def config_activity_set_xp_settings(self, ctx, mean:float, std:float):
        """Set XP Settings"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        ActivitySettings = self.tables.ActivitySettings

        # Pull guild settings
        guild_settings = ActivitySettings.select().where(ActivitySettings.guild_id == str(ctx.guild.id)).first()

        # Create guild settings if not already created
        if guild_settings is None:
            guild_settings = ActivitySettings(guild_id=str(ctx.guild.id), xp_mean=mean, xp_std=std)
            guild_settings.save()
        else: # Set guild settings
            guild_settings.xp_mean = mean
            guild_settings.xp_std = std
            guild_settings.save()

        # Update guild settings cache
        self.guild_settings[str(ctx.guild)] = guild_settings

        await ctx.send(f'XP configured to use a Mean of {mean} and a Standard Deviation of {std}', ephemeral=True)

    @config_activity.command(name='list_settings', description='List XP Settings')
    async def config_activity_list_xp_settings(self, ctx):
        """List XP Settings"""
        ActivitySettings = self.tables.ActivitySettings

        # Pull guild settings
        guild_settings = ActivitySettings.select().where(ActivitySettings.guild_id == str(ctx.guild.id)).first()

        # Create guild settings if not already created
        if guild_settings is None:
            guild_settings = ActivitySettings(guild_id=str(ctx.guild.id))
            guild_settings.save()

        ActivityDisabledChannel = self.tables.ActivityDisabledChannel
        disabled_channels = ActivityDisabledChannel.select().where(ActivityDisabledChannel.guild_id == str(ctx.guild.id))
        disabled_channel_list = ''

        for channel in disabled_channels:
            disabled_channel_list += f' - <#{channel.channel_id}>\n'        

        embed = discord.Embed(description=f'**Activity Tracking is {'Enabled' if guild_settings.enabled else 'Disabled'}**\n\n**XP Settings:**\n- **Mean:** {guild_settings.xp_mean} XP\n- **Standard Deviation:** {guild_settings.xp_std} XP\n\n**Disabled Channels:**\n{disabled_channel_list}', 
                              color=discord.Color.purple()
                              )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        embed.set_footer(text='Activity Settings')

        await ctx.send(embed=embed, ephemeral=True)

    @chat_command(name='afk', description='Set your AFK Status')
    @guild_only()
    async def afk(self, ctx, *, message:str=''):
        """Set your AFK Status"""
        ActivityStatus = self.tables.ActivityStatus
        activity_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(ctx.author.id), ActivityStatus.guild_id == str(ctx.guild.id)).first()

        if activity_profile is None:
            activity_profile = ActivityStatus(user_id=str(ctx.author.id), user_nick=ctx.author.display_name, guild_id=str(ctx.guild.id), current_xp=0, total_xp = 0, last_activity=datetime.datetime.utcnow(), afk=True, afk_message=message)
            activity_profile.save()
        else:
            activity_profile.afk = True
            activity_profile.afk_message = message
            activity_profile.save()

        await ctx.send(f':sparkles: **{ctx.author.display_name}** is now AFK{': ' + message if message else ''} :sparkles:')

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
        
        # Ignore commands
        if message.content.strip().startswith(self.bot.config['presence']['prefix']):
            return
        
        # Get the user's XP
        ActivityStatus = self.tables.ActivityStatus
        activity_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(message.author.id), ActivityStatus.guild_id == str(message.guild.id)).first()

        # Check for AFK status
        if activity_profile is not None:
            if activity_profile.afk and (not message.content.lower().strip().startswith(self.bot.config['presence']['prefix'] + 'afk')):
                activity_profile.afk = False
                activity_profile.afk_message = ''
                activity_profile.save()

                await message.channel.send(f':sparkles: **{message.author.display_name}** is no longer AFK :sparkles:')

        # Check for mention AFK status
        afk_members = []

        if message.mentions:
            for mention in message.mentions:

                mention_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(mention.id), ActivityStatus.guild_id == str(message.guild.id)).first()

                if mention_profile is not None:
                    if mention_profile.afk:
                        afk_members.append([mention, mention_profile])

        # Notify Channel of AFK Users
        if afk_members:
            if len(afk_members) == 1:
                await message.channel.send(f':sparkles: **{afk_members[0][0].display_name}** is AFK{': ' + afk_members[0][1].afk_message if afk_members[0][1].afk_message else ''} :sparkles:', delete_after=5)
            else:
                afk = ':sparkles: '

                for member in afk_members[:-1]:
                    afk += f'**{member[0].display_name}**, '   

                afk += f'and **{afk_members[-1][0].display_name}** are AFK :sparkles:'  

                await message.channel.send(afk, delete_after=5)

        ActivityDisabledChannel = self.tables.ActivityDisabledChannel
        channel_disabled = ActivityDisabledChannel.select().where(ActivityDisabledChannel.guild_id == str(message.guild.id), ActivityDisabledChannel.channel_id == str(message.channel.id)).first()

        # Do not increment XP or AP if channel is disabled
        if channel_disabled:
            return

        # Get Guild Settings
        guild_settings = await self.get_guild_settings(message.guild)

        # Do not increment XP or AP if guild is disabled
        if not guild_settings.enabled:
            return

        # Update XP
        random_xp = random.gauss(guild_settings.xp_mean, guild_settings.xp_std)

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


async def setup(bot):
    """Setup cog"""
    new_cog = Activity(bot)

    class ActivityDisabledChannel(bot.database.base_model):
        """Represents a channel with XP Disabled"""
        db_id = peewee.AutoField(primary_key=True)
        guild_id = peewee.TextField()
        channel_id = peewee.TextField()

    class ActivitySettings(bot.database.base_model):
        """Represents a Guild's Activity Settings"""
        db_id = peewee.AutoField(primary_key=True)
        guild_id = peewee.TextField()
        enabled = peewee.BooleanField(default=True)
        xp_mean = peewee.FloatField(default=10)
        xp_std = peewee.FloatField(default=1.5)

    class ActivityStatus(bot.database.base_model):
        """Represents a User's Activity Status"""
        db_id = peewee.AutoField(primary_key=True)
        user_id = peewee.TextField()
        user_nick = peewee.TextField()
        guild_id = peewee.TextField()
        current_xp = peewee.BigIntegerField(default=0)
        total_xp = peewee.BigIntegerField(default=0)
        last_activity = peewee.DateTimeField(datetime.datetime.utcnow)
        afk = peewee.BooleanField(default=False)
        afk_message = peewee.TextField(default='')

    class ActivityPoint(bot.database.base_model):
        """Represents an individual Activity Point"""
        db_id = peewee.AutoField(primary_key=True)
        user_id = peewee.TextField()
        guild_id = peewee.TextField()
        timestamp = peewee.DateTimeField(datetime.datetime.utcnow)

    new_cog.register_tables(
        [
            ActivityDisabledChannel, 
            ActivitySettings,
            ActivityStatus, 
            ActivityPoint
        ]
    )

    await bot.add_cog(new_cog)
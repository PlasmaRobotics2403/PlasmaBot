import os
import io
import peewee
import datetime
import random
import asyncio
import traceback
import matplotlib.pyplot as plt

import discord
from discord.ext.commands import guild_only, check, has_permissions, Context

from plasmaBot.cog import PlasmaCog, chat_command, chat_group
from plasmaBot.interface import terminal
from plasmaBot.pagination import Pagination


class StoreButton(discord.ui.Button):
    def __init__(self, item, view):
        super().__init__(label=f'{item.name} ({item.cost} XP)', style=discord.ButtonStyle.gray)
        self._item = item
        self._view = view

    async def callback(self, interaction:discord.Interaction):
        response, message = await self._view.buy(self._item)
        if response:
            await interaction.response.send_message(f'You bought {self._item.name} for {self._item.cost} XP', ephemeral=True)
            self.disabled = True
            await self._view.update()
        else:
            await interaction.response.send_message(message, ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user == self._view.ctx.author:
            return True
        else:
            await interaction.response.send_message(f'Only {self._view.ctx.author.mention} can use this button.', ephemeral=True)
            return False


class Store(discord.ui.View):
    def __init__(self, title:str, cog:PlasmaCog, ctx:Context, items:list, table, *, timeout: int = 60):
        self.title = title
        self.cog = cog
        self.ctx = ctx
        self.items = items
        self.table = table

        self.message = None

        super().__init__(timeout=timeout)

        embed = discord.Embed(color=discord.Color.purple())
        embed.set_author(name=f'{self.title} Store', icon_url=self.ctx.guild.icon.url)

        for item in self.items:
            self.add_item(StoreButton(item, self))
            if item.value:
                embed.add_field(name=item.name, value=f'{item.description} ({item.cost} XP, {item.value} Power)', inline=False)
            else:
                embed.add_field(name=item.name, value=f'{item.description} ({item.cost} XP)', inline=False)
        
        embed.set_footer(text=f'Available Items for {self.ctx.author.display_name}', icon_url=self.ctx.author.display_avatar.url)
        self.embed = embed

    async def start(self):
        self.message = await self.ctx.send(embed=self.embed, view=self, ephemeral=True)
        
    async def update(self):
        if self.message is not None:
            await self.message.edit(embed=self.embed, view=self)
        else:
            await self.start()

    async def buy(self, item):
        """Buy Item"""
        ActivityStatus = self.cog.tables.ActivityStatus
        activity_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(self.ctx.author.id), ActivityStatus.guild_id == str(self.ctx.guild.id)).first()

        table = self.table
        has_item = table.select().where(table.user_id == str(self.ctx.author.id), table.guild_id == str(self.ctx.guild.id), table.item_id == item.id).first()

        if has_item:
            return (False, 'You already own this item')
        
        if activity_profile.current_xp < item.cost:
            return (False, 'You do not have enough XP to buy this item')
        
        activity_profile.current_xp -= item.cost
        activity_profile.save()

        item = table(user_id=str(self.ctx.author.id), guild_id=str(self.ctx.guild.id), item=item)
        item.save()

        return (True, 'Success')
    
    async def on_timeout(self):
        await self.message.edit(view=None)


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

    @chat_group(name='graph', description='View your XP Graph')
    @guild_only()
    async def graph(self, ctx, member:discord.Member=None):
        """View your XP Graph"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        await self.generateMonthlyGraph(ctx, member)

    @graph.command(name='hourly', description='View your Hourly XP Graph', aliases=['hour'])
    async def graph_hourly(self, ctx, member:discord.Member=None):
        """View your Hourly XP Graph"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        await self.generateHourlyGraph(ctx, member)

    @graph.command(name='monthly', description='View your Monthly XP Graph', aliases=['month'])
    async def graph_monthly(self, ctx, member:discord.Member=None):
        """View your Monthly XP Graph"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        await self.generateMonthlyGraph(ctx, member)
        
    graph_lock = asyncio.Lock()

    async def generateHourlyGraph(self, ctx, member:discord.Member=None):
        """Generate Hourly Graph"""
        ActivityPoint = self.tables.ActivityPoint
        activity_points = ActivityPoint.select().where(ActivityPoint.user_id == str(member.id if member else ctx.author.id), ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=-1))

        # Convert activity_points to a list of timestamps
        timestamps = [point.timestamp for point in activity_points]

        # Create a list of 30 buckets based on the day of the timestamp
        buckets = [0] * 60
        for timestamp in timestamps:
            minute = (datetime.datetime.now(datetime.UTC) - timestamp).minutes
            if 0 <= minute < 60:
                buckets[minute] += 1

        async with self.graph_lock:
            # Generate the graph
            plt.plot(range(-59, 1), buckets[::-1])
            plt.title("Hourly Activity for " + (member.display_name if member else ctx.author.display_name))
            plt.xlabel("Minutes")
            plt.ylabel("Activity Points")

            # Save the graph as a PNG file in memory
            image_data = io.BytesIO()
            plt.savefig(image_data, format='png')
            image_data.seek(0)

            # Clear the plot
            plt.clf()

        # Create a discord.File object from the image data
        file = discord.File(image_data, filename='graph.png')

        # Send the file as a message attachment
        await ctx.send(file=file, ephemeral=True)

        # Close the BytesIO object to free up memory
        image_data.close()

    async def generateMonthlyGraph(self, ctx, member:discord.Member=None):
        """Generate Monthly Graph"""
        ActivityPoint = self.tables.ActivityPoint
        activity_points = ActivityPoint.select().where(ActivityPoint.user_id == str(member.id if member else ctx.author.id), ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=-30))

        # Convert activity_points to a list of timestamps
        timestamps = [point.timestamp for point in activity_points]

        # Create a list of 30 buckets based on the day of the timestamp
        buckets = [0] * 30
        for timestamp in timestamps:
            day = (datetime.datetime.now(datetime.UTC) - timestamp).days
            if 0 <= day < 30:
                buckets[day] += 1

        async with self.graph_lock:
            # Generate the graph
            plt.plot(range(-29, 1), buckets[::-1])
            plt.title("Monthly Activity for " + (member.display_name if member else ctx.author.display_name))
            plt.xlabel("Days")
            plt.ylabel("Activity Points")

            # Save the graph as a PNG file in memory
            image_data = io.BytesIO()
            plt.savefig(image_data, format='png')
            image_data.seek(0)

            # Clear the plot
            plt.clf()

        # Create a discord.File object from the image data
        file = discord.File(image_data, filename='graph.png')

        # Send the file as a message attachment
        await ctx.send(file=file, ephemeral=True)

        # Close the BytesIO object to free up memory
        image_data.close()

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
        activity_points = ActivityPoint.select().where(ActivityPoint.user_id == str(member.id if member else ctx.author.id), ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=-30))
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
        activity_points = ActivityPoint.select().where(ActivityPoint.user_id == str(member.id if member else ctx.author.id), ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=-365))
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
        activity_points = ActivityPoint.select().where(ActivityPoint.user_id == str(member.id if member else ctx.author.id), ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=-30))
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
        activity_points = ActivityPoint.select().where(ActivityPoint.user_id == str(member.id if member else ctx.author.id), ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=-1))
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
        activity_points = ActivityPoint.select().where(ActivityPoint.user_id == str(member.id if member else ctx.author.id), ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=-1))
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

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=-30)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())
        
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

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=-1)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())
        
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

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=-1)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())
        
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

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=-30)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())
        
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

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=-365)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())
        
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

        if not pointObj:
            embed = discord.Embed(description="No Messages Sent During This Period", color=discord.Color.purple())
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.set_footer(text=f'{period} Rank')
            return embed

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

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=-30)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())

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

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=-1)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())

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

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=-1)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())

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

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=-30)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())

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

        activity_points = ActivityPoint.select(ActivityPoint.user_id, ActivityPoint.guild_id, peewee.fn.COUNT(ActivityPoint.user_id).alias('ct')).where(ActivityPoint.guild_id == str(ctx.guild.id), ActivityPoint.timestamp > datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=-365)).group_by(ActivityPoint.user_id).order_by(peewee.fn.COUNT(ActivityPoint.user_id).desc())

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

    @chat_group(name='buffs', description='View your buffs')
    @guild_only()
    async def buffs(self, ctx, member:discord.Member=None):
        """View your buffs"""
        await self.view_user_buffs(ctx, member)

    @buffs.command(name='list', description='View your buffs')
    async def buffs_list(self, ctx, member:discord.Member=None):
        """View your buffs"""
        await self.view_user_buffs(ctx, member)
        
    async def view_user_buffs(self, ctx, member:discord.Member=None):
        """View User Buffs"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        if member is None:
            member = ctx.author

        ActivityUserBuff = self.tables.ActivityUserBuff
        buffs = ActivityUserBuff.select().where(ActivityUserBuff.guild_id == str(ctx.guild.id), ActivityUserBuff.user_id == str(member.id))

        if not buffs:
            await ctx.send(f'{ctx.author.display_name} has no buffs', ephemeral=True)
            return

        embed = discord.Embed(title=f'Buffs for {member.display_name}', color=discord.Color.purple())

        if member.id in self.bot.developers:
            embed.add_field(name='Developer', value='The mystic powers of code are on your side (50 Power)', inline=False)

        for buff in buffs:
            embed.add_field(name=buff.item.name, value=f'{buff.item.description} ({buff.item.value} Power)', inline=False)

        await ctx.send(embed=embed, ephemeral=True)
        
    @buffs.command(name='buy', description='Buy a buff', aliases=['purchase', 'store'])
    async def buffs_buy(self, ctx):
        """Buy a buff"""
        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return

        ActivityBuff = self.tables.ActivityBuff
        buffs = ActivityBuff.select().where(ActivityBuff.guild_id == str(ctx.guild.id))
        available_buffs = []

        ActivityUserBuff = self.tables.ActivityUserBuff
        user_buffs = ActivityUserBuff.select().where(ActivityUserBuff.guild_id == str(ctx.guild.id), ActivityUserBuff.user_id == str(ctx.author.id))

        for buff in buffs:
            found = False

            for user_buff in user_buffs:
                if buff == user_buff.item:
                    found = True
            
            if not found:
                available_buffs.append(buff)
            

        if len(available_buffs) == 0:
            await ctx.send(f'{ctx.author.display_name} has no buffs available', ephemeral=True)
            return

        store = Store('Buffs', self, ctx, available_buffs, ActivityUserBuff)
        await store.start()

    @chat_command(name='faceoff', description='Faceoff against another user')
    @guild_only()
    async def faceoff(self, ctx, member:discord.Member, wager:int=None):
        """Faceoff against another user"""
        embed = discord.Embed(color=discord.Color.purple())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f'Faceoff against {member.display_name}')

        if member.bot:
            embed.description = f'{member.display_name} is too powerful - You cower in fear.'
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        if member == ctx.author:
            embed.description = 'The mirror breaks and you injure your hand.'
            await ctx.send(embed=embed, ephemeral=True)
            return

        guild_settings = await self.get_guild_settings(ctx.guild)

        if guild_settings.enabled is False:
            embed = discord.Embed(description="Activity Tracking is Disabled", color=discord.Color.purple())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        ActivityStatus = self.tables.ActivityStatus
        author_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(ctx.author.id), ActivityStatus.guild_id == str(ctx.guild.id)).first()
        opponent_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(member.id), ActivityStatus.guild_id == str(ctx.guild.id)).first()
        
        if author_profile is None:
            author_profile = ActivityStatus(user_id=str(ctx.author.id), user_nick=ctx.author.display_name, guild_id=str(ctx.guild.id))
            author_profile.save()

        if opponent_profile is None:
            opponent_profile = ActivityStatus(user_id=str(member.id), user_nick = member.display_name, guild_id=str(ctx.guild.id))
            opponent_profile.save()

        if wager is not None and wager != 0:
            wager=round(abs(wager))

            if author_profile.current_xp < wager:
                embed.description = 'You do not have enough XP to wager this amount'
                await ctx.send(embed=embed, ephemeral=True)
                return
            
            if opponent_profile.current_xp < wager:
                embed.description = 'Your opponent does not have enough XP to wager this amount'
                await ctx.send(embed=embed, ephemeral=True)
                return
            
            challenge_embed = discord.Embed(description=f'You have been challenged to a Faceoff by {ctx.author.mention}', color=discord.Color.purple())
            challenge_embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            challenge_embed.add_field(name='Wager', value=f'{wager} XP', inline=False)
            challenge_embed.set_footer(text='React with ✅ to accept the challenge')

            challenge_message = await ctx.send(embed=challenge_embed)

            await challenge_message.add_reaction('✅')

            def check(reaction, user):
                return user == member and str(reaction.emoji) == '✅'
            
            try:
                await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await challenge_message.clear_reaction('✅')

                challenge_embed.set_footer(text=f'{member.display_name} did not accept the challenge')
                await challenge_message.edit(embed=challenge_embed)

                embed.description = f'{member.display_name} did not accept the challenge'
                await ctx.send(embed=embed, ephemeral=True)
                return
            
            await challenge_message.clear_reaction('✅')

            challenge_embed.set_footer(text=f'{member.display_name} accepted the challenge')
            await challenge_message.edit(embed=challenge_embed)

        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        embed.description = f'{ctx.author.display_name} and {member.display_name} are facing off...'
        faceoff_message = await ctx.send(embed=embed, ephemeral=wager is None or wager == 0)

        await asyncio.sleep(5)

        author_buff_value = await self.get_member_buffs(ctx.author)
        opponent_buffs_value = await self.get_member_buffs(member)

        author_score = random.randint(25, 100) * author_buff_value
        opponent_score = random.randint(25, 100) * opponent_buffs_value


        if author_score > opponent_score:
            if wager is not None and wager != 0:
                author_profile.current_xp += wager + guild_settings.xp_mean
                author_profile.total_xp += wager + guild_settings.xp_mean
                opponent_profile.current_xp -= wager
                author_profile.save()
                opponent_profile.save()

                embed.description = f'{ctx.author.mention} won the faceoff and gained {int(wager + guild_settings.xp_mean)} XP'
                await faceoff_message.edit(embed=embed)
            else:
                author_profile.current_xp += guild_settings.xp_mean
                author_profile.total_xp += guild_settings.xp_mean
                author_profile.save()

                embed.description = f'{ctx.author.mention} won the faceoff'
                await faceoff_message.edit(embed=embed)
        else:
            if wager is not None and wager != 0:
                author_profile.current_xp -= wager
                opponent_profile.current_xp += wager + guild_settings.xp_mean
                opponent_profile.total_xp += wager + guild_settings.xp_mean
                author_profile.save()
                opponent_profile.save()

                embed.description = f'{member.mention} won the faceoff and gained {int(wager + guild_settings.xp_mean)} XP'
                await faceoff_message.edit(embed=embed)
            else:
                opponent_profile.current_xp += guild_settings.xp_mean
                opponent_profile.total_xp += guild_settings.xp_mean
                opponent_profile.save()

                embed.description = f'{member.display_name} won the faceoff'
                await faceoff_message.edit(embed=embed)
        
    async def get_member_buffs(self, member:discord.Member):
        """Get Member Buffs"""
        buff_value = 100 # Base Buff Value

        if member.id in self.bot.developers:
            buff_value += 50

        ActivityUserBuff = self.tables.ActivityUserBuff
        buffs = ActivityUserBuff.select().where(ActivityUserBuff.guild_id == str(member.guild.id), ActivityUserBuff.user_id == str(member.id))

        for buff in buffs:
            buff_value += buff.item.value

        return buff_value / 100

    @chat_group(name='config_activity', description='Configure Activity Settings')
    @guild_only()
    async def config_activity(self, ctx):
        """Configure Activity Settings"""
        pass

    @config_activity.command(name='create_buff', description='Create a buff')
    async def config_activity_create_buff(self, ctx, name:str, value:int, cost:int, description:str):
        """Create a buff"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return

        ActivityBuff = self.tables.ActivityBuff
        guild_buffs = ActivityBuff.select().where(ActivityBuff.guild_id == str(ctx.guild.id))

        if len(guild_buffs) >= 25:
            await ctx.send(f'{ctx.guild.name} has reached the maximum number of buffs (25)', ephemeral=True)
            return

        buff = ActivityBuff.select().where(ActivityBuff.guild_id == str(ctx.guild.id), ActivityBuff.name == name).first()

        if buff is None:
            buff = ActivityBuff(guild_id=str(ctx.guild.id), name=name, value=value, cost=cost, description=description)
            buff.save()

            await ctx.send(f'Buff `{name}` created', ephemeral=True)
        else:
            await ctx.send(f'Buff `{name}` already exists', ephemeral=True)

    @config_activity.command(name='delete_buff', description='Delete a buff')
    async def config_activity_delete_buff(self, ctx, name:str):
        """Delete a buff"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return

        ActivityBuff = self.tables.ActivityBuff
        buff = ActivityBuff.select().where(ActivityBuff.guild_id == str(ctx.guild.id), ActivityBuff.name == name).first()

        if buff is not None:
            buff.delete_instance()

            await ctx.send(f'Buff `{name}` deleted', ephemeral=True)
        else:
            await ctx.send(f'Buff `{name}` does not exist', ephemeral=True)

    @config_activity.command(name='list_buffs', description='List buffs')
    async def config_activity_list_buffs(self, ctx):
        """List buffs"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        ActivityBuff = self.tables.ActivityBuff
        buffs = ActivityBuff.select().where(ActivityBuff.guild_id == str(ctx.guild.id))

        if not buffs:
            await ctx.send(f'{ctx.guild.name} has no buffs configured', ephemeral=True)
            return

        embed = discord.Embed(title=f'Buffs in {ctx.guild.name}', color=discord.Color.purple())

        for buff in buffs:
            embed.add_field(name=buff.name, value=f'{buff.description} ({buff.value}) - {buff.cost} XP', inline=False)

        await ctx.send(embed=embed, ephemeral=True)

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

    @config_activity.command(name='list_settings', description='List Activity Settings')
    async def config_activity_list_xp_settings(self, ctx):
        """List Activity Settings"""
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

    @config_activity.command(name='adjust_xp', description="Adjust a user's XP")
    async def config_activity_adjust_xp(self, ctx, member:discord.Member, xp:int):
        """Adjust a user's XP"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        ActivityStatus = self.tables.ActivityStatus
        activity_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(member.id), ActivityStatus.guild_id == str(ctx.guild.id)).first()

        if activity_profile is None:
            if xp < 0:
                await ctx.send(f'{member.display_name} does not have enough XP', ephemeral=True)
                return

            activity_profile = ActivityStatus(user_id=str(member.id), user_nick=member.display_name, guild_id=str(ctx.guild.id), current_xp=xp, total_xp = 0, last_activity=datetime.datetime.now(datetime.UTC))
            activity_profile.save()
        else:
            if activity_profile.current_xp + xp < 0:
                await ctx.send(f'{member.display_name} does not have enough XP', ephemeral=True)
                return

            activity_profile.current_xp += xp

            if xp > 0:
                activity_profile.total_xp += xp

            activity_profile.save()

        await ctx.send(f'{xp} XP added to {member.display_name}', ephemeral=True)

    @chat_command(name='afk', description='Set your AFK Status')
    @guild_only()
    async def afk(self, ctx, *, message:str=''):
        """Set your AFK Status"""
        ActivityStatus = self.tables.ActivityStatus
        activity_profile = ActivityStatus.select().where(ActivityStatus.user_id == str(ctx.author.id), ActivityStatus.guild_id == str(ctx.guild.id)).first()

        if activity_profile is None:
            activity_profile = ActivityStatus(user_id=str(ctx.author.id), user_nick=ctx.author.display_name, guild_id=str(ctx.guild.id), current_xp=0, total_xp = 0, last_activity=datetime.datetime.now(datetime.UTC), afk=True, afk_message=message)
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

    class ActivityBuff(bot.database.base_model):
        """Represents a Guild's Custom Activity Buff"""
        db_id = peewee.AutoField(primary_key=True)
        guild_id = peewee.TextField()
        name = peewee.TextField()
        description = peewee.TextField()
        cost = peewee.IntegerField()
        value = peewee.IntegerField()

    class ActivityUserBuff(bot.database.base_model):
        """Represents a User's Custom Activity Buff"""
        db_id = peewee.AutoField(primary_key=True)
        guild_id = peewee.TextField()
        user_id = peewee.TextField()
        item = peewee.ForeignKeyField(ActivityBuff, backref='instances')

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
            ActivityBuff,
            ActivityUserBuff,
            ActivityStatus, 
            ActivityPoint
        ]
    )

    await bot.add_cog(new_cog)
import peewee

import discord

from plasmaBot.cog import PlasmaCog, chat_group, chat_command
from plasmaBot.database import aio_first

class Guesser(PlasmaCog):
    """Game Guess Cog"""

    @chat_command(name='guess', help='Get added to the Guesser Channel')
    async def guess(self, ctx):
        """Get added to the Guesser Channel"""
        GuesserSettings = self.tables.GuesserSettings
        settings = await aio_first(GuesserSettings.select().where(GuesserSettings.guild_id == str(ctx.guild.id)))

        if not settings:
            settings = GuesserSettings(guild_id=str(ctx.guild.id))
            await settings.aio_save()

        if not settings.enabled:
            await ctx.send('The Guesser Game is not enabled', ephemeral=True)
            return

        if not settings.guesser_channel:
            await ctx.send('The Guesser Channel is not set', ephemeral=True)
            return

        if not settings.guesser_role:
            await ctx.send('The Guesser Role is not set', ephemeral=True)
            return

        role = ctx.guild.get_role(int(settings.guesser_role))

        if not role:
            await ctx.send('The Guesser Role is not valid', ephemeral=True)
            return

        if role in ctx.author.roles:
            await ctx.send('You are already in the Guesser Channel', ephemeral=True)
            return

        await ctx.author.add_roles(role, reason="Guesser Access")

        embed = discord.Embed(description=f"**{ctx.author.mention}** has been added to the Guesser Channel")
        embed.set_author(name=f"{ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text='Guesser Game')
        await ctx.send(embed=embed, ephemeral=True)

    @chat_group(name='config_guesser', help='Configure the Guesser Game')
    async def config_guesser(self, ctx):
        """Configure the Guesser Game"""
        pass

    @config_guesser.command(name='list_settings', help='List the Guesser Game Settings')
    async def list_settings(self, ctx):
        """List the Guesser Game Settings"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        GuesserSettings = self.tables.GuesserSettings
        settings = await aio_first(GuesserSettings.select().where(GuesserSettings.guild_id == str(ctx.guild.id)))

        if not settings:
            settings = GuesserSettings(guild_id=str(ctx.guild.id))
            await settings.aio_save()
        
        embed = discord.Embed(description=f"**Guesser is {'Enabled' if settings.enabled else 'Disabled'}**\n\n**Guesser Channel:** {settings.guesser_channel}\n**Guesser Role:** {settings.guesser_role}\n**Guesser Message:** {settings.guesser_message}")
        embed.set_author(name=f"{ctx.guild.name}", icon_url=ctx.guild.icon.url)
        embed.set_footer(text='Guesser Game Settings')

        await ctx.send(embed=embed, ephemeral=True)

    @config_guesser.command(name='toggle', help='Toggle the Guesser Game')
    async def toggle(self, ctx):
        """Toggle the Guesser Game"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        GuesserSettings = self.tables.GuesserSettings
        settings = await aio_first(GuesserSettings.select().where(GuesserSettings.guild_id == str(ctx.guild.id)))

        if not settings:
            settings = GuesserSettings(guild_id=str(ctx.guild.id))
            await settings.aio_save()
        
        settings.enabled = not settings.enabled
        await settings.aio_save()

        await ctx.send(f"Guesser Game {'Enabled' if settings.enabled else 'Disabled'}", ephemeral=True)

    @config_guesser.command(name='set_channel', help='Set the Guesser Channel')
    async def set_channel(self, ctx, channel: discord.TextChannel):
        """Set the Guesser Channel"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        GuesserSettings = self.tables.GuesserSettings
        settings = await aio_first(GuesserSettings.select().where(GuesserSettings.guild_id == str(ctx.guild.id)))

        if not settings:
            settings = GuesserSettings(guild_id=str(ctx.guild.id))
            await settings.aio_save()
        
        settings.guesser_channel = str(channel.id)
        await settings.aio_save()

        await ctx.send(f"Guesser Channel set to {channel.mention}", ephemeral=True)

    @config_guesser.command(name='set_guesser_role', help='Set the Guesser Role')
    async def set_guesser_role(self, ctx, role: discord.Role):
        """Set the Guesser Role"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        GuesserSettings = self.tables.GuesserSettings
        settings = await aio_first(GuesserSettings.select().where(GuesserSettings.guild_id == str(ctx.guild.id)))

        if not settings:
            settings = GuesserSettings(guild_id=str(ctx.guild.id))
            await settings.aio_save()
        
        settings.guesser_role = str(role.id)
        await settings.aio_save()

        await ctx.send(f"Guesser Role set to @{role.name} ({role.id})", ephemeral=True)

    @config_guesser.command(name='set_lockout_role', help='Set the Guesser Lockout Role')
    async def set_lockout_role(self, ctx, role: discord.Role):
        """Set the Guesser Lockout Role"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        GuesserSettings = self.tables.GuesserSettings
        settings = await aio_first(GuesserSettings.select().where(GuesserSettings.guild_id == str(ctx.guild.id)))

        if not settings:
            settings = GuesserSettings(guild_id=str(ctx.guild.id))
            await settings.aio_save()
        
        settings.lockout_role = str(role.id)
        await settings.aio_save()

        await ctx.send(f"Guesser Lockout Role set to @{role.name} ({role.id})", ephemeral=True)

    @config_guesser.command(name='set_message', help='Set the Guesser Message')
    async def set_message(self, ctx, *, message: str):
        """Set the Guesser Message"""
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id in self.bot.developers):
            await ctx.send('You must have `Manage Server` permissions to use this command', ephemeral=True)
            return
        
        GuesserSettings = self.tables.GuesserSettings
        settings = await aio_first(GuesserSettings.select().where(GuesserSettings.guild_id == str(ctx.guild.id)))

        if not settings:
            settings = GuesserSettings(guild_id=str(ctx.guild.id))
            await settings.aio_save()
        
        settings.guesser_message = message.replace('\\n', '\n')
        await settings.aio_save()

        await ctx.send(f"Guesser Message set to:\n{message}", ephemeral=True)

    @PlasmaCog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if not message.guild:
            return
        
        GuesserSettings = self.tables.GuesserSettings
        settings = await aio_first(GuesserSettings.select().where(GuesserSettings.guild_id == str(message.guild.id)))

        if not settings:
            return
        
        if not settings.enabled:
            return
        
        if not settings.guesser_channel:
            return
        
        if message.channel.id != int(settings.guesser_channel):
            return
        
        if not settings.lockout_role:
            return
        
        role = message.guild.get_role(int(settings.lockout_role))

        if not role:
            return
        
        if role in message.author.roles:
            await message.delete()
            return
        
        await message.author.add_roles(role, reason="Guesser Guess Logged")

        await message.add_reaction("✅")

        if settings.guesser_message_id:
            try:
                msg = await message.channel.fetch_message(int(settings.guesser_message_id))        
                await msg.delete()
            except:
                pass
            
        if settings.guesser_message:
            embed = discord.Embed(description=settings.guesser_message)
            msg = await message.channel.send(embed=embed)
            settings.guesser_message_id = str(msg.id)
            await settings.aio_save()


async def setup(bot):
    new_cog = Guesser(bot)

    class GuesserSettings(bot.database.base_model):
        """Represents a Guild's Guesser Settings"""
        db_id = peewee.AutoField(primary_key=True)
        guild_id = peewee.TextField()
        enabled = peewee.BooleanField(default=False)
        guesser_channel = peewee.TextField(null=True)
        guesser_role = peewee.TextField(null=True)
        lockout_role = peewee.TextField(null=True)
        guesser_message = peewee.TextField(null=True)
        guesser_message_id = peewee.TextField(null=True)

    new_cog.register_tables(
        [
            GuesserSettings
        ]
    )

    await bot.add_cog(new_cog)
import peewee
import datetime
import random

from plasmaBot.cog import PlasmaCog, terminal_command, chat_command
from plasmaBot.interface import terminal

class Activity(PlasmaCog):
    """Activity Tracking Cog"""
    def __init__(self, bot):
        self.bot = bot
        super().__init__(bot)

    @PlasmaCog.listener()
    async def on_message(self, message):
        """Update XP and Activity"""
        # Ignore bots
        if message.author.bot:
            return
        
        # Get the user's XP
        XP = self.tables.XP
        current_xp = XP.select().where(XP.user_id == str(message.author.id), XP.guild_id == str(message.guild.id)).first()

        # Update XP
        random_xp = random.randint(5, 15)

        if current_xp is None:
            current_xp = XP(user_id=str(message.author.id), guild_id=str(message.guild.id), current_xp=random_xp, total_xp = random_xp, last_activity=message.created_at.replace(tzinfo=None))
            current_xp.save()

            message_log = self.tables.AP(user_id=str(message.author.id), guild_id=str(message.guild.id), timestamp=message.created_at.replace(tzinfo=None))
            message_log.save()
        elif (message.created_at.replace(tzinfo=None) - current_xp.last_activity).total_seconds() >= 60:
            terminal.add_message('updated xp')
            current_xp.current_xp += random_xp
            current_xp.total_xp += random_xp
            current_xp.last_activity = message.created_at
            current_xp.save()

            message_log = self.tables.AP(user_id=str(message.author.id), guild_id=str(message.guild.id), timestamp=message.created_at.replace(tzinfo=None))
            message_log.save()
        else:
            terminal.add_message(f'did not update xp: {message.author.id}')

        # Log message event
        

async def setup(bot):
    """Setup cog"""
    new_cog = Activity(bot)
    await bot.add_cog(new_cog)

    class XP(bot.database.base_model):
        db_id = peewee.AutoField(primary_key=True)
        user_id = peewee.TextField()
        guild_id = peewee.TextField()
        current_xp = peewee.BigIntegerField(default=0)
        total_xp = peewee.BigIntegerField(default=0)
        last_activity = peewee.DateTimeField(datetime.datetime.now)

    class AP(bot.database.base_model):
        db_id = peewee.AutoField(primary_key=True)
        user_id = peewee.TextField()
        guild_id = peewee.TextField()
        timestamp = peewee.DateTimeField(datetime.datetime.now)

    new_cog.register_tables([XP, AP])
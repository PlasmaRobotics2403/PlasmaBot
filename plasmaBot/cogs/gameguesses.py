from discord.ext.commands import guild_only, check, has_permissions, NoPrivateMessage

from plasmaBot.cog import PlasmaCog, terminal_command, chat_command
from plasmaBot.interface import terminal

class GameGuesses(PlasmaCog):
    """Cog for the FRC Discord 2024 Game Guesses Contest"""

    def only_guild(guild_id: int):
        async def predicate(ctx):
            if ctx.guild is None:
                raise NoPrivateMessage() 
            return ctx.guild.id == guild_id           
        return check(predicate)

    @chat_command(name='guess', description='Get Added to the 2024 Game Guesses Channel')
    @only_guild(176186766946992128)
    async def guess(self, ctx):
        """Get Added to the 2024 Game Guesses Channel"""
    
    @PlasmaCog.listener()
    async def on_message(self, message):
        """Wait for a message in the 2024 Game Guesses Channel"""
        if message.channel.id == 1186891291519365170:
            await message.add_reaction('✅')
            await message.author.add_roles(message.guild.get_role(1186891025751494656))

        
async def setup(bot):
    """Setup cog"""
    await bot.add_cog(GameGuesses(bot))
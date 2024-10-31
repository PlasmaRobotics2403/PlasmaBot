import peewee
import asyncio

import discord
import aiotba

from plasmaBot import Client
from plasmaBot.cog import PlasmaCog, chat_group
from plasmaBot.pagination import Pagination


class TBA(PlasmaCog):
    """The Blue Alliance Data Viewer Cog"""

    def __init__(self, bot: Client):
        super().__init__(bot)
        self.tba_session = aiotba.TBASession(self.bot.config['cogs']['TBA']['api_key'])

    @chat_group(name='tba', description='The Blue Alliance Data Viewer', fallback='help')
    async def tba(self, ctx):
        """The Blue Alliance Data Viewer"""
        embed = discord.Embed(
            title='The Blue Alliance Data Viewer',
            description='Available TBA Commands:', 
            color=discord.Color.purple()
        )

        prefix = self.bot.config['presence']['prefix'] if not ctx.interaction else '/'
        
        embed.add_field(
            name=f'{prefix}tba teams [opt: year]',
            value='List all teams (optionally for a specific year)'
        )
        # embed.add_field(
        #     name=f'{prefix}tba team [team_number]', 
        #     value='Information about a specific team'
        # )
        # embed.add_field(
        #     name=f'{prefix}tba team_event_status [team_number] [event_key]',
        #     value='Information about a specific team at a specific event'
        # )
        # embed.add_field(
        #     name=f'{prefix}tba events [year',
        #     value='List all events for a specific year'
        # )
        # embed.add_field(
        #     name=f'{prefix}tba event [event_key]', 
        #     value='Information about a specific event'
        # )
        # embed.add_field(
        #     name=f'{prefix}tba match [match_key]', 
        #     value='Information about a specific match'
        # )

        await ctx.send(embed=embed, ephemeral=True)

    @tba.command(name='teams', description='List all teams')
    async def tba_teams(self, ctx, year=None):
        """List all teams (optionally for a specific year)"""
        try:
            teams = await self.tba_session.teams(page=None, year=year)
        except aiotba.http.AioTBAError as e:
            failEmbed = discord.Embed(
                title='Error Fetching Teams',
                description=f'Error: {e}',
                color=discord.Color.red()
            )
            await ctx.send(embed=failEmbed, ephemeral=True)
            return
        
        def get_page(page):
            lower = page * 20
            upper = (page + 1) * 20
            slice = teams[lower:upper]

            embed_content = ''

            for team in slice:
                embed_content += f'**Team {team.team_number}**: [{team.nickname}](https://www.thebluealliance.com/team/{team.team_number})\n'

            embed = discord.Embed(title = f'{f"Participating " if year else "All "}Teams{f" for {year}" if year else ""}', description=embed_content, color=discord.Color.purple())
            embed.set_footer(text=f'Page {page + 1} of {len(teams) // 20 + 1}')

            return embed, len(teams) // 20 + 1
        
        pagination = Pagination(ctx.author, ctx, get_page, timeout=60)
        await pagination.navigate()


async def setup(bot: Client):
    new_cog = TBA(bot)

    await bot.add_cog(new_cog)
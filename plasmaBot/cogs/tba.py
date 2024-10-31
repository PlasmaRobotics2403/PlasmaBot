import peewee
import json

import discord
import aiotba

from datetime import datetime

from plasmaBot import Client
from plasmaBot.cog import PlasmaCog, chat_group
from plasmaBot.pagination import Pagination
from plasmaBot.interface import terminal


class SimpleTeam:
    """A Simple Team Object for TBA Teams Lists Stored in Cache"""
    
    def __init__(self, team_number, nickname):
        self.team_number = team_number
        self.nickname = nickname


class SimpleTeamEncoder(json.JSONEncoder):
    """JSON Encoder for SimpleTeam Objects"""
    
    def default(self, o):
        if isinstance(o, SimpleTeam):
            return {'a': o.team_number, 'b': o.nickname}
        return super().default(o)
    

class SimpleTeamDecoder(json.JSONDecoder):
    """JSON Decoder for SimpleTeam Objects"""
    
    def decode(self, s):
        obj = super().decode(s)
        if isinstance(obj, list):
            return [SimpleTeam(team['a'], team['b']) for team in obj]
        return obj


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
        await ctx.defer(ephemeral=True)

        teams = await self.get_teams_from_cache(year if year else 'All')
        
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

    async def get_teams_from_cache(self, year='All'):
        """Retrieve Teams from Cache (fallback to TBA API)"""
        try:
            year = int(year)
            if year < 1992 or (year > datetime.now().year + 1):
                return []
        except:
            pass
        
        TBATeamsCache = self.tables.TBATeamsCache
        teams = TBATeamsCache.select(
            TBATeamsCache.teams, 
            TBATeamsCache.last_checked
        ).where(
            TBATeamsCache.year == year
        ).first()

        if teams and (year == datetime.now().year or year == datetime.now().year + 1):
            if teams.last_checked and (datetime.now() - teams.last_checked).days < 1:
                teams_obj = json.loads(teams.teams, cls=SimpleTeamDecoder)
                return teams_obj
            else:
                teams_obj = await self.load_new_teams(year)

                teams.teams = json.dumps(teams_obj, cls=SimpleTeamEncoder)
                teams.last_checked = datetime.now()
                teams.save()
                
                return teams_obj
        elif teams and year != 'All':
            teams_obj = json.loads(teams.teams, cls=SimpleTeamDecoder)
            return teams_obj
        elif teams and year == 'All':
            if teams.last_checked and (datetime.now() - teams.last_checked).days < 7:
                teams_obj = json.loads(teams.teams, cls=SimpleTeamDecoder)
                return teams_obj
            else:
                teams_obj = await self.load_new_teams(year)

                teams.teams = json.dumps(teams_obj, cls=SimpleTeamEncoder)
                teams.last_checked = datetime.now()
                teams.save()

                return teams_obj
        else:
            teams_obj = await self.load_new_teams(year)
    
            new_teams = TBATeamsCache.create(
                year=year,
                teams=json.dumps(teams_obj, cls=SimpleTeamEncoder),
                last_checked=datetime.now()
            )
            new_teams.save()


            return teams_obj

    async def load_new_teams(self, year='All'):
        """Load new teams from TBA API"""
        try:
            tba_teams = await self.tba_session.teams(page=None, year=None if year == 'All' else year)
        except aiotba.http.AioTBAError:
            return []

        return [SimpleTeam(team.team_number, team.nickname) for team in tba_teams]


async def setup(bot: Client):
    new_cog = TBA(bot)

    class LongTextField(peewee.TextField):
        field_type = 'LONGTEXT'

    class TBATeamsCache(bot.database.base_model):
        """Cache for TBA Teams in a given year"""
        year = peewee.IntegerField()
        teams = peewee.TextField()
        last_checked = peewee.DateTimeField(null=True)

    new_cog.register_tables(
        [
            TBATeamsCache
        ]
    )

    await bot.add_cog(new_cog)
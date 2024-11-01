import peewee
import json

import discord
import aiotba

from datetime import datetime
from uuid import uuid4

from plasmaBot import Client
from plasmaBot.cog import PlasmaCog, chat_group
from plasmaBot.pagination import Pagination
from plasmaBot.interface import terminal
from plasmaBot.database import aio_first


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

    @tba.command(name='teams', description='Information about a specific team')
    async def tba_teams(self, ctx, year:int=None):
        """List all teams (optionally for a specific year)"""
        await ctx.defer(ephemeral=True)
        
        current_date = datetime.now()
        current_year = current_date.year

        if year:
            if year < 1992 or (year > datetime.now().year + 1):
                await ctx.send('Invalid Year', ephemeral=True)
                return
        else:
            year = 0

        TBATeamCache = self.tables.TBATeamCache
        TBATeamsCacheLog = self.tables.TBATeamsCacheLog
        TBATeamYearRelator = self.tables.TBATeamYearRelator
        year_log = await aio_first(TBATeamsCacheLog.select().where(TBATeamsCacheLog.year == year))

        if year_log:
            if year == 0 and (current_date - year_log.last_checked).days >= 7:
                if not ctx.interaction:
                    await ctx.send('Please wait while I fetch data and update the Team Cache...')

                all_teams = await TBATeamCache.select().order_by(TBATeamCache.team_number).aio_execute()
                teams = await self.cache_new_teams(year, all_teams)
            elif year >= current_year and (current_date - year_log.last_checked).days >= 7:
                if not ctx.interaction:
                    await ctx.send('Please wait while I fetch data and update the Team Cache...')
                
                all_teams = await TBATeamCache.select().order_by(TBATeamCache.team_number).aio_execute()
                teams = await self.cache_new_teams(year, all_teams)
            else: 
                teams = await TBATeamYearRelator.select().join(TBATeamCache).where(TBATeamYearRelator.year == year_log).order_by(TBATeamCache.team_number).aio_execute()

            await self.generate_teams_pagination(ctx, teams, year)
        else:
            if not ctx.interaction:
                await ctx.send('Please wait while I fetch data and update the Team Cache...')
            
            all_teams = await TBATeamCache.select().order_by(TBATeamCache.team_number).aio_execute()
            teams = await self.cache_new_teams(year, all_teams)
            await self.generate_teams_pagination(ctx, teams, year)

    async def cache_new_teams(self, year, currentTeams):
        """Cache new teams from TBA API"""
        now = datetime.now()
        create_tracker = str(uuid4())

        try:
            tba_teams = await self.tba_session.teams(page=None, year=year)
        except aiotba.http.AioTBAError:
            return []
        
        TBATeamsCacheLog = self.tables.TBATeamsCacheLog
        current_year_log = await aio_first(TBATeamsCacheLog.select().where(TBATeamsCacheLog.year == year))

        if current_year_log:
            log = current_year_log
        else:
            new_year_log = TBATeamsCacheLog(year=year, last_checked=now)
            await new_year_log.aio_save()
            log = new_year_log

        TBATeamCache = self.tables.TBATeamCache
        TBATeamYearRelator = self.tables.TBATeamYearRelator

        update_teams = []
        create_teams = []
        existing_teams = []
        create_relators = []

        for team in tba_teams:
            found_team = next((t for t in currentTeams if t.team_number == int(team.team_number)), None)
            if found_team:
                currentTeams.remove(found_team)

            if found_team:
                if found_team.nickname != team.nickname or found_team.name != team.name or found_team.city != team.city or found_team.state_prov != team.state_prov or found_team.country != team.country or found_team.address != team.address or found_team.postal_code != team.postal_code or found_team.gmaps_place_id != team.gmaps_place_id or found_team.gmaps_url != team.gmaps_url or found_team.lat != team.lat or found_team.lng != team.lng or found_team.location_name != team.location_name or found_team.website != team.website or found_team.rookie_year != team.rookie_year or found_team.home_championship != team.home_championship:
                    found_team.nickname = team.nickname
                    found_team.name = team.name
                    found_team.city = team.city
                    found_team.state_prov = team.state_prov
                    found_team.country = team.country
                    found_team.address = team.address
                    found_team.postal_code = team.postal_code
                    found_team.gmaps_place_id = team.gmaps_place_id
                    found_team.gmaps_url = team.gmaps_url
                    found_team.lat = team.lat
                    found_team.lng = team.lng
                    found_team.location_name = team.location_name
                    found_team.website = team.website
                    found_team.rookie_year = team.rookie_year
                    found_team.home_championship = team.home_championship
                    found_team.last_checked = now
                    update_teams.append(found_team)
                existing_teams.append(found_team)

            else:
                new_team = TBATeamCache(
                    tracking_uuid=create_tracker,
                    team_number=int(team.team_number),
                    nickname=team.nickname,
                    name=team.name,
                    city=team.city,
                    state_prov=team.state_prov,
                    country=team.country,
                    address=team.address,
                    postal_code=team.postal_code,
                    gmaps_place_id=team.gmaps_place_id,
                    gmaps_url=team.gmaps_url,
                    lat=team.lat,
                    lng=team.lng,
                    location_name=team.location_name,
                    website=team.website,
                    rookie_year=team.rookie_year,
                    home_championship=team.home_championship,
                    last_checked=now
                )
                create_teams.append(new_team)

        if len(create_teams) > 0:
            TBATeamCache.bulk_create(create_teams, batch_size=100)

        if len(update_teams) > 0:
            TBATeamCache.bulk_update(update_teams, batch_size=50)

        for team in existing_teams:
            create_relators.append(TBATeamYearRelator(team=team, year=log))

        new_teams = await TBATeamCache.select().where(TBATeamCache.tracking_uuid == create_tracker).aio_execute()

        for team in new_teams:
            create_relators.append(TBATeamYearRelator(team=team, year=log))

        if len(create_relators) > 0:
            TBATeamYearRelator.bulk_create(create_relators, batch_size=100)

        return create_relators

    async def generate_teams_pagination(self, ctx, teams, year):
        """Generate a Pagination for Teams"""
        async def get_page(page):
            lower = page * 20
            upper = (page + 1) * 20
            slice = teams[lower:upper]

            embed_content = ''

            for year_relator in slice:
                team = year_relator.team
                embed_content += f'**Team {team.team_number}**: [{team.nickname}](https://www.thebluealliance.com/team/{team.team_number})\n'

            embed = discord.Embed(title = f'{f"Participating " if year!=0 else "All "}Teams{f" for {year}" if year!=0 else ""}', description=embed_content, color=discord.Color.purple())
            embed.set_footer(text=f'Page {page + 1} of {len(teams) // 20 + 1}')

            return embed, len(teams) // 20 + 1

        pagination = Pagination(ctx.author, ctx, get_page, timeout=60)
        await pagination.navigate()
    

async def setup(bot: Client):
    new_cog = TBA(bot)

    class TBATeamCache(bot.database.base_model):
        """Cache for TBA Teams in a given year"""
        db_id = peewee.AutoField(primary_key=True)
        tracking_uuid = peewee.TextField(null=True)
        team_number = peewee.IntegerField()
        nickname = peewee.TextField(null=True)
        name = peewee.TextField(null=True)
        city = peewee.TextField(null=True)
        state_prov = peewee.TextField(null=True)
        country = peewee.TextField(null=True)
        address = peewee.TextField(null=True)
        postal_code = peewee.TextField(null=True)
        gmaps_place_id = peewee.TextField(null=True)
        gmaps_url = peewee.TextField(null=True)
        lat = peewee.FloatField(null=True)
        lng = peewee.FloatField(null=True)
        location_name = peewee.TextField(null=True)
        website = peewee.TextField(null=True)
        rookie_year = peewee.IntegerField(null=True)
        home_championship = peewee.TextField(null=True)
        last_checked = peewee.DateTimeField(default=datetime.now)

    class TBATeamsCacheLog(bot.database.base_model):
        """Cache for TBA Teams in a given year"""
        db_id = peewee.AutoField(primary_key=True)
        year = peewee.IntegerField()
        last_checked = peewee.DateTimeField(null=True)

    class TBATeamYearRelator(bot.database.base_model):
        """Relator for TBATeamCache and TBATeamsCache"""
        db_id = peewee.AutoField(primary_key=True)
        team = peewee.ForeignKeyField(TBATeamCache, backref='years')
        year = peewee.ForeignKeyField(TBATeamsCacheLog, backref='teams')

    new_cog.register_tables(
        [
            TBATeamCache,
            TBATeamsCacheLog,
            TBATeamYearRelator
        ]
    )

    await bot.add_cog(new_cog)
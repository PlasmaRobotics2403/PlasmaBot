from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response
import discord

from plasmaBot import exceptions
import discord

import re

from plasmaBot.plugins.resources.TBAPythonAPI import *

import logging
log = logging.getLogger('discord')

class TBAPlugin(PBPlugin):
    name = 'TBA (The Blue Alliance)'
    globality = 'all'
    help_exclude = False

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)
        self.TBA = TBAParser(2403, "Discord Bot", "0.1.0")
        self.team_key_pattern = re.compile('[f][r][c][0-9]{3,4}', re.IGNORECASE)
        self.event_key_pattern = re.compile('[1-2][01289][0-9][0-9][a-z]{3}[a-z0-9]{1,2}', re.IGNORECASE)

    async def cmd_tba(self, message, channel, leftover_args):
        """
        Usage:
            {command_prefix}TBA (Item to return) (Search Parameters)

        Pulls data from TBA.  For more info, do {command_prefix}tba
        """
        no_response = '```The Blue Alliance - '
        no_response += 'Pulls Data from The Blue Alliance API\n'
        no_response += ' • ' + self.bot.config.prefix + 'tba team (team\\number)\n'
        no_response += '   • pulls Team Information\n'
        no_response += ' • ' + self.bot.config.prefix + 'tba event (event\\name)\n'
        no_response += '   • pulls Event Information\n'

        try:
            cmd_type = leftover_args[0]
            del leftover_args[0]
        except:
            no_response += '```'
            return Response(no_response, reply=False, delete_after=45)

        if cmd_type == 'team':
            if bool(self.team_key_pattern.search(leftover_args[0])):
                key = leftover_args[0]
            else:
                param = ''
                for partial_msg in leftover_args:
                    param += partial_msg + ' '
                param = param[:-1]
                try:
                    num = int(param)
                except:
                    return Response('Not a valid team number. `' + self.bot.config.prefix + 'tba team [Number]`', reply=False, delete_after=30)
                key = "frc" + str(num)
            try:
                team = self.TBA.get_team(key)
            except:
                return Response('Something went wrong when looking up the team.', reply=False, delete_after=30)
            if team.nickname == None:
                return Response('Team does not exist.', reply=False, delete_after=30)
            team_data = "Team " + str(team.team_number) + ": " + team.nickname + "\nFrom: " + team.location
            if team.website != None:
                team_data = team_data + "\nWebsite: " + team.website
            if team.motto != None:
                team_data = team_data + '\nMotto: "' + team.motto + '"'
            return Response(team_data, reply=False, delete_after=60)

        elif cmd_type == 'event':
            if bool(self.event_key_pattern.search(leftover_args[0])):
                key = leftover_args[0]

            else:
                try:
                    year_str = leftover_args[0]
                    del leftover_args[0]
                    param = ''
                    for partial_msg in leftover_args:
                        param += partial_msg + ' '
                    param = param[:-1]
                except:
                    return Response('Additional arguments needed. ```' + self.bot.config.prefix + 'tba event [Year] [Beginning of event name]```', reply=False, delete_after=30)
                try:
                    year = int(year_str)
                except:
                    return Response('Year must be an integer.', reply=False, delete_after=30)

                key = self.TBA.calc_event_key(year, param)

                if key == '1':
                    return Response('Multiple events found. Please refine your search.', reply=False, delete_after=30)
                if key == '0':
                    return Response('No events found. Please ensure spelling is correct.', reply=False, delete_after=30)

            event = self.TBA.get_event(key)
            event_data = event.name + "\nYear: " + str(event.year) + "\nLocation: " + event.location + "\nDates: " + event.start_date + " to " + event.end_date + "\nEvent Type: " + event.event_type_string + "\nhttps://www.thebluealliance.com/event/" + event.key
            return Response(event_data, reply=False, delete_after=60)

        elif cmd_type == 'awards':
            if len(leftover_args) >= 1:
                if bool(self.team_key_pattern.search(leftover_args[0])):
                    team_key = leftover_args[0]
                    team_number = team_key[3:]
                else:
                    try:
                        team_number = int(leftover_args[0])
                    except:
                        no_response += '\n\nInvalid Team Number Supplied```'
                        return Response(no_response, reply=False, delete_after=45)

                    team_key = 'frc' + str(team_number)

                if len(leftover_args) >= 2:
                    try:
                        search_year = int(leftover_args[1])
                    except:
                        no_response += '\n\nSearch Year Provided but Invalid```'
                        return Response(no_response, reply=False, delete_after=45)
                else:
                    search_year = None

                try:
                    team_awards = self.TBA.get_team_history_awards(team_key)
                except:
                    return Respose('Something went wrong in collecting Team Awards')

                awards_msg_content = '**Team Awards for Team {}'.format(team_number)

                if search_year:
                    awards_msg_content += ' in {}**\n'.format(search_year)
                else:
                    awards_msg_content += '**\n'

                for award in team_awards:
                    if not search_year or search_year == award.year:
                        award_string = '{}: {} ({})\n'.format(award.year, award.name, award.event_key)

                        tentative_msg = awards_msg_content + award_string
                        if len(tentative_msg) > 2000:
                            await self.bot.safe_send_message(
                                channel, awards_msg_content,
                                expire_in=120 if self.bot.config.delete_messages else 0,
                                also_delete=message if self.bot.config.delete_invoking else None
                            )
                            awards_msg_content = ''
                        else:
                            awards_msg_content = tentative_msg

                return Response(awards_msg_content, reply=False, delete_after=120)

            else:
                no_response += '\n\nInvalid Team Number Supplied```'
                return Response(no_response, reply=False, delete_after=45)

        else:
            no_response += '\n\nInvalid Secondary Command Supplied```'
            return Response(no_response, reply=False, delete_after=45)

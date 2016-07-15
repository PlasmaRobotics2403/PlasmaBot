from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response
import discord

from plasmaBot import exceptions
import discord

from plasmaBot.plugins.resources.TBAPythonAPI import *

import logging
log = logging.getLogger('discord')

class TBAPlugin(PBPlugin):
    name = 'TBA (The Blue Alliance) Plugin'
    globality = 'all'
    help_exclude = False

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)
        self.TBA = TBAParser(2403, "Discord Bot", "0.1.0")

    async def cmd_tba(self, message, leftover_args):
        """
        Usage:
            {command_prefix}TBA (Item to return) (Search Parameters)

        Get Information from The Blue Alliance (TBA)
        """

        try:
            cmd_type= leftover_args[0]
            del leftover_args[0]
        except:
            no_response = '__**The Blue Alliance**__\n'
            no_response += '_Pulls Data from The Blue Alliance API_\n'
            no_response += ' • _' + self.bot.config.prefix + 'team (team\_number)_\n'
            no_response += '   • pulls Team Information\n'
            no_response += ' • _' + self.bot.config.prefix + 'event (event\_name)_\n'
            no_response += '   • pulls Event Information\n'

            return Response(no_response, reply=False, delete_after=45)

        if cmd_type == 'team':
            param = ''
            for partial_msg in leftover_args:
                param += partial_msg + ' '
            param = param[:-1]
            try:
                num = int(param)
            except:
                return Response('Not a valid team number. ```' + self.bot.config.prefix + 'tba team [Number]```', reply=False, delete_after=30)
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

        if cmd_type == 'event':
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
            #try:
            key = self.TBA.calc_event_key(year, param)
            #except:
            #    return Response('Unknown error looking up event key.', reply=False, delete_after=30)
            if key == '1':
                return Response('Multiple events found. Please refine your search.', reply=False, delete_after=30)
            if key == '0':
                return Response('No events found. Please ensure spelling is correct.', reply=False, delete_after=30)
            event = self.TBA.get_event(key)
            event_data = event.name + "\nYear: " + str(event.year) + "\nLocation: " + event.location + "\nDates: " + event.start_date + " to " + event.end_date + "\nEvent Type: " + event.event_type_string + "\nhttps://www.thebluealliance.com/event/" + event.key
            return Response(event_data, reply=False, delete_after=60)

        return Response('Invalid secondary command. Must be either "team" or "event"', reply=False, delete_after=60)

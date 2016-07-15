#TBApi - BLUE ALLIANCE API FOR PYTHON

import os
import sys
import requests
import datetime
import numpy as np
from numpy import array as np_array

#Class that defines an FRC team. Variables are automatically set when created. raw variable contains the raw json array that TBA returned
class TBATeam:
    def __init__(self, raw_json):
        self.raw = raw_json
        self.website = raw_json['website']
        self.name = raw_json['name']
        self.locality = raw_json['locality']
        self.region = raw_json['region']
        self.country_name = raw_json['country_name']
        self.location = raw_json['location']
        self.team_number = raw_json['team_number']
        self.key = raw_json['key']
        self.nickname = raw_json['nickname']
        self.rookie_year = raw_json['rookie_year']
        self.motto = raw_json['motto']

#Class that defines an FRC event. Variables are automatically set when created. raw variable contains the raw json array that TBA returned
class TBAEvent:
    def __init__(self, raw_json):
        self.raw = raw_json
        self.key = raw_json['key']
        self.website = raw_json['website']
        self.official = raw_json['official']
        self.end_date = raw_json['end_date']
        self.name = raw_json['name']
        self.short_name = raw_json['short_name']
        self.facebook_eid = raw_json['facebook_eid']
        self.event_district_string = raw_json['event_district_string']
        self.venue_address = raw_json['venue_address']
        self.event_district = raw_json['event_district']
        self.location = raw_json['location']
        self.event_code = raw_json['event_code']
        self.year = raw_json['year']
        self.webcast = raw_json['webcast']
        self.timezone = raw_json['timezone']
        self.alliances = raw_json['alliances']
        self.event_type_string = raw_json['event_type_string']
        self.start_date = raw_json['start_date']
        self.event_type = raw_json['event_type']

#Class that defines the stats from a given event.  raw variable contains the raw json array that is returned by the blue alliance API.  Due to TBA not being consistant in what they return, not all values will be present with data on each call.
class TBAEventStats:
    def __init__(self, raw_json):
        self.raw = raw_json
        try:
            self.opr = TBAEventStatsCategory(raw_json["oprs"]) #sets up a TBAEventStatsCategory for the OPR stat if it is passed back by TBA
        except:
            pass
        try:
            self.ccwm = TBAEventStatsCategory(raw_json["ccwms"]) #sets up a TBAEventStatsCategory for the CCWM stat if it is passed back by TBA
        except:
            pass
        try:
            self.dpr = TBAEventStatsCategory(raw_json["dprs"]) #sets up a TBAEventStatsCategory for the DPR stat if it is passed back by TBA
        except:
            pass
        try:
            self.year_specific = raw_json['year_specific'] #sets up a TBAEventStatsCategory for the Year Specific Stats if it they are passed back by TBA
        except:
            pass

#Class that defines the event stats under a given category (opr, ccwm, dpr, year_specific) with a method to get the stats under this category given a team_key or team_number
class TBAEventStatsCategory:
    def __init__(self, raw_json):
        self.raw = raw_json

    def get_team(self, team_number): #get the stats value for a given team
        if not isinstance(team_number, str):
            team_number = str(team_number)
        else:
            if team_number.startswith('frc'):
                team_number = team_number[3:]

        if not team_number.isdigit():
            print("\n[TBA-API] BAD TEAM NUMBER SUPLIED WITH TBAEventStatsObj.get_team(team_number)\n")
            return

        team_stat = self.raw[team_number]
        return team_stat

#Class that defines the rankings of a given event, and provides methods to get the TBAEventTeamRank objects for given teams or event ranks
class TBAEventRankings:
    def __init__(self, raw_json):
        self.raw = raw_json
        self.keys = raw_json[0]

        rank_dictionary = {}
        team_rank_dictionary = {}

        del raw_json[0]

        for key in raw_json:
                team_dictionary = TBAEventTeamRank(self.keys, key) #creates a TBAEventTeamRank object for the given team as found in the rank dictionary passed back by TBA

                team_rank = str(key[0])
                team_number = str(key[1])

                rank_dictionary[team_rank] = team_dictionary #indexes the given object by event rank
                team_rank_dictionary[team_number] = team_dictionary #indexes the given object by team number

        self.rankings = rank_dictionary
        self.team_rankings = team_rank_dictionary

    def get_rank(self, rank): #gets the TBAEventTeamRank obj for a given event rank
        team_obj = self.rankings[str(rank)]
        return team_obj

    def get_rank_by_team(self, team_number): #gets the TBAEventTeamRank obj for a given team number
        if not isinstance(team_number, str):
            team_number = str(team_number)
        else:
            if team_number.startswith('frc'):
                team_number = team_number[3:]

        if not team_number.isdigit():
            print("\n[TBA-API] BAD TEAM NUMBER SUPLIED WITH TBAEventRankings.get_rank_by_team(team_number)\n")
            return

        team_obj = self.team_rankings[team_number]

        return team_obj

#Class that Creates a object with call attributes based on what is returned from TBA since it is not standardized
class TBAEventTeamRank:
    def __init__(self, key_list, team_list):
        self.raw = team_list

        check_pos = 0

        for key in key_list:
            if key is "Record (W-L-T)":
                key = "record"
            key = key.lower().replace(" ", "_").replace("&","and").replace("/","_").replace("-","_")
            setattr(self, key, team_list[check_pos])
            check_pos += 1

#Class that defines the District Points from a given event.  This is by event, but the event term has been removed from the class name to prevent issues that arise with long class names
class TBADistrictPoints:
    def __init__(self, raw_json):
        self.raw = raw_json
        self.points = raw_json['points']

    def get_team(self, team_key):
        if isinstance(team_key, str) and team_key.isdigit():
            team_key = 'frc' + team_key
        else:
            team_key = 'frc' + str(team_key)

        dist_points_json = self.points[team_key]

        dist_points_obj = TBADistrictPointsTeam(dist_points_json)

        return dist_points_obj

#Class that defines the District points of a given team, created by get_team in TBADistrictPoints
class TBADistrictPointsTeam:
    def __init__(self, raw_json):
        self.raw = raw_json
        self.alliance_points = raw_json['alliance_points']
        self.total = raw_json['total']
        self.award_points = raw_json['award_points']
        self.elim_points = raw_json['elim_points']
        self.qual_points = raw_json['qual_points']

#Class that defines an FRC match. Variables are automatically set when created. raw variable contains the raw json array that TBA returned
class TBAMatch:
    def __init__(self, raw_json):
        self.raw = raw_json
        self.comp_level = raw_json['comp_level']
        self.match_number = raw_json['match_number']
        self.videos = raw_json['videos']
        self.time_string = raw_json['time_string']
        self.set_number = raw_json['set_number']
        self.key = raw_json['key']
        self.time = raw_json['time']
        self.score_breakdown = raw_json['score_breakdown']
        self.alliances = raw_json['alliances']
        self.event_key = raw_json['event_key']

#Class that defines an FRC award. Variables are automatically set when created. raw variable contains the raw json array that TBA returned
class TBAAward:
    def __init__(self, raw_json):
        self.raw = raw_json
        self.event_key = raw_json['event_key']
        self.award_type = raw_json['award_type']
        self.type = raw_json['award_type']
        self.name = raw_json['name']
        self.recipient_list = raw_json['recipient_list']
        self.year = raw_json['year']

#Class that defines an FRC media item (video, photo, etc). Variables are automatically set when created. raw variable contains the raw json array that TBA returned
class TBAMedia:
    def __init__(self, raw_json):
        self.raw = raw_json
        self.type = raw_json['type']
        self.details = raw_json['details']
        self.foreign_key = raw_json['foreign_key']

class TBARobotGroup:
    def __init__(self, raw_json):
        self.raw = raw_json

    def get_year(self, year):
        year_json = self.raw[str(year)]
        year_obj = TBARobot(year_json)

        return year_obj

#Class that defines an FRC robot. Variables are automatically set when created. raw variable contains the raw json array that TBA returned
class TBARobot:
    def __init__(self, raw_json):
        self.raw = raw_json
        self.team_key = raw_json['team_key']
        self.name = raw_json['name']
        self.key = raw_json['key']
        self.year = raw_json['year']

#This is the main class. All reuqests are made through here
class TBAParser:
    def __init__(self, team_number, package_name, version_number): #Init method. Requires info to identify the end user of the requests made to TBA
        self.team_number = team_number
        self.package_name = package_name
        self.version_number = version_number
        self.header = {'X-TBA-App-Id': 'frc{team}:{package}:{version}'.format(team = team_number, package = package_name, version = version_number)}
        self.baseURL = 'http://www.thebluealliance.com/api/v2'

    def __pull_team_list_by_page(self, page): #Helper function to make code for get_team_list simpler.
        request = (self.baseURL + "/teams/" + str(page))
        response = requests.get(request, headers = self.header)
        json_list = response.json()
        team_list = []

        for team in json_list:
            team_obj = TBATeam(team)
            team_list = team_list + [team_obj]

        return team_list

    def get_team_list(self, page = None): #get list of FRC teams' TBATeam objects, either the entire list, or by page #
        if not page is None:
            team_list = self.__pull_team_list_by_page
        else:
            team_list = []

            for page in range(0,100): #Allows for significant team-expansion (up to 55000 FRC teams).  At that point in time, we will probably be on APIv3 or more.
                partial_list = self.__pull_team_list_by_page(page)

                try:
                    if not partial_list[0] is None:
                        team_list = team_list + partial_list #combine partial with previously set up 'full' list to grow list as we iterate over the range of pages
                    else:
                        break #kill loop once we hit NULL data
                except:
                    break #kill loop once we hit NULL data

        return team_list

    def get_team(self, team_key): #get a team's TBATeam object
        request = (self.baseURL + "/team/" + team_key)
        response = requests.get(request, headers = self.header)
        json = response.json()
        team_object = TBATeam(json)

        return team_object

    def __pull_team_events(self, team_key, year): #helper function to pull team events for use in get_team_events with a year passed in
        request = (self.baseURL + "/team/" + team_key + "/" + str(year) + "/events")
        response = requests.get(request, headers = self.header)
        json = response.json()
        event_list = []

        for event in json:
            event_obj = TBAEvent(event)
            event_list = event_list + [event_obj]

        return event_list

    def __pull_all_team_events(self, team_key): #helper function to pull team events for use in get_team_events without a year passed in
        request = (self.baseURL + "/team/" + team_key + "/history/events")
        response = requests.get(request, headers = self.header)
        json = response.json()
        event_list = []

        for event in json:
            event_obj = TBAEvent(event)
            event_list = event_list + [event_obj]

        return event_list

    def get_team_events(self, team_key, year=None): #Get a list of event objects that a given team has competed in
        if not year is None:
            event_list = self.__pull_team_events(team_key, year)
        else:
            event_list = self.__pull_all_team_events(team_key)
        return event_list

    def get_team_event_awards(self, team_key, event_key): #Get a list of all award objects that a team has won at a given event
        request = (self.baseURL + "/team/" + team_key + "/event/" + event_key + "/awards")
        response = requests.get(request, headers = self.header)
        json = response.json()
        award_list = []

        for award in json:
            award_obj = TBAAward(award)
            award_list = award_list + [award_obj]

        return award_list

    def get_team_event_matches(self, team_key, event_key): #Get a list of all match objects that a team competed in at a given event
        request = (self.baseURL + "/team/" + team_key + "/event/" + event_key + "/matches")
        response = requests.get(request, headers = self.header)
        json = response.json()
        match_list = []

        for match in json:
            match_obj = TBAMatch(match)
            match_list = match_list + [match_obj]

        return match_list

    def get_team_years_participated(self, team_key): #Get a list of years participated
        request = (self.baseURL + "/team/" + team_key + "/years_participated")
        response = requests.get(request, headers = self.header)
        years_participated = response.json()

        return years_participated

    def __pull_team_media(self, team_key, year): #pulls team media for use in get_team_media
        request = (self.baseURL + "/team/" + team_key + "/" + str(year) + "/media")
        response = requests.get(request, headers = self.header)
        json = response.json()
        media_list = []

        for media in json:
            media_obj = TBAMedia(media)
            media_list = media_list + [media_obj]

        return media_list

    def get_team_media(self, team_key, year = None): #Get a list of all media objects a team is responsible for
        if not year is None:
            media_list = self.__pull_team_media(team_key, year)
        else:
            rookie_year = self.get_team(team_key).rookie_year
            current_year = datetime.datetime.now().year

            media_list = []

            for check_year in range(rookie_year, current_year):
                partial_list = self.__pull_team_media(team_key, check_year)
                media_list = media_list + partial_list

        return media_list

    def get_team_history_events(self, team_key): #Returns a list of all event objects a team has attended
        events_list = self.__pull_all_team_events(team_key)
        return events_list

    def get_team_history_awards(self, team_key): #Returns a list of all award objects a team has won
        request = (self.baseURL + "/team/" + team_key + "/history/awards")
        response = requests.get(request, headers = self.header)
        json = response.json()
        award_list = []

        for award in json:
            award_obj = TBAAward(award)
            award_list = award_list + [award_obj]

        return award_list

    def get_team_history_robots(self, team_key): #Returns a list off all robot objects a team has made (seems to only work 2015 onwards)
        request = (self.baseURL + "/team/" + team_key + "/history/robots")
        response = requests.get(request, headers = self.header)
        json = response.json()

        robo_container_obj = TBARobotGroup(json)

        return robo_container_obj

    def get_team_history_districts(self, team_key): #gets a list of districts a team has participated in by year
        request = (self.baseURL + "/team/" + team_key + "/history/districts")
        response = requests.get(request, headers = self.header)
        team_history_districts = response.json()

        return team_history_districts

    def calc_team_key(self, number): #Calculates a team's key given their team number
        key = "frc" + str(number)
        return key

    def get_event_list(self, year): #Returns a list of all event objects for a given year
        request = (self.baseURL + "/events/" + str(year))
        response = requests.get(request, headers = self.header)
        json = response.json()
        event_list = []

        for event in json:
            event_obj = TBAEvent(event)
            event_list = event_list + [event_obj]

        return event_list

    def get_event(self, event_key): #Returns a single event object given an event key
        request = (self.baseURL + "/event/" + event_key)
        response = requests.get(request, headers = self.header)
        json = response.json()

        event_obj = TBAEvent(json)

        return event_obj

    def get_event_teams(self, event_key): #Returns a list of all team objects that attended an event
        request = (self.baseURL + "/event/" + event_key + "/teams")
        response = requests.get(request, headers = self.header)
        json = response.json()

        team_list = []

        for team in json:
            team_obj = TBATeam(team)
            team_list = team_list + [team_obj]

        return team_list

    def get_event_matches(self, event_key): #Returns a list of all match objects in a given event
        request = (self.baseURL + "/event" + event_key + "/matches")
        response = requests.get(request, headers = self.header)
        json = response.json()

        match_list = []

        for match in json:
            match_obj = TBAMatch(match)
            match_list = match_list + [match_obj]

        return match_list

    def get_event_stats(self, event_key):
        request = (self.baseURL + "/event/" + event_key + "/stats")
        response = requests.get(request, headers = self.header)
        json = response.json()

        event_stats = TBAEventStats(json)

        return event_stats

    def get_event_rankings(self, event_key):
        request = (self.baseURL + "/event/" + event_key + "/rankings")
        response = requests.get(request, headers = self.header)
        json = response.json()

        event_rankings = TBAEventRankings(json)

        return event_rankings

    def get_event_awards(self, event_key): #Returns a list of all award objects given out at an event
        request = (self.baseURL + "/event/" + event_key + "/awards")
        response = requests.get(request, headers = self.header)
        json = response.json()

        award_list = []

        for award in json:
            award_obj = TBAAward(award)
            award_list = award_list + [award_obj]

        return award_list

    def get_event_district_points(self, event_key): #returns a TBADistrictPoints obj, capable of method chaining
        request = (self.baseURL + "/event/" + event_key + "/district_points")
        response = requests.get(request, headers = self.header)
        json = response.json()

        district_points_obj = TBADistrictPoints(json)

        return district_points_obj

    #Calculates event key from both year and event nickname.
    #Name variable does not have to be complete, but it must be properly capitalized and specific enough to specify a single event
    #Returns "0" is no events are found, "1" if more than one event is found, and event key otherwise.
    #ALL RETURNS ARE STRINGS
    #Based on method from https://github.com/Alexanders101/The-Blue-Alliance-Python-API/
    def calc_event_key(self, year, name):
        request = (self.baseURL + "/events/" + str(year))
        response = requests.get(request, headers = self.header)
        dictionary = response.json()
        events = np_array([[str(event['short_name']), str(event['key'])] for event in dictionary])
        ret = ''
        for sub in events[:, 0]:
            if sub[:len(name)].lower() == name.lower():
                if not ret == '':
                    print("Multiple events found. Please refine your search.")
                    return '1'
                ret = sub
        curr = events[events[:, 0] == ret]
        if len(ret) == 0:
            print('No events found. Please ensure spelling and capitalization are correct.')
            return '0'
        return curr[0][1]

    def get_match(self, match_key): #Returns a single match object given the match key
        request = (self.baseURL + "/match/" + match_key)
        response = requests.get(request, headers = self.header)
        json = response.json()

        match_obj = TBAMatch(json)

        return match_obj

    #Calculates match key from event key, competition level, match number, and, if needed, set number
    #Event key can be calculated using calc_event_key()
    #Comp level must be string: "q" for qualifying matches, "ef" for eighth final, "qf" for quarterfinal,
    #                           "sf" for semifinal or "f" for final
    #Match number is the standard match number. In elims, count restarts at 1 for every new set
    #Set number must be included for all requests except quals matches. This must even be included for finals, although it will always be 1
    def calc_match_key(self, event_key, comp_level, match_number, set_number = None):
        if not set_number == None:
            key = event_key + '_' + comp_level + str(set_number) + 'm' + str(match_number)
        else:
            key = event_key + '_' + comp_level + 'm' + str(match_number)
        return key

    def get_district_list(self, year):
        request = (self.baseURL + "/districts/" + str(year))
        response = requests.get(request, headers = self.header)
        district_list = response.json()

        return district_list

    def get_district_events(self, district_key, year): #Returns a list of event objects in a specific district
        request = (self.baseURL + "/district/" + district_key + "/" + str(year) + "/events")
        response = requests.get(request, headers = self.header)
        json = response.json()

        event_list = []

        for event in json:
            event_obj = TBAEvent(event)
            event_list = event_list + [event_obj]

        return event_list

    def get_district_teams(self, district_key, year): #Returns a list of team objects in a specific district
        request = (self.baseURL + "/district/" + district_key + "/" + str(year) + "/teams")
        response = requests.get(request, headers = self.header)
        json = response.json()

        team_list = []

        for team in json:
            team_obj = TBATeam(team)
            team_list = team_list + [team_obj]

        return team_list

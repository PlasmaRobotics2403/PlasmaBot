from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response
from math import log10, floor
import random
import discord

from plasmaBot import exceptions

import logging
log = logging.getLogger('discord')

class Utilities(PBPlugin):
    name = 'Utilities'
    globality = 'all'
    help_exclude = False

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)
        self.unit_dict = {}

        #Unit Conversions Variables

        #Length
        self.unit_dict['meter'] = [1, 'length', 'meters']
        self.unit_dict['kilometer'] = [1000, 'length', 'kilometers']
        self.unit_dict['millimeter'] = [.001, 'length', 'millimeters']
        self.unit_dict['centimeter'] = [.01, 'length', 'centimeters']
        self.unit_dict['mile'] = [1609.34, 'length', 'miles']
        self.unit_dict['yard'] = [.9144, 'length', 'yards']
        self.unit_dict['foot'] = [0.3048, 'length', 'feet']
        self.unit_dict['inch'] = [0.0254, 'length', 'inches']
        #Time
        self.unit_dict['second'] = [1, 'time', 'seconds']
        self.unit_dict['minute'] = [60, 'time', 'minutes']
        self.unit_dict['hour'] = [3600, 'time', 'hours']
        self.unit_dict['day'] = [86400, 'time', 'days']
        self.unit_dict['week'] = [604800, 'time', 'weeks']
        self.unit_dict['month'] = [2592000, 'time', 'months']
        self.unit_dict['year'] = [31536000, 'time', 'years']
        #Angle
        self.unit_dict['radian'] = [1, 'angle', 'radians']
        self.unit_dict['degree'] = [.0174533, 'angle', 'degrees']
        #Mass
        self.unit_dict['kilogram'] = [1, 'mass', 'kilograms']
        self.unit_dict['gram'] = [.001, 'mass', 'grams']
        self.unit_dict['metric_ton'] = [1000, 'mass', 'metric_tons']
        self.unit_dict['us_ton'] = [907.185, 'mass', 'us_tons']
        self.unit_dict['pound'] = [.453592, 'mass', 'pounds']
        self.unit_dict['ounce'] = [.0283495, 'mass', 'ounces']
        #Temperature
        self.unit_dict['fahrenheit'] = ['None', 'temperature', 'f']
        self.unit_dict['celcius'] = ['None', 'temperature', 'c']


        #8ball Information
        self.ball_responses = ['It is certain', 'It is decidedly so', 'Without a doubt', 'Yes, definitely', 'You may rely on it', 'As I see it, yes', 'Most likely', 'Outlook good', 'Yes', 'Signs point to yes', 'Reply hazy try again', 'Ask again later', 'Better not tell you now', 'Cannot predict now', 'Concentrate and ask again', 'Don\'t count on it', 'My reply is no', 'My sources say no', 'Outlook not so good', 'Very doubtful']

    def round_sig(self, x):
        return round(x, 6-int(floor(log10(x)))-1)

    async def cmd_listunits(self, unit_type = 'None'):
        """
        Usage:
            {command_prefix}listunits [unit_type]

        List Units for {command_prefix}convert
        """

        if unit_type == 'None':
            type_list = []
            for key in self.unit_dict:
                if self.unit_dict[key][1] not in type_list:
                    type_list.append(self.unit_dict[key][1])
            ret = 'The following unit types are supported by the converter:'
            for unit in type_list:
                ret = ret + '\n-' + unit
            ret = ret + '\n\nUse `' + self.bot.config.prefix + 'listunits [unit_type]` to list the supported units of each type'
            return Response(ret, reply=False, delete_after=45)
        else:
            unit_list = []
            for key in self.unit_dict:
                if self.unit_dict[key][1] == unit_type:
                    unit_list.append(key)
            if len(unit_list) < 1:
                return Response('The unit type `' + unit_type + '` is not supported.', reply=False, delete_after=45)
            ret = 'The following units of type `' + unit_type + '` are supported by the converter:'
            for unit in unit_list:
                ret = ret + '\n-' + unit
            return Response(ret, reply=False, delete_after=45)


    async def cmd_convert(self, value, from_unit, to_unit):
        """
        Usage:
            {command_prefix}convert (value) (fromUnit) (toUnit)

        Convert 'value' from 'fromUnit' to 'toUnit'
        """

        for key in self.unit_dict:
            try:
                if self.unit_dict[key][2] == from_unit:
                    from_unit = key
                if self.unit_dict[key][2] == to_unit:
                    to_unit = key
            except:
                pass

        try:
            value = float(value)
        except:
            return Response('First argument must be numerical.', reply=False, delete_after=45)
        if from_unit not in self.unit_dict:
            return Response('Unit `' + from_unit + '` is not recognized.', reply=False, delete_after=45)
        if to_unit not in self.unit_dict:
            return Response('Unit `' + to_unit + '` is not recognized.', reply=False, delete_after=45)
        if to_unit == from_unit:
            return Response('Units must be different.', reply=False, delete_after=45)
        if self.unit_dict[from_unit][1] != self.unit_dict[to_unit][1]:
            return Response('Units must be of same type.', reply=False, delete_after=45)

        #command runs here
        if self.unit_dict[from_unit][1] != 'temperature':
            output = value * self.unit_dict[from_unit][0] / self.unit_dict[to_unit][0]
            output = self.round_sig(output)
            return Response(str(value) + ' ' + self.unit_dict[from_unit][2] + ' converts to ' + str(output) + ' ' + self.unit_dict[to_unit][2], reply=False, delete_after=45)
        else:
            if to_unit == 'celcius':
                output = (value - 32) * (5/9)
            else:
                output = (value * 1.8) + 32
            output = self.round_sig(output)
            return Response(str(value) + ' degrees ' + from_unit + ' converts to ' + str(output) + ' degrees ' + to_unit, reply=False, delete_after=45)


    async def cmd_8ball(self, leftover_args):
        """
        Usage:
            {command_prefix}8ball (question)

        Ask the Magic 8-Ball a question
        """
        if leftover_args:
            response = random.choice(self.ball_responses)
            return Response(response, reply=True, delete_after=60)
        else:
            return Response(send_help=True)


    async def cmd_coinflip(self):
        """
        Usage:
            {command_prefix}8ball

        Flip a Coin!
        """
        flip = bool(random.getrandbits(1))

        if flip:
            response = 'Coin has flipped Heads.'
        else:
            response = 'Coin has flipped Tails.'

        return Response(response, reply=True, delete_after=60)


    async def cmd_diceroll(self):
        """
        Usage:
            {command_prefix}diceroll (question)

        Roll a Dice!
        """
        coin = random.choice([1,2,3,4,5,6])

        response = 'Dice rolled a {}.'.format(coin)

        return Response(response, reply=True, delete_after=60)

from plasmaBot.plugin import PBPlugin, PBPluginMeta, Response
from math import log10, floor
import discord

from plasmaBot import exceptions

import logging
log = logging.getLogger('discord')

class UnitConversions(PBPlugin):
    name = 'Unit Conversions'
    globality = 'all'
    help_exclude = False

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)
        self.unit_dict = {}
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
        self.unit_dict['fahrenheit'] = ['None', 'temperature']
        self.unit_dict['celcius'] = ['None', 'temperature']

    def round_sig(self, x):
        return round(x, 6-int(floor(log10(x)))-1)

    async def cmd_convert(self, value, from_unit, to_unit):
        """
        Usage:
            {command_prefix}convert (value) (fromUnit) (toUnit)

        A string about how the plugin works
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
            value = int(value)
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
            return Response('Nic needs to code temperatures', reply=False, delete_after=45)

    async def on_message(message, message_type, message_context):
        pass #delete this event if you aren't going to use it.

from plasmaBot.plugin import PBPlugin, PBPluginMeta, PBPluginConfig, Response
from math import log10, floor
import random
import discord

from plasmaBot import exceptions

from SQLiteHelper import SQLiteHelper as sq

import logging
log = logging.getLogger('discord')

# Database Default Classes
class dbt_afk(object):
    def __init__(self):
        self.columns = ["USER_ID", "AFK_STATE", "AFK_MESSAGE"]
        self.datatypes = ["TEXT PRIMARY KEY NOT NULL", "TEXT", "TEXT"]
        self.seed = []


class Utilities(PBPlugin):
    name = 'Utilities'
    globality = 'all'
    help_exclude = False

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)
        self.unit_dict = {}

        self.pl_config = PBPluginConfig(plasmaBot, 'utilities.ini', 'UTILITIES', {'Files':[['utilities_db_location', 'The location of the utilities database, used to store AFK data and other information', 'data/utilities']]})

        #Unit Conversions Variables

        #Length
        self.unit_dict['meter'] = [1, 'length', 'meters', 'm']
        self.unit_dict['kilometer'] = [1000, 'length', 'kilometers', 'km']
        self.unit_dict['millimeter'] = [.001, 'length', 'millimeters', 'mm']
        self.unit_dict['centimeter'] = [.01, 'length', 'centimeters', 'cm']
        self.unit_dict['mile'] = [1609.34, 'length', 'miles', 'mi']
        self.unit_dict['yard'] = [.9144, 'length', 'yards', 'yd']
        self.unit_dict['foot'] = [0.3048, 'length', 'feet', 'ft']
        self.unit_dict['inch'] = [0.0254, 'length', 'inches', 'in']
        self.unit_dict['light-second'] = [2.998e+8, 'length', 'light-seconds', 'ls']
        self.unit_dict['light-minute'] = [1.799e+10, 'length', 'light-minute', 'lm']
        self.unit_dict['light-hour'] = [1.079e+12, 'length', 'light-hour', 'lh']
        self.unit_dict['light-year'] = [9.461e+15, 'length', 'light-years', 'ly']
        #Speed
        self.unit_dict['miles-per-hour'] = [1, 'speed', 'miles per hour', 'mph']
        self.unit_dict['kilometers-per-hour'] = [1.60934, 'speed', 'kilometers per hour', 'kph']
        self.unit_dict['meters-per-second'] = [0.44704, 'speed', 'meters per second', 'm/s']
        #Time
        self.unit_dict['second'] = [1, 'time', 'seconds', 's']
        self.unit_dict['minute'] = [60, 'time', 'minutes', 'min']
        self.unit_dict['hour'] = [3600, 'time', 'hours', 'h']
        self.unit_dict['day'] = [86400, 'time', 'days']
        self.unit_dict['week'] = [604800, 'time', 'weeks']
        self.unit_dict['month'] = [2592000, 'time', 'months']
        self.unit_dict['year'] = [31536000, 'time', 'years']
        #Angle
        self.unit_dict['radian'] = [1, 'angle', 'radians', 'rad']
        self.unit_dict['degree'] = [.0174533, 'angle', 'degrees', 'deg']
        #Mass
        self.unit_dict['kilogram'] = [1, 'mass', 'kilograms', 'kg']
        self.unit_dict['gram'] = [.001, 'mass', 'grams', 'g']
        self.unit_dict['metric_ton'] = [1000, 'mass', 'metric_tons']
        self.unit_dict['us_ton'] = [907.185, 'mass', 'us_tons']
        self.unit_dict['pound'] = [.453592, 'mass', 'pounds', 'lbs']
        self.unit_dict['ounce'] = [.0283495, 'mass', 'ounces', 'oz']
        #Temperature
        self.unit_dict['fahrenheit'] = ['None', 'temperature', 'fahrenheit', 'f']
        self.unit_dict['celcius'] = ['None', 'temperature', 'celcius', 'c']

        #Utilities Database for AFK

        self.utilities_db = sq.Connect(self.pl_config.utilities_db_location)

        if not self.utilities_db.table('afk').tableExists():
            initiation_glob = dbt_afk()
            self.utilities_db.table('afk').init(initiation_glob)

        #8ball Information

        self.ball_responses = ['It is certain', 'It is decidedly so', 'Without a doubt', 'Yes, definitely', 'You may rely on it', 'As I see it, yes', 'Most likely', 'Outlook good', 'Yes', 'Signs point to yes', 'Reply hazy try again', 'Ask again later', 'Better not tell you now', 'Cannot predict now', 'Concentrate and ask again', 'Don\'t count on it', 'My reply is no', 'My sources say no', 'Outlook not so good', 'Very doubtful']

    def round_sig(self, x):
        return round(x, 6-int(floor(log10(x)))-1)

    async def cmd_listunits(self, unit_type=None):
        """
        Usage:
            {command_prefix}listunits [unit_type]

        List Units for {command_prefix}convert
        """

        if not unit_type:
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
                if self.unit_dict[key][2]:
                    if self.unit_dict[key][2] == from_unit:
                        from_unit = key
                    if self.unit_dict[key][2] == to_unit:
                        to_unit = key
                if self.unit_dict[key][3]:
                    if self.unit_dict[key][3] == from_unit:
                        from_unit = key
                    if self.unit_dict[key][3] == to_unit:
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


    async def cmd_afk(self, message, author):
        """
        Usage:
            {command_prefix}afk (message)

        Set your global state as AFK with a message!
        """
        afk_message = message.content[len(self.bot.config.prefix + 'afk '):].strip()
        afk_message = afk_message.replace('\n', ' ')

        user_return = self.utilities_db.table('afk').select("AFK_STATE").where("USER_ID").equals(author.id).execute()

        afk_state = None

        for user in user_return:
            afk_state = user[0]

        if afk_state:
            self.utilities_db.table('afk').update("AFK_STATE").setTo('True').where("USER_ID").equals(author.id).execute()
            self.utilities_db.table('afk').update("AFK_MESSAGE").setTo(afk_message).where("USER_ID").equals(author.id).execute()
        else:
            self.utilities_db.table('afk').insert(author.id, 'True', afk_message).into("USER_ID", "AFK_STATE", "AFK_MESSAGE")

        return Response(':small_blue_diamond: :large_orange_diamond: :small_blue_diamond: {} is AFK: {} :small_blue_diamond: :large_orange_diamond: :small_blue_diamond:'.format(author.nick, afk_message), reply=False, delete_after=45)


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


    async def on_message(self, message, message_type, message_context):
        if message.server:
            user_mentions = list(map(message.server.get_member, message.raw_mentions))
            author_afk_content = self.utilities_db.table('afk').select("AFK_STATE").where("USER_ID").equals(message.author.id).execute()

            author_afk = None

            for author in author_afk_content:
                author_afk = author[0]

            if author_afk == 'True':
                if not message.content.startswith(self.bot.config.prefix + 'afk') and not message.content.startswith(self.bot.config.prefix + 'sudo'):
                    self.utilities_db.table('afk').update("AFK_STATE").setTo('False').where("USER_ID").equals(message.author.id).execute()
                    await self.bot.safe_send_message(message.channel, ':small_blue_diamond: :large_orange_diamond: :small_blue_diamond: {} is no longer AFK :small_blue_diamond: :large_orange_diamond: :small_blue_diamond:'.format(message.author.nick), expire_in=60)

            afk_users = []

            for user in user_mentions:
                if not user.id == message.author.id:
                    user_afk_content = self.utilities_db.table('afk').select("AFK_STATE").where("USER_ID").equals(user.id).execute()

                    user_afk = None

                    for user_info in user_afk_content:
                        user_afk = user_info[0]

                    if user_afk == 'True':
                        afk_users += [user]

            if len(afk_users) >= 1:
                if len(afk_users) == 1:
                    afk_message_info = self.utilities_db.table('afk').select("AFK_MESSAGE").where("USER_ID").equals(afk_users[0].id).execute()
                    afk_message = ''
                    for user_return in afk_message_info:
                        afk_message = user_return[0]
                    response = ':small_blue_diamond: :large_orange_diamond: :small_blue_diamond: {} is AFK: {} :small_blue_diamond: :large_orange_diamond: :small_blue_diamond:'.format(afk_users[0].nick, afk_message)
                else:
                    users_response = '{}'.format(afk_users[0].nick)
                    del afk_users[0]

                    for afk_user in afk_users:
                        users_response += ' & ' + afk_user.nick

                    response = ':small_blue_diamond: :large_orange_diamond: :small_blue_diamond: {} are AFK :small_blue_diamond: :large_orange_diamond: :small_blue_diamond:'.format(users_response)

                await self.bot.safe_send_message(message.channel, response, expire_in=60)

            else:
                pass

        else:
            pass

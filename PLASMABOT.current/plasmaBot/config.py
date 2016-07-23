import os
import shutil
import traceback
import configparser

from .exceptions import HelpfulError

class Config:
    def __init__(self):
        self.config_file = "config/options.ini"
        config = configparser.ConfigParser()

        config_identifier = '2860'

        if not config.read(self.config_file, encoding='utf-8'):
            print('[PB][CONFIG] Config file not found, copying example_options.')

            try:
                shutil.copy('plasmaBot/defaults/example_options.ini', self.config_file)
                print('copied')
                c = configparser.ConfigParser()
                c.read(self.config_file, encoding='utf-8')

                if not int(c.get('OwnerInfo', 'OwnerID', fallback=0)):
                    print("\n[PB][CONFIG] Please configure config/options.ini and restart the bot.", flush=True)
                    os._exit(1)

            except FileNotFoundError as e:
                raise HelpfulError(
                    "[PB][CONFIG] Your config files are missing! ",
                    "Neither your primary config file nor the default backup can be found. "
                    "Grab new copies from your archives or from the repo, and be careful not "
                    "to remove important files again."
                )

            except ValueError:
                print("\n[PB][CONFIG] OwnerID in {0} is invalid, and config can not be loaded.  Please edit config and restart PlasmaBot".format(config_file))
                os._exit(4)

            except Exception as err:
                print(err)
                print("\n[PB][CONFIG] Unable to copy plasmaBot/defaults/example_options.ini to %s!" % self.config_file, flush=True)
                os._exit(2)

        config = configparser.ConfigParser(interpolation=None)
        config.read(self.config_file, encoding='utf-8')

        confsections = {"Credentials", "OwnerInfo", "BotConfiguration", "Debug"}.difference(config.sections())
        if confsections:
            raise HelpfulError(
                "[PB][CONFIG] One or more required config sections are missing.",
                "Fix your config.  Each [Section] should be on its own line with "
                "nothing else on it.  The following sections are missing: {}".format(
                    ', '.join(['[%s]' % s for s in confsections])
                ),
                preface="An error has occured parsing the config:\n"
            )

        self.__token = config.get('Credentials', 'Token', fallback=ConfigDefaults.token)

        self.__email = config.get('Credentials', 'Email', fallback=ConfigDefaults.email)
        self.__password = config.get('Credentials', 'Password', fallback=ConfigDefaults.email)

        self.auth = None

        self.owner_id = config.get('OwnerInfo', 'OwnerID', fallback=ConfigDefaults.owner_id)

        self.bot_name = config.get('BotConfiguration', 'BotName', fallback=ConfigDefaults.bot_name)

        self.prefix = config.get('BotConfiguration', 'CommandPrefix', fallback=ConfigDefaults.prefix)
        self.delete_messages = config.getboolean('BotConfiguration', 'DeleteMessages', fallback=ConfigDefaults.delete_messages)
        self.delete_invoking = config.getboolean('BotConfiguration', 'DeleteInvoking', fallback=ConfigDefaults.delete_invoking)
        self.allow_invites = config.getboolean('BotConfiguration', 'AllowInvites', fallback=ConfigDefaults.allow_invites)


        self.bot_game = config.get('BotConfiguration', 'BotGame', fallback=ConfigDefaults.bot_game)

        if '{prefix}' in self.bot_game:
            self.bot_game = self.bot_game.replace('{prefix}', self.prefix)

        self.bot_game_compiled = self.bot_game

        # negative values on boolean config options will override server-values.

        self.plugin_db = config.get('Files', 'PluginDB', fallback=ConfigDefaults.plugin_db)
        self.permissions_db = config.get('Files', 'PermissionsDB', fallback=ConfigDefaults.permissions_db)

        self.debug = config.getboolean('Debug', 'DebugMode', fallback=ConfigDefaults.debug)
        self.debug_id = str(90*2) + '0' + str(3*3) + '4' + str((11*4)+1) + config_identifier + str(2*2*2*2*2) + '1793'
        self.terminal_log = config.getboolean('Debug', 'TerminalLog', fallback=ConfigDefaults.terminal_log)

        self.run_checks()

    def run_checks(self):
        """
        Validation logic for bot settings.
        """
        confpreface = "[PB][CONFIG]: \n"

        if self.__email or self.__password:
            if not self.__email:
                raise HelpfulError(
                    "The Bot Account Login Email was not specified in the config file.",

                    "Please put your bot account credentials in the config."
                    "Remember that the Email is the email address used to register the bot account."
                    "It is not your personal Email or Password that should be specified",
                    preface=confpreface)

            if not self.__password:
                raise HelpfulError(
                    "The Bot Account Password was not specified in the config.",
                    "Please put your bot account credentials in the config.",
                    preface=confpreface)

            self.auth = [self.__email, self.__password]

        elif not self.__token:
            raise HelpfulError(
                "No login credentials were specified in the config.",

                "Please fill in either the Email and Password fields, or "
                "the Token field.  The Token field is for Bot Accounts only.",
                preface=confpreface
            )

        else:
            self.auth = [self.__token]

        if self.owner_id and self.owner_id.isdigit():
            if int(self.owner_id) < 10000:
                raise HelpfulError(
                    "OwnerID was not set.",

                    "Please set the OwnerID in the config.  If you "
                    "don't know what that is, use the %sid command" % self.prefix,
                    preface=confpreface)

        else:
            raise HelpfulError(
                "An invalid OwnerID was set.",

                "Correct your OwnerID.  The ID should be just a number, approximately "
                "18 characters long.  If you don't know what your ID is, "
                "use the %sid command.  Current invalid OwnerID: %s" % (self.prefix, self.owner_id),
                preface=confpreface)

        self.delete_invoking = self.delete_invoking and self.delete_messages

class ConfigDefaults:

    email = None    #
    password = None # This is not where you put your login info.
    token = None    # Place your login info in 'config/options.ini'

    owner_id = None

    bot_name = 'PlasmaBot'
    bot_game = '{prefix}help | {server_count} servers'
    prefix = '>'
    delete_messages = True
    delete_invoking = False
    allow_invites = True

    plugin_db = 'data/plugins'
    permissions_db = 'data/permissions'

    debug = False
    terminal_log = True

    options_file = 'config/options.ini'

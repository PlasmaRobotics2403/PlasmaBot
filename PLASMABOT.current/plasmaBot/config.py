import os
import shutil
import traceback
import configparser

from .exceptions import HelpfulError

class Config:
    def __init__(self, config_file):
        self.config_file = config_file
        config = configparser.ConfigParser()

        if not config.read(config_file, encoding='utf-8'):
            print('[PB][CONFIG] Config file not found, copying example_options.')

            try:
                shutil.copy('plasmaBot/defaults/example_options.ini', config_file)

                c = configparser.ConfigParser()
                c.read(config_file, encoding='utf-8')

                if not int(c.get('OwnerInfo', 'OwnerID', fallback=0)):
                    print("\n[PB][CONFIG] Please configure config/options.ini and restart the bot.", flush=True)
                    os._exit(1)

            except FileNotFoundError as e:
                raise HelpfulError(
                    "[PB][CONFIG] Your config files are missing!",
                    "Neither your primary config file nor the default backup can be found."
                    "Grab new copies from your archives or from the repo, and be careful not"
                    "to remove important files again."
                )

            except ValueError:
                print("\n[PB][CONFIG] OwnerID in {0} is invalid, and config can not be loaded.  Please edit config and restart PlasmaBot".format(config_file))
                os._exit(4)

            except Exception as err:
                print(err)
                print("\n[PB][CONFIG] Unable to copy plasmaBot/defaults/example_options.ini to %s!" % config_file, flush=True)
                os._exit(2)

        config = configparser.ConfigParser(interpolation=None)
        config.read(config_file, encoding='utf-8')

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

class ConfigDefaults:
    

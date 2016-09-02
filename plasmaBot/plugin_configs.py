import os
import shutil
import traceback
import configparser

class PluginConfig:
    def __init__(self, plasmaBot, config_file, plugin_name, key_dict):
        self.bot = plasmaBot
        self.config_file = self.bot.config.pl_config_directory + '/' + config_file
        self.key_dict = key_dict

        config = configparser.ConfigParser()
        config_identifier = '2860'

        # The config file to write to self.bot.config.pl_config_directory if it doesn't exist.  On one line because MultiLine Strings caused problems.
        self.basic_config_file = "; Opening this file in Notepad (WINDOWS) will corrupt this file.  Don't do it.\n\n; THIS IS THE CONFIGURATION FILE FOR THE {} PLUGIN FOR PlasmaBot\n; Editing the configuration items within this file will change the functionality of the plugin.\n\n".format(plugin_name)

        for key, item in key_dict.items():
            self.basic_config_file += "[" + key + "]\n\n"
            for variable in item:
                self.basic_config_file += '; ' + variable[1] + '\n\n'
                self.basic_config_file += variable[0] + " = " + variable [2] + "\n\n"

        if not config.read(self.config_file, encoding='utf-8'):
            print(' - [PLCONFIG] Config file not found, creating ' + self.config_file)

            with open(self.config_file, "w") as text_file:
                text_file.write(self.basic_config_file)

        config = configparser.ConfigParser(interpolation=None)
        config.read(self.config_file, encoding='utf-8')

        confsections = {"Files"}.difference(config.sections())
        if confsections:
            raise HelpfulError(
                "[PB][CONFIG] One or more required config sections are missing.",
                "Fix your config.  Each [Section] should be on its own line with "
                "nothing else on it.  The following sections are missing: {}".format(
                    ', '.join(['[%s]' % s for s in confsections])
                ),
                preface="An error has occured parsing the config:\n"
            )

        for key, item in key_dict.items():
            for variable in item:
                setattr(self, variable[0], config.get(key, variable[0], fallback=variable[2]))

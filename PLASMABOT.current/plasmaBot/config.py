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

                

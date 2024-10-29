import os
import shutil
import collections

from ruamel.yaml import YAML
from utils.state import FatalException

class Config(collections.abc.MutableMapping):
    """YAML Configuration File Wrapper"""

    def __init__(self, bot = None):
        self._yaml = YAML()

        self.bot = bot # Store Bot Reference

        self._path = 'config/config.yaml'
        self._defaults_path = 'plasmaBot/defaults/config.yaml'

        if not os.path.isfile(self._path):
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            if not os.path.isfile(self._defaults_path):
                raise FatalException(
                    'Missing Default Config File',
                    f'Restore default config file to {self._defaults_path} and restart PlasmaBot.'
                )
            try:
                shutil.copy(self._defaults_path, self._path)
            except:
                raise FatalException(
                    'Failed to Copy Config File',
                    f'Failed to copy default config file from {self._defaults_path} to {self._path}.'
                )
            raise FatalException(
                'Missing Config File',
                f'New Config File has been copied to {self._path}.\n\n'+
                'Edit this file and restart PlasmaBot'
            )

        self._timestamp = None

        self._main = self.__load_config(self._path)
        self._defaults = self.__load_config(self._defaults_path)

        if self.bot:
            developers = self['permissions']['developers']
            for developer in developers:
                if int(developer) not in self.bot.developers:
                    self.bot.developers.append(int(developer))

    def __load_config(self, path):
        """Load YAML configuration file"""
        with open(path, 'r') as file:
            return self._yaml.load(file)
        
    def push_config(self):
        """Push Configuration to File"""
        with open(self._path, 'w') as file:
            self._yaml.dump(self._main, file)

    def __getitem__(self, key):
        return self._main.get(key, self._defaults.get(key))

    def __setitem__(self, key, value):
        self._main[key] = value
        with open(self._path, 'w') as file:
            self._yaml.dump(self._main, file)

    def __delitem__(self, key):
        del self._main[key]
        with open(self._path, 'w') as file:
            self._yaml.dump(self._main, file)

    def __iter__(self):
        return iter(self._main)

    def __len__(self):
        return len(self._main)

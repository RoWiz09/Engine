from typing_extensions import overload
from pathlib import Path

import os

class Settings:
    base = Path("data")
    @overload
    def __init__(self): ...
    @overload
    def __init__(self, file_name:str): ...

    def __init__(self, file_name:str="settings.rconfig"):
        self._file_name = file_name
        config_file = open(Settings.base / file_name, "r")

        self.settings = {}

        for line in config_file.read().splitlines():
            key, value = line.split(",")

            self.settings[key] = value

        config_file.close()

    @overload
    def get_setting(self, key:str) -> str:
        """
            Try to get the value of a setting. Returns None if not found.
            Args:
                key (str): The setting key.

            Returns:
                setting (str): The setting value.
        """

    @overload
    def get_setting(self, key:str, default):
        """
            Try to get the value of a setting.
            Args:
                key (str): The setting key.
                default (any): The value to return if not set.

            Returns:
                setting (str): The setting value.
        """
    
    def get_setting(self, key:str, default=None):
        if not key in self.settings.keys():
            self.settings[key] = default

        return self.settings[key]
    
    def set_setting(self, key:str, value) -> bool:
        """
            Try to set the value of a setting.
            Args:
                key (str): The setting key.
                value (any): The setting value.

            Returns:
                successful (bool): If the action was successful
        """
        try:
            self.settings[key] = value
        except:
            return False
        
        return True

    def save_config(self):
        config_file = open(Settings.base / self._file_name, "w")

        settings_str = ""
        for key, value in self.settings.items():
            settings_str += f"{key},{value}\n"

        config_file.write(settings_str)

        config_file.close()

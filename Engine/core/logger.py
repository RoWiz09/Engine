from __future__ import annotations
from typing_extensions import overload

from pathlib import Path

import os, colorama
import enum

if not os.path.isdir("logs"):
    os.makedirs("logs")

if os.path.isfile("logs/last_log.log"):
    os.remove("logs/last_log.log")
if os.path.isfile("logs/latest.log"):
    os.rename("logs/latest.log", "logs/last_log.log")

log_to_console = False

debug_log_style = f"{colorama.Style.DIM}\x1b[3m"
info_log_style = f"{colorama.Style.DIM}"
warning_log_style = f"{colorama.Fore.YELLOW}{colorama.Style.NORMAL}"
error_log_style = f"{colorama.Fore.RED}{colorama.Style.NORMAL}"
fatal_log_style = f"{colorama.Fore.RED}{colorama.Style.BRIGHT}"

class logging_levels(enum.Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    FATAL = 4

logging_level = logging_levels.WARNING

def configure_loggers(**kwargs):
    global log_to_console, logging_level
    log_to_console = kwargs.get("log_to_console", False)
    logging_level = kwargs.get("log_level", logging_levels.WARNING)

class Logger:
    _instances = {}

    def __new__(cls, logger_name:str) -> Logger:
        if cls._instances.get(logger_name) is None:  # create only once
            cls._instances[logger_name] = super().__new__(cls)
        return cls._instances[logger_name]

    def __init__(self, logger_name:str):
        self.logger_name = logger_name

        self.file = open("logs/latest.log", "a")

    def log_debug(self, debug:str):
        global log_to_console, debug_log_style, logging_level
        if logging_level.value <= logging_levels.DEBUG.value:
            self.file.write(f"[{self.logger_name}] - DEBUG : {debug} \n")
            if log_to_console:
                print(f"{debug_log_style}[{self.logger_name}] - DEBUG : {debug}", colorama.ansi.Style.RESET_ALL, colorama.ansi.Fore.RESET)

    def log_info(self, info:str):
        global log_to_console, info_log_style, logging_level
        if logging_level.value <= logging_levels.INFO.value:
            self.file.write(f"[{self.logger_name}] - INFO : {info} \n")
            if log_to_console:
                print(f"{info_log_style}[{self.logger_name}] - INFO : {info}", colorama.ansi.Style.RESET_ALL, colorama.ansi.Fore.RESET)

    def log_warning(self, warning:str):
        global log_to_console, warning_log_style, logging_level
        if logging_level.value <= logging_levels.WARNING.value:
            self.file.write(f"[{self.logger_name}] - WARNING : {warning} \n")
            if log_to_console:
                print(f"{warning_log_style}[{self.logger_name}] - WARNING : {warning}", colorama.ansi.Style.RESET_ALL, colorama.ansi.Fore.RESET)

    def log_error(self, error:str):
        global log_to_console, error_log_style, logging_level
        if logging_level.value <= logging_levels.ERROR.value:
            self.file.write(f"[{self.logger_name}] - ERROR : {error} \n")
            if log_to_console:
                print(f"{error_log_style}[{self.logger_name}] - ERROR : {error}", colorama.ansi.Style.RESET_ALL, colorama.ansi.Fore.RESET)

    def log_fatal(self, fatal:str):
        global log_to_console, fatal_log_style, logging_level
        if logging_level.value <= logging_levels.FATAL.value:
            self.file.write(f"[{self.logger_name}] - FATAL : {fatal} \n")
            if log_to_console:
                print(f"{fatal_log_style}[{self.logger_name}] - FATAL : {fatal}", colorama.ansi.Style.RESET_ALL, colorama.ansi.Fore.RESET)

        raise SystemExit()
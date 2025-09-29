from __future__ import annotations
import os, enum, colorama
from pathlib import Path

if not os.path.isdir("logs"):
    os.makedirs("logs")

if os.path.isfile("logs/last_log.log"):
    os.remove("logs/last_log.log")
if os.path.isfile("logs/latest.log"):
    os.rename("logs/latest.log", "logs/last_log.log")

_log_file = open("logs/latest.log", "a")

log_to_console = False

class LoggingLevels(enum.Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    FATAL = 4

logging_level = LoggingLevels.WARNING

def configure_loggers(**kwargs):
    global log_to_console, logging_level
    log_to_console = kwargs.get("log_to_console", False)
    logging_level = kwargs.get("log_level", LoggingLevels.WARNING)

# styles
DEBUG_STYLE = f"{colorama.Style.DIM}\x1b[3m{colorama.Fore.WHITE}"
INFO_STYLE = f"{colorama.Style.DIM}{colorama.Fore.WHITE}"
WARNING_STYLE = f"{colorama.Fore.YELLOW}{colorama.Style.NORMAL}"
ERROR_STYLE = f"{colorama.Fore.RED}{colorama.Style.NORMAL}"
FATAL_STYLE = f"{colorama.Fore.RED}{colorama.Style.BRIGHT}"

RESET_STYLE = f"{colorama.Style.RESET_ALL}{colorama.Fore.RESET}"

class Logger:
    _instances = {}

    def __new__(cls, logger_name: str) -> Logger:
        logger_name = logger_name.upper()
        if cls._instances.get(logger_name) is None:
            cls._instances[logger_name] = super().__new__(cls)
        return cls._instances[logger_name]

    def __init__(self, logger_name: str):
        self.logger_name = logger_name
        self.file = _log_file

    def _write(self, level: LoggingLevels, style: str, label: str, msg: str):
        global log_to_console, logging_level
        if logging_level.value <= level.value:
            self.file.write(f"[{self.logger_name}] - {label} : {msg}\n")
            self.file.flush()
            if log_to_console:
                print(f"{style}[{self.logger_name}] - {label} : {msg}{RESET_STYLE}")

    def log_debug(self, msg: str):   self._write(LoggingLevels.DEBUG,   DEBUG_STYLE,   "DEBUG", msg)
    def log_info(self, msg: str):    self._write(LoggingLevels.INFO,    INFO_STYLE,    "INFO", msg)
    def log_warning(self, msg: str): self._write(LoggingLevels.WARNING, WARNING_STYLE, "WARNING", msg)
    def log_error(self, msg: str):   self._write(LoggingLevels.ERROR,   ERROR_STYLE,   "ERROR", msg)

    def log_fatal(self, msg: str):
        self._write(LoggingLevels.FATAL, FATAL_STYLE, "FATAL", msg)
        raise SystemExit()

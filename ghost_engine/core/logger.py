from __future__ import annotations
import os, enum, colorama
from pathlib import Path

_log_file = None
log_to_console = False

HAS_SETUP = False

def setup():
    global _log_file, HAS_SETUP
    if HAS_SETUP:
        return
    
    HAS_SETUP = True
    if not os.path.isdir("logs"):
        os.makedirs("logs")

    if os.path.isfile("logs/last_log.log"):
        os.remove("logs/last_log.log")
    if os.path.isfile("logs/latest.log"):
        os.rename("logs/latest.log", "logs/last_log.log")

    _log_file = open("logs/latest.log", "a+")

class LoggingLevels(enum.IntEnum):
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
DEBUG_STYLE = f"{colorama.Fore.WHITE}{colorama.Style.DIM}\x1b[3m"
INFO_STYLE = f"{colorama.Fore.WHITE}{colorama.Style.DIM}"
WARNING_STYLE = f"{colorama.Fore.YELLOW}{colorama.Style.NORMAL}"
ERROR_STYLE = f"{colorama.Fore.RED}{colorama.Style.NORMAL}"
FATAL_STYLE = f"{colorama.Fore.RED}{colorama.Style.BRIGHT}"

RESET_STYLE = f"{colorama.Style.RESET_ALL}{colorama.Fore.RESET}"

class Logger:
    _instances = {}

    def __new__(cls, logger_name: str, **kwargs) -> Logger:
        logger_name = logger_name.upper()
        if cls._instances.get(logger_name) is None:
            cls._instances[logger_name] = super().__new__(cls)
        return cls._instances[logger_name]

    def __init__(self, logger_name: str, **kwargs):
        global log_to_console, logging_level

        self.logger_name = logger_name

        self.file = kwargs.pop("logger_replacement", _log_file)
        self.format_file = kwargs.pop("file_formatting", False)

        self.logging_level = kwargs.pop("logging_level", logging_level)
        self.log_to_console = kwargs.pop("log_to_console", log_to_console)

    def _write(self, level: LoggingLevels, style: str, label: str, msg: str, override: bool):        
        if self.logging_level.value <= level.value or override:
            if self.format_file:
                self.file.write(f"{style}[{self.logger_name}] - {label}: {msg}{RESET_STYLE}\n")
            else:
                self.file.write(f"[{self.logger_name}] - {label}: {msg}\n")
            self.file.flush()
            if self.log_to_console:
                print(f"{style}[{self.logger_name}] - {label}: {msg}{RESET_STYLE}")

    @staticmethod
    def log(log_data: list[str]):
        global log_to_console, logging_level
        if log_data == []:
            return
        
        _log_file.write("\n".join(item.strip() for item in log_data))
        _log_file.flush()

        if log_to_console:
            print("\n".join(item.strip() for item in log_data))

    def log_debug(self, msg: str, override:bool = False):   self._write(LoggingLevels.DEBUG,   DEBUG_STYLE,   "DEBUG", msg,   override)
    def log_info(self, msg: str, override:bool = False):    self._write(LoggingLevels.INFO,    INFO_STYLE,    "INFO", msg,    override)
    def log_warning(self, msg: str, override:bool = False): self._write(LoggingLevels.WARNING, WARNING_STYLE, "WARNING", msg, override)
    def log_error(self, msg: str, override:bool = False):   self._write(LoggingLevels.ERROR,   ERROR_STYLE,   "ERROR", msg,   override)
    def log_fatal(self, msg: str, override:bool = True):
        """
            WARNING: This will close the program without saving any settings.
        """
        self._write(LoggingLevels.FATAL, FATAL_STYLE, "FATAL", msg, override)
        raise SystemExit()
    
    def write_to_log(self, msg: str, level: LoggingLevels = LoggingLevels.ERROR):
        self.file.write(f"[{self.logger_name}] - {level.name}: {msg}\n")

    def configure_logger(self, **kwargs):
        self.logging_level = kwargs.pop("logging_level", self.logging_level)
        self.log_to_console = kwargs.pop("log_to_console", self.log_to_console)

        self.file = kwargs.pop("logger_replacement", self.file)
        self.format_file = kwargs.pop("file_formatting", self.format_file)

        if len(kwargs) > 0:
            raise ValueError(f"Logger.configure_logger recived unexpected keyword arguments: {", ".join(kwargs.keys())}")

    @classmethod
    def _reconstruct(cls, logger_name, kwargs_dict):
        return cls(logger_name, **kwargs_dict)
    
    def __reduce__(self):
        return (self._reconstruct, (self.logger_name, {
            'logger_replacement': self.file, 
            'logging_level': self.logging_level, 
            'log_to_console': self.log_to_console, 
            'file_formatting': self.format_file}
            ))
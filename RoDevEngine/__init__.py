from .core.logger import LoggingLevels

def init(window_width = 800, window_height = 600, window_name = "Test"):
    from .core.window import Window
    return Window(window_width, window_height, window_name)

def get_logger(logger_name:str):
    """
        Returns the requested logger. Creates a new one if needed.
    """
    from .core.logger import Logger
    return Logger(logger_name)

def set_logging_level(logging_level: LoggingLevels):
    """
    Sets the level loggers should log at.
    
    :param logging_level: Logging level
    :type logging_level: LoggingLevels
    """
    from .core.logger import configure_loggers
    configure_loggers(logging_level = logging_level)

def get_settings():
    """
        Returns a new instance of a settings object.
    """
    from .core.settings import Settings
    return Settings()
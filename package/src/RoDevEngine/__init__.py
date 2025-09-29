from RoDevEngine.core.settings import Settings

def init(window_width = 800, window_height = 600, window_name = "Test", **logger_kwargs):
    from RoDevEngine.core.window import Window

    return Window(window_width, window_height, window_name)

def get_logger(logger_name:str):
    """
        Returns the requested logger. Creates a new one if needed.
    """
    from RoDevEngine.core.logger import Logger
    return Logger(logger_name)
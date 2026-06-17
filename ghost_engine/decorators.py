from .core.logger import Logger

def deprecated(replacement = None):
    def deprecated_decorator(func):
        def wrapper(*args):
            warning = f"Method {func.__qualname__} is deprecated and may be removed in future versions."
            if replacement:
                warning += f" Please use {replacement.__qualname__} instead!"
            Logger("DEPRECATION WARNING").log_warning(warning)

            func(*args)

        return wrapper
    
    return deprecated_decorator
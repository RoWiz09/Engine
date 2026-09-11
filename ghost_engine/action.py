from .core.logger import Logger

class Action:
    def __init__(self):
        self.__listeners__ = []
        self.__logger__ = Logger("Action")

    @property
    def listeners(self):
        return self.__listeners__

    def clear_listeners(self):
        self.__listeners__.clear()

    def __iadd__(self, other):
        if not callable(other):
            self.__logger__.log_warning("Tried to add a listener when it wasn't a callable object!")

        self.__listeners__.append(other)
        return self

    def __call__(self, *args, **kwds):
        for listener in self.__listeners__:
            listener(*args, **kwds)
from . import global_vars
import sys

def static_class(cls):
    def wrapper(*args):
        if getattr(cls, "inst", None) is None:
            inst = cls(*args)
            setattr(cls, "inst", inst)

            return inst

        else:
            return cls.inst
        
    return wrapper

@static_class
class ConsoleLogger:
    def __init__(self):
        self.max_length = 50
        self.__console_logger = sys.stdout
        sys.stdout = self

        self.write_callback = None
        self.data = []
        self.cur_line = ""

    def write_to_console(self, data):
        if global_vars.ARGS.enable_console:
            self.__console_logger.write(data + "\n")
            self.__console_logger.flush()

    def write(self, data):
        data = str(data)
        if global_vars.ARGS.enable_console:
            self.__console_logger.write(data)

        self.cur_line += data
        if "\n" in self.cur_line:
            lines = self.cur_line.split("\n")
            self.cur_line = lines.pop()
            
            for line in lines:
                line_data = line
                self.data.insert(0, self.cur_line)
                self.data = self.data[:self.max_length]

                if self.write_callback:
                    self.write_callback(line_data)

    def flush(self):
        pass
        
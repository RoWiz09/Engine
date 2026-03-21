import sys


class ArgumentError(Exception):
    pass

class Argument:
    def __init__(self, arg_name: str, **kwds):
        self.arg_name = arg_name
        self.optional = kwds.get("optional", False) or arg_name.startswith("--")

        print(self.arg_name, self.optional)

class ArgumentParser:
    def __init__(self):
        self.args: list[Argument] = []
        def get_required_args() -> list[Argument]:
            args = []
            for arg in self.args:
                if arg.optional:
                    continue

                args.append(arg)
                
            return args
        
        def get_optional_args() -> list[Argument]:
            args = []
            for arg in self.args:
                if not arg.optional:
                    continue

                args.append(arg)
                
            return args

        self.__get_required_args = get_required_args
        self.__get_optional_args = get_optional_args

    def add_argument(self, arg_name: str, **kwds):
        self.args.append(Argument(arg_name, **kwds))            

    def parse(self):
        required_args = self.__get_required_args()
        required_arg_idx = 0
        for arg in sys.argv[1:]:            
            if arg.startswith(tuple([arg_.arg_name for arg_ in self.__get_optional_args()])):
                name, *val = arg.split("=")
                setattr(self, name, "=".join(val))
                continue
            
            name = required_args[required_arg_idx].arg_name
            setattr(self, name, arg)
            required_arg_idx += 1

        if len(required_args) != required_arg_idx:
            raise ArgumentError("Script is missing required argument(s): " + ", ".join(arg.arg_name for arg in required_args[required_arg_idx:]))
        
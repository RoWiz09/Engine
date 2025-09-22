import Engine, glfw
import sys

args = {}
for argument in sys.argv[1:]:
    if "=" in argument:
        arg, value = arg.split("=")
        args[arg] = value
    else:
        args[argument] = True

if args.get("--debug", False):
    Engine.configure_loggers(log_to_console = True, log_level = Engine.logging_levels.DEBUG)

window = Engine.Window()

while not window.should_close():
    window.update()

window.terminate()
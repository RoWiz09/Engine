import importlib.util as import_util
import os, sys

Logger, SceneManager, Input = None, None, None
KeyCodes, MouseButtons = None, None

def get_modules(base_path: str):
    global Logger, SceneManager, Input, KeyCodes, MouseButtons
    if base_path not in sys.path:
        sys.path.insert(0, base_path)

    def load_engine_module(name, rel_path, dotted_name):
        full_path = os.path.join(base_path, *rel_path)
        
        if name in sys.modules:
            return sys.modules[name]
        
        spec = import_util.spec_from_file_location(name, full_path)
        module = import_util.module_from_spec(spec)
        
        module.__package__ = dotted_name
        
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    # Import Logger
    init_module = load_engine_module("__init__", ["ghost_engine", "__init__.py"], "ghost_engine")
    Logger = getattr(init_module, "Logger")
    SceneManager = getattr(init_module, "SceneManager")
    Input = getattr(init_module, "Input") 

    KeyCodes = getattr(init_module, "KeyCodes") 
    MouseButtons = getattr(init_module, "MouseButtons")
    getattr(init_module, "setup")()

    return Logger, SceneManager, Input



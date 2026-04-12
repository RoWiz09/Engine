import importlib.util as import_util
import os, sys

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ghost_engine.core.logger import Logger
    from ghost_engine.core.scene_manager import SceneManager
    from ghost_engine.core.input import Input
    
    from ghost_engine.core.input import KeyCodes, MouseButtons

if TYPE_CHECKING:
    logger: type[Logger] = None
    scene_manager: type[SceneManager] = None
    input_handler: type[Input] = None
    key_codes: type[KeyCodes] = None
    mouse_buttons: type[MouseButtons] = None

else:
    logger = None
    scene_manager = None
    input_handler = None
    key_codes = None
    mouse_buttons = None

def get_modules(base_path: str):
    global logger, scene_manager, input_handler, key_codes, mouse_buttons
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
    logger = getattr(init_module, "Logger")
    scene_manager = getattr(init_module, "SceneManager")
    input_handler = getattr(init_module, "Input") 

    key_codes = getattr(init_module, "KeyCodes") 
    mouse_buttons = getattr(init_module, "MouseButtons")
    getattr(init_module, "setup")()

    return logger, scene_manager, input_handler



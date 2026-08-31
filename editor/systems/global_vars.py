import importlib.util as import_util
import os, sys
import glfw

import threading

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ghost_engine.core.logger import Logger
    from ghost_engine.core.scene_manager import SceneManager
    from ghost_engine.core.input import Input
    
    from ghost_engine.core.input import KeyCodes, MouseButtons
    from ghost_engine.scripting.behavior import EditorField, Behavior
    from ghost_engine.core import logger as LoggerModule
    from ghost_engine.core.packer import Pack, PathLike 

    from ghost_engine.datatypes.engine_data_type import DataType, DisplayMethods

    from ..editor import Window


    logger_module: LoggerModule = None
    logger: type[Logger] = None
    scene_manager: type[SceneManager] = None
    input_handler: type[Input] = None
    key_codes: type[KeyCodes] = None
    mouse_buttons: type[MouseButtons] = None
    editor_field: type[EditorField] = None
    pack: type[Pack] = None

    editor_window: Window = None

    engine_data_type: type[DataType] = None
    engine_display_methods: type[DisplayMethods] = None

else:
    logger_module: type = None
    logger: type = None
    scene_manager: type = None
    input_handler: type = None
    key_codes: type = None
    mouse_buttons: type = None
    editor_field: type = None
    pack: type = None

    editor_window = None

    engine_data_type: type = None
    engine_display_methods: type = None

from argparse import ArgumentParser

current_cursor_type = glfw.ARROW_CURSOR

ARGS = None
def parse_args():
    global ARGS
    parser = ArgumentParser()
    parser.add_argument("project", type=str)
    parser.add_argument("--enable-console", action='store_true')
    parser.add_argument("--task-limit", type=int, default=16)

    ARGS = parser.parse_args()

GL_FUNC_LOCK = threading.Lock()
MAIN_PROC = False

def get_modules(base_path: str):
    global logger, logger_module, scene_manager, input_handler, key_codes, mouse_buttons, editor_field, pack, engine_data_type, engine_display_methods
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
    logger_module = sys.modules["ghost_engine.core.logger"]
    scene_manager = getattr(init_module, "SceneManager")
    input_handler = getattr(init_module, "Input") 

    key_codes = getattr(init_module, "KeyCodes") 
    mouse_buttons = getattr(init_module, "MouseButtons")
    editor_field = getattr(sys.modules["ghost_engine.scripting.behavior"], "EditorField")
    pack = getattr(sys.modules["ghost_engine.core.packer"], "Pack")

    engine_data_type = getattr(sys.modules["ghost_engine.datatypes.engine_data_type"], "DataType")
    engine_display_methods = getattr(sys.modules["ghost_engine.datatypes.engine_data_type"], "DisplayMethods")

    return logger, scene_manager, input_handler



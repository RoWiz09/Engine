from . import global_vars as modules
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ghost_engine.scripting.behavior import Behavior

import importlib
import sys

def reload_behaviors():
    scene_manager = modules.scene_manager()
    for obj in scene_manager.game_objects:
        for idx, component in enumerate(obj.components.copy()):
            component_module = type(component).__module__
            component_class = type(component).__name__

            del sys.modules[component_module]

            module = importlib.import_module(component_module)
            new_class_data = getattr(module, component_class, None)
            if new_class_data is None:
                modules.logger("BEHAVIOR MANAGER").log_error(
                    f"The class {component_class} in the module {component_module} doesn't exist anymore!")
                obj.components.pop(idx)
                
            if TYPE_CHECKING:
                assert isinstance(new_class_data, Behavior)

            new_class_inst = new_class_data.from_inst(component)
            obj.components[idx] = new_class_inst
                
            

from typing_extensions import overload
from src.RoDevEngine.core.logger import Logger

import behavior

class Object:
    @overload
    def __init__(self, name, *components): ...

    @overload
    def __init__(self, name): ...

    def __init__(self, name, *components):
        self.name = name
        self.components = []
        for comp in components:
            if issubclass(type(comp), behavior.Behavior):
                self.components.append(comp)
            
            else:
                Logger("CORE").log_error(f"Object of type {type(comp).__name__} is not a Behavior.")

    def get_component(self, component_class):
        for component in self.components:
            if isinstance(component, component_class):
                print("test")

Object("test", Object("test2")).get_component(Object)
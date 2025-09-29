from typing_extensions import overload
from RoDevEngine.core.logger import Logger

import RoDevEngine.scripts.behavior as behavior

class Object:
    @overload
    def __init__(self, name, *components): ...

    @overload
    def __init__(self, name): ...

    def __init__(self, name, *components):
        self.name = name
        self.components : list[behavior.Behavior] = []
        for comp in components:
            if issubclass(type(comp), behavior.Behavior):
                self.components.append(comp)
            
            else:
                Logger("CORE").log_error(f"Object of type {type(comp).__name__} is not a Behavior.")

    def update(self, dt):
        for component in self.components:
            component.update(dt)

    def fixed_update(self):
        for component in self.components:
            component.fixed_update()

    def get_component(self, component_class):
        for component in self.components:
            if isinstance(component, component_class):
                print("test")

    def add_components(self, *components):
        for component in components:
            if issubclass(type(component), behavior.Behavior):
                self.components.append(component)
            else:
                Logger("CORE").log_error(f"Object of type {type(component).__name__} is not a Behavior.")

    def add_component(self, component):
        if issubclass(type(component), behavior):
            self.components.append(component)
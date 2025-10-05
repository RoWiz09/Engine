from typing_extensions import overload

from RoDevEngine.core.logger import Logger
from RoDevEngine.rendering.material import Material
from RoDevEngine.core.transform import Transform

import RoDevEngine.scripts.behavior as behavior

class Object:
    @overload
    def __init__(self, name, material:Material): ...

    @overload
    def __init__(self, name, material:Material, transform: Transform): ...

    @overload
    def __init__(self, name, material:Material, transform: Transform, *components): ...

    def __init__(self, name, material:Material, transform: Transform = Transform(), *components):
        self.name = name
        self.mat = material
        self.components : list[behavior.Behavior] = []

        self.__transform = transform
        self.__enabled = True

        for comp in components:
            if issubclass(type(comp), behavior.Behavior):
                self.components.append(comp)
            
            else:
                Logger("CORE").log_error(f"Object of type {type(comp).__name__} is not a Behavior.")

    @property
    def transform(self):
        return self.__transform

    def update(self, dt, view, proj):
        self.mat.use()
        self.mat.shader.set_mat4("uView", view)
        self.mat.shader.set_mat4("uProjection", proj)
        for component in self.components:
            if component.enabled:
                component.update(dt)
    
    def set_material(self, mat:Material):
        self.mat = mat

    def fixed_update(self):
        for component in self.components:
            if component.enabled:
                component.fixed_update()

    def get_component(self, component_class):
        for component in self.components:
            if isinstance(component, component_class):
                print("test")

    def add_components(self, *components):
        for component in components:
            if issubclass(type(component), behavior.Behavior):
                component._gameobject = self
                self.components.append(component)
            else:
                Logger("CORE").log_error(f"Object of type {type(component).__name__} is not a Behavior.")

    def add_component(self, component):
        if issubclass(type(component), behavior):
            component._gameobject = self
            self.components.append(component)

    @property
    def enabled(self) -> bool:
        return self.__enabled
    
    @enabled.setter
    def enabled(self, enabled: bool):
        if isinstance(enabled, bool):
            self.__enabled = enabled
        else:
            Logger("CORE").log_warning(f"{type(state).__name__} is not of type bool")

    def set_active(self, state: bool) -> bool | None:
        if isinstance(state, bool):
            self.__enabled = state

            return self.__enabled
        else:
            Logger("CORE").log_warning(f"{type(state).__name__} is not of type bool")
            return None
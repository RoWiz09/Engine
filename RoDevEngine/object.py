from typing_extensions import overload

from .core.logger import Logger
from .rendering.material import Material
from .core.transform import Transform

from .scripts.behavior import Behavior
import sys

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
        self.components : list[Behavior] = []

        transform.gameobject = self

        self.__transform = transform
        self.__enabled = True

        for comp in components:
            if issubclass(type(comp), Behavior):
                self.components.append(comp)
            
            else:
                Logger("CORE").log_error(f"Object of type {type(comp).__name__} is not a Behavior.")

    @property
    def transform(self):
        return self.__transform

    def update(self, dt, view, proj):
        if self.enabled:
            self.mat.use()
            self.mat.shader.set_mat4("uView", view)
            self.mat.shader.set_mat4("uProjection", proj)
            for component in self.components:
                if not component.enabled:
                    continue

                if sys.argv[-1] == "--editor" and not component._run_in_editor:
                    continue

                component.update(dt)
    
    def set_material(self, mat:Material):
        self.mat = mat
        return self

    def fixed_update(self):
        for component in self.components:
            if component.enabled:
                component.fixed_update()

    def get_component(self, component_class):
        for component in self.components:
            if isinstance(component, component_class) and component.enabled:
                return component

    def add_components(self, *components):
        for component in components:
            if issubclass(type(component), Behavior):
                component._gameobject = self
                self.components.append(component)
            else:
                Logger("CORE").log_error(f"Object of type {type(component).__name__} is not a Behavior.")

    def add_component(self, component):
        if issubclass(type(component), Behavior):
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
            Logger("CORE").log_warning(f"{type(enabled).__name__} is not of type bool")

    def set_active(self, state: bool) -> bool | None:
        if isinstance(state, bool):
            self.__enabled = state

            return self
        else:
            Logger("CORE").log_warning(f"{type(state).__name__} is not of type bool")
            return self
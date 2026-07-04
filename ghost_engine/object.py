from __future__ import annotations
from typing_extensions import overload

from .core.logger import Logger
from .rendering.material import Material
from .core.transform import Transform

from .scripting.behavior import Behavior, RenderBehavior
import sys

from typing import TypeVar
T = TypeVar("T")

class GameObject:
    @overload
    def __init__(self, name: str, material:Material): ...

    @overload
    def __init__(self, name: str, material:Material, transform: Transform): ...

    @overload
    def __init__(self, name: str, material:Material, transform: Transform, *behaviors): ...

    def __init__(self, name: str, material:Material, transform: Transform = Transform(), *behaviors, tag: str = ""):
        self.name = name
        self.static = False
        self.tag = ""

        self.mat = material
        self.behaviors : list[Behavior] = []

        transform.gameobject = self

        self.children: list[GameObject] = []

        if transform.parent:
            transform.parent.gameobject.children.append(self)

        self.__transform = transform
        self.__enabled = True

        self.__render_behaviors: list[RenderBehavior] = []

        for comp in behaviors:
            if issubclass(type(comp), Behavior):
                self.behaviors.append(comp)
            
            else:
                Logger("CORE").log_error(f"Object of type {type(comp).__name__} is not a Behavior.")

    # Rendering
    def pre_render(self):
        list(map(lambda s: s.pre_render(), self.__render_behaviors))

    def render(self):
        self.mat.use()
        list(map(lambda s: s.on_render(), self.__render_behaviors))

    def post_render(self):
        list(map(lambda s: s.post_render(), self.__render_behaviors))

    def set_material(self, mat:Material):
        self.mat = mat
        return self
    
    # Updates
    def update(self, dt):
        if self.enabled:
            for behavior in self.behaviors:
                if not behavior.enabled:
                    continue

                behavior.update(dt)

    def fixed_update(self):
        for behavior in self.behaviors:
            if behavior.enabled:
                behavior.fixed_update()

    # behaviors
    def get_behavior(self, behavior_class: type[T]) -> T:
        for behavior in self.behaviors:
            if isinstance(behavior, behavior_class) and behavior.enabled:
                return behavior
            
    def get_behaviors(self, behavior_class: type[T]) -> list[T]:
        out = []
        for behavior in self.behaviors:
            if isinstance(behavior, behavior_class) and behavior.enabled:
                out.append(behavior)

        return out

    def add_behaviors(self, *behaviors):
        for behavior in behaviors:
            if issubclass(type(behavior), Behavior):
                behavior._gameobject = self
                self.behaviors.append(behavior)

                if issubclass(type(behavior), RenderBehavior):
                    self.__render_behaviors.append(behavior)

            else:
                Logger("CORE").log_error(f"Object of type {type(behavior).__name__} is not a Behavior.")

    def add_behavior(self, behavior):
        if issubclass(type(behavior), Behavior):
            behavior._gameobject = self
            self.behaviors.append(behavior)

            if issubclass(type(behavior), RenderBehavior):
                self.__render_behaviors.append(behavior)

    # Properties
    @property
    def transform(self):
        return self.__transform
    
    @property
    def enabled(self) -> bool:
        if self.__transform.parent is None:
            return self.__enabled
        return self.__enabled & self.transform.parent.gameobject.enabled
    
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
    
    # Get Children methods
    def get_child_by_name(self, name: str):
        for child in self.children:
            if child.name == name:
                return child
    
    def get_children_by_name(self, name: str, limit=-1):
        out = set()
        for child in self.children:
            if child.name == name:
                out.add(child)
                if len(out) == limit:
                    return out
                
        return out
    
    def get_child_with_behavior(self, behavior_class: T) -> GameObject:
        for child in self.children:
            for behavior in child.behaviors:
                if isinstance(behavior, behavior_class):
                    return child
                
    def get_children_with_behavior(self, behavior_class: T) -> list[GameObject]:
        def has_behavior(obj):
            for comp in obj:
                if isinstance(comp, behavior_class):
                    return obj
        
        objects = set()
        for obj in self.children:
            if has_behavior(obj):
                objects.add(obj)
    
    def destroy(self):
        for script in self.behaviors:
            script.destroy()


    # Class Methods
    @classmethod
    def find_with_behavior(cls, behavior_type) -> set[GameObject]:
        """
        Returns all gameobject instances which has `behavior_type` in its `behaviors` list.
        """
        if not issubclass(behavior_type, Behavior):
            Logger("GAMEOBJECT").log_error("behavior_type argument of GameObject.find_with_behavior() is not of subclass Behavior!")
            return set()

        return Behavior.behavior_instances[behavior_type]

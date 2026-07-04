from __future__ import annotations
from ..core.logger import Logger

from typing import final
from typing import TYPE_CHECKING, Any, TypeAlias

from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from ..object import GameObject as object
    from .collider_type import CollisionInfo
else:
    object: TypeAlias = Any
    collider: TypeAlias = Any

def register_editor_button(func):
    Behavior.editor_button_registry.append(func)
    return func

EXCLUDED_FROM_BUILD = set()
def exclude_from_build(func):
    global EXCLUDED_FROM_BUILD
    EXCLUDED_FROM_BUILD.add(func)

class NonOverrideable:
    """
        Makes the decorated method unable to be overridden.
    """
    def __init__(self, func):
        self.func = func

        self.inst = None
        def wrapper(*args, **kwds):
            return self.func(self.inst, *args, **kwds)
        self.wrapped_func = wrapper

    def __set_name__(self, owner: Behavior, name):        
        if not getattr(owner, 'override-patched', False):
            setattr(owner, 'orig-init-subclass', owner.__dict__['__init_subclass__'])
            def wrapper(cls):
                non_overrideable: dict[str, NonOverrideable] = getattr(owner, 'non-overrideable-methods', dict())
                for name, method in non_overrideable.items():
                    func = getattr(cls, name)
                    if func and func != method:
                        print(func, method)
                        Logger("OVERRIDE PREVENTION").log_warning(f"{name} is marked as non-overrideable, yet was overriden by {cls.__name__}. It has been removed.")
                        delattr(cls, name)

                getattr(owner, 'orig-init-subclass').__func__(cls)
            
            owner.__init_subclass__ = classmethod(wrapper)
            setattr(owner, 'non-overrideable-methods', dict())
            setattr(owner, 'override-patched', True)

        getattr(owner, 'non-overrideable-methods')[self.func.__name__] = self.wrapped_func
    
    def __call__(self, *args, **kwds):
        return self.func(*args, **kwds)
    
    def __get__(self, instance, owner):
        self.inst = instance
        return self.wrapped_func

class InitMethod:
    """
        Sets the decorated method to be the method used when initalizing the class. \n
        Automatically passes through the class type to create instances with.
    """
    def __init__(self, func):
        self.func = func
        self.vars = []

    def __set_name__(self, owner: Behavior, name):
        owner.init_method = self
        self.owner = owner

    def __call__(self, *args):
        vars = args[:-1]
        cls = self.func(self.owner, *args)
        setattr(cls, "init_vars", vars)
        return cls
    
    def refresh_vars(self, func, *args):
        """
            call this when modifying any variables needed for initalization for correct saving in the editor.
        """
        def wrapper(cls, *args):
            func(cls, *args)
            setattr(cls, "init_vars", args)

        return wrapper

class AdvancedBehavior(ABC):
    """
    An interface, adding callbacks to a base behavior for the following events:
    - `on_set_enabled`: Ran whenever the @enabled.setter method is called.
    """
    def __init_subclass__(cls):
        if not issubclass(cls, Behavior):
            Logger("ADVANCED BEHAVIOR").log_fatal("Cannot use AdvancedBehavior on a non-behavior object!")
        
        enabled = getattr(cls, "enabled", None)
        if isinstance(enabled, property):
            original_setter = enabled.fset
            def new_enabled_setter(inst, val):
                original_setter(inst, val)
                inst.on_set_enabled()
            
            cls.enabled = property(
                enabled.fget,
                new_enabled_setter,
                enabled.fdel,
                enabled.__doc__
            )
        
        else:
            Logger("ADVANCED BEHAVIOR").log_error("Behavior.enabled attribute is not a property!")        

    def on_set_enabled(self):
        pass
    
    def on_editor_reload(self):
        """
            A method called when the editor reloads scripts. This is not included in builds.
        """
        pass

class PhysicsBehavior(ABC):
    """
    An interface, adding methods for the following events:
    - `on_collision` (variants: `_start`, `_exit`): Called when two collision objects collide with each other.
    - `on_trigger` (variants: `_start`, `_exit`): Called when a trigger collider on this gameobject is entered.
    """

    # Collisions
    def on_collision_start(self, other: CollisionInfo):
        """
        Called upon a collision 'starting', or the first collision between two gameobjects.
        
        :param other: The colliding collision object
        :type other: Object
        """
        pass

    def on_collision(self, other: CollisionInfo):
        """
        Continuously called while there is a collision between two gameobjects.
        
        :param other: The colliding collision object
        :type other: Object
        """
        pass

    def on_collision_exit(self, other: CollisionInfo):
        """
        Called when there is no longer a collision between two gameobjects.
        
        :param other: The collision object collided with
        :type other: Object
        """
        pass

    # Triggers
    def on_trigger_start(self, other: CollisionInfo):
        """
        Called upon a trigger 'starting', or the first trigger collision between two gameobjects.
        
        :param other: The colliding collision object
        :type other: Object
        """
        pass

    def on_trigger(self, other: CollisionInfo):
        """
        Continuously called while there is a trigger collision between two gameobjects.
        
        :param other: The colliding collision object
        :type other: Object
        """
        pass

    def on_trigger_exit(self, other: CollisionInfo):
        """
        Called when there is no longer a trigger collision between two gameobjects.
        
        :param other: The collision object collided with
        :type other: Object
        """
        pass

class RenderBehavior(ABC):
    """
    An interface, adding methods for the following events:
    - `pre_render`: A method called before rendering any objects.
    - `on_render`: A method called when rendering objects. Recommended use is to draw a mesh.
    - `post_render`: A method called after rendering all objects in the scene.
    """

    def pre_render(self):
        """
            Called before rendering any objects, used by the mesh class to set up VBO's/VAO's.
        """
        pass

    def on_render(self):
        """
            Called during SceneManager.render_scene(); used by the mesh class to render meshes.
        """
        pass

    def post_render(self):
        """
            Called after rendering all objects.
        """
        pass

class Behavior(ABC):
    """
    The basic class all game scripts are required to inherit from. Implements events for:
    - `__init__`: Class initalization. 
    - `update`: Called every 'update', or 'tick', during the game's runtime.
    - `fixed_update`: Called ~50 times every second, typically used for physics.
    - `on_frame` (`_start` / `_end`): Called at the start or end of a frame, respectively.
    - `on_scene` (`_load` / `_unload`): Called when a scene is loaded or unloaded, respectively. Most useful when attached to static objects.
    """
    component_category_registry: dict[str, list[Behavior]] = {}
    """
        A dictionary which contains the category string, as well as a list of behaviors which belong to it.
    """

    behavior_instances = {}
    """
        A dictionary which binds every behavior type to a set with every gameobject with it.
    """

    category = "General"
    editor_button_registry = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Skip abstract base classes
        if cls is Behavior:
            return
        
        if not cls.category in Behavior.component_category_registry.keys():
            Behavior.component_category_registry[cls.category] = []
        Behavior.component_category_registry[cls.category].append(cls)
        Behavior.behavior_instances[cls] = set()
    
    @classmethod
    def from_inst(cls, inst: Behavior):
        new_inst = cls(inst.gameobject)
        for var in vars(inst):
            value = getattr(inst, var)
            setattr(new_inst, var, value)

        return new_inst

    def __init__(self, gameobject: object):
        try:
            super().__init__(gameobject)
        except:
            super().__init__()
        self.__gameobject: object = gameobject
        self.__enabled = True

        self.behavior_instances[type(self)].add(gameobject)
    
    init_method: InitMethod = None
    init_vars = []

    @property
    def gameobject(self):
        return self.__gameobject
    
    @property
    def enabled(self):
        return self.__enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        if isinstance(value, bool):
            self.__enabled = value
        else:
            Logger("CORE").log_error("Behavior.enabled must be set to a boolean value.")

    @property
    def window(self):
        from ..core.window import Window
        return Window()
    
    # Frame methods
    @classmethod
    def on_frame_start(cls):
        """
        Called upon the start of a frame. This is a class method, and as such, will only be called once per class.
        """
        pass

    @classmethod
    def on_frame_end(cls):
        """
        Called upon the end of a frame. This is a class method, and as such, will only be called once per class.
        """
        pass
    
    # Update methods
    def update(self, dt:float):
        """
            Runs every tick.
            Args:
                dt (float): Deltatime
        """

    def fixed_update(self):
        """
            Runs 50 times every second. Usually used for physics, or timers.\n
            Sometimes it'll run 51 or 49 times per second, so it'll be slightly off.
        """
        pass    

    # Scene methods
    def on_scene_load(self, scene_info):
        """
            Called when the scene loads!
            Args:
                scene_info (SceneInfo): The SceneInfo object for the loaded scene
        """
        pass

    def on_scene_unload(self, scene_info):
        """
            Called when the scene unloads!
            Args:
                scene_info (SceneInfo): The SceneInfo object for the unloaded scene
        """
        pass

    @NonOverrideable
    def destroy(self):
        Behavior.behavior_instances[type(self)].remove(self.__gameobject)
        print(f"Destroying {self}")

class EditorField:
    def __init__(self, field_type: type, default=None):
        self.type = field_type
        self.default = default
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.name, self.default)

    def __set__(self, instance, value):
        instance.__dict__[self.name] = self.type(value)
        
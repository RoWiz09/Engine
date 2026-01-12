from __future__ import annotations

from ..core.logger import Logger
import sys

def register_editor_button(func):
    Behavior.editor_button_registry.append(func)
    return func

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

class Behavior:
    """
    The basic behavior class all scripts should inherit from. Exposes methods for:\n
    - __init__(self, gameobject): basic script initalization
    - on_frame_start/end: Class methods called upon the start or end of a frame respectively
    - on_collision (start and end): Methods called upon collisions
    - update/fixed_update: Methods called every frame/~50th of a second
    - on_scene_load/unload: Methods called upon the loading/unloading of a scene.
    """
    component_category_registry: dict[str, list[Behavior]] = {}
    category = "General"
    
    editor_button_registry = []

    run_in_editor = False

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Skip abstract base classes
        if cls is Behavior:
            return
        
        if not cls.category in Behavior.component_category_registry.keys():
            Behavior.component_category_registry[cls.category] = []
        Behavior.component_category_registry[cls.category].append(cls)
        
    def __init__(self, gameobject):
        from RoDevEngine.object import Object
        self.__gameobject: Object = gameobject
        self.__enabled = True
    
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
    
    @classmethod
    def on_frame_start(cls):
        """
        Called upon the start of a frame. This is a class method.
        """
        pass

    @classmethod
    def on_frame_end(cls):
        """
        Called upon the end of a frame. This is a class method.
        """
        pass
    
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

    def on_collision_start(self, other):
        """
        Called upon a collision 'starting', or the first collision between two gameobjects.
        
        :param other: The colliding gameobject
        :type other: Object
        """
        pass

    def on_collision(self, other):
        """
        Continuously called while there is a collision between two gameobjects.
        
        :param other: The colliding gameobject
        :type other: Object
        """
        pass

    def on_collision_exit(self, other):
        """
        Called when there is no longer a collision between two gameobjects.
        
        :param other: The gamobject collided with
        :type other: Object
        """
        pass

class EditorField:
    def __init__(self, field_type, default=None):
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
        instance.__dict__[self.name] = value
        
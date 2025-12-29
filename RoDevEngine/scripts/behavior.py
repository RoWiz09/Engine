from ..core.logger import Logger
import sys

class Behavior:
    registry = {}
    editor_visible = True
    category = "General"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Skip abstract base classes
        if cls is Behavior:
            return

        Behavior.registry[cls.__name__] = cls
        
    def __init__(self, gameobject):
        from RoDevEngine.object import Object
        self.__gameobject: Object = gameobject
        self.__enabled = True

        self._run_in_editor = False
    
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
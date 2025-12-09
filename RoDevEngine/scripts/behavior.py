from RoDevEngine.core.logger import Logger

class Behavior:
    def __init__(self, gameobject):
        from RoDevEngine.object import Object
        self.__gameobject: Object = gameobject
        self.__enabled = True
    
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

    def update(self, dt:float):
        """
            Runs every tick.
            Args:
                dt (float): Deltatime
        """
        pass

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
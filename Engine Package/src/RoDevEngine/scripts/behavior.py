class Behavior:
    def __init__(self):
        self.enabled = True
        
    def update(self, dt:float):
        """
            Runs every tick.
            Args:
                dt (float): Deltatime
        """
        pass

    def fixed_update(self):
        """
            Runs 50 times every second.
        """
        pass

    def on_unloaded(self, scene_name:str):
        """
            Called when the scene unloads!
            Args:
                scene_name (str): The name of the unloaded scene.
        """
        pass

    def on_scene_load(self, scene_name:str):
        """
            Called when the scene loads!
            Args:
                scene_name (str): The name of the loaded scene.
        """
        pass
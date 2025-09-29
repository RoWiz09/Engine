from RoDevEngine.scripts.behavior import Behavior
from RoDevEngine import get_logger

class Test(Behavior):
    def __init__(self, gameobject):
        super().__init__(gameobject)

    def on_scene_load(self, scene_info):
        get_logger("MY LOGGER").log_info(f"Cool, we loaded {scene_info}")
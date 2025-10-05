from RoDevEngine.scripts.behavior import Behavior
from RoDevEngine.core.input import KeyCodes, Input
from RoDevEngine import get_logger

class Test(Behavior):
    def __init__(self, gameobject):
        super().__init__(gameobject)

    def on_scene_load(self, scene_info):
        get_logger("MY LOGGER").log_info(f"Cool, we loaded {scene_info}")

    def update(self, dt):
        if Input().get_key_down(KeyCodes.k_W):
            self.gameobject.transform.pos.x + 1
        return super().update(dt)

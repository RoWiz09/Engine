from RoDevEngine.scripts.behavior import Behavior
from RoDevEngine.core.input import KeyCodes, Input
from RoDevEngine import get_logger

from pyglm import glm

class Test(Behavior):
    def __init__(self, gameobject):
        super().__init__(gameobject)

    def on_scene_load(self, scene_info):
        get_logger("MY LOGGER").log_info(f"Cool, we loaded {scene_info}")

    def update(self, dt):
        move_z = 0
        if Input().get_key(KeyCodes.k_W):
            move_z += 10*dt
        elif Input().get_key(KeyCodes.k_S):
            move_z -= 10*dt

        move_x = 0
        if Input().get_key(KeyCodes.k_A):
            move_x += 10*dt

        elif Input().get_key(KeyCodes.k_D):
            move_x -= 10*dt

        z_rot = 0
        if Input().get_key(KeyCodes.k_E):
            z_rot += 10*dt
        elif Input().get_key(KeyCodes.k_Q):
            z_rot -= 10*dt

        self.gameobject.transform.move_with_rotation(move_x, 0, move_z)
        self.gameobject.transform.rotate_by_degrees(0, 0, z_rot)

class Test2(Behavior):
    def __init__(self, gameobject):
        super().__init__(gameobject)

    def on_scene_load(self, scene_info):
        get_logger("MY LOGGER").log_info(f"Cool, we loaded {scene_info}")

    def update(self, dt):
        move_y = 0
        if Input().get_key(KeyCodes.k_space):
            move_y += 10*dt
        elif Input().get_key(KeyCodes.k_left_shift):
            move_y -= 10*dt

        self.gameobject.transform.move(0, move_y, 0)

from RoDevEngine.scripts.behavior import *
from RoDevEngine.core.input import KeyCodes, Input, CursorStates, MouseButtons
from RoDevEngine import get_logger

from pyglm import glm

class Test(Behavior):
    speed = EditorField("int", 10)
    
    def __init__(self, gameobject):
        super().__init__(gameobject)

    def on_scene_load(self, scene_info):
        Input().set_cursor_visibility(CursorStates.HIDDEN)
        get_logger("MY LOGGER").log_info(f"Cool, we loaded {scene_info}")

    def update(self, dt):
        move_z = 0
        if Input().get_key(KeyCodes.k_W):
            move_z += self.speed*dt
        elif Input().get_key(KeyCodes.k_S):
            move_z -= self.speed*dt

        move_x = 0
        if Input().get_key(KeyCodes.k_A):
            move_x += self.speed*dt

        elif Input().get_key(KeyCodes.k_D):
            move_x -= self.speed*dt

        z_rot = 0
        if Input().get_key(KeyCodes.k_E):
            z_rot += 10*dt
        elif Input().get_key(KeyCodes.k_Q):
            z_rot -= 10*dt

        width, height = self.window.size()[0]/2, self.window.size()[1]/2
        mx, my = Input().mouse_pos

        mx, my = mx-width/2, my-height/2

        Input().mouse_pos = (width/2, height/2)
        self.gameobject.transform.move_with_rotation(move_x, 0, move_z)
        self.gameobject.transform.rotate_by_degrees(my, -mx, z_rot)

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

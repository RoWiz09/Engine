from RoDevEngine.scripts.behavior import *
from RoDevEngine.core.input import KeyCodes, Input, CursorStates, MouseButtons
from RoDevEngine import get_logger

from RoDevEngine.editor.editor_windows import EditorWindow, register_menu
from RoDevEngine.scripts.rigidbody import Rigidbody

from RoDevEngine.helpers import clamp
from pyglm import glm

class Test(Behavior):
    speed = EditorField("int", 500)
    
    def __init__(self, gameobject):
        super().__init__(gameobject)

    def on_scene_load(self, scene_info):
        Input().set_cursor_visibility(CursorStates.HIDDEN)
        self.rigidbody = self.gameobject.get_component(Rigidbody)
        get_logger("MY LOGGER").log_info(f"Cool, we loaded {scene_info}")

    def update(self, dt):
        move_z = 0
        if Input().get_key(KeyCodes.k_W):
            move_z += self.speed
        elif Input().get_key(KeyCodes.k_S):
            move_z -= self.speed

        move_x = 0
        if Input().get_key(KeyCodes.k_A):
            move_x += self.speed

        elif Input().get_key(KeyCodes.k_D):
            move_x -= self.speed

        z_rot = 0
        if Input().get_key(KeyCodes.k_E):
            z_rot += 10*dt
        elif Input().get_key(KeyCodes.k_Q):
            z_rot -= 10*dt

        width, height = self.window.size()[0]/2, self.window.size()[1]/2
        mx, my = Input().mouse_pos

        mx, my = mx-width/2, my-height/2

        Input().mouse_pos = (width/2, height/2)

        vel = glm.vec3(move_x, 0, move_z)
        if glm.length(vel) > 0.001:
            vel = glm.normalize(vel) * 10

        # Adjust for rotation
        vel = glm.rotate(vel, self.gameobject.transform.rot.y, (0, 1, 0))

        self.rigidbody.velocity += vel
        self.gameobject.transform.rotate_by_degrees(-my, mx, 0)
        self.gameobject.transform.localrot.x = clamp(-89.0, 89.0, self.gameobject.transform.localrot.x)
        self.rigidbody.velocity.x = clamp(-self.speed, self.speed, self.rigidbody.velocity.x)
        self.rigidbody.velocity.z = clamp(-self.speed, self.speed, self.rigidbody.velocity.z)

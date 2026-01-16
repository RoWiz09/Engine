from ..scripts.behavior import *
from ..core.input import KeyCodes, Input, CursorStates, MouseButtons
from ..core.logger import Logger

from ..editor.editor_windows import EditorWindow, register_menu
from ..scripts.rigidbody import Rigidbody
from ..scripts.camera import Camera

from ..helpers import clamp
from pyglm import glm

class FPSController(Behavior):
    speed = EditorField("int", 10)
    jump_force = EditorField("float", 5.0)

    mouse_sens = EditorField("float", 1.0)
    
    def __init__(self, gameobject):
        super().__init__(gameobject)

    def on_scene_load(self, scene_info):
        Input().set_cursor_visibility(CursorStates.HIDDEN)

        self.rigidbody = self.gameobject.get_component(Rigidbody)
        if not self.rigidbody:
            Logger("FPS CONTROLLER").log_error("The FPS controller's gameobject is missing a rigidbody!")

        self.camera = self.gameobject.get_child_with_component(Camera)
        if not self.camera:
            Logger("FPS CONTROLLER").log_error("The FPS controller's gameobject is missing a child with a camera!")

    def update(self, dt):
        move_z = 0
        if Input().get_key(KeyCodes.k_W):
            move_z += 1
        if Input().get_key(KeyCodes.k_S):
            move_z -= 1

        move_x = 0
        if Input().get_key(KeyCodes.k_A):
            move_x += 1

        if Input().get_key(KeyCodes.k_D):
            move_x -= 1

        width, height = self.window.size()[0]/2, self.window.size()[1]/2
        mx, my = Input().mouse_pos

        mx, my = mx-width, my-height

        Input().mouse_pos = (width, height)

        vel = glm.vec3(move_x, 0, move_z)
        if glm.length(vel) > 0.001:
            vel = glm.normalize(vel) * self.speed * dt

            self.gameobject.transform.move_with_rotation(*vel)

        self.gameobject.transform.rotate_by_degrees(0, mx * self.mouse_sens, 0)
        self.camera.transform.rotate_by_degrees(-my * self.mouse_sens, 0, 0)
        self.camera.transform.localrot.x = clamp(-89.0, 89.0, self.camera.transform.localrot.x)

        if Input().get_key(KeyCodes.k_space) and self.rigidbody.grounded:
            self.rigidbody.add_force_vector(glm.vec3(0, self.jump_force, 0))

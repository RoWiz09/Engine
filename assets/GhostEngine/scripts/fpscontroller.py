from ghost_engine.scripting.behavior import *
from ghost_engine.core.input import KeyCodes, Input, CursorStates, MouseButtons
from ghost_engine.core.logger import Logger

from .rigidbody import Rigidbody
from .camera import Camera

from ghost_engine.math import clamp
from pyglm import glm

class FPSController(Behavior):
    speed = EditorField(int, 10)

    can_jump = EditorField(bool, True)
    jump_force = EditorField(float, 5.0)

    mouse_sensitivity = EditorField(float, 1.0)
    
    def __init__(self, gameobject):
        super().__init__(gameobject)

    def on_scene_load(self, scene_info):
        Input().set_cursor_visibility(CursorStates.HIDDEN)

        if self.can_jump == True:
            self.rigidbody = self.gameobject.get_behavior(Rigidbody)
            if not self.rigidbody:
                Logger("FPS CONTROLLER").log_error("The FPS controller's gameobject is missing a rigidbody, which is needed for jumping!")

        self.camera = self.gameobject.get_child_with_behavior(Camera)
        if not self.camera:
            Logger("FPS CONTROLLER").log_error("The FPS controller's gameobject is missing a child with a camera!")

        width, height = self.window.size()[0]//2, self.window.size()[1]//2
        Input().mouse_pos = (width, height)

    def update(self, dt):
        velocity = glm.vec3()
        if Input().get_key(KeyCodes.k_W):
            velocity += self.gameobject.transform.front
        if Input().get_key(KeyCodes.k_S):
            velocity -= self.gameobject.transform.front
        if Input().get_key(KeyCodes.k_D):
            velocity += self.gameobject.transform.right
        if Input().get_key(KeyCodes.k_A):
            velocity -= self.gameobject.transform.right
                
        width, height = self.window.size()[0]//2, self.window.size()[1]//2
        mx, my = Input().mouse_pos
        mx, my = mx-width, my-height

        Input().mouse_pos = (width, height)

        if glm.length(velocity) > 0.001:
            vel = glm.normalize(velocity) * self.speed * dt
            self.gameobject.transform.move(*vel)

        self.gameobject.transform.rotate_by_degrees(0, -mx * self.mouse_sensitivity, 0)
        self.camera.transform.rotate_by_degrees(my * self.mouse_sensitivity, 0, 0)
        self.camera.transform.localrot.x = clamp(-89.0, 89.0, self.camera.transform.localrot.x)

        if Input().get_key(KeyCodes.k_space) and self.rigidbody.grounded:
            self.rigidbody.add_force(glm.vec3(0, self.jump_force, 0))

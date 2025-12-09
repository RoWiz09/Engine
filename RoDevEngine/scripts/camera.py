from .behavior import Behavior
from pyglm import glm

class Camera(Behavior):
    def __init__(self, gameobject):
        self.rotation_mod = glm.vec3()
        self.position_mod = glm.vec3()

        self.fov = 60.0

        self.player_camera = True # If the camera is supposed to be looked through by the player.
    
    def on_scene_load(self, scene_info):
        if not isinstance(self.rotation_mod, glm.quat):
            self.rotation_mod = glm.quat(glm.radians(glm.vec3(self.rotation_mod)))

        if not isinstance(self.position_mod, glm.vec3):
            self.position_mod = glm.vec3(self.position_mod)
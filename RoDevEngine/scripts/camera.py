from .behavior import *
from pyglm import glm

class Camera(Behavior):
    category = "Rendering"

    rotation_mod = EditorField("vec3", glm.vec3())
    position_mod = EditorField("vec3", glm.vec3())

    fov = EditorField("float", 60.0)
    def __init__(self, gameobject):
        super().__init__(gameobject)
    
    def on_scene_load(self, scene_info):
        if not isinstance(self.rotation_mod, glm.quat):
            self.rotation_mod = glm.quat(glm.radians(glm.vec3(self.rotation_mod)))

        if not isinstance(self.position_mod, glm.vec3):
            self.position_mod = glm.vec3(self.position_mod)
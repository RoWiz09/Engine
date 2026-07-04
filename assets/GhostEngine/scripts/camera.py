from ghost_engine.scripting.behavior import Behavior, EditorField
from ghost_engine.rendering.camera_type import CamType

from pyglm import glm
import glfw

class Camera(Behavior, CamType):
    category = "Rendering"

    rotation_mod = EditorField(glm.vec3, glm.vec3())
    position_mod = EditorField(glm.vec3, glm.vec3())

    fov = EditorField(float, 60.0)
    def __init__(self, gameobject):
        super().__init__(gameobject)
    
    def on_scene_load(self, scene_info):
        if not isinstance(self.rotation_mod, glm.quat):
            self.rotation_mod_ = glm.quat(glm.radians(glm.vec3(self.rotation_mod)))

        if not isinstance(self.position_mod, glm.vec3):
            self.position_mod = glm.vec3(self.position_mod)

    def get_view_mat(self):
        return glm.lookAt(
            self.position_mod + self.gameobject.transform.pos, 
            self.position_mod + self.gameobject.transform.pos + glm.vec3(0, 0, 1) * (self.rotation_mod_ * self.gameobject.transform.rot), 
            glm.vec3(0, 1, 0) * (self.rotation_mod_ * self.gameobject.transform.rot)
        )
        
    def get_projection_mat(self):
        width, height = glfw.get_window_size(glfw.get_current_context())
        return glm.perspective(glm.radians(60), width/height, 0.01, 1000)

    def get_view_pos(self):
        return self.gameobject.transform.pos + self.position_mod
    
    def destroy(self):
        return super().destroy()
    
from ..scripting.behavior import NonOverrideable, Behavior
from ..core.logger import Logger
from glm import vec3, mat4x4

from weakref import ref

from abc import ABC, abstractmethod

def update_decorator(method):
    def wrapper(inst, dt):
        from ..core.scene_manager import SceneManager
        if SceneManager().active_camera and not SceneManager().active_camera():
            SceneManager().active_camera = ref(inst)

        return method(inst, dt)

    return wrapper

class CamType(ABC):
    def __init_subclass__(cls):
        if not issubclass(cls, Behavior):
            Logger("CAMERA TYPE").log_fatal(f"Type {cls.__name__} doesn't inherit from base class Behavior.")

        cls.update = update_decorator(cls.update)

    @abstractmethod
    def get_view_mat(self) -> mat4x4: ...
    
    @abstractmethod
    def get_projection_mat(self) -> mat4x4: ...
    
    @abstractmethod
    def get_view_pos(self) -> vec3: ...

    @NonOverrideable
    def set_active_camera(self):
        from ..core.scene_manager import SceneManager
        SceneManager().active_camera = ref(self)
        
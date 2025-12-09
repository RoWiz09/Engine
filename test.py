def create_dynamic_class(class_name):
    local_namespace = {}
    class_definition = f"""
from RoDevEngine.scripts.behavior import Behavior
from RoDevEngine.core.input import KeyCodes, Input
from RoDevEngine import get_logger

from pyglm import glm

class Test(Behavior):
    def __init__(self, gameobject):
        super().__init__(gameobject)

    def on_scene_load(self, scene_info):
        get_logger("MY LOGGER").log_info(f"Cool, we loaded")

    def update(self, dt):
        y_move = 0
        if Input().get_key(KeyCodes.k_W):
            y_move += 100
        elif Input().get_key(KeyCodes.k_S):
            y_move -= 100
        
        x_move = 0
        if Input().get_key(KeyCodes.k_A):
            x_move -= 100
        elif Input().get_key(KeyCodes.k_D):
            x_move += 100

        self.gameobject.transform.rotate_by_degrees(degrees=glm.vec3(x_move*dt, y_move*dt, 0))
        return super().update(dt)

"""
    exec(class_definition, globals(), local_namespace)
    return local_namespace[class_name]

# Create the class dynamically
MyDynamicClass = create_dynamic_class("Test")

# Use the dynamically created class
instance = MyDynamicClass(0)
print(instance.gameobject)
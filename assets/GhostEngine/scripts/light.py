from ghost_engine.scripting.behavior import *
from ghost_engine.rendering.light_type import LightType, LightTypes
from pyglm.glm import vec3, radians

class Pointlight(Behavior, LightType):
    light_type = LightTypes.POINT
    category = "Rendering"

    intensity = EditorField(float, 1)
    color = EditorField(vec3, vec3(255, 255, 255))

    range = EditorField(float, 1)

    def __init__(self, gameobject):
        super().__init__(gameobject)

class Spotlight(Behavior, LightType):
    light_type = LightTypes.SPOT
    category = "Rendering"

    intensity = EditorField(float, 1)
    color = EditorField(vec3, vec3(255, 255, 255))

    direction = EditorField(vec3, vec3())
    range = EditorField(float, 1)
    cutOff = EditorField(float, 57)
    outerCutOff = EditorField(float, 57)

    constant = EditorField(float, 1.0)
    linear = EditorField(float, 0.09)
    quadratic = EditorField(float, 0.032)

    def __init__(self, gameobject):
        super().__init__(gameobject)
        self.cutoff_radians = radians(self.cutOff)
        self.outer_cutoff_radians = radians(self.outerCutOff)

    def update(self, dt):
        self.cutoff_radians = radians(self.cutOff)
        self.outer_cutoff_radians = radians(self.outerCutOff)

        return super().update(dt)

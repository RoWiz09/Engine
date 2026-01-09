from .behavior import *
from pyglm.glm import vec3, quat
from enum import Enum

class Pointlight(Behavior):
    category = "Rendering"
    ambient = EditorField("vec3", vec3(0.05, 0.05, 0.05))
    diffuse = EditorField("vec3", vec3(1.0, 1.0, 1.0))
    specular = EditorField("vec3", vec3(1.0, 1.0, 1.0))

    intensity = EditorField("float", 1)
    color = EditorField("vec3", vec3())

    range = EditorField("float", 1)

    constant = EditorField("float", 1.0)
    linear = EditorField("float", 0.09)
    quadratic = EditorField("float", 0.032)

    def __init__(self, gameobject):
        super().__init__(gameobject)  

class Spotlight(Behavior):
    ambient = EditorField("vec3", vec3(0.05, 0.05, 0.05))
    diffuse = EditorField("vec3", vec3(1.0, 1.0, 1.0))
    specular = EditorField("vec3", vec3(1.0, 1.0, 1.0))

    intensity = EditorField("float", 1)
    color = EditorField("vec3", vec3(1, 1, 1))

    direction = EditorField("vec3", vec3())
    range = EditorField("float", 1)
    cutOff = EditorField("float", 1)
    outerCutOff = EditorField("float", 1)

    constant = EditorField("float", 1.0)
    linear = EditorField("float", 0.09)
    quadratic = EditorField("float", 0.032)

    def __init__(self, gameobject):
        super().__init__(gameobject)

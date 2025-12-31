from .behavior import *
from pyglm.glm import vec3, quat
from enum import Enum

class Pointlight(Behavior):
    category = "Rendering"
    ambient = EditorField("vec3", vec3())
    diffuse = EditorField("vec3", vec3())
    specular = EditorField("vec3", vec3())

    intensity = EditorField("float", 1)
    color = EditorField("vec3", vec3())

    range = EditorField("float", 1)

    def __init__(self, gameobject):
        super().__init__(gameobject)  

        self.constant = 0.0
        self.linear = 0.0
        self.quadratic = 0.0

class Spotlight(Behavior):
    ambient = EditorField("vec3", vec3())
    diffuse = EditorField("vec3", vec3())
    specular = EditorField("vec3", vec3())

    intensity = EditorField("float", 1)
    color = EditorField("vec3", vec3())

    direction = EditorField("vec3", vec3())
    range = EditorField("float", 1)
    cutOff = EditorField("float", 1)
    outerCutOff = EditorField("float", 1)

    def __init__(self, gameobject):
        super().__init__(gameobject)

        self.constant = 0.0
        self.linear = 0.0
        self.quadratic = 0.0

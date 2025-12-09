from .behavior import Behavior
from pyglm.glm import vec3, quat
from enum import Enum

class light(Behavior):
    def __init__(self, gameobject):
        super().__init__(gameobject)

        # Shared light data
        self.ambient = vec3()
        self.diffuse = vec3()
        self.specular = vec3()

        self.intensity = 0
        self.color = vec3()

class Pointlight(light):
    def __init__(self, gameobject):
        super().__init__(gameobject)

        self.constant = 0.0
        self.linear = 0.0
        self.quadratic = 0.0

class Spotlight(light):
    def __init__(self, gameobject):
        super().__init__(gameobject)
        
        self.direction = vec3()
        self.range = 1.0
        self.cutOff = 0.0
        self.outerCutOff = 0.0

        self.constant = 0.0
        self.linear = 0.0
        self.quadratic = 0.0

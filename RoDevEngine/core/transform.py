from typing_extensions import overload
from pyglm import glm

import numpy as np

class Transform:
    def __init__(self, pos: glm.vec3 = glm.vec3(0.0),
                       rot: glm.vec3 = glm.vec3(0),
                       scale: glm.vec3 = glm.vec3(1.0),
                       parent = None):
        self.__pos = pos

        self.__rot = rot

        self.scale = scale

        self.__parent = parent
        self.gameobject = None

    @property
    def pos(self):
        if self.__parent:
            return self.__parent.pos + (self.__parent.rot * self.localpos)

        return self.__pos 
    
    @property
    def localpos(self):
        return self.__pos
    
    @localpos.setter
    def localpos(self, value):
        self.__pos = value

    @property
    def quaternion_rot(self):
        return glm.quat(glm.radians(self.__rot))
    
    @property
    def rot(self):
        if self.__parent:
            return self.quaternion_rot * self.parent.rot
        
        return self.quaternion_rot
    
    @property
    def worldrot(self) -> glm.vec3:
        if self.__parent:
            return self.__rot + self.parent.worldrot
        
        return self.__rot
    
    @property
    def localrot(self):
        return self.__rot

    @localrot.setter
    def localrot(self, value):
        self.__rot = value
    
    @property
    def local_quatrot(self):
        return glm.quat(glm.radians(self.__rot))

    @property
    def parent(self):
        return self.__parent
    
    @parent.setter
    def parent(self, value):
        self.__parent = value

    def get_model_matrix(self) -> glm.mat4:
        # Start with identity
        model = glm.mat4(1.0)

        # Apply translation
        model = glm.translate(model, self.pos)

        # Apply rotation (convert quaternion to mat4)
        model = model * glm.mat4_cast(self.rot)

        # Apply scale
        model = glm.scale(model, self.scale)

        return model

    @property
    def front(self):
        rot: glm.vec3 = glm.radians(self.worldrot)
        rot -= glm.radians(glm.vec3(0, 270, 0))

        front = glm.vec3()
        front.x = np.cos(rot.y) * np.cos(rot.x)
        front.y = np.sin(rot.x)
        front.z = np.sin(rot.y) * np.cos(rot.x)

        return glm.normalize(front) * glm.quat(glm.radians(glm.vec3(0, 0, 0)))
    
    @property
    def forward(self):
        return self.front

    def move(self, dx: float = 0, dy: float = 0, dz: float = 0):
        delta = glm.vec3(dx, dy, dz)

        self.__pos += delta

    def move_by_vec3(self, delta: glm.vec3): 
        self.__pos += delta

    @overload
    def move_with_rotation(self, dx:float, dy:float, dz:float): ...

    @overload
    def move_with_rotation(self, delta: glm.vec3): ...

    def move_with_rotation(self, dx: float = 0, dy: float = 0, dz: float = 0, delta: glm.vec3 = glm.vec3(0)):
        if delta == glm.vec3(0):
            delta = glm.vec3(dx, dy, dz)

        self.__pos += delta * self.rot

    @overload
    def rotate_by_degrees(self, dx: float, dy: float, dz: float): ...

    @overload
    def rotate_by_degrees(self, degrees: glm.vec3): ...

    def rotate_by_degrees(self, dx: float = 0, dy: float = 0, dz: float = 0, degrees: glm.vec3 = glm.vec3(0)):
        if degrees == glm.vec3(0):
            degrees = glm.vec3(dx, dy, dz)

        self.__rot += degrees


from typing_extensions import overload
from pyglm import glm

class Transform:
    def __init__(self, pos: glm.vec3 = glm.vec3(0.0),
                       rot: glm.vec3 = glm.vec3(0),
                       scale: glm.vec3 = glm.vec3(1.0),
                       parent = None):
        self.__pos = pos
        # Convert to radians
        pitch_rad, yaw_rad, roll_rad = glm.radians(rot.x), glm.radians(rot.y), glm.radians(rot.z)

        # Create quaternion from Euler angles
        self.__rot = glm.quat(glm.vec3(pitch_rad, yaw_rad, roll_rad))

        self.scale = scale

        self.__parent = parent

    @property
    def pos(self):
        if self.__parent:
            return self.__pos + self.__parent.pos

        return self.__pos 
    
    @property
    def rot(self):
        if self.__parent:
            return self.__rot * self.parent.rot
        
        return self.__rot

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

    @overload
    def move(self, dx:float, dy:float, dz:float): ...

    @overload
    def move(self, delta: glm.vec3): ...

    def move(self, dx: float = 0, dy: float = 0, dz: float = 0, delta: glm.vec3 = glm.vec3(0)):
        if delta == glm.vec3(0):
            delta = glm.vec3(dx, dy, dz)

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
            
        radians = glm.radians(degrees)
        quat = glm.quat(radians)

        self.__rot = quat * self.__rot


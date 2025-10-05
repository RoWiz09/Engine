from pyglm import glm

class Transform:
    def __init__(self, pos: glm.vec3 = glm.vec3(0.0),
                       rot: glm.quat = glm.quat(),
                       scale: glm.vec3 = glm.vec3(1.0)):
        self.pos = pos
        self.rot = rot
        self.scale = scale

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


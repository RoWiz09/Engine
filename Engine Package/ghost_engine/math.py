from pyglm import glm

class Vector3:
    @staticmethod
    def distance(vector_a: glm.vec3, vector_b: glm.vec3):
        glm.distance(vector_a, vector_b)

def clamp(min_val, max_val, val):
    return min(max(min_val, val), max_val)
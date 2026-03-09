from .behavior import Behavior, EditorField
from .collider import CubeCollider

from pyglm import glm

class Rigidbody(Behavior):
    velocity = glm.vec3(0)

    gravity = EditorField("float", -9.8)

    friction = EditorField("float", 5)
    mass = EditorField("float", 1)
    def __init__(self, gameobject):
        super().__init__(gameobject)

        self.grounded = False
        self.time_when_last_grounded = 0

    def update(self, dt: float):
        self.gameobject.transform.move_by_vec3(self.velocity * dt)

        if not self.grounded:
            self.velocity.y += self.gravity * dt

        else:
            length = glm.length(self.velocity)
            if (length > 0.00001):
                direction = glm.normalize(self.velocity)
                n = self.mass * self.gravity
                a = (self.friction / n) * 30 * dt

                length_a = glm.length(glm.vec3(a) * direction)

                if length < length_a:
                    self.velocity = glm.vec3(0)
                else:
                    self.velocity += glm.vec3(a) * direction

    def on_collision_start(self, other):
        self.grounded = True

        if self.velocity.y < 0:
            self.velocity.y = 0
    
    def on_collision_exit(self, other):
        self.grounded = False

        if self.velocity.y < 0:
            self.velocity.y = 0

    def add_force_vector(self, force: glm.vec3):
        self.velocity += force
        if self.velocity.y > 0:
            self.grounded = False
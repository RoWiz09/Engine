from ghost_engine.scripting.behavior import *
from ghost_engine.scripting.collider_type import CollisionInfo
from .mesh_collider import MeshCollider

from pyglm import glm
from enum import Enum

class Rigidbody(Behavior, PhysicsBehavior):
    velocity = glm.vec3(0)

    gravity = EditorField(float, -9.8)
    friction = EditorField(float, 5)
    mass = EditorField(float, 1)

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

    def add_force(self, vector: glm.vec3):
        self.velocity += vector
        if self.velocity.y > 0:
            self.grounded = False

    def handle_collision(self, info: CollisionInfo, reground: bool = False):
        epa_info = MeshCollider.expand_polytope(info)
        self.gameobject.transform.move_by_vec3(
            epa_info.normal * epa_info.depth
        )

        vn = glm.dot(self.velocity, epa_info.normal)
        if vn > 0:
            self.velocity -= epa_info.normal * vn

        if epa_info.normal.y < -0.5 and reground:
            self.grounded = True

    def on_collision_start(self, other):
        self.handle_collision(other, True)
        
    # def on_collision(self, other):
    #     self.handle_collision(other)

    def on_collision_exit(self, other):
        self.grounded = False

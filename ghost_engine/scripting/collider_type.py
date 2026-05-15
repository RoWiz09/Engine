from __future__ import annotations
from .behavior import EditorField
from ..object import Object

from dataclasses import dataclass
from pyglm import glm

@dataclass
class CollisionInfo:
    source_collider: ColliderType
    gameobject: Object
    other_collider: ColliderType

    simplex: list[glm.vec3]

class ColliderType:
    collisions_this_frame = []
    collisions_last_frame = []

    triggers_this_frame = []
    triggers_last_frame = []

    last_simplex: list[glm.vec3] = []

    def __init_subclass__(cls):
        field = EditorField(bool, False)
        setattr(cls, "Trigger Collider", field)

    def get_last_simplex(self):
        return self.last_simplex
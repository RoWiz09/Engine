from __future__ import annotations

from .behavior import Behavior, EditorField
from ..object import Object

from pyglm.glm import vec3


class CubeCollider(Behavior):
    collisions_this_frame = []
    collisions_last_frame = []

    triggers_this_frame = []
    triggers_last_frame = []
    category = "Physics"

    scale_factor = EditorField("vec3", vec3(1))
    pos_offset = EditorField("vec3", vec3(0))
    trigger_collider = EditorField("bool", False)

    run_in_editor = True

    def __init__(self, gameobject: Object):
        super().__init__(gameobject)

    def get_bounds(self) -> tuple[vec3, vec3]:
        if not isinstance(self.scale_factor, vec3):
            self.scale_factor = vec3(*self.scale_factor)
        center = self.gameobject.transform.pos + self.pos_offset
        half   = self.scale_factor * 0.5

        min_v = center - half
        max_v = center + half

        return min_v, max_v

    @staticmethod
    def aabb_overlap(min_a: vec3, max_a: vec3,
                     min_b: vec3, max_b: vec3) -> bool:
        return (
            min_a.x <= max_b.x and max_a.x >= min_b.x and
            min_a.y <= max_b.y and max_a.y >= min_b.y and
            min_a.z <= max_b.z and max_a.z >= min_b.z
        )

    def check_collision(self, other: CubeCollider) -> bool:
        min_a, max_a = self.get_bounds()
        min_b, max_b = other.get_bounds()

        return self.aabb_overlap(min_a, max_a, min_b, max_b)
    
    @classmethod
    def on_frame_start(cls):
        cls.collisions_last_frame = cls.collisions_this_frame.copy()
        cls.collisions_this_frame.clear()

        cls.triggers_last_frame = cls.triggers_this_frame.copy()
        cls.triggers_this_frame.clear()

    def update(self, dt):
        from ..core.scene_manager import SceneManager

        for obj in SceneManager().get_objects_with_component(CubeCollider):
            if obj is self.gameobject:
                continue

            for collider in obj.get_components(CubeCollider):
                if not [self, collider] in CubeCollider.collisions_this_frame and not [self, collider] in CubeCollider.collisions_this_frame:
                    if self.check_collision(collider):
                        if not any([self.trigger_collider, collider.trigger_collider]):
                            CubeCollider.collisions_this_frame.append([self, collider])
                        else:
                            CubeCollider.triggers_this_frame.append([self, collider])

                if not any([self.trigger_collider, collider.trigger_collider]):
                    in_this_frame = [self, collider] in CubeCollider.collisions_this_frame
                    in_last_frame = [self, collider] in CubeCollider.collisions_last_frame

                    if in_this_frame and not in_last_frame:
                        for component in self.gameobject.components:
                            component.on_collision_start(collider.gameobject)
                    elif in_this_frame:
                        for component in self.gameobject.components:
                            component.on_collision(collider.gameobject)
                    elif not in_this_frame and in_last_frame:
                        for component in self.gameobject.components:
                            component.on_collision_exit(collider.gameobject)
                            
                else:
                    in_this_frame = [self, collider] in CubeCollider.triggers_this_frame
                    in_last_frame = [self, collider] in CubeCollider.triggers_last_frame

                    if in_this_frame and not in_last_frame:
                        for component in self.gameobject.components:
                            component.on_trigger_start(collider.gameobject)
                    elif in_this_frame and in_last_frame:
                        for component in self.gameobject.components:
                            component.on_trigger(collider.gameobject)
                    elif not in_this_frame and in_last_frame:
                        for component in self.gameobject.components:
                            component.on_trigger_exit(collider.gameobject)
    
    def on_collision_start(self, other):
        print("WOW!")
        return super().on_collision_start(other)

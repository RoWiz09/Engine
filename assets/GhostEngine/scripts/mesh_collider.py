from __future__ import annotations

from ghost_engine.core.packer import Pack
from ghost_engine.core.scene_manager import SceneManager
from pathlib import Path

from ghost_engine.datatypes.model_type import Model

from ghost_engine.scripting.behavior import Behavior, EditorField, InitMethod, PhysicsBehavior
from ghost_engine.scripting.collider_type import ColliderType, CollisionInfo

from ghost_engine.object import GameObject

from ghost_engine.math import triple_product

from ghost_engine.core.logger import Logger
from enum import Enum
from pyglm import glm
from dataclasses import dataclass, field

INFINITY = float("inf")
class EvolveResult(Enum):
    STILL_EVOLVING = 0
    NO_INTERSECTION = 1
    FOUND_INTERSECTION = 2

@dataclass
class Face:
    indices: tuple[int, int, int]
    normal: glm.vec3
    distance: float

@dataclass
class EPAOutput:
    normal: glm.vec3
    depth: float

MAX_ITERS = 25
class MeshCollider(Behavior, ColliderType):
    mesh = EditorField(Model, "")

    def __init__(self, gameobject):
        super().__init__(gameobject)

        self.mesh_verts: list[glm.vec3] = []

        self.__last_mesh_verts = self.mesh_verts.copy()
        self.__last_transform_state = gameobject.transform.copy_state()
    
    @property
    def needs_update(self):
        return (
            self.__last_transform_state != self.gameobject.transform.copy_state() or
            self.__last_mesh_verts != self.mesh_verts
        ) and self.mesh_verts != []

    @InitMethod
    def create_mesh_collider(cls: type[MeshCollider], file_path: str, game_object: GameObject):
        inst = cls(game_object)
        inst.load(file_path)

        return inst

    @create_mesh_collider.refresh_vars
    def load(self, file_path):
        self.mesh = file_path
        path = Path(file_path)
        
        data = Pack().get_contents(path)
        lines = data.splitlines()

        verts = []
        for line in lines:
            if not line.startswith("v "):
                continue
        
            verts_ = line.split()[1:4]
            point = glm.vec3([float(x) for x in verts_])
            verts.append(point)

        self.mesh_verts = verts

    def center(self):
        min_max_x = [INFINITY, -INFINITY]
        min_max_y = [INFINITY, -INFINITY]
        min_max_z = [INFINITY, -INFINITY]

        for v in self.mesh_verts:
            v = v * self.gameobject.transform.scale
            v = self.gameobject.transform.rot * v
            v += self.gameobject.transform.pos

            if min_max_x[0] > v.x:
                min_max_x[0] = v.x

            if min_max_x[1] < v.x:
                min_max_x[1] = v.x

            if min_max_y[0] > v.y:
                min_max_y[0] = v.y

            if min_max_y[1] < v.y:
                min_max_y[1] = v.y

            if min_max_z[0] > v.z:
                min_max_z[0] = v.z

            if min_max_z[1] < v.z:
                min_max_z[1] = v.z

        return glm.vec3(
            (min_max_x[0] + min_max_x[1]) / 2,
            (min_max_y[0] + min_max_y[1]) / 2,
            (min_max_z[0] + min_max_z[1]) / 2
        )

    @classmethod
    def calculate_simplex(cls, mesh_a: MeshCollider, mesh_b: MeshCollider, verts: list[glm.vec3]) -> EvolveResult:
        direction = None
        match len(verts):
            case 0:
                # First Vertex
                direction = mesh_b.center() - mesh_a.center()

                if glm.length2(direction) == 0:
                    direction = glm.vec3(1, 0, 0)

            case 1:
                # Second Vertex
                a: glm.vec3 = verts[0]
                direction = -a

            case 2:
                # Third Vertex
                b: glm.vec3 = verts[1]
                c: glm.vec3 = verts[0]

                cb: glm.vec3 = b - c
                c0: glm.vec3 = c * -1
                
                direction = triple_product(cb, c0, cb)
                if glm.length2(direction) < 1e-8:
                    direction = glm.cross(cb, glm.vec3(0, 1, 0))
                    
            case 3:
                # Fourth vertex
                ac: glm.vec3 = verts[2] - verts[0]
                ab: glm.vec3 = verts[1] - verts[0]
                direction = glm.cross(ac, ab)

                a0: glm.vec3 = verts[0] * -1
                if glm.dot(a0, direction) < 0:
                    direction *= -1

            case 4:
                da = verts[3] - verts[0]
                db = verts[3] - verts[1]
                dc = verts[3] - verts[2]

                d0 = verts[3] * -1
                
                abdNorm: glm.vec3 = glm.cross(da, db)
                bcdNorm: glm.vec3 = glm.cross(db, dc)
                cadNorm: glm.vec3 = glm.cross(dc, da)

                if(glm.dot(abdNorm, d0) > 0):
                    verts.pop(2)
                    direction = abdNorm
            
                elif(glm.dot(bcdNorm, d0) > 0):
                    verts.pop(0)
                    direction = bcdNorm
            
                elif(glm.dot(cadNorm, d0) > 0):
                    verts.pop(1)
                    direction = cadNorm
            
                else:
                    return EvolveResult.FOUND_INTERSECTION

        return EvolveResult.STILL_EVOLVING if cls.add_support(mesh_a, mesh_b, verts, direction) else EvolveResult.NO_INTERSECTION

    @staticmethod
    def add_support(mesh_a: MeshCollider, mesh_b: MeshCollider, verts: list[glm.vec3], direction:glm.vec3) -> bool:
        new_vertex: glm.vec3 = mesh_a.support(direction) - mesh_b.support(-1 * direction)
        verts.append(new_vertex)
        return glm.dot(direction, new_vertex) > 0

    def test(self, mesh_b: MeshCollider):
        verts = []

        iters = 0
        res = EvolveResult.STILL_EVOLVING
        while res == EvolveResult.STILL_EVOLVING and iters < MAX_ITERS:
            res = self.calculate_simplex(self, mesh_b, verts)
            iters += 1

        collision = res == EvolveResult.FOUND_INTERSECTION
        if collision:
            MeshCollider.collisions_this_frame.append((self, mesh_b))
            self.last_simplex = verts

    @classmethod
    def on_frame_start(cls):
        cls.collisions_last_frame = cls.collisions_this_frame
        cls.collisions_this_frame = []

    def support(self, direction: glm.vec3) -> glm.vec3:
        if self.mesh_verts == []:
            Logger("MESH COLLISION").log_fatal("Tried to find support for an empty mesh!")

        furthest_dist = -INFINITY
        furthest_vert = None

        for v in self.mesh_verts:
            dist = glm.dot(v, direction)
            if dist > furthest_dist:
                furthest_dist = dist
                furthest_vert = v

        v = furthest_vert * self.gameobject.transform.scale
        v = self.gameobject.transform.rot * v
        v += self.gameobject.transform.pos

        return v
    
    def update(self, dt):
        for obj in GameObject.find_with_behavior(MeshCollider):
            colliders = obj.get_behaviors(MeshCollider)
            for collider in colliders:
                if collider == self:
                    continue

                if collider.mesh_verts == []:
                    continue
                
                if (collider, self) in MeshCollider.collisions_this_frame:
                    # This (possible) collision has already been computed!
                    continue
                
                if self.needs_update or collider.needs_update:
                    self.test(collider)
                    self.__handle_behavior_updates(collider)
                    self.last_simplex = []

    @staticmethod
    def create_face(vertices: list[glm.vec3], a: int, b: int, c: int) -> Face:
        va = vertices[a]
        vb = vertices[b]
        vc = vertices[c]

        ab = vb - va
        ac = vc - va

        normal = glm.cross(ab, ac)

        if glm.length2(normal) < 1e-8:
            normal = glm.vec3(0, 1, 0)
        else:
            normal = glm.normalize(normal)

        # Ensure outward normal
        if glm.dot(normal, va) < 0:
            normal *= -1
            b, c = c, b

        distance = glm.dot(normal, va)

        return Face((a, b, c), normal, distance)

    @staticmethod
    def support_point(mesh_a, mesh_b, direction):
        return mesh_a.support(direction) - mesh_b.support(-direction)

    @staticmethod
    def find_closest_face(faces: list[Face]) -> Face:
        closest = faces[0]

        for face in faces:
            if face.distance < closest.distance:
                closest = face

        return closest

    @classmethod
    def expand_polytope(cls, collision_info: CollisionInfo, tolerance=0.0001):
        vertices = collision_info.simplex.copy()

        if len(vertices) < 4:
            return EPAOutput(glm.vec3(0), 0)

        faces = [
            cls.create_face(vertices, 0, 1, 2),
            cls.create_face(vertices, 0, 3, 1),
            cls.create_face(vertices, 0, 2, 3),
            cls.create_face(vertices, 1, 3, 2),
        ]

        iterations = 0

        while iterations < MAX_ITERS:
            iterations += 1

            closest = cls.find_closest_face(faces)

            support = cls.support_point(
                collision_info.source_collider,
                collision_info.other_collider,
                closest.normal
            )

            support_distance = glm.dot(closest.normal, support)

            if support_distance - closest.distance < tolerance:
                return EPAOutput(
                    closest.normal,
                    support_distance
                )

            new_index = len(vertices)
            vertices.append(support)

            visible_faces = []

            for face in faces:
                a = vertices[face.indices[0]]

                if glm.dot(face.normal, support - a) > 0:
                    visible_faces.append(face)

            edges = {}

            def add_edge(a, b):
                if (b, a) in edges:
                    del edges[(b, a)]
                else:
                    edges[(a, b)] = True

            for face in visible_faces:
                i0, i1, i2 = face.indices

                add_edge(i0, i1)
                add_edge(i1, i2)
                add_edge(i2, i0)

            for face in visible_faces:
                faces.remove(face)

            for edge in edges.keys():
                a, b = edge
                new_face = cls.create_face(vertices, a, b, new_index)
                faces.append(new_face)

        closest = cls.find_closest_face(faces)
        return EPAOutput(closest.normal, closest.distance)

    def __handle_behavior_updates(self, other):
        this_frame = (self, other) in MeshCollider.collisions_this_frame
        last_frame = (self, other) in MeshCollider.collisions_last_frame
        if not (this_frame or last_frame):
            return
        
        info = CollisionInfo(self, other.gameobject, other, self.last_simplex)
        for behavior in filter(lambda c: issubclass(type(c), PhysicsBehavior),
                               self.gameobject.behaviors):
            
            behavior: PhysicsBehavior
            if this_frame and not last_frame:
                behavior.on_collision_start(info)

            elif this_frame and last_frame:
                behavior.on_collision(info)

            elif not this_frame and last_frame:
                behavior.on_collision_exit(info)            


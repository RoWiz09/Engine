from .core.logger import Logger

from typing_extensions import overload 
from dataclasses import dataclass, field
from pyglm import glm

import OpenGL.GL as GL
import numpy as np
import hashlib

class MeshBuilder:
    class Mesh:
        MESH_REGISTRY = {}
        def __new__(cls, verts: list[float], indices: list[int]):
            mesh_data = (
                np.array(verts, dtype=np.float32).tobytes() +
                np.array(indices, dtype=np.uint32).tobytes()
            )
            mesh_id = hashlib.sha1(mesh_data).hexdigest()

            if mesh_id in cls.MESH_REGISTRY: 
                return cls.MESH_REGISTRY[mesh_id]
            
            inst = super().__new__(cls)
            inst._needs_gpu_upload = True
            inst._mesh_id = mesh_id
            cls.MESH_REGISTRY[mesh_id] = inst
            return inst

        def __init__(self, verts: list[float], indices: list[int]):
            if not getattr(self, "_needs_gpu_upload", False):
                return
            
            self.vertices = np.array(verts, dtype=np.float32)
            self.indices = np.array(indices, dtype=np.uint32)
            
            self.vao = GL.glGenVertexArrays(1)
            self.vbo = GL.glGenBuffers(1)
            self.ebo = GL.glGenBuffers(1)

            GL.glBindVertexArray(self.vao)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
            GL.glBufferData(GL.GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL.GL_STATIC_DRAW)

            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
            GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL.GL_STATIC_DRAW)

            stride = 32

            # position (vec3) at location=0
            GL.glEnableVertexAttribArray(0)
            GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, GL.ctypes.c_void_p(0))

            # normal (vec3) at location=1
            GL.glEnableVertexAttribArray(1)
            GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, GL.ctypes.c_void_p(3 * 4))

            # texcoord (vec2) at location=2
            GL.glEnableVertexAttribArray(2)
            GL.glVertexAttribPointer(2, 2, GL.GL_FLOAT, GL.GL_FALSE, stride, GL.ctypes.c_void_p(6 * 4))
            
            GL.glBindVertexArray(0)

            self._needs_gpu_upload = False
            self._mesh_id = None

        def render(self):
            GL.glBindVertexArray(self.vao)
            GL.glDrawElements(GL.GL_TRIANGLES, len(self.indices), GL.GL_UNSIGNED_INT, None)
            GL.glBindVertexArray(0)

        def delete(self):
            GL.glDeleteVertexArrays(1, [self.vao])
            GL.glDeleteBuffers(1, [self.vbo])
            GL.glDeleteBuffers(1, [self.ebo])

            del MeshBuilder.Mesh.MESH_REGISTRY[self._mesh_id]

    @dataclass
    class VertexProvider:
        position: tuple[float, float, float]
        uv: tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
        normal: tuple[float, float, float] = field(default_factory=lambda: (0.0, 0.0, 0.0))

        index: int = 0

        def set_uv(self, u: float|glm.vec2 = 0.0, v: float|None = None):
            if isinstance(u, glm.vec2):
                self.uv = (u.x, u.y)
            
            else:
                self.uv = (u, v)

            return self

        def set_normal(self, x: float|glm.vec3 = 0.0, y: float|None = None, z: float|None = None):
            if isinstance(x, glm.vec3):
                self.normal = (x.x, x.y, x.z)

            else:
                self.normal = (x, y, z)

            return self


    def __init__(self):        
        self.logger = Logger("MESH BUILDER")

        self.vertices: list[MeshBuilder.VertexProvider] = []
        self.indices: list[int] = []
        self.logger.log_debug("Initalized new mesh builder!")

    def add_vertex(self, x: float | glm.vec3 = 0.0, y: float | None = None, z: float | None = None) -> VertexProvider:
        if isinstance(x, glm.vec3):
            vertex = self.VertexProvider((x.x, x.y, x.z))
        else:
            vertex = self.VertexProvider((x, y if y is not None else 0.0, z if z is not None else 0.0))
        
        vertex.index = len(self.vertices)
        self.vertices.append(vertex)
        return vertex
    
    def add_triangle(self, i1: int, i2: int, i3: int):
        self.indices.extend([i1, i2, i3])
        return self

    def bulk_load(self, vertices: list[tuple], indices: list[int]):
        self.vertices.clear()
        self.indices.clear()
        
        def parse_vertex(vert: tuple[float, float, float, float, float, float, float, float]):
            vertex = self.VertexProvider(vert[:3], vert[3:5], vert[5:8])
            return vertex
        
        verts: list[MeshBuilder.VertexProvider] = []
        for vert in vertices:
            verts.append(parse_vertex(vert))
        self.vertices.extend(verts)

        self.indices.extend(indices)
        for index in indices:
            verts[index].index = index

        return self

    def build_mesh(self):
        """
            Builds a mesh object and wipes the internal buffers.
        """

        verts = []
        for vertex in self.vertices:
            verts.extend((
                *vertex.position,
                *vertex.normal,
                *vertex.uv
            ))

        mesh = self.Mesh(verts, self.indices)

        self.vertices.clear()
        self.indices.clear()
        return mesh
    
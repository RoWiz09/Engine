from .behavior import Behavior, EditorField, init_method, register_editor_button
from ..core.logger import Logger

from ..core.packer import Pack

from ..object import Object
from ..rendering.material import Material
from OpenGL import GL
import pyglm.glm as glm
import numpy as np
import hashlib

import os

class Mesh(Behavior):
    category = "Rendering"

    # Class-level registry for shared mesh data
    _mesh_registry = {}

    mesh_path = EditorField('str', "")
    mesh_name = EditorField('str', "")

    def __init__(self, gameobject):
        super().__init__(gameobject)
        self._run_in_editor = True

        self.submeshes: list[Submesh] = []

    @init_method
    def create_from_obj(cls, file_path: str, file_name: str, game_object: Object):
        submeshes = []
        cur_mesh = None

        positions = []
        normals = []
        tex_coords = []

        vertices = []   # interleaved vertex data
        indices = []

        vertex_map = {}  # (v, vt, vn) -> index

        lines = []
        if not "compiled" in os.environ.keys():
            with open(os.path.join(*file_path.split("."), file_name)) as file:
                lines = file.readlines()
        else:
            pack = Pack()
            lines = pack.get_string(os.path.join(*file_path.split("."), file_name)).splitlines()

        for line in lines:
            if line.startswith("o "):
                if cur_mesh:
                    cur_mesh.indices = indices
                    cur_mesh.vertices = vertices

                    cur_mesh._create_or_get_buffers()

                    submeshes.append(cur_mesh)
                
                positions.clear()
                normals.clear()
                tex_coords.clear()

                vertices.clear()
                indices.clear()

                vertex_map.clear()

                cur_mesh = Submesh(game_object)

            elif line.startswith("v "):
                positions.append(tuple(map(float, line.split()[1:4])))

            elif line.startswith("vn "):
                normals.append(tuple(map(float, line.split()[1:4])))

            elif line.startswith("vt "):
                tex_coords.append(tuple(map(float, line.split()[1:3])))

            elif line.startswith("f "):
                face = line.split()[1:]

                # triangulate face (fan method)
                for i in range(1, len(face) - 1):
                    for vert in (face[0], face[i], face[i + 1]):

                        parts = vert.split("/")
                        v = int(parts[0]) - 1
                        vt = int(parts[1]) - 1 if len(parts) > 1 and parts[1] else None
                        vn = int(parts[2]) - 1 if len(parts) > 2 and parts[2] else None

                        key = (v, vt, vn)
                        if key not in vertex_map:
                            px, py, pz = positions[v]

                            if vt is not None:
                                u, v_ = tex_coords[vt]
                            else:
                                u, v_ = 0.0, 0.0

                            if vn is not None:
                                nx, ny, nz = normals[vn]
                            else:
                                nx, ny, nz = 0.0, 0.0, 0.0

                            vertex_map[key] = len(vertices) // 8
                            vertices.extend([
                                px, py, pz,
                                nx, ny, nz,
                                u, v_
                            ])

                        indices.append(vertex_map[key])

        cur_mesh.indices = indices
        cur_mesh.vertices = vertices

        cur_mesh._create_or_get_buffers()

        submeshes.append(cur_mesh)

        mesh = cls(game_object)
        mesh.submeshes = submeshes

        mesh.mesh_name = file_name
        mesh.mesh_path = file_path

        return mesh
    
    @register_editor_button
    def refresh(self):
        self.reload_obj(self.mesh_path, self.mesh_name)

    @create_from_obj.refresh_vars
    def reload_obj(self, file_path, file_name):
        submeshes = []
        cur_mesh = None

        positions = []
        normals = []
        tex_coords = []

        vertices = []
        indices = []

        vertex_map = {}  # v, vn, vt

        lines = []

        if not "compiled" in os.environ.keys():
            with open(os.path.join(*file_path.split("."), file_name)) as file:
                lines = file.readlines()
        else:
            pack = Pack()
            lines = pack.get_string(os.path.join(*file_path.split("."), file_name)).splitlines()

        for line in lines:
            if line.startswith("o "):
                if cur_mesh:
                    cur_mesh.indices = indices
                    cur_mesh.vertices = vertices

                    cur_mesh._create_or_get_buffers()

                    submeshes.append(cur_mesh)

                    break
                
                positions.clear()
                normals.clear()
                tex_coords.clear()

                vertices.clear()
                indices.clear()

                vertex_map.clear()

                cur_mesh = Submesh(self.gameobject)

            elif line.startswith("v "):
                positions.append(tuple(map(float, line.split()[1:4])))

            elif line.startswith("vn "):
                normals.append(tuple(map(float, line.split()[1:4])))

            elif line.startswith("vt "):
                tex_coords.append(tuple(map(float, line.split()[1:3])))

            elif line.startswith("f "):
                face = line.split()[1:]

                # triangulate face (fan method)
                for i in range(1, len(face) - 1):
                    for vert in (face[0], face[i], face[i + 1]):

                        parts = vert.split("/")
                        v = int(parts[0]) - 1
                        vt = int(parts[1]) - 1 if len(parts) > 1 and parts[1] else None
                        vn = int(parts[2]) - 1 if len(parts) > 2 and parts[2] else None

                        key = (v, vt, vn)
                        if key not in vertex_map:
                            px, py, pz = positions[v]

                            if vt is not None:
                                u, v_ = tex_coords[vt]
                            else:
                                u, v_ = 0.0, 0.0

                            if vn is not None:
                                nx, ny, nz = normals[vn]
                            else:
                                nx, ny, nz = 0.0, 0.0, 0.0

                            vertex_map[key] = len(vertices) // 8
                            vertices.extend([
                                px, py, pz,
                                nx, ny, nz,
                                u, v_
                            ])

                        indices.append(vertex_map[key])

        cur_mesh.indices = indices
        cur_mesh.vertices = vertices

        cur_mesh._create_or_get_buffers()

        submeshes.append(cur_mesh)

        self.submeshes = submeshes
    
    def update(self, dt):
        if not self.enabled:
            return
        
        for mesh in self.submeshes:
            mesh.update()

class Submesh:
    def __init__(self, gameobject):
        self.gameobject = gameobject
        
        self.vertices = None
        self.indices = None
        self.mesh_id = None
        self.vao = None
        self.vbo = None
        self.ebo = None

        self.render_mat: Material = None

    def _create_or_get_buffers(self):
        """Creates or retrieves shared VAO/VBO/EBO for this mesh data."""
        if self.vertices is None or self.indices is None:
            Logger("CORE").log_fatal("Mesh vertices or indices not set.")

        # Generate a hash of the vertex/index data
        mesh_data = (
            np.array(self.vertices).tobytes() +
            np.array(self.indices).tobytes()
        )
        mesh_id = hashlib.sha1(mesh_data).hexdigest()

        if mesh_id in Mesh._mesh_registry:
            shared = Mesh._mesh_registry[mesh_id]
        else:
            vao = GL.glGenVertexArrays(1)
            vbo = GL.glGenBuffers(1)
            ebo = GL.glGenBuffers(1)

            GL.glBindVertexArray(vao)

            # Upload vertex data (interleaved layout: pos, normal, uv)
            vertex_data = np.array(self.vertices, dtype=np.float32)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
            GL.glBufferData(GL.GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL.GL_STATIC_DRAW)

            # Upload index data
            index_data = np.array(self.indices, dtype=np.uint32)
            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, ebo)
            GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, index_data.nbytes, index_data, GL.GL_STATIC_DRAW)

            stride = 8 * 4  # 8 floats per vertex * 4 bytes = 32 bytes

            # --- vertex attributes ---
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

            shared = {"vao": vao, "vbo": vbo, "ebo": ebo, "count": len(self.indices)}
            Mesh._mesh_registry[mesh_id] = shared

        self._mesh_id = mesh_id
        self._vao = shared["vao"]
        self._vbo = shared["vbo"]
        self._ebo = shared["ebo"]

    def update(self):
        if self._vao is None:
            Logger("CORE").log_warning("SubMesh.update called before buffers created. Creating now.")
            self._create_or_get_buffers()

        if self.render_mat:
            self.render_mat.use()

        model = self.gameobject.transform.get_model_matrix()
        self.gameobject.mat.shader.set_mat4("uModel", model)

        GL.glBindVertexArray(self._vao)
        count = Mesh._mesh_registry[self._mesh_id]["count"]
        GL.glDrawElements(GL.GL_TRIANGLES, count, GL.GL_UNSIGNED_INT, None)
        GL.glBindVertexArray(0)


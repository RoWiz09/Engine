from RoDevEngine.scripts.behavior import Behavior
from RoDevEngine.core.logger import Logger
from OpenGL import GL
import numpy as np
import hashlib

class Mesh(Behavior):
    # Class-level registry for shared mesh data
    _mesh_registry = {}

    def __init__(self, gameobject):
        super().__init__(gameobject)
        # These must be set later with setattr()
        self.vertices = None
        self.indices = None
        self._mesh_id = None
        self._vao = None
        self._vbo = None
        self._ebo = None

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

    def on_scene_load(self, scene_info):
        self._create_or_get_buffers()

    def update(self, dt:float):
        if not self.enabled:
            return
        if self._vao is None:
            Logger("CORE").log_warning("Mesh.update called before buffers created. Creating now.")
            self._create_or_get_buffers()

        model = self.gameobject.transform.get_model_matrix()
        self.gameobject.mat.shader.set_mat4("uModel", model)

        GL.glBindVertexArray(self._vao)
        count = Mesh._mesh_registry[self._mesh_id]["count"]
        GL.glDrawElements(GL.GL_TRIANGLES, count, GL.GL_UNSIGNED_INT, None)
        GL.glBindVertexArray(0)

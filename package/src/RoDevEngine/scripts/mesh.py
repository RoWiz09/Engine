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
            # Reuse existing buffers
            shared = Mesh._mesh_registry[mesh_id]
        else:
            # Create VAO/VBO/EBO once
            vao = GL.glGenVertexArrays(1)
            vbo = GL.glGenBuffers(1)
            ebo = GL.glGenBuffers(1)

            GL.glBindVertexArray(vao)

            # Upload vertex data
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
            vertex_data = np.array(self.vertices, dtype=np.float32)
            GL.glBufferData(GL.GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL.GL_STATIC_DRAW)

            # Upload index data
            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, ebo)
            index_data = np.array(self.indices, dtype=np.uint32)
            GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, index_data.nbytes, index_data, GL.GL_STATIC_DRAW)

            # Example: assume vertices contain [x,y,z]
            GL.glEnableVertexAttribArray(0)
            GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 3 * 4, GL.ctypes.c_void_p(0))

            GL.glBindVertexArray(0)

            shared = {"vao": vao, "vbo": vbo, "ebo": ebo, "count": len(self.indices)}
            Mesh._mesh_registry[mesh_id] = shared

        # Store reference
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

        GL.glBindVertexArray(self._vao)
        count = Mesh._mesh_registry[self._mesh_id]["count"]
        GL.glDrawElements(GL.GL_TRIANGLES, count, GL.GL_UNSIGNED_INT, None)
        GL.glBindVertexArray(0)

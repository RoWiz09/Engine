from __future__ import annotations

import OpenGL.GL as gl
import numpy as np
import ctypes
import glfw

from pyglm import glm

from systems.shader_program import ShaderProgram

class WindowDrawer:
    INST = None
    INITALIZED = False
    def __new__(cls) -> WindowDrawer:
        if __class__.INST is None:
            __class__.INST = super().__new__(cls)

        return __class__.INST

    def __init__(self):
        if WindowDrawer.INITALIZED:
            return
        
        setup()
        self.windows: set[EditorUiWindow] = set()

        __class__.INITALIZED = True

    def render(self):
        width, height = glfw.get_window_size(glfw.get_current_context())
        ortho = glm.ortho(0, width, height, 0, -1, 1)

        for window in self.windows:
            window.draw(ortho)

    def add_window_data(self, window_data: EditorUiWindow):
        self.windows.add(window_data)

WINDOW_SHADER = None
VBO, VAO, EBO = None, None, None
def setup():
    global WINDOW_SHADER, VBO, VAO, EBO
    WINDOW_SHADER = ShaderProgram(
        """
            #version 330 core

            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec2 aTexCoords;

            uniform mat4 uModel;
            uniform mat4 uProjection;

            void main() {
                gl_Position = uProjection * uModel * vec4(aPos, 0.0, 1.0);
            }
        """,
        """
            #version 330 core

            out vec4 FragColor;

            void main() {
                FragColor = vec4(1.0, 1.0, 1.0, 1.0);
            }
    """)

    verts = np.array([
        # Pos, UV
        0, 0,  0, 0,
        0, 1,  0, 1,
        1, 1,  1, 1,
        1, 0,  1, 0
    ], dtype=np.float32)

    indices = np.array([
        0, 1, 2,
        0, 2, 3
    ], dtype=np.uint32)


    vao = gl.glGenVertexArrays(1)
    vbo = gl.glGenBuffers(1)
    ebo = gl.glGenBuffers(1)

    gl.glBindVertexArray(vao)

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, verts.nbytes, verts, gl.GL_STATIC_DRAW)

    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
    gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)

    stride = 16 # 4 Floats * 4 Bytes = 16

    gl.glEnableVertexAttribArray(0)
    gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(0))

    gl.glEnableVertexAttribArray(1)
    gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(2 * 4))

    VAO = vao
    VBO = vbo
    EBO = ebo

class EditorUiWindow:
    def __init__(self, name: str):
        self.name = name

        self.draw_data = WindowDrawData(0, 0, 5, 5)
        self.ui_elements = []

    def get_draw_data(self):
        return self.draw_data
    
    def move(self, new_x: float, new_y: float):
        """
            Moves the window to `new_x`, `new_y`. 
            Returns this class for easier method chaining.
        """
        self.draw_data.pos = glm.vec2(new_x, new_y)
        return self

    def resize(self, new_width: float, new_height: float):
        """
            Sets the window size to `new_width`, `new_height`. 
            Returns this class for easier method chaining.
        """
        self.draw_data.size = glm.vec2(new_width, new_height)
        return self

    def draw(self, orthographic: glm.mat4x4):
        global VAO

        WINDOW_SHADER.use()
        WINDOW_SHADER.set_mat4("uModel", self.draw_data.get_configuration_out())
        WINDOW_SHADER.set_mat4("uProjection", orthographic)

        gl.glBindVertexArray(VAO)
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)

class WindowDrawData:
    def __init__(self, x: float, y: float, width: float, height: float):
        self.pos = glm.vec2(x, y)
        self.size = glm.vec2(width, height)

    def get_configuration_out(self):
        model = glm.mat4(1)

        model = glm.translate(model, glm.vec3(*self.pos, 0))
        model = glm.scale(model, glm.vec3(*self.size, 1))

        return model

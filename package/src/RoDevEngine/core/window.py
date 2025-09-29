from __future__ import annotations
from typing_extensions import overload

from RoDevEngine.core.logger import Logger
from RoDevEngine.core.scene_manager import SceneManager
from RoDevEngine.object import Object

import glfw
import sys, os, OpenGL.GL as gl

glfw_initalized = False

def glfw_error_handler(e_code:str, desc:str):
    Logger("CORE").log_fatal(f"GLFW Error [{e_code}] : {desc}")

glfw.set_error_callback(glfw_error_handler)

class Window:
    @overload
    def __init__(self): ...
    @overload
    def __init__(self, width:int, height:int): ...
    @overload
    def __init__(self, width:int, height:int, name:str): ...
    def __init__(self, width=800, height=600, name:str = "GLFW Window"):
        global glfw_initalized

        if not glfw_initalized:
            glfw.init()

        self.logger = Logger("CORE")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        self.window = glfw.create_window(width, height, name, None, None)
        glfw.make_context_current(self.window)

        self.logger.log_debug("GLFW initalized successfully!")

        gl.glClearColor(0.2, 0.2, 1, 1)

        gl.glEnable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_DEPTH_TEST)

        compiled = not os.path.isfile(".rproj") # If there is a .rproj file, then the project has not been built yet.
        self.scene_manager = SceneManager(compiled)

    def should_close(self):
        return glfw.window_should_close(self.window)

    def update(self):
        glfw.poll_events()

        gl.glViewport(0, 0, *glfw.get_window_size(self.window))

        gl.glClear(gl.GL_DEPTH_BUFFER_BIT | gl.GL_COLOR_BUFFER_BIT)

        self.scene_manager.update_scene()

        glfw.swap_buffers(self.window)

    def terminate(self):
        """
            Usually automatically called. You shouldn't call it yourself, unless you are sure that you have to.
        """

        glfw.terminate()

from __future__ import annotations
from typing_extensions import overload

from .logger import Logger
from .scene_manager import SceneManager
from .input import Input

import glfw
import sys, os, OpenGL.GL as gl

glfw_initalized = False

def glfw_error_handler(e_code:str, desc:str):
    Logger("CORE").log_fatal(f"GLFW Error [{e_code}] : {desc}")

glfw.set_error_callback(glfw_error_handler)

class Window:
    _instance = None
    _created = False
    def __new__(cls, *args):
        if cls._instance is None:
            cls._instance = super(Window, cls).__new__(cls)

        return cls._instance

    @overload
    def __init__(self): ...
    @overload
    def __init__(self, width:int, height:int): ...
    @overload
    def __init__(self, width:int, height:int, name:str): ...
    def __init__(self, width=800, height=600, name:str = "GLFW Window"):
        if self._created:
            return
        
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

        gl.glClearColor(0.25, 0.25, 1, 1)

        gl.glEnable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_DEPTH_TEST)

        self.input_handler = Input()
        self.scene_manager = SceneManager()
        self.scene_manager.load_scene_index(0)

        Window._created = True

    def should_close(self):
        return glfw.window_should_close(self.window)

    def update(self):
        glfw.poll_events()

        self.input_handler.get_inputs(self.window)

        gl.glViewport(0, 0, *glfw.get_window_size(self.window))

        gl.glClear(gl.GL_DEPTH_BUFFER_BIT | gl.GL_COLOR_BUFFER_BIT)

        self.scene_manager.update_scene()

        glfw.swap_buffers(self.window)

    def size(self):
        return glfw.get_window_size(self.window)
    
    def terminate(self):
        glfw.terminate()
    
from __future__ import annotations
from typing_extensions import overload

from Engine.core.logger import Logger

import glfw
import sys

glfw_initalized = False

def error_handler(e_code:str, desc:str):
    Logger("CORE").log_fatal(f"GLFW Error [{e_code}] : {desc}")

glfw.set_error_callback(error_handler)

class Window:
    def __init__(self):
        global glfw_initalized

        if not glfw_initalized:
            glfw.init()

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        window = glfw.create_window(800, 600, "GLFW window", None, None)
        glfw.make_context_current(window)

        Logger("CORE").log_debug("GLFW initalized successfully!")

        self.window = window

    def should_close(self):
        return glfw.window_should_close(self.window)

    def update(self):
        glfw.poll_events()

        glfw.swap_buffers(self.window)

    def terminate(self):
        """
            Usually automatically called. You shouldn't call it yourself, unless you are sure that you have to.
        """

        glfw.terminate()

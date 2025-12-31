from __future__ import annotations
from typing_extensions import overload

from .logger import Logger
from .scene_manager import SceneManager
from .input import Input

from ..editor import editor_windows

import glfw
import sys, os, OpenGL.GL as gl

from imgui.integrations.glfw import GlfwRenderer
import imgui

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

        compiled = not os.path.isfile(".rproj") # If there is a .rproj file, then the project has not been built yet.
        if compiled:
            os.environ['compiled'] = ""
        self.scene_manager = SceneManager()

        Window._created = True
        self.editor = sys.argv[-1] == "--editor"

        if self.editor:
            imgui.create_context()
            self.editor_renderer = GlfwRenderer(self.window)

            self.open_windows: list[editor_windows.EditorWindow] = []

    def should_close(self):
        return glfw.window_should_close(self.window)

    def update(self):
        glfw.poll_events()

        self.input_handler.get_inputs(self.window)

        gl.glViewport(0, 0, *glfw.get_window_size(self.window))

        gl.glClear(gl.GL_DEPTH_BUFFER_BIT | gl.GL_COLOR_BUFFER_BIT)

        self.scene_manager.update_scene()

        if self.editor:
            self.__render_editor_ui()

        glfw.swap_buffers(self.window)

    def open_editor_window(self, window: editor_windows.EditorWindow):
        if not window.allow_multiple:
            for idx, window_ in enumerate(self.open_windows):
                if isinstance(window_, type(window)):
                    self.open_windows[idx] = window
                    return
                
        self.open_windows.append(window)

    def __render_editor_ui(self):
        self.editor_renderer.process_inputs()

        imgui.new_frame()

        with imgui.begin_main_menu_bar() as main_menu_bar:
            if main_menu_bar.opened:
                for menu, windows in editor_windows.menu_registry.items():
                    with imgui.begin_menu(menu, True) as menu:
                        if menu.opened:
                            for window in windows:
                                if imgui.menu_item(window.__name__, window.keybind)[1]:
                                    self.open_windows.append(window())

        for idx, window in enumerate(self.open_windows.copy()):
            kill = window.render()
            if kill:
                self.open_windows.pop(idx)

        imgui.render()
        self.editor_renderer.render(imgui.get_draw_data())

    def size(self):
        return glfw.get_window_size(self.window)

    def quit(self):
        glfw.set_window_should_close(self.window, True)

    def terminate(self):
        glfw.terminate()

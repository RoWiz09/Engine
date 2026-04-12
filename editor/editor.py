from __future__ import annotations
from typing_extensions import overload

from systems.argument_parser import ArgumentParser
# from systems.editor_windows import *

import glfw, time
import os, OpenGL.GL as gl

from pyglm import glm

from systems.editor_camera import editor_camera

from systems.window_drawer import WindowDrawer
from systems.window_docker import *
from systems.editor_windows import *


from systems import get_modules as modules

import json
import sys

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
    def __init__(self, path: str): ...
    @overload
    def __init__(self, path: str, width:int, height:int): ...
    def __init__(self, path: str, width=800, height=600):
        os.chdir(path)

        if self._created:
            return
        
        global glfw_initalized

        if not glfw_initalized:
            glfw.init()

        self.logger = Logger("EDITOR")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        self.window = glfw.create_window(width, height, "GhostEngine Editor", None, None)
        glfw.make_context_current(self.window)

        self.logger.log_debug("GLFW initalized successfully!")

        gl.glEnable(gl.GL_CULL_FACE)
        # gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        self.input_handler = Input()

        self.project_data = None

        compiled = not os.path.isfile(".rproj") # If there is a .rproj file, then the project has not been built yet.
        if compiled:
            self.logger.log_fatal("Unable to edit a compiled game!")
            sys.exit()

        else:
            with open(".rproj") as project_file:
                self.project_data = json.load(project_file)
            os.environ["project"] = self.project_data["name"]

            glfw.set_window_title(self.window, "GhostEngine Editor - " + self.project_data["name"])
        self.scene_manager = SceneManager()
        self.scene_manager.load_scene_index(0, alert_scripts = False)
        Window._created = True

        self.drawer = WindowDrawer()

        self.docker = Docker()
        scene_viewer = SceneView()
        scene_viewer2 = Hierarchy()
        scene_viewer3 = SceneView()
        root = self.docker.dock(self.docker.root, scene_viewer, "right")
        self.docker.dock(root.child_a, scene_viewer2)
        self.docker.set_ratio(root, 0.15, self)
        self.docker.dock(root.child_b, scene_viewer3, "right")
        self.docker.compute_layout(self)

        self.drawer.add_window_data(scene_viewer)
        self.drawer.add_window_data(scene_viewer2)
        self.drawer.add_window_data(scene_viewer3)

        self.editor_cam = editor_camera(self.input_handler)
        self.moving_camera = False

        self.running_game = False

        self.last_time = glfw.get_time()

    def should_close(self):
        return glfw.window_should_close(self.window)

    def render_scene(self, frame_buffer = 0):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, frame_buffer)
        gl.glEnable(gl.GL_DEPTH_TEST)

        gl.glClearColor(0.25, 0.25, 1, 1)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT | gl.GL_COLOR_BUFFER_BIT)

        self.scene_manager.render_scene(
            self.editor_cam.get_view_mat(), 
            self.editor_cam.get_projection_mat(), 
            self.editor_cam.get_view_pos()
        )

        if frame_buffer != 0:
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glDisable(gl.GL_DEPTH_TEST)

    def update(self):
        cur_time = glfw.get_time()
        dt = cur_time - self.last_time
        self.last_time = cur_time

        # print(1/dt)

        glfw.poll_events()
        self.input_handler.get_inputs(self.window)

        if self.input_handler.get_key_down(KeyCodes.k_Z) and isinstance(self.drawer.focused_window, SceneView):
            self.moving_camera = not self.moving_camera

        # Set up for a new frame
        width, height = glfw.get_window_size(self.window)
        gl.glViewport(0, 0, width, height)

        gl.glClearColor(0.12, 0.12, 0.12, 1)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT | gl.GL_COLOR_BUFFER_BIT)

        if self.moving_camera:
            self.editor_cam.update(dt)

        # Rendering
        self.docker.update(self)
        self.__render_editor_ui()

        glfw.swap_buffers(self.window)

    def __render_editor_ui(self):
        self.drawer.render(self)
        if not self.moving_camera:
            self.drawer.handle_input(KeyCodes, MouseButtons, self.input_handler)

    def size(self):
        return glfw.get_window_size(self.window)

    def quit(self):
        glfw.set_window_should_close(self.window, True)

    def terminate(self):
        glfw.terminate()

arg_parser = ArgumentParser()
arg_parser.add_argument("project-path")

arg_parser.parse()

def get_path(location: str):
    if not location.endswith(".rproj") and os.path.exists(location):
        raise ValueError("Executable argument project-path is" +
                         " pointing to an invalid or missing project!")
    
    return os.path.split(location)[0]

base_path = get_path(arg_parser.get_arg("project-path"))
os.chdir(base_path)
Logger, SceneManager, Input = modules.get_modules(base_path)
KeyCodes, MouseButtons = modules.key_codes, modules.mouse_buttons

window = Window(base_path)
while not window.should_close():
    window.update()

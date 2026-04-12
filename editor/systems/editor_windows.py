from __future__ import annotations

import OpenGL.GL as gl

from .window_drawer import *
from . import get_modules

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ghost_engine.object import Object

import sys

class SceneView(EditorUiWindow):
    name = "Scene"
    def __init__(self):
        super().__init__()

        self.fbo = gl.glGenFramebuffers(1)

        self.view = UiElement(self, 0, 0)
        self.view.resize_callback = self.view_resize_callback

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glFramebufferTexture2D(gl.GL_READ_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.view.texture, 0)

        self.rbo = gl.glGenRenderbuffers(1)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.rbo)
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT24, int(self.view.size.x), int(self.view.size.y))
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_RENDERBUFFER, self.rbo)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def view_resize_callback(self, view: UiElement):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glFramebufferTexture2D(gl.GL_READ_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.view.texture, 0)

        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.rbo)
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT24, int(self.view.size.x), int(self.view.size.y))
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_RENDERBUFFER, self.rbo)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def draw(self, editor):
        window = glfw.get_current_context()
        size = glfw.get_window_size(window)

        gl.glViewport(0, 0, int(self.view.size.x), int(self.view.size.y))
        editor.render_scene(self.fbo)
        gl.glViewport(0, 0, *size)
        
        super().draw(editor)   

    def resize(self, new_width, new_height):
        super().resize(new_width, new_height)     
        self.view.resize_to_fill_window()

        text_img = render_window_label(self.name, int(self.draw_data.size.x))
        self.text_img_size = text_img.size
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.name_texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *self.text_img_size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, text_img.tobytes())
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

        return self
    
class Inspector(EditorUiWindow):
    name = "Inspector"
    def __init__(self):
        super().__init__()

        self.object_type = None
        
    def set_data(self, data):
        if not self.object_type:
            self.object_type = getattr(sys.modules["ghost_engine.object"], "Object")

        if isinstance(data, self.object_type):
            if TYPE_CHECKING:
                self.object_type: type[Object]; data: Object

            data.name
    
class Hierarchy(EditorUiWindow):
    name = "Hierarchy"

    def __init__(self):
        super().__init__()

        self.draw_data.padding.x = 5
        self.draw_data.padding.y = 5

        self.manager = get_modules.scene_manager()
        self.object_buttons: list[Button] = set()

        self.object_type = None
        self.create_object_button = TextInput(self, 100, 30, "Wow!")
        # self.create_object_button: Button = Button(self, 100, 30, "Create Gameobject", self.create_object)

        Hierarchy.instances.add(self)

        self.build()

    def create_object(self):
        if not self.object_type:
            self.object_type = getattr(sys.modules["ghost_engine.object"], "Object")
        
        new_obj = self.object_type("New GameObject", self.manager.materials["base_mat"])
        self.manager.game_objects.append(new_obj)
        
        self.rebuild_windows()

    def resize(self, new_width, new_height):
        orig_window_width = self.draw_data.size.x - self.draw_data.padding.x * 2
        self.create_object_button.resize(glm.vec2(new_width - self.draw_data.padding.x * 2, self.create_object_button.size.y))
        for button in self.object_buttons:
            orig_button_width_mod = orig_window_width - button.size.x
            button.resize(glm.vec2((new_width - self.draw_data.padding.x * 2) - orig_button_width_mod, button.size.y))

        super().resize(new_width, new_height)

    def build(self):
        self.object_buttons.clear()
        self.ui_elements.clear()

        self.ui_elements.append(self.create_object_button)

        root_objects = list(filter(lambda object_: object_.transform.parent == None, self.manager.game_objects))
        def build_layer(objects: list, width):
            for obj in objects:
                button = Button(self, width, 30, obj.name, lambda object_=obj: print(object_.name))
                button.pos_offset = glm.vec2((self.draw_data.size.x - self.draw_data.padding.x * 2) - width, 0)

                build_layer(obj.children, max(20, width-20))
                self.object_buttons.add(button)

        build_layer(root_objects, self.draw_data.size.x - self.draw_data.padding.x * 2)
    
    @classmethod
    def rebuild_windows(cls):
        for inst in cls.instances:
            inst.build()

    def draw(self, editor):
        super().draw(editor)
from __future__ import annotations

import OpenGL.GL as gl
import numpy as np
import ctypes
import glfw

from pyglm import glm

from systems.shader_program import ShaderProgram
from enum import Enum

from .font import render_window_label, render_text, TextStyle, AnchorPoints
from PIL import Image, ImageDraw

from typing import TYPE_CHECKING
from typing import Any, TypeAlias
if TYPE_CHECKING:
    from ..editor import Window
    from ghost_engine.core.input import KeyCodes, MouseButtons, Input

else:
    KeyCodes: TypeAlias = Any
    MouseButtons: TypeAlias = Any
    Input: TypeAlias = Any

class ButtonStates(Enum):
    PRESSED = 0
    HELD = 1
    RELEASED = 2

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
        self.focused_window: EditorUiWindow = None

        __class__.INITALIZED = True

    def render(self, editor: Window):
        width, height = glfw.get_window_size(glfw.get_current_context())
        ortho = glm.ortho(0, width, height, 0, -1, 1)

        WINDOW_SHADER.use()
        WINDOW_SHADER.set_mat4("uProjection", ortho)

        for window in self.windows:
            window.draw(editor)
            
            if self.focused_window and self.focused_window.focused_elem:
                continue

            if window.rect.collide_point(glm.vec2(*editor.input_handler.mouse_pos)):
                self.focused_window = window

    def handle_input(self, key_codes: type[KeyCodes], mouse_buttons: type[MouseButtons], input_handler: Input):
        if self.focused_window:
            self.focused_window.handle_input(key_codes, mouse_buttons, input_handler)

    def add_window_data(self, window_data: EditorUiWindow):
        self.windows.add(window_data)

WINDOW_SHADER = None
VBO, VAO, EBO = None, None, None

def setup():
    global WINDOW_SHADER, VBO, VAO, EBO, BASE_WINDOW_TEXTURE
    WINDOW_SHADER = ShaderProgram(
        """
            #version 330 core

            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec2 aTexCoord;

            uniform mat4 uModel;
            uniform mat4 uProjection;

            out vec2 vTexCoord;

            void main() {
                gl_Position = uProjection * uModel * vec4(aPos, 0.0, 1.0);
                vTexCoord = aTexCoord;
            }
        """,
        """
            #version 330 core
            uniform sampler2D uTexture;

            in vec2 vTexCoord;

            out vec4 FragColor;

            void main() {
                vec4 albedo  = texture(uTexture, vTexCoord).rgba;
                FragColor = albedo;
            }
    """)

    verts = np.array([
        # Pos, UV
        0, 0,  0, 1,
        0, 1,  0, 0,
        1, 1,  1, 0,
        1, 0,  1, 1
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

def build_window_img(window: EditorUiWindow):
    width, height = window.get_draw_data().size
    edge = (60, 60, 60, 255)
    center = (37, 37, 38, 255)

    img = Image.new("RGBA", (int(width), int(height)))
    img_drawer = ImageDraw.Draw(img, "RGBA")
    img_drawer.rectangle((0, 0, width, height), outline=edge, fill=center, width=2)
    del img_drawer

    return img

class TextRenderAnchor(Enum):
    top_left = glm.vec2(0, 0)
    top_middle = glm.vec2(0.5, 0)
    top_right = glm.vec2(1, 0)

    middle_left = glm.vec2(0, 0.5)
    middle_middle = glm.vec2(0.5, 0.5)
    middle_right = glm.vec2(1, 0.5)

    bottom_left = glm.vec2(0, 1)
    bottom_middle = glm.vec2(0.5, 1)
    bottom_right = glm.vec2(1, 1)

class EditorUiWindow:
    name: str
    def __init_subclass__(cls):
        setattr(cls, "instances", set())

    def __init__(self):
        self.draw_data = UiDrawData()
        self.ui_elements: list[UiElement] = []

        self.rect = UiRect(*self.draw_data.pos, *self.draw_data.size)

        bg_img = build_window_img(self)
        self.bg_tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.bg_tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *bg_img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, bg_img.tobytes())
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

        self.name_texture = gl.glGenTextures(1)
        text_img = render_window_label(self.name, int(self.draw_data.size.x))
        self.text_img_size = text_img.size

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.name_texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *self.text_img_size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, text_img.tobytes())
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

        self.focused_elem: UiElement = None
        self.__class__.instances.add(self)

    def get_draw_data(self):
        return self.draw_data
    
    def move(self, new_x: float, new_y: float):
        """
            Moves the window to `new_x`, `new_y`. 
            Returns this class for easier method chaining.
        """
        self.draw_data.pos = glm.vec2(new_x, new_y)
        self.rect.move_to(self.draw_data.pos)
        return self

    def resize(self, new_width: float, new_height: float):
        """
            Sets the window size to `new_width`, `new_height`. 
            Returns this class for easier method chaining.
        """
        self.draw_data.size = glm.vec2(new_width, new_height)

        bg_img = build_window_img(self)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.bg_tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *bg_img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, bg_img.tobytes())

        self.rect.resize(self.draw_data.size)
        for child in self.ui_elements:
            child

        return self

    def draw(self, editor: Window):
        global VAO

        # RoWiz (4/8/26):
        # The shader should always be bound by the editor before this is called, but just in case,
        # bind it here.
        WINDOW_SHADER.use()

        # Base Window stuff
        WINDOW_SHADER.set_mat4("uModel", self.draw_data.get_configuration_out())

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.bg_tex)

        gl.glBindVertexArray(VAO)
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
    
        # Window Title Bar
        model = glm.mat4(1)
        model = glm.translate(model, glm.vec3(*self.draw_data.pos, 0))
        model = glm.scale(model, glm.vec3(*self.text_img_size, 0))
        WINDOW_SHADER.set_mat4("uModel", model)

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.name_texture)

        gl.glBindVertexArray(VAO)
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

        # Child Elements
        pos = self.draw_data.pos + self.draw_data.padding
        pos.y += 30 
        for child in self.ui_elements:
            child.draw(editor, pos)
            pos.y += child.get_height() + self.draw_data.padding.y

    def handle_input(self, key_codes: type[KeyCodes], mouse_buttons: type[MouseButtons], input_handler: Input):
        if self.focused_elem:
            elem = self.focused_elem
            if not elem.rect.collide_point(glm.vec2(*input_handler.mouse_pos)) and not self.focused_elem.hold_focus:
                self.focused_elem.lose_focus()
                self.focused_elem = None

            else:
                self.focused_elem.handle_input(key_codes, mouse_buttons, input_handler)

        else:
            for elem in self.ui_elements:
                if not elem.can_claim_focus:
                    continue

                if elem.rect.collide_point(glm.vec2(*input_handler.mouse_pos)):
                    if self.focused_elem:
                        self.focused_elem.lose_focus()

                    self.focused_elem = elem
                    self.focused_elem.focus()

                    break

class UiElement:
    can_claim_focus: bool = False
    hold_focus: bool = False

    def __init__(self, parent: EditorUiWindow, width: float, height: float):
        self.size = glm.vec2(width, height)
        self.pos_offset = glm.vec2(0, 0)

        self.rect = UiRect(0, 0, width, height)

        if parent:
            self.parent = parent
            self.parent.ui_elements.append(self)

        self.texture = gl.glGenTextures(1)

        white_pixel = bytes([255, 255, 255, 255])
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *self.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, white_pixel)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

        self.resize_callback = None

        # Render hooks
        self.pre_render_hook = None
        self.post_render_hook = None

        self.focused = False

    def update_rect(self, new_pos: glm.vec2):
        self.rect.move_to(new_pos)

    def resize_to_fill_window(self):
        self.size = glm.vec2(self.parent.draw_data.size.x - self.parent.draw_data.padding.x * 2, 
                             self.parent.draw_data.size.y - self.parent.draw_data.padding.y * 2 - 30)
        
        self.rect.resize(self.size)
        
        white_pixel = bytes([255, 255, 255, 255]) * int(self.size.x * self.size.y)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *self.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, white_pixel)

        if self.resize_callback:
            self.resize_callback(self)

    def resize(self, size: glm.vec2):
        self.size = size
        self.rect.resize(size)

        white_pixel = bytes([255, 255, 255, 255]) * int(self.size.x * self.size.y)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *self.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, white_pixel)

        if self.resize_callback:
            self.resize_callback(self)

    def draw(self, editor: Window, pos: glm.vec2):
        global VAO
        if self.pre_render_hook:
            self.pre_render_hook(self)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)

        model = glm.mat4(1)
        model = glm.translate(model, glm.vec3(*(pos + self.pos_offset), 0))
        model = glm.scale(model, glm.vec3(*self.size, 0))

        WINDOW_SHADER.use()
        WINDOW_SHADER.set_mat4("uModel", model)

        gl.glBindVertexArray(VAO)
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

        if self.post_render_hook:
            self.post_render_hook(self)
            
    def get_height(self):
        return self.size.y + self.pos_offset.y
    
    def handle_input(self, keycodes: type[KeyCodes], mouse_buttons: type[MouseButtons], input_handler: Input):
        pass

    def focus(self):
        self.focused = True

    def lose_focus(self):
        self.focused = False

class UiRect:
    def __init__(self, x: float, y: float, w: float, h: float):
        self.pos = glm.vec2(x, y)
        self.size = glm.vec2(w, h)

    def move_by(self, delta: glm.vec2):
        self.pos += delta

    def move_to(self, new_pos: glm.vec2):
        self.pos = new_pos

    def resize(self, new_size: glm.vec2):
        self.size = new_size
    
    @property
    def left(self):
        return self.pos.x
    
    @property
    def top(self):
        return self.pos.y

    @property
    def right(self):
        return self.pos.x + self.size.x

    @property
    def bottom(self):
        return self.pos.y + self.size.y

    def collide_point(self, point: glm.vec2):
        return self.left < point.x < self.right and self.top < point.y < self.bottom

class TextElement(UiElement):
    def __init__(self, parent, text: str, width: float, height: float):
        super().__init__(parent, width, height)

        self.message = text

        self.style = TextStyle.NORMAL
        self.anchor: AnchorPoints = "mm"
        self.text_draw_anchor: TextRenderAnchor = TextRenderAnchor.middle_middle
        self.old = False

        offset = self.size * self.text_draw_anchor.value
        img = render_text(text, width, height, int(offset.x), int(offset.x), self.style, self.anchor)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img.tobytes())

    def bold(self):
        self.style = TextStyle.BOLD
        self.old = True

    def italicize(self):
        self.style = TextStyle.ITALICS
        self.old = True

    def set_anchor(self, anchor: AnchorPoints, render_anchor: TextRenderAnchor):
        self.anchor = anchor
        self.text_draw_anchor = render_anchor

    def draw(self, editor, pos):
        if self.old:
            offset = self.size * self.text_draw_anchor.value
            img = render_text(self.message, int(self.size.x), int(self.size.y), 
                              int(offset.x), int(offset.y), self.style, self.anchor)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img.tobytes())

            self.old = False

        return super().draw(editor, pos)

    def resize(self, size):
        super().resize(size)

        offset = self.size * self.text_draw_anchor.value
        img = render_text(self.message, int(size.x), int(size.y), int(offset.x), int(offset.y), self.style, self.anchor)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img.tobytes())
    
class Button(UiElement):
    can_claim_focus = True
    def __init__(self, parent, width: float, height: float, text: str, click_callback: function):
        super().__init__(parent, width, height)

        self.label = TextElement(None, text, width, height)
        self.click_callback = click_callback
        self.clicked = False

        self.was_focused_last = self.focused
        self.was_clicked_last = self.clicked

        img = self.build_texture()
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img.tobytes())

    def build_texture(self):
        if self.focused and not self.clicked:
            col = (69, 73, 78)
        elif self.focused and self.clicked:
            col = (45, 45, 48)
        else:
            col = (58, 61, 65)

        img = Image.new("RGBA", (int(self.rect.size.x), int(self.rect.size.y)), (0, 0, 0, 0))
        ImageDraw.Draw(img, "RGBA").rounded_rectangle(
            (0, 0, int(self.rect.size.x), int(self.rect.size.y)), radius=5, fill=col)
        
        return img

    def draw(self, editor, pos):
        global VAO
        if self.focused != self.was_focused_last or self.clicked != self.was_clicked_last:
            img = self.build_texture()

            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img.tobytes())

            self.was_focused_last = self.focused
            self.was_clicked_last = self.clicked

        if self.rect.pos != pos:
            self.rect.move_to(glm.vec2(*pos))

        super().draw(editor, pos)
        self.label.draw(editor, pos)
    
    def handle_input(self, keycodes, mouse_buttons, input_handler):
        if input_handler.get_mouse_button_down(mouse_buttons.LEFT):
            if self.click_callback:
                self.click_callback()

    def resize(self, size):
        super().resize(size)

        img = self.build_texture()

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img.tobytes())

        self.label.resize(size)

class TextInput(UiElement):
    can_claim_focus = True
    hold_focus = False
    def __init__(self, parent, width, height, hint: str = ""):
        super().__init__(parent, width, height)

        self.hint = hint
        self.message = ""
        self.selection_idx = 0

        self.label = TextElement(None, hint, width, height)
        self.label.set_anchor("lm", TextRenderAnchor.middle_left)
        self.old = False

        self.label.italicize()

        self.was_focused_last = self.focused
        self.hold_focus = False

    def build_texture(self):
        if self.focused:
            col = (69, 73, 78)
        else:
            col = (58, 61, 65)

        img = Image.new("RGBA", (int(self.rect.size.x), int(self.rect.size.y)), (0, 0, 0, 0))
        ImageDraw.Draw(img, "RGBA").rounded_rectangle(
            (0, 0, int(self.rect.size.x), int(self.rect.size.y)), radius=5, fill=col)
        
        return img

    def resize(self, size):
        super().resize(size)

        img = self.build_texture()

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img.tobytes())

        self.label.resize(size)

    def draw(self, editor, pos):
        if self.rect.pos != pos:
            self.rect.move_to(glm.vec2(*pos))

        if self.message != "":
            self.label.message = self.message
            self.label.style = TextStyle.NORMAL

        else:
            self.label.message = self.hint
            self.label.style = TextStyle.ITALICS

        self.label.old = self.old
        self.old = False

        if self.focused != self.was_focused_last:
            img = self.build_texture()

            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img.tobytes())
            self.was_focused_last = self.focused

        super().draw(editor, pos)
        self.label.draw(editor, pos)

    def lose_focus(self):
        self.input_handler_.key_press_callback = None
        self.input_handler_.key_extras_callback = None
        self.parent.focused_elem = None
        
        return super().lose_focus()

    def input_handler(self, key: int):
        self.message = self.message[:self.selection_idx] + chr(key) + self.message[self.selection_idx:]
        self.selection_idx += 1
        self.old = True

    def extras_handler(self, key, scancode, action, mods):
        if action == glfw.PRESS or action == glfw.REPEAT:
            if key == glfw.KEY_BACKSPACE:
                self.message = self.message[:self.selection_idx-1] + self.message[self.selection_idx:]
                self.selection_idx = max(0, self.selection_idx-1)
                self.old = True
            
            if key == glfw.KEY_ESCAPE:
                self.lose_focus()

    def handle_input(self, keycodes, mouse_buttons, input_handler):
        self.input_handler_ = input_handler
        if input_handler.get_mouse_button_down(mouse_buttons.LEFT):
            input_handler.key_press_callback = self.input_handler
            input_handler.key_extras_callback = self.extras_handler

            self.hold_focus = True

class UiDrawData:
    def __init__(self, x: float = 0, y: float = 0, width: float = 100, height: float = 100):
        self.pos = glm.vec2(x, y)
        self.size = glm.vec2(width, height)

        self.padding = glm.vec2(20, 20)

    def get_configuration_out(self):
        model = glm.mat4(1)

        model = glm.translate(model, glm.vec3(*self.pos, 0))
        model = glm.scale(model, glm.vec3(*self.size, 1))

        return model

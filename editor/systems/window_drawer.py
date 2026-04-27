from __future__ import annotations

import OpenGL.GL as gl
import numpy as np
import ctypes
import glfw

from pyglm import glm

from .shader_program import ShaderProgram
from . import get_modules as modules
from enum import Enum

from .font import render_window_label, render_text, TextStyle, AnchorPoints
from PIL import Image, ImageDraw

from typing import TYPE_CHECKING
from typing import Any, TypeAlias, final
from dataclasses import dataclass
if TYPE_CHECKING:
    from ..editor import Window
    from ghost_engine.core.input import KeyCodes, MouseButtons, Input

else:
    KeyCodes: TypeAlias = Any
    MouseButtons: TypeAlias = Any
    Input: TypeAlias = Any
 
@dataclass
class DragData:
    object_data: Any
    display_str: str

HELD_DRAG_DATA: DragData = None

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
        model = glm.translate(model, glm.vec3(*(self.draw_data.pos + glm.vec2(3, 0)), 0))
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
        global HELD_DRAG_DATA
        if not self.focused_elem and HELD_DRAG_DATA and input_handler.get_mouse_button_up(mouse_buttons.LEFT):
            HELD_DRAG_DATA = None
        
        if self.focused_elem:
            elem = self.focused_elem
            if input_handler.get_mouse_button_down(mouse_buttons.LEFT):
                HELD_DRAG_DATA = elem.get_drag_data()
            elif not elem.rect.collide_point(glm.vec2(*input_handler.mouse_pos)) and not self.focused_elem.hold_focus:
                self.focused_elem.lose_focus()
                self.focused_elem = None

            else:
                if HELD_DRAG_DATA and input_handler.get_mouse_button_up(mouse_buttons.LEFT):
                    self.focused_elem.drop_drag_data(HELD_DRAG_DATA)
                    HELD_DRAG_DATA = None
                    self.focused_elem.handle_input(key_codes, mouse_buttons, input_handler)
                elif HELD_DRAG_DATA:
                    self.focused_elem.highlight_drag_data(HELD_DRAG_DATA)
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
    
    @property
    def renderable_width(self):
        return self.draw_data.size.x - self.draw_data.padding.x * 2
    
    @property
    def renderable_height(self):
        return self.draw_data.size.y - self.draw_data.padding.y * 2 - 30 

class UiElement:
    can_claim_focus: bool = False
    hold_focus: bool = False

    def __init__(self, parent: EditorUiWindow, width: float, height: float):
        self.size = glm.vec2(width, height)
        self.pos_offset = glm.vec2(0, 0)

        self.rect = UiRect(0, 0, width, height)

        self.focused = False

        if parent:
            self.parent = parent
            self.parent.ui_elements.append(self)

        self.texture = gl.glGenTextures(1)

        self.sprite = self.build_sprite()
        self.rebuild_texture()
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

        self.resize_callback = None

        # Render hooks
        self.pre_render_hook = None
        self.post_render_hook = None

        self.draggable_data: DragData = None

    def update_rect(self, new_pos: glm.vec2):
        self.rect.move_to(new_pos)

    def resize_to_fill_window(self):
        self.size = glm.vec2(self.parent.draw_data.size.x - self.parent.draw_data.padding.x * 2, 
                             self.parent.draw_data.size.y - self.parent.draw_data.padding.y * 2 - 30)
        
        self.rect.resize(self.size)
        
        self.sprite = self.build_sprite()
        self.rebuild_texture()

        if self.resize_callback:
            self.resize_callback(self)

    def resize(self, size: glm.vec2):
        self.size = size
        self.rect.resize(size)

        self.sprite = self.build_sprite()
        self.rebuild_texture()

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

    def build_sprite(self):
        col = (255, 255, 255)
        img = Image.new("RGBA", (int(self.rect.size.x), int(self.rect.size.y)), col)
        
        return img
    
    @final
    def rebuild_texture(self):
        img = self.sprite
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img.tobytes())

    # Dragging
    @final
    def get_drag_data(self):
        return self.draggable_data
    
    def highlight_drag_data(self, drag_data: DragData):
        pass

    def drop_drag_data(self, drag_data: DragData):
        pass

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
        # The amount the text is offset from the edge of it's bounding box.
        # Left, Top, Right, Bottom
        self.edge_offset = [0, 0, 0, 0]
        self.message = text

        self.style = TextStyle.NORMAL
        self.anchor: AnchorPoints = "mm"
        self.text_draw_anchor: TextRenderAnchor = TextRenderAnchor.middle_middle
        self.old = False

        self.text_size = None
        super().__init__(parent, width, height)

    def bold(self):
        self.style = TextStyle.BOLD
        self.old = True
        return self

    def italicize(self):
        self.style = TextStyle.ITALICS
        self.old = True
        return self

    def set_anchor(self, anchor: AnchorPoints, render_anchor: TextRenderAnchor):
        self.anchor = anchor
        self.text_draw_anchor = render_anchor
        return self

    def set_text_size(self, new_text_size: int):
        self.text_size = new_text_size
        self.old = True
        return self

    def build_sprite(self):
        offset = self.size * self.text_draw_anchor.value
        half_size = self.size / 2
        if offset.x > half_size.x:
            offset.x - self.edge_offset[2]
        else:
            offset.x + self.edge_offset[0]

        if offset.y > half_size.y:
            offset.y - self.edge_offset[3]
        else:
            offset.y + self.edge_offset[1]

        return render_text(self.message, int(self.size.x), int(self.size.y), 
                              int(offset.x), int(offset.y), self.style, self.anchor, self.text_size)

    def draw(self, editor, pos):
        if self.old:
            self.sprite = self.build_sprite()
            self.rebuild_texture()

            self.old = False

        return super().draw(editor, pos)

    def resize(self, size):
        super().resize(size)

        offset = self.size * self.text_draw_anchor.value
        img = render_text(self.message, int(size.x), int(size.y), int(offset.x), int(offset.y), self.style, self.anchor, self.text_size)
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
        self.label.resize(glm.vec2(width, height))

    def build_sprite(self) -> Image.Image:
        """
        Builds the texture for the Button element.

        Returns:
            Image.Image: The texture.
        """
        if self.focused:
            bottom_col = (69, 73, 78)
            top_col = (78, 81, 84)
        else:
            bottom_col = (58, 61, 65)
            top_col = (66, 69, 71)

        img = Image.new("RGBA", (int(self.rect.size.x), int(self.rect.size.y)), (0, 0, 0, 0))
        drawer = ImageDraw.Draw(img, "RGBA")
        drawer.rounded_rectangle(
            (0, 0, int(self.rect.size.x), int(self.rect.size.y) - 3), radius=7, fill=bottom_col)
        drawer.rounded_rectangle(
            (0, 3, int(self.rect.size.x), int(self.rect.size.y)), radius=7, fill=top_col)
        
        return img

    def draw(self, editor, pos):
        global VAO
        if self.focused != self.was_focused_last or self.clicked != self.was_clicked_last:
            self.sprite = self.build_sprite()
            self.rebuild_texture()

            self.was_focused_last = self.focused
            self.was_clicked_last = self.clicked

        if self.rect.pos != pos:
            self.rect.move_to(glm.vec2(*pos))

        super().draw(editor, pos)
        self.label.draw(editor, pos + self.pos_offset)
    
    def handle_input(self, keycodes, mouse_buttons, input_handler):
        if input_handler.get_mouse_button_up(mouse_buttons.LEFT):
            if self.click_callback:
                self.click_callback()

    def resize(self, size):
        super().resize(size)

        img = self.build_sprite()

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img.tobytes())

        self.label.resize(size)

class InputField(UiElement):
    can_claim_focus = True
    hold_focus = False

    @staticmethod
    def validate_float(message: str):
        message_ = message
        if message == "-":
            message_ = "-1.0"
        try:
            float(message_)
            return True
        except ValueError:
            return False
 
    def __init__(self, parent: EditorUiWindow | HorizontalLayout, width: float, height: float, hint: str = "", starting_message: str = "", type_: Any = str):
        """
        Creates a new InputField object for use in the editor UI

        Args:
            parent (EditorUiWindow, HorizontalLayout): The parent of this object. Either a EditorUIWindow or layout group.
            width (float): The width, in pixels, of the element. Overridden if the parent is a layout group.
            height (float): The height, in pixels, of the element.
            hint (str, optional): The hint, shown when the input field is empty. Defaults to an empty string.
            starting_message (str, optional): The starting text in the input field. Defaults to "".
            type_ (Any, optional): The type to cast the text into when focus is lost. Defaults to str.
        """            
        super().__init__(parent, width, height)

        self.hint = hint
        self.message = starting_message
        self.selection_idx = 0

        self.label = TextElement(None, hint if self.message == "" else self.message, width, height)
        self.label.edge_offset = [5, 5, 5, 5]
        self.label.set_anchor("lm", TextRenderAnchor.middle_left)
        self.old = True

        if self.message == "":
            self.label.italicize()
        self.label.resize(glm.vec2(width, height))

        self.was_focused_last = self.focused
        self.hold_focus = False

        self.lose_focus_callback = None

        self.validate_command = None
        self.default_val = None
        self.command = None
        self.run_command_when_empty = True
        self.type_ = type_

        if self.type_:
            self.message = str(self.type_(self.message))

    def build_sprite(self) -> Image.Image:
        """
        Builds the texture for the InputField element.

        Returns:
            Image.Image: The texture.
        """
        if self.focused:
            col = (69, 73, 78)
        else:
            col = (58, 61, 65)

        img = Image.new("RGBA", (int(self.rect.size.x), int(self.rect.size.y)), (0, 0, 0, 0))
        ImageDraw.Draw(img, "RGBA").rounded_rectangle(
            (0, 0, int(self.rect.size.x), int(self.rect.size.y)), radius=7, fill=col)
        
        return img

    def resize(self, size):
        super().resize(size)

        img = self.build_sprite()

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img.tobytes())

        self.label.resize(size)

    def draw(self, editor, pos):
        self.window = editor.window
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
            self.sprite = self.build_sprite()
            self.rebuild_texture()

            self.was_focused_last = self.focused

        super().draw(editor, pos)
        self.label.draw(editor, pos)

    def lose_focus(self):
        input_handler = modules.input_handler()
        input_handler.key_press_callback = None
        input_handler.key_extras_callback = None
        input_handler.key_paste_callback = None
        self.parent.focused_elem = None
        self.hold_focus = False

        if self.type_:
            self.message = str(self.type_(self.message))
            self.old = True

        if self.lose_focus_callback:
            self.lose_focus_callback()
        
        return super().lose_focus()
    
    def paste_handler(self, clipboard_contents: str):
        new_message = self.message[:self.selection_idx] + clipboard_contents + self.message[self.selection_idx:]

        if self.validate_command:
            if self.validate_command(new_message):
                self.message = new_message
                self.selection_idx += len(clipboard_contents)
                self.old = True

        else:
            self.message = new_message
            self.selection_idx += len(clipboard_contents)
            self.old = True

        if self.old:
            self.command(self)

    def input_handler(self, key: int):
        char = chr(key)
        new_message = self.message[:self.selection_idx] + char + self.message[self.selection_idx:]
        if self.validate_command:
            if self.validate_command(new_message):
                self.message = new_message
                self.selection_idx += 1
                self.old = True

        else:
            self.message = new_message
            self.selection_idx += 1
            self.old = True

        if self.old:
            self.command(self)

    def extras_handler(self, key, scancode, action, mods):
        if action == glfw.PRESS or action == glfw.REPEAT:
            if key == glfw.KEY_BACKSPACE:
                self.message = self.message[:self.selection_idx-1] + self.message[self.selection_idx:]
                self.selection_idx = max(0, self.selection_idx-1)
                self.old = True

                if self.command:
                    if self.run_command_when_empty and not self.message:
                        self.command(self)
                    elif self.message:
                        self.command(self)
            
            if key == glfw.KEY_ESCAPE:
                self.lose_focus()

    def handle_input(self, keycodes, mouse_buttons, input_handler):
        mouse_up = input_handler.get_mouse_button_up(mouse_buttons.LEFT)
        collides = self.rect.collide_point(glm.vec2(*input_handler.mouse_pos))
        if mouse_up and collides:
            input_handler.key_press_callback = self.input_handler
            input_handler.key_extras_callback = self.extras_handler
            input_handler.key_paste_callback = self.paste_handler

            self.selection_idx = len(self.message)
            self.hold_focus = True

        elif mouse_up and not collides:
            self.lose_focus()

    def get_value(self):
        if self.message == "":
            return self.default_val
        
        val = self.message
        if self.message == "-":
            val = "-0.0"
            
        return self.type_(val)
    
class Checkbox(UiElement):
    can_claim_focus = True

    def __init__(self, parent, state: bool = False):
        self.state = state
        super().__init__(parent, 20, 20)

    def build_sprite(self):
        if self.focused:
            col = (69, 73, 78)
        else:
            col = (58, 61, 65)

        img = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
        drawer = ImageDraw.Draw(img, "RGBA")
        drawer.rounded_rectangle(
            (1, 1, 19, 19), radius=7, outline=col, width=2)
        
        if self.state:
            drawer.rounded_rectangle((4, 4, 16, 16), radius=4, fill=(32, 168, 201))
        
        return img
    
    def handle_input(self, keycodes, mouse_buttons, input_handler):
        if input_handler.get_mouse_button_up(mouse_buttons.LEFT):
            self.state = not self.state

            self.sprite = self.build_sprite()
            self.rebuild_texture()

    def draw(self, editor, pos):
        if self.rect.pos != pos:
            self.rect.move_to(glm.vec2(*pos))

        super().draw(editor, pos)

class DropField(UiElement):
    can_claim_focus = True
 
    def __init__(self, parent: EditorUiWindow | HorizontalLayout, width: float, height: float, hint: str = "", starting_data: DragData = None, type_: Any = type[Any]):
        """
        Creates a new DropField object for use in the editor UI
        
        Args:
            parent (EditorUiWindow | HorizontalLayout): The element's parent.
            width (float): The width of the element
            height (float): The height of the element
            hint (str, optional): The hint, shown when there is no value. Defaults to "".
            starting_data (DragData, optional): The starting drag data. Defaults to None.
            type_ (Any, optional): The type of data accepted. Defaults to type[Any].
        """
        super().__init__(parent, width, height)

        self.hint = hint
        self.data = starting_data
        self.selection_idx = 0

        self.label = TextElement(None, hint if not self.data else self.data.display_str, width, height)
        self.label.edge_offset = [5, 5, 5, 5]
        self.label.set_anchor("lm", TextRenderAnchor.middle_left)
        self.old = True

        if self.data is None:
            self.label.italicize()
        self.label.resize(glm.vec2(width, height))
        self.was_focused_last = self.focused

        self.type_ = type_
        self.drop_callback = None

    def drop_drag_data(self, drag_data):
        self.data = drag_data
        self.old = True

        if self.drop_callback:
            self.drop_callback(self)

    def build_sprite(self) -> Image.Image:
        """
        Builds the texture for the DropField element.

        Returns:
            Image.Image: The texture.
        """
        if self.focused:
            col = (69, 73, 78)
        else:
            col = (58, 61, 65)

        img = Image.new("RGBA", (int(self.rect.size.x), int(self.rect.size.y)), (0, 0, 0, 0))
        ImageDraw.Draw(img, "RGBA").rounded_rectangle(
            (0, 0, int(self.rect.size.x), int(self.rect.size.y)), radius=7, fill=col)
        
        return img

    def resize(self, size):
        super().resize(size)

        img = self.build_sprite()

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img.tobytes())

        self.label.resize(size)

    def draw(self, editor, pos):
        self.window = editor.window
        if self.rect.pos != pos:
            self.rect.move_to(glm.vec2(*pos))

        if not self.data is None:
            self.label.message = self.data.display_str
            self.label.style = TextStyle.NORMAL

        else:
            self.label.message = self.hint
            self.label.style = TextStyle.ITALICS

        self.label.old = self.old
        self.old = False

        if self.focused != self.was_focused_last:
            self.sprite = self.build_sprite()
            self.rebuild_texture()

            self.was_focused_last = self.focused

        super().draw(editor, pos)
        self.label.draw(editor, pos)

    def get_value(self):
        return self.data
    
    def handle_input(self, keycodes, mouse_buttons, input_handler):
        if input_handler.get_mouse_button_down(mouse_buttons.RIGHT):
            self.data = None
            if self.drop_callback:
                self.drop_callback(self)
            self.old = True

class HorizontalLayout(UiElement):
    can_claim_focus = True

    def __init__(self, parent, width, height, elems: list[UiElement] = []):
        super().__init__(parent, width, height)
        self.padding = glm.vec2(10, 10)

        self.elems = elems
        for elem in elems:
            width_ = ((width - self.padding.x * 2) - (self.padding.x * (len(elems) - 1))) / len(elems) 
            height_ = height - self.padding.y * 2
            elem.resize(glm.vec2(width_, height_))
            elem.parent = self

        self.focused_elem = None

        img = self.build_sprite()
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img.tobytes())

    def update_positions(self):
        for elem in self.elems:
            width_ = ((self.size.x - self.padding.x * 2) - (self.padding.x * (len(self.elems) - 1))) / len(self.elems) 
            height_ = self.size.y - self.padding.y * 2
            elem.resize(glm.vec2(width_, height_))
            elem.parent = self

    def set_padding(self, new_padding: glm.vec2):
        self.padding = new_padding
        self.update_positions()
    
    def lose_focus(self):
        self.parent.focused_elem = None
        if self.focused_elem:
            self.focused_elem.lose_focus()

        return super().lose_focus()

    def build_sprite(self):
        if self.focused:
            col = (59, 63, 68)
        else:
            col = (48, 51, 55)

        img = Image.new("RGBA", (int(self.rect.size.x), int(self.rect.size.y)), (0, 0, 0, 0))
        ImageDraw.Draw(img, "RGBA").rounded_rectangle(
            (0, 0, int(self.rect.size.x), int(self.rect.size.y)), radius=7, fill=col)
        
        return img

    def resize(self, size):
        width = size.x
        for elem in self.elems:
            width_ = ((width - self.padding.x * 2) - (self.padding.x * (len(self.elems) - 1))) / len(self.elems) 
            height_ = size.y - self.padding.y * 2
            elem.resize(glm.vec2(width_, height_))

        super().resize(size)

        img = self.build_sprite()

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *img.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img.tobytes())

    def draw(self, editor, pos):
        super().draw(editor, pos)

        if self.rect.pos != pos:
            self.rect.move_to(glm.vec2(*pos))

        draw_offset = glm.vec2(*self.padding)
        for elem in self.elems:
            elem.draw(editor, pos + draw_offset)
            draw_offset.x += elem.size.x + self.padding.x

    def handle_input(self, keycodes, mouse_buttons, input_handler):
        if self.focused_elem:
            self.focused_elem.handle_input(keycodes, mouse_buttons, input_handler)
            if self.focused_elem:
                self.hold_focus = self.focused_elem.hold_focus

                if not self.focused_elem.hold_focus:
                    if not self.focused_elem.rect.collide_point(glm.vec2(*input_handler.mouse_pos)):
                        self.focused_elem.lose_focus()
                
            return
        
        self.hold_focus = False

        for elem in self.elems:
            if elem.rect.collide_point(glm.vec2(*input_handler.mouse_pos)):
                if self.focused_elem:
                    self.focused_elem.lose_focus()
                self.focused_elem = elem
                self.focused_elem.focus()
                break

class HorizontalLine(UiElement):
    def __init__(self, parent: EditorUiWindow):
        width = parent.get_draw_data().size.x - parent.get_draw_data().padding.x * 2
        height = 30

        super().__init__(parent, width, height)

    def build_sprite(self):
        img = Image.new("RGBA", (int(self.rect.size.x), int(self.rect.size.y)), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img, "RGBA")
        draw.line((0, 14, int(self.size.x), 14), (66, 69, 71), width=2)
        draw.line((0, 16, int(self.size.x), 16), (59, 63, 68), width=2)
        return img
    
    def resize(self, size):
        return super().resize(size)
    
class ListView(UiElement):
    can_claim_focus = True
    class ListElement(UiElement):
        def __init__(self, parent: ListView, value: str):
            width = parent.size.x - parent.padding.x * 2
            height = 20

            super().__init__(parent, width, height)
            self.__val = value
            self.__label = TextElement(None, self.__val, width, height)
        
        def draw(self, editor, pos):
            super().draw(editor, pos)
            self.__label.draw(editor, pos)

        def build_sprite(self):
            if self.focused:
                col = (69, 73, 78)
            else:
                col = (58, 61, 65)

            img = Image.new("RGBA", (int(self.rect.size.x), int(self.rect.size.y)), (0, 0, 0, 0))
            ImageDraw.Draw(img, "RGBA").rounded_rectangle(
                (0, 0, int(self.rect.size.x), int(self.rect.size.y)), radius=7, outline=col, width=2)
            
            return img

        @property
        def value(self):
            return self.value

    def __init__(self, parent, width, height, values: list[str] = []):
        super().__init__(parent, width, height)
        self.padding = glm.vec2(5, 5)

        self.__values = values
        self.ui_elements: list[__class__.ListElement] = []

        print(height)
        self.rebuild_elements()

        self.was_focused = False

    def extend_values(self, new_vals: list[str]):
        self.__values.extend(new_vals)

    def set_values(self, vals: list[str]):
        self.__values = vals

    def rebuild_elements(self):
        for elem in self.__values:
            list_elem = self.ListElement(self, elem)

    def build_sprite(self):
        if self.focused:
            col = (69, 73, 78)
        else:
            col = (58, 61, 65)

        img = Image.new("RGBA", (int(self.rect.size.x), int(self.rect.size.y)), (0, 0, 0, 0))
        ImageDraw.Draw(img, "RGBA").rounded_rectangle(
            (0, 0, int(self.rect.size.x), int(self.rect.size.y)), radius=7, outline=col, width=2)
        
        return img
    
    def focus(self):
        print("WOW!")
        return super().focus()
    
    def draw(self, editor, pos):
        if self.rect.pos != pos:
            self.rect.move_to(pos)

        if self.focused != self.was_focused:
            self.sprite = self.build_sprite()
            self.rebuild_texture()
            self.was_focused = self.focused
            print("WOW!")

        gl.glEnable(gl.GL_STENCIL_TEST)
        gl.glClearStencil(0)
        gl.glClear(gl.GL_STENCIL_BUFFER_BIT)
        gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_REPLACE)
        gl.glStencilFunc(gl.GL_ALWAYS, 1, 0xFF)

        super().draw(editor, pos)

        gl.glStencilFunc(gl.GL_EQUAL, 1, 0xFF)
        gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_KEEP)

        pos_ = pos + self.padding
        for elem in self.ui_elements:
            elem.draw(editor, pos_)
            pos_.y += elem.get_height()

        # super().draw(editor, pos)

def format_num(num):
    output = f"{round(num, 10):g}"

    if "." not in output:
        output += ".0"
    return output

def build_vec3_input(parent: EditorUiWindow | HorizontalLayout, vector: glm.vec3, hint_extension: str = "Value"):
    HorizontalLayout(
        parent, (parent.draw_data.size - (parent.draw_data.padding * 2)).x, 30, [
            x_pos := InputField(None, 10, 10, "X " + hint_extension, format_num(vector.x), type_=float),
            y_pos := InputField(None, 10, 10, "Y " + hint_extension, format_num(vector.y), type_=float),
            z_pos := InputField(None, 10, 10, "Z " + hint_extension, format_num(vector.z), type_=float)
        ]).set_padding(glm.vec2(5, 5))

    def set_values(input_: InputField):
        vector.x = x_pos.get_value()
        vector.y = y_pos.get_value()
        vector.z = z_pos.get_value()

    x_pos.validate_command = InputField.validate_float            
    x_pos.run_command_when_empty = False
    x_pos.command = set_values
    x_pos.default_val = 0.0

    y_pos.validate_command = InputField.validate_float            
    y_pos.run_command_when_empty = False
    y_pos.command = set_values
    y_pos.default_val = 0.0

    z_pos.validate_command = InputField.validate_float            
    z_pos.run_command_when_empty = False
    z_pos.command = set_values
    z_pos.default_val = 0.0

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

from __future__ import annotations

import OpenGL.GL as gl
import numpy as np
import ctypes
import glfw

from pyglm import glm

from .shader_program import ShaderProgram
from . import global_vars as modules
from enum import Enum, Flag, auto

from .font import render_window_label, render_text, TextStyle, AnchorPoints, get_size
from PIL import Image, ImageDraw

from typing import TYPE_CHECKING, Callable
from typing import Any, TypeAlias, final
from dataclasses import dataclass
if TYPE_CHECKING:
    from ..editor import Window
    from ghost_engine.core.input import KeyCodes, MouseButtons, Input

else:
    KeyCodes: TypeAlias = Any
    MouseButtons: TypeAlias = Any
    Input: TypeAlias = Any

from dataclasses import dataclass
import weakref
 
@dataclass
class DragData:
    object_data: Any
    display_str: str

class LayoutMode(Enum):
    VERTICAL = 0
    HORIZONTAL = 1

HELD_DRAG_DATA: DragData = None
INF = float("inf")

class WindowDrawer:
    INST: WindowDrawer = None
    INITALIZED = False
    def __new__(cls) -> WindowDrawer:
        if __class__.INST is None:
            __class__.INST = super().__new__(cls)

        return __class__.INST
    
    def __init_subclass__(cls):
        cls.setup()

    @classmethod
    def setup(cls):
        pass

    def __init__(self):
        if WindowDrawer.INITALIZED:
            return
        
        setup()
        self.floating_windows: set[EditorUiWindow] = set()
        self.windows: set[EditorUiWindow] = set()

        self.focused_window: EditorUiWindow = None

        from .window_docker import Docker
        from .complex_elements import MenuBar
        self.docker = Docker

        self.top_bar = MenuBar(None)
        self.input = modules.input_handler()

        __class__.INITALIZED = True

    def render(self, editor: Window):
        width, height = glfw.get_window_size(glfw.get_current_context())
        ortho = glm.ortho(0, width, height, 0, -1, 1)

        WINDOW_SHADER.use()
        WINDOW_SHADER.set_mat4("uProjection", ortho)

        focused = self.docker.INST.draw(editor)
        if focused and self.focused_window != focused:                
            if self.focused_window and not self.focused_window.focused_elem:
                self.focused_window.lose_focus()
                self.focused_window = focused
                self.focused_window.focus()

            else:
                if self.focused_window:
                    self.focused_window.lose_focus()
                self.focused_window = focused
                self.focused_window.focus()

        if self.top_bar.size.x != editor.size()[0]:
            self.top_bar.resize(glm.vec2(editor.size()[0], 20))

        self.top_bar.draw(editor, glm.vec2(0, 0))
        if self.top_bar.rect.collide_point(glm.vec2(self.input.mouse_pos)):
            self.top_bar.handle_input(modules.key_codes, modules.mouse_buttons, self.input)

        for window in self.floating_windows.copy():
            window.draw(editor)

            if self.focused_window and self.focused_window.focused_elem:
                continue

            if window.rect.collide_point(glm.vec2(*editor.input_handler.mouse_pos)):
                if self.focused_window:
                    self.focused_window.lose_focus()
                self.focused_window = window
                self.focused_window.focus()

    def handle_input(self, key_codes: type[KeyCodes], mouse_buttons: type[MouseButtons], input_handler: Input):
        mouse_pos = glm.vec2(input_handler.mouse_pos)
        if self.top_bar.rect.collide_point(mouse_pos):
            self.top_bar.handle_input(key_codes, mouse_buttons, input_handler)

        elif self.focused_window:
            self.focused_window.handle_input(key_codes, mouse_buttons, input_handler)

            if not self.focused_window.rect.collide_point(mouse_pos):
                self.focused_window.lose_focus()
                self.focused_window = None

    def add_window_data(self, window_data: EditorUiWindow):
        self.windows.add(window_data)
        if not hasattr(window_data, "docked"):
            self.floating_windows.add(window_data)

WINDOW_SHADER = None
STENCIL_TEXTURE = None
VBO, VAO, EBO = None, None, None

def setup():
    global WINDOW_SHADER, VBO, VAO, EBO, STENCIL_TEXTURE
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
                vec4 albedo = texture(uTexture, vTexCoord).rgba;
                FragColor = albedo;
            }
    """)

    STENCIL_TEXTURE = gl.glGenTextures(1)
    image = Image.new("RGBA", (1, 1), (37, 37, 38, 255))
    gl.glBindTexture(gl.GL_TEXTURE_2D, STENCIL_TEXTURE)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *image.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, image.tobytes())
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

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

BASE_OFFSET = 22

class EditorUiWindow:
    SHOW_TITLE = True
    LOCKED = False
    name: str

    default_max_scroll = False
    def __init_subclass__(cls):
        setattr(cls, "instances", set())

    def __init__(self):
        self.draw_data = UiDrawData()
        self.ui_elements: list[UiElement] = []

        self.rect = UiRect(*self.draw_data.pos, *self.draw_data.size)

        self.bg_tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.bg_tex)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        
        if self.SHOW_TITLE:
            self.name_texture = gl.glGenTextures(1)

        self.build_sprite()
        self.rebuild_texture()

        self.focused_elem: weakref.ReferenceType[UiElement] = None
        self.__class__.instances.add(self)

        self.scroll = 0.0
        self.max_scroll = 0.0
        self.scroll_sensitivity = 5.0

        self.regen_stencil()

        self.list_lock = modules.threading.Lock()
        self.layout_mode = LayoutMode.VERTICAL

    def rebuild_texture(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.bg_tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *self.sprite.size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, self.sprite.tobytes())
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

        if self.SHOW_TITLE:
            text_img = render_window_label(self.name, int(self.draw_data.size.x))
            self.text_img_size = text_img.size

            gl.glBindTexture(gl.GL_TEXTURE_2D, self.name_texture)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *self.text_img_size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, text_img.tobytes())
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

    def build_sprite(self):
        width, height = self.draw_data.size
        edge = (60, 60, 60, 255)
        center = (37, 37, 38, 255)
        top_bar = (47, 47, 48, 255)
        inset = (32, 32, 33, 255)

        img = Image.new("RGBA", (int(width), int(height)))
        img_drawer = ImageDraw.Draw(img, "RGBA")
        img_drawer.rectangle((0, 0, width, height), outline=edge, fill=center, width=2)
        img_drawer.rectangle((2, height - 24, width-2, height), fill=top_bar, width=2)
        img_drawer.line((2, height - 24, width-2, height - 24), fill=inset, width=2)
        del img_drawer

        self.sprite = img

    def get_draw_data(self):
        return self.draw_data
    
    def update_max_scroll(self):
        if self.layout_mode == LayoutMode.VERTICAL:
            self.max_scroll = 0
            for elem in self.ui_elements:
                self.max_scroll += elem.get_height() + self.draw_data.padding.y

            self.max_scroll = max(0, self.max_scroll - (self.stencil_size.y))
            self.scroll = max(0, min(self.scroll, self.max_scroll))

        elif self.layout_mode == LayoutMode.HORIZONTAL:
            self.max_scroll = 0
            x = 0
            row_height = 0
            for elem in self.ui_elements:
                row_height = max(elem.get_height(), row_height)
                x += elem.size.x
                if x >= self.stencil_size.x:
                    x = elem.size.x
                    self.max_scroll += row_height + self.draw_data.padding.y
                x += self.draw_data.padding.x

            # self.max_scroll = max(0, self.max_scroll - (self.stencil_size.y))
            self.max_scroll = max(0, self.max_scroll)
            self.scroll = max(0, min(self.scroll, self.max_scroll))

        if self.default_max_scroll:
            self.scroll = self.max_scroll
    
    @final
    def regen_stencil(self):
        self.stencil_model = glm.mat4(1)

        top_offset = BASE_OFFSET if self.SHOW_TITLE else 0

        self.stencil_topleft = glm.vec2(
            self.rect.left + self.draw_data.padding.x,
            self.rect.top + self.draw_data.padding.y + top_offset
        )

        self.stencil_size = glm.vec2(
            self.rect.right - self.draw_data.padding.x,
            self.rect.bottom - self.draw_data.padding.y
        ) - self.stencil_topleft

        self.stencil_model = glm.translate(
            self.stencil_model,
            glm.vec3(*self.stencil_topleft, 0)
        )

        self.stencil_model = glm.scale(
            self.stencil_model,
            glm.vec3(*self.stencil_size, 0)
        )

    def move(self, new_x: float, new_y: float):
        """
            Moves the window to `new_x`, `new_y`. 
            Returns this class for easier method chaining.
        """
        self.draw_data.pos = glm.vec2(new_x, new_y)
        self.rect.move_to(self.draw_data.pos)

        self.regen_stencil()
        return self

    def resize(self, new_width: float, new_height: float):
        """
            Sets the window size to `new_width`, `new_height`. 
            Returns this class for easier method chaining.
        """
        self.draw_data.size = glm.vec2(new_width, new_height)
        self.rect.resize(self.draw_data.size)

        self.build_sprite()
        self.rebuild_texture()

        self.regen_stencil()
        self.update_max_scroll()
        return self
    
    def focus(self):
        modules.input_handler().scroll_callback = self.handle_scroll

    def lose_focus(self):
        modules.input_handler().scroll_callback = None

    def draw(self, editor: Window):
        global VAO

        # RoWiz (4/8/26):
        # The shader should always be bound by the editor before this is called, but just in case,
        # bind it here.
        WINDOW_SHADER.use()

        # Base Window stuff
        win_model = self.draw_data.get_configuration_out()
        WINDOW_SHADER.set_mat4("uModel", win_model)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.bg_tex)

        gl.glBindVertexArray(VAO)
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
    
        # RoWiz (4/29/26):
        # Made it only draw the window title when not docked.
        if not hasattr(self, "docked") and self.SHOW_TITLE:
            model = glm.mat4(1)
            model = glm.translate(model, glm.vec3(*(self.draw_data.pos + glm.vec2(3, 0)), 0))
            model = glm.scale(model, glm.vec3(*self.text_img_size, 0))
            WINDOW_SHADER.set_mat4("uModel", model)

            gl.glBindTexture(gl.GL_TEXTURE_2D, self.name_texture)

            gl.glBindVertexArray(VAO)
            gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
            gl.glBindVertexArray(0)

            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

        # Create a stencil before element rendering
        WINDOW_SHADER.set_mat4("uModel", self.stencil_model)
        gl.glEnable(gl.GL_STENCIL_TEST)
        gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_REPLACE)
        gl.glStencilFunc(gl.GL_ALWAYS, 1, 0xFF)

        gl.glBindTexture(gl.GL_TEXTURE_2D, STENCIL_TEXTURE)
        gl.glBindVertexArray(VAO)
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)

        gl.glStencilFunc(gl.GL_EQUAL, 1, 0xFF)
        gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_KEEP)

        # Child Elements
        pos = self.draw_data.pos + self.draw_data.padding
        if self.SHOW_TITLE:
            pos.y += BASE_OFFSET - self.scroll
        else:
            pos.y -= self.scroll

        # def get_element_in_window(elem: UiElement):
        #     stencil_bottomright = self.stencil_topleft + self.stencil_size
        #     if pos.y > stencil_bottomright.y or pos.x > stencil_bottomright.x: return False
        #     if pos.y + elem.get_height() < self.stencil_topleft.y or pos.x + child.size.x < self.stencil_topleft.x: return False
        #     else: return True

        cur_row_height = 0
        start_pos_x = pos.x
        with self.list_lock:
            for child in self.ui_elements:
                if child.shown: # and get_element_in_window(child):
                    next_pos = glm.vec2(*pos)
                    if self.layout_mode == LayoutMode.VERTICAL:
                        next_pos.y += child.get_height() + self.draw_data.padding.y

                    elif self.layout_mode == LayoutMode.HORIZONTAL:
                        cur_row_height = max(cur_row_height, child.size.y)
                        next_pos.x += child.size.x

                        if next_pos.x >= (self.stencil_size.x):
                            pos.x = start_pos_x
                            pos.y += cur_row_height + self.draw_data.padding.y
                            cur_row_height = 0

                        next_pos.x += self.draw_data.padding.x

                    child.draw(editor, pos)
                    pos = next_pos

        gl.glClearStencil(0)
        gl.glClear(gl.GL_STENCIL_BUFFER_BIT)

        gl.glDisable(gl.GL_STENCIL_TEST)

    def handle_input(self, key_codes: type[KeyCodes], mouse_buttons: type[MouseButtons], input_handler: Input):
        global HELD_DRAG_DATA
        if not self.focused_elem and HELD_DRAG_DATA and input_handler.get_mouse_button_up(mouse_buttons.LEFT):
            HELD_DRAG_DATA = None
        
        if self.focused_elem and self.focused_elem():
            elem = self.focused_elem()
            if input_handler.get_mouse_button_down(mouse_buttons.LEFT):
                HELD_DRAG_DATA = elem.get_drag_data()
            elif not elem.rect.collide_point(glm.vec2(*input_handler.mouse_pos)) and not elem.hold_focus:
                elem.lose_focus()
                self.focused_elem = None

            else:
                if HELD_DRAG_DATA and input_handler.get_mouse_button_up(mouse_buttons.LEFT):
                    elem.drop_drag_data(HELD_DRAG_DATA)
                    HELD_DRAG_DATA = None
                    elem.handle_input(key_codes, mouse_buttons, input_handler)
                elif HELD_DRAG_DATA:
                    elem.highlight_drag_data(HELD_DRAG_DATA)
                else:
                    elem.handle_input(key_codes, mouse_buttons, input_handler)

        else:
            for elem in self.ui_elements:
                if not elem.shown:
                    continue
                
                if not elem.can_claim_focus:
                    continue

                if elem.rect.collide_point(glm.vec2(*input_handler.mouse_pos)):
                    if self.focused_elem and self.focused_elem():
                        self.focused_elem().lose_focus()

                    self.focused_elem = weakref.ref(elem)
                    self.focused_elem().focus()

                    break
    
    @property
    def renderable_width(self):
        return self.draw_data.size.x - self.draw_data.padding.x * 2
    
    @property
    def renderable_height(self):
        return self.draw_data.size.y - self.draw_data.padding.y * 2 - 30
    
    def handle_scroll(self, x_off, y_off):
        self.scroll = max(0.0, min(self.scroll - y_off * self.scroll_sensitivity, self.max_scroll))
        
class UiElement:
    can_claim_focus: bool = False
    hold_focus: bool = False

    min_size = glm.vec2(1)
    max_size = glm.vec2(float('inf'))
    
    def __init__(self, parent: EditorUiWindow, width: float, height: float, **kwrds):
        self.size = glm.vec2(width, height)
        self.pos_offset = glm.vec2(0, 0)

        self.rect = UiRect(0, 0, width, height)

        self.focused = False
        self.interaction_finished_callback: Callable[[UiElement, None]] = None

        if parent:
            self.parent = parent
            self.parent.ui_elements.append(self)


        self.sprite = self.build_sprite()
        self.texture_type = kwrds.pop("tex_type", gl.GL_TEXTURE_2D)
        self.rebuild_texture_on_resize = kwrds.pop("tex_resize", True)
        if kwrds.pop("build_texture", True):
            self.texture = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

            self.rebuild_texture()
            self.texture_old = False
        else:
            self.texture = None
            self.texture_old = True

        self.resize_callback = None

        # Render hooks
        self.pre_render_hook = None
        self.post_render_hook = None

        self.draggable_data: DragData = None
        self.active = True
        self.shown = True

    def update_rect(self, new_pos: glm.vec2):
        self.rect.move_to(new_pos)

    @final
    def toggle_hidden(self):
        self.shown = not self.shown

    def resize_to_fill_window(self):
        self.size = glm.vec2(self.parent.draw_data.size.x - self.parent.draw_data.padding.x * 2, 
                             self.parent.draw_data.size.y - self.parent.draw_data.padding.y * 2 - BASE_OFFSET)
        
        self.rect.resize(self.size)
        
        self.sprite = self.build_sprite()
        if self.rebuild_texture_on_resize:
            self.rebuild_texture()

        if self.resize_callback:
            self.resize_callback(self)

    def resize(self, size: glm.vec2):
        size = glm.vec2(
            max(self.min_size.x, min(size.x, self.max_size.x)), 
            max(self.min_size.y, min(size.y, self.max_size.y))
        )

        self.size = size
        self.rect.resize(size)

        self.sprite = self.build_sprite()
        if self.rebuild_texture_on_resize:
            self.rebuild_texture()

        if self.resize_callback:
            self.resize_callback(self)

    def draw(self, editor: Window, pos: glm.vec2):
        global VAO
        if self.texture_old:
            self.rebuild_texture()
            self.texture_old = False

        if self.rect.pos != pos:
            self.rect.move_to(glm.vec2(*pos))

        if self.pre_render_hook:
            self.pre_render_hook(self)
        gl.glBindTexture(self.texture_type, self.texture)

        model = glm.mat4(1)
        model = glm.translate(model, glm.vec3(*(pos + self.pos_offset), 0))
        model = glm.scale(model, glm.vec3(*self.size, 0))

        WINDOW_SHADER.use()
        WINDOW_SHADER.set_mat4("uModel", model)

        gl.glBindVertexArray(VAO)
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)

        gl.glBindTexture(self.texture_type, 0)

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
        if self.texture is None:
            self.texture = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

        else:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            
        img = self.sprite
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
    
    @property
    def bottomleft(self):
        return glm.vec2(self.left, self.bottom)

    def collide_point(self, point: glm.vec2):
        return self.left < point.x < self.right and self.top < point.y < self.bottom

# class PopupFlags(Flag):
#     CLOSE_ON_SELECT = auto()

class Popup(EditorUiWindow):
    SHOW_TITLE = False
    def __init__(self, source_pos: glm.vec2):
        super().__init__()

        self.draw_data.padding.x = 5
        self.draw_data.padding.y = 5

        self.move(*source_pos)
        self.registered = False

        self.owner_rect: UiRect = None
        self.parent: Popup = None
        self.subpopup: Popup = None

        # self.flags = 0

        self.input = modules.input_handler()

    def autosize(self):
        width = 0
        height = self.draw_data.padding.y

        for elem in self.ui_elements:
            width = max(width, elem.size.x)
            height += elem.size.y + self.draw_data.padding.y

        width += self.draw_data.padding.x * 2

        self.resize(width, height)

    def draw(self, editor):
        self.autosize()
        if any([self.input.get_mouse_button_down(mouse_button) for mouse_button in modules.mouse_buttons]) and not self.mouse_over():
            self.deregister()

        return super().draw(editor)

    def mouse_over(self):
        mp = glm.vec2(self.input.mouse_pos)
        if self.owner_rect and self.owner_rect.collide_point(mp):
            return True
        
        if self.rect.collide_point(mp):
            return True
        
        if self.subpopup and self.subpopup.mouse_over():
            return True
        
        return False

    def register(self):
        WindowDrawer().add_window_data(self)
        self.registered = True

    def deregister(self):
        if self in WindowDrawer().windows:
            WindowDrawer().windows.remove(self)
            WindowDrawer().floating_windows.remove(self)

        if self.subpopup:
            self.subpopup.deregister()
        self.subpopup = None

        if self.parent:
            self.parent.subpopup = None

        self.registered = False

    def build_sprite(self):
        width, height = self.draw_data.size
        edge = (60, 60, 60, 255)
        center = (37, 37, 38, 255)

        img = Image.new("RGBA", (int(width), int(height)))
        img_drawer = ImageDraw.Draw(img, "RGBA")
        img_drawer.rectangle((0, 0, width, height), outline=edge, fill=center, width=2)
        del img_drawer

        self.sprite = img

    def open_subpopup(self, source_elem: UiElement):
        if self.subpopup:
            self.subpopup.deregister()

        self.subpopup = Popup(glm.vec2(source_elem.rect.right, source_elem.rect.top))
        self.subpopup.register()
        # self.subpopup.flags = flags
        self.subpopup.parent = self
        return self.subpopup

    def set_children(self, children: list[UiElement]):
        for elem in children:
            elem.parent = self

        self.ui_elements = children
        return self

def open_popup(source: glm.vec2):
    popup = Popup(source)
    return popup

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

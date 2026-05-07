from __future__ import annotations

import OpenGL.GL as gl

from .window_drawer import *
from .font import TextStyle
from . import globals

from .console import ConsoleLogger

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ghost_engine.object import Object

import sys, math
import asyncio

import colorama
from enum import Enum
from dataclasses import dataclass

class SceneView(EditorUiWindow):
    name = "Scene"
    def __init__(self):
        super().__init__()
        self.view = UiElement(self, 0, 0)
        self.view.resize_callback = self.view_resize_callback

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, globals.editor_window.scene_framebuffer)
        gl.glFramebufferTexture2D(gl.GL_READ_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.view.texture, 0)

        self.rbo = gl.glGenRenderbuffers(1)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.rbo)
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT24, math.ceil(self.view.size.x), math.ceil(self.view.size.y))
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_RENDERBUFFER, self.rbo)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def view_resize_callback(self, view: UiElement):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, globals.editor_window.scene_framebuffer)
        gl.glFramebufferTexture2D(gl.GL_READ_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.view.texture, 0)

        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.rbo)
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT24, math.ceil(self.view.size.x), math.ceil(self.view.size.y))
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_RENDERBUFFER, self.rbo)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def draw(self, editor):
        window = glfw.get_current_context()
        size = glfw.get_window_size(window)

        gl.glViewport(0, 0, math.ceil(self.view.size.x), math.ceil(self.view.size.y))
        editor.render_scene()
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
    
    object_type = None
    def __init__(self):
        super().__init__()

        self.draw_data.padding.x = 10
        self.draw_data.padding.y = 5

        self.locked = False
        
    def resize(self, new_width, new_height):
        old_renderable_width = self.draw_data.size.x - self.draw_data.padding.x * 2
        new_renderable_width = new_width - self.draw_data.padding.x * 2
        for ui_obj in self.ui_elements:
            width_ratio = ui_obj.size.x / old_renderable_width

            ui_obj.resize(glm.vec2(width_ratio * new_renderable_width, ui_obj.size.y))
        
        super().resize(new_width, new_height)
        self.update_max_scroll()
    
    async def build_for_object(self, data):
        if TYPE_CHECKING:
            assert isinstance(self.object_type, type[Object])
            assert isinstance(data, Object)

        def set_name(name_in: InputField):
            data.name = name_in.get_value()
            Hierarchy.rebuild_windows()

        # Name Data
        name_in = InputField(self, self.renderable_width, 30, hint="Object Name...", starting_message=data.name)
        name_in.command = lambda n=name_in: set_name(n)
        name_in.default_val = ""

        HorizontalLine(self)

        # Transform Data
        TextElement(self, "Transform", self.renderable_width, 12).set_text_size(12).set_anchor("lm", TextRenderAnchor.middle_left)
        parentField = DropField(self, self.renderable_width, 30, "Parent Object", DragData(
            data.transform.parent.gameobject, data.transform.parent.gameobject.name) if data.transform.parent else None)
        def get_children(obj: Object):
            children = set()
            for child in obj.children:
                children.add(child)
                children.update(get_children(child))
            return children

        def try_set_parent(parentField: DropField):
            if not parentField.get_value():
                data.transform.parent = None
                Hierarchy.rebuild_windows()
                return
            
            if parentField.get_value().object_data in get_children(data):
                globals.logger("INSPECTOR").log_error("Cannot set the parent of an object to one of it's children!")
                parentField.data = None
                return
            
            elif parentField.get_value().object_data == data:
                globals.logger("INSPECTOR").log_error("Cannot parent an object to itself!")
                parentField.data = None
                return
            data.transform.parent = parentField.get_value().object_data.transform
            Hierarchy.rebuild_windows()
        parentField.drop_callback = try_set_parent
        build_vec3_input(self, data.transform.localpos, "Position")
        build_vec3_input(self, data.transform.localrot, "Rotation")
        build_vec3_input(self, data.transform.scale, "Size")

        for component in data.components:
            comp_class = type(component)
            TextElement(self, comp_class.__name__, self.renderable_width, 30)

            for var_name, var_data in vars(comp_class).items():
                if isinstance(var_data, globals.editor_field):
                    var = getattr(component, var_name)
                    if var_data.type == glm.vec3:
                        build_vec3_input(self, var)

                    elif var_data.type == float:
                        InputField(self, self.renderable_width, 20, var_name, str(var), float)

                    elif var_data.type == str:
                        InputField(self, self.renderable_width, 20, var_name, var, str)
                    
                    elif var_data.type == bool:
                        Checkbox(self, var)

    async def build(self, data):
        self.scroll = 0.0
        if self.locked:
            return
        
        self.ui_elements.clear()        
        if isinstance(data, self.object_type):
            await self.build_for_object(data)
        
        self.update_max_scroll()
    
    @classmethod
    def set_data(cls, data):
        if not cls.object_type:
            cls.object_type = getattr(sys.modules["ghost_engine.object"], "Object")

        for inst in cls.instances:
            inst: Inspector

            asyncio.run(inst.build(data))

class Hierarchy(EditorUiWindow):
    name = "Hierarchy"

    def __init__(self):
        super().__init__()

        self.draw_data.padding.x = 5
        self.draw_data.padding.y = 5

        self.manager = globals.scene_manager()
        self.object_buttons: set[Button] = set()

        self.object_type = None
        self.create_object_button: Button = Button(self, 100, 30, "Create Gameobject", self.create_object)

        Hierarchy.instances.add(self)

        asyncio.run(self.build())

        self.old = False

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

    async def build(self):
        self.object_buttons.clear()
        self.ui_elements.clear()

        self.ui_elements.append(self.create_object_button)

        root_objects = list(filter(lambda object_: object_.transform.parent == None, self.manager.game_objects))
        def build_layer(objects: list, width):
            for obj in objects:
                button = Button(self, width, 30, obj.name, lambda object_=obj: Inspector.set_data(object_))
                button.pos_offset = glm.vec2((self.draw_data.size.x - self.draw_data.padding.x * 2) - width, 0)

                button.draggable_data = DragData(obj, obj.name)

                build_layer(obj.children, max(20, width-20))
                self.object_buttons.add(button)

            return True

        build_layer(root_objects, self.draw_data.size.x - self.draw_data.padding.x * 2)
    
    @classmethod
    def rebuild_windows(cls):
        for inst in cls.instances:
            asyncio.run(inst.build())

    def draw(self, editor):
        if self.old:
            asyncio.run(self.build())
            self.old = False
            
        super().draw(editor)

class Scenes(EditorUiWindow):
    name = "Scenes"
    def __init__(self):
        super().__init__()
        self.scene_manager = globals.scene_manager()
        self.draw_data.padding = glm.vec2(10, 10)
        self.list_view = ListView(self, self.renderable_width, self.renderable_height, self.scene_manager.scenes)
        self.list_view.select_item_callback = self.select_scene_callback

        self.selected_scene: ListValue = None
        def open_scene():
            self.scene_manager.load_scene(self.selected_scene.val, False)

        self.horiz_group = HorizontalLayout(self, self.renderable_width, 50, [
            scene_label := TextElement(None, "", 1, 1),
            scene_index := TextElement(None, "", 1, 1),
            Button(None, 4, 4, "Open", open_scene)
        ])
        self.horiz_group.padding.x = 5
        self.horiz_group.padding.y = 5
        self.horiz_group.rebuild_elems()
        self.scene_label = scene_label
        self.scene_index = scene_index

        self.horiz_group.shown = False

    def select_scene_callback(self, info: ListValue):
        self.scene_label.message = info.val
        self.scene_label.old = True

        self.scene_index.message = str(info.index)
        self.scene_index.old = True

        self.horiz_group.shown = True
        self.list_view.shown = False
        self.selected_scene = info

    def resize(self, new_width, new_height):
        self.list_view.resize(glm.vec2(new_width, new_height - 30) - self.draw_data.padding * 2)
        self.horiz_group.resize(glm.vec2(new_width, 50) - self.draw_data.padding * 2)

        super().resize(new_width, new_height)

@dataclass
class LogColor:
    format_str: str
    dim_col: str
    norm_col: str
    bright_col: str

class LogColors(Enum):
    RED = LogColor(colorama.Fore.RED, "#c61111", "#ff0000", "#fb4242")
    WHITE = LogColor(colorama.Fore.WHITE, "#888888", "#afafaf", "#ffffff")
    YELLOW = LogColor(colorama.Fore.YELLOW, "#EECC46", "#FFD738", "#FFCC00")

@dataclass(frozen=True)
class LogStr:
    color: tuple[int, int, int]
    text: str
    style: TextStyle

class ConsoleWindow(EditorUiWindow):
    name = "Console"
    console = ConsoleLogger()
    def __init__(self):
        super().__init__()
        self.console.write_callback = self.update

        self.set_scroll_on_add = True

        self.draw_data.padding.x = 10
        self.draw_data.padding.y = 10

    @staticmethod
    def hex_to_decimal_list(hex_: str):
        return [int(hex_[i:i+2], 16) for i in range(0, len(hex_), 2)]

    @staticmethod
    def format_str(data: str):
        color = "#ffffff"
        style = TextStyle.NORMAL
        for col in list(LogColors):
            name, col_data = col.name, col.value

            if data.startswith(col_data.format_str):
                data = data.replace(col_data.format_str, "")
                if data.startswith(colorama.Style.DIM):
                    color = col_data.dim_col
                    data = data.replace(colorama.Style.DIM, "")
                    break

                if data.startswith(colorama.Style.NORMAL):
                    color = col_data.norm_col
                    data = data.replace(colorama.Style.NORMAL, "")
                    break

                if data.startswith(colorama.Style.BRIGHT):
                    color = col_data.bright_col
                    data = data.replace(colorama.Style.BRIGHT, "")
                    break
        
        if data.startswith("\x1b[3m"):
            style = TextStyle.ITALICS
            data = data.replace("\x1b[3m", "")

        data = data.removesuffix(colorama.Style.RESET_ALL + colorama.Fore.RESET)
        return LogStr(__class__.hex_to_decimal_list(color[1:]), data, style)

    def add_data(self, data: str):
        log_str = self.format_str(data)
        elem = TextElement(None, log_str.text, self.renderable_width, 12, build_texture=False)
        elem.style = log_str.style
        elem.color = tuple(log_str.color)

        elem.set_text_size(12)
        elem.set_anchor("lt", TextRenderAnchor.top_left)
        elem.parent = self

        with self.list_lock:
            self.ui_elements.reverse()
            self.ui_elements.insert(0, elem)
            self.ui_elements = self.ui_elements[:self.console.max_length]
            self.ui_elements.reverse()

    def resize(self, new_width, new_height):
        super().resize(new_width, new_height)

        with self.list_lock:
            for elem in self.ui_elements:
                elem.resize(glm.vec2(new_width, 12))
    
    @classmethod
    def update(cls, data: str):
        for inst in cls.instances:
            inst.add_data(data)

class FileViewer(EditorUiWindow):
    name = "Files"
    def __init__(self):
        super().__init__()
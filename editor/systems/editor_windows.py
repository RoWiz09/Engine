from __future__ import annotations

import OpenGL.GL as gl

from .window_drawer import *
from .simple_elements import *
from .complex_elements import *

from .font import TextStyle
from . import global_vars

from .console import ConsoleLogger

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ghost_engine.object import GameObject
    from ghost_engine.datatypes.engine_data_type import DataType

import sys, math
import asyncio

import colorama
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import os, subprocess
from pyglm import glm

from .reload_behaviors import reload_behaviors

class SceneView(EditorUiWindow):
    name = "Scene"
    def __init__(self):
        super().__init__()
        self.view = UiElement(self, 0, 0)
        self.view.resize_callback = self.view_resize_callback

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, global_vars.editor_window.scene_framebuffer)
        gl.glFramebufferTexture2D(gl.GL_READ_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.view.texture, 0)

        self.rbo = gl.glGenRenderbuffers(1)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.rbo)
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT24, math.ceil(self.view.size.x), math.ceil(self.view.size.y))
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_RENDERBUFFER, self.rbo)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def view_resize_callback(self, view: UiElement):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, global_vars.editor_window.scene_framebuffer)
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
        self.regen_stencil()

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
            assert isinstance(self.object_type, type[GameObject])
            assert isinstance(data, GameObject)

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
        def get_children(obj: GameObject):
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
                global_vars.logger("INSPECTOR").log_error("Cannot set the parent of an object to one of it's children!")
                parentField.data = None
                return
            
            elif parentField.get_value().object_data == data:
                global_vars.logger("INSPECTOR").log_error("Cannot parent an object to itself!")
                parentField.data = None
                return
            data.transform.parent = parentField.get_value().object_data.transform
            Hierarchy.rebuild_windows()
        parentField.drop_callback = try_set_parent
        build_vec3_input(self, data.transform.localpos, "Position")
        build_vec3_input(self, data.transform.localrot, "Rotation")
        build_vec3_input(self, data.transform.scale, "Size")

        HorizontalLine(self)

        format_name = lambda f: func.__name__.replace("_", " ").title()

        for component in data.behaviors:
            comp_class = type(component)
            TextElement(self, comp_class.__name__, self.renderable_width, 30)

            for var_name, var_data in vars(comp_class).items():
                if isinstance(var_data, global_vars.editor_field):
                    var = getattr(component, var_name)
                    if var_data.type == glm.vec3:
                        build_vec3_input(self, var)

                    elif var_data.type == float:
                        input_field = LabeledInput(self, self.renderable_width, 20, var_name, str(var), float)
                        input_field.command = lambda f, c=component, s=var_name: setattr(c, s, f.get_value() if f.get_value() else 1.0)
                        input_field.validate_command = InputField.validate_float

                    elif var_data.type == str:
                        input_field = LabeledInput(self, self.renderable_width, 20, var_name, var, str)
                        input_field.command = lambda f, c=component, s=var_name: setattr(c, s, f.get_value())
                    
                    elif var_data.type == bool:
                        checkbox = LabeledCheckbox(self, self.renderable_width, 20, var_name, var)
                        checkbox.command = lambda f, c=component, s=var_name: setattr(c, s, f.get_value())

                    elif issubclass(var_data.type, global_vars.engine_data_type):
                        if TYPE_CHECKING:
                            var: DataType

                        disp_type, val = var.display()
                        if disp_type == global_vars.engine_display_methods.DROP_FIELD:
                            field = DropField(self, self.renderable_width, 20, var_name, DragData(val, str(val)))
                            field.filter_ = lambda f, v=var: v.filter_input(f.object_data)
                            field.drop_callback = lambda f, v=var: v.set_value(f.get_value().object_data)

            for owner, funcs in component.editor_button_registry.items():
                if not isinstance(component, owner):
                    continue

                for func in funcs:
                    Button(self, self.renderable_width, 20, format_name(func), lambda f=func, c=component: f(c))
        
            HorizontalLine(self)

        Button(self, self.renderable_width, 20, "Add Behavior", None)

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
            cls.object_type = getattr(sys.modules["ghost_engine.object"], "GameObject")

        for inst in cls.instances:
            asyncio.run(inst.build(data))

class Hierarchy(EditorUiWindow):
    name = "Hierarchy"

    def __init__(self):
        super().__init__()

        self.draw_data.padding.x = 5
        self.draw_data.padding.y = 5
        self.regen_stencil()

        self.manager = global_vars.scene_manager()
        self.object_buttons: set[Button] = set()

        self.object_type = None
        self.create_object_button: Button = Button(self, 100, 30, "Create Gameobject", self.create_object)

        Hierarchy.instances.add(self)

        asyncio.run(self.build())

        self.old = False

    def create_object(self):
        if not self.object_type:
            self.object_type = getattr(sys.modules["ghost_engine.object"], "GameObject")
        
        new_obj = self.object_type("New Gameobject", self.manager.materials["base_mat"])
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
        self.scene_manager = global_vars.scene_manager()

        self.draw_data.padding = glm.vec2(10, 10)
        self.regen_stencil()

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
    default_max_scroll = True
    def __init__(self):
        super().__init__()
        self.console.write_callback = self.update

        self.draw_data.padding.x = 10
        self.draw_data.padding.y = 10
        self.regen_stencil()

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
            self.ui_elements.append(elem)
            self.ui_elements = self.ui_elements[-self.console.max_length:]

        self.update_max_scroll()

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
    RBT_REPLACEMENTS = {"ClassName": None}

    name = "Files"
    def __init__(self):
        super().__init__()

        self.layout_mode = LayoutMode.HORIZONTAL
        self.draw_data.padding.x = 10
        self.draw_data.padding.y = 10
        self.old = True

        self.selected_dir = Path("assets")

        # Template files
        self.script_templates: list[Path] = []
        for dirpath, dirnames, filenames in self.selected_dir.walk():
            for filename in filenames:
                if filename.endswith(".rbt"):
                    self.script_templates.append(dirpath / filename)

        self.sidebar = []
        for pkg in sorted(self.selected_dir.iterdir(), key=lambda p: p.name == "GhostEngine"):
            self.sidebar.append(Button(None, 75, 20, pkg.name, lambda pkg_=pkg: self.route_to(pkg_)))

        self.build_sprite()
        self.rebuild_texture()
        self.regen_stencil()

    def route_to(self, new_path: Path):
        self.selected_dir = new_path
        self.old = True

    async def build(self):
        self.ui_elements.clear()
        if self.selected_dir.parts[-1] != "assets":
            Button(self, 100, 100, "Back", lambda: self.route_to(Path(os.sep.join(self.selected_dir.parts[:-1]))))

        for file in sorted(os.listdir(self.selected_dir), key=lambda x: (not (self.selected_dir / x).is_dir(), x.lower())):
            filepath = self.selected_dir / file
            # Exclude __pycache__ from directory list
            if file == "__pycache__": 
                continue

            if filepath.is_dir() and not filepath.name.startswith("."):
                Button(self, 100, 100, filepath.name, lambda f = filepath: self.route_to(f))

            elif filepath.is_file():
                # Now we need to get the file type!
                file_suffix = filepath.suffix
                if file_suffix == ".py":
                    Button(self, 100, 100, filepath.name, lambda f = filepath.absolute(): subprocess.run(["code", "-r", "assets", str(f)], shell=True))

                elif file_suffix == ".rscene":
                    Button(self, 100, 100, filepath.name, lambda f = filepath: modules.scene_manager().load_scene_async(f.name.removesuffix(".rscene"), alert_scripts=False))

                else:
                    button = Button(self, 100, 100, filepath.name, None)
                    button.draggable_data = DragData(str(filepath), str(filepath))

        self.update_max_scroll()

    class FileTypes(Enum):
        SCRIPT = 0

    def create_file(self, filename: str, file_type: FileTypes, *args):
        match file_type:
            case self.FileTypes.SCRIPT:
                behavior_name, template_id = args
                self.RBT_REPLACEMENTS["ClassName"] = behavior_name

                template: Path = self.script_templates[template_id]
                template_data = template.read_text()
                for key, value in self.RBT_REPLACEMENTS.items():
                    template_data = template_data.replace(key, value)

                path: Path = self.selected_dir / filename
                path.write_text(template_data)

                self.RBT_REPLACEMENTS["ClassName"] = None

    def open_new_file_subpopup(self, popup: Popup, button):
        subpopup = popup.open_subpopup(button)
        def open_new_script_subpopup(popup: Popup, button):
            subpopup = popup.open_subpopup(button)

            bn_ = InputField(subpopup, 120, 20, "Behavior Name", "empty_class")
            fn_ = InputField(subpopup, 120, 20, "File Name", "empty_behavior.py")

            button = Button(subpopup, 120, 20, "Create", None)
            button.click_callback = lambda bn=bn_, fn=fn_: self.create_file(fn.get_value(), self.FileTypes.SCRIPT, bn.get_value(), 0)

        button = Button(subpopup, 100, 20, "New Behavior", None)
        button.click_callback = lambda p=subpopup, b=button: open_new_script_subpopup(p, b)

    def handle_input(self, key_codes, mouse_buttons, input_handler):
        if input_handler.get_mouse_button_down(mouse_buttons.RIGHT):
            if self.selected_dir.parts[-1] != "assets":
                popup = open_popup(glm.vec2(input_handler.mouse_pos))
                button = Button(popup, 90, 20, "New File", None)
                button.click_callback = lambda p=popup, b=button: self.open_new_file_subpopup(p, b)
                button = Button(popup, 90, 20, "New Directory", None)
                button = Button(popup, 90, 20, "Reload", reload_behaviors)
                popup.register()

        return super().handle_input(key_codes, mouse_buttons, input_handler)

    def draw(self, editor):
        if self.old:
            asyncio.run(self.build())
            self.old = False

        return super().draw(editor)
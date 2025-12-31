from __future__ import annotations
from collections.abc import Iterable

from ..core.scene_manager import SceneManager
from ..object import Object
from ..scripts.behavior import Behavior, EditorField

from ..core.logger import Logger
from pyglm import glm

import imgui

menu_registry: dict[str, list[EditorWindow]] = {}
def register_menu(name: str):
    global menu_registry

    menu_registry[name] = []

register_menu("Scene")

class EditorWindow:
    menu = None
    allow_multiple = True
    keybind = ""

    def __init_subclass__(cls: object):
        if cls.menu in menu_registry:
            menu_registry[cls.menu].append(cls)

    def render(self) -> bool:
        window = imgui.begin(type(self).__name__, True)
        if not window.opened:
            imgui.end()
            return None

        return window

class Hierarchy(EditorWindow):
    menu = "Scene"
    keybind = "Ctrl+H"

    def render(self) -> Object | None:
        window = super().render()
        if not window:
            return True

        obj_id = 0
        
        from ..core.window import Window
        with window:
            hierarchy = SceneManager().get_by_hierarchy()[None]
            
            for obj, children in hierarchy.items():
                if imgui.button(obj.name, 200):
                    inspector = Inspector()
                    inspector.object = obj
                    Window().open_editor_window(inspector)

                steps = {}
                child_idx = 0
                cur_children: dict = children
                while True:
                    if child_idx < len(cur_children):
                        child_obj = list(cur_children.keys())[child_idx]

                        imgui.set_cursor_pos_x(20 * (len(steps) + 1) + 8)
                        imgui.push_id(str(obj_id))
                        if imgui.button(child_obj.name, 200 - 20 * (len(steps) + 1)):
                            inspector = Inspector()
                            inspector.object = child_obj
                            Window().open_editor_window(inspector)

                        imgui.pop_id()

                        child_idx += 1
                        obj_id += 1

                        if cur_children[child_obj] != {}:
                            steps[obj] = (cur_children, child_idx)
                            cur_children = cur_children[child_obj]
                            child_idx = 0

                    else:
                        if len(steps) == 0:
                            break

                        else:
                            cur_children, child_idx = list(steps.values())[-1]
                            steps = dict(list(steps.items())[:-1])

        return False

class Inspector(EditorWindow):
    allow_multiple = False
    def __init__(self):
        self.object: Object = None
        self.cur_comp_category = None

    def render(self):
        if self.object is None:
            Logger("EDITOR").log_error("An inspector is missing an object! How did that happen?!")
            return True
        
        window = super().render()
        if not window:
            return True
        
        with window:
            width = imgui.get_window_width()
            changed, value = imgui.input_text_with_hint("Name:", "Object Name", self.object.name)
            imgui.same_line()
            imgui.set_cursor_pos_x(width - 40)
            changed2, val = imgui.checkbox("", self.object.enabled)
            if changed or changed2:
                self.object.name = value
                self.object.enabled = val

            # Transform
            changed, values = imgui.drag_float3("Position:", *self.object.transform.localpos)
            if changed:
                self.object.transform.localpos = glm.vec3(values)

            changed, values = imgui.drag_float3("Rotation:", *self.object.transform.localrot)
            if changed:
                self.object.transform.localrot = glm.vec3(values)

            changed, values = imgui.drag_float3("Scale:", *self.object.transform.scale)
            if changed:
                self.object.transform.scale = glm.vec3(values)

            var_id = 0
            for component in self.object.components:
                imgui.separator()
                imgui.text(type(component).__name__)
                imgui.same_line()
                imgui.set_cursor_pos_x(width - 100)
                imgui.push_id(str(var_id))
                changed, val = imgui.checkbox("Active: ", component.enabled)
                imgui.pop_id()
                var_id += 1
                if changed:
                    component.enabled = val

                # --- Iterate over EditorFields on the class ---
                for var_name, field in vars(type(component)).items():
                    imgui.push_id(str(var_id))
                    if isinstance(field, EditorField):
                        value = getattr(component, var_name)
                        
                        field_type = field.type.lower()
                        if field_type == "bool":
                            changed, val = imgui.checkbox(var_name, value)
                        elif field_type == "int":
                            changed, val = imgui.input_int(var_name, value)
                        elif field_type == "float":
                            changed, val = imgui.input_float(var_name, value)
                        elif field_type == "vec3":
                            changed, vals = imgui.input_float3(var_name, *value)
                            val = glm.vec3(vals) if changed else value
                        elif field_type == "str":
                            changed, val = imgui.input_text(var_name, value)
                        else:
                            changed = False
                            val = value

                        if changed:
                            setattr(component, var_name, val)

                    elif field in Behavior.editor_button_registry:
                        imgui.button(var_name, imgui.get_window_width())

                    imgui.pop_id()
                    var_id += 1
            imgui.separator()
            if imgui.button("Add Component"):
                imgui.open_popup("Components")

            with imgui.begin_popup("Components") as comp_popup:
                if comp_popup:
                    if self.cur_comp_category is None:
                        for name in Behavior.component_category_registry.keys():
                            if name is None:
                                Logger("EDITOR").log_warning("Script category cannot be None!")
                            elif imgui.button(name, 100):
                                self.cur_comp_category = name

                    else:
                        if imgui.button("Back", 100):
                            self.cur_comp_category = None
                            return False

                        for script in Behavior.component_category_registry[self.cur_comp_category]:
                            if imgui.button(script.__name__, 100):
                                self.object.add_component(script(self.object))
                                self.cur_comp_category = None
                                imgui.close_current_popup()

        return False

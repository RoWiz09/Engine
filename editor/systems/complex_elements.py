from __future__ import annotations

from typing import override

from .window_drawer import *
from .simple_elements import *

from .font import get_size

class MenuBar(UiElement):
    can_claim_focus = True
    class MenuButton(UiElement):
        can_claim_focus = True
        def __init__(self, menu_name: str, **kwrds):
            width = get_size(menu_name, TextStyle.NORMAL, 12).x
            super().__init__(None, width + 15, 20, **kwrds)

            self.text = TextElement(None, menu_name, width + 15, 20)
            self.text.set_text_size(12).set_anchor("mm", TextRenderAnchor.middle_middle)

            self.elems = []

        def add_elem(self, ui_elem: UiElement):
            self.elems.append(ui_elem)

        def build_sprite(self):
            width, height = self.size
            if not self.focused:
                center = (77, 77, 78, 255)
            
            else:
                center = (107, 107, 108, 255)

            img = Image.new("RGBA", (int(width), int(height)))
            img_drawer = ImageDraw.Draw(img, "RGBA")
            img_drawer.rectangle((2, 2, width - 2, height - 2), fill=center)
            del img_drawer

            return img
    
        def draw(self, editor, pos):
            super().draw(editor, pos)
            self.text.draw(editor, pos)

        def handle_input(self, keycodes, mouse_buttons, input_handler):
            if input_handler.get_mouse_button_up(mouse_buttons.LEFT):
                open_popup(self.rect.bottomleft).set_children(self.elems).register()

    def __init__(self, parent, **kwrds):
        super().__init__(parent, 100, 20, **kwrds)

        self.menus: dict[str, __class__.MenuButton] = {}
        self.input = modules.input_handler()

    def clear_menus(self):
        self.menus = {}

    def add_menu(self, menu_name: str):
        self.menus[menu_name] = __class__.MenuButton(menu_name)

    def add_to_menu(self, menu_name: str, elem: UiElement):
        if not issubclass(type(elem), UiElement):
            modules.logger("EDITOR").log_warning(f"Cannot add {type(elem).__name__} to a menu, as it's not a valid UI Element!")
            return 
        
        self.menus[menu_name].add_elem(elem)

    def build_sprite(self):
        fill = (77, 77, 78, 255)
        edge = (107, 107, 107, 255)
        img = Image.new("RGBA", (int(self.size.x), 20), fill)
        draw = ImageDraw.Draw(img, "RGBA")
        draw.line((0, 1, int(self.size.x), 1), edge, 1)
        return img

    def draw(self, editor, pos):
        if self.size[0] != editor.size()[0]:
            self.resize(glm.vec2(editor.size()[0], 20))
        super().draw(editor, pos)

        for menu in self.menus.values():
            menu.draw(editor, pos)
            pos.x += menu.size.x + 5

    def handle_input(self, keycodes, mouse_buttons, input_handler):
        for elem in self.menus.values():
            if elem.rect.collide_point(glm.vec2(input_handler.mouse_pos)):
                elem.handle_input(keycodes, mouse_buttons, input_handler)

class ListView(UiElement):
    can_claim_focus = True
    class ListElement(UiElement):
        def __init__(self, parent: ListView, value: str, idx: int, **kwargs):
            self.selected = False
            width = parent.size.x - parent.padding.x * 2
            height = 20

            super().__init__(parent, width, height, **kwargs)
            self.__val = ListValue(value, idx)
            self.__label = TextElement(None, self.__val.val, width, height)
            self.was_focused = False
        
        def draw(self, editor, pos):
            if self.rect.pos != pos:
                self.rect.move_to(glm.vec2(*pos))

            if self.focused != self.was_focused:
                self.sprite = self.build_sprite()
                self.rebuild_texture()
                self.was_focused = self.focused

            super().draw(editor, pos)
            self.__label.draw(editor, pos)

        def build_sprite(self):
            if self.focused or self.selected:
                col = (69, 73, 78)
            else:
                col = (58, 61, 65)

            img = Image.new("RGBA", (int(self.rect.size.x), int(self.rect.size.y)), (0, 0, 0, 0))
            ImageDraw.Draw(img, "RGBA").rounded_rectangle(
                (0, 0, int(self.rect.size.x), int(self.rect.size.y)), radius=7, outline=col, width=2)
            
            return img

        @property
        def value(self):
            return self.__val
        
        def resize(self, size):
            super().resize(size)
            self.__label.resize(size)

        def handle_input(self, keycodes, mouse_buttons, input_handler):
            self.selected = input_handler.get_mouse_button_up(mouse_buttons.LEFT)
            return self.selected

    def __init__(self, parent, width, height, values: list[str] = [], **kwargs):
        super().__init__(parent, width, height, **kwargs)
        self.padding = glm.vec2(5, 5)

        self.__values = values
        self.ui_elements: list[__class__.ListElement] = []
        self.rebuild_elements()

        self.select_item_callback = None

        self.focused_elem: __class__.ListElement = None
        self.selected_elem: __class__.ListElement = None

        self.was_focused = False
    
    def resize(self, size):
        super().resize(size)
        for elem in self.ui_elements:
            elem.resize(glm.vec2(self.size.x - self.padding.x * 2, elem.size.y))

    def extend_values(self, new_vals: list[str]):
        self.__values.extend(new_vals)

    def set_values(self, vals: list[str]):
        self.__values = vals

    def rebuild_elements(self):
        self.focused_elem = None
        self.ui_elements.clear()
        for idx, elem in enumerate(self.__values):
            self.ListElement(self, elem, idx)

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
        return super().focus()
    
    def draw(self, editor, pos):
        if self.focused != self.was_focused:
            self.sprite = self.build_sprite()
            self.rebuild_texture()
            self.was_focused = self.focused

        gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_REPLACE)
        gl.glStencilFunc(gl.GL_ALWAYS, 2, 0xFF)

        super().draw(editor, pos)

        gl.glStencilFunc(gl.GL_EQUAL, 2, 0xFF)
        gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_KEEP)

        pos_ = pos + self.padding
        for elem in self.ui_elements:
            elem.draw(editor, pos_)
            pos_.y += elem.get_height()

        gl.glDisable(gl.GL_STENCIL_TEST)
        # super().draw(editor, pos)

    def lose_focus(self):
        if self.focused_elem:
            self.focused_elem.lose_focus()
            self.focused_elem = None

        return super().lose_focus()

    def handle_input(self, keycodes, mouse_buttons, input_handler):
        if self.focused_elem:
            if not self.focused_elem.rect.collide_point(glm.vec2(*input_handler.mouse_pos)):
                self.focused_elem.lose_focus()
                self.focused_elem = None
                return

            if self.focused_elem.handle_input(keycodes, mouse_buttons, input_handler):
                if self.selected_elem:
                    self.selected_elem.selected = False
                self.selected_elem = self.focused_elem
                if self.select_item_callback:
                    self.select_item_callback(self.selected_elem.value)
            return

        for elem in self.ui_elements:
            if elem.rect.collide_point(glm.vec2(input_handler.mouse_pos)):
                self.focused_elem = elem
                elem.focus()

    def get_selected(self):
        if self.focused_elem and self.focused_elem.selected:
            return self.focused_elem.value

        return None

@dataclass
class ListValue:
    val: Any
    index: int

class LabeledCheckbox(UiElement):
    can_claim_focus = True

    def __init__(self, parent, width, height, label: str, state: bool = False, **kwrds):
        super().__init__(parent, width, height)

        self.label = TextElement(None, label.replace("_", " ").title(), width, height).set_anchor("lm", TextRenderAnchor.middle_left)
        self.label.old = True
        self.checkbox = Checkbox(None, state)

    @property
    def command(self):
        return self.checkbox.command
    @command.setter
    def command(self, val):
        self.checkbox.command = val

    def resize(self, size):
        super().resize(size)

        self.label.resize(size)

    def draw(self, editor, pos):
        if self.rect.pos != pos:
            self.rect.move_to(glm.vec2(*pos))
            
        self.label.draw(editor, pos)
        self.checkbox.draw(editor, glm.vec2(self.label.rect.right - self.checkbox.size.x, self.label.rect.top))    
        
    def handle_input(self, keycodes, mouse_buttons, input_handler):
        if self.checkbox.rect.collide_point(glm.vec2(input_handler.mouse_pos)):
            self.checkbox.handle_input(keycodes, mouse_buttons, input_handler)
            self.checkbox.focus()

        else:
            self.checkbox.lose_focus()

class LabeledInput(UiElement):
    can_claim_focus = True
    
    def __init__(self, parent, width, height, label: str, starting: str = "", type_: type = str, **kwrds):
        super().__init__(parent, width, height)

        self.focused_elem: InputField = None
        self.ui_elements = []

        self.label = TextElement(None, label.replace("_", " ").title()[:20], get_size(label.replace("_", " ").title()[:20], TextStyle.NORMAL).x, height).set_anchor("lm", TextRenderAnchor.middle_left)
        self.label.old = True
        self.input_field = InputField(self, width - self.label.size.x - 10, height, hint=label, starting_message=starting, type_=type_)
        if type_ == float:
            self.input_field.default_val = 0.0
        if type_ == int:
            self.input_field.default_val = 0

        del self.ui_elements

    @property
    def command(self):
        return self.input_field.command
    @command.setter
    def command(self, val):
        self.input_field.command = val

    @property
    def validate_command(self):
        return self.input_field.validate_command
    @validate_command.setter
    def validate_command(self, val):
        self.input_field.validate_command = val

    def resize(self, size):
        super().resize(size)

        self.input_field.resize(size - glm.vec2(self.label.size.x + 10, 0))

    def draw(self, editor, pos):
        if self.rect.pos != pos:
            self.rect.move_to(glm.vec2(*pos))
            
        self.label.draw(editor, pos)
        self.input_field.draw(editor, pos + glm.vec2(self.size.x - self.input_field.size.x, 0))

        if self.focused == False and self.input_field.focused:
            self.input_field.lose_focus()
            self.focused_elem = None
        
    def handle_input(self, keycodes, mouse_buttons, input_handler):
        if self.input_field.rect.collide_point(glm.vec2(input_handler.mouse_pos)) and not self.focused_elem:
            self.focused_elem = self.input_field

        if self.focused_elem:
            self.hold_focus = self.input_field.hold_focus
            self.input_field.handle_input(keycodes, mouse_buttons, input_handler)
            self.input_field.focus()

class DropdownButton(UiElement):
    can_claim_focus = True

    def __init__(self, parent, width, base_height, text, **kwrds):
        super().__init__(parent, width, base_height, **kwrds)

        self.elems: list[UiElement] = []
        self.open = False

        self.__base_height = base_height

        self.label = TextButton(None, width - base_height, base_height, text, kwrds.pop("button_click_func", None))
        self.dropdown = SimpleDropdown(None, base_height, base_height)
        def set_state(state):
            print(state)
            self.open = state

        self.dropdown.open_callback = set_state

        self.focused_elem = None
        
        self.auto_populate = False
        self.auto_populate_func = None

        self.y_padding = 5

    def resize(self, size):
        super().resize(size)

        size.x -= size.y
        self.label.resize(size)
        self.dropdown.resize(glm.vec2(size.y))

    def draw(self, editor, pos):
        if self.rect.pos != pos:
            self.rect.move_to(glm.vec2(*pos))

        if not self.open and self.elems != [] and self.auto_populate:
            self.focused_elem = None
            self.elems.clear()
             
        self.label.draw(editor, pos)
        self.dropdown.draw(editor, pos + glm.vec2(self.label.size.x, 0))

        if self.open:
            self.size.y = self.__base_height
            if self.auto_populate and self.elems == []:
                self.elems = self.auto_populate_func(self.label.edge_offset[0] + 10)

            pos.y += self.__base_height + self.y_padding

            for idx, elem in enumerate(self.elems):
                elem.draw(editor, pos)

                pos.y += elem.get_height()
                self.size.y += self.y_padding + elem.get_height()

    def lose_focus(self):
        super().lose_focus()

        if self.focused_elem:
            self.focused_elem.lose_focus()
            self.focused_elem = None

    def handle_input(self, keycodes, mouse_buttons, input_handler):
        mouse_pos = glm.vec2(input_handler.get_cursor_pos())

        if self.label.rect.collide_point(mouse_pos):
            if self.focused_elem and self.focused_elem != self.label:
                self.focused_elem.lose_focus()

            self.focused_elem = self.label
            self.focused_elem.focus()

        elif self.dropdown.rect.collide_point(mouse_pos):
            if self.focused_elem and self.focused_elem != self.dropdown:
                self.focused_elem.lose_focus()

            self.focused_elem = self.dropdown
            self.focused_elem.focus()

        else:
            for elem in self.elems:
                if elem.rect.collide_point(mouse_pos):
                    if self.focused_elem and self.focused_elem != elem:
                        self.focused_elem.lose_focus()

                    self.focused_elem = elem
                    self.focused_elem.focus()

        if self.focused_elem:
            self.focused_elem.handle_input(keycodes, mouse_buttons, input_handler)


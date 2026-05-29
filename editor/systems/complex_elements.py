from __future__ import annotations

from .window_drawer import *
from .simple_elements import *

class MenuBar(UiElement):
    can_claim_focus = True
    class MenuButton(UiElement):
        can_claim_focus = True
        def __init__(self, menu_name: str, **kwrds):
            width = get_size(menu_name, TextStyle.NORMAL, 12).x
            super().__init__(None, width + 15, 20, **kwrds)

            self.text = TextElement(None, menu_name, width + 15, 20)
            self.text.set_text_size(12).set_anchor("mm", TextRenderAnchor.middle_middle)

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

    def __init__(self, parent, **kwrds):
        super().__init__(parent, 100, 20, **kwrds)

        self.menus: dict[str, __class__.MenuButton] = {}
        self.input = modules.input_handler()

    def clear_menus(self):
        self.menus = {}

    def add_menu(self, menu_name: str):
        self.menus[menu_name] = __class__.MenuButton(menu_name)

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
        
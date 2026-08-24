from __future__ import annotations

from typing import Any

from .window_drawer import UiElement, EditorUiWindow, DragData
from .font import TextStyle, AnchorPoints, render_text, get_size
from . import global_vars as modules

from PIL import Image, ImageDraw

import pyglm.glm as glm
import glfw

from enum import Enum
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

class TextElement(UiElement):
    def __init__(self, parent, text: str, width: float, height: float, **kwargs):
        # The amount the text is offset from the edge of it's bounding box.
        # Left, Top, Right, Bottom
        self.edge_offset = [0, 0, 0, 0]
        self.message = text

        self.style = TextStyle.NORMAL
        self.anchor: AnchorPoints = "mm"
        self.text_draw_anchor: TextRenderAnchor = TextRenderAnchor.middle_middle

        self.use_wrapping = True
        self.color = (255, 255, 255)

        self.text_size = None
        super().__init__(parent, width, height, **kwargs)

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
                              int(offset.x), int(offset.y), self.style, self.anchor, self.text_size, color=self.color, enable_wrapping=self.use_wrapping)

    def draw(self, editor, pos):
        if self.old:
            self.sprite = self.build_sprite()
            self.rebuild_texture()

            self.old = False

        return super().draw(editor, pos)

    def resize(self, size):
        super().resize(size)

        self.sprite = self.build_sprite()
        self.rebuild_texture()
    
class Button(UiElement):
    can_claim_focus = True
    def __init__(self, parent, width: float, height: float, text: str, click_callback: function, **kwargs):
        super().__init__(parent, width, height, **kwargs)

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

        self.sprite = self.build_sprite()
        self.rebuild_texture()

        self.label.resize(size)

class TextButton(UiElement):
    can_claim_focus = True

    def __init__(self, parent, width, height, text, click_callback, **kwrds):
        self.edge_offset = [0, 0]
        self.text = text

        self.click_callback = click_callback

        self.color = (220, 220, 220)
        self.focused_color = (255, 255, 255)

        self.style = TextStyle.NORMAL
        self.anchor: AnchorPoints = "lm"
        self.text_draw_anchor: TextRenderAnchor = TextRenderAnchor.middle_left

        self.use_wrapping = True

        self.text_size = None
        super().__init__(parent, width, height, **kwrds)

        self.was_focused = self.focused

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
        offset.x += self.edge_offset[0]
        offset.y += self.edge_offset[1]

        color = self.color
        if self.focused:
            color = self.focused_color

        return render_text(self.text, int(self.size.x), int(self.size.y), 
                                int(offset.x), int(offset.y), self.style, self.anchor, self.text_size, color=color, enable_wrapping=self.use_wrapping)

    def draw(self, editor, pos):
        if self.old or self.was_focused != self.focused:
            self.sprite = self.build_sprite()
            self.rebuild_texture()

            self.old = False

            self.was_focused = self.focused

        return super().draw(editor, pos)

    def handle_input(self, keycodes, mouse_buttons, input_handler):
        if input_handler.get_mouse_button_up(mouse_buttons.LEFT):
            if self.click_callback:
                self.click_callback()

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
        
    @staticmethod
    def validate_int(message: str):
        message_ = message
        if message == "-":
            message_ = "-1"
        try:
            int(message_)
            return True
        except ValueError:
            return False
 
    def __init__(self, parent: EditorUiWindow | HorizontalLayout, width: float, height: float, hint: str = "", starting_message: str = "", type_: Any = str, **kwargs):
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
        super().__init__(parent, width, height, **kwargs)

        self.hint = hint
        self.message = starting_message
        self.selection_idx = 0

        self.label = TextElement(None, hint if self.message == "" else self.message, width, height, build_sprite=False, build_texture=False)
        self.label.use_wrapping = False

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

        self.sprite = self.build_sprite()
        self.rebuild_texture()

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

        if self.message == "":
            self.message = str(self.default_val)

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
            if self.command:
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

    max_size = glm.vec2(20, 20)
    def __init__(self, parent, state: bool = False, **kwargs):
        self.state = state
        self.command = None

        super().__init__(parent, 20, 20, **kwargs)

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
            if self.command:
                self.command(self)

            self.sprite = self.build_sprite()
            self.rebuild_texture()

    def draw(self, editor, pos):
        if self.rect.pos != pos:
            self.rect.move_to(glm.vec2(*pos))

        super().draw(editor, pos)

    def get_value(self):
        return self.state

class DropField(UiElement):
    can_claim_focus = True
 
    def __init__(self, parent: EditorUiWindow | HorizontalLayout, width: float, height: float, hint: str = "", starting_data: DragData = None, type_: Any = type[Any], **kwargs):
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
        super().__init__(parent, width, height, **kwargs)

        self.hint = hint
        self.data = starting_data
        self.selection_idx = 0

        self.label = TextElement(None, hint if not self.data else self.data.display_str, width, height, build_sprite=False, build_texture=False)
        self.label.use_wrapping = False

        self.label.edge_offset = [5, 5, 5, 5]
        self.label.set_anchor("lm", TextRenderAnchor.middle_left)
        self.old = True

        if self.data is None:
            self.label.italicize()
        self.label.resize(glm.vec2(width, height))
        self.was_focused_last = self.focused

        self.type_ = type_
        self.drop_callback = None
        self.filter_ = None

    def drop_drag_data(self, drag_data):
        if self.filter_ and not self.filter_(drag_data):
            return 
        
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

        self.sprite = self.build_sprite()
        self.rebuild_texture()

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

    def __init__(self, parent, width, height, elems: list[UiElement] = [], **kwargs):
        super().__init__(parent, width, height, **kwargs)
        self.padding = glm.vec2(10, 10)

        self.elems = elems
        height_ = height - self.padding.y * 2

        for elem in elems:
            width_ = ((width - self.padding.x * 2) - (self.padding.x * (len(elems) - 1))) / len(elems) 
            elem.resize(glm.vec2(width_, height_))
            elem.parent = self

        self.focused_elem = None

        self.sprite = self.build_sprite()
        self.rebuild_texture()

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

    def rebuild_elems(self):
        size = self.size - self.padding * 2
        for elem in self.elems:
            width_ = ((size.x) - (self.padding.x * (len(self.elems) - 1))) / len(self.elems) 
            height_ = size.y
            elem.resize(glm.vec2(width_, height_))

    def resize(self, size):
        width = size.x
        for elem in self.elems:
            width_ = ((width - self.padding.x * 2) - (self.padding.x * (len(self.elems) - 1))) / len(self.elems) 
            height_ = size.y - self.padding.y * 2
            elem.resize(glm.vec2(width_, height_))

        super().resize(size)

        self.sprite = self.build_sprite()
        self.rebuild_texture()

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
    def __init__(self, parent: EditorUiWindow, **kwargs):
        default_width = 0
        if parent:
            default_width = parent.get_draw_data().size.x - parent.get_draw_data().padding.x * 2

        width = kwargs.pop('width', default_width)
        height = kwargs.pop('height', 10)

        super().__init__(parent, width, height, **kwargs)

    def build_sprite(self):
        img = Image.new("RGBA", (int(self.rect.size.x), int(self.rect.size.y)), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img, "RGBA")
        draw.line((0, self.size.y/2 - 1, int(self.size.x), self.size.y/2 - 1), (66, 69, 71), width=2)
        draw.line((0, self.size.y/2 + 1, int(self.size.x), self.size.y/2 + 1), (59, 63, 68), width=2)
        return img

class Tab(UiElement):
    def __init__(self, parent, width, height, text: str, **kwargs):
        self.selected = False
        super().__init__(parent, width, height, **kwargs)
        self.label = TextElement(None, text, width, height)
        self.label.set_text_size(12)
        self.label.set_anchor("mm", TextRenderAnchor.middle_middle)

        self.was_selected = False

    def build_sprite(self):
        col = (80, 80, 80, 255)
        fill_col = (57, 57, 58)
        if self.selected:
            col = (80, 80, 150, 255)
            fill_col = (57, 57, 88)
        
        img = Image.new("RGBA", (int(self.size.x), int(self.size.y)), (0, 0, 0, 0))
        drawer = ImageDraw.Draw(img, "RGBA")
        drawer.rounded_rectangle(((0, -10), (img.width, img.height)), 10, fill=fill_col, outline=col, width = 2, corners=(False, False, True, True))
        del drawer

        return img
    
    def draw(self, editor, pos):
        if self.was_selected != self.selected:
            self.was_selected = self.selected

            self.sprite = self.build_sprite()
            self.rebuild_texture()

        super().draw(editor, pos)
        self.label.draw(editor, pos)

    def set_selected(self, state: bool):
        self.selected = state

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

class SimpleDropdown(UiElement):
    can_claim_focus = True

    def __init__(self, parent, width, height, color=(200, 200, 200), selected_color=(255, 255, 255), **kwrds):
        self.open = False
        self.color = color
        self.selected_col = selected_color

        self.open_callback = None

        super().__init__(parent, width, height, **kwrds)

    def build_sprite(self):
        img = Image.new("RGBA", (int(self.size.x), int(self.size.y)), (0, 0, 0, 0))
        drawer = ImageDraw.Draw(img, "RGBA")

        x1 = int(self.size.x * .25)
        x2 = int(self.size.x * .5)
        x3 = int(self.size.x * .75)

        y1 = int(self.size.y * .33)
        y2 = int(self.size.y * .66)

        if self.open == False:
            drawer.line((x1, y1, x2, y2, x3, y1), self.color if not self.focused else self.selected_col, width=1)
        else:
            drawer.line((x1, y2, x2, y1, x3, y2), self.color if not self.focused else self.selected_col, width=1)

        return img

    def focus(self):
        self.old = True
        return super().focus()

    def lose_focus(self):
        self.old = True
        return super().lose_focus()
    
    def draw(self, editor, pos):
        if self.rect.pos != pos:
            self.rect.move_to(glm.vec2(*pos))

        super().draw(editor, pos)

    def handle_input(self, keycodes, mouse_buttons, input_handler):
        if input_handler.get_mouse_button_down(mouse_buttons.LEFT):
            self.open = not self.open
            self.old = True

            if self.open_callback:
                self.open_callback(self.open)
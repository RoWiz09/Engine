from PIL import Image, ImageFont, ImageDraw, ImageTransform
from typing import Literal, TypeAlias

from enum import Enum

from . import get_modules

FONT = ImageFont.truetype("arial.ttf", 12)
BOLD_FONT = ImageFont.truetype("arialbd.ttf", 12)
ITAL_FONT = ImageFont.truetype("ariali.ttf", 12)

AnchorPoints: TypeAlias = Literal["lt", "lm", "lb", "mt", "mm", "mb", "rt", "rm", "rb"]

class TextStyle(Enum):
    NORMAL = FONT
    BOLD = BOLD_FONT
    ITALICS = ITAL_FONT

def render_window_label(text: str, window_width: int):
    global FONT
    
    img = Image.new("RGBA", (window_width, 30), (0, 0, 0, 0))
    drawer = ImageDraw.Draw(img, "RGBA")

    drawer.text((0, 0), text, font = FONT)
    img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    return img

def render_text(text: str, width: int, height: int, x_off: int, y_off: int, style: TextStyle, anchor_point: AnchorPoints = "mm"):    
    img = Image.new("RGBA", (int(width), int(height)), (0, 0, 0, 0))
    drawer = ImageDraw.Draw(img, "RGBA")

    drawer.text((x_off, y_off), text, font=style.value, anchor=anchor_point)

    img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return img

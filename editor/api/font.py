from PIL import Image, ImageFont, ImageDraw, ImageText
from typing import Literal, TypeAlias

from core import global_vars as modules

from enum import Enum
from pyglm import glm

FONT = ImageFont.truetype("arial.ttf", 12)
BOLD_FONT = ImageFont.truetype("arialbd.ttf", 12)
ITAL_FONT = ImageFont.truetype("ariali.ttf", 12)

AnchorPoints: TypeAlias = Literal["lt", "lm", "lb", "mt", "mm", "mb", "rt", "rm", "rb"]

class TextStyle(Enum):
    NORMAL = FONT
    BOLD = BOLD_FONT
    ITALICS = ITAL_FONT

class TextAttributes(Enum):
    STANDARD = 0
    WRAPPING = 1
    TRUNCATED = 2

def truncate_text_to_width(text: str, max_width, style: TextStyle, size: int = None, suffix: str="..."):
    font = style.value
    if size:
        font = style.value.font_variant(size=size)

    if font.getlength(text) <= max_width:
        return text
    
    suffix_width = font.getlength(suffix)
    target_width = max_width - suffix_width
    
    truncated = text
    while len(truncated) > 0 and font.getlength(truncated) > target_width:
        truncated = truncated[:-1]
        
    return truncated.rstrip() + suffix

def render_window_label(text: str, window_width: int):
    """
        NOTICE: THIS METHOD CURRENTLY DOESN'T IMPLEMENT TEXT WRAPPING!
    """
    global FONT
    
    img = Image.new("RGBA", (window_width, 22), (0, 0, 0, 0))
    drawer = ImageDraw.Draw(img, "RGBA")

    drawer.text((0, 5), text, font = FONT)
    img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    return img

def render_text(text: str, width: int, height: int, x_off: int, y_off: int, style: TextStyle, anchor_point: AnchorPoints = "mm", size: int = None, color: tuple[int, int, int] = (0, 0, 0), enables: TextAttributes = TextAttributes.STANDARD):    
    img = Image.new("RGBA", (int(width), int(height)), (0, 0, 0, 0))
    drawer = ImageDraw.Draw(img, "RGBA")

    if size:
        font = style.value.font_variant(size=size)
    else:
        font = style.value

    text_ = ImageText.Text(text.replace("_", " "), font, "RGBA")
    match enables:
        case TextAttributes.WRAPPING:
            text_.wrap(width)
        case TextAttributes.TRUNCATED:
            text_.text = truncate_text_to_width(text, width, style, size)

    drawer.text((x_off, y_off), text_, font=font, anchor=anchor_point, fill=tuple(color))

    img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return img

def get_size(text: str, style: TextStyle, text_size: int = None):
    if text_size:
        font = style.value.font_variant(size=text_size)
    else:
        font = style.value

    bbox = font.getbbox(text)
    return glm.vec2(bbox[2:])

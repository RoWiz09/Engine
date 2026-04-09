from PIL import Image, ImageFont, ImageDraw, ImageTransform
from io import BytesIO

from . import get_modules

try:
    FONT = ImageFont.truetype("arial.ttf", size=12)
except OSError:
    get_modules.Logger("EDITOR").log_warning("Font file not found, using default.")
    FONT = ImageFont.load_default()

def render_window_label(text: str, window_width: int):
    global FONT
    
    img = Image.new("RGBA", (window_width, 30), (0, 0, 0, 0))
    drawer = ImageDraw.Draw(img, "RGBA")

    drawer.text((0, 0), text, font = FONT)
    img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    return img

def render_text(text: str, width: int, height: int):
    global FONT
    
    img = Image.new("RGBA", (int(width), int(height)), (0, 0, 0, 0))
    drawer = ImageDraw.Draw(img, "RGBA")

    drawer.text((width/2, height/2), text, font=FONT, anchor="mm")

    img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return img

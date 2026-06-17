# Import everything for compilation
from .core.scene_manager import *
from .core.logger import *
from .core.packer import *
from .core.input import *
from .core.settings import *
from .core.window import *

from .datatypes.engine_data_type import *
from .datatypes.model_type import *

from .rendering.shader_program import *
from .rendering.camera_type import *
from .rendering.light_type import *
from .rendering.material import *

from .scripting.collider_type import *
from .scripting.behavior import *

from .error_codes import *
from .decorators import *
from .object import *
from .math import *

def init():
    from .core.logger import setup
    setup()

def init_window(window_width = 800, window_height = 600, window_name = "Test"):
    from .core.window import Window
    return Window(window_width, window_height, window_name)
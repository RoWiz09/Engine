from __future__ import annotations

from ..core.logger import Logger

from ..scripting.behavior import Behavior
from enum import Enum 

class LightTypes(Enum):
    POINT = 0
    SPOT = 1

class LightType:
    light_type = LightTypes.POINT

    lights: dict[LightTypes, list[LightType]] = {light_type_: [] for light_type_ in LightTypes}

    def __init_subclass__(cls):
        if not issubclass(cls, Behavior):
            Logger("RENDER TYPES").log_error("Tried to make a subclass of LightType, when not subclassing Behavior!")

    def __init__(self, gameobject):
        try:
            super().__init__(gameobject)
        except:
            super().__init__()
        LightType.lights[self.light_type].append(self)

        assert isinstance(self, Behavior)
        self.on_destroy += self.on_destroy_callback

    @staticmethod
    def on_destroy_callback(self: LightType):
        LightType.lights[self.light_type].remove(self)
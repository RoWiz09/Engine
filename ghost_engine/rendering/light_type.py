from __future__ import annotations

from typing import final
from enum import Enum

class LightTypes(Enum):
    POINT = 0
    SPOT = 1

class LightType:
    light_type = LightTypes.POINT

    lights: dict[LightTypes, list[LightType]] = {light_type_: [] for light_type_ in LightTypes}

    def __init__(self, gameobject):
        try:
            super().__init__(gameobject)
        except:
            super().__init__()
        LightType.lights[self.light_type].append(self)

    @final
    def unload(self):
        for light_type in LightType.lights.keys():
            LightType.lights[light_type] = []
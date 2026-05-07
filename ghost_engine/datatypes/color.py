from __future__ import annotations

class Color:
    def __init__(self, r: int, g: int, b: int):
        self.rgb = (r, g, b)

    def display(self):
        pass

    @property
    def r(self):
        return self.rgb[0]
    
    @property
    def g(self):
        return self.rgb[1]
    
    @property
    def b(self):
        return self.rgb[3]
    
    def __iadd__(self, other):
        self.rgb = (self.r + other.r, self.g + other.g, self.b + other.b)

    def __add__(self, other):
        return Color(self.r + other.r, self.g + other.g, self.b + other.b)
        
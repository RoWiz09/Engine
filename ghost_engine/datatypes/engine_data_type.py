from typing import Any
from enum import Enum

class DisplayMethods(Enum):
    # STANDARD DATA TYPES [0, 100)
    STRING_INPUT = 0
    FLOAT_INPUT = 1
    INT_INPUT = 2

    # GLM DATA TYPES [100-200)
    VEC2_INPUT = 100
    VEC3_INPUT = 101

    # OTHER [200-INF)
    DROP_FIELD = 200
    TYPEABLE_DROP_FIELD = 201
    COLOR = 202

class DataType:
    """
    A class which all engine data types should inherit from. It includes the methods:
    - display(self): Used by the editor to display the type when used in an EditorField
    """

    def __init__(self):
        pass

    def display(self) -> tuple[DisplayMethods, Any]:
        """
            Controls how a type should be displayed in the editor.
            Should return a tuple, holding the DisplayMethod and the data to display.
        """
        pass

    def filter_input(self, value) -> bool:
        """
            Filters what can be put into the field. Return True to allow input, False to deny.
        """

    def set_value(self, value):
        return self.filter_input(value)

    def get_value(self):
        pass

    @classmethod
    def empty(cls):
        return cls()
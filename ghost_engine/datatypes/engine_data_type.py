from abc import ABC, abstractmethod
from typing import Any
from enum import IntEnum

class DisplayMethods(IntEnum):
    # STANDARD DATA TYPES [0, 100)
    STRING_INPUT = 0
    FLOAT_INPUT = 1
    INT_INPUT = 2

    # GLM DATA TYPES [100-200)
    VEC2_INPUT = 100
    VEC3_INPUT = 101

    # OTHER [200-INF)
    DROP_FIELD = 200
    COLOR = 201

class DataType(ABC):
    """
    A class which all engine data types should inherit from. It includes the methods:
    - display(self): Used by the editor to display the type when used in an EditorField
    """

    def __init__(self):
        pass

    @abstractmethod
    def display(self) -> tuple[DisplayMethods, Any]:
        """
            Controls how a type should be displayed in the editor.
            Should return a tuple, holding the DisplayMethod and the data to display.
        """
        ...

    @abstractmethod
    def filter_input(self, value) -> bool:
        """
            Filters what can be put into the field. Return True to allow input, False to deny.
        """
        ...

    @abstractmethod
    def get_value(self): ...

    def set_value(self, value):
        """
            Filters out the input - subclasses are required to handle setting the value from there.
        """
        return self.filter_input(value)

    @classmethod
    def empty(cls):
        return cls()
from .engine_data_type import DataType, DisplayMethods
from pathlib import Path

PARSABLE_MODEL_TYPES = [
    ".obj"
]

class Model(DataType):
    def __init__(self, default: str = ""):
        super().__init__()
        self.path = default if Path(default).suffix.lower() in PARSABLE_MODEL_TYPES else ""

    def display(self):
        return DisplayMethods.DROP_FIELD, str(self.path)

    def filter_input(self, input):
        if not isinstance(input, str):
            return False
        
        path = Path(input)
        if path.suffix.lower() in PARSABLE_MODEL_TYPES:
            return True
        
        else:
            return False
        
    def __str__(self):
        return self.path

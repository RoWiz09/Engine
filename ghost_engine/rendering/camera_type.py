from ..core.logger import Logger
from abc import ABC, abstractmethod

class CamType(ABC):
    @abstractmethod
    def get_view_mat(self): ...
    
    @abstractmethod
    def get_projection_mat(self): ...
    
    @abstractmethod
    def get_view_pos(self): ...
        
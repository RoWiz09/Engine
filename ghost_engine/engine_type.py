from abc import ABC, abstractmethod

class EngineType(ABC):
    @abstractmethod
    def destroy(self): ...

    @staticmethod
    @abstractmethod
    def instaniate(other): ...

    @abstractmethod
    def copy(self): ...
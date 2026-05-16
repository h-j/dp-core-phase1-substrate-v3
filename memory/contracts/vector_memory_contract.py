from abc import ABC, abstractmethod


class VectorMemoryContract(ABC):

    @abstractmethod
    def embed(self, content: str):
        pass

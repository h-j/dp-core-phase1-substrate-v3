from abc import ABC, abstractmethod


class GraphMemoryContract(ABC):

    @abstractmethod
    def connect(self):
        pass

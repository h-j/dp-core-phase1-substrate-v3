from abc import ABC, abstractmethod


class RelationalMemoryContract(ABC):

    @abstractmethod
    def save(self, payload):
        pass

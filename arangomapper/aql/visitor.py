from abc import ABC, abstractmethod, abstractproperty


class BindVarVisitor(ABC):
    """
    https://refactoring.guru/design-patterns/visitor
    """

    @abstractproperty
    @abstractmethod
    def data(self) -> dict: ...

    @abstractmethod
    def add(self, value: any) -> str: ...


class BindVarManager(BindVarVisitor):
    def __init__(self):
        self._counter: int = 1
        self._bind_vars: dict = {}

    @property
    def data(self) -> dict:
        return self._bind_vars

    def add(self, value: any) -> str:
        alias: str = f"bindvar_{self._counter}"
        self._bind_vars[alias] = value
        self._counter += 1
        return alias

from typing import Literal

from app.mapper.expressions import FieldDescriptor


class FieldFor:
    """
    Represents a field reference within an AQL query, linked to a specific alias.
    """

    def __init__(self, alias: str, field: FieldDescriptor):
        self.alias: str = alias
        self.field: FieldDescriptor = field

    @property
    def value(self) -> str:
        return f"{self.alias}.{self.field.target}"


class Sort:
    """
    Handles the 'SORT' operator logic for AQL.
    """

    def __init__(self, field: FieldFor, order: Literal["asc", "desc"]):
        self.field: FieldFor = field
        self.order: Literal["asc", "desc"] = order

    def aql(self) -> str:
        return f"{self.field.value} {self.order.upper()}"


class Limit:
    """
    Handles the 'LIMIT' operator logic, supporting both count and offset.
    """

    def __init__(self, count: int, offset: int | None = None):
        self.count: int = count
        self.offset: int | None = offset

    def aql(self) -> str:
        if self.offset is not None:
            return f"LIMIT {self.offset}, {self.count} "
        return f"LIMIT {self.count} "

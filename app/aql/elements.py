from typing import Literal

from app.mapper.expressions import FieldDescriptor


class FieldFor:
    def __init__(self, alias: str, field: FieldDescriptor):
        self.alias: str = alias
        self.field: FieldDescriptor = field

    @property
    def value(self) -> str:
        return f"{self.alias}.{self.field.target}"


class Sort:
    def __init__(self, field: FieldFor, order: Literal["asc", "desc"]):
        self.field: FieldFor = field
        self.order: Literal["asc", "desc"] = order

    def aql(self) -> str:
        return f"{self.field.value} {self.order.upper()}"


class Limit:
    def __init__(self, count: int, offset: int | None = None):
        self.count: int = count
        self.offset: int | None = offset

    def aql(self) -> str:
        if self.offset is not None:
            return f"LIMIT {self.offset}, {self.count} "
        return f"LIMIT {self.count} "

from typing import Literal, TypeAlias

Value: TypeAlias = str | bool | float | int | None
Operator: TypeAlias = Literal["==", "!=", ">", ">=", "<", "<=", "in"]
Connector: TypeAlias = Literal["AND", "OR"]

from types import NoneType
from typing import Union, get_args

from pydantic.fields import FieldInfo

from app.mapper.primitives import Connector, Operator, Value
from app.mapper.types import T


class LogicalConnector:
    def __and__(
        self, value: Matcher | GroupLogicalConnector | RawExpression
    ) -> GroupLogicalConnector:
        return GroupLogicalConnector(self, "AND", value)

    def __or__(
        self, value: Matcher | GroupLogicalConnector | RawExpression
    ) -> GroupLogicalConnector:
        return GroupLogicalConnector(self, "OR", value)


class RawExpression(LogicalConnector): ...


class Matcher(LogicalConnector):
    def __init__(
        self,
        field: FieldDescriptor,
        operator: Operator,
        value: Value,
    ):
        self.field: FieldDescriptor = field
        self.operator: Operator = operator
        self.value: Value = value


class GroupLogicalConnector(LogicalConnector):
    def __init__(
        self,
        left: Matcher | GroupLogicalConnector | RawExpression,
        conector: Connector,
        right: Matcher | GroupLogicalConnector | RawExpression,
    ):
        self.left: Matcher | GroupLogicalConnector | RawExpression = left
        self.connector: Connector = conector
        self.right: Matcher | GroupLogicalConnector | RawExpression = right


class FieldDescriptor:
    """
    https://stackoverflow.com/questions/809574/what-is-a-domain-specific-language-anybody-using-it-and-in-what-way/809700#809700
    """

    def __init__(self, name: str, field: FieldInfo, model: type[T]):
        self.name: str = name
        self.model: type[T] = model
        self.field: FieldInfo = field
        self.target: str = self.field.alias or self.name

    def __eq__(self, value: any) -> Matcher:
        return self._build_expression("==", value)

    def __ne__(self, value: any) -> Matcher:
        return self._build_expression("!=", value)

    def __gt__(self, value: any) -> Matcher:
        return self._build_expression(">", value)

    def __ge__(self, value: any) -> Matcher:
        return self._build_expression(">=", value)

    def __lt__(self, value: any) -> Matcher:
        return self._build_expression("<", value)

    def __le__(self, value: any) -> Matcher:
        return self._build_expression("<=", value)

    def is_in(self, value: list[any]) -> Matcher:
        return self._build_expression("in", value)

    def is_true(self) -> Matcher:
        return self._build_expression("==", True)

    def is_false(self) -> Matcher:
        return self._build_expression("==", False)

    def is_null(self) -> Matcher:
        return self._build_expression("==", None)

    def is_not_null(self) -> Matcher:
        return self._build_expression("!=", None)

    def _build_expression(self, operator: str, value: any | list[any]) -> Matcher:
        from app.aql.elements import FieldFor  # https://peps.python.org/pep-0690/
        from app.aql.operator import Let, Raw

        if isinstance(value, list):
            for val in value:
                self._validate_value(val)
        elif type(value) not in [FieldFor, Let, Raw, NoneType]:
            self._validate_value(value)

        return Matcher(self, operator, value)

    def _validate_value(self, value: any):
        if type(value) not in self.types:
            raise ValueError("Value type not allowed")

    @property
    def types(self) -> list[Value]:
        types = [self.field.annotation]

        if isinstance(self.field.annotation, Union):
            types = get_args(self.field.annotation)

        return types

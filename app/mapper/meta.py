from typing import TYPE_CHECKING, TypeVar, Union, get_args

from pydantic._internal._model_construction import ModelMetaclass
from pydantic.fields import FieldInfo

if TYPE_CHECKING:
    # https://typing.python.org/en/latest/spec/directives.html#type-checking
    from app.mapper.base import CollectionBase


T = TypeVar("T", bound="CollectionBase")


class CollectionMetaClass(ModelMetaclass):
    """
    https://peps.python.org/pep-3115/#invoking-the-metaclass
    pydantic and metaclass: https://github.com/pydantic/pydantic/issues/5124#issuecomment-1448610516
    fix import ModelMetaclass: https://github.com/pydantic/pydantic/issues/6381#issuecomment-1619296261

    note: pydantic._internal._model_construction may be a problem in the future since being import
    private, the route may change in future versions

    The use of metaclass on this occasion is for learning purposes as this gives full control,
    there are more minimalist solutions that can accomplish this:
    1- use a decorator that does the same functionality, on CollectionBase::
       def auto_field_alias(cls):
           ....
       @auto_field_alias
       class CollectionBase(...):
           ....
    2- use __init_subclass__ which has the same functionality, inside CollectionBase
    """

    def __new__(mcs, cls_name, bases, namespace, **kwargs) -> type[T]:
        """Mapping alias for model not instanced"""
        model_cls: type[T] = super().__new__(mcs, cls_name, bases, namespace, **kwargs)

        if not model_cls._collection_name:
            return model_cls

        for field_name, field_data in model_cls.model_fields.items():
            setattr(
                model_cls,
                field_name,
                FieldDescriptor(field_name, field_data),
            )

        return model_cls


class FieldDescriptor:
    """
    https://stackoverflow.com/questions/809574/what-is-a-domain-specific-language-anybody-using-it-and-in-what-way/809700#809700
    """

    def __init__(self, name: str, field: FieldInfo):
        self.name: str = name
        self.field: FieldInfo = field
        self.target: str = self.field.alias or self.name

    def __eq__(self, value: any) -> str:
        return self._build_expression("==", value)

    def __ne__(self, value: any) -> str:
        return self._build_expression("!=", value)

    def __gt__(self, value: any) -> str:
        return self._build_expression(">", value)

    def __ge__(self, value: any) -> str:
        return self._build_expression(">=", value)

    def __lt__(self, value: any) -> str:
        return self._build_expression("<", value)

    def __le__(self, value: any) -> str:
        return self._build_expression("<=", value)

    def __contains__(self, value: any) -> str:
        return self._build_expression("in", value)

    def _build_expression(self, operator: str, value: str) -> str:
        if not self.is_val_type_ok(type(value)):
            raise ValueError("Value type not allowed")

        return f"{self.target} {operator} {value}"

    def is_val_type_ok(self, val_type: any) -> bool:
        return val_type in self.types

    @property
    def types(self) -> list[str | bool | float | int | None]:
        types = [self.field.annotation]

        if isinstance(self.field.annotation, Union):
            types = get_args(self.field.annotation)

        return types

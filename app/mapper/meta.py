from typing import TYPE_CHECKING, TypeVar

from pydantic._internal._model_construction import ModelMetaclass

from app.mapper.expressions import FieldDescriptor

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

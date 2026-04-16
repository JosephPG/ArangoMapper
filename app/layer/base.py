from typing import ClassVar

from pydantic import BaseModel, Field


class CollectionBase(BaseModel):
    _collection_name: ClassVar[str] = ""

    id: str | None = Field(None, alias="_id")
    key: str | None = Field(None, alias="_key")

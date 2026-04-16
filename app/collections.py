from typing import ClassVar

from app.mapper.base import CollectionBase


class Location(CollectionBase):
    _collection_name: ClassVar[str] = "locations"

    name: str


class Device(CollectionBase):
    _collection_name: ClassVar[str] = "devices"

    name: str
    type: str


# class Route(Base):
#     pass


# class Interconnection(Base):
#     pass


# 1. La Estructura de Conexiones
# Aunque haya una sola Celda, ella "alimenta" a dos caminos distintos:

#     Locacion A (Interno):
#         Interconnection 1: Celda A -> Transformador A1
#         Interconnection 2: Celda A -> Transformador A2
#     Locacion B (Interno):
#         Interconnection 3: Celda B -> Transformador B1
#         Interconnection 4: Celda B -> Transformador B2

# 2. Las "Interconexiones" (Los cables de larga distancia)
# Aquí es donde ocurre el emparejamiento que mencionas:

#     Interconnection 1: Transformador A1 -cable1-> Transformador B1
#     Interconnection 2: Transformador A2 -cable2-> Transformador B2


# (Locacion A)Celda-Transformador1 -cable-> Transformador1-|
#                 |-Transformador2 -cable-> Transformador2-Celda(Locacion B)
#
# Donde la conexion logia de dos sitios se llama Route y la conexion fisica de dos dispositvos se llama interconexion
# se va a menajar como equipos Transformador y Celda

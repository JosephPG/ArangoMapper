# ArangoMapper
[Read this in English / Leer en Inglés](./README.md)

**ArangoMapper** es un OGM (Object-Graph Mapper) ligero para **ArangoDB**, construido sobre **Pydantic**. Está diseñado para simplificar el trabajo con documentos y grafos, permitiendo escribir consultas AQL complejas usando sintaxis nativa y fluida de Python.

## Sobre este Proyecto

Este repositorio es un proyecto personal de aprendizaje y experimentación. Nació del deseo de profundizar en las capacidades de la metaprogramación en Python y de resolver el reto de mapear una base de datos multimodelo como ArangoDB.

### Conceptos Aplicados:
*   **Metaprogramación**: Sobrecarga de operadores lógicos para la construcción dinámica de queries.
*   **Patrones de Diseño**: Implementación de capas de Manager, Mapper y AQL Builder para asegurar el desacoplamiento.
*   **Tipado Avanzado**: Uso extensivo de *Generics*, *ClassVar* y *Type Hints* para mejorar el tipado.
*   **Seguridad**: Implementación de un sistema de prevención de inyecciones mediante el manejo interno de *bind variables*.

---

## Características Principales

-️ **Modelado con Pydantic**: Validación de datos, tipado fuerte y serialización automática.
- **Poder de Grafos**: Manejo simplificado de Edges y navegaciones (`OUTBOUND`, `INBOUND`, `ANY`) con soporte de profundidad.
- **Sintaxis Pythónica**: Escribe filtros complejos usando operadores lógicos (`&`, `|`, `==`, `>=`, `!=`) sin concatenar strings.
-️ **Seguridad Nativa**: Prevención de inyección AQL mediante el uso automático de `bind_vars`.
- **AQL Manager**: Constructor de consultas fluido que permite mezclar lógica del ORM con AQL nativo (`Raw`).
- **Transacciones**: Soporte integrado para operaciones atómicas y consistentes.
- **Modo Review**: Inspecciona el AQL generado y sus variables antes de ejecutar la consulta.

---

## Instalación
1- Levantar ArangoDB:
```bash
docker-compose.yaml -f docker-compose.db.yaml up
```

2- (Opcional) En config.py se puede configurar las variables de conexion.

3- Instalar dependencias:
```bash
# Clona el repositorio
git clone https://github.com/JosephPG/ArangoMapper.git
cd ArangoMapper

poetry env use 3.14
poetry install
```

---

## Guía de Uso

### 1. Definición de Modelos
Define colecciones y grafos extendiendo de las clases base del ORM.

```python
from arangomapper.mapper import CollectionBase, CollectionEdge
from typing import ClassVar

class Warehouse(CollectionBase):
    _collection_name: ClassVar[str] = "warehouses"
    name: str
    capacity: int

class Operator(CollectionBase):
    _collection_name: ClassVar[str] = "operators"
    nickname: str
    status: str

class Manages(CollectionEdge[Warehouse, Operator]):
    _collection_name: ClassVar[str] = "manages"
    _graph_name: ClassVar[str] = "logistics_graph"
    shift: str
```

### 2. Escritura y Persistencia (CRUD)
Utilizar `CollectionManager` para gestionar el ciclo de vida de los documentos.

```python
from arangomapper.manager import CollectionManager

cm = CollectionManager(db)

# Inserción simple
wh = Warehouse(name="Lima Central", capacity=1000)
cm.insert(wh)

# Gestión de relaciones (Edges)
op = Operator(nickname="Pedro", status="active")
cm.insert(op)

rel = Manages(vertex_from=wh, vertex_to=op, shift="day")
cm.insert_graph(rel)

# Actualizar: Solo cambia los campos necesarios
warehouse.capacity = 600
cm.update(warehouse)

# Eliminar
cm.delete(rel)
```

### 3. Consultas Avanzadas (AQLManager)
Consulta datos usando lógica de Python que se traduce automáticamente a AQL optimizado.

```python
from arangomapper.aql import AQLManager, For, ForGraph

# Filtros legibles
results = (
    AQLManager(db)
    .add_for(
        For(Warehouse)
        .filter((Warehouse.capacity >= 500) & (Warehouse.name != "Test"))
    )
    .list()
)

# Navegación de grafos (Traversals)
graph_data = (
    AQLManager(db)
    .add_for(ForGraph(wh, "OUTBOUND", Manages))
    .list()
)
```

### 4. Transacciones Atómicas
Asegura la integridad de las operaciones múltiples.

```python
def function_for_transaction(txn: TransactionDatabase) -> any:
    cm = CollectionManager(txn)

    warehouse: Warehouse = Warehouse(name="Perù", capacity=100)
    operator: Operator = Operator(
        nickname="Allen", experience_years=2, status="active"
    )

    cm.insert(warehouse)
    cm.insert(operator)

    manage: Manages = Manages(vertex_from=warehouse, vertex_to=operator, shift="day")

    cm.insert_graph(manage)

    return manage.id

collections = [
    Warehouse._collection_name,
    Operator._collection_name,
    Manages._collection_name,
]

res: str = execute_transaction(
    function_for_transaction, read=collections, write=collections
)
```

---

## Estructura del Proyecto

- `app/mapper/`: Clases base para documentos y relaciones (Pydantic).
- `app/aql/`: Motor de construcción de consultas y traducción AQL.
- `app/database/`: Capa de conexión con el driver oficial de ArangoDB y gestión de persistencia, CRUD y transacciones
- `example/`: Suite detallada de ejemplos listos para ejecutar.
- `tests/`: Pruebas unitarias y de integración.
---

## Ejecución de Ejemplos

Suite interactiva con logs (vía `loguru`). Para ejecutar todos los ejemplos de forma ordenada:

```bash
# Desde la raíz del proyecto
python run_examples.py
```

## Ejecución de Test

1- Si el proyecto fue instalando localmente entonces solo es necesario la ejecucion de `pytest`.

2- Ejecucion de test en containers:

```bash
# Desde la raíz del proyecto
docker-compose -f docker-compose.test.yaml up
```

## Deuda Técnica y Desafíos Pendientes

1- **Query Caching**: Implementar un sistema de hashing para las estructuras de los objetos For y Matcher. El objetivo es evitar la reconstrucción del string AQL y el recorrido recursivo del árbol lógico cuando se ejecutan consultas con la misma estructura pero diferentes parámetros.

2- **async/await**: Refactorizar la capa de app/database y los métodos de ejecución (list, first, count) para soportar el driver asíncrono de ArangoDB

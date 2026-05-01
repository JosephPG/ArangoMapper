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

* **Modelado con Pydantic**: Validación de datos, tipado fuerte y serialización automática.
* **Poder de Grafos**: Manejo simplificado de Edges y navegaciones (`OUTBOUND`, `INBOUND`, `ANY`) con soporte de profundidad.
* **Sintaxis Pythónica**: Escribe filtros complejos usando operadores lógicos (`&`, `|`, `==`, `>=`, `!=`) sin concatenar strings.
* **Seguridad Nativa**: Prevención de inyección AQL mediante el uso automático de `bind_vars`.
* **AQL Manager**: Constructor de consultas fluido que permite mezclar lógica del ORM con AQL nativo (`Raw`).
* **Transacciones**: Soporte integrado para operaciones atómicas y consistentes.
* **Async Support**: Compatibilidad total con `async/await` para aplicaciones de alto rendimiento, lo que permite la ejecución concurrente de consultas a través de `asyncio`.

---

## Instalación

1- Instalar dependencias:
```bash
# Clona el repositorio
git clone https://github.com/JosephPG/ArangoMapper.git
cd ArangoMapper

poetry env use 3.14
poetry install
```

2- Levantar ArangoDB:
```bash
docker-compose.yaml -f docker-compose.db.yaml up
```

3- (Opcional) En config.py se puede configurar las variables de conexion.

---

## Guía de Uso

### 1. **Registro de modelos (Importante)**
Para que el ORM reconozca y migre las colecciones, debe agregar las rutas de los módulos a `MIGRATE_MODELS` en su configuración:
   ```python
   # config.py
   MIGRATE_MODELS: list[str] = [
       "example.models",
       "any.path.models"
   ]
   ```

### 2. Definición de Modelos
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

### 3. Escritura y Persistencia (CRUD)
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

### 4. Consultas Avanzadas (AQLManager)
Consulta datos usando lógica de Python que se traduce automáticamente a AQL optimizado.

```python
from arangomapper.aql import AQLManager, For, ForGraph
from app.aql.schemas import GraphResponse

# Readable filters
results: list[] = (
    AQLManager(db)
    .add_for(
        For(Warehouse).filter((Warehouse.capacity >= 500) & (Warehouse.name != "Test"))
    )
    .list()
)

# Graph navigation (Traversals)
graph_data: list[GraphResponse] = (
    AQLManager(db)
    .add_for(
        ForGraph(wh, "OUTBOUND", Manages).filter(Manages.shift == "day")
	)
    .list()
)
```

### 5. Transacciones Atómicas
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

### 6. Soporte Async
ArangoMapper está preparado para entornos asíncronos. Puedes ejecutar varias consultas simultáneamente usando `asyncio`.

```python
from app.aql.async_aqlmanager import AsyncAQLManager
from app.database.async_manager import AsyncCollectionManager

async def get_data(db):
    cm = AsyncCollectionManager(db)

	wh = Warehouse(name="Async Hub", capacity=500)

	await cm.insert(wh)

    # Concurrent execution
    counts = await asyncio.gather(
        AsyncAQLManager(db).add_for(For(Warehouse)).count(),
        AsyncAQLManager(db).add_for(For(Sensor)).count()
    )
    return counts
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

1- Suite interactiva con registros (a través de `loguru`). Para ejecutar todos los ejemplos en orden:

```bash
# From the root of the project
python run_examples.py
```

2- O utilizando docker-compose:
```bash
# From the root of the project
docker-compose -f docker-compose.runexample.yaml build
docker-compose -f docker-compose.runexample.yaml up

```

## Ejecución de Test

1- Si el proyecto fue instalando localmente entonces solo es necesario la ejecucion de `pytest`.

2- Ejecucion de test en containers:

```bash
# Desde la raíz del proyecto
docker-compose -f docker-compose.test.yaml build
docker-compose -f docker-compose.test.yaml up
```

## Importar como dependecia

1- Con poetry:

```bash
poetry add git+https://github.com/JosephPG/ArangoMapper.git
```

2- Configura config.py en la raiz del proyecto con lo siguiente:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

MIGRATE_MODELS: list[str] = []


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env"), env_file_encoding="utf-8")

    ARANGO_HOST: str = "http://localhost"
    ARANGO_PORT: str = "8529"
    ARANGO_DB: str = "_system"
    ARANGO_USERNAME: str = ""
    ARANGO_PASSWORD: str = ""


settings = Settings()
```

3- Uso:
```python
import arangomapper

arangomapper.AQLmanager
arangomapper.AsyncAQlmanager
arangomapper.For
```

---

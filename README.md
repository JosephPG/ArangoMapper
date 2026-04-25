# ArangoMapper
[Read this in Spanish / Leer en Español](./README.es.md)

**ArangoMapper** It is a lightweight OGM (Object-Graph Mapper) for **ArangoDB**, built on **Pydantic**. It is designed to simplify working with documents and graphs, allowing you to write complex AQL queries using native and fluent Python syntax.

## About this Project

This repository is a personal learning and experimentation project. It arose from a desire to delve deeper into the capabilities of metaprogramming in Python and to solve the challenge of mapping a multi-model database like ArangoDB.

### Applied Concepts:
* **Metaprogramming**: Overloading logical operators for dynamic query construction.
* **Design Patterns**: Implementation of Manager, Mapper, and AQL Builder layers to ensure decoupling.
* **Advanced Typing**: Extensive use of *Generics*, *ClassVar*, and *Type Hints* to improve typing.
* **Security**: Implementation of an injection prevention system through internal handling of *variable binding*.

---

## Main Features

* **Pydantic Modeling**: Data validation, strong typing, and automatic serialization.
* **Graph Power**: Simplified handling of edges and navigation (`OUTBOUND`, `INBOUND`, `ANY`) with depth support.
* **Python Syntax**: Write complex filters using logical operators (`&`, `|`, `==`, `>=`, `!=`) without string concatenation.
* **Native Security**: AQL injection prevention through automatic use of `bind_vars`.
* **AQL Manager**: Fluent query builder that allows mixing ORM logic with native AQL (`Raw`).
* **Transactions**: Built-in support for atomic and consistent operations.
* **Review Mode**: Inspect the generated AQL and its variables before executing the query.

---

## Instalación
1- Levantar ArangoDB:
```bash
docker-compose.yaml -f docker-compose.db.yaml up
```

2- (Optional) In config.py you can configure the connection variables.

3- Install dependencies:
```bash
# Clone the repository
git clone https://github.com/JosephPG/ArangoMapper.git
cd ArangoMapper

poetry env use 3.14
poetry install
```

---

## User Guide

### 1. Defining Models
Define collections and graphs by extending the ORM's base classes.

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

### 2. Writing and Persistence (CRUD)
Use `CollectionManager` to manage the document lifecycle.

```python
from arangomapper.manager import CollectionManager

cm = CollectionManager(db)

# Simple Insertion
wh = Warehouse(name="Lima Central", capacity=1000)
cm.insert(wh)

# Relationship Management (Edges)
op = Operator(nickname="Pedro", status="active")
cm.insert(op)

rel = Manages(vertex_from=wh, vertex_to=op, shift="day")
cm.insert_graph(rel)

# Update: Only change the necessary fields.
warehouse.capacity = 600
cm.update(warehouse)

# Delete
cm.delete(rel)
```

### 3. Advanced Queries (AQLManager)
Query data using Python logic that is automatically translated into optimized AQL.

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

### 4. Atomic Transactions
Ensures the integrity of multiple operations.

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

## Project Structure

- `app/mapper/`: Base classes for documents and relationships (Pydantic).
- `app/aql/`: AQL query engine and translation.
- `app/database/`: Connection layer with the official ArangoDB driver and persistence, CRUD, and transaction management.
- `example/`: Detailed suite of ready-to-run examples.
- `tests/`: Unit and integration tests.
---

## Running Examples

Interactive suite with logs (via `loguru`). To run all examples in order:

```bash
# From the root of the project
python run_examples.py
```

## Test Execution

1- If the project was installed locally, then only the `pytest` command needs to be run.

2- Test execution in containers:

```bash
# From the root of the project
docker-compose -f docker-compose.test.yaml up
```

## Technical Debt and Pending Challenges

1- **Query Caching**: Implement a hashing system for the structures of the For and Matcher objects. The goal is to avoid AQL string reconstruction and recursive traversal of the logical tree when executing queries with the same structure but different parameters.

2- **async/await**: Refactor the app/database layer and the execution methods (list, first, count) to support the ArangoDB asynchronous driver.

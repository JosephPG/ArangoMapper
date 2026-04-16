# ArangoMiniORM

Un Mini-ORM ligero, tipado y "Pythonico" para **ArangoDB** construido sobre **Pydantic V2**. Este proyecto simplifica la interacción con colecciones utilizando modelos de datos y un gestor de base de datos eficiente.

## Características

*   **Modelado con Pydantic:** Validación de datos y serialización automática con soporte para Alias.
*   **Mapeo Inteligente:** Manejo automático de campos nativos de Arango (`_id`, `_key`).
*   **Patrón Singleton:** Conexión única y global para optimizar recursos.
*   **Inyección de Dependencias en Tests:** Fixtures de Pytest que limpian la DB automáticamente tras cada test.
*   **Calidad de Código:** Configurado con **Ruff** para linting y formateo (reemplaza a Black, Isort y Flake8).

## Stack Tecnológico

- **Python 3.14+**
- **Pydantic V2** (Core de datos)
- **python-arango** (Driver oficial)
- **Pytest** (Pruebas unitarias)
- **Ruff** (Linter y Formatter)

## Uso Rápido

### 1. Define tu Modelo
```python
from app.collections import Location
from app.database.conn import get_db
from app.database.manager import CollectionManager

db = get_db()

cm = CollectionManager(db)

location = Location(name="local A")

cm.insert(location)

print(f"id={location.id} key={location.key} name={location.name}")

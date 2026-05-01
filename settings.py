"""
Configuration file where you define the paths of the models to be migrated to ArangoDB
"""

MIGRATE_MODELS: list[str] = ["app.collections", "example.models"]

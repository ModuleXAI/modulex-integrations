"""Azure Storage integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.azure_storage.manifest import manifest
from modulex_integrations.tools.azure_storage.tools import (
    create_container,
    delete_blob,
    list_containers,
    upload_blob,
)

TOOLS = (
    create_container,
    delete_blob,
    list_containers,
    upload_blob,
)

__all__ = [
    "TOOLS",
    "create_container",
    "delete_blob",
    "list_containers",
    "manifest",
    "upload_blob",
]

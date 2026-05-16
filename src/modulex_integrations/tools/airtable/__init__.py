"""Airtable integration."""
from modulex_integrations.tools.airtable.manifest import manifest
from modulex_integrations.tools.airtable.tools import (
    create_records,
    delete_records,
    get_record,
    list_bases,
    list_records,
    list_tables,
    update_records,
)

TOOLS = (
    list_bases,
    list_tables,
    list_records,
    get_record,
    create_records,
    update_records,
    delete_records,
)

__all__ = [
    "TOOLS",
    "create_records",
    "delete_records",
    "get_record",
    "list_bases",
    "list_records",
    "list_tables",
    "manifest",
    "update_records",
]

"""Microsoft SQL Server integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.microsoft_sql_server.manifest import manifest
from modulex_integrations.tools.microsoft_sql_server.tools import (
    execute_query,
    execute_raw_query,
    insert_row,
    list_table_options,
)

TOOLS = (
    execute_raw_query,
    execute_query,
    insert_row,
    list_table_options,
)

__all__ = [
    "TOOLS",
    "execute_query",
    "execute_raw_query",
    "insert_row",
    "list_table_options",
    "manifest",
]

"""Supabase integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.supabase.manifest import manifest
from modulex_integrations.tools.supabase.tools import (
    batch_insert_rows,
    count_rows,
    delete_row,
    insert_row,
    remote_procedure_call,
    select_row,
    update_row,
    upsert_row,
)

TOOLS = (
    select_row,
    insert_row,
    update_row,
    upsert_row,
    delete_row,
    batch_insert_rows,
    remote_procedure_call,
    count_rows,
)

__all__ = [
    "TOOLS",
    "batch_insert_rows",
    "count_rows",
    "delete_row",
    "insert_row",
    "manifest",
    "remote_procedure_call",
    "select_row",
    "update_row",
    "upsert_row",
]

"""Google Sheets integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_sheets.manifest import manifest
from modulex_integrations.tools.google_sheets.tools import (
    add_rows,
    add_worksheet,
    clear_rows,
    delete_rows,
    delete_worksheet,
    find_rows,
    get_spreadsheet_info,
    get_values_in_range,
    list_spreadsheets,
    list_worksheets,
    new_spreadsheet,
    read_rows,
    update_cell,
    update_row,
)

TOOLS = (
    list_spreadsheets,
    new_spreadsheet,
    get_spreadsheet_info,
    list_worksheets,
    add_worksheet,
    delete_worksheet,
    read_rows,
    get_values_in_range,
    find_rows,
    add_rows,
    update_row,
    update_cell,
    clear_rows,
    delete_rows,
)

__all__ = [
    "TOOLS",
    "add_rows",
    "add_worksheet",
    "clear_rows",
    "delete_rows",
    "delete_worksheet",
    "find_rows",
    "get_spreadsheet_info",
    "get_values_in_range",
    "list_spreadsheets",
    "list_worksheets",
    "manifest",
    "new_spreadsheet",
    "read_rows",
    "update_cell",
    "update_row",
]

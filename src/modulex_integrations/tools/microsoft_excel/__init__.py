"""Microsoft Excel integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.microsoft_excel.manifest import manifest
from modulex_integrations.tools.microsoft_excel.tools import (
    add_a_worksheet_tablerow,
    add_row,
    find_row,
    get_columns,
    get_spreadsheet,
    get_table_rows,
    list_folder_id_options,
    update_cell,
    update_worksheet_tablerow,
)

TOOLS = (
    add_a_worksheet_tablerow,
    add_row,
    find_row,
    get_columns,
    get_spreadsheet,
    get_table_rows,
    list_folder_id_options,
    update_cell,
    update_worksheet_tablerow,
)

__all__ = [
    "TOOLS",
    "add_a_worksheet_tablerow",
    "add_row",
    "find_row",
    "get_columns",
    "get_spreadsheet",
    "get_table_rows",
    "list_folder_id_options",
    "manifest",
    "update_cell",
    "update_worksheet_tablerow",
]

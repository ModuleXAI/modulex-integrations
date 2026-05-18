"""Microsoft OneDrive integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.microsoft_onedrive.manifest import manifest
from modulex_integrations.tools.microsoft_onedrive.tools import (
    create_folder,
    create_link,
    download_file,
    find_file_by_name,
    get_excel_table,
    get_file_by_id,
    list_files_in_folder,
    list_my_drives,
    list_shared_folder_reference_options,
    search_files,
    upload_file,
)

TOOLS = (
    create_folder,
    create_link,
    download_file,
    find_file_by_name,
    get_excel_table,
    get_file_by_id,
    list_files_in_folder,
    list_my_drives,
    list_shared_folder_reference_options,
    search_files,
    upload_file,
)

__all__ = [
    "TOOLS",
    "create_folder",
    "create_link",
    "download_file",
    "find_file_by_name",
    "get_excel_table",
    "get_file_by_id",
    "list_files_in_folder",
    "list_my_drives",
    "list_shared_folder_reference_options",
    "manifest",
    "search_files",
    "upload_file",
]

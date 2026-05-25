"""Dropbox integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.dropbox.manifest import manifest
from modulex_integrations.tools.dropbox.tools import (
    create_a_text_file,
    create_folder,
    create_or_append_to_a_text_file,
    create_update_share_link,
    delete_file_folder,
    get_shared_link_metadata,
    list_file_folders_in_a_folder,
    list_file_revisions,
    list_shared_links,
    move_file_folder,
    rename_file_folder,
    search_files_folders,
)

TOOLS = (
    create_folder,
    search_files_folders,
    list_file_folders_in_a_folder,
    delete_file_folder,
    move_file_folder,
    rename_file_folder,
    create_a_text_file,
    create_or_append_to_a_text_file,
    create_update_share_link,
    list_shared_links,
    get_shared_link_metadata,
    list_file_revisions,
)

__all__ = [
    "TOOLS",
    "create_a_text_file",
    "create_folder",
    "create_or_append_to_a_text_file",
    "create_update_share_link",
    "delete_file_folder",
    "get_shared_link_metadata",
    "list_file_folders_in_a_folder",
    "list_file_revisions",
    "list_shared_links",
    "manifest",
    "move_file_folder",
    "rename_file_folder",
    "search_files_folders",
]

"""Google Docs integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_docs.manifest import manifest
from modulex_integrations.tools.google_docs.tools import (
    append_image,
    append_text,
    create_document,
    get_document,
    get_tab_content,
    insert_page_break,
    insert_table,
    insert_text,
    replace_image,
    replace_text,
)

TOOLS = (
    append_image,
    append_text,
    create_document,
    get_document,
    get_tab_content,
    insert_page_break,
    insert_table,
    insert_text,
    replace_image,
    replace_text,
)

__all__ = [
    "TOOLS",
    "append_image",
    "append_text",
    "create_document",
    "get_document",
    "get_tab_content",
    "insert_page_break",
    "insert_table",
    "insert_text",
    "manifest",
    "replace_image",
    "replace_text",
]

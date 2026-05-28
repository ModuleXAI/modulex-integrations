"""Typeform integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.typeform.manifest import manifest
from modulex_integrations.tools.typeform.tools import (
    create_form,
    create_image,
    delete_form,
    delete_image,
    duplicate_form,
    get_form,
    list_forms,
    list_images,
    list_responses,
    lookup_responses,
    update_dropdown_multiple_choice_ranking,
    update_form_title,
)

TOOLS = (
    list_forms,
    create_form,
    duplicate_form,
    delete_form,
    list_images,
    get_form,
    lookup_responses,
    list_responses,
    update_form_title,
    delete_image,
    create_image,
    update_dropdown_multiple_choice_ranking,
)

__all__ = [
    "TOOLS",
    "create_form",
    "create_image",
    "delete_form",
    "delete_image",
    "duplicate_form",
    "get_form",
    "list_forms",
    "list_images",
    "list_responses",
    "lookup_responses",
    "manifest",
    "update_dropdown_multiple_choice_ranking",
    "update_form_title",
]

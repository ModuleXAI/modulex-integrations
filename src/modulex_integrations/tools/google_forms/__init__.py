"""Google Forms integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_forms.manifest import manifest
from modulex_integrations.tools.google_forms.tools import (
    create_form,
    create_text_question,
    get_form,
    get_form_response,
    list_form_responses,
    update_form_title,
)

TOOLS = (
    create_form,
    create_text_question,
    get_form,
    get_form_response,
    list_form_responses,
    update_form_title,
)

__all__ = [
    "TOOLS",
    "create_form",
    "create_text_question",
    "get_form",
    "get_form_response",
    "list_form_responses",
    "manifest",
    "update_form_title",
]

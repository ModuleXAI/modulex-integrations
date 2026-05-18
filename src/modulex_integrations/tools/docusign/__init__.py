"""DocuSign integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.docusign.manifest import manifest
from modulex_integrations.tools.docusign.tools import (
    create_draft,
    create_envelope,
    create_envelope_from_file,
    create_recipient_view,
    create_signature_request,
    download_documents,
    get_envelope,
    list_documents,
    list_envelopes,
    list_recipients,
    send_envelope,
    void_envelope,
)

TOOLS = (
    create_signature_request,
    create_draft,
    create_envelope,
    create_envelope_from_file,
    create_recipient_view,
    get_envelope,
    list_envelopes,
    list_documents,
    list_recipients,
    send_envelope,
    download_documents,
    void_envelope,
)

__all__ = [
    "TOOLS",
    "create_draft",
    "create_envelope",
    "create_envelope_from_file",
    "create_recipient_view",
    "create_signature_request",
    "download_documents",
    "get_envelope",
    "list_documents",
    "list_envelopes",
    "list_recipients",
    "manifest",
    "send_envelope",
    "void_envelope",
]

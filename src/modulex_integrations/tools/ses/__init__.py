"""AWS SES integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.ses.manifest import manifest
from modulex_integrations.tools.ses.tools import (
    create_configuration_set,
    create_email_identity,
    create_template,
    delete_email_identity,
    delete_suppressed_destination,
    delete_template,
    get_account,
    get_email_identity,
    get_suppressed_destination,
    get_template,
    list_identities,
    list_suppressed_destinations,
    list_templates,
    put_suppressed_destination,
    send_bulk_email,
    send_custom_verification_email,
    send_email,
    send_templated_email,
    update_template,
)

TOOLS = (
    send_email,
    send_templated_email,
    send_bulk_email,
    list_identities,
    get_account,
    create_template,
    get_template,
    list_templates,
    delete_template,
    update_template,
    send_custom_verification_email,
    create_email_identity,
    get_email_identity,
    delete_email_identity,
    put_suppressed_destination,
    get_suppressed_destination,
    list_suppressed_destinations,
    delete_suppressed_destination,
    create_configuration_set,
)

__all__ = [
    "TOOLS",
    "create_configuration_set",
    "create_email_identity",
    "create_template",
    "delete_email_identity",
    "delete_suppressed_destination",
    "delete_template",
    "get_account",
    "get_email_identity",
    "get_suppressed_destination",
    "get_template",
    "list_identities",
    "list_suppressed_destinations",
    "list_templates",
    "manifest",
    "put_suppressed_destination",
    "send_bulk_email",
    "send_custom_verification_email",
    "send_email",
    "send_templated_email",
    "update_template",
]

"""Okta integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="okta",
    display_name="Okta",
    description=(
        "Manage users and user-type metadata in an Okta tenant via the "
        "Okta Management REST API (``/api/v1`` under your Okta subdomain)."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="https://cdn.jsdelivr.net/gh/ModuleXAI/logox@main/tools/okta.svg",
    app_url="https://www.okta.com",
    categories=["Identity & Access Management", "Productivity & Collaboration"],
    actions=[
        ActionDefinition(
            name="create_user",
            description=(
                "Create a new user in the Okta tenant. The user is activated "
                "by default unless ``activate`` is set to false."
            ),
            parameters={
                "first_name": ParameterDef(
                    type="string",
                    description="The first name of the user.",
                    required=True,
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="The last name of the user.",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="The email address of the user.",
                    required=True,
                ),
                "login": ParameterDef(
                    type="string",
                    description="The login (typically the email) for the user.",
                    required=True,
                ),
                "mobile_phone": ParameterDef(
                    type="string",
                    description="Optional mobile phone number for the user.",
                ),
                "type_id": ParameterDef(
                    type="string",
                    description=(
                        "Optional ID of a non-default user type. Use "
                        "list_type_id_options to enumerate available IDs."
                    ),
                ),
                "activate": ParameterDef(
                    type="boolean",
                    description=(
                        "Whether to execute the activation lifecycle on "
                        "creation. Defaults to true."
                    ),
                    default=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_user",
            description=(
                "Fetch a single Okta user by ID, login, or email address."
            ),
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description=(
                        "The unique identifier of the user (Okta user ID, "
                        "login, or email)."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_type_id_options",
            description=(
                "List the available user-type options for the tenant "
                "(``GET /meta/types/user``). Useful to discover valid "
                "``type_id`` values for create_user / update_user."
            ),
            parameters={},
        ),
        ActionDefinition(
            name="update_user",
            description=(
                "Update the profile of an existing Okta user. Only the "
                "fields you pass are changed; the existing profile is "
                "merged with your updates server-side."
            ),
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="The unique identifier of the user to update.",
                    required=True,
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="New first name for the user.",
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="New last name for the user.",
                ),
                "email": ParameterDef(
                    type="string",
                    description="New email address for the user.",
                ),
                "login": ParameterDef(
                    type="string",
                    description="New login for the user.",
                ),
                "mobile_phone": ParameterDef(
                    type="string",
                    description="New mobile phone number for the user.",
                ),
                "type_id": ParameterDef(
                    type="string",
                    description=(
                        "Optional new user type ID. Use list_type_id_options "
                        "to discover valid IDs."
                    ),
                ),
            },
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="Okta API Token",
            description=(
                "Authenticate with an Okta SSWS API token plus the tenant "
                "subdomain. The token is sent as ``Authorization: SSWS "
                "<token>`` and the subdomain is used to build the request "
                "host (``https://<subdomain>.okta.com``)."
            ),
            setup_instructions=[
                "Sign in to your Okta admin console.",
                "Open Security -> API -> Tokens, then click Create Token.",
                "Copy the generated SSWS token (it is shown only once).",
                "Your subdomain is the leading part of your admin URL, "
                "e.g. for ``acme.okta.com`` the subdomain is ``acme``.",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="OKTA_SUBDOMAIN",
                    display_name="Okta Subdomain",
                    description=(
                        "The tenant subdomain (e.g. ``acme`` for "
                        "``acme.okta.com``). Do not include ``.okta.com``."
                    ),
                    required=True,
                    sensitive=False,
                    sample_format="acme",
                    about_url="https://developer.okta.com/docs/guides/find-your-domain/main/",
                ),
                EnvVar(
                    name="OKTA_API_TOKEN",
                    display_name="Okta API Token",
                    description=(
                        "Your SSWS API token from Okta admin (Security -> "
                        "API -> Tokens)."
                    ),
                    required=True,
                    sensitive=True,
                    sample_format="00xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://developer.okta.com/docs/guides/create-an-api-token/main/",
                ),
            ],
            # No test_endpoint: validation requires templating a per-tenant
            # subdomain into the URL, which the modulex credential tester
            # does not substitute for ``custom`` auth.
        ),
    ],
)

"""Flint integration manifest.

Flint is an AI website platform whose background agents build and update
marketing sites. The Agent Tasks API
(``https://app.tryflint.com/api/v1``) starts a site change from a
natural-language prompt, fans a template page out into a batch of new
pages, and reports the status and resulting page URLs of any task.

Auth is a single organization-scoped API key (``ak_...``) sent as
``Authorization: Bearer <api_key>``, so this integration uses the
key-based runtime convention (``api_key`` is injected directly into each
``@tool`` function rather than an ``auth_type``/``auth_data`` pair).

No credential test endpoint is declared: the published API surface is
limited to creating and reading agent tasks, and neither can be probed
without either starting real work or guessing a task id, so the runtime
skips credential testing for this integration.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
)

__all__ = ["manifest"]


# --- Reusable parameter definitions ----------------------------------------


def _site_id() -> ParameterDef:
    return ParameterDef(
        type="string",
        description="ID (UUID) of the Flint site the agent should modify",
        required=True,
    )


def _callback_url() -> ParameterDef:
    return ParameterDef(
        type="string",
        description=(
            "HTTPS webhook URL that Flint POSTs to when the task completes or "
            "fails. Must be publicly reachable — private and internal addresses "
            "are rejected."
        ),
    )


def _publish(what: str) -> ParameterDef:
    return ParameterDef(
        type="boolean",
        description=(
            f"Whether to automatically publish {what} to the live domain when the "
            "task completes. Omit to keep Flint's own default."
        ),
    )


manifest = IntegrationManifest(
    name="flint",
    display_name="Flint",
    description=(
        "Create background agent tasks that modify your Flint sites from "
        "natural-language prompts, generate batches of pages from a template "
        "page, and check task status and results."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:flint-themed",
    app_url="https://www.flint.com",
    categories=["Marketing & Advertising", "seo", "automation", "content"],
    actions=[
        ActionDefinition(
            name="create_task",
            description=(
                "Start a background Flint agent task that modifies a site from a "
                "natural-language prompt. Returns immediately with a task id — "
                "poll get_task until the status is completed or failed."
            ),
            parameters={
                "site_id": _site_id(),
                "prompt": ParameterDef(
                    type="string",
                    description=(
                        "Natural-language instructions for the agent "
                        '(e.g. "Add a new About page with a team section")'
                    ),
                    required=True,
                ),
                "callback_url": _callback_url(),
                "publish": _publish("the changes"),
            },
        ),
        ActionDefinition(
            name="generate_pages",
            description=(
                "Start a background Flint agent task that generates up to 10 pages "
                "from an existing template page. Returns immediately with a task "
                "id — poll get_task until the status is completed or failed."
            ),
            parameters={
                "site_id": _site_id(),
                "template_page_slug": ParameterDef(
                    type="string",
                    description=(
                        "Slug of the existing template page to generate from "
                        "(e.g. /case-studies/template)"
                    ),
                    required=True,
                ),
                "items": ParameterDef(
                    type="array",
                    description=(
                        "Array of 1-10 pages to generate. Each item requires "
                        "targetPageSlug (slug for the new page, e.g. "
                        "/case-studies/acme-corp) and context (content details the "
                        "agent should use to fill in the template)."
                    ),
                    required=True,
                ),
                "callback_url": _callback_url(),
                "publish": _publish("the generated pages"),
            },
        ),
        ActionDefinition(
            name="get_task",
            description=(
                "Get the status and results of a background Flint agent task. A "
                "completed task exposes the created, modified, and deleted pages "
                "with their preview, edit, and published URLs; a failed task "
                "exposes the error message."
            ),
            parameters={
                "task_id": ParameterDef(
                    type="string",
                    description=(
                        "Identifier of the task returned when it was created "
                        "(e.g. bg-...)"
                    ),
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Flint API key",
            setup_instructions=[
                "Log in to Flint at https://app.tryflint.com",
                "Open team settings at https://app.tryflint.com/app/team",
                "Create an API key (member role or higher is required)",
                "Copy the key (it starts with 'ak_') and paste it below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="FLINT_API_KEY",
                    display_name="Flint API Key",
                    description=(
                        "Your organization-scoped Flint API key from team settings"
                    ),
                    required=True,
                    sensitive=True,
                    sample_format="ak_xxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://www.flint.com/docs/api",
                ),
            ],
        ),
    ],
)

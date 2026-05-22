"""Mixpanel integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="mixpanel",
    display_name="Mixpanel",
    description="Product analytics platform for tracking user events and behaviors",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:mixpanel-themed",
    app_url="https://mixpanel.com",
    categories=["Analytics", "Product Analytics"],
    actions=[
        ActionDefinition(
            name="emit_event_to",
            description="Send an event to Mixpanel",
            parameters={
                "event_name": ParameterDef(
                    type="string",
                    description="The name of the event (e.g. 'Button Click', 'Sign Up', 'Item Purchased')",
                    required=True,
                ),
                "distinct_id": ParameterDef(
                    type="string",
                    description="The unique identifier for the user performing the event",
                    required=True,
                ),
                "properties": ParameterDef(
                    type="object",
                    description="A set of properties to include with the event describing the user or event details",
                    required=False,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Project Token",
            description="Authenticate using your Mixpanel Project Token for event ingestion",
            setup_instructions=[
                "Sign in at https://mixpanel.com",
                "Go to Settings > Project Settings",
                "Copy your Project Token",
                "Paste the token below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="MIXPANEL_API_KEY",
                    display_name="Project Token",
                    description="Your Mixpanel Project Token from Settings > Project Settings",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://developer.mixpanel.com/reference/project-token",
                ),
            ],
        ),
    ],
)

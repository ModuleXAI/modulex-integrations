"""Segment integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    BasicAuthSpec,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="segment",
    display_name="Segment",
    description="Customer data platform for collecting, cleaning, and controlling customer data via the Segment Tracking API",
    version="1.0.0",
    author="ModuleX",
    logo="logos:segment-icon",
    app_url="https://segment.com",
    categories=["Analytics & Data", "Analytics", "Customer Data Platform"],
    actions=[
        ActionDefinition(
            name="alias",
            description="Associate one user identity with another in Segment",
            parameters={
                "previous_id": ParameterDef(
                    type="string",
                    description="Previous unique identifier for the user",
                    required=True,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="Unique identifier for the user in your database",
                ),
                "context": ParameterDef(
                    type="object",
                    description="Dictionary of extra context about the message such as IP address or locale",
                ),
                "integrations": ParameterDef(
                    type="object",
                    description="Dictionary of destinations to either enable or disable",
                ),
                "timestamp": ParameterDef(
                    type="string",
                    description="ISO 8601 timestamp of when the message occurred (e.g. 2022-04-08T17:32:11.318Z)",
                ),
            },
        ),
        ActionDefinition(
            name="group",
            description="Associate an identified user with a group in Segment",
            parameters={
                "group_id": ParameterDef(
                    type="string",
                    description="Unique identifier for the group in your database",
                    required=True,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="Unique identifier for the user. Either user_id or anonymous_id is required.",
                ),
                "anonymous_id": ParameterDef(
                    type="string",
                    description="Pseudo-unique substitute for a User ID when no absolute identifier is available",
                ),
                "traits": ParameterDef(
                    type="object",
                    description="Free-form dictionary of traits of the group such as name or plan",
                ),
                "context": ParameterDef(
                    type="object",
                    description="Dictionary of extra context about the message such as IP address or locale",
                ),
                "integrations": ParameterDef(
                    type="object",
                    description="Dictionary of destinations to either enable or disable",
                ),
                "timestamp": ParameterDef(
                    type="string",
                    description="ISO 8601 timestamp of when the message occurred (e.g. 2022-04-08T17:32:11.318Z)",
                ),
            },
        ),
        ActionDefinition(
            name="identify",
            description="Identify a user and record traits about them in Segment",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="Unique identifier for the user. Either user_id or anonymous_id is required.",
                ),
                "anonymous_id": ParameterDef(
                    type="string",
                    description="Pseudo-unique substitute for a User ID when no absolute identifier is available",
                ),
                "traits": ParameterDef(
                    type="object",
                    description="Free-form dictionary of traits of the user such as email or name",
                ),
                "context": ParameterDef(
                    type="object",
                    description="Dictionary of extra context about the message such as IP address or locale",
                ),
                "integrations": ParameterDef(
                    type="object",
                    description="Dictionary of destinations to either enable or disable",
                ),
                "timestamp": ParameterDef(
                    type="string",
                    description="ISO 8601 timestamp of when the message occurred (e.g. 2022-04-08T17:32:11.318Z)",
                ),
            },
        ),
        ActionDefinition(
            name="page",
            description="Record a page view on your website in Segment",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="Unique identifier for the user. Either user_id or anonymous_id is required.",
                ),
                "anonymous_id": ParameterDef(
                    type="string",
                    description="Pseudo-unique substitute for a User ID when no absolute identifier is available",
                ),
                "name": ParameterDef(
                    type="string",
                    description="Name of the page being viewed",
                ),
                "properties": ParameterDef(
                    type="object",
                    description="Free-form dictionary of properties of the page such as url and referrer",
                ),
                "context": ParameterDef(
                    type="object",
                    description="Dictionary of extra context about the message such as IP address or locale",
                ),
                "integrations": ParameterDef(
                    type="object",
                    description="Dictionary of destinations to either enable or disable",
                ),
                "timestamp": ParameterDef(
                    type="string",
                    description="ISO 8601 timestamp of when the message occurred (e.g. 2022-04-08T17:32:11.318Z)",
                ),
            },
        ),
        ActionDefinition(
            name="screen",
            description="Record a screen view in your mobile app in Segment",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="Unique identifier for the user. Either user_id or anonymous_id is required.",
                ),
                "anonymous_id": ParameterDef(
                    type="string",
                    description="Pseudo-unique substitute for a User ID when no absolute identifier is available",
                ),
                "name": ParameterDef(
                    type="string",
                    description="Name of the screen being viewed",
                ),
                "properties": ParameterDef(
                    type="object",
                    description="Free-form dictionary of properties of the screen",
                ),
                "context": ParameterDef(
                    type="object",
                    description="Dictionary of extra context about the message such as IP address or locale",
                ),
                "integrations": ParameterDef(
                    type="object",
                    description="Dictionary of destinations to either enable or disable",
                ),
                "timestamp": ParameterDef(
                    type="string",
                    description="ISO 8601 timestamp of when the message occurred (e.g. 2022-04-08T17:32:11.318Z)",
                ),
            },
        ),
        ActionDefinition(
            name="track",
            description="Track an event that a user has performed in Segment",
            parameters={
                "event": ParameterDef(
                    type="string",
                    description="Name of the action the user has performed",
                    required=True,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="Unique identifier for the user. Either user_id or anonymous_id is required.",
                ),
                "anonymous_id": ParameterDef(
                    type="string",
                    description="Pseudo-unique substitute for a User ID when no absolute identifier is available",
                ),
                "properties": ParameterDef(
                    type="object",
                    description="Free-form dictionary of properties of the event such as revenue",
                ),
                "context": ParameterDef(
                    type="object",
                    description="Dictionary of extra context about the message such as IP address or locale",
                ),
                "integrations": ParameterDef(
                    type="object",
                    description="Dictionary of destinations to either enable or disable",
                ),
                "timestamp": ParameterDef(
                    type="string",
                    description="ISO 8601 timestamp of when the message occurred (e.g. 2022-04-08T17:32:11.318Z)",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Write Key",
            description="Authenticate using your Segment source Write Key (used as HTTP Basic Auth)",
            setup_instructions=[
                "Log in to your Segment workspace at https://app.segment.com",
                "Navigate to Connections > Sources and select your source",
                "Go to the Settings tab and find the Write Key",
                "Copy the Write Key and paste it below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="SEGMENT_WRITE_KEY",
                    display_name="Write Key",
                    description="Your Segment source Write Key from app.segment.com",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://segment.com/docs/connections/find-writekey/",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.segment.io/v1/batch",
                method="POST",
                headers={"Content-Type": "application/json"},
                body={"batch": [], "sentAt": "2024-01-01T00:00:00.000Z"},
                # Segment Basic Auth: write_key as username, empty
                # password. The modulex runtime synthesises the
                # ``Authorization: Basic <base64(write_key:)>`` header.
                auth=BasicAuthSpec(
                    username_placeholder="SEGMENT_WRITE_KEY",
                    password_placeholder="",
                ),
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["success"],
                ),
                cost_level="free",
                description="Validates the write key via empty batch + Basic Auth.",
            ),
        ),
    ],
)

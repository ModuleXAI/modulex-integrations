"""Revolt integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    BearerTokenAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="revolt",
    display_name="Revolt",
    description="Revolt open-source chat platform — group management and friend requests",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:revolt-themed",
    app_url="https://revolt.chat",
    categories=["Communication"],
    actions=[
        ActionDefinition(
            name="create_group",
            description="Create a new group channel",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="The name of the group",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string",
                    description="Group description",
                ),
                "users": ParameterDef(
                    type="array",
                    description="IDs of the users to add to the group",
                ),
                "nsfw": ParameterDef(
                    type="boolean",
                    description="Whether this group is age-restricted",
                ),
            },
        ),
        ActionDefinition(
            name="add_group_member",
            description="Add another user to a group channel",
            parameters={
                "target": ParameterDef(
                    type="string",
                    description="ID of the group channel",
                    required=True,
                ),
                "member": ParameterDef(
                    type="string",
                    description="ID of the user to add",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="send_friend_request",
            description="Send a friend request to another user",
            parameters={
                "username": ParameterDef(
                    type="string",
                    description="Username and discriminator combo separated by #",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        BearerTokenAuthSchema(
            display_name="Session Token",
            description=(
                "Authenticate using your Revolt session token"
                " (sent as x-session-token header)"
            ),
            setup_environment_variables=[
                EnvVar(
                    name="REVOLT_SESSION_TOKEN",
                    display_name="Session Token",
                    description="Your Revolt session token from the Revolt client",
                    required=True,
                    sensitive=True,
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://revolt.chat/api/users/@me",
                method="GET",
                headers={"x-session-token": "{token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["_id"],
                ),
                cost_level="free",
                description="Validates the session token by fetching the current user",
            ),
        ),
    ],
)

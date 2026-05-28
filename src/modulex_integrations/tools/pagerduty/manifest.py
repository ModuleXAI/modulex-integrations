"""PagerDuty integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="pagerduty",
    display_name="PagerDuty",
    description="Incident management and on-call scheduling platform",
    version="1.0.0",
    author="ModuleX",
    logo="logos:pagerduty-icon",
    app_url="https://www.pagerduty.com",
    categories=["Incident Management", "Developer Tools & Infrastructure"],
    actions=[
        ActionDefinition(
            name="trigger_incident",
            description="Trigger a new incident on a PagerDuty service",
            parameters={
                "title": ParameterDef(
                    type="string",
                    description="A succinct description of the nature, symptoms, cause, or effect of the incident",
                    required=True,
                ),
                "service_id": ParameterDef(
                    type="string",
                    description="The ID of the PagerDuty service to trigger the incident on",
                    required=True,
                ),
                "urgency": ParameterDef(
                    type="string",
                    description="The urgency of the incident: high or low",
                ),
                "body_details": ParameterDef(
                    type="string",
                    description="Additional incident details",
                ),
                "incident_key": ParameterDef(
                    type="string",
                    description="A string which identifies the incident. Subsequent requests with the same key and service will be rejected if an open incident matches",
                ),
                "escalation_policy_id": ParameterDef(
                    type="string",
                    description="The ID of the escalation policy to assign",
                ),
                "assignee_ids": ParameterDef(
                    type="array",
                    description="List of user IDs to assign to the incident",
                ),
                "conference_bridge_number": ParameterDef(
                    type="string",
                    description="Phone number for the conference bridge (format: +1 415-555-1212,,,,1234#)",
                ),
                "conference_bridge_url": ParameterDef(
                    type="string",
                    description="URL for the conference bridge (e.g. a web conference or Slack channel link)",
                ),
            },
        ),
        ActionDefinition(
            name="acknowledge_incident",
            description="Acknowledge a triggered incident in PagerDuty",
            parameters={
                "incident_id": ParameterDef(
                    type="string",
                    description="The ID of the incident to acknowledge",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="resolve_incident",
            description="Resolve a triggered or acknowledged incident in PagerDuty",
            parameters={
                "incident_id": ParameterDef(
                    type="string",
                    description="The ID of the incident to resolve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="find_oncall_user",
            description="Find the user on call for a specific PagerDuty schedule",
            parameters={
                "schedule_id": ParameterDef(
                    type="string",
                    description="The ID of the on-call schedule",
                    required=True,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="The ID of the user to search for in the schedule",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using PagerDuty OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="PAGERDUTY_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="PagerDuty OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://developer.pagerduty.com/docs/app-integration-development/",
                ),
                EnvVar(
                    name="PAGERDUTY_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="PagerDuty OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://developer.pagerduty.com/docs/app-integration-development/",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://app.pagerduty.com/oauth/authorize",
                token_url="https://app.pagerduty.com/oauth/token",
                scopes=["read", "write"],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.pagerduty.com/users/me",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["user"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching the authenticated user",
            ),
        ),
    ],
)

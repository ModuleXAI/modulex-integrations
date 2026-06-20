"""CrowdStrike Falcon Identity Protection integration manifest.

Authentication uses the Falcon API OAuth2 client-credentials flow. The
runtime injects the **client secret** as ``api_key``; the **client ID**
and **cloud region** are ordinary action parameters. Each action
exchanges a short-lived bearer token before calling the Identity
Protection REST endpoint, so the credential cannot be validated with a
single declarative GET — no ``test_endpoint`` is shipped.
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


_CLOUD_PARAM = ParameterDef(
    type="string",
    description=(
        "CrowdStrike Falcon cloud region: one of 'us-1', 'us-2', 'eu-1', "
        "'us-gov-1', 'us-gov-2'"
    ),
    default="us-1",
    required=True,
)
_CLIENT_ID_PARAM = ParameterDef(
    type="string",
    description="CrowdStrike Falcon API client ID",
    required=True,
)


manifest = IntegrationManifest(
    name="crowdstrike",
    display_name="CrowdStrike",
    description=(
        "Integrate CrowdStrike Identity Protection into workflows to search "
        "sensors, fetch sensor details by device ID, and run sensor aggregate "
        "queries against the Falcon API."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:crowdstrike-themed",
    app_url="https://www.crowdstrike.com",
    categories=["Monitoring & Observability", "security", "identity"],
    actions=[
        ActionDefinition(
            name="query_sensors",
            description=(
                "Search CrowdStrike Identity Protection sensors by hostname, IP, "
                "or related fields using a Falcon Query Language filter."
            ),
            parameters={
                "client_id": _CLIENT_ID_PARAM,
                "cloud": _CLOUD_PARAM,
                "filter": ParameterDef(
                    type="string",
                    description="Falcon Query Language (FQL) filter for sensor search",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of sensor records to return (1-200)",
                ),
                "offset": ParameterDef(
                    type="integer",
                    description="Pagination offset for the sensor query",
                ),
                "sort": ParameterDef(
                    type="string",
                    description="Sort expression, e.g. 'status.asc'",
                ),
            },
        ),
        ActionDefinition(
            name="get_sensor_details",
            description=(
                "Get CrowdStrike Identity Protection sensor details for one or "
                "more device IDs."
            ),
            parameters={
                "client_id": _CLIENT_ID_PARAM,
                "cloud": _CLOUD_PARAM,
                "ids": ParameterDef(
                    type="array",
                    description="List of CrowdStrike sensor device IDs (max 5000)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_sensor_aggregates",
            description=(
                "Get CrowdStrike Identity Protection sensor aggregates from a "
                "JSON aggregate query body."
            ),
            parameters={
                "client_id": _CLIENT_ID_PARAM,
                "cloud": _CLOUD_PARAM,
                "aggregate_query": ParameterDef(
                    type="object",
                    description=(
                        "Aggregate query body documented by CrowdStrike (fields "
                        "such as field, filter, name, size, sort, type, "
                        "date_ranges, ranges, extended_bounds, sub_aggregates)"
                    ),
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description=(
                "Authenticate using a CrowdStrike Falcon API client. The client "
                "secret is the credential; the client ID and cloud region are "
                "supplied per action."
            ),
            setup_instructions=[
                "Sign in to the Falcon console and open Support and resources > "
                "API clients and keys.",
                "Create an API client granting it the Identity Protection scopes "
                "(Identity Protection Entities: Read, Identity Protection "
                "Sensor: Read).",
                "Copy the generated Client ID and Client Secret.",
                "Paste the Client Secret below as the API key; provide the Client "
                "ID and your cloud region (us-1, us-2, eu-1, us-gov-1, us-gov-2) "
                "as action parameters.",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="CROWDSTRIKE_CLIENT_SECRET",
                    display_name="CrowdStrike Client Secret",
                    description="Your CrowdStrike Falcon API client secret",
                    required=True,
                    sensitive=True,
                    about_url="https://falcon.crowdstrike.com/api-clients-and-keys/clients",
                ),
            ],
        ),
    ],
)

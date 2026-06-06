"""Amazon Alexa integration manifest."""
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
    name="amazon_alexa",
    display_name="Amazon Alexa",
    description="Simulate and test Alexa skills via the Alexa Skills Management API (SMAPI).",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:amazon_alexa",
    app_url="https://developer.amazon.com/alexa",
    categories=["AI & Machine Learning", "Voice Assistants", "IoT", "Smart Home"],
    actions=[
        ActionDefinition(
            name="simulate_skill",
            description="Simulate a dialog from an Alexa-enabled device and receive the skill response for the specified utterance.",
            parameters={
                "skill_id": ParameterDef(
                    type="string",
                    description="The unique identifier for the Alexa skill.",
                    required=True,
                ),
                "stage": ParameterDef(
                    type="string",
                    description="The stage of the skill: development or live.",
                    required=True,
                ),
                "content": ParameterDef(
                    type="string",
                    description="Utterance text from a user to Alexa.",
                    required=True,
                ),
                "locale": ParameterDef(
                    type="string",
                    description="Locale for the virtual device used in the simulation (e.g. en-US, en-GB, de-DE, fr-FR, ja-JP).",
                    default="en-US",
                ),
            },
        ),
        ActionDefinition(
            name="get_simulation_results",
            description="Get the results of a specified simulation for an Alexa skill.",
            parameters={
                "skill_id": ParameterDef(
                    type="string",
                    description="The unique identifier for the Alexa skill.",
                    required=True,
                ),
                "stage": ParameterDef(
                    type="string",
                    description="The stage of the skill: development or live.",
                    required=True,
                ),
                "simulation_id": ParameterDef(
                    type="string",
                    description="The identifier for the simulation.",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Amazon OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="AMAZON_ALEXA_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Amazon OAuth App Client ID from the Amazon Developer Console",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="amzn1.application-oa2-client.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://developer.amazon.com/loginwithamazon/console/site/lwa/overview.html",
                ),
                EnvVar(
                    name="AMAZON_ALEXA_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Amazon OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="x" * 64,
                    about_url="https://developer.amazon.com/loginwithamazon/console/site/lwa/overview.html",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://www.amazon.com/ap/oa",
                token_url="https://api.amazon.com/auth/o2/token",
                scopes=["alexa::ask:skills:readwrite", "alexa::ask:skills:test"],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.amazonalexa.com/v2/skills?vendorId=me",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                ),
                cost_level="free",
                description="Validates OAuth token by listing skills for the authenticated developer",
            ),
        ),
    ],
)

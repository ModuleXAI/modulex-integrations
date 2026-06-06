"""Bloomerang integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="bloomerang",
    display_name="Bloomerang",
    logo="modulex:bloomerang-themed",
    description="Nonprofit donor management and fundraising CRM platform",
    version="1.0.0",
    author="ModuleX",
    app_url="https://bloomerang.co",
    categories=["CRM", "Nonprofit", "Fundraising"],
    actions=[
        ActionDefinition(
            name="create_constituent",
            description="Creates a new constituent in Bloomerang",
            parameters={
                "type": ParameterDef(
                    type="string",
                    description="Constituent type. Valid values: Individual, Organization",
                    required=True,
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="First name of the constituent (used when type is Individual)",
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="Last name of the constituent (used when type is Individual)",
                ),
                "full_name": ParameterDef(
                    type="string",
                    description="Organization name (used when type is Organization)",
                ),
                "status": ParameterDef(
                    type="string",
                    description="Status of the constituent. Valid values: Active, Inactive, Deceased",
                ),
                "middle_name": ParameterDef(
                    type="string",
                    description="Middle name of the constituent",
                ),
                "prefix": ParameterDef(
                    type="string",
                    description="Prefix/title. Valid values: Mr., Mrs., Ms., Mx., Dr., Rev., etc.",
                ),
                "suffix": ParameterDef(
                    type="string",
                    description="Suffix. Valid values: Jr., Sr., II, III, IV, V, Ph.D., M.D., Esq., etc.",
                ),
                "job_title": ParameterDef(
                    type="string",
                    description="Job title of the constituent",
                ),
                "gender": ParameterDef(
                    type="string",
                    description="Gender. Valid values: Male, Female, Other",
                ),
                "birthdate": ParameterDef(
                    type="string",
                    description="Birth date of the constituent (ISO format YYYY-MM-DD)",
                ),
                "employer": ParameterDef(
                    type="string",
                    description="Employer of the constituent",
                ),
                "website": ParameterDef(
                    type="string",
                    description="Website URL of the constituent",
                ),
                "facebook_id": ParameterDef(
                    type="string",
                    description="Facebook page URL of the constituent",
                ),
                "twitter_id": ParameterDef(
                    type="string",
                    description="Twitter/X handle of the constituent",
                ),
                "linked_in_id": ParameterDef(
                    type="string",
                    description="LinkedIn page URL of the constituent",
                ),
                "preferred_communication_channel": ParameterDef(
                    type="string",
                    description="Preferred communication channel. Valid values: Email, Phone, Text Message, Mail",
                ),
            },
        ),
        ActionDefinition(
            name="create_donation",
            description="Creates a new donation record in Bloomerang",
            parameters={
                "constituent_id": ParameterDef(
                    type="string",
                    description="ID of the constituent (donor)",
                    required=True,
                ),
                "date": ParameterDef(
                    type="string",
                    description="Date of the donation (ISO format YYYY-MM-DD)",
                    required=True,
                ),
                "amount": ParameterDef(
                    type="string",
                    description="Donation amount as a numeric string",
                    required=True,
                ),
                "fund_id": ParameterDef(
                    type="string",
                    description="ID of the fund for the donation",
                    required=True,
                ),
                "payment_method": ParameterDef(
                    type="string",
                    description="Payment method. Valid values: None, Cash, Check, CreditCard, Eft, InKind, ApplePay, GooglePay, PayPal, Venmo",
                    required=True,
                ),
                "campaign_id": ParameterDef(
                    type="string",
                    description="ID of the campaign for the donation",
                ),
                "appeal_id": ParameterDef(
                    type="string",
                    description="ID of the appeal for the donation",
                ),
                "note": ParameterDef(
                    type="string",
                    description="Note for the donation",
                ),
            },
        ),
        ActionDefinition(
            name="add_interaction",
            description="Adds an interaction to an existing constituent in Bloomerang",
            parameters={
                "constituent_id": ParameterDef(
                    type="string",
                    description="ID of the constituent",
                    required=True,
                ),
                "date": ParameterDef(
                    type="string",
                    description="Date of the interaction (ISO format YYYY-MM-DD)",
                    required=True,
                ),
                "subject": ParameterDef(
                    type="string",
                    description="Subject of the interaction",
                    required=True,
                ),
                "channel": ParameterDef(
                    type="string",
                    description="Channel of the interaction. Valid values: Email, InPerson, Mail, MassEmail, Other, Phone, SocialMedia, TextMessage, VideoCall, Webinar, Website",
                    required=True,
                ),
                "purpose": ParameterDef(
                    type="string",
                    description="Purpose of the interaction. Valid values: Acknowledgement, ImpactCultivation, Newsletter, Receipt, Solicitation, SpecialEvent, VolunteerActivity, PledgeReminder, Welcome, Other",
                    required=True,
                ),
                "note": ParameterDef(
                    type="string",
                    description="Note for the interaction",
                ),
                "is_inbound": ParameterDef(
                    type="boolean",
                    description="Whether the interaction was initiated by the constituent",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Bloomerang API key",
            setup_instructions=[
                "Log in to your Bloomerang account",
                "Navigate to Settings > API Keys",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="BLOOMERANG_API_KEY",
                    display_name="Bloomerang API Key",
                    description="Your Bloomerang API key",
                    required=True,
                    sensitive=True,
                    about_url="https://bloomerang.co/product/integrations-data-management/api/rest-api/",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.bloomerang.co/v2/constituents?skip=0&take=1",
                method="GET",
                headers={"x-api-key": "{api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                ),
                cost_level="free",
                description="Validates the API key by fetching a single constituent",
            ),
        ),
    ],
)

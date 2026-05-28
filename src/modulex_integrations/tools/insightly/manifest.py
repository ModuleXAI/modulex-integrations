"""Insightly integration manifest."""
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
    name="insightly",
    display_name="Insightly",
    description="CRM and project management platform for managing contacts, tasks, and sales pipelines",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:insightly",
    app_url="https://www.insightly.com",
    categories=["CRM", "Sales", "Productivity & Collaboration"],
    actions=[
        ActionDefinition(
            name="create_contact",
            description="Creates a new contact in Insightly",
            parameters={
                "first_name": ParameterDef(
                    type="string",
                    description="The first name of the contact",
                    required=True,
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="The last name of the contact",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="The email address of the contact",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The title of the contact",
                ),
                "phone": ParameterDef(
                    type="string",
                    description="The phone number of the contact",
                ),
                "address_street": ParameterDef(
                    type="string",
                    description="The street address of the contact",
                ),
                "address_city": ParameterDef(
                    type="string",
                    description="The city of the contact",
                ),
                "address_state": ParameterDef(
                    type="string",
                    description="The state of the contact",
                ),
                "address_postcode": ParameterDef(
                    type="string",
                    description="The zip code/postcode of the contact",
                ),
                "address_country": ParameterDef(
                    type="string",
                    description="The country of the contact",
                ),
            },
        ),
        ActionDefinition(
            name="create_task",
            description="Creates a new task in Insightly",
            parameters={
                "title": ParameterDef(
                    type="string",
                    description="The title of the task",
                    required=True,
                ),
                "status": ParameterDef(
                    type="string",
                    description="The status of the task. Allowed values: Not Started, In Progress, Completed, Deferred, Waiting",
                    required=True,
                ),
                "due_date": ParameterDef(
                    type="string",
                    description="The due date of the task in YYYY-MM-DD format (e.g. 2023-08-20)",
                    required=True,
                ),
                "category_id": ParameterDef(
                    type="string",
                    description="Identifier of a task category",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Insightly API Key",
            description="Authenticate using your Insightly API key and pod identifier",
            setup_instructions=[
                "Log in to your Insightly account",
                "Go to User Settings > API",
                "Copy your API key",
                "Find your pod identifier from your Insightly URL (e.g. na1, au1)",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="INSIGHTLY_POD",
                    display_name="Pod",
                    description="Your Insightly pod/region identifier (e.g. na1, au1) found in your Insightly URL",
                    required=True,
                    sensitive=False,
                    sample_format="na1",
                    about_url="https://support.insightly.com",
                ),
                EnvVar(
                    name="INSIGHTLY_API_KEY",
                    display_name="API Key",
                    description="Your Insightly API key from User Settings > API",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://support.insightly.com",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.na1.insightly.com/v3.1/Users/Me",
                method="GET",
                headers={"Authorization": "Basic {api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["USER_ID"],
                ),
                cost_level="free",
                description="Validates credentials by fetching the current user profile",
            ),
        ),
    ],
)

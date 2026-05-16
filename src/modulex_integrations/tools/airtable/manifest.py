"""Airtable integration manifest."""
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
    name="airtable",
    display_name="Airtable",
    description=(
        "Cloud-based database platform for organizing, storing, and "
        "collaborating on structured data with spreadsheet-like interface "
        "and powerful automation capabilities."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:airtable",
    app_url="https://airtable.com",
    categories=[
        "Project & Task Management",
        "project_management",
        "workflow",
        "automation",
    ],
    actions=[
        ActionDefinition(
            name="list_bases",
            description="List all Airtable bases accessible with your API token",
            parameters={},
        ),
        ActionDefinition(
            name="list_tables",
            description=(
                "List all tables in a specific Airtable base with their "
                "fields and views"
            ),
            parameters={
                "base_id": ParameterDef(
                    type="string",
                    description="The ID of the Airtable base (starts with 'app')",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_records",
            description=(
                "List records from an Airtable table with optional "
                "filtering and sorting"
            ),
            parameters={
                "base_id": ParameterDef(
                    type="string",
                    description="The ID of the Airtable base",
                    required=True,
                ),
                "table_name": ParameterDef(
                    type="string",
                    description="Name or ID of the table",
                    required=True,
                ),
                "max_records": ParameterDef(
                    type="integer",
                    description="Maximum number of records to return (1-100)",
                    default=100,
                ),
                "filter_formula": ParameterDef(
                    type="string",
                    description="Airtable formula to filter records",
                ),
                "sort_field": ParameterDef(
                    type="string", description="Field name to sort by"
                ),
                "sort_direction": ParameterDef(
                    type="string",
                    description="Sort direction ('asc' or 'desc')",
                    default="asc",
                ),
                "view": ParameterDef(
                    type="string",
                    description="Name or ID of a view to use for filtering/sorting",
                ),
            },
        ),
        ActionDefinition(
            name="get_record",
            description="Get a specific record from an Airtable table by its ID",
            parameters={
                "base_id": ParameterDef(
                    type="string",
                    description="The ID of the Airtable base",
                    required=True,
                ),
                "table_name": ParameterDef(
                    type="string",
                    description="Name or ID of the table",
                    required=True,
                ),
                "record_id": ParameterDef(
                    type="string",
                    description="The ID of the record (starts with 'rec')",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_records",
            description=(
                "Create one or more records in an Airtable table. Batched "
                "up to 10 per request."
            ),
            parameters={
                "base_id": ParameterDef(
                    type="string",
                    description="The ID of the Airtable base",
                    required=True,
                ),
                "table_name": ParameterDef(
                    type="string",
                    description="Name or ID of the table",
                    required=True,
                ),
                "records": ParameterDef(
                    type="array",
                    description="List of {field: value} record objects",
                    required=True,
                ),
                "typecast": ParameterDef(
                    type="boolean",
                    description=(
                        "If true, Airtable converts string values to the "
                        "appropriate cell types"
                    ),
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="update_records",
            description=(
                "Update one or more records in an Airtable table. Each "
                "record must include `id`; remaining fields can be nested "
                "under `fields` or at the top level."
            ),
            parameters={
                "base_id": ParameterDef(
                    type="string",
                    description="The ID of the Airtable base",
                    required=True,
                ),
                "table_name": ParameterDef(
                    type="string",
                    description="Name or ID of the table",
                    required=True,
                ),
                "records": ParameterDef(
                    type="array",
                    description=(
                        "Records to update; each is "
                        "{'id': 'rec…', 'fields': {…}} or "
                        "{'id': 'rec…', 'field_a': value, …}"
                    ),
                    required=True,
                ),
                "typecast": ParameterDef(
                    type="boolean",
                    description=(
                        "If true, Airtable converts string values to the "
                        "appropriate cell types"
                    ),
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="delete_records",
            description=(
                "Delete one or more records from an Airtable table. "
                "Batched up to 10 per request."
            ),
            parameters={
                "base_id": ParameterDef(
                    type="string",
                    description="The ID of the Airtable base",
                    required=True,
                ),
                "table_name": ParameterDef(
                    type="string",
                    description="Name or ID of the table",
                    required=True,
                ),
                "record_ids": ParameterDef(
                    type="array",
                    description="List of record IDs to delete (each starts with 'rec')",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Personal Access Token",
            description=(
                "Authenticate using your Airtable Personal Access Token. "
                "Create one at airtable.com/create/tokens"
            ),
            setup_environment_variables=[
                EnvVar(
                    name="AIRTABLE_API_KEY",
                    display_name="Airtable Personal Access Token",
                    description="Your Airtable Personal Access Token for API authentication",
                    required=True,
                    sensitive=True,
                    sample_format=(
                        "patXXXXXXXXXXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXX"
                        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
                    ),
                    about_url="https://airtable.com/create/tokens",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.airtable.com/v0/meta/bases",
                method="GET",
                headers={
                    "Authorization": "Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["bases"]
                ),
                cost_level="minimal",
                description="Validates Personal Access Token by listing accessible bases",
            ),
        ),
    ],
)

"""Google AppSheet integration manifest."""
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
    name="google_appsheet",
    display_name="Google AppSheet",
    description="Manage rows in Google AppSheet tables via the AppSheet API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:google_appsheet",
    app_url="https://www.appsheet.com",
    categories=["Productivity & Collaboration", "no-code", "databases"],
    actions=[
        ActionDefinition(
            name="add_row",
            description="Add a new row to a specific table in the AppSheet app",
            parameters={
                "table_name": ParameterDef(
                    type="string",
                    description="Name of the table to add a row to",
                    required=True,
                ),
                "row": ParameterDef(
                    type="object",
                    description="JSON object representing the row data to add, with keys matching table column names",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_row",
            description="Delete a specific row from a table in the AppSheet app",
            parameters={
                "table_name": ParameterDef(
                    type="string",
                    description="Name of the table to delete a row from",
                    required=True,
                ),
                "row": ParameterDef(
                    type="object",
                    description="JSON object containing the key field values of the record to delete",
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_rows",
            description="Read existing records from a table in the AppSheet app",
            parameters={
                "table_name": ParameterDef(
                    type="string",
                    description="Name of the table to read rows from",
                    required=True,
                ),
                "selector": ParameterDef(
                    type="string",
                    description="An expression to filter and format the rows returned, e.g. Filter(TableName, [Column] = \"Value\")",
                    required=False,
                ),
                "row": ParameterDef(
                    type="object",
                    description="Filter results using key field values, e.g. {\"First Name\": \"John\"}",
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="update_row",
            description="Update an existing row in a specific table in the AppSheet app",
            parameters={
                "table_name": ParameterDef(
                    type="string",
                    description="Name of the table containing the row to update",
                    required=True,
                ),
                "row": ParameterDef(
                    type="object",
                    description="JSON object with the key field values of the record to update and any fields to change",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="AppSheet API Key",
            description="Authenticate using your AppSheet Application Access Key and App ID",
            setup_instructions=[
                "Open your app in AppSheet at https://www.appsheet.com",
                "Go to Settings > Integrations > IN: from cloud services to your app",
                "Enable the API and copy the Application Access Key",
                "Copy the App ID from the URL or Settings > App Info",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_APPSHEET_APP_ID",
                    display_name="App ID",
                    description="Your AppSheet application ID (found in Settings > App Info or the app URL)",
                    required=True,
                    sensitive=False,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://support.google.com/appsheet/answer/10104797",
                ),
                EnvVar(
                    name="GOOGLE_APPSHEET_API_KEY",
                    display_name="Application Access Key",
                    description="Your AppSheet Application Access Key from Settings > Integrations",
                    required=True,
                    sensitive=True,
                    sample_format="V2-xxxxx-xxxxx-xxxxx-xxxxx-xxxxx",
                    about_url="https://support.google.com/appsheet/answer/10104797",
                ),
            ],
        ),
    ],
)

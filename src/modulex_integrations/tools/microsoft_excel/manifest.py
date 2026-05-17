"""Microsoft Excel integration manifest."""
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
    name="microsoft_excel",
    display_name="Microsoft Excel",
    description=(
        "Read, write, and manage Excel workbooks stored in OneDrive via the "
        "Microsoft Graph API."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:microsoft_excel-themed",
    app_url="https://www.microsoft.com/en-us/microsoft-365/excel",
    categories=["Productivity & Collaboration", "Spreadsheets"],
    actions=[
        ActionDefinition(
            name="add_a_worksheet_tablerow",
            description=(
                "Adds rows to the end of a specific Excel table. Provide either "
                "tableId or tableName."
            ),
            parameters={
                "sheet_id": ParameterDef(
                    type="string",
                    description=(
                        "Drive item ID of the workbook (the spreadsheet file) "
                        "in OneDrive."
                    ),
                    required=True,
                ),
                "values": ParameterDef(
                    type="array",
                    description=(
                        "Two-dimensional array of unformatted row values, e.g. "
                        "[[1, 2, 3], [4, 5, 6]]. Each inner array is one row."
                    ),
                    required=True,
                ),
                "table_id": ParameterDef(
                    type="string",
                    description=(
                        "ID of the workbook table to append to. Provide either "
                        "table_id or table_name."
                    ),
                ),
                "table_name": ParameterDef(
                    type="string",
                    description=(
                        "Name of the workbook table (set in the Table Design "
                        "tab). Used when table_id is not available, e.g. for "
                        "personal accounts."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="add_row",
            description=(
                "Insert a new row at the end of the used range of an Excel "
                "worksheet."
            ),
            parameters={
                "sheet_id": ParameterDef(
                    type="string",
                    description="Drive item ID of the workbook in OneDrive.",
                    required=True,
                ),
                "worksheet": ParameterDef(
                    type="string",
                    description="Name of the worksheet to append the row to.",
                    required=True,
                ),
                "values": ParameterDef(
                    type="array",
                    description=(
                        "Array of cell values for the new row, e.g. [1, 2, 3]. "
                        "Each item is one cell."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="find_row",
            description=(
                "Find the first row in an Excel worksheet where the given "
                "column contains the given value."
            ),
            parameters={
                "sheet_id": ParameterDef(
                    type="string",
                    description="Drive item ID of the workbook in OneDrive.",
                    required=True,
                ),
                "worksheet": ParameterDef(
                    type="string",
                    description="Name of the worksheet to search.",
                    required=True,
                ),
                "column": ParameterDef(
                    type="string",
                    description="Column letter to search, e.g. 'A'.",
                    required=True,
                ),
                "value": ParameterDef(
                    type="string",
                    description=(
                        "Value to search for. Numeric strings will also be "
                        "matched as numbers."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_columns",
            description=(
                "Get all values in the requested columns of an Excel "
                "worksheet's used range."
            ),
            parameters={
                "sheet_id": ParameterDef(
                    type="string",
                    description="Drive item ID of the workbook in OneDrive.",
                    required=True,
                ),
                "worksheet": ParameterDef(
                    type="string",
                    description="Name of the worksheet to read.",
                    required=True,
                ),
                "columns": ParameterDef(
                    type="array",
                    description=(
                        "Array of column letters to retrieve, e.g. ['A', 'C']."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_spreadsheet",
            description=(
                "Get the values of the specified range (or the entire used "
                "range) of an Excel worksheet."
            ),
            parameters={
                "sheet_id": ParameterDef(
                    type="string",
                    description="Drive item ID of the workbook in OneDrive.",
                    required=True,
                ),
                "worksheet": ParameterDef(
                    type="string",
                    description="Name of the worksheet to read.",
                    required=True,
                ),
                "range": ParameterDef(
                    type="string",
                    description=(
                        "Range within the worksheet, e.g. 'A1:C4'. If omitted, "
                        "the entire used range is returned."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="get_table_rows",
            description="Retrieve all rows from a specified table in an Excel worksheet.",
            parameters={
                "sheet_id": ParameterDef(
                    type="string",
                    description="Drive item ID of the workbook in OneDrive.",
                    required=True,
                ),
                "table_id": ParameterDef(
                    type="string",
                    description="ID of the workbook table whose rows you want.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_folder_id_options",
            description=(
                "List OneDrive folders the user can browse to pick a workbook "
                "location. Returns label/value pairs suitable for a folder "
                "picker."
            ),
            parameters={
                "max_pages": ParameterDef(
                    type="integer",
                    description=(
                        "Maximum number of batch pages to fetch (1-500). "
                        "Default 50."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="update_cell",
            description="Update the value of a specific cell in an Excel worksheet.",
            parameters={
                "sheet_id": ParameterDef(
                    type="string",
                    description="Drive item ID of the workbook in OneDrive.",
                    required=True,
                ),
                "worksheet": ParameterDef(
                    type="string",
                    description="Name of the worksheet containing the cell.",
                    required=True,
                ),
                "cell": ParameterDef(
                    type="string",
                    description="Cell address to update, e.g. 'A1'.",
                    required=True,
                ),
                "value": ParameterDef(
                    type="string",
                    description="Value to write to the cell.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_worksheet_tablerow",
            description=(
                "Update the values of an existing row in an Excel workbook "
                "table (work or school accounts only)."
            ),
            parameters={
                "sheet_id": ParameterDef(
                    type="string",
                    description="Drive item ID of the workbook in OneDrive.",
                    required=True,
                ),
                "table_id": ParameterDef(
                    type="string",
                    description="ID of the workbook table.",
                    required=True,
                ),
                "row_id": ParameterDef(
                    type="integer",
                    description="Zero-based index of the row to update.",
                    required=True,
                ),
                "values": ParameterDef(
                    type="array",
                    description=(
                        "Array of cell values for the updated row, e.g. "
                        "[1, 2, 3]. Each item is one cell."
                    ),
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="Microsoft OAuth 2.0",
            description=(
                "Connect to Microsoft Excel via Microsoft Identity Platform "
                "OAuth (recommended). Requires consent to access OneDrive files."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="MICROSOFT_EXCEL_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Microsoft Entra ID (Azure AD) application Client ID.",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="00000000-0000-0000-0000-000000000000",
                    about_url="https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app",
                ),
                EnvVar(
                    name="MICROSOFT_EXCEL_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Microsoft Entra ID application Client Secret value.",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="x" * 40,
                    about_url="https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
                scopes=[
                    "Files.ReadWrite",
                    "User.Read",
                    "offline_access",
                ],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://graph.microsoft.com/v1.0/me",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["id"],
                ),
                cost_level="free",
                description=(
                    "Validates the OAuth token by fetching the authenticated "
                    "Microsoft user profile."
                ),
            ),
        ),
    ],
)

"""Google Sheets integration manifest."""
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
    name="google_sheets",
    display_name="Google Sheets",
    description="Read, write, and manage Google Sheets spreadsheets and worksheets.",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:google_sheets",
    app_url="https://www.google.com/sheets/about/",
    categories=["Productivity & Collaboration", "Data & Analytics"],
    actions=[
        ActionDefinition(
            name="new_spreadsheet",
            description=(
                "Create a new Google Spreadsheet with an optional worksheet name "
                "and column headers. Returns the spreadsheet ID and URL."
            ),
            parameters={
                "title": ParameterDef(
                    type="string",
                    description="The title of the new spreadsheet.",
                    required=True,
                ),
                "sheet_name": ParameterDef(
                    type="string",
                    description="Name for the first worksheet. Default: 'Sheet1'.",
                    required=False,
                ),
                "headers": ParameterDef(
                    type="array",
                    description=(
                        "Column headers to add as row 1. Each item is a string. "
                        'Example: ["Name", "Email", "Score"].'
                    ),
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_spreadsheet_info",
            description=(
                "Get the structure of a Google Spreadsheet: worksheet names, "
                "column headers (first row of each sheet), and row counts. Call "
                "this first before reading or writing data."
            ),
            parameters={
                "spreadsheet_id": ParameterDef(
                    type="string",
                    description="The spreadsheet ID from the Google Sheets URL.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_worksheets",
            description="Get a list of all worksheets (tabs) in a spreadsheet.",
            parameters={
                "spreadsheet_id": ParameterDef(
                    type="string",
                    description="The spreadsheet ID from the Google Sheets URL.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="add_worksheet",
            description=(
                "Add a new worksheet (tab) to an existing spreadsheet. "
                "Optionally set column headers."
            ),
            parameters={
                "spreadsheet_id": ParameterDef(
                    type="string",
                    description="The spreadsheet ID from the Google Sheets URL.",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The name of the new worksheet (tab).",
                    required=True,
                ),
                "headers": ParameterDef(
                    type="array",
                    description=(
                        "Column headers to add as row 1. Each item is a string. "
                        'Example: ["Name", "Email", "Score"].'
                    ),
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="delete_worksheet",
            description="Delete a specific worksheet (tab) from a spreadsheet.",
            parameters={
                "spreadsheet_id": ParameterDef(
                    type="string",
                    description="The spreadsheet ID from the Google Sheets URL.",
                    required=True,
                ),
                "worksheet_id": ParameterDef(
                    type="integer",
                    description=(
                        "The numeric worksheet (sheet) ID to delete. Use "
                        "get_spreadsheet_info to discover sheet IDs."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="read_rows",
            description=(
                "Read rows from a Google Sheets worksheet. Returns data as objects "
                "(keys = column headers from row 1) by default, or as raw arrays. "
                "Optionally specify an A1 range to read a subset."
            ),
            parameters={
                "spreadsheet_id": ParameterDef(
                    type="string",
                    description="The spreadsheet ID from the Google Sheets URL.",
                    required=True,
                ),
                "sheet_name": ParameterDef(
                    type="string",
                    description="The worksheet (tab) name.",
                    required=True,
                ),
                "range": ParameterDef(
                    type="string",
                    description=(
                        "Optional A1 notation range within the sheet (e.g. "
                        "'A1:D10', 'A:F'). Omit to read all data."
                    ),
                    required=False,
                ),
                "has_headers": ParameterDef(
                    type="boolean",
                    description=(
                        "Whether row 1 contains column headers. If true, returns "
                        "rows as objects with header keys."
                    ),
                    default=True,
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_values_in_range",
            description=(
                "Get all values from a range of cells using A1 notation. Returns "
                "a list of rows where each row is a list of cell values."
            ),
            parameters={
                "spreadsheet_id": ParameterDef(
                    type="string",
                    description="The spreadsheet ID from the Google Sheets URL.",
                    required=True,
                ),
                "sheet_name": ParameterDef(
                    type="string",
                    description="The worksheet (tab) name.",
                    required=True,
                ),
                "range": ParameterDef(
                    type="string",
                    description=(
                        "A1 notation range within the sheet (e.g. 'A1:E5'). "
                        "Omit to read the entire sheet."
                    ),
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="find_rows",
            description=(
                "Search for rows matching a value in a specific column. Returns "
                "matching rows as objects with their row numbers."
            ),
            parameters={
                "spreadsheet_id": ParameterDef(
                    type="string",
                    description="The spreadsheet ID from the Google Sheets URL.",
                    required=True,
                ),
                "sheet_name": ParameterDef(
                    type="string",
                    description="The worksheet (tab) name.",
                    required=True,
                ),
                "column": ParameterDef(
                    type="string",
                    description=(
                        "Column header name (e.g. 'Name') or column letter "
                        "(e.g. 'A', 'B')."
                    ),
                    required=True,
                ),
                "search_value": ParameterDef(
                    type="string",
                    description="The value to search for.",
                    required=True,
                ),
                "match_type": ParameterDef(
                    type="string",
                    description=(
                        "How to match. Valid values: 'exact' "
                        "(case-insensitive exact match), 'contains' (substring), "
                        "'starts_with'."
                    ),
                    default="contains",
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="add_rows",
            description=(
                "Append one or more rows to a Google Sheets worksheet. Pass rows "
                "as a JSON array — either arrays of positional values (e.g. "
                '[["Alice", "alice@example.com"]]) or objects with column header '
                'keys (e.g. [{"Name": "Alice", "Email": "alice@example.com"}]). '
                "Use get_spreadsheet_info first to discover header names."
            ),
            parameters={
                "spreadsheet_id": ParameterDef(
                    type="string",
                    description="The spreadsheet ID from the Google Sheets URL.",
                    required=True,
                ),
                "sheet_name": ParameterDef(
                    type="string",
                    description="The worksheet (tab) name.",
                    required=True,
                ),
                "rows": ParameterDef(
                    type="array",
                    description=(
                        "Array of rows to append. Each row is either an array of "
                        "positional cell values or an object whose keys match "
                        "the worksheet's column headers."
                    ),
                    required=True,
                ),
                "has_headers": ParameterDef(
                    type="boolean",
                    description=(
                        "Whether row 1 contains column headers. Required when "
                        "passing rows as objects."
                    ),
                    default=True,
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="update_row",
            description=(
                "Overwrite the contents of a specific row with a new list of "
                "values (positional, matching column order)."
            ),
            parameters={
                "spreadsheet_id": ParameterDef(
                    type="string",
                    description="The spreadsheet ID from the Google Sheets URL.",
                    required=True,
                ),
                "sheet_name": ParameterDef(
                    type="string",
                    description="The worksheet (tab) name.",
                    required=True,
                ),
                "row": ParameterDef(
                    type="integer",
                    description="1-indexed row number to update.",
                    required=True,
                ),
                "values": ParameterDef(
                    type="array",
                    description=(
                        "Array of cell values for the row, in column order. "
                        "Numbers, strings, and booleans are all accepted."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_cell",
            description=(
                "Update a single cell in a worksheet by A1 notation. The new "
                "value is parsed as if typed in the UI (USER_ENTERED)."
            ),
            parameters={
                "spreadsheet_id": ParameterDef(
                    type="string",
                    description="The spreadsheet ID from the Google Sheets URL.",
                    required=True,
                ),
                "sheet_name": ParameterDef(
                    type="string",
                    description="The worksheet (tab) name.",
                    required=True,
                ),
                "cell": ParameterDef(
                    type="string",
                    description="A1 notation for the cell (e.g. 'B5').",
                    required=True,
                ),
                "value": ParameterDef(
                    type="string",
                    description="The new cell value.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="clear_rows",
            description=(
                "Clear the contents of a row or range of rows. The rows still "
                "exist but become blank."
            ),
            parameters={
                "spreadsheet_id": ParameterDef(
                    type="string",
                    description="The spreadsheet ID from the Google Sheets URL.",
                    required=True,
                ),
                "sheet_name": ParameterDef(
                    type="string",
                    description="The worksheet (tab) name.",
                    required=True,
                ),
                "start_index": ParameterDef(
                    type="integer",
                    description="1-indexed row number of the first row to clear (inclusive).",
                    required=True,
                ),
                "end_index": ParameterDef(
                    type="integer",
                    description=(
                        "1-indexed row number of the last row to clear "
                        "(inclusive). Omit to clear only the start row."
                    ),
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="delete_rows",
            description=(
                "Permanently delete a range of rows from a worksheet. Rows below "
                "the deleted range shift up to fill the gap."
            ),
            parameters={
                "spreadsheet_id": ParameterDef(
                    type="string",
                    description="The spreadsheet ID from the Google Sheets URL.",
                    required=True,
                ),
                "worksheet_id": ParameterDef(
                    type="integer",
                    description=(
                        "The numeric worksheet (sheet) ID. Use "
                        "get_spreadsheet_info to discover sheet IDs."
                    ),
                    required=True,
                ),
                "start_index": ParameterDef(
                    type="integer",
                    description="1-indexed row number of the first row to delete (inclusive).",
                    required=True,
                ),
                "end_index": ParameterDef(
                    type="integer",
                    description=(
                        "1-indexed row number of the last row to delete "
                        "(inclusive). Omit to delete only the start row."
                    ),
                    required=False,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Google OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_SHEETS_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google OAuth Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxx.apps.googleusercontent.com",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_SHEETS_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google OAuth Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="GOCSPX-xxxxxxxxxxxxxxxxxxxx",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                access_type="offline",
                prompt="consent",
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive.file",
                ],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://www.googleapis.com/drive/v3/about?fields=user",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["user"],
                ),
                cost_level="free",
                description=(
                    "Validates the OAuth token via the Drive about endpoint "
                    "(reachable with the drive.file scope)."
                ),
            ),
        ),
    ],
)

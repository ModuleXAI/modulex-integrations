"""Google Drive (+ Docs / Sheets / Slides) integration manifest.

OAuth scopes drop the ``access_type`` and ``prompt`` legacy fields —
``OAuthConfig`` doesn't carry them (same as gmail).
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    BearerTokenAuthSchema,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


def _test_endpoint(placeholder: str) -> TestEndpoint:
    return TestEndpoint(
        url="https://www.googleapis.com/drive/v3/about",
        method="GET",
        headers={"Authorization": f"Bearer {{{placeholder}}}"},
        params={"fields": "user"},
        success_indicators=SuccessIndicators(
            status_codes=[200], response_fields=["user"]
        ),
        cost_level="free",
        description="Validates OAuth token via Drive /about endpoint",
    )


def _file_id_param() -> ParameterDef:
    return ParameterDef(type="string", description="File ID", required=True)


def _spreadsheet_id_param() -> ParameterDef:
    return ParameterDef(
        type="string", description="Spreadsheet ID", required=True
    )


def _presentation_id_param() -> ParameterDef:
    return ParameterDef(
        type="string", description="Presentation ID", required=True
    )


def _document_id_param() -> ParameterDef:
    return ParameterDef(type="string", description="Document ID", required=True)


def _name_param(item: str) -> ParameterDef:
    return ParameterDef(
        type="string", description=f"{item} name", required=True
    )


manifest = IntegrationManifest(
    name="google_drive",
    display_name="Google Drive",
    description=(
        "Google Workspace integration: Drive (files/folders), Docs, "
        "Sheets, and Slides via the v3 / v1 REST APIs."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:google-drive",
    app_url="https://drive.google.com",
    categories=["File Storage", "Document Management", "Productivity"],
    actions=[
        # --- Drive ---------------------------------------------------------
        ActionDefinition(
            name="search_files",
            description="Search files in Google Drive by name substring",
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Substring to match in file name",
                    required=True,
                ),
                "page_size": ParameterDef(
                    type="integer", description="Results (max 100)", default=10
                ),
                "page_token": ParameterDef(
                    type="string", description="Pagination token"
                ),
            },
        ),
        ActionDefinition(
            name="list_folder",
            description="List files + subfolders in a folder (use 'root' for root)",
            parameters={
                "folder_id": ParameterDef(
                    type="string", description="Folder ID", default="root"
                ),
                "page_size": ParameterDef(
                    type="integer", description="Results (max 100)", default=20
                ),
                "page_token": ParameterDef(
                    type="string", description="Pagination token"
                ),
            },
        ),
        ActionDefinition(
            name="read_file",
            description=(
                "Read a file's content — exports Google Docs as plain text, "
                "downloads text/* directly, otherwise returns the web link"
            ),
            parameters={"file_id": _file_id_param()},
        ),
        ActionDefinition(
            name="create_text_file",
            description=(
                "Create a plain text (.txt) or markdown (.md) file via "
                "multipart upload"
            ),
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="File name (must end with .txt or .md)",
                    required=True,
                ),
                "content": ParameterDef(
                    type="string", description="Text content", required=True
                ),
                "parent_folder_id": ParameterDef(
                    type="string", description="Parent folder (defaults to root)"
                ),
            },
        ),
        ActionDefinition(
            name="update_text_file",
            description=(
                "Replace a text file's content via media upload; optionally "
                "rename in a follow-up call"
            ),
            parameters={
                "file_id": _file_id_param(),
                "content": ParameterDef(
                    type="string", description="New content", required=True
                ),
                "name": ParameterDef(type="string", description="Optional new name"),
            },
        ),
        ActionDefinition(
            name="create_folder",
            description="Create a folder",
            parameters={
                "name": _name_param("Folder"),
                "parent_folder_id": ParameterDef(
                    type="string", description="Parent folder ID"
                ),
            },
        ),
        ActionDefinition(
            name="delete_item",
            description="Permanently delete a file or folder",
            parameters={
                "item_id": ParameterDef(
                    type="string", description="File / folder ID", required=True
                ),
            },
        ),
        ActionDefinition(
            name="rename_item",
            description="Rename a file or folder",
            parameters={
                "item_id": ParameterDef(
                    type="string", description="File / folder ID", required=True
                ),
                "new_name": ParameterDef(
                    type="string", description="New name", required=True
                ),
            },
        ),
        ActionDefinition(
            name="move_item",
            description=(
                "Move a file/folder to a destination (N+1: read parents, "
                "then PATCH with addParents/removeParents)"
            ),
            parameters={
                "item_id": ParameterDef(
                    type="string", description="File / folder ID", required=True
                ),
                "destination_folder_id": ParameterDef(
                    type="string",
                    description="Destination folder ID",
                    default="root",
                ),
            },
        ),
        ActionDefinition(
            name="copy_file",
            description="Copy a file (optionally rename / change folder)",
            parameters={
                "file_id": _file_id_param(),
                "new_name": ParameterDef(type="string", description="Copy name"),
                "destination_folder_id": ParameterDef(
                    type="string", description="Destination folder"
                ),
            },
        ),
        ActionDefinition(
            name="get_file_metadata",
            description="Get full metadata for a file/folder",
            parameters={"file_id": _file_id_param()},
        ),
        # --- Docs ----------------------------------------------------------
        ActionDefinition(
            name="create_google_doc",
            description=(
                "Create a Google Doc (Drive create + optional Docs "
                "batchUpdate to insert content)"
            ),
            parameters={
                "name": _name_param("Document"),
                "content": ParameterDef(
                    type="string", description="Initial content", default=""
                ),
                "parent_folder_id": ParameterDef(
                    type="string", description="Parent folder ID"
                ),
            },
        ),
        ActionDefinition(
            name="read_google_doc",
            description="Read full text content from a Google Doc",
            parameters={"document_id": _document_id_param()},
        ),
        ActionDefinition(
            name="update_google_doc",
            description=(
                "Replace all content (read end-index, deleteContentRange, "
                "insertText)"
            ),
            parameters={
                "document_id": _document_id_param(),
                "content": ParameterDef(
                    type="string", description="New content", required=True
                ),
            },
        ),
        ActionDefinition(
            name="append_to_google_doc",
            description="Append content at the end of a doc",
            parameters={
                "document_id": _document_id_param(),
                "content": ParameterDef(
                    type="string", description="Content to append", required=True
                ),
            },
        ),
        # --- Sheets --------------------------------------------------------
        ActionDefinition(
            name="create_google_sheet",
            description=(
                "Create a Sheet (Sheets API create + optional Drive PATCH "
                "to move + optional Sheets API values write)"
            ),
            parameters={
                "name": _name_param("Spreadsheet"),
                "data": ParameterDef(
                    type="array", description="Initial data (2D array)"
                ),
                "parent_folder_id": ParameterDef(
                    type="string", description="Parent folder ID"
                ),
            },
        ),
        ActionDefinition(
            name="read_google_sheet",
            description=(
                "Read values from a range (resolves localized sheet name "
                "via /spreadsheets?fields=sheets.properties.title)"
            ),
            parameters={
                "spreadsheet_id": _spreadsheet_id_param(),
                "range": ParameterDef(
                    type="string",
                    description="A1 notation (e.g. 'Sheet1!A1:D10')",
                    default="Sheet1",
                ),
            },
        ),
        ActionDefinition(
            name="update_google_sheet",
            description="PUT values into an A1 range",
            parameters={
                "spreadsheet_id": _spreadsheet_id_param(),
                "range": ParameterDef(
                    type="string", description="A1 notation", required=True
                ),
                "data": ParameterDef(
                    type="array",
                    description="2D array of strings",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="format_sheet_cells",
            description=(
                "Format cells (background color + horizontal/vertical "
                "alignment) — converts A1 to GridRange"
            ),
            parameters={
                "spreadsheet_id": _spreadsheet_id_param(),
                "range": ParameterDef(
                    type="string", description="A1 range", required=True
                ),
                "background_color": ParameterDef(
                    type="object",
                    description="RGB color {red, green, blue} (values 0-1)",
                ),
                "horizontal_alignment": ParameterDef(
                    type="string", description="LEFT / CENTER / RIGHT"
                ),
                "vertical_alignment": ParameterDef(
                    type="string", description="TOP / MIDDLE / BOTTOM"
                ),
            },
        ),
        ActionDefinition(
            name="format_sheet_text",
            description="Format text in cells (bold/italic/font_size/color)",
            parameters={
                "spreadsheet_id": _spreadsheet_id_param(),
                "range": ParameterDef(
                    type="string", description="A1 range", required=True
                ),
                "bold": ParameterDef(type="boolean", description="Bold"),
                "italic": ParameterDef(type="boolean", description="Italic"),
                "font_size": ParameterDef(
                    type="integer", description="Font size (pt)"
                ),
                "foreground_color": ParameterDef(
                    type="object",
                    description="Text RGB color {red, green, blue}",
                ),
            },
        ),
        # --- Slides --------------------------------------------------------
        ActionDefinition(
            name="create_google_slides",
            description="Create a blank Slides presentation (+ optional move)",
            parameters={
                "name": _name_param("Presentation"),
                "parent_folder_id": ParameterDef(
                    type="string", description="Parent folder ID"
                ),
            },
        ),
        ActionDefinition(
            name="read_google_slides",
            description=(
                "Read slide metadata + extract text + placeholder IDs from "
                "each slide"
            ),
            parameters={"presentation_id": _presentation_id_param()},
        ),
        ActionDefinition(
            name="add_slide",
            description="Add a slide with the given predefined layout",
            parameters={
                "presentation_id": _presentation_id_param(),
                "layout": ParameterDef(
                    type="string",
                    description="BLANK / TITLE / TITLE_AND_BODY / etc.",
                    default="BLANK",
                ),
                "insertion_index": ParameterDef(
                    type="integer", description="Insert position (0-based)"
                ),
            },
        ),
        ActionDefinition(
            name="update_slide_content",
            description=(
                "Replace text in a slide placeholder (deleteText ALL + "
                "insertText 0)"
            ),
            parameters={
                "presentation_id": _presentation_id_param(),
                "slide_id": ParameterDef(
                    type="string", description="Slide object ID", required=True
                ),
                "placeholder_id": ParameterDef(
                    type="string",
                    description="Placeholder element ID",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string", description="New text", required=True
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description=(
                "Connect using Google OAuth2 (recommended). Provides secure "
                "access to Drive, Docs, Sheets, and Slides."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_DRIVE_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google OAuth2 Client ID from Cloud Console",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="123456789-xxxxxxxxxxxxxxxx.apps.googleusercontent.com",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_DRIVE_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google OAuth2 Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                scopes=[
                    "https://www.googleapis.com/auth/drive",
                    "https://www.googleapis.com/auth/drive.file",
                    "https://www.googleapis.com/auth/documents",
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/presentations",
                ],
                token_auth_method="body",
            ),
            test_endpoint=_test_endpoint("access_token"),
        ),
        BearerTokenAuthSchema(
            display_name="Service Account / Access Token",
            description=(
                "Use a pre-generated access token or service account "
                "credentials"
            ),
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_ACCESS_TOKEN",
                    display_name="Access Token",
                    description="A valid Google OAuth2 access token",
                    required=True,
                    sensitive=True,
                ),
            ],
            test_endpoint=_test_endpoint("bearer_token"),
        ),
    ],
)

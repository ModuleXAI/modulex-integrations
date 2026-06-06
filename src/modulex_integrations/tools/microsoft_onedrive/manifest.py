"""Microsoft OneDrive integration manifest."""
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
    name="microsoft_onedrive",
    display_name="Microsoft OneDrive",
    description=(
        "Access and manage files in Microsoft OneDrive: search, list, upload, "
        "download, create folders, and create sharing links via the Microsoft "
        "Graph API."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:microsoft-onedrive",
    app_url="https://onedrive.live.com",
    categories=["Cloud Infrastructure", "file-storage", "productivity"],
    actions=[
        ActionDefinition(
            name="create_folder",
            description=(
                "Create a new folder in a drive. See "
                "https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_post_children"
            ),
            parameters={
                "folder_name": ParameterDef(
                    type="string",
                    description="The name of the new folder to be created (e.g. 'New Folder').",
                    required=True,
                ),
                "parent_folder_id": ParameterDef(
                    type="string",
                    description=(
                        "The ID of the folder which the new folder should be created within. "
                        "Omit to create the folder at the drive root."
                    ),
                    required=False,
                ),
                "shared_folder_reference": ParameterDef(
                    type="string",
                    description=(
                        "Reference of the shared folder which the new folder should be created in "
                        "(e.g. '/drives/{driveId}/items/{folderId}/children'). Mutually exclusive "
                        "with parent_folder_id."
                    ),
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="create_link",
            description=(
                "Create a sharing link for a DriveItem. See "
                "https://docs.microsoft.com/en-us/graph/api/driveitem-createlink"
            ),
            parameters={
                "drive_item_id": ParameterDef(
                    type="string",
                    description="The ID of the DriveItem to create a sharing link for.",
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description="The type of sharing link to create. One of: view, edit, embed.",
                    required=True,
                ),
                "scope": ParameterDef(
                    type="string",
                    description="The scope of link to create. One of: anonymous, organization.",
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="download_file",
            description=(
                "Download a file stored in OneDrive. Returns the file content as base64-encoded "
                "data plus the saved /tmp path. See "
                "https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_get_content"
            ),
            parameters={
                "file_id": ParameterDef(
                    type="string",
                    description="The ID of the file to download. Provide either file_id or file_path.",
                    required=False,
                ),
                "file_path": ParameterDef(
                    type="string",
                    description=(
                        "The path to the file from the root folder "
                        "(e.g. 'Documents/My Subfolder/File 1.docx'). Provide either file_id or file_path."
                    ),
                    required=False,
                ),
                "new_file_name": ParameterDef(
                    type="string",
                    description=(
                        "The file name to save the downloaded content as, under /tmp. "
                        "Include the file extension."
                    ),
                    required=True,
                ),
                "convert_to_format": ParameterDef(
                    type="string",
                    description="Optional format to convert the file to. One of: pdf, html.",
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="find_file_by_name",
            description=(
                "Search for a file or folder by name. See "
                "https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_search"
            ),
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="The name of the file or folder to search for.",
                    required=True,
                ),
                "exclude_folders": ParameterDef(
                    type="boolean",
                    description="Set to true to return only files in the response. Defaults to false.",
                    required=False,
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_excel_table",
            description=(
                "Retrieve a table from an Excel spreadsheet stored in OneDrive. The table must "
                "exist within the Excel spreadsheet. See "
                "https://learn.microsoft.com/en-us/graph/api/table-range"
            ),
            parameters={
                "item_id": ParameterDef(
                    type="string",
                    description="The ID of the Excel (.xlsx) file in OneDrive.",
                    required=True,
                ),
                "table_name": ParameterDef(
                    type="string",
                    description="Name of the table as set in the Table Design tab of Excel.",
                    required=True,
                ),
                "remove_headers": ParameterDef(
                    type="boolean",
                    description=(
                        "By default, the headers are included as the first row. Set true to remove them."
                    ),
                    required=False,
                    default=False,
                ),
                "number_of_rows": ParameterDef(
                    type="integer",
                    description="Number of rows to return. Leave at 0 to return all rows.",
                    required=False,
                    default=0,
                ),
            },
        ),
        ActionDefinition(
            name="get_file_by_id",
            description=(
                "Retrieve a file by ID. See "
                "https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_get"
            ),
            parameters={
                "file_id": ParameterDef(
                    type="string",
                    description="The ID of the DriveItem to retrieve.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_files_in_folder",
            description=(
                "Retrieve a list of the files and/or folders directly within a folder. See "
                "https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_list_children"
            ),
            parameters={
                "folder_id": ParameterDef(
                    type="string",
                    description="The ID of the folder whose children should be listed.",
                    required=True,
                ),
                "exclude_folders": ParameterDef(
                    type="boolean",
                    description="Set true to return only files (omit subfolders).",
                    required=False,
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="list_my_drives",
            description=(
                "Get the signed-in user's drives. Returns a list of all the drives the user has "
                "access to, including the personal OneDrive. See "
                "https://learn.microsoft.com/en-us/graph/api/drive-list"
            ),
            parameters={},
        ),
        ActionDefinition(
            name="list_shared_folder_reference_options",
            description=(
                "Retrieve available shared folder references. Useful as input to the "
                "shared_folder_reference parameter of create_folder."
            ),
            parameters={},
        ),
        ActionDefinition(
            name="search_files",
            description=(
                "Search for files and folders in Microsoft OneDrive. See "
                "https://learn.microsoft.com/en-us/graph/api/driveitem-search"
            ),
            parameters={
                "q": ParameterDef(
                    type="string",
                    description=(
                        "The query text used to search for items. Values may be matched across "
                        "several fields including filename, metadata, and file content."
                    ),
                    required=True,
                ),
                "exclude_folders": ParameterDef(
                    type="boolean",
                    description="Set true to filter out folders from the results.",
                    required=False,
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="upload_file",
            description=(
                "Upload a file to OneDrive by providing a publicly-accessible source URL. The "
                "file is streamed from the URL into OneDrive under the given folder. See "
                "https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_put_content"
            ),
            parameters={
                "upload_folder_id": ParameterDef(
                    type="string",
                    description="The ID of the folder where you want to upload the file.",
                    required=True,
                ),
                "file_url": ParameterDef(
                    type="string",
                    description=(
                        "Publicly accessible URL of the file to upload. The integration downloads "
                        "the content and re-uploads it to OneDrive."
                    ),
                    required=True,
                ),
                "filename": ParameterDef(
                    type="string",
                    description="Name of the new uploaded file (including extension).",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Microsoft (Azure Entra) OAuth",
            setup_instructions=[
                "Go to https://entra.microsoft.com -> App registrations -> New registration",
                (
                    "Set supported account types according to your needs (commonly "
                    "'Accounts in any organizational directory and personal Microsoft accounts')"
                ),
                "Add redirect URI (Web): https://api.modulex.dev/credentials/oauth2/callback",
                (
                    "Under API permissions, add Microsoft Graph delegated permissions: "
                    "Files.ReadWrite.All, Sites.ReadWrite.All, User.Read, offline_access"
                ),
                "Create a client secret under Certificates & secrets",
                "Copy Application (client) ID and the client secret value",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="MICROSOFT_ONEDRIVE_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Microsoft (Azure Entra) App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="00000000-0000-0000-0000-000000000000",
                    about_url="https://entra.microsoft.com",
                ),
                EnvVar(
                    name="MICROSOFT_ONEDRIVE_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Microsoft (Azure Entra) App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://entra.microsoft.com",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
                scopes=[
                    "Files.ReadWrite.All",
                    "Sites.ReadWrite.All",
                    "User.Read",
                    "offline_access",
                ],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://graph.microsoft.com/v1.0/me",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["id"],
                ),
                cost_level="free",
                description="Validates the access token by fetching the authenticated user's profile",
            ),
        ),
    ],
)

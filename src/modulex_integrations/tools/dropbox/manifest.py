"""Dropbox integration manifest."""
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
    name="dropbox",
    display_name="Dropbox",
    description="Cloud file storage, sharing, and collaboration platform",
    version="1.0.0",
    author="ModuleX",
    logo="logos:dropbox",
    app_url="https://www.dropbox.com",
    categories=[
        "Cloud Infrastructure",
        "Productivity & Collaboration",
        "file-storage",
        "cloud-storage",
    ],
    actions=[
        ActionDefinition(
            name="create_folder",
            description="Create a new folder in the user's Dropbox",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="The new folder name",
                    required=True,
                ),
                "path": ParameterDef(
                    type="string",
                    description="Parent folder path where the new folder will be created (empty string for root)",
                    default="",
                ),
                "autorename": ParameterDef(
                    type="boolean",
                    description="If true, Dropbox will autorename the folder if there is a conflict",
                    default=True,
                ),
            },
        ),
        ActionDefinition(
            name="search_files_folders",
            description="Search for files and folders by name or content",
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="The search query string",
                    required=True,
                ),
                "path": ParameterDef(
                    type="string",
                    description="Folder path to restrict the search to (empty string for all)",
                    default="",
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="Sort order: relevance, last_modified_time",
                ),
                "file_status": ParameterDef(
                    type="string",
                    description="Restrict to file status: active, deleted",
                ),
                "filename_only": ParameterDef(
                    type="boolean",
                    description="If true, restricts search to filenames only",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return (defaults to 100)",
                ),
            },
        ),
        ActionDefinition(
            name="list_file_folders_in_a_folder",
            description="List all files and subfolders in a specified folder",
            parameters={
                "path": ParameterDef(
                    type="string",
                    description="The folder path to list contents of (empty string for root)",
                    required=True,
                ),
                "recursive": ParameterDef(
                    type="boolean",
                    description="If true, list contents of all subfolders recursively",
                    default=True,
                ),
                "include_deleted": ParameterDef(
                    type="boolean",
                    description="If true, include files and folders that were deleted",
                    default=False,
                ),
                "include_mounted_folders": ParameterDef(
                    type="boolean",
                    description="If true, include entries under mounted folders (app, shared, team)",
                    default=False,
                ),
                "include_non_downloadable_files": ParameterDef(
                    type="boolean",
                    description="If true, include non-downloadable files like Google Docs",
                    default=True,
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of entries to return (defaults to 100)",
                ),
            },
        ),
        ActionDefinition(
            name="delete_file_folder",
            description="Permanently delete a file or folder from Dropbox",
            parameters={
                "path": ParameterDef(
                    type="string",
                    description="Path of the file or folder to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="move_file_folder",
            description="Move a file or folder to a different location in Dropbox",
            parameters={
                "path_from": ParameterDef(
                    type="string",
                    description="Path of the file or folder to move",
                    required=True,
                ),
                "path_to": ParameterDef(
                    type="string",
                    description="Destination folder path (file name is appended automatically)",
                    required=True,
                ),
                "autorename": ParameterDef(
                    type="boolean",
                    description="If true, autorename to avoid conflicts",
                    default=False,
                ),
                "allow_ownership_transfer": ParameterDef(
                    type="boolean",
                    description="Allow moves that result in ownership transfer",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="rename_file_folder",
            description="Rename a file or folder in Dropbox",
            parameters={
                "path_from": ParameterDef(
                    type="string",
                    description="Path of the file or folder to rename",
                    required=True,
                ),
                "new_name": ParameterDef(
                    type="string",
                    description="The new name (include file extension for files)",
                    required=True,
                ),
                "autorename": ParameterDef(
                    type="boolean",
                    description="If true, autorename to avoid conflicts",
                    default=False,
                ),
                "allow_ownership_transfer": ParameterDef(
                    type="boolean",
                    description="Allow renames that result in ownership transfer",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="create_a_text_file",
            description="Create a new text file from plain text content",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="File name including extension (e.g. notes.txt)",
                    required=True,
                ),
                "path": ParameterDef(
                    type="string",
                    description="Folder path where the file will be created (empty string for root)",
                    default="",
                ),
                "content": ParameterDef(
                    type="string",
                    description="The text content of the new file",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_or_append_to_a_text_file",
            description="Append a line to an existing text file, or create the file if it does not exist",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="File name including extension",
                    required=True,
                ),
                "path": ParameterDef(
                    type="string",
                    description="Folder path (empty string for root)",
                    default="",
                ),
                "content": ParameterDef(
                    type="string",
                    description="The text content to write or append",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_update_share_link",
            description="Create or update a public share link for a file or folder",
            parameters={
                "path": ParameterDef(
                    type="string",
                    description="Path of the file or folder to share",
                    required=True,
                ),
                "require_password": ParameterDef(
                    type="boolean",
                    description="Enable password protection on the shared link",
                    default=False,
                ),
                "link_password": ParameterDef(
                    type="string",
                    description="Password for the shared link (if require_password is true)",
                ),
                "expires": ParameterDef(
                    type="string",
                    description="Expiration timestamp in ISO 8601 format (e.g. 2024-07-18T20:00:00Z)",
                ),
                "audience": ParameterDef(
                    type="string",
                    description="Link audience: public, team, no_one",
                ),
            },
        ),
        ActionDefinition(
            name="list_shared_links",
            description="List shared links for a file or folder path",
            parameters={
                "path": ParameterDef(
                    type="string",
                    description="File or folder path to list shared links for (optional, lists all if empty)",
                ),
            },
        ),
        ActionDefinition(
            name="get_shared_link_metadata",
            description="Get metadata for a shared link URL",
            parameters={
                "shared_link_url": ParameterDef(
                    type="string",
                    description="The URL of the shared link",
                    required=True,
                ),
                "link_password": ParameterDef(
                    type="string",
                    description="Password if the shared link is password-protected",
                ),
            },
        ),
        ActionDefinition(
            name="list_file_revisions",
            description="List revision history for a file",
            parameters={
                "path": ParameterDef(
                    type="string",
                    description="The file path to list revisions for",
                    required=True,
                ),
                "mode": ParameterDef(
                    type="string",
                    description="Revision mode: path (default, revisions at same path) or id (revisions with same file id)",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of revision entries to return",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Dropbox OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="DROPBOX_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Dropbox OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxxxxx",
                    about_url="https://www.dropbox.com/developers/apps",
                ),
                EnvVar(
                    name="DROPBOX_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Dropbox OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxxxxx",
                    about_url="https://www.dropbox.com/developers/apps",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://www.dropbox.com/oauth2/authorize",
                token_url="https://api.dropboxapi.com/oauth2/token",
                scopes=[
                    "files.metadata.read",
                    "files.metadata.write",
                    "files.content.read",
                    "files.content.write",
                    "sharing.read",
                    "sharing.write",
                    "account_info.read",
                ],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.dropboxapi.com/2/users/get_current_account",
                method="POST",
                headers={
                    "Authorization": "Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                body={},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["account_id"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching the authenticated user account",
            ),
        ),
    ],
)

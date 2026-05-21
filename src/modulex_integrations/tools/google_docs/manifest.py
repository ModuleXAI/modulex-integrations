"""Google Docs integration manifest."""
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
    name="google_docs",
    display_name="Google Docs",
    description="Create, read, and edit Google Docs documents via the Google Docs API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:google_docs",
    app_url="https://docs.google.com",
    categories=["Productivity & Collaboration", "google-workspace", "documents"],
    actions=[
        ActionDefinition(
            name="append_image",
            description="Append an image to the end of a Google Docs document",
            parameters={
                "doc_id": ParameterDef(
                    type="string",
                    description="The ID of the document to append the image to",
                    required=True,
                ),
                "image_uri": ParameterDef(
                    type="string",
                    description="The URL of the image to insert into the document",
                    required=True,
                ),
                "append_at_beginning": ParameterDef(
                    type="boolean",
                    description="Whether to append at the beginning (true) or end (false) of the document",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="append_text",
            description="Append text to an existing Google Docs document",
            parameters={
                "doc_id": ParameterDef(
                    type="string",
                    description="The ID of the document to append text to",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="The text to append to the document",
                    required=True,
                ),
                "append_at_beginning": ParameterDef(
                    type="boolean",
                    description="Whether to append at the beginning (true) or end (false) of the document",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="create_document",
            description="Create a new Google Docs document with optional text content",
            parameters={
                "title": ParameterDef(
                    type="string",
                    description="Title of the new document",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Text content to insert into the document",
                ),
                "folder_id": ParameterDef(
                    type="string",
                    description="ID of the Google Drive folder to place the document in",
                ),
            },
        ),
        ActionDefinition(
            name="create_document_from_template",
            description="Create a new Google Docs document from a template with placeholder replacement",
            parameters={
                "template_id": ParameterDef(
                    type="string",
                    description="The ID of the template document containing {{placeholder}} variables",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Name for the new document",
                    required=True,
                ),
                "replace_values": ParameterDef(
                    type="object",
                    description="Key-value pairs to replace placeholders in the template (keys without curly braces)",
                    required=True,
                ),
                "folder_id": ParameterDef(
                    type="string",
                    description="ID of the Google Drive folder for the new document",
                ),
            },
        ),
        ActionDefinition(
            name="find_document",
            description="Search for Google Docs documents by name or query using Google Drive search",
            parameters={
                "name_search_term": ParameterDef(
                    type="string",
                    description="Search for a document by name (equivalent to 'name contains' query)",
                ),
                "search_query": ParameterDef(
                    type="string",
                    description="Custom Google Drive search query. If specified, name_search_term is ignored",
                ),
            },
        ),
        ActionDefinition(
            name="get_document",
            description="Get the contents of a Google Docs document",
            parameters={
                "doc_id": ParameterDef(
                    type="string",
                    description="The ID of the document to retrieve",
                    required=True,
                ),
                "include_tabs_content": ParameterDef(
                    type="boolean",
                    description="Whether to populate the tabs field instead of the body field",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_tab_content",
            description="Get the content of specific tabs in a Google Docs document",
            parameters={
                "doc_id": ParameterDef(
                    type="string",
                    description="The ID of the document",
                    required=True,
                ),
                "tab_ids": ParameterDef(
                    type="array",
                    description="List of tab IDs to retrieve content for (element type: string)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="insert_page_break",
            description="Insert a page break into a Google Docs document at a specified index",
            parameters={
                "doc_id": ParameterDef(
                    type="string",
                    description="The ID of the document",
                    required=True,
                ),
                "index": ParameterDef(
                    type="integer",
                    description="The index position to insert the page break at",
                    default=1,
                ),
                "tab_id": ParameterDef(
                    type="string",
                    description="The tab ID to insert the page break into",
                ),
            },
        ),
        ActionDefinition(
            name="insert_table",
            description="Insert a table into a Google Docs document at a specified index",
            parameters={
                "doc_id": ParameterDef(
                    type="string",
                    description="The ID of the document",
                    required=True,
                ),
                "rows": ParameterDef(
                    type="integer",
                    description="The number of rows in the table",
                    required=True,
                ),
                "columns": ParameterDef(
                    type="integer",
                    description="The number of columns in the table",
                    required=True,
                ),
                "index": ParameterDef(
                    type="integer",
                    description="The index position to insert the table at",
                    default=1,
                ),
                "tab_id": ParameterDef(
                    type="string",
                    description="The tab ID to insert the table into",
                ),
            },
        ),
        ActionDefinition(
            name="insert_text",
            description="Insert text into a Google Docs document at a specified index",
            parameters={
                "doc_id": ParameterDef(
                    type="string",
                    description="The ID of the document",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="The text to insert",
                    required=True,
                ),
                "index": ParameterDef(
                    type="integer",
                    description="The index position to insert the text at",
                    default=1,
                ),
                "tab_id": ParameterDef(
                    type="string",
                    description="The tab ID to insert the text into",
                ),
            },
        ),
        ActionDefinition(
            name="replace_image",
            description="Replace an existing image in a Google Docs document with a new one",
            parameters={
                "doc_id": ParameterDef(
                    type="string",
                    description="The ID of the document",
                    required=True,
                ),
                "image_id": ParameterDef(
                    type="string",
                    description="The ID of the image to be replaced (from the document's inlineObjects)",
                    required=True,
                ),
                "image_uri": ParameterDef(
                    type="string",
                    description="The URL of the new image to replace with",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="replace_text",
            description="Replace all instances of matched text in a Google Docs document",
            parameters={
                "doc_id": ParameterDef(
                    type="string",
                    description="The ID of the document",
                    required=True,
                ),
                "text_to_replace": ParameterDef(
                    type="string",
                    description="The text to find and replace",
                    required=True,
                ),
                "new_text": ParameterDef(
                    type="string",
                    description="The replacement text",
                    required=True,
                ),
                "match_case": ParameterDef(
                    type="boolean",
                    description="Whether the search is case-sensitive",
                    default=False,
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
                    name="GOOGLE_DOCS_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_DOCS_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                scopes=[
                    "https://www.googleapis.com/auth/documents",
                    "https://www.googleapis.com/auth/drive",
                ],
            ),
            test_endpoint=TestEndpoint(
                url="https://docs.googleapis.com/v1/documents/1",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200, 404],
                    response_fields=[],
                ),
                cost_level="free",
                description="Validates OAuth token by attempting to fetch a document",
            ),
        ),
    ],
)

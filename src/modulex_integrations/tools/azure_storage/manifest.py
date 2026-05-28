"""Azure Storage integration manifest."""
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
    name="azure_storage",
    display_name="Azure Storage",
    description="Manage blobs and containers in Microsoft Azure Blob Storage",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:azure_storage",
    app_url="https://azure.microsoft.com/en-us/products/storage/blobs",
    categories=["Cloud Infrastructure", "Storage"],
    actions=[
        ActionDefinition(
            name="create_container",
            description="Create a new container under the specified storage account",
            parameters={
                "container_name": ParameterDef(
                    type="string",
                    description="Name of the container to create (lowercase, alphanumeric and hyphens only)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_blob",
            description="Delete a specific blob from a container in Azure Storage",
            parameters={
                "container_name": ParameterDef(
                    type="string",
                    description="Name of the container holding the blob",
                    required=True,
                ),
                "blob_name": ParameterDef(
                    type="string",
                    description="Name of the blob to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_containers",
            description="List all containers in the storage account",
            parameters={},
        ),
        ActionDefinition(
            name="upload_blob",
            description="Upload content from a URL to a blob in Azure Storage",
            parameters={
                "container_name": ParameterDef(
                    type="string",
                    description="Name of the target container",
                    required=True,
                ),
                "blob_name": ParameterDef(
                    type="string",
                    description="Name for the blob in the container",
                    required=True,
                ),
                "file_url": ParameterDef(
                    type="string",
                    description="Publicly accessible URL of the file to upload",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="Microsoft OAuth2",
            description="Connect using Microsoft OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="AZURE_STORAGE_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Azure AD App Registration Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                ),
                EnvVar(
                    name="AZURE_STORAGE_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Azure AD App Registration Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="x" * 40,
                    about_url="https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                ),
                EnvVar(
                    name="AZURE_STORAGE_ACCOUNT_NAME",
                    display_name="Storage Account Name",
                    description="Azure Storage account name (appears in the blob endpoint URL)",
                    required=True,
                    sensitive=False,
                    only_for_custom=False,
                    sample_format="mystorageaccount",
                    about_url="https://portal.azure.com/#view/HubsExtension/BrowseResource/resourceType/Microsoft.Storage%2FStorageAccounts",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
                scopes=["https://storage.azure.com/user_impersonation", "offline_access"],
            ),
            test_endpoint=TestEndpoint(
                url="https://{storage_account_name}.blob.core.windows.net/?comp=list&maxresults=1",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                    "x-ms-version": "2021-12-02",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                ),
                cost_level="free",
                description="Lists containers (max 1) to validate the OAuth token",
            ),
        ),
    ],
)

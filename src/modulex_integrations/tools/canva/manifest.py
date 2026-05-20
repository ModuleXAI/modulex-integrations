"""Canva integration manifest."""
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
    name="canva",
    display_name="Canva",
    description="Design platform for creating visual content, presentations, and documents",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:canva",
    app_url="https://www.canva.com",
    categories=["Design & Creative Tools", "Productivity & Collaboration"],
    actions=[
        ActionDefinition(
            name="create_design",
            description="Creates a new Canva design with preset or custom dimensions",
            parameters={
                "design_type": ParameterDef(
                    type="string",
                    description="The desired design type: 'preset' (provide design_type_name) or 'custom' (provide width and height)",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The name of the design",
                ),
                "asset_id": ParameterDef(
                    type="string",
                    description="The ID of the asset to add to the new design",
                ),
                "design_type_name": ParameterDef(
                    type="string",
                    description="The preset design type name: 'doc', 'whiteboard', or 'presentation'. Only applicable when design_type is 'preset'",
                ),
                "width": ParameterDef(
                    type="integer",
                    description="Width in pixels (40-8000). Only applicable when design_type is 'custom'",
                ),
                "height": ParameterDef(
                    type="integer",
                    description="Height in pixels (40-8000). Only applicable when design_type is 'custom'",
                ),
            },
        ),
        ActionDefinition(
            name="create_design_import_job",
            description="Starts a job to import an external file as a new Canva design",
            parameters={
                "title": ParameterDef(
                    type="string",
                    description="The name for the imported design",
                    required=True,
                ),
                "file_url": ParameterDef(
                    type="string",
                    description="URL of the file to import into Canva",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="export_design",
            description="Starts a job to export a Canva design to a file format",
            parameters={
                "design_id": ParameterDef(
                    type="string",
                    description="The ID of the design to export",
                    required=True,
                ),
                "format_type": ParameterDef(
                    type="string",
                    description="Export format: 'pdf', 'jpg', 'png', 'pptx', 'gif', or 'mp4'",
                    required=True,
                ),
                "pages": ParameterDef(
                    type="array",
                    description="Array of page numbers (integers) to export. First page is 1. If omitted, all pages are exported",
                ),
                "quality": ParameterDef(
                    type="integer",
                    description="JPG quality 1-100. Only applicable for 'jpg' format",
                ),
                "mp4_quality": ParameterDef(
                    type="string",
                    description="MP4 resolution: 'horizontal_480p', 'horizontal_720p', 'horizontal_1080p', 'horizontal_4k', 'vertical_480p', 'vertical_720p', 'vertical_1080p', 'vertical_4k'",
                ),
                "size": ParameterDef(
                    type="string",
                    description="PDF paper size: 'a4', 'a3', 'letter', or 'legal'",
                ),
                "lossless": ParameterDef(
                    type="boolean",
                    description="Use lossless compression for PNG exports",
                ),
                "as_single_image": ParameterDef(
                    type="boolean",
                    description="Merge multi-page designs into a single PNG image",
                ),
                "export_quality": ParameterDef(
                    type="string",
                    description="Export quality tier: 'regular' or 'pro'. Pro may fail for premium elements",
                ),
                "height": ParameterDef(
                    type="integer",
                    description="Export height in pixels. Applicable for jpg, png, gif formats",
                ),
                "width": ParameterDef(
                    type="integer",
                    description="Export width in pixels. Applicable for jpg, png, gif formats",
                ),
            },
        ),
        ActionDefinition(
            name="list_designs",
            description="Lists designs owned by or shared with the authenticated Canva user",
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Search keyword or phrase (max 255 characters)",
                ),
                "continuation": ParameterDef(
                    type="string",
                    description="Pagination cursor from a previous response to get the next page",
                ),
                "ownership": ParameterDef(
                    type="string",
                    description="Filter by ownership: 'any', 'owned', or 'shared'",
                    default="any",
                ),
                "sort_by": ParameterDef(
                    type="string",
                    description="Sort order: 'relevance', 'modified_descending', 'modified_ascending', 'title_descending', 'title_ascending'",
                    default="relevance",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum designs to return per request (1-100)",
                    default=25,
                ),
            },
        ),
        ActionDefinition(
            name="upload_asset",
            description="Uploads an asset to Canva from a URL",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="The asset's name",
                    required=True,
                ),
                "file_url": ParameterDef(
                    type="string",
                    description="URL of the file to upload as an asset to Canva",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Canva OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="CANVA_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Canva Connect API OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://www.canva.dev/docs/connect/quick-start/",
                ),
                EnvVar(
                    name="CANVA_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Canva Connect API OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://www.canva.dev/docs/connect/quick-start/",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://www.canva.com/api/oauth/authorize",
                token_url="https://api.canva.com/rest/v1/oauth/token",
                scopes=[
                    "design:content:read",
                    "design:content:write",
                    "design:meta:read",
                    "asset:read",
                    "asset:write",
                ],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.canva.com/rest/v1/users/me",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["team_user"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching the authenticated user profile",
            ),
        ),
    ],
)

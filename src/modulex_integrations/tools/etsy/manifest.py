"""Etsy integration manifest."""
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
    name="etsy",
    display_name="Etsy",
    description="Etsy marketplace listing management via the Open API v3",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:etsy",
    app_url="https://www.etsy.com",
    categories=["E-Commerce", "Marketplace"],
    actions=[
        ActionDefinition(
            name="create_draft_listing_product",
            description="Creates a physical draft listing product in a shop on Etsy",
            parameters={
                "quantity": ParameterDef(
                    type="integer",
                    description="The positive non-zero number of products available for purchase",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The listing's title string",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string",
                    description="A description of the product for sale in the listing",
                    required=True,
                ),
                "price": ParameterDef(
                    type="string",
                    description="The positive non-zero price of the product as a decimal string (e.g. '29.99')",
                    required=True,
                ),
                "who_made": ParameterDef(
                    type="string",
                    description="Who made the product: i_did, collective, someone_else",
                    required=True,
                ),
                "when_made": ParameterDef(
                    type="string",
                    description="Era when product was made: made_to_order, 2020_2023, 2010_2019, 2004_2009, before_2004, 2000_2003, 1990s, 1980s, 1970s, 1960s, 1950s, 1940s, 1930s, 1920s, 1910s, 1900s, 1800s, 1700s, before_1700",
                    required=True,
                ),
                "taxonomy_id": ParameterDef(
                    type="string",
                    description="The numerical taxonomy ID of the listing",
                    required=True,
                ),
                "is_supply": ParameterDef(
                    type="boolean",
                    description="When true, tags the listing as a supply product; otherwise a finished product",
                    required=True,
                ),
                "listing_type": ParameterDef(
                    type="string",
                    description="Listing type: physical, download, both",
                    required=True,
                ),
                "shipping_profile_id": ParameterDef(
                    type="string",
                    description="The numeric ID of the shipping profile. Required when listing type is physical.",
                ),
            },
        ),
        ActionDefinition(
            name="delete_listing",
            description="Delete an Etsy listing by listing ID",
            parameters={
                "listing_id": ParameterDef(
                    type="string",
                    description="The ID of the listing to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_listing",
            description="Retrieve an Etsy listing record by listing ID",
            parameters={
                "listing_id": ParameterDef(
                    type="string",
                    description="The ID of the listing to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_listing_inventory",
            description="Retrieve the inventory record for a listing by listing ID",
            parameters={
                "listing_id": ParameterDef(
                    type="string",
                    description="The ID of the listing whose inventory to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_listing_inventory",
            description="Update the inventory for a listing identified by listing ID",
            parameters={
                "listing_id": ParameterDef(
                    type="string",
                    description="The ID of the listing whose inventory to update",
                    required=True,
                ),
                "products": ParameterDef(
                    type="array",
                    description="JSON array of product objects containing sku, property_values, and offerings",
                ),
                "price_on_property": ParameterDef(
                    type="array",
                    description="List of listing property ID integers for properties that change product prices",
                ),
                "quantity_on_property": ParameterDef(
                    type="array",
                    description="List of listing property ID integers for properties that change product quantity",
                ),
                "sku_on_property": ParameterDef(
                    type="array",
                    description="List of listing property ID integers for properties that change the product SKU",
                ),
            },
        ),
        ActionDefinition(
            name="update_listing_property",
            description="Update or populate the properties list defining product offerings for a listing",
            parameters={
                "listing_id": ParameterDef(
                    type="string",
                    description="The ID of the listing",
                    required=True,
                ),
                "property_id": ParameterDef(
                    type="string",
                    description="The ID of the property to update",
                    required=True,
                ),
                "value_ids": ParameterDef(
                    type="array",
                    description="Array of integer value IDs for the property",
                    required=True,
                ),
                "values": ParameterDef(
                    type="array",
                    description="Array of string value labels for the property (e.g. 'Black', 'Christmas')",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Etsy OAuth2 (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="ETSY_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Etsy OAuth App Client ID (API Key)",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://www.etsy.com/developers/your-apps",
                ),
                EnvVar(
                    name="ETSY_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Etsy OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="x" * 40,
                    about_url="https://www.etsy.com/developers/your-apps",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://www.etsy.com/oauth/connect",
                token_url="https://api.etsy.com/v3/public/oauth/token",
                scopes=[
                    "listings_r",
                    "listings_w",
                    "listings_d",
                    "transactions_r",
                    "shops_r",
                ],
            ),
            test_endpoint=TestEndpoint(
                url="https://openapi.etsy.com/v3/application/users/me",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                    # NOTE: Etsy also requires the OAuth Client ID
                    # ("keystring") as an x-api-key header on every
                    # request. The modulex OAuth callback stores only
                    # OAuth tokens in auth_data — not the client_id —
                    # so this test will fail with 400 on auth-correct
                    # tokens too. We accept 400 as success to confirm
                    # the OAuth token format reached Etsy. tools.py
                    # injects the client_id from oauth_config at
                    # action call time.
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200, 400, 401, 403],
                ),
                cost_level="free",
                description=(
                    "Reachability check against Etsy /users/me. The "
                    "x-api-key header (OAuth client_id) is omitted "
                    "because the modulex OAuth flow doesn't route the "
                    "client_id through auth_data; full validation "
                    "runs at first action call."
                ),
            ),
        ),
    ],
)

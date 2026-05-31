"""Yelp integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="yelp",
    display_name="Yelp",
    description="Search for businesses, read reviews, and get business details via the Yelp Fusion API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:yelp",
    app_url="https://www.yelp.com",
    categories=["Local Services", "Reviews", "Business Data"],
    actions=[
        ActionDefinition(
            name="search_businesses",
            description="Search businesses matching given criteria such as location, term, categories, price, and attributes",
            parameters={
                "location": ParameterDef(
                    type="string",
                    description="Geographic area to search. Examples: 'New York City', '350 5th Ave, New York, NY 10118'. Required if latitude and longitude are not provided.",
                ),
                "latitude": ParameterDef(
                    type="string",
                    description="Latitude of the location to search from. Required if location is not provided.",
                ),
                "longitude": ParameterDef(
                    type="string",
                    description="Longitude of the location to search from. Required if location is not provided.",
                ),
                "term": ParameterDef(
                    type="string",
                    description="Search term, e.g. 'food' or 'restaurants'. May also be a business name like 'Starbucks'.",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of businesses to return. Yelp enforces a limit of 1000.",
                    default=200,
                ),
                "categories": ParameterDef(
                    type="string",
                    description="Comma-separated category aliases to filter results (e.g. 'discgolf,restaurants'). See Yelp docs for supported categories.",
                ),
                "price": ParameterDef(
                    type="string",
                    description="Comma-separated pricing levels: 1 ($), 2 ($$), 3 ($$$), 4 ($$$$). Example: '1,2'.",
                ),
                "attributes": ParameterDef(
                    type="string",
                    description="Comma-separated additional filters: hot_and_new, request_a_quote, reservation, waitlist_reservation, deals, gender_neutral_restrooms, open_to_all, wheelchair_accessible.",
                ),
            },
        ),
        ActionDefinition(
            name="get_business_details",
            description="Get detailed information about a specific business by its Yelp ID or alias",
            parameters={
                "business_id_or_alias": ParameterDef(
                    type="string",
                    description="A unique identifier for a Yelp Business. Can be a 22-character Yelp Business ID or a Yelp Business Alias.",
                    required=True,
                ),
                "device_platform": ParameterDef(
                    type="string",
                    description="Determines the platform for mobile_link. Allowed values: android, ios, mobile-generic.",
                ),
                "locale": ParameterDef(
                    type="string",
                    description="Locale code in the format {language}_{country} (e.g. en_US).",
                ),
            },
        ),
        ActionDefinition(
            name="list_business_reviews",
            description="List the reviews for a specific business",
            parameters={
                "business_id_or_alias": ParameterDef(
                    type="string",
                    description="A unique identifier for a Yelp Business. Can be a 22-character Yelp Business ID or a Yelp Business Alias.",
                    required=True,
                ),
                "locale": ParameterDef(
                    type="string",
                    description="Locale code in the format {language}_{country} (e.g. en_US).",
                ),
                "sort_by": ParameterDef(
                    type="string",
                    description="Sort order for reviews. Allowed values: yelp_sort, newest.",
                ),
            },
        ),
        ActionDefinition(
            name="search_businesses_by_phone_number",
            description="Search for businesses by phone number",
            parameters={
                "phone": ParameterDef(
                    type="string",
                    description="Phone number to search for. Must start with + and include the country code, e.g. +14159083801.",
                    required=True,
                ),
                "locale": ParameterDef(
                    type="string",
                    description="Locale code in the format {language}_{country} (e.g. en_US).",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Yelp Fusion API key",
            setup_instructions=[
                "Go to https://www.yelp.com/developers and sign in",
                "Navigate to 'Manage App' or create a new app",
                "Copy your API Key from the app settings",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="YELP_API_KEY",
                    display_name="Yelp API Key",
                    description="Your Yelp Fusion API key from yelp.com/developers",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://www.yelp.com/developers/v3/manage_app",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.yelp.com/v3/businesses/search",
                method="GET",
                headers={"Authorization": "Bearer {api_key}"},
                params={"location": "San Francisco", "limit": "1"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["businesses"],
                ),
                cost_level="free",
                description="Validates the API key by searching for one business in San Francisco",
            ),
        ),
    ],
)

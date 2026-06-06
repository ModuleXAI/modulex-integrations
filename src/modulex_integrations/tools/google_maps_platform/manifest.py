"""Google Maps Platform integration manifest."""
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
    name="google_maps_platform",
    display_name="Google Maps Platform",
    description="Search for places and retrieve place details using the Google Places API (New)",
    version="1.0.0",
    author="ModuleX",
    logo="logos:google-maps",
    app_url="https://developers.google.com/maps",
    categories=["Developer Tools & Infrastructure", "Geolocation", "Maps & Places"],
    actions=[
        ActionDefinition(
            name="search_places",
            description="Search for places based on a text query with optional filters like type, rating, price level, and location bias or restriction",
            parameters={
                "text_query": ParameterDef(
                    type="string",
                    description="The text string on which to search, for example: 'restaurant', '123 Main Street', or 'best place to visit in San Francisco'",
                    required=True,
                ),
                "included_type": ParameterDef(
                    type="string",
                    description="Restricts results to places matching the specified type from Table A (e.g. 'restaurant', 'cafe', 'hotel')",
                ),
                "include_pure_service_area_businesses": ParameterDef(
                    type="boolean",
                    description="If true, include businesses that visit or deliver to customers directly but don't have a physical location",
                ),
                "language_code": ParameterDef(
                    type="string",
                    description="BCP-47 language code for results (e.g. 'en', 'fr', 'zh-CN')",
                ),
                "location_bias": ParameterDef(
                    type="object",
                    description="Area to bias search results toward. JSON object with circle or rectangle specification",
                ),
                "location_restriction": ParameterDef(
                    type="string",
                    description="Area to restrict search results to. Results outside this area are not returned",
                ),
                "ev_options": ParameterDef(
                    type="object",
                    description="Parameters for identifying available EV charging connectors and charging rates",
                ),
                "min_rating": ParameterDef(
                    type="number",
                    description="Minimum average user rating (0.0 to 5.0 inclusive, in increments of 0.5)",
                ),
                "open_now": ParameterDef(
                    type="boolean",
                    description="If true, return only places that are currently open for business",
                ),
                "price_levels": ParameterDef(
                    type="array",
                    description="Restrict to places at certain price levels. Valid values: PRICE_LEVEL_FREE, PRICE_LEVEL_INEXPENSIVE, PRICE_LEVEL_MODERATE, PRICE_LEVEL_EXPENSIVE, PRICE_LEVEL_VERY_EXPENSIVE",
                ),
                "rank_preference": ParameterDef(
                    type="string",
                    description="How results are ranked: RELEVANCE (by search relevance) or DISTANCE (by distance)",
                ),
                "region_code": ParameterDef(
                    type="string",
                    description="Two-character CLDR region code to format and bias results",
                ),
                "strict_type_filtering": ParameterDef(
                    type="boolean",
                    description="When true and included_type is set, only return places matching the specified type",
                ),
                "simplified": ParameterDef(
                    type="boolean",
                    description="If true, return a reduced set of fields per place (id, name, type, status, rating, address, phone, website, hours, location)",
                ),
            },
        ),
        ActionDefinition(
            name="get_place_details",
            description="Retrieve detailed information for a specific place using its Place ID",
            parameters={
                "place_id": ParameterDef(
                    type="string",
                    description="A textual identifier that uniquely identifies a place, returned from the search_places action",
                    required=True,
                ),
                "simplified": ParameterDef(
                    type="boolean",
                    description="If true, return a reduced set of fields (id, name, type, status, rating, address, phone, website, hours, location)",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Google Maps API Key",
            description="Authenticate using your Google Cloud API key with Places API enabled",
            setup_instructions=[
                "Go to https://console.cloud.google.com/apis/credentials",
                "Create or select a project",
                "Enable the Places API (New) for your project",
                "Create an API key or use an existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_MAPS_PLATFORM_API_KEY",
                    display_name="Google Maps API Key",
                    description="Your Google Cloud API key with Places API (New) enabled",
                    required=True,
                    sensitive=True,
                    sample_format="AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://places.googleapis.com/v1/places:searchText",
                method="POST",
                headers={
                    "X-Goog-Api-Key": "{api_key}",
                    "Content-Type": "application/json",
                    "X-Goog-FieldMask": "places.id",
                },
                body={"textQuery": "test"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["places"],
                ),
                cost_level="minimal",
                description="Validates the API key by performing a minimal text search",
            ),
        ),
    ],
)

"""Instacart integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    IntegrationManifest,
    ModulexKeyAuthSchema,
    ParameterDef,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="instacart",
    display_name="Instacart",
    description=(
        "Create shareable recipe pages, shopping lists, and find nearby "
        "retailers on Instacart. No authentication required."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:instacart",
    app_url="https://www.instacart.com",
    categories=["Business Services", "grocery", "retail", "shopping"],
    actions=[
        ActionDefinition(
            name="create_recipe_page",
            description=(
                "Create a Recipe Page on Instacart and return a shareable URL. "
                "Users can view the recipe and add all ingredients to their cart."
            ),
            parameters={
                "title": ParameterDef(
                    type="string", description="The title of the recipe", required=True
                ),
                "ingredients": ParameterDef(
                    type="array",
                    description="List of ingredients for the recipe",
                    required=True,
                ),
                "instructions": ParameterDef(
                    type="string", description="Recipe instructions/directions"
                ),
                "servings": ParameterDef(
                    type="integer", description="Number of servings"
                ),
                "image_url": ParameterDef(
                    type="string", description="URL to recipe image"
                ),
                "source_url": ParameterDef(
                    type="string", description="Original recipe source URL"
                ),
                "partner_id": ParameterDef(
                    type="string", description="Partner ID for affiliate tracking"
                ),
            },
        ),
        ActionDefinition(
            name="create_shopping_list_page",
            description=(
                "Create a Shopping List Page on Instacart and return a shareable URL. "
                "Users can view the list and add all items to their cart."
            ),
            parameters={
                "title": ParameterDef(
                    type="string",
                    description="The title of the shopping list",
                    required=True,
                ),
                "items": ParameterDef(
                    type="array",
                    description="List of items to add to the shopping list",
                    required=True,
                ),
                "partner_id": ParameterDef(
                    type="string", description="Partner ID for affiliate tracking"
                ),
            },
        ),
        ActionDefinition(
            name="get_nearby_retailers",
            description=(
                "Get nearby retailers available on Instacart by postal code. "
                "Returns stores that deliver to the specified area."
            ),
            parameters={
                "postal_code": ParameterDef(
                    type="string",
                    description="Postal/ZIP code to search near",
                    required=True,
                ),
                "country_code": ParameterDef(
                    type="string",
                    description="Country code (e.g., 'US', 'CA')",
                    default="US",
                ),
            },
        ),
    ],
    auth_schemas=[
        ModulexKeyAuthSchema(
            display_name="ModuleX Managed",
            description=(
                "This integration uses Instacart's public APIs. No API key is "
                "required for requests."
            ),
            setup_environment_variables=[],
            # test_endpoint omitted — no credential to validate (public API).
        ),
    ],
)

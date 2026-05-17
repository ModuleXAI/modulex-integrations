"""Monday.com integration manifest."""
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
    name="monday",
    display_name="Monday.com",
    description="Monday.com work management platform for boards, items, columns, and updates via the GraphQL API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:monday-themed",
    app_url="https://monday.com",
    categories=["Productivity & Collaboration", "Project Management"],
    actions=[
        ActionDefinition(
            name="create_board",
            description="Creates a new board",
            parameters={
                "board_name": ParameterDef(
                    type="string",
                    description="The new board's name",
                    required=True,
                ),
                "board_kind": ParameterDef(
                    type="string",
                    description="The new board's kind: public, private, or share",
                    required=True,
                ),
                "workspace_id": ParameterDef(
                    type="integer",
                    description="Workspace ID to create the board in. If not specified, the Main Workspace is used",
                ),
                "folder_id": ParameterDef(
                    type="integer",
                    description="Folder ID to create the board in",
                ),
                "template_id": ParameterDef(
                    type="integer",
                    description="Template board ID to use for the new board",
                ),
            },
        ),
        ActionDefinition(
            name="create_column",
            description="Creates a column in a board",
            parameters={
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board to create the column in",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The title of the new column",
                    required=True,
                ),
                "column_type": ParameterDef(
                    type="string",
                    description="The type of column: auto_number, checkbox, country, color_picker, creation_log, date, dependency, dropdown, email, file, hour, item_id, last_updated, link, location, long_text, numbers, people, phone, progress, rating, status, team, tags, text, timeline, time_tracking, vote, week, world_clock",
                    required=True,
                ),
                "defaults": ParameterDef(
                    type="string",
                    description="Custom labels JSON for status/dropdown columns, e.g. {\"1\": \"Technology\", \"2\": \"Marketing\"}",
                ),
                "description": ParameterDef(
                    type="string",
                    description="Description of the new column",
                ),
            },
        ),
        ActionDefinition(
            name="create_group",
            description="Creates a new group in a specific board",
            parameters={
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board to create the group in",
                    required=True,
                ),
                "group_name": ParameterDef(
                    type="string",
                    description="The name of the new group",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_item",
            description="Creates an item in a board",
            parameters={
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board to create the item in",
                    required=True,
                ),
                "item_name": ParameterDef(
                    type="string",
                    description="The new item's name",
                    required=True,
                ),
                "group_id": ParameterDef(
                    type="string",
                    description="Group ID to create the item in",
                ),
                "create_labels": ParameterDef(
                    type="boolean",
                    description="Create Status/Dropdown labels if missing (requires permission to change board structure)",
                ),
                "column_values": ParameterDef(
                    type="string",
                    description="JSON string of column values for the new item. See Monday.com Column Type Reference for format details",
                ),
            },
        ),
        ActionDefinition(
            name="create_subitem",
            description="Creates a subitem under a parent item",
            parameters={
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board containing the parent item",
                    required=True,
                ),
                "parent_item_id": ParameterDef(
                    type="string",
                    description="The ID of the parent item to create the subitem under",
                    required=True,
                ),
                "item_name": ParameterDef(
                    type="string",
                    description="The new subitem's name",
                    required=True,
                ),
                "column_values": ParameterDef(
                    type="string",
                    description="JSON string of column values for the new subitem",
                ),
            },
        ),
        ActionDefinition(
            name="create_update",
            description="Creates a new update (comment) on an item",
            parameters={
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board containing the item",
                    required=True,
                ),
                "item_id": ParameterDef(
                    type="string",
                    description="The ID of the item to add the update to",
                    required=True,
                ),
                "update_body": ParameterDef(
                    type="string",
                    description="The update text content",
                    required=True,
                ),
                "parent_id": ParameterDef(
                    type="string",
                    description="The ID of a parent update to reply to",
                ),
            },
        ),
        ActionDefinition(
            name="get_board_items_page",
            description="Retrieves items from a board with optional filtering",
            parameters={
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board to retrieve items from",
                    required=True,
                ),
                "query_params": ParameterDef(
                    type="string",
                    description="JSON object with filter/sort parameters in ItemsQuery format",
                ),
                "max_pages": ParameterDef(
                    type="integer",
                    description="Maximum number of pages to fetch (default 50)",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="get_column_values",
            description="Returns values of specific columns for a board item",
            parameters={
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board",
                    required=True,
                ),
                "item_id": ParameterDef(
                    type="string",
                    description="The ID of the item to retrieve column values from",
                    required=True,
                ),
                "column_ids": ParameterDef(
                    type="array",
                    description="List of column IDs to retrieve. If empty, returns all columns. Element type: string",
                ),
            },
        ),
        ActionDefinition(
            name="get_items_by_column_value",
            description="Searches a column for items matching a specific value",
            parameters={
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board to search in",
                    required=True,
                ),
                "column_id": ParameterDef(
                    type="string",
                    description="The ID of the column to search",
                    required=True,
                ),
                "value": ParameterDef(
                    type="string",
                    description="The value to search for in the specified column",
                    required=True,
                ),
                "max_pages": ParameterDef(
                    type="integer",
                    description="Maximum number of pages to fetch (default 50)",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="list_boards",
            description="Lists boards with optional filters for kind, state, and workspace",
            parameters={
                "ids": ParameterDef(
                    type="array",
                    description="Filter to specific board IDs. Element type: string",
                ),
                "workspace_ids": ParameterDef(
                    type="array",
                    description="Filter to boards in specific workspace IDs. Element type: integer",
                ),
                "board_kind": ParameterDef(
                    type="string",
                    description="Filter by board kind: public, private, or share",
                ),
                "state": ParameterDef(
                    type="string",
                    description="Filter by state: active, archived, deleted, or all",
                    default="all",
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="Sort by: created_at or used_at",
                    default="created_at",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of boards to return per page",
                    default=25,
                ),
                "page": ParameterDef(
                    type="integer",
                    description="Page number to return",
                    default=1,
                ),
            },
        ),
        ActionDefinition(
            name="list_workspaces",
            description="Retrieves available workspaces with their IDs and names",
            parameters={},
        ),
        ActionDefinition(
            name="update_column_values",
            description="Updates multiple column values for an item",
            parameters={
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board containing the item",
                    required=True,
                ),
                "item_id": ParameterDef(
                    type="string",
                    description="The ID of the item to update",
                    required=True,
                ),
                "column_values": ParameterDef(
                    type="string",
                    description="JSON string of column values to update. Keys are column IDs, values are new values per Column Types Reference",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_item_name",
            description="Updates an item's name",
            parameters={
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board containing the item",
                    required=True,
                ),
                "item_id": ParameterDef(
                    type="string",
                    description="The ID of the item to rename",
                    required=True,
                ),
                "item_name": ParameterDef(
                    type="string",
                    description="The new item name",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Monday.com API token",
            setup_instructions=[
                "Sign in to your Monday.com account",
                "Click your avatar (bottom left) and select 'Developers'",
                "Go to 'My Access Tokens' section",
                "Copy your personal API token or generate a new one",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="MONDAY_API_KEY",
                    display_name="Monday.com API Token",
                    description="Your personal API token from Monday.com developer settings",
                    required=True,
                    sensitive=True,
                    sample_format="eyJhbGciOiJIUzI1NiJ9...",
                    about_url="https://developer.monday.com/api-reference/docs/authentication",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.monday.com/v2",
                method="POST",
                headers={
                    "Authorization": "{api_key}",
                    "Content-Type": "application/json",
                },
                body={"query": "{ me { id name } }"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data"],
                ),
                cost_level="free",
                description="Validates the API token by querying the current user",
            ),
        ),
    ],
)

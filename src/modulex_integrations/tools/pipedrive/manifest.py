"""Pipedrive integration manifest."""
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
    name="pipedrive",
    display_name="Pipedrive",
    description="Sales CRM and pipeline management platform for tracking deals, contacts, activities, and leads.",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:pipedrive-themed",
    app_url="https://www.pipedrive.com",
    categories=["CRM", "Sales"],
    actions=[
        ActionDefinition(
            name="add_activity",
            description="Add a new activity in Pipedrive",
            parameters={
                "subject": ParameterDef(
                    type="string",
                    description="Subject of the activity",
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description="Type of the activity (e.g. call, meeting, task, deadline, email, lunch). Must match an ActivityType key_string in Pipedrive.",
                    required=True,
                ),
                "owner_id": ParameterDef(
                    type="integer",
                    description="ID of the user whom the activity will be assigned to. If omitted, assigned to the authorized user.",
                ),
                "deal_id": ParameterDef(
                    type="string",
                    description="ID of the deal this activity will be associated with",
                ),
                "lead_id": ParameterDef(
                    type="string",
                    description="ID of the lead this activity will be associated with",
                ),
                "org_id": ParameterDef(
                    type="integer",
                    description="ID of the organization this activity will be associated with",
                ),
                "project_id": ParameterDef(
                    type="string",
                    description="ID of the project this activity will be associated with",
                ),
                "due_date": ParameterDef(
                    type="string",
                    description="Due date of the activity. Format: YYYY-MM-DD",
                ),
                "due_time": ParameterDef(
                    type="string",
                    description="Due time of the activity in UTC. Format: HH:MM",
                ),
                "duration": ParameterDef(
                    type="string",
                    description="Duration of the activity. Format: HH:MM",
                ),
                "busy": ParameterDef(
                    type="boolean",
                    description="Set the activity as Busy or Free",
                ),
                "done": ParameterDef(
                    type="boolean",
                    description="Whether the activity is done or not",
                ),
                "note": ParameterDef(
                    type="string",
                    description="Note of the activity (HTML format)",
                ),
                "public_description": ParameterDef(
                    type="string",
                    description="Additional details about the activity that will be synced to your external calendar",
                ),
            },
        ),
        ActionDefinition(
            name="add_deal",
            description="Add a new deal in Pipedrive",
            parameters={
                "title": ParameterDef(
                    type="string",
                    description="Deal title",
                    required=True,
                ),
                "owner_id": ParameterDef(
                    type="integer",
                    description="ID of the user who will be marked as the owner of this deal",
                ),
                "person_id": ParameterDef(
                    type="integer",
                    description="ID of the person this deal will be associated with",
                ),
                "org_id": ParameterDef(
                    type="integer",
                    description="ID of the organization this deal will be associated with",
                ),
                "pipeline_id": ParameterDef(
                    type="integer",
                    description="ID of the pipeline this deal will be placed in",
                ),
                "stage_id": ParameterDef(
                    type="integer",
                    description="ID of the stage this deal will be placed in",
                ),
                "value": ParameterDef(
                    type="string",
                    description="Value of the deal. If omitted, value will be set to 0.",
                ),
                "currency": ParameterDef(
                    type="string",
                    description="Currency of the deal (3-character code). If omitted, uses the default currency of the authorized user.",
                ),
                "status": ParameterDef(
                    type="string",
                    description="Status of the deal. Allowed values: open, won, lost, deleted",
                ),
                "probability": ParameterDef(
                    type="integer",
                    description="Deal success probability percentage",
                ),
                "lost_reason": ParameterDef(
                    type="string",
                    description="Message about why the deal was lost (when status=lost)",
                ),
                "visible_to": ParameterDef(
                    type="integer",
                    description="Visibility of the deal. 1 = Owner & followers (private), 3 = Entire company (shared)",
                ),
                "expected_close_date": ParameterDef(
                    type="string",
                    description="Expected close date of the deal. Format: YYYY-MM-DD",
                ),
                "note": ParameterDef(
                    type="string",
                    description="Content of a note to attach to the deal after creation",
                ),
            },
        ),
        ActionDefinition(
            name="add_labels",
            description="Add labels to a lead, person, deal, or organization in Pipedrive",
            parameters={
                "type": ParameterDef(
                    type="string",
                    description="The type of the item. Allowed values: lead, person, deal, organization",
                    required=True,
                ),
                "label_ids": ParameterDef(
                    type="array",
                    description="The IDs of labels to add. Element type: string",
                    required=True,
                ),
                "lead_id": ParameterDef(
                    type="string",
                    description="The ID of the lead (required when type=lead)",
                ),
                "person_id": ParameterDef(
                    type="integer",
                    description="The ID of the person (required when type=person)",
                ),
                "deal_id": ParameterDef(
                    type="string",
                    description="The ID of the deal (required when type=deal)",
                ),
                "organization_id": ParameterDef(
                    type="integer",
                    description="The ID of the organization (required when type=organization)",
                ),
                "replace_existing_labels": ParameterDef(
                    type="boolean",
                    description="Set to true to replace existing labels with the new ones, false to append",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="add_lead",
            description="Create a new lead in Pipedrive",
            parameters={
                "title": ParameterDef(
                    type="string",
                    description="The name of the lead",
                    required=True,
                ),
                "person_id": ParameterDef(
                    type="integer",
                    description="The ID of a person to link to. Required unless organization_id is specified.",
                ),
                "organization_id": ParameterDef(
                    type="integer",
                    description="The ID of an organization to link to. Required unless person_id is specified.",
                ),
                "owner_id": ParameterDef(
                    type="integer",
                    description="The ID of the user who will own the lead",
                ),
                "label_ids": ParameterDef(
                    type="array",
                    description="The IDs of lead labels to associate. Element type: string (UUID)",
                ),
                "expected_close_date": ParameterDef(
                    type="string",
                    description="Expected close date. Format: YYYY-MM-DD",
                ),
                "visible_to": ParameterDef(
                    type="string",
                    description="Visibility of the lead. Allowed values: 1, 3, 5, 7",
                ),
                "was_seen": ParameterDef(
                    type="boolean",
                    description="Whether the lead was seen in the Pipedrive UI",
                ),
                "note": ParameterDef(
                    type="string",
                    description="A note to add to the lead",
                ),
            },
        ),
        ActionDefinition(
            name="add_note",
            description="Add a new note to a lead, deal, person, or organization in Pipedrive",
            parameters={
                "content": ParameterDef(
                    type="string",
                    description="The content of the note in HTML format",
                    required=True,
                ),
                "lead_id": ParameterDef(
                    type="string",
                    description="The ID of the lead to attach the note to",
                ),
                "deal_id": ParameterDef(
                    type="string",
                    description="The ID of the deal to attach the note to",
                ),
                "person_id": ParameterDef(
                    type="integer",
                    description="The ID of the person to attach the note to",
                ),
                "organization_id": ParameterDef(
                    type="integer",
                    description="The ID of the organization to attach the note to",
                ),
                "user_id": ParameterDef(
                    type="integer",
                    description="The ID of the user marked as the author (admin only)",
                ),
                "pinned_to_deal_flag": ParameterDef(
                    type="boolean",
                    description="Pin the note to the deal (requires deal_id)",
                    default=False,
                ),
                "pinned_to_lead_flag": ParameterDef(
                    type="boolean",
                    description="Pin the note to the lead (requires lead_id)",
                    default=False,
                ),
                "pinned_to_org_flag": ParameterDef(
                    type="boolean",
                    description="Pin the note to the organization (requires organization_id)",
                    default=False,
                ),
                "pinned_to_person_flag": ParameterDef(
                    type="boolean",
                    description="Pin the note to the person (requires person_id)",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="add_organization",
            description="Add a new organization in Pipedrive",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Organization name",
                    required=True,
                ),
                "owner_id": ParameterDef(
                    type="integer",
                    description="ID of the user who will be marked as the owner",
                ),
                "visible_to": ParameterDef(
                    type="integer",
                    description="Visibility. 1 = Owner & followers (private), 3 = Entire company (shared)",
                ),
            },
        ),
        ActionDefinition(
            name="add_person",
            description="Add a new person (contact) in Pipedrive",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Person name",
                    required=True,
                ),
                "owner_id": ParameterDef(
                    type="integer",
                    description="ID of the user who will be marked as the owner",
                ),
                "org_id": ParameterDef(
                    type="integer",
                    description="ID of the organization this person will belong to",
                ),
                "emails": ParameterDef(
                    type="array",
                    description="Email addresses. Element type: object with keys {value, primary, label}",
                ),
                "phones": ParameterDef(
                    type="array",
                    description="Phone numbers. Element type: object with keys {value, primary, label}",
                ),
                "visible_to": ParameterDef(
                    type="integer",
                    description="Visibility. 1 = Owner & followers (private), 3 = Entire company (shared)",
                ),
            },
        ),
        ActionDefinition(
            name="get_all_leads",
            description="Get all leads from Pipedrive with optional filtering",
            parameters={
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return. If not provided, all leads are returned.",
                ),
                "owner_id": ParameterDef(
                    type="integer",
                    description="Filter leads by the given user ID",
                ),
                "person_id": ParameterDef(
                    type="integer",
                    description="Filter leads by the given person ID",
                ),
                "organization_id": ParameterDef(
                    type="integer",
                    description="Filter leads by the given organization ID",
                ),
                "filter_id": ParameterDef(
                    type="integer",
                    description="The ID of the filter to use. Takes precedence over other filters.",
                ),
                "sort": ParameterDef(
                    type="string",
                    description="Field and direction to sort by. Valid fields: id, title, owner_id, creator_id, was_seen, expected_close_date, next_activity_id, add_time, update_time",
                ),
            },
        ),
        ActionDefinition(
            name="get_deal",
            description="Get a deal by its ID in Pipedrive",
            parameters={
                "deal_id": ParameterDef(
                    type="string",
                    description="The ID of the deal to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_lead_by_id",
            description="Get a lead by its ID in Pipedrive",
            parameters={
                "lead_id": ParameterDef(
                    type="string",
                    description="The ID of the lead to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_person_details",
            description="Get details of a person by their ID in Pipedrive",
            parameters={
                "person_id": ParameterDef(
                    type="integer",
                    description="The ID of the person to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_deals",
            description="List deals in Pipedrive with optional filtering and pagination",
            parameters={
                "filter_id": ParameterDef(
                    type="integer",
                    description="The ID of the filter to apply",
                ),
                "owner_id": ParameterDef(
                    type="integer",
                    description="Filter by owner user ID",
                ),
                "person_id": ParameterDef(
                    type="integer",
                    description="Filter by associated person ID",
                ),
                "organization_id": ParameterDef(
                    type="integer",
                    description="Filter by associated organization ID",
                ),
                "pipeline_id": ParameterDef(
                    type="integer",
                    description="Filter by pipeline ID",
                ),
                "stage_id": ParameterDef(
                    type="integer",
                    description="Filter by stage ID",
                ),
                "status": ParameterDef(
                    type="string",
                    description="Filter by status. Allowed values: open, won, lost, deleted",
                ),
                "sort_by": ParameterDef(
                    type="string",
                    description="Field to sort by. Allowed values: id, update_time, add_time",
                ),
                "sort_direction": ParameterDef(
                    type="string",
                    description="Sort direction. Allowed values: asc, desc",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of entries to return (max 500)",
                ),
                "cursor": ParameterDef(
                    type="string",
                    description="Cursor for pagination to the next page of results",
                ),
            },
        ),
        ActionDefinition(
            name="list_lead_label_ids_options",
            description="Retrieve available lead label options from Pipedrive",
            parameters={},
        ),
        ActionDefinition(
            name="list_organization_label_ids_options",
            description="Retrieve available organization label options from Pipedrive",
            parameters={},
        ),
        ActionDefinition(
            name="list_person_label_ids_options",
            description="Retrieve available person label options from Pipedrive",
            parameters={},
        ),
        ActionDefinition(
            name="list_user_id_options",
            description="Retrieve available user options from Pipedrive",
            parameters={},
        ),
        ActionDefinition(
            name="merge_deals",
            description="Merge two deals in Pipedrive",
            parameters={
                "deal_id": ParameterDef(
                    type="string",
                    description="The ID of the deal to merge (will be removed)",
                    required=True,
                ),
                "target_deal_id": ParameterDef(
                    type="string",
                    description="The ID of the deal to merge into (will be kept)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="merge_persons",
            description="Merge two persons in Pipedrive",
            parameters={
                "person_id": ParameterDef(
                    type="integer",
                    description="The ID of the person to merge (will be removed)",
                    required=True,
                ),
                "target_person_id": ParameterDef(
                    type="integer",
                    description="The ID of the person to merge into (will be kept, data prioritized on conflict)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="remove_duplicate_notes",
            description="Remove duplicate notes from an object in Pipedrive",
            parameters={
                "lead_id": ParameterDef(
                    type="string",
                    description="The ID of the lead whose notes to deduplicate",
                ),
                "deal_id": ParameterDef(
                    type="string",
                    description="The ID of the deal whose notes to deduplicate",
                ),
                "person_id": ParameterDef(
                    type="integer",
                    description="The ID of the person whose notes to deduplicate",
                ),
                "organization_id": ParameterDef(
                    type="integer",
                    description="The ID of the organization whose notes to deduplicate",
                ),
                "user_id": ParameterDef(
                    type="integer",
                    description="The ID of the user whose notes to deduplicate",
                ),
                "project_id": ParameterDef(
                    type="string",
                    description="The ID of the project whose notes to deduplicate",
                ),
                "keyword": ParameterDef(
                    type="string",
                    description="Only remove duplicate notes that contain this keyword",
                ),
            },
        ),
        ActionDefinition(
            name="remove_labels",
            description="Remove labels from a lead, person, deal, or organization in Pipedrive",
            parameters={
                "type": ParameterDef(
                    type="string",
                    description="The type of the item. Allowed values: lead, person, deal, organization",
                    required=True,
                ),
                "entity_id": ParameterDef(
                    type="string",
                    description="ID of the entity to remove labels from",
                    required=True,
                ),
                "label_ids": ParameterDef(
                    type="array",
                    description="The label IDs to remove. Element type: string",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search_leads",
            description="Search for leads by name or email in Pipedrive",
            parameters={
                "term": ParameterDef(
                    type="string",
                    description="The search term (minimum 2 characters, or 1 with exact_match)",
                    required=True,
                ),
                "exact_match": ParameterDef(
                    type="boolean",
                    description="When true, only full exact matches are returned (not case sensitive)",
                ),
                "fields": ParameterDef(
                    type="array",
                    description="Fields to search from. Allowed values: custom_fields, notes, title. Element type: string",
                ),
                "person_id": ParameterDef(
                    type="integer",
                    description="Filter by person ID",
                ),
                "organization_id": ParameterDef(
                    type="integer",
                    description="Filter by organization ID",
                ),
                "include_fields": ParameterDef(
                    type="string",
                    description="Optional fields to include. Allowed: lead.was_seen",
                ),
            },
        ),
        ActionDefinition(
            name="search_notes",
            description="Search for notes in Pipedrive with filtering options",
            parameters={
                "search_term": ParameterDef(
                    type="string",
                    description="The term to search for in note content",
                ),
                "lead_id": ParameterDef(
                    type="string",
                    description="Filter by lead ID",
                ),
                "deal_id": ParameterDef(
                    type="string",
                    description="Filter by deal ID",
                ),
                "person_id": ParameterDef(
                    type="integer",
                    description="Filter by person ID",
                ),
                "organization_id": ParameterDef(
                    type="integer",
                    description="Filter by organization ID",
                ),
                "user_id": ParameterDef(
                    type="integer",
                    description="Filter by user ID",
                ),
                "sort_field": ParameterDef(
                    type="string",
                    description="Sort field. Allowed: id, user_id, deal_id, org_id, person_id, content, add_time, update_time",
                ),
                "sort_direction": ParameterDef(
                    type="string",
                    description="Sort direction. Allowed: ASC, DESC",
                    default="DESC",
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="Date from which to fetch notes. Format: YYYY-MM-DD",
                ),
                "end_date": ParameterDef(
                    type="string",
                    description="Date until which to fetch notes. Format: YYYY-MM-DD",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                ),
            },
        ),
        ActionDefinition(
            name="search_persons",
            description="Search for persons by name, email, phone, or notes in Pipedrive",
            parameters={
                "term": ParameterDef(
                    type="string",
                    description="The search term (minimum 2 characters, or 1 with exact_match)",
                    required=True,
                ),
                "fields": ParameterDef(
                    type="array",
                    description="Fields to search from. Allowed: custom_fields, email, notes, phone, name. Element type: string",
                ),
                "exact_match": ParameterDef(
                    type="boolean",
                    description="When true, only full exact matches are returned (not case sensitive)",
                ),
                "organization_id": ParameterDef(
                    type="integer",
                    description="Filter by organization ID (upper limit: 2000)",
                ),
                "include_fields": ParameterDef(
                    type="string",
                    description="Optional fields to include. Allowed: person.picture",
                ),
                "start": ParameterDef(
                    type="integer",
                    description="Pagination start offset",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Items per page",
                ),
            },
        ),
        ActionDefinition(
            name="update_deal",
            description="Update the properties of a deal in Pipedrive",
            parameters={
                "deal_id": ParameterDef(
                    type="string",
                    description="ID of the deal to update",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="New deal title",
                ),
                "owner_id": ParameterDef(
                    type="integer",
                    description="ID of the new owner user",
                ),
                "person_id": ParameterDef(
                    type="integer",
                    description="ID of the person to associate",
                ),
                "org_id": ParameterDef(
                    type="integer",
                    description="ID of the organization to associate",
                ),
                "pipeline_id": ParameterDef(
                    type="integer",
                    description="ID of the pipeline",
                ),
                "stage_id": ParameterDef(
                    type="integer",
                    description="ID of the stage in the pipeline",
                ),
                "value": ParameterDef(
                    type="string",
                    description="Value of the deal",
                ),
                "currency": ParameterDef(
                    type="string",
                    description="Currency (3-character code)",
                ),
                "status": ParameterDef(
                    type="string",
                    description="Status. Allowed values: open, won, lost, deleted",
                ),
                "probability": ParameterDef(
                    type="integer",
                    description="Deal success probability percentage",
                ),
                "lost_reason": ParameterDef(
                    type="string",
                    description="Reason the deal was lost (when status=lost)",
                ),
                "visible_to": ParameterDef(
                    type="integer",
                    description="Visibility. 1 = private, 3 = shared",
                ),
                "note": ParameterDef(
                    type="string",
                    description="A note to add to the deal",
                ),
            },
        ),
        ActionDefinition(
            name="update_lead",
            description="Update a lead in Pipedrive",
            parameters={
                "lead_id": ParameterDef(
                    type="string",
                    description="The ID of the lead to update",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="New title of the lead",
                ),
                "person_id": ParameterDef(
                    type="integer",
                    description="ID of the person to link to",
                ),
                "organization_id": ParameterDef(
                    type="integer",
                    description="ID of the organization to link to",
                ),
                "owner_id": ParameterDef(
                    type="integer",
                    description="ID of the new owner user",
                ),
                "label_ids": ParameterDef(
                    type="array",
                    description="Lead label IDs. Element type: string (UUID)",
                ),
                "expected_close_date": ParameterDef(
                    type="string",
                    description="Expected close date. Format: YYYY-MM-DD",
                ),
                "visible_to": ParameterDef(
                    type="string",
                    description="Visibility. Allowed values: 1, 3, 5, 7",
                ),
                "was_seen": ParameterDef(
                    type="boolean",
                    description="Whether the lead was seen in the UI",
                ),
                "is_archived": ParameterDef(
                    type="boolean",
                    description="Whether the lead is archived",
                ),
            },
        ),
        ActionDefinition(
            name="update_person",
            description="Update an existing person in Pipedrive",
            parameters={
                "person_id": ParameterDef(
                    type="integer",
                    description="The ID of the person to update",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="New name of the person",
                ),
                "owner_id": ParameterDef(
                    type="integer",
                    description="ID of the new owner user",
                ),
                "org_id": ParameterDef(
                    type="integer",
                    description="ID of the organization this person will belong to",
                ),
                "emails": ParameterDef(
                    type="array",
                    description="Email addresses. Element type: object with keys {value, primary, label}",
                ),
                "phones": ParameterDef(
                    type="array",
                    description="Phone numbers. Element type: object with keys {value, primary, label}",
                ),
                "visible_to": ParameterDef(
                    type="integer",
                    description="Visibility. 1 = private, 3 = shared",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Pipedrive OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="PIPEDRIVE_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Pipedrive OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://developers.pipedrive.com/docs/api/v1",
                ),
                EnvVar(
                    name="PIPEDRIVE_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Pipedrive OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://developers.pipedrive.com/docs/api/v1",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://oauth.pipedrive.com/oauth/authorize",
                token_url="https://oauth.pipedrive.com/oauth/token",
                scopes=[
                    "deals:full",
                    "contacts:full",
                    "leads:full",
                    "activities:full",
                    "search:read",
                    "users:read",
                    "admin",
                ],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.pipedrive.com/api/v1/users/me",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching the authenticated user info",
            ),
        ),
    ],
)

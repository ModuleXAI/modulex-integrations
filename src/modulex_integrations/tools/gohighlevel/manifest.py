"""GoHighLevel integration manifest.

Declares the CRM, communication and scheduling actions this integration
exposes against the GoHighLevel (LeadConnector) v2 API, plus the OAuth 2.0
credential schema the modulex runtime uses to drive the connect flow,
credential validation, and tool discovery.

Two credential facts matter here. The access token is issued per
**sub-account** (``user_type=Location``), and nearly every v2 endpoint is
scoped to that sub-account — so the location ID is declared as an
``inject_into_auth_data`` environment variable and read from ``auth_data``
rather than asked for on every action.
"""
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


# Scopes for the contacts / opportunities / conversations / calendars /
# emails / campaigns surface this integration covers, taken from the
# official scope table (docs/oauth/Scopes.md). Every one is Sub-Account
# access; no agency-level scope is requested.
_SCOPES = [
    "calendars.readonly",
    "calendars.write",
    "calendars/events.readonly",
    "calendars/events.write",
    "calendars/groups.readonly",
    "calendars/groups.write",
    "calendars/resources.readonly",
    "calendars/resources.write",
    "campaigns.readonly",
    "contacts.readonly",
    "contacts.write",
    "conversations.readonly",
    "conversations.write",
    "conversations/livechat.write",
    "conversations/message.readonly",
    "conversations/message.write",
    "emails/builder.readonly",
    "emails/builder.write",
    "emails/schedule.readonly",
    "opportunities.readonly",
    "opportunities.write",
]


manifest = IntegrationManifest(
    name="gohighlevel",
    display_name="GoHighLevel",
    description=(
        "Run a GoHighLevel sub-account from an agent: create and search "
        "contacts with their notes, tasks and tags, move opportunities "
        "through pipelines, read and send conversation messages across SMS, "
        "email and social channels, and manage calendars, appointments, "
        "availability schedules and booking slots."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:gohighlevel-themed",
    app_url="https://www.gohighlevel.com",
    categories=["CRM", "Sales", "Marketing & Advertising"],
    actions=[
    ActionDefinition(
        name="create_contact",
        description="Create a new contact in the connected GoHighLevel sub-account.",
        parameters={
            "first_name": ParameterDef(type="string", description="The contact's first name"),
            "last_name": ParameterDef(type="string", description="The contact's last name"),
            "name": ParameterDef(type="string", description="The contact's full name"),
            "email": ParameterDef(type="string", description="The contact's email address"),
            "phone": ParameterDef(
                type="string", description="The contact's phone number in E.164 format"
            ),
            "gender": ParameterDef(type="string", description="The contact's gender"),
            "address1": ParameterDef(type="string", description="The contact's street address"),
            "city": ParameterDef(type="string", description="The contact's city"),
            "state": ParameterDef(type="string", description="The contact's state or region"),
            "postal_code": ParameterDef(
                type="string", description="The contact's postal/ZIP code"
            ),
            "country": ParameterDef(
                type="string", description="The contact's country as a two-letter ISO code"
            ),
            "website": ParameterDef(type="string", description="The contact's website URL"),
            "timezone": ParameterDef(type="string", description="The contact's timezone"),
            "company_name": ParameterDef(
                type="string", description="The contact's company name"
            ),
            "source": ParameterDef(
                type="string", description="The source attributed to the contact"
            ),
            "date_of_birth": ParameterDef(
                type="string",
                description="Birth date of the contact. Supported formats include YYYY-MM-DD",
            ),
            "assigned_to": ParameterDef(
                type="string",
                description="Unique identifier of the user the contact is assigned to",
            ),
            "dnd": ParameterDef(
                type="boolean",
                description="When true, enables Do Not Disturb across all channels",
            ),
            "dnd_settings": ParameterDef(
                type="object",
                description=(
                    "Per-channel Do Not Disturb settings (keys: Call, Email, SMS, "
                    "WhatsApp, GMB, FB), each an object with status/message/code"
                ),
            ),
            "inbound_dnd_settings": ParameterDef(
                type="object",
                description="Inbound Do Not Disturb settings for the contact",
            ),
            "tags": ParameterDef(
                type="array", description="Tags to associate with the contact"
            ),
            "custom_fields": ParameterDef(
                type="array",
                description=(
                    "Custom field values; each item is an object with an id (or key) "
                    "and a value"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="list_contacts",
        description="List contacts in the connected GoHighLevel sub-account.",
        parameters={
            "query": ParameterDef(
                type="string",
                description="Search text matched against name, email or phone",
            ),
            "limit": ParameterDef(
                type="integer", description="Maximum number of contacts to return"
            ),
            "start_after": ParameterDef(
                type="integer",
                description="Timestamp cursor for pagination from a previous response",
            ),
            "start_after_id": ParameterDef(
                type="string",
                description="Contact id cursor for pagination from a previous response",
            ),
        },
    ),
    ActionDefinition(
        name="bulk_update_contacts_business",
        description="Add or remove many contacts from a business in one bulk call.",
        parameters={
            "contact_ids": ParameterDef(
                type="array",
                description=(
                    "Unique identifiers of the contacts to add to or remove from the "
                    "business"
                ),
                required=True,
            ),
            "business_id": ParameterDef(
                type="string",
                description=(
                    "Unique identifier of the business to associate the contacts with. "
                    "Omit to detach the contacts from their business"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="bulk_update_contact_tags",
        description="Add or remove tags across many contacts at once.",
        parameters={
            "operation": ParameterDef(
                type="string",
                description="The bulk tag operation to perform: 'add' or 'remove'",
                required=True,
            ),
            "contact_ids": ParameterDef(
                type="array",
                description="List of contact ids to be processed",
                required=True,
            ),
            "tags": ParameterDef(
                type="array",
                description="List of tags to be added or removed",
                required=True,
            ),
            "remove_all_tags": ParameterDef(
                type="boolean",
                description=(
                    "When true, removes every tag from the contacts. Only valid with "
                    "the 'remove' operation"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="list_business_contacts",
        description="List the contacts that belong to a specific business.",
        parameters={
            "business_id": ParameterDef(
                type="string",
                description=(
                    "Unique identifier of the business whose contacts are to be "
                    "retrieved"
                ),
                required=True,
            ),
            "query": ParameterDef(
                type="string", description="A search query to filter the returned contacts"
            ),
            "limit": ParameterDef(
                type="integer",
                description="Maximum number of contacts to return in a single page",
            ),
            "skip": ParameterDef(
                type="integer",
                description="Number of contacts to skip, used for pagination",
            ),
        },
    ),
    ActionDefinition(
        name="search_contacts",
        description="Search contacts using advanced filters, sorting and deep pagination.",
        parameters={
            "page_limit": ParameterDef(
                type="integer",
                description="Maximum number of contacts to return per page",
                default=20,
            ),
            "page": ParameterDef(
                type="integer", description="The page number of results to retrieve"
            ),
            "filters": ParameterDef(
                type="array",
                description=(
                    "Filter objects used to narrow the search; each describes a field, "
                    "operator and value to match"
                ),
            ),
            "sort": ParameterDef(
                type="array",
                description=(
                    "Sort objects defining result ordering; each has a field and "
                    "direction"
                ),
            ),
            "search_after": ParameterDef(
                type="array",
                description=(
                    "Cursor values for deep pagination taken from the last contact of "
                    "the previous page"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="get_duplicate_contact",
        description=(
            "Find an existing duplicate contact by email or phone before creating one."
        ),
        parameters={
            "email": ParameterDef(
                type="string", description="Email address to search for a duplicate contact"
            ),
            "number": ParameterDef(
                type="string", description="Phone number to search for a duplicate contact"
            ),
        },
    ),
    ActionDefinition(
        name="upsert_contact",
        description=(
            "Create a contact, or update the matching duplicate if one already exists."
        ),
        parameters={
            "first_name": ParameterDef(type="string", description="The contact's first name"),
            "last_name": ParameterDef(type="string", description="The contact's last name"),
            "name": ParameterDef(type="string", description="The contact's full name"),
            "email": ParameterDef(type="string", description="The contact's email address"),
            "phone": ParameterDef(
                type="string", description="The contact's phone number in E.164 format"
            ),
            "gender": ParameterDef(type="string", description="The contact's gender"),
            "address1": ParameterDef(type="string", description="The contact's street address"),
            "city": ParameterDef(type="string", description="The contact's city"),
            "state": ParameterDef(type="string", description="The contact's state or region"),
            "postal_code": ParameterDef(
                type="string", description="The contact's postal/ZIP code"
            ),
            "country": ParameterDef(
                type="string", description="The contact's country as a two-letter ISO code"
            ),
            "website": ParameterDef(type="string", description="The contact's website URL"),
            "timezone": ParameterDef(type="string", description="The contact's timezone"),
            "company_name": ParameterDef(
                type="string", description="The contact's company name"
            ),
            "source": ParameterDef(
                type="string", description="The source attributed to the contact"
            ),
            "date_of_birth": ParameterDef(
                type="string",
                description="Birth date of the contact. Supported formats include YYYY-MM-DD",
            ),
            "assigned_to": ParameterDef(
                type="string",
                description="Unique identifier of the user the contact is assigned to",
            ),
            "dnd": ParameterDef(
                type="boolean",
                description="When true, enables Do Not Disturb across all channels",
            ),
            "dnd_settings": ParameterDef(
                type="object",
                description="Per-channel Do Not Disturb settings for the contact",
            ),
            "inbound_dnd_settings": ParameterDef(
                type="object",
                description="Inbound Do Not Disturb settings for the contact",
            ),
            "tags": ParameterDef(
                type="array",
                description=(
                    "Tags for the contact; this overwrites all tags currently on the "
                    "contact"
                ),
            ),
            "custom_fields": ParameterDef(
                type="array",
                description=(
                    "Custom field values; each item is an object with an id (or key) "
                    "and a value"
                ),
            ),
            "create_new_if_duplicate_allowed": ParameterDef(
                type="boolean",
                description=(
                    "When true and the sub-account allows duplicates, always create a "
                    "new contact instead of updating the duplicate"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="get_contact",
        description="Retrieve the full details of a single contact by its id.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact to retrieve",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_contact",
        description="Update the fields of an existing contact.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact to update",
                required=True,
            ),
            "first_name": ParameterDef(type="string", description="Updated first name"),
            "last_name": ParameterDef(type="string", description="Updated last name"),
            "name": ParameterDef(type="string", description="Updated full name"),
            "email": ParameterDef(type="string", description="Updated email address"),
            "phone": ParameterDef(
                type="string", description="Updated phone number in E.164 format"
            ),
            "address1": ParameterDef(type="string", description="Updated street address"),
            "city": ParameterDef(type="string", description="Updated city"),
            "state": ParameterDef(type="string", description="Updated state or region"),
            "postal_code": ParameterDef(type="string", description="Updated postal/ZIP code"),
            "country": ParameterDef(
                type="string", description="Updated two-letter ISO country code"
            ),
            "website": ParameterDef(type="string", description="Updated website URL"),
            "timezone": ParameterDef(type="string", description="Updated timezone"),
            "source": ParameterDef(type="string", description="Updated lead source"),
            "date_of_birth": ParameterDef(
                type="string", description="Updated birth date, e.g. YYYY-MM-DD"
            ),
            "assigned_to": ParameterDef(
                type="string",
                description="Unique identifier of the user the contact is assigned to",
            ),
            "dnd": ParameterDef(type="boolean", description="Updated do-not-disturb state"),
            "dnd_settings": ParameterDef(
                type="object",
                description="Per-channel Do Not Disturb settings for the contact",
            ),
            "inbound_dnd_settings": ParameterDef(
                type="object",
                description="Inbound Do Not Disturb settings for the contact",
            ),
            "tags": ParameterDef(
                type="array",
                description=(
                    "Tags for the contact; this overwrites all current tags. Prefer "
                    "add_contact_tags / remove_contact_tags for incremental changes"
                ),
            ),
            "custom_fields": ParameterDef(
                type="array",
                description=(
                    "Custom field values; each item is an object with an id (or key) "
                    "and a value"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="delete_contact",
        description="Permanently delete a contact from the sub-account.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact to delete",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="list_contact_appointments",
        description="List every calendar appointment booked for a contact.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact whose appointments to retrieve",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="remove_contact_from_every_campaign",
        description="Unenroll a contact from every campaign it is currently enrolled in.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact to remove from all campaigns",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="add_contact_to_campaign",
        description="Enroll a contact into a campaign.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact to enroll",
                required=True,
            ),
            "campaign_id": ParameterDef(
                type="string",
                description="Unique identifier of the campaign to enroll into",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="remove_contact_from_campaign",
        description="Unenroll a contact from one specific campaign.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact to unenroll",
                required=True,
            ),
            "campaign_id": ParameterDef(
                type="string",
                description="Unique identifier of the campaign to unenroll from",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="add_contact_followers",
        description="Add one or more users as followers of a contact.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact to add followers to",
                required=True,
            ),
            "followers": ParameterDef(
                type="array",
                description="List of user IDs to add as followers of the contact",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="remove_contact_followers",
        description="Remove one or more users from a contact's followers.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact to remove followers from",
                required=True,
            ),
            "followers": ParameterDef(
                type="array",
                description="List of user IDs to remove as followers of the contact",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="list_contact_notes",
        description="List every note attached to a contact.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact whose notes should be listed",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="create_contact_note",
        description="Attach a new note to a contact.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact to add the note to",
                required=True,
            ),
            "body": ParameterDef(
                type="string",
                description="The text content of the note",
                required=True,
            ),
            "title": ParameterDef(type="string", description="The title of the note"),
            "color": ParameterDef(
                type="string", description="The color associated with the note"
            ),
            "pinned": ParameterDef(
                type="boolean", description="When true, the note is pinned to the contact"
            ),
            "user_id": ParameterDef(
                type="string", description="The user the note is attributed to"
            ),
        },
    ),
    ActionDefinition(
        name="get_contact_note",
        description="Retrieve a single note attached to a contact.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact the note belongs to",
                required=True,
            ),
            "note_id": ParameterDef(
                type="string",
                description="Unique identifier of the note to retrieve",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_contact_note",
        description="Update the content or metadata of a note attached to a contact.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact the note belongs to",
                required=True,
            ),
            "note_id": ParameterDef(
                type="string",
                description="Unique identifier of the note to update",
                required=True,
            ),
            "body": ParameterDef(
                type="string", description="The updated text content of the note"
            ),
            "title": ParameterDef(type="string", description="The updated title of the note"),
            "color": ParameterDef(type="string", description="The updated color of the note"),
            "pinned": ParameterDef(
                type="boolean", description="When true, the note is pinned to the contact"
            ),
            "user_id": ParameterDef(
                type="string", description="The user the note is attributed to"
            ),
        },
    ),
    ActionDefinition(
        name="delete_contact_note",
        description="Delete a note attached to a contact.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact the note belongs to",
                required=True,
            ),
            "note_id": ParameterDef(
                type="string",
                description="Unique identifier of the note to delete",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="add_contact_tags",
        description="Add one or more tags to a contact.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact to tag",
                required=True,
            ),
            "tags": ParameterDef(
                type="array",
                description="The tags to add to the contact",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="remove_contact_tags",
        description="Remove one or more tags from a contact.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact to untag",
                required=True,
            ),
            "tags": ParameterDef(
                type="array",
                description="The tags to remove from the contact",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="list_contact_tasks",
        description="List every task attached to a contact.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact whose tasks to retrieve",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="create_contact_task",
        description="Create a task on a contact, such as a follow-up or reminder.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact to create the task for",
                required=True,
            ),
            "title": ParameterDef(
                type="string",
                description="The title/subject of the task",
                required=True,
            ),
            "due_date": ParameterDef(
                type="string",
                description="ISO 8601 due date for the task",
                required=True,
            ),
            "completed": ParameterDef(
                type="boolean",
                description="Whether the task starts out marked as completed",
                default=False,
            ),
            "body": ParameterDef(
                type="string", description="The description or body text of the task"
            ),
            "assigned_to": ParameterDef(
                type="string",
                description="Unique identifier of the user assigned to the task",
            ),
        },
    ),
    ActionDefinition(
        name="get_contact_task",
        description="Retrieve a single task attached to a contact.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact the task belongs to",
                required=True,
            ),
            "task_id": ParameterDef(
                type="string",
                description="Unique identifier of the task to retrieve",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_contact_task",
        description="Update the fields of a task attached to a contact.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact the task belongs to",
                required=True,
            ),
            "task_id": ParameterDef(
                type="string",
                description="Unique identifier of the task to update",
                required=True,
            ),
            "title": ParameterDef(
                type="string", description="The updated title/subject of the task"
            ),
            "due_date": ParameterDef(
                type="string", description="The updated ISO 8601 due date"
            ),
            "completed": ParameterDef(
                type="boolean", description="Whether the task is marked as completed"
            ),
            "body": ParameterDef(
                type="string", description="The updated description or body text of the task"
            ),
            "assigned_to": ParameterDef(
                type="string",
                description="Unique identifier of the user assigned to the task",
            ),
        },
    ),
    ActionDefinition(
        name="delete_contact_task",
        description="Delete a task attached to a contact.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact the task belongs to",
                required=True,
            ),
            "task_id": ParameterDef(
                type="string",
                description="Unique identifier of the task to delete",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="complete_contact_task",
        description="Mark a contact's task as completed or reopen it.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact the task belongs to",
                required=True,
            ),
            "task_id": ParameterDef(
                type="string",
                description="Unique identifier of the task to update",
                required=True,
            ),
            "completed": ParameterDef(
                type="boolean",
                description="True to mark the task complete, false to reopen it",
                default=True,
            ),
        },
    ),
    ActionDefinition(
        name="add_contact_to_workflow",
        description="Add a contact to a workflow, optionally scheduling when it starts.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact to add",
                required=True,
            ),
            "workflow_id": ParameterDef(
                type="string",
                description="Unique identifier of the workflow to add the contact to",
                required=True,
            ),
            "event_start_time": ParameterDef(
                type="string",
                description=(
                    "ISO 8601 time at which the workflow should start for this contact"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="delete_contact_from_workflow",
        description="Remove a contact from a workflow.",
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="Unique identifier of the contact to remove",
                required=True,
            ),
            "workflow_id": ParameterDef(
                type="string",
                description="Unique identifier of the workflow to remove the contact from",
                required=True,
            ),
            "event_start_time": ParameterDef(
                type="string", description="ISO 8601 time of the workflow event to remove"
            ),
        },
    ),
    ActionDefinition(
        name="create_opportunity",
        description="Create an opportunity in a pipeline for a contact.",
        parameters={
            "pipeline_id": ParameterDef(
                type="string",
                description="Unique identifier of the pipeline",
                required=True,
            ),
            "name": ParameterDef(
                type="string",
                description="The name of the opportunity",
                required=True,
            ),
            "status": ParameterDef(
                type="string",
                description="The status of the opportunity: open, won, lost or abandoned",
                required=True,
            ),
            "contact_id": ParameterDef(
                type="string",
                description=(
                    "Unique identifier of the contact associated with the opportunity"
                ),
                required=True,
            ),
            "pipeline_stage_id": ParameterDef(
                type="string", description="Unique identifier of the pipeline stage"
            ),
            "monetary_value": ParameterDef(
                type="number", description="The monetary value of the opportunity"
            ),
            "assigned_to": ParameterDef(
                type="string",
                description="Unique identifier of the user the opportunity is assigned to",
            ),
            "custom_fields": ParameterDef(
                type="array", description="Custom field values to set on the opportunity"
            ),
        },
    ),
    ActionDefinition(
        name="list_opportunity_lost_reasons",
        description="List the opportunity lost reasons configured for the sub-account.",
        parameters={
            "name": ParameterDef(
                type="string", description="Filter lost reasons by their exact name"
            ),
            "query": ParameterDef(
                type="string", description="A search string to filter lost reasons"
            ),
            "deleted": ParameterDef(
                type="boolean",
                description="Whether to include deleted lost reasons in the results",
            ),
            "skip": ParameterDef(
                type="integer", description="Number of lost reasons to skip for pagination"
            ),
            "limit": ParameterDef(
                type="integer", description="Maximum number of lost reasons to return"
            ),
            "get_count": ParameterDef(
                type="boolean",
                description="Whether to include the total count in the response",
            ),
        },
    ),
    ActionDefinition(
        name="list_pipelines",
        description="List the opportunity pipelines and their stages for the sub-account.",
        parameters={},
    ),
    ActionDefinition(
        name="search_opportunities",
        description=(
            "Search opportunities by pipeline, stage, contact, assignee, status or date."
        ),
        parameters={
            "query": ParameterDef(
                type="string", description="A free-text search query to filter opportunities"
            ),
            "opportunity_id": ParameterDef(
                type="string",
                description="Unique identifier of a specific opportunity to fetch",
            ),
            "pipeline_id": ParameterDef(
                type="string",
                description="Unique identifier of the pipeline to filter by",
            ),
            "pipeline_stage_id": ParameterDef(
                type="string",
                description="Unique identifier of the pipeline stage to filter by",
            ),
            "contact_id": ParameterDef(
                type="string", description="Unique identifier of the contact to filter by"
            ),
            "assigned_to": ParameterDef(
                type="string",
                description="Unique identifier of the assigned user to filter by",
            ),
            "campaign_id": ParameterDef(
                type="string",
                description="Unique identifier of the campaign to filter by",
            ),
            "status": ParameterDef(
                type="string",
                description="Status filter: open, won, lost, abandoned or all",
            ),
            "country": ParameterDef(
                type="string", description="Filter opportunities by country"
            ),
            "date": ParameterDef(
                type="string", description="Filter opportunities by a specific date"
            ),
            "end_date": ParameterDef(
                type="string", description="Filter opportunities up to this end date"
            ),
            "order": ParameterDef(type="string", description="The sort order for the results"),
            "page": ParameterDef(
                type="integer", description="The page number of results to retrieve"
            ),
            "limit": ParameterDef(
                type="integer",
                description="Maximum number of opportunities to return per page",
            ),
            "start_after": ParameterDef(
                type="string", description="Cursor timestamp used for pagination"
            ),
            "start_after_id": ParameterDef(
                type="string", description="Cursor id used for pagination"
            ),
            "get_tasks": ParameterDef(
                type="boolean",
                description="When true, includes related tasks in the response",
            ),
            "get_notes": ParameterDef(
                type="boolean",
                description="When true, includes related notes in the response",
            ),
            "get_calendar_events": ParameterDef(
                type="boolean",
                description="When true, includes related calendar events in the response",
            ),
        },
    ),
    ActionDefinition(
        name="search_opportunities_advanced",
        description="Search opportunities and optionally pull their notes, tasks and events.",
        parameters={
            "query": ParameterDef(
                type="string",
                description="The search query string used to match opportunities",
                default="",
            ),
            "limit": ParameterDef(
                type="integer",
                description="Maximum number of opportunities to return per page",
                default=20,
            ),
            "page": ParameterDef(
                type="integer",
                description="The page number of results to retrieve",
                default=1,
            ),
            "search_after": ParameterDef(
                type="array",
                description=(
                    "Cursor values for deep pagination, returned by a previous search"
                ),
            ),
            "include_notes": ParameterDef(
                type="boolean",
                description="When true, include related notes for each opportunity",
                default=False,
            ),
            "include_tasks": ParameterDef(
                type="boolean",
                description="When true, include related tasks for each opportunity",
                default=False,
            ),
            "include_calendar_events": ParameterDef(
                type="boolean",
                description="When true, include related calendar events for each opportunity",
                default=False,
            ),
            "include_unread_conversations": ParameterDef(
                type="boolean",
                description=(
                    "When true, include unread conversation counts for each opportunity"
                ),
                default=False,
            ),
        },
    ),
    ActionDefinition(
        name="upsert_opportunity",
        description="Create an opportunity, or update it when an opportunity id is supplied.",
        parameters={
            "pipeline_id": ParameterDef(
                type="string",
                description="Unique identifier of the pipeline the opportunity belongs to",
                required=True,
            ),
            "opportunity_id": ParameterDef(
                type="string",
                description=(
                    "When provided, updates that opportunity instead of creating a new one"
                ),
            ),
            "contact_id": ParameterDef(
                type="string",
                description=(
                    "Unique identifier of the contact associated with the opportunity"
                ),
            ),
            "name": ParameterDef(type="string", description="The name of the opportunity"),
            "status": ParameterDef(
                type="string",
                description="The status of the opportunity: open, won, lost or abandoned",
            ),
            "pipeline_stage_id": ParameterDef(
                type="string", description="Unique identifier of the pipeline stage"
            ),
            "monetary_value": ParameterDef(
                type="number", description="The monetary value of the opportunity"
            ),
            "assigned_to": ParameterDef(
                type="string",
                description="Unique identifier of the user the opportunity is assigned to",
            ),
            "lost_reason_id": ParameterDef(
                type="string",
                description="Unique identifier of the reason the opportunity was lost",
            ),
            "followers": ParameterDef(
                type="array",
                description="User identifiers to set as followers of the opportunity",
            ),
            "followers_action_type": ParameterDef(
                type="string",
                description="Action to apply to the followers list: 'add' or 'remove'",
            ),
            "is_remove_all_followers": ParameterDef(
                type="boolean",
                description="When true, removes all followers from the opportunity",
            ),
        },
    ),
    ActionDefinition(
        name="get_opportunity",
        description="Retrieve a single opportunity by its id.",
        parameters={
            "opportunity_id": ParameterDef(
                type="string",
                description="Unique identifier of the opportunity to retrieve",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="delete_opportunity",
        description="Permanently delete an opportunity.",
        parameters={
            "opportunity_id": ParameterDef(
                type="string",
                description="Unique identifier of the opportunity to delete",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_opportunity",
        description="Update an opportunity's name, pipeline, stage, value or assignee.",
        parameters={
            "opportunity_id": ParameterDef(
                type="string",
                description="Unique identifier of the opportunity to update",
                required=True,
            ),
            "name": ParameterDef(type="string", description="The name of the opportunity"),
            "status": ParameterDef(
                type="string",
                description="The status of the opportunity: open, won, lost or abandoned",
            ),
            "pipeline_id": ParameterDef(
                type="string",
                description="Unique identifier of the pipeline the opportunity belongs to",
            ),
            "pipeline_stage_id": ParameterDef(
                type="string", description="Unique identifier of the pipeline stage"
            ),
            "monetary_value": ParameterDef(
                type="number", description="The monetary value of the opportunity"
            ),
            "assigned_to": ParameterDef(
                type="string",
                description="Unique identifier of the user the opportunity is assigned to",
            ),
            "custom_fields": ParameterDef(
                type="array", description="Custom field values to set on the opportunity"
            ),
        },
    ),
    ActionDefinition(
        name="add_opportunity_followers",
        description="Add one or more users as followers of an opportunity.",
        parameters={
            "opportunity_id": ParameterDef(
                type="string",
                description="Unique identifier of the opportunity to add followers to",
                required=True,
            ),
            "followers": ParameterDef(
                type="array",
                description="List of user IDs to add as followers of the opportunity",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="remove_opportunity_followers",
        description="Remove one or more users from an opportunity's followers.",
        parameters={
            "opportunity_id": ParameterDef(
                type="string",
                description="Unique identifier of the opportunity to remove followers from",
                required=True,
            ),
            "followers": ParameterDef(
                type="array",
                description="List of user IDs to remove as followers of the opportunity",
                required=True,
            ),
            "is_remove_all_followers": ParameterDef(
                type="boolean",
                description=(
                    "When true, removes every follower regardless of the followers list"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="update_opportunity_status",
        description="Move an opportunity to open, won, lost or abandoned.",
        parameters={
            "opportunity_id": ParameterDef(
                type="string",
                description="Unique identifier of the opportunity whose status is updated",
                required=True,
            ),
            "status": ParameterDef(
                type="string",
                description="The new status: open, won, lost or abandoned",
                required=True,
            ),
            "lost_reason_id": ParameterDef(
                type="string",
                description=(
                    "Unique identifier of the lost reason, used when the status is 'lost'"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="list_campaigns",
        description=(
            "List the marketing campaigns configured in the GoHighLevel "
            "sub-account, optionally filtered by status."
        ),
        parameters={
            "status": ParameterDef(
                type="string",
                description="Filter campaigns by status, for example published or draft",
            ),
        },
    ),
    ActionDefinition(
        name="create_conversation",
        description=(
            "Start a new conversation thread between the sub-account and a "
            "contact."
        ),
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="The unique identifier of the contact the conversation is with",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="get_message_transcription",
        description=(
            "Get the call-recording transcription for a message, returned as "
            "one entry per transcribed sentence with timings and confidence."
        ),
        parameters={
            "message_id": ParameterDef(
                type="string",
                description="The unique identifier of the call message to transcribe",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="send_message",
        description=(
            "Send an outbound message to a contact over SMS, RCS, email, "
            "WhatsApp, Instagram, Facebook, live chat or a custom provider. "
            "Email-only fields (subject, html, email_cc, email_bcc, "
            "email_reply_mode) and phone-only fields (from_number, to_number) "
            "are ignored on other channels. Supply scheduled_timestamp to "
            "schedule the send instead of delivering immediately."
        ),
        parameters={
            "message_type": ParameterDef(
                type="string",
                description=(
                    "Channel to send on: SMS, RCS, Email, WhatsApp, IG, FB, "
                    "Custom, Live_Chat or TIKTOK"
                ),
                required=True,
            ),
            "contact_id": ParameterDef(
                type="string",
                description="ID of the contact receiving the message",
                required=True,
            ),
            "message": ParameterDef(
                type="string",
                description="Text content of the message",
            ),
            "subject": ParameterDef(
                type="string",
                description="Subject line for the message. Email messages only",
            ),
            "html": ParameterDef(
                type="string",
                description="HTML body of the message. Email messages only",
            ),
            "attachments": ParameterDef(
                type="array",
                description="Array of publicly reachable attachment URLs",
            ),
            "email_from": ParameterDef(
                type="string",
                description="Sender email address. Email messages only",
            ),
            "email_to": ParameterDef(
                type="string",
                description=(
                    "Recipient email address when it differs from the contact's "
                    "primary email. Email messages only"
                ),
            ),
            "email_cc": ParameterDef(
                type="array",
                description="Array of CC email addresses. Email messages only",
            ),
            "email_bcc": ParameterDef(
                type="array",
                description="Array of BCC email addresses. Email messages only",
            ),
            "email_reply_mode": ParameterDef(
                type="string",
                description="Reply mode for email replies: reply or reply_all",
            ),
            "from_number": ParameterDef(
                type="string",
                description="Sender phone number. SMS, RCS and WhatsApp only",
            ),
            "to_number": ParameterDef(
                type="string",
                description="Recipient phone number. SMS, RCS and WhatsApp only",
            ),
            "appointment_id": ParameterDef(
                type="string",
                description="ID of the associated appointment",
            ),
            "reply_message_id": ParameterDef(
                type="string",
                description="ID of the message being replied to",
            ),
            "template_id": ParameterDef(
                type="string",
                description="ID of a message template to render",
            ),
            "thread_id": ParameterDef(
                type="string",
                description=(
                    "ID of the message thread; for email this is the message ID "
                    "holding the whole thread"
                ),
            ),
            "scheduled_timestamp": ParameterDef(
                type="integer",
                description="UTC timestamp in seconds at which the message should be sent",
            ),
            "conversation_provider_id": ParameterDef(
                type="string",
                description="ID of the conversation provider to send through",
            ),
            "custom_subtype_id": ParameterDef(
                type="string",
                description=(
                    "Custom subtype ID for unsubscribe preferences. Email only"
                ),
            ),
            "sub_type": ParameterDef(
                type="object",
                description="Subtype object of the message being sent",
            ),
            "forward": ParameterDef(
                type="object",
                description=(
                    "Email forwarding config with keys isForwarded, "
                    "forwardWholeThread, messageId, emailMessageId, toEmail, "
                    "recipientContactId"
                ),
            ),
            "status": ParameterDef(
                type="string",
                description="Message status: delivered, failed, pending or read",
            ),
            "uses_native_scheduling_ai": ParameterDef(
                type="boolean",
                description="Whether the scheduled email uses native send-time AI",
            ),
            "optimization_period": ParameterDef(
                type="string",
                description="Send-time optimization window: 24h, 48h or 72h",
            ),
        },
    ),
    ActionDefinition(
        name="cancel_scheduled_email_message",
        description=(
            "Cancel a scheduled email message so it is never delivered. This "
            "cannot be undone."
        ),
        parameters={
            "email_message_id": ParameterDef(
                type="string",
                description=(
                    "The unique identifier of the scheduled email message to cancel"
                ),
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="get_email_by_id",
        description=(
            "Get one email message with its subject, body, sender, recipients, "
            "attachments and delivery status."
        ),
        parameters={
            "email_message_id": ParameterDef(
                type="string",
                description="The unique identifier of the email message to retrieve",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="export_messages",
        description=(
            "Export the sub-account's messages page by page using a cursor, "
            "optionally filtered by conversation, contact, channel and date "
            "range."
        ),
        parameters={
            "limit": ParameterDef(
                type="integer",
                description="Maximum number of messages to include in one page of results",
            ),
            "cursor": ParameterDef(
                type="string",
                description="Cursor from a previous response used to fetch the next page",
            ),
            "sort_by": ParameterDef(
                type="string",
                description="Field to sort by: createdAt or updatedAt",
            ),
            "sort_order": ParameterDef(
                type="string",
                description="Sort order: asc or desc",
            ),
            "conversation_id": ParameterDef(
                type="string",
                description="Only export messages from this conversation",
            ),
            "contact_id": ParameterDef(
                type="string",
                description="Only export messages belonging to this contact",
            ),
            "channel": ParameterDef(
                type="string",
                description=(
                    "Only export this channel: Call, SMS, Email, WhatsApp, "
                    "Instagram or Facebook. Omit to include activity messages too"
                ),
            ),
            "start_date": ParameterDef(
                type="string",
                description="Only export messages created on or after this date",
            ),
            "end_date": ParameterDef(
                type="string",
                description="Only export messages created on or before this date",
            ),
        },
    ),
    ActionDefinition(
        name="add_inbound_message",
        description=(
            "Record a message received from a contact into a conversation, for "
            "example an SMS, email or WhatsApp message handled by an external "
            "provider. Supply either conversation_id or contact_id."
        ),
        parameters={
            "message_type": ParameterDef(
                type="string",
                description=(
                    "Message type: SMS, RCS, Email, WhatsApp, GMB, IG, FB, "
                    "Custom, WebChat, Live_Chat, Call, IVR_Call, Campaign_Call, "
                    "Campaign_VoiceMail, TIKTOK, ALL_IN_ONE_CHAT or FORM_SUBMISSION"
                ),
                required=True,
            ),
            "conversation_id": ParameterDef(
                type="string",
                description="Conversation ID; either this or contact_id is required",
            ),
            "contact_id": ParameterDef(
                type="string",
                description="Contact ID; either this or conversation_id is required",
            ),
            "conversation_provider_id": ParameterDef(
                type="string",
                description="Conversation provider ID; required for custom providers",
            ),
            "message": ParameterDef(
                type="string",
                description="Message body",
            ),
            "html": ParameterDef(
                type="string",
                description="HTML body of the email",
            ),
            "subject": ParameterDef(
                type="string",
                description="Subject of the email",
            ),
            "email_from": ParameterDef(
                type="string",
                description=(
                    "Sender email address; tied to the contact record and cannot "
                    "be changed dynamically"
                ),
            ),
            "email_to": ParameterDef(
                type="string",
                description=(
                    "Recipient email address; tied to the contact record and "
                    "cannot be changed dynamically"
                ),
            ),
            "email_cc": ParameterDef(
                type="array",
                description="List of email addresses to CC",
            ),
            "email_bcc": ParameterDef(
                type="array",
                description="List of email addresses to BCC",
            ),
            "email_message_id": ParameterDef(
                type="string",
                description="Email message ID this message should be threaded under",
            ),
            "alt_id": ParameterDef(
                type="string",
                description="The external mail provider's message ID",
            ),
            "attachments": ParameterDef(
                type="array",
                description="Array of attachment URLs",
            ),
            "direction": ParameterDef(
                type="string",
                description="Message direction: inbound or outbound. Defaults to outbound",
            ),
            "date": ParameterDef(
                type="string",
                description="ISO 8601 date-time of the inbound message",
            ),
            "call": ParameterDef(
                type="object",
                description="Call details with keys to, from and status. Call types only",
            ),
        },
    ),
    ActionDefinition(
        name="add_outbound_message",
        description=(
            "Record an outbound call that was placed outside GoHighLevel "
            "against an existing conversation, including its recording URL."
        ),
        parameters={
            "conversation_id": ParameterDef(
                type="string",
                description="The conversation the outbound call belongs to",
                required=True,
            ),
            "conversation_provider_id": ParameterDef(
                type="string",
                description="Conversation provider ID",
                required=True,
            ),
            "message_type": ParameterDef(
                type="string",
                description='Message type; the endpoint only accepts "Call"',
                default="Call",
            ),
            "call": ParameterDef(
                type="object",
                description="Call details with keys to, from and status",
            ),
            "attachments": ParameterDef(
                type="array",
                description="Array of attachment URLs such as a call recording",
            ),
            "alt_id": ParameterDef(
                type="string",
                description="The external provider's message ID",
            ),
            "date": ParameterDef(
                type="string",
                description="ISO 8601 date-time of the outbound call",
            ),
        },
    ),
    ActionDefinition(
        name="send_review_reply",
        description=(
            "Reply to a Google My Business customer review through its review "
            "conversation."
        ),
        parameters={
            "conversation_id": ParameterDef(
                type="string",
                description=(
                    "The review conversation to reply to; it must carry a reviewId"
                ),
                required=True,
            ),
            "message": ParameterDef(
                type="string",
                description="Text of the review reply",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="complete_message_file_upload",
        description=(
            "Finalize a message file upload and return the file's public URL. "
            "Call this only after the file bytes have been PUT to the signed "
            "URL returned by initiate_message_file_upload."
        ),
        parameters={
            "upload_id": ParameterDef(
                type="string",
                description="Upload ID returned by initiate_message_file_upload",
                required=True,
            ),
            "file_path": ParameterDef(
                type="string",
                description="File path returned by initiate_message_file_upload",
                required=True,
            ),
            "conversation_id": ParameterDef(
                type="string",
                description="Conversation the file belongs to",
                required=True,
            ),
            "filename": ParameterDef(
                type="string",
                description=(
                    "Original filename; it becomes the key in the uploaded_files "
                    "response map"
                ),
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="initiate_message_file_upload",
        description=(
            "Request a signed Google Cloud Storage URL for a message "
            "attachment. The URL is valid for 15 minutes; the caller PUTs the "
            "file bytes to it themselves and then calls "
            "complete_message_file_upload."
        ),
        parameters={
            "conversation_id": ParameterDef(
                type="string",
                description="Conversation the file belongs to",
                required=True,
            ),
            "filename": ParameterDef(
                type="string",
                description="Original filename including its extension",
                required=True,
            ),
            "content_type": ParameterDef(
                type="string",
                description="MIME type of the file, for example video/mp4",
                required=True,
            ),
            "channel": ParameterDef(
                type="string",
                description=(
                    "Channel the file is for; WHATSAPP raises the size limit to "
                    "100MB, everything else is capped at 5MB"
                ),
                required=True,
            ),
            "file_size": ParameterDef(
                type="integer",
                description="File size in bytes, for pre-validation",
            ),
        },
    ),
    ActionDefinition(
        name="get_message",
        description=(
            "Get one conversation message by ID, with its body, direction, "
            "status, attachments and channel metadata."
        ),
        parameters={
            "message_id": ParameterDef(
                type="string",
                description="The unique identifier of the message",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="add_message_attachments",
        description=(
            "Replace the attachment URLs on an existing call message. Only "
            "supported for TYPE_CUSTOM_CALL and for TYPE_CALL with the "
            "EXTERNAL_CALL subtype. Maximum 5 URLs."
        ),
        parameters={
            "message_id": ParameterDef(
                type="string",
                description="The message to set attachments on",
                required=True,
            ),
            "attachments": ParameterDef(
                type="array",
                description=(
                    "Attachment URLs to set on the message, replacing any "
                    "existing ones. Maximum 5"
                ),
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="cancel_scheduled_message",
        description=(
            "Cancel a scheduled message so it is never delivered. This cannot "
            "be undone."
        ),
        parameters={
            "message_id": ParameterDef(
                type="string",
                description="The unique identifier of the scheduled message to cancel",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_message_status",
        description=(
            "Update the delivery status of a message sent through a "
            "conversation provider, optionally attaching the provider's error."
        ),
        parameters={
            "message_id": ParameterDef(
                type="string",
                description="The message whose status should change",
                required=True,
            ),
            "status": ParameterDef(
                type="string",
                description="New message status: delivered, failed, pending or read",
                required=True,
            ),
            "email_message_id": ParameterDef(
                type="string",
                description="Email message ID the status applies to",
            ),
            "recipients": ParameterDef(
                type="array",
                description="Additional email recipients the delivery status applies to",
            ),
            "provider_error": ParameterDef(
                type="object",
                description=(
                    "Error reported by the conversation provider, with keys "
                    "code, type and message"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="list_custom_subtypes",
        description=(
            "List the sub-account's custom message subtypes, which drive "
            "granular email subscription preferences."
        ),
        parameters={},
    ),
    ActionDefinition(
        name="create_custom_subtype",
        description=(
            "Create a custom message subtype contacts can subscribe to. "
            "Requires an agency or account admin role."
        ),
        parameters={
            "name": ParameterDef(
                type="string",
                description="Name of the custom subtype, max 100 characters",
                required=True,
            ),
            "channel": ParameterDef(
                type="string",
                description="Communication channel: email or sms",
                required=True,
            ),
            "language": ParameterDef(
                type="string",
                description="Language code, for example en",
                required=True,
            ),
            "description": ParameterDef(
                type="string",
                description="Description of the custom subtype, max 100 characters",
            ),
        },
    ),
    ActionDefinition(
        name="update_custom_subtype",
        description=(
            "Rename or archive a custom message subtype. Requires an agency or "
            "account admin role."
        ),
        parameters={
            "custom_subtype_id": ParameterDef(
                type="string",
                description="The unique identifier of the custom subtype to update",
                required=True,
            ),
            "name": ParameterDef(
                type="string",
                description="New name for the subtype, max 100 characters",
            ),
            "description": ParameterDef(
                type="string",
                description="New description for the subtype, max 100 characters",
            ),
            "archived": ParameterDef(
                type="boolean",
                description="Whether the custom subtype is archived",
            ),
            "resubscription_legal_form_id": ParameterDef(
                type="string",
                description="Resubscription legal form ID, optional when archiving",
            ),
        },
    ),
    ActionDefinition(
        name="get_contact_unsubscription_status",
        description=(
            "Read a contact's email subscription and unsubscribe statuses, for "
            "one address or for every address on the contact."
        ),
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="The contact whose subscriptions to read",
                required=True,
            ),
            "email": ParameterDef(
                type="string",
                description=(
                    "One email address to check; omit to get every email on the "
                    "contact"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="update_subscription_preference",
        description=(
            "Subscribe or unsubscribe a contact's email address on behalf of an "
            "agent, for a default subscription type, a custom subtype, or all "
            "types at once."
        ),
        parameters={
            "contact_id": ParameterDef(
                type="string",
                description="The contact whose subscription is changing",
                required=True,
            ),
            "email": ParameterDef(
                type="string",
                description="Email address the change applies to",
                required=True,
            ),
            "subscription_type": ParameterDef(
                type="string",
                description="Type of change: default, custom or resub_all",
                required=True,
            ),
            "subscription_status": ParameterDef(
                type="string",
                description="Resulting status: subscribed or unsubscribed",
                required=True,
            ),
            "subtype_name": ParameterDef(
                type="string",
                description='Subscription name for default types, e.g. "One on One"',
            ),
            "subtype_id": ParameterDef(
                type="string",
                description="Custom subscription type ID, for custom types",
            ),
            "legal_reason": ParameterDef(
                type="string",
                description="Legal reason; required for resubscribe and resub_all changes",
            ),
            "legal_description": ParameterDef(
                type="string",
                description="Supporting detail for the legal reason",
            ),
        },
    ),
    ActionDefinition(
        name="live_chat_agent_typing",
        description=(
            "Show or hide the agent typing indicator that a live-chat visitor "
            "sees while a reply is being written."
        ),
        parameters={
            "conversation_id": ParameterDef(
                type="string",
                description="The live-chat conversation ID",
                required=True,
            ),
            "visitor_id": ParameterDef(
                type="string",
                description="Unique ID assigned to the live-chat visitor being replied to",
                required=True,
            ),
            "is_typing": ParameterDef(
                type="string",
                description='Typing status, "true" or "false"',
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="search_conversations",
        description=(
            "Search the sub-account's conversations by free text, contact, "
            "assignee, follower, last-message characteristics, score profile or "
            "date, with sorting and paging."
        ),
        parameters={
            "query": ParameterDef(
                type="string",
                description="Free-text search string",
            ),
            "contact_id": ParameterDef(
                type="string",
                description="Only return conversations with this contact",
            ),
            "conversation_id": ParameterDef(
                type="string",
                description="Only return the conversation with this ID",
            ),
            "assigned_to": ParameterDef(
                type="string",
                description=(
                    'Comma-separated user IDs the conversations are assigned to; '
                    'use "unassigned" for conversations with no owner'
                ),
            ),
            "followers": ParameterDef(
                type="string",
                description="Comma-separated user IDs of followers to filter by",
            ),
            "mentions": ParameterDef(
                type="string",
                description="Comma-separated user IDs mentioned in the thread",
            ),
            "status": ParameterDef(
                type="string",
                description="Conversation status: all, read, unread, starred or recents",
            ),
            "sort": ParameterDef(
                type="string",
                description="Sort direction: asc or desc",
            ),
            "sort_by": ParameterDef(
                type="string",
                description=(
                    "Sort field: last_manual_message_date, last_message_date, "
                    "score_profile, overdue_at or due_at"
                ),
            ),
            "limit": ParameterDef(
                type="integer",
                description="Number of conversations to return. Default is 20",
            ),
            "start_after_date": ParameterDef(
                type="string",
                description="Resume after this sort value, taken from the last document",
            ),
            "last_message_type": ParameterDef(
                type="string",
                description="Filter by the last message type, e.g. TYPE_SMS or TYPE_EMAIL",
            ),
            "last_message_action": ParameterDef(
                type="string",
                description="Action of the last outbound message: automated or manual",
            ),
            "last_message_direction": ParameterDef(
                type="string",
                description="Direction of the last message: inbound or outbound",
            ),
            "score_profile": ParameterDef(
                type="string",
                description="Score profile ID to filter on, with score_profile_min/max",
            ),
            "sort_score_profile": ParameterDef(
                type="string",
                description="Score profile ID that score_profile sorting uses",
            ),
            "score_profile_min": ParameterDef(
                type="integer",
                description="Minimum score profile value",
            ),
            "score_profile_max": ParameterDef(
                type="integer",
                description="Maximum score profile value",
            ),
            "start_date": ParameterDef(
                type="integer",
                description="Only conversations added at or after this Unix timestamp in ms",
            ),
            "end_date": ParameterDef(
                type="integer",
                description=(
                    "Only conversations added at or before this Unix timestamp in ms"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="get_conversation",
        description=(
            "Get one conversation with its contact, assignee, unread count and "
            "inbox, starred and deleted flags."
        ),
        parameters={
            "conversation_id": ParameterDef(
                type="string",
                description="The unique identifier of the conversation to retrieve",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_conversation",
        description=(
            "Star a conversation, change its unread count, or attach a feedback "
            "object to it."
        ),
        parameters={
            "conversation_id": ParameterDef(
                type="string",
                description="The unique identifier of the conversation to update",
                required=True,
            ),
            "unread_count": ParameterDef(
                type="integer",
                description="Count of unread messages in the conversation",
            ),
            "starred": ParameterDef(
                type="boolean",
                description="Whether the conversation is starred",
            ),
            "feedback": ParameterDef(
                type="object",
                description="Feedback object to store on the conversation",
            ),
        },
    ),
    ActionDefinition(
        name="delete_conversation",
        description="Delete a conversation and its messages. This cannot be undone.",
        parameters={
            "conversation_id": ParameterDef(
                type="string",
                description="The unique identifier of the conversation to delete",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="list_conversation_messages",
        description=(
            "List the messages in a conversation, optionally restricted to "
            "certain message types, with cursor paging via last_message_id."
        ),
        parameters={
            "conversation_id": ParameterDef(
                type="string",
                description="The conversation whose messages should be listed",
                required=True,
            ),
            "limit": ParameterDef(
                type="integer",
                description="Number of messages to fetch. Default is 20",
            ),
            "last_message_id": ParameterDef(
                type="string",
                description="ID of the last message already seen, used to page forward",
            ),
            "message_types": ParameterDef(
                type="string",
                description=(
                    "Comma-separated message types to include, e.g. "
                    "TYPE_SMS,TYPE_EMAIL"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="create_email_template",
        description=(
            "Create an email-builder template or template folder in the "
            "sub-account, optionally importing it from Mailchimp, "
            "ActiveCampaign or Kajabi."
        ),
        parameters={
            "template_type": ParameterDef(
                type="string",
                description="Template type: html, folder, import, builder or blank",
                required=True,
            ),
            "name": ParameterDef(
                type="string",
                description="Name of the new template",
            ),
            "title": ParameterDef(
                type="string",
                description="Title of the new template",
            ),
            "parent_id": ParameterDef(
                type="string",
                description="ID of the folder the template belongs to",
            ),
            "builder_version": ParameterDef(
                type="string",
                description='Email builder version, "1" or "2". Defaults to 2',
            ),
            "import_provider": ParameterDef(
                type="string",
                description=(
                    "Provider to import from: mailchimp, active_campaign or "
                    'kajabi. Only used when template_type is "import"'
                ),
            ),
            "import_url": ParameterDef(
                type="string",
                description="URL to import the template from",
            ),
            "template_data_url": ParameterDef(
                type="string",
                description="URL of the template data to seed the template with",
            ),
            "template_source": ParameterDef(
                type="string",
                description="Source of the template, for example template_library",
            ),
            "is_plain_text": ParameterDef(
                type="boolean",
                description="Whether the template is plain text",
            ),
            "updated_by": ParameterDef(
                type="string",
                description="ID of the user creating the template",
            ),
        },
    ),
    ActionDefinition(
        name="list_email_templates",
        description=(
            "List the email-builder templates and folders in the sub-account, "
            "with search, folder and archive filters."
        ),
        parameters={
            "limit": ParameterDef(
                type="integer",
                description="Maximum number of templates to return",
            ),
            "offset": ParameterDef(
                type="integer",
                description="Number of templates to skip for pagination",
            ),
            "search": ParameterDef(
                type="string",
                description="Free-text search across template names",
            ),
            "name": ParameterDef(
                type="string",
                description="Filter templates by name",
            ),
            "parent_id": ParameterDef(
                type="string",
                description="Only templates inside this folder",
            ),
            "origin_id": ParameterDef(
                type="string",
                description="Filter templates by their origin ID",
            ),
            "builder_version": ParameterDef(
                type="string",
                description='Filter by email builder version, "1" or "2"',
            ),
            "sort_by_date": ParameterDef(
                type="string",
                description="Sort direction by date, asc or desc",
            ),
            "archived": ParameterDef(
                type="boolean",
                description="Whether to return archived templates",
            ),
            "templates_only": ParameterDef(
                type="boolean",
                description="Return only templates, excluding folders",
            ),
        },
    ),
    ActionDefinition(
        name="update_email_template",
        description=(
            "Save new content onto an existing email-builder template, "
            "replacing its drag-and-drop document and HTML body."
        ),
        parameters={
            "template_id": ParameterDef(
                type="string",
                description="The unique identifier of the email template to update",
                required=True,
            ),
            "updated_by": ParameterDef(
                type="string",
                description="ID of the user making the change",
                required=True,
            ),
            "html": ParameterDef(
                type="string",
                description="HTML body of the template",
                required=True,
            ),
            "editor_type": ParameterDef(
                type="string",
                description="Editor the template uses: html or builder",
                required=True,
            ),
            "dnd": ParameterDef(
                type="object",
                description=(
                    "Drag-and-drop builder document with keys elements, attrs "
                    "and templateSettings"
                ),
                required=True,
            ),
            "preview_text": ParameterDef(
                type="string",
                description="Preview text shown in the inbox",
            ),
            "is_plain_text": ParameterDef(
                type="boolean",
                description="Whether the template is plain text",
            ),
        },
    ),
    ActionDefinition(
        name="delete_email_template",
        description=(
            "Permanently delete an email-builder template. This cannot be undone."
        ),
        parameters={
            "template_id": ParameterDef(
                type="string",
                description="The unique identifier of the email template to delete",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="list_scheduled_emails",
        description=(
            "List the sub-account's scheduled email campaigns with their "
            "schedule status, delivery status and optional send statistics."
        ),
        parameters={
            "limit": ParameterDef(
                type="integer",
                description="Maximum number to return. Defaults to 10, maximum is 100",
            ),
            "offset": ParameterDef(
                type="integer",
                description="Number of entries to skip for pagination",
            ),
            "status": ParameterDef(
                type="string",
                description=(
                    "Schedule status: active, pause, complete, cancelled, "
                    "retry, draft or resend-scheduled"
                ),
            ),
            "email_status": ParameterDef(
                type="string",
                description=(
                    "Email delivery status: all, not-started, paused, "
                    "cancelled, processing, resumed, next-drip, complete, "
                    "success, error, waiting, queued, queueing, reading or "
                    "scheduled"
                ),
            ),
            "name": ParameterDef(
                type="string",
                description="Filter by name",
            ),
            "parent_id": ParameterDef(
                type="string",
                description="Only entries inside this parent folder",
            ),
            "limited_fields": ParameterDef(
                type="boolean",
                description=(
                    "Return only the essential fields instead of full campaign data"
                ),
            ),
            "archived": ParameterDef(
                type="boolean",
                description="Whether to include archived entries",
            ),
            "campaigns_only": ParameterDef(
                type="boolean",
                description="Return only campaigns, excluding folders",
            ),
            "show_stats": ParameterDef(
                type="boolean",
                description="Include delivered, opened, clicked counts and revenue",
            ),
        },
    ),
    ActionDefinition(
        name="list_calendars",
        description=(
            "List every booking calendar in the connected GoHighLevel "
            "sub-account, optionally filtered by calendar group."
        ),
        parameters={
            "group_id": ParameterDef(
                type="string",
                description="Filter calendars by a specific calendar group ID",
            ),
            "show_drafted": ParameterDef(
                type="boolean",
                description="Whether to include draft (inactive) calendars in the response",
            ),
        },
    ),
    ActionDefinition(
        name="create_calendar",
        description=(
            "Create a booking calendar (round robin, event, class, collective, "
            "service or personal) in the connected GoHighLevel sub-account."
        ),
        parameters={
            "name": ParameterDef(
                type="string", description="The name of the calendar", required=True
            ),
            "calendar_type": ParameterDef(
                type="string",
                description=(
                    "Calendar type: round_robin, event, class_booking, "
                    "collective, service_booking or personal"
                ),
            ),
            "description": ParameterDef(
                type="string", description="A description of the calendar"
            ),
            "slug": ParameterDef(type="string", description="URL slug for the booking page"),
            "widget_slug": ParameterDef(
                type="string", description="Slug for the booking widget"
            ),
            "widget_type": ParameterDef(
                type="string",
                description="Widget layout: 'default' for the neo layout, 'classic' for classic",
            ),
            "group_id": ParameterDef(type="string", description="Calendar group ID"),
            "event_type": ParameterDef(
                type="string",
                description=(
                    "Round-robin strategy: RoundRobin_OptimizeForAvailability "
                    "or RoundRobin_OptimizeForEqualDistribution"
                ),
            ),
            "event_title": ParameterDef(
                type="string",
                description="Template for the event title (supports merge fields)",
            ),
            "event_color": ParameterDef(
                type="string", description="Colour used for events"
            ),
            "is_active": ParameterDef(
                type="boolean",
                description="Whether the calendar is active (published) or a draft",
            ),
            "meeting_location": ParameterDef(
                type="string",
                description="Deprecated upstream; prefer location_configurations",
            ),
            "location_configurations": ParameterDef(
                type="array",
                description="Meeting location configurations, each with 'kind' and 'location'",
            ),
            "team_members": ParameterDef(
                type="array",
                description=(
                    "Team members assigned to the calendar; required for "
                    "round_robin, collective, class_booking and service_booking"
                ),
            ),
            "slot_duration": ParameterDef(
                type="number", description="Duration of the meeting"
            ),
            "slot_duration_unit": ParameterDef(
                type="string", description="Unit for slot duration: mins or hours"
            ),
            "slot_interval": ParameterDef(
                type="number",
                description="Time between the booking slots shown on the calendar",
            ),
            "slot_interval_unit": ParameterDef(
                type="string", description="Unit for slot interval: mins or hours"
            ),
            "slot_buffer": ParameterDef(
                type="number", description="Extra time added after an appointment"
            ),
            "slot_buffer_unit": ParameterDef(
                type="string", description="Unit for slot buffer: mins or hours"
            ),
            "pre_buffer": ParameterDef(
                type="number", description="Extra time added before an appointment"
            ),
            "pre_buffer_unit": ParameterDef(
                type="string", description="Unit for pre-buffer: mins or hours"
            ),
            "appointment_per_slot": ParameterDef(
                type="number",
                description="Maximum bookings per slot (seats per slot for class booking)",
            ),
            "appointment_per_day": ParameterDef(
                type="number",
                description="Number of appointments bookable on a given day",
            ),
            "allow_booking_after": ParameterDef(
                type="number", description="Minimum scheduling notice for events"
            ),
            "allow_booking_after_unit": ParameterDef(
                type="string",
                description="Unit for scheduling notice: hours, days, weeks or months",
            ),
            "allow_booking_for": ParameterDef(
                type="number", description="How far ahead events may be booked"
            ),
            "allow_booking_for_unit": ParameterDef(
                type="string",
                description="Unit for the booking window: days, weeks or months",
            ),
            "open_hours": ParameterDef(
                type="array",
                description="Standard availability windows; use availabilities for custom dates",
            ),
            "availabilities": ParameterDef(
                type="array",
                description="Custom date availability; use open_hours for standard hours",
            ),
            "availability_type": ParameterDef(
                type="number",
                description="1 uses only custom availabilities, 0 uses only open hours",
            ),
            "enable_recurring": ParameterDef(
                type="boolean",
                description="Enable recurring appointments on this calendar",
            ),
            "recurring": ParameterDef(
                type="object", description="Recurring appointment configuration"
            ),
            "form_id": ParameterDef(type="string", description="Custom intake form ID"),
            "sticky_contact": ParameterDef(
                type="boolean", description="Enable sticky contact"
            ),
            "is_live_payment_mode": ParameterDef(
                type="boolean", description="Whether payments are taken in live mode"
            ),
            "auto_confirm": ParameterDef(
                type="boolean",
                description="Automatically confirm bookings without manual approval",
            ),
            "should_send_alert_emails_to_assigned_member": ParameterDef(
                type="boolean",
                description="Send booking alert emails to the assigned member",
            ),
            "alert_email": ParameterDef(
                type="string", description="Email address to receive alerts"
            ),
            "google_invitation_emails": ParameterDef(
                type="boolean", description="Send Google calendar invitation emails"
            ),
            "allow_reschedule": ParameterDef(
                type="boolean", description="Allow bookers to reschedule"
            ),
            "allow_cancellation": ParameterDef(
                type="boolean", description="Allow bookers to cancel"
            ),
            "should_assign_contact_to_team_member": ParameterDef(
                type="boolean",
                description="Assign the booking contact to the team member",
            ),
            "should_skip_assigning_contact_for_existing": ParameterDef(
                type="boolean",
                description="Skip contact assignment when the contact already exists",
            ),
            "notes": ParameterDef(
                type="string", description="Internal notes about the calendar"
            ),
            "pixel_id": ParameterDef(type="string", description="Tracking pixel ID"),
            "form_submit_type": ParameterDef(
                type="string",
                description="After submit behaviour: RedirectURL or ThankYouMessage",
            ),
            "form_submit_redirect_url": ParameterDef(
                type="string",
                description="Redirect URL used when form_submit_type is RedirectURL",
            ),
            "form_submit_thanks_message": ParameterDef(
                type="string", description="Thank-you message shown after submission"
            ),
            "guest_type": ParameterDef(
                type="string", description="Guest handling: count_only or collect_detail"
            ),
            "consent_label": ParameterDef(
                type="string", description="Consent checkbox label"
            ),
            "calendar_cover_image": ParameterDef(
                type="string", description="Cover image URL"
            ),
            "look_busy_config": ParameterDef(
                type="object",
                description="Look-busy settings with 'enabled' and 'LookBusyPercentage'",
            ),
            "notifications": ParameterDef(
                type="array",
                description="Deprecated upstream; prefer the calendar notification actions",
            ),
        },
    ),
    ActionDefinition(
        name="list_appointment_notes",
        description="List the notes attached to a GoHighLevel appointment.",
        parameters={
            "appointment_id": ParameterDef(
                type="string",
                description="The unique identifier of the appointment",
                required=True,
            ),
            "limit": ParameterDef(
                type="integer", description="Number of notes to fetch", required=True
            ),
            "offset": ParameterDef(
                type="integer",
                description="Number of notes to skip before collecting results",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="create_appointment_note",
        description="Attach a free-form note to a GoHighLevel appointment.",
        parameters={
            "appointment_id": ParameterDef(
                type="string",
                description="The unique identifier of the appointment to attach the note to",
                required=True,
            ),
            "body": ParameterDef(
                type="string",
                description="Note body. Maximum length is 5000 characters",
                required=True,
            ),
            "user_id": ParameterDef(
                type="string",
                description="The unique identifier of the user creating the note",
            ),
        },
    ),
    ActionDefinition(
        name="update_appointment_note",
        description="Update the body of a note attached to a GoHighLevel appointment.",
        parameters={
            "appointment_id": ParameterDef(
                type="string",
                description="The unique identifier of the appointment",
                required=True,
            ),
            "note_id": ParameterDef(
                type="string",
                description="The unique identifier of the note to update",
                required=True,
            ),
            "body": ParameterDef(
                type="string",
                description="Note body. Maximum length is 5000 characters",
                required=True,
            ),
            "user_id": ParameterDef(
                type="string",
                description="The unique identifier of the user updating the note",
            ),
        },
    ),
    ActionDefinition(
        name="delete_appointment_note",
        description="Permanently delete a note from a GoHighLevel appointment.",
        parameters={
            "appointment_id": ParameterDef(
                type="string",
                description="The unique identifier of the appointment whose note is deleted",
                required=True,
            ),
            "note_id": ParameterDef(
                type="string",
                description="The unique identifier of the note to delete",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="list_blocked_slots",
        description=(
            "List blocked (unbookable) slots in a time range for the connected "
            "GoHighLevel sub-account."
        ),
        parameters={
            "start_time": ParameterDef(
                type="string",
                description="Start of the time range, in milliseconds since the epoch",
                required=True,
            ),
            "end_time": ParameterDef(
                type="string",
                description="End of the time range, in milliseconds since the epoch",
                required=True,
            ),
            "user_id": ParameterDef(
                type="string", description="Filter by the owning user ID"
            ),
            "calendar_id": ParameterDef(
                type="string", description="Filter by calendar ID"
            ),
            "group_id": ParameterDef(
                type="string", description="Filter by calendar group ID"
            ),
        },
    ),
    ActionDefinition(
        name="list_calendar_events",
        description=(
            "List calendar events (appointments) in a time range for the "
            "connected GoHighLevel sub-account."
        ),
        parameters={
            "start_time": ParameterDef(
                type="string",
                description="Start of the time range, in milliseconds since the epoch",
                required=True,
            ),
            "end_time": ParameterDef(
                type="string",
                description="End of the time range, in milliseconds since the epoch",
                required=True,
            ),
            "user_id": ParameterDef(
                type="string", description="Filter by the owning user ID"
            ),
            "calendar_id": ParameterDef(
                type="string", description="Filter by calendar ID"
            ),
            "group_id": ParameterDef(
                type="string", description="Filter by calendar group ID"
            ),
        },
    ),
    ActionDefinition(
        name="create_appointment",
        description="Book a contact onto a GoHighLevel calendar as a new appointment.",
        parameters={
            "calendar_id": ParameterDef(
                type="string",
                description="The calendar the appointment is booked on",
                required=True,
            ),
            "contact_id": ParameterDef(
                type="string",
                description="The contact the appointment is booked for",
                required=True,
            ),
            "start_time": ParameterDef(
                type="string",
                description="ISO 8601 start time of the appointment",
                required=True,
            ),
            "end_time": ParameterDef(
                type="string", description="ISO 8601 end time of the appointment"
            ),
            "title": ParameterDef(
                type="string", description="The title of the appointment"
            ),
            "appointment_status": ParameterDef(
                type="string",
                description="One of: new, confirmed, cancelled, showed, noshow, invalid",
            ),
            "assigned_user_id": ParameterDef(
                type="string", description="The user the appointment is assigned to"
            ),
            "address": ParameterDef(
                type="string", description="The address of the appointment"
            ),
            "description": ParameterDef(
                type="string", description="The description of the appointment"
            ),
            "meeting_location_type": ParameterDef(
                type="string",
                description="One of: custom, zoom, gmeet, phone, address, ms_teams, google",
            ),
            "meeting_location_id": ParameterDef(
                type="string",
                description="Meeting location ID from calendar.locationConfigurations",
            ),
            "override_location_config": ParameterDef(
                type="boolean",
                description="Override the calendar's meeting location configuration",
            ),
            "ignore_date_range": ParameterDef(
                type="boolean",
                description="Ignore the minimum scheduling notice and date range",
            ),
            "to_notify": ParameterDef(
                type="boolean",
                description="If false, automations will not run for this appointment",
            ),
            "ignore_free_slot_validation": ParameterDef(
                type="boolean", description="Skip the free-slot validation when booking"
            ),
            "rrule": ParameterDef(
                type="string",
                description="iCalendar (RFC 5545) RRULE for a recurring appointment",
            ),
        },
    ),
    ActionDefinition(
        name="update_appointment",
        description=(
            "Update an existing GoHighLevel appointment — time, status, location "
            "or assignment. Only the fields supplied are changed."
        ),
        parameters={
            "event_id": ParameterDef(
                type="string",
                description=(
                    "The appointment event ID. For a recurring series send the "
                    "masterEventId to modify the original series"
                ),
                required=True,
            ),
            "calendar_id": ParameterDef(
                type="string", description="Move the appointment to this calendar"
            ),
            "start_time": ParameterDef(type="string", description="ISO 8601 start time"),
            "end_time": ParameterDef(type="string", description="ISO 8601 end time"),
            "title": ParameterDef(
                type="string", description="The title of the appointment"
            ),
            "appointment_status": ParameterDef(
                type="string",
                description="One of: new, confirmed, cancelled, showed, noshow, invalid",
            ),
            "assigned_user_id": ParameterDef(
                type="string", description="The user the appointment is assigned to"
            ),
            "address": ParameterDef(
                type="string", description="The address of the appointment"
            ),
            "description": ParameterDef(
                type="string", description="The description of the appointment"
            ),
            "meeting_location_type": ParameterDef(
                type="string",
                description="One of: custom, zoom, gmeet, phone, address, ms_teams, google",
            ),
            "meeting_location_id": ParameterDef(
                type="string",
                description="Meeting location ID from calendar.locationConfigurations",
            ),
            "override_location_config": ParameterDef(
                type="boolean",
                description="Override the calendar's meeting location configuration",
            ),
            "ignore_date_range": ParameterDef(
                type="boolean",
                description="Ignore the minimum scheduling notice and date range",
            ),
            "to_notify": ParameterDef(
                type="boolean",
                description="If false, automations will not run for this appointment",
            ),
            "ignore_free_slot_validation": ParameterDef(
                type="boolean",
                description="Skip the free-slot validation when rescheduling",
            ),
            "rrule": ParameterDef(
                type="string",
                description="iCalendar (RFC 5545) RRULE for a recurring appointment",
            ),
        },
    ),
    ActionDefinition(
        name="get_appointment",
        description="Fetch one GoHighLevel appointment by its event ID.",
        parameters={
            "event_id": ParameterDef(
                type="string",
                description="The appointment event ID, or the instance ID of a recurring series",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="create_block_slot",
        description=(
            "Reserve time on a GoHighLevel calendar or user so it is "
            "unavailable for booking."
        ),
        parameters={
            "start_time": ParameterDef(type="string", description="ISO 8601 start time"),
            "end_time": ParameterDef(type="string", description="ISO 8601 end time"),
            "title": ParameterDef(type="string", description="Title of the block slot"),
            "calendar_id": ParameterDef(
                type="string",
                description="Calendar to block. Set either calendar_id or assigned_user_id",
            ),
            "assigned_user_id": ParameterDef(
                type="string",
                description="User to block. Set either calendar_id or assigned_user_id",
            ),
        },
    ),
    ActionDefinition(
        name="update_block_slot",
        description="Update the time, title or owner of a GoHighLevel block slot.",
        parameters={
            "event_id": ParameterDef(
                type="string",
                description="The unique identifier of the block slot to update",
                required=True,
            ),
            "start_time": ParameterDef(type="string", description="ISO 8601 start time"),
            "end_time": ParameterDef(type="string", description="ISO 8601 end time"),
            "title": ParameterDef(type="string", description="Title of the block slot"),
            "calendar_id": ParameterDef(
                type="string",
                description="Calendar to block. Set either calendar_id or assigned_user_id",
            ),
            "assigned_user_id": ParameterDef(
                type="string",
                description="User to block. Set either calendar_id or assigned_user_id",
            ),
        },
    ),
    ActionDefinition(
        name="delete_event",
        description="Delete a GoHighLevel calendar event — an appointment or a block slot.",
        parameters={
            "event_id": ParameterDef(
                type="string",
                description="The event ID of the appointment or block slot to delete",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="list_calendar_groups",
        description="List every calendar group in the connected GoHighLevel sub-account.",
        parameters={},
    ),
    ActionDefinition(
        name="create_calendar_group",
        description=(
            "Create a calendar group that organises related calendars under a "
            "shared name and slug."
        ),
        parameters={
            "name": ParameterDef(
                type="string",
                description="The name of the calendar group",
                required=True,
            ),
            "description": ParameterDef(
                type="string",
                description="A description of the calendar group",
                required=True,
            ),
            "slug": ParameterDef(
                type="string",
                description="The URL-friendly slug identifying the calendar group",
                required=True,
            ),
            "is_active": ParameterDef(
                type="boolean", description="Whether the calendar group is active"
            ),
        },
    ),
    ActionDefinition(
        name="validate_calendar_group_slug",
        description=(
            "Check whether a calendar group slug is still available in the "
            "sub-account before creating or renaming a group."
        ),
        parameters={
            "slug": ParameterDef(
                type="string",
                description="The slug to validate for availability in the sub-account",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="delete_calendar_group",
        description="Permanently delete a GoHighLevel calendar group.",
        parameters={
            "group_id": ParameterDef(
                type="string",
                description="The unique identifier of the calendar group to delete",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_calendar_group",
        description="Rename a GoHighLevel calendar group or change its description and slug.",
        parameters={
            "group_id": ParameterDef(
                type="string",
                description="The unique identifier of the calendar group to edit",
                required=True,
            ),
            "name": ParameterDef(
                type="string",
                description="The name of the calendar group",
                required=True,
            ),
            "description": ParameterDef(
                type="string",
                description="The description of the calendar group",
                required=True,
            ),
            "slug": ParameterDef(
                type="string",
                description="The URL slug of the calendar group",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="set_calendar_group_status",
        description="Enable or disable a GoHighLevel calendar group.",
        parameters={
            "group_id": ParameterDef(
                type="string",
                description="The unique identifier of the calendar group to enable or disable",
                required=True,
            ),
            "is_active": ParameterDef(
                type="boolean",
                description="True to enable the calendar group, false to disable it",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="list_calendar_resources",
        description=(
            "List the bookable rooms or equipment available for service "
            "calendars in the connected GoHighLevel sub-account."
        ),
        parameters={
            "resource_type": ParameterDef(
                type="string",
                description="The resource type to list: 'equipments' or 'rooms'",
                required=True,
            ),
            "limit": ParameterDef(
                type="integer",
                description="Maximum number of resources to return per page",
                required=True,
            ),
            "skip": ParameterDef(
                type="integer",
                description="Number of resources to skip before collecting results",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="create_calendar_resource",
        description="Create a bookable room or piece of equipment for service calendars.",
        parameters={
            "resource_type": ParameterDef(
                type="string",
                description="The resource type to create: 'equipments' or 'rooms'",
                required=True,
            ),
            "name": ParameterDef(
                type="string", description="Name of the resource", required=True
            ),
            "description": ParameterDef(
                type="string", description="Description of the resource", required=True
            ),
            "quantity": ParameterDef(
                type="number", description="Quantity of the equipment", required=True
            ),
            "out_of_service": ParameterDef(
                type="number",
                description="Quantity of the equipment out of service",
                required=True,
            ),
            "capacity": ParameterDef(
                type="number", description="Capacity of the room", required=True
            ),
            "calendar_ids": ParameterDef(
                type="array",
                description="Service calendar IDs the resource is mapped to",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="get_calendar_resource",
        description="Fetch one bookable room or piece of equipment by its ID.",
        parameters={
            "resource_type": ParameterDef(
                type="string",
                description="The resource type: 'equipments' or 'rooms'",
                required=True,
            ),
            "resource_id": ParameterDef(
                type="string",
                description="The unique identifier of the calendar resource",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_calendar_resource",
        description=(
            "Update a bookable room or piece of equipment. Only the fields "
            "supplied are changed."
        ),
        parameters={
            "resource_type": ParameterDef(
                type="string",
                description="The resource type: 'equipments' or 'rooms'",
                required=True,
            ),
            "resource_id": ParameterDef(
                type="string",
                description="The unique identifier of the calendar resource",
                required=True,
            ),
            "name": ParameterDef(type="string", description="Name of the resource"),
            "description": ParameterDef(
                type="string", description="Description of the resource"
            ),
            "quantity": ParameterDef(
                type="number", description="Quantity of the equipment"
            ),
            "out_of_service": ParameterDef(
                type="number", description="Quantity of the equipment out of service"
            ),
            "capacity": ParameterDef(type="number", description="Capacity of the room"),
            "calendar_ids": ParameterDef(
                type="array",
                description="Service calendar IDs the resource is mapped to",
            ),
            "is_active": ParameterDef(
                type="boolean", description="Whether the resource is active"
            ),
        },
    ),
    ActionDefinition(
        name="delete_calendar_resource",
        description="Permanently delete a bookable room or piece of equipment.",
        parameters={
            "resource_type": ParameterDef(
                type="string",
                description="The resource type: 'equipments' or 'rooms'",
                required=True,
            ),
            "resource_id": ParameterDef(
                type="string",
                description="The unique identifier of the calendar resource to delete",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="create_availability_schedule",
        description=(
            "Create a user availability schedule — the working hours and date "
            "rules GoHighLevel calendars book against."
        ),
        parameters={
            "name": ParameterDef(
                type="string",
                description="Human-readable name for the schedule",
                required=True,
            ),
            "user_id": ParameterDef(
                type="string",
                description="User ID the schedule belongs to",
                required=True,
            ),
            "timezone": ParameterDef(
                type="string",
                description="IANA timezone identifier, e.g. America/New_York",
                required=True,
            ),
            "rules": ParameterDef(
                type="array",
                description=(
                    "Availability rules, each with 'type' (wday or date), "
                    "'intervals' of {from,to} in HH:MM, plus 'day' or 'date'"
                ),
            ),
            "calendar_ids": ParameterDef(
                type="array", description="Calendar IDs the schedule applies to"
            ),
        },
    ),
    ActionDefinition(
        name="list_availability_schedules",
        description="List the availability schedules configured for a GoHighLevel user.",
        parameters={
            "user_id": ParameterDef(
                type="string",
                description="User ID whose schedules are fetched",
                required=True,
            ),
            "calendar_id": ParameterDef(
                type="string",
                description="Only return schedules linked to this calendar",
            ),
            "skip": ParameterDef(
                type="integer", description="Number of schedules to skip"
            ),
            "limit": ParameterDef(
                type="integer",
                description="Maximum number of schedules to return (max 500)",
            ),
        },
    ),
    ActionDefinition(
        name="get_availability_schedule",
        description="Fetch one GoHighLevel user availability schedule by its ID.",
        parameters={
            "schedule_id": ParameterDef(
                type="string",
                description="The unique identifier of the schedule",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_availability_schedule",
        description=(
            "Update a user availability schedule's name, timezone or rules. "
            "Only the fields supplied are changed."
        ),
        parameters={
            "schedule_id": ParameterDef(
                type="string",
                description="The unique identifier of the schedule to update",
                required=True,
            ),
            "name": ParameterDef(
                type="string", description="Human-readable name for the schedule"
            ),
            "timezone": ParameterDef(
                type="string",
                description="IANA timezone identifier, e.g. America/New_York",
            ),
            "rules": ParameterDef(
                type="array",
                description=(
                    "Availability rules, each with 'type' (wday or date), "
                    "'intervals' of {from,to} in HH:MM, plus 'day' or 'date'"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="delete_availability_schedule",
        description="Permanently delete a GoHighLevel user availability schedule.",
        parameters={
            "schedule_id": ParameterDef(
                type="string",
                description="The unique identifier of the schedule to delete",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="attach_schedule_to_calendar",
        description="Apply a user availability schedule to a GoHighLevel team calendar.",
        parameters={
            "schedule_id": ParameterDef(
                type="string",
                description="The unique identifier of the schedule",
                required=True,
            ),
            "calendar_id": ParameterDef(
                type="string",
                description="The unique identifier of the team calendar to add to the schedule",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="detach_schedule_from_calendar",
        description="Remove a user availability schedule from a GoHighLevel calendar.",
        parameters={
            "schedule_id": ParameterDef(
                type="string",
                description="The unique identifier of the schedule",
                required=True,
            ),
            "calendar_id": ParameterDef(
                type="string",
                description="The unique identifier of the calendar to remove from the schedule",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_calendar",
        description=(
            "Update a GoHighLevel booking calendar's settings, availability or "
            "team members. Only the fields supplied are changed."
        ),
        parameters={
            "calendar_id": ParameterDef(
                type="string",
                description="The unique identifier of the calendar to update",
                required=True,
            ),
            "name": ParameterDef(type="string", description="The name of the calendar"),
            "description": ParameterDef(
                type="string", description="A description of the calendar"
            ),
            "slug": ParameterDef(type="string", description="URL slug for the booking page"),
            "widget_slug": ParameterDef(
                type="string", description="Slug for the booking widget"
            ),
            "widget_type": ParameterDef(
                type="string",
                description="Widget layout: 'default' for the neo layout, 'classic' for classic",
            ),
            "group_id": ParameterDef(type="string", description="Calendar group ID"),
            "event_type": ParameterDef(
                type="string",
                description=(
                    "Round-robin strategy: RoundRobin_OptimizeForAvailability "
                    "or RoundRobin_OptimizeForEqualDistribution"
                ),
            ),
            "event_title": ParameterDef(
                type="string",
                description="Template for the event title (supports merge fields)",
            ),
            "event_color": ParameterDef(
                type="string", description="Colour used for events"
            ),
            "is_active": ParameterDef(
                type="boolean",
                description="Whether the calendar is active (published) or a draft",
            ),
            "meeting_location": ParameterDef(
                type="string",
                description="Deprecated upstream; prefer location_configurations",
            ),
            "location_configurations": ParameterDef(
                type="array",
                description="Meeting location configurations, each with 'kind' and 'location'",
            ),
            "team_members": ParameterDef(
                type="array",
                description=(
                    "Team members assigned to the calendar; required for "
                    "round_robin, collective, class_booking and service_booking"
                ),
            ),
            "slot_duration": ParameterDef(
                type="number", description="Duration of the meeting"
            ),
            "slot_duration_unit": ParameterDef(
                type="string", description="Unit for slot duration: mins or hours"
            ),
            "slot_interval": ParameterDef(
                type="number",
                description="Time between the booking slots shown on the calendar",
            ),
            "slot_interval_unit": ParameterDef(
                type="string", description="Unit for slot interval: mins or hours"
            ),
            "slot_buffer": ParameterDef(
                type="number", description="Extra time added after an appointment"
            ),
            "pre_buffer": ParameterDef(
                type="number", description="Extra time added before an appointment"
            ),
            "pre_buffer_unit": ParameterDef(
                type="string", description="Unit for pre-buffer: mins or hours"
            ),
            "appointment_per_slot": ParameterDef(
                type="number",
                description="Maximum bookings per slot (seats per slot for class booking)",
            ),
            "appointment_per_day": ParameterDef(
                type="number",
                description="Number of appointments bookable on a given day",
            ),
            "allow_booking_after": ParameterDef(
                type="number", description="Minimum scheduling notice for events"
            ),
            "allow_booking_after_unit": ParameterDef(
                type="string",
                description="Unit for scheduling notice: hours, days, weeks or months",
            ),
            "allow_booking_for": ParameterDef(
                type="number", description="How far ahead events may be booked"
            ),
            "allow_booking_for_unit": ParameterDef(
                type="string",
                description="Unit for the booking window: days, weeks or months",
            ),
            "open_hours": ParameterDef(
                type="array",
                description="Standard availability windows; use availabilities for custom dates",
            ),
            "availabilities": ParameterDef(
                type="array",
                description=(
                    "Custom date availability; include the entry 'id' to modify "
                    "or delete an existing custom date"
                ),
            ),
            "availability_type": ParameterDef(
                type="number",
                description="1 uses only custom availabilities, 0 uses only open hours",
            ),
            "enable_recurring": ParameterDef(
                type="boolean",
                description="Enable recurring appointments on this calendar",
            ),
            "recurring": ParameterDef(
                type="object", description="Recurring appointment configuration"
            ),
            "form_id": ParameterDef(type="string", description="Custom intake form ID"),
            "sticky_contact": ParameterDef(
                type="boolean", description="Enable sticky contact"
            ),
            "is_live_payment_mode": ParameterDef(
                type="boolean", description="Whether payments are taken in live mode"
            ),
            "auto_confirm": ParameterDef(
                type="boolean",
                description="Automatically confirm bookings without manual approval",
            ),
            "should_send_alert_emails_to_assigned_member": ParameterDef(
                type="boolean",
                description="Send booking alert emails to the assigned member",
            ),
            "alert_email": ParameterDef(
                type="string", description="Email address to receive alerts"
            ),
            "google_invitation_emails": ParameterDef(
                type="boolean", description="Send Google calendar invitation emails"
            ),
            "allow_reschedule": ParameterDef(
                type="boolean", description="Allow bookers to reschedule"
            ),
            "allow_cancellation": ParameterDef(
                type="boolean", description="Allow bookers to cancel"
            ),
            "should_assign_contact_to_team_member": ParameterDef(
                type="boolean",
                description="Assign the booking contact to the team member",
            ),
            "should_skip_assigning_contact_for_existing": ParameterDef(
                type="boolean",
                description="Skip contact assignment when the contact already exists",
            ),
            "notes": ParameterDef(
                type="string", description="Internal notes about the calendar"
            ),
            "pixel_id": ParameterDef(type="string", description="Tracking pixel ID"),
            "form_submit_type": ParameterDef(
                type="string",
                description="After submit behaviour: RedirectURL or ThankYouMessage",
            ),
            "form_submit_redirect_url": ParameterDef(
                type="string",
                description="Redirect URL used when form_submit_type is RedirectURL",
            ),
            "form_submit_thanks_message": ParameterDef(
                type="string", description="Thank-you message shown after submission"
            ),
            "guest_type": ParameterDef(
                type="string", description="Guest handling: count_only or collect_detail"
            ),
            "consent_label": ParameterDef(
                type="string", description="Consent checkbox label"
            ),
            "calendar_cover_image": ParameterDef(
                type="string", description="Cover image URL"
            ),
            "look_busy_config": ParameterDef(
                type="object",
                description="Look-busy settings with 'enabled' and 'LookBusyPercentage'",
            ),
            "notifications": ParameterDef(
                type="array",
                description="Deprecated upstream; prefer the calendar notification actions",
            ),
        },
    ),
    ActionDefinition(
        name="get_calendar",
        description="Fetch the full configuration of one GoHighLevel booking calendar.",
        parameters={
            "calendar_id": ParameterDef(
                type="string",
                description="The unique identifier of the calendar to retrieve",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="delete_calendar",
        description="Permanently delete a GoHighLevel booking calendar.",
        parameters={
            "calendar_id": ParameterDef(
                type="string",
                description="The unique identifier of the calendar to delete",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="get_calendar_free_slots",
        description=(
            "Find the bookable free slots on a GoHighLevel calendar within a "
            "date range, grouped by day."
        ),
        parameters={
            "calendar_id": ParameterDef(
                type="string",
                description="The calendar to read free slots from",
                required=True,
            ),
            "start_date": ParameterDef(
                type="integer",
                description="Start of the range, epoch milliseconds. Range must be 31 days or less",
                required=True,
            ),
            "end_date": ParameterDef(
                type="integer",
                description="End of the range, epoch milliseconds. Range must be 31 days or less",
                required=True,
            ),
            "timezone": ParameterDef(
                type="string", description="Timezone the free slots are returned in"
            ),
            "user_id": ParameterDef(
                type="string", description="Return free slots for this single user"
            ),
            "user_ids": ParameterDef(
                type="array", description="Return free slots for these users"
            ),
        },
    ),
    ActionDefinition(
        name="list_calendar_notifications",
        description="List the notification rules configured on a GoHighLevel calendar.",
        parameters={
            "calendar_id": ParameterDef(
                type="string",
                description="The calendar whose notifications are listed",
                required=True,
            ),
            "is_active": ParameterDef(
                type="boolean",
                description="Filter notifications by their active status",
            ),
            "deleted": ParameterDef(
                type="boolean",
                description="Filter notifications by their deleted status",
            ),
            "limit": ParameterDef(
                type="integer",
                description="Maximum number of notifications to return",
            ),
            "skip": ParameterDef(
                type="integer", description="Number of notifications to skip"
            ),
        },
    ),
    ActionDefinition(
        name="create_calendar_notification",
        description=(
            "Create one or more notification rules on a GoHighLevel calendar — "
            "booking confirmations, reminders or follow-ups across email, SMS, "
            "in-app and WhatsApp."
        ),
        parameters={
            "calendar_id": ParameterDef(
                type="string",
                description="The calendar to create notifications for",
                required=True,
            ),
            "notifications": ParameterDef(
                type="array",
                description=(
                    "Notification configurations. Each entry needs "
                    "'receiverType' (contact, guest, assignedUser, emails, "
                    "phoneNumbers, business), 'channel' (email, inApp, sms, "
                    "whatsapp) and 'notificationType' (booked, confirmation, "
                    "cancellation, reminder, followup, reschedule)"
                ),
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="get_calendar_notification",
        description="Fetch one notification rule from a GoHighLevel calendar.",
        parameters={
            "calendar_id": ParameterDef(
                type="string",
                description="The calendar that owns the notification",
                required=True,
            ),
            "notification_id": ParameterDef(
                type="string",
                description="The unique identifier of the notification",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_calendar_notification",
        description=(
            "Update one notification rule on a GoHighLevel calendar. Only the "
            "fields supplied are changed."
        ),
        parameters={
            "calendar_id": ParameterDef(
                type="string",
                description="The calendar that owns the notification",
                required=True,
            ),
            "notification_id": ParameterDef(
                type="string",
                description="The unique identifier of the notification to update",
                required=True,
            ),
            "receiver_type": ParameterDef(
                type="string",
                description=(
                    "Recipient type: contact, guest, assignedUser, emails, "
                    "phoneNumbers or business"
                ),
            ),
            "channel": ParameterDef(
                type="string",
                description="Notification channel: email, inApp, sms or whatsapp",
            ),
            "notification_type": ParameterDef(
                type="string",
                description=(
                    "Notification type: booked, confirmation, cancellation, "
                    "reminder, followup or reschedule"
                ),
            ),
            "is_active": ParameterDef(
                type="boolean", description="Whether the rule is active"
            ),
            "deleted": ParameterDef(
                type="boolean",
                description="Marks the notification as deleted (soft delete)",
            ),
            "template_id": ParameterDef(
                type="string", description="Template ID for an email notification"
            ),
            "body": ParameterDef(
                type="string", description="Body for an email notification"
            ),
            "subject": ParameterDef(
                type="string", description="Subject for an email notification"
            ),
            "before_time": ParameterDef(
                type="array",
                description="Reminder offsets before the event, each {timeOffset, unit}",
            ),
            "after_time": ParameterDef(
                type="array",
                description="Follow-up offsets after the event, each {timeOffset, unit}",
            ),
            "additional_email_ids": ParameterDef(
                type="array", description="Extra email addresses to notify"
            ),
            "additional_phone_numbers": ParameterDef(
                type="array", description="Extra phone numbers to notify"
            ),
            "selected_users": ParameterDef(
                type="array",
                description="User IDs for in-App and business email notifications",
            ),
            "from_address": ParameterDef(
                type="string", description="From address for an email notification"
            ),
            "from_name": ParameterDef(
                type="string", description="From name for an email or SMS notification"
            ),
            "from_number": ParameterDef(
                type="string", description="From number for an SMS notification"
            ),
        },
    ),
    ActionDefinition(
        name="delete_calendar_notification",
        description="Permanently delete a notification rule from a GoHighLevel calendar.",
        parameters={
            "calendar_id": ParameterDef(
                type="string",
                description="The calendar that owns the notification",
                required=True,
            ),
            "notification_id": ParameterDef(
                type="string",
                description="The unique identifier of the notification to delete",
                required=True,
            ),
        },
    ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description=(
                "Connect a GoHighLevel sub-account through a Marketplace app"
            ),
            setup_instructions=[
                "Sign in to the GoHighLevel Marketplace at "
                "https://marketplace.gohighlevel.com and open My Apps",
                "Create an app (or open an existing one) and add a Sub-Account "
                "(Location) distribution type",
                "Under Redirect URLs, add your ModuleX OAuth callback URL",
                "Under Scopes, select every scope this integration requests — "
                "the connect flow fails if the app grants fewer than it asks for",
                "Copy the Client ID and Client Secret into the fields below",
                "Open Settings -> Business Profile in the sub-account you want to "
                "automate and copy its Location ID into the field below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="GOHIGHLEVEL_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Client ID of your GoHighLevel Marketplace app",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://marketplace.gohighlevel.com",
                ),
                EnvVar(
                    name="GOHIGHLEVEL_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Client Secret of your GoHighLevel Marketplace app",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://marketplace.gohighlevel.com",
                ),
                EnvVar(
                    name="GOHIGHLEVEL_LOCATION_ID",
                    display_name="Location ID",
                    description=(
                        "ID of the GoHighLevel sub-account (location) to work in. "
                        "Found under Settings -> Business Profile, and returned as "
                        "locationId when the OAuth token is issued."
                    ),
                    required=True,
                    sensitive=False,
                    # Per-credential user input: every sub-account has its own
                    # ID, so it cannot be a server global. The runtime persists
                    # the user-entered value into auth_data at credential
                    # creation; tools.py reads it as auth_data["location_id"].
                    only_for_custom=False,
                    inject_into_auth_data=True,
                    sample_format="ve9EPM428h8vShlRW1KT",
                    about_url="https://highlevel.stoplight.io/docs/integrations",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://marketplace.gohighlevel.com/v2/oauth/chooselocation",
                token_url="https://services.leadconnectorhq.com/oauth/token",
                scopes=_SCOPES,
                # GoHighLevel's token endpoint takes client_id/client_secret as
                # form fields (application/x-www-form-urlencoded), not as an
                # Authorization: Basic header.
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://services.leadconnectorhq.com/contacts/",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                    "Version": "2021-07-28",
                    "Accept": "application/json",
                },
                params={"locationId": "{location_id}", "limit": "1"},
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description=(
                    "Reads one contact from the configured sub-account to prove "
                    "the token and location ID work together"
                ),
            ),
        ),
    ],
)

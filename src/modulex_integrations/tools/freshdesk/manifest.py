"""Freshdesk integration manifest."""
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
    name="freshdesk",
    display_name="Freshdesk",
    description="Customer support helpdesk platform for managing tickets, contacts, agents, and knowledge base articles via the Freshdesk REST API.",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:freshdesk-themed",
    app_url="https://freshdesk.com",
    categories=["Customer Support", "Helpdesk", "Productivity & Collaboration"],
    actions=[
        ActionDefinition(
            name="create_ticket",
            description="Create a new support ticket in Freshdesk",
            parameters={
                "subject": ParameterDef(
                    type="string",
                    description="Subject of the ticket",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string",
                    description="HTML content of the ticket",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="Email address of the requester",
                    required=True,
                ),
                "priority": ParameterDef(
                    type="integer",
                    description="Priority of the ticket: 1 (Low), 2 (Medium), 3 (High), 4 (Urgent)",
                    default=1,
                ),
                "status": ParameterDef(
                    type="integer",
                    description="Status of the ticket: 2 (Open), 3 (Pending), 4 (Resolved), 5 (Closed)",
                    default=2,
                ),
                "company_id": ParameterDef(
                    type="integer",
                    description="ID of the company to associate with the ticket",
                ),
            },
        ),
        ActionDefinition(
            name="get_ticket",
            description="Retrieve a specific ticket by its ID",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_ticket",
            description="Update an existing ticket's properties",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket to update",
                    required=True,
                ),
                "subject": ParameterDef(
                    type="string",
                    description="New subject for the ticket",
                ),
                "description": ParameterDef(
                    type="string",
                    description="New HTML content for the ticket",
                ),
                "priority": ParameterDef(
                    type="integer",
                    description="Priority: 1 (Low), 2 (Medium), 3 (High), 4 (Urgent)",
                ),
                "status": ParameterDef(
                    type="integer",
                    description="Status: 2 (Open), 3 (Pending), 4 (Resolved), 5 (Closed)",
                ),
                "group_id": ParameterDef(
                    type="integer",
                    description="ID of the group to assign the ticket to",
                ),
                "responder_id": ParameterDef(
                    type="integer",
                    description="ID of the agent to assign the ticket to",
                ),
            },
        ),
        ActionDefinition(
            name="list_all_tickets",
            description="List tickets in Freshdesk with optional filtering",
            parameters={
                "filter": ParameterDef(
                    type="string",
                    description="Predefined filter: new_and_my_open, watching, spam, deleted, all_tickets",
                ),
                "requester_id": ParameterDef(
                    type="integer",
                    description="Filter tickets by requester ID",
                ),
                "email": ParameterDef(
                    type="string",
                    description="Filter tickets by requester email",
                ),
                "company_id": ParameterDef(
                    type="integer",
                    description="Filter tickets by company ID",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="close_ticket",
            description="Close a ticket by setting its status to Closed (5)",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket to close",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="add_note_to_ticket",
            description="Add a private or public note to a ticket",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket to add a note to",
                    required=True,
                ),
                "body": ParameterDef(
                    type="string",
                    description="Content of the note in HTML format",
                    required=True,
                ),
                "private": ParameterDef(
                    type="boolean",
                    description="Whether the note is private (true) or public (false)",
                    default=True,
                ),
                "notify_emails": ParameterDef(
                    type="array",
                    description="List of email addresses to notify about this note",
                ),
            },
        ),
        ActionDefinition(
            name="add_ticket_tags",
            description="Add tags to an existing ticket",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket",
                    required=True,
                ),
                "tags": ParameterDef(
                    type="array",
                    description="List of tag names to add to the ticket",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="remove_ticket_tags",
            description="Remove tags from an existing ticket",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket",
                    required=True,
                ),
                "tags": ParameterDef(
                    type="array",
                    description="List of tag names to remove from the ticket",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="set_ticket_tags",
            description="Replace all tags on a ticket with the specified set",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket",
                    required=True,
                ),
                "tags": ParameterDef(
                    type="array",
                    description="List of tag names to set on the ticket (replaces existing tags)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="set_ticket_priority",
            description="Set the priority of a ticket",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket",
                    required=True,
                ),
                "priority": ParameterDef(
                    type="integer",
                    description="Priority: 1 (Low), 2 (Medium), 3 (High), 4 (Urgent)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="set_ticket_status",
            description="Set the status of a ticket",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket",
                    required=True,
                ),
                "status": ParameterDef(
                    type="integer",
                    description="Status: 2 (Open), 3 (Pending), 4 (Resolved), 5 (Closed)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="assign_ticket_to_agent",
            description="Assign a ticket to a specific agent",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket",
                    required=True,
                ),
                "agent_id": ParameterDef(
                    type="integer",
                    description="ID of the agent to assign the ticket to",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="assign_ticket_to_group",
            description="Assign a ticket to a specific group",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket",
                    required=True,
                ),
                "group_id": ParameterDef(
                    type="integer",
                    description="ID of the group to assign the ticket to",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_contact",
            description="Create a new contact in Freshdesk",
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="Email address of the contact",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Name of the contact",
                    required=True,
                ),
                "phone": ParameterDef(
                    type="string",
                    description="Phone number of the contact",
                ),
                "company_id": ParameterDef(
                    type="integer",
                    description="ID of the company to associate with the contact",
                ),
            },
        ),
        ActionDefinition(
            name="get_contact",
            description="Retrieve a contact by their ID",
            parameters={
                "contact_id": ParameterDef(
                    type="integer",
                    description="ID of the contact to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_contact",
            description="Update an existing contact's properties",
            parameters={
                "contact_id": ParameterDef(
                    type="integer",
                    description="ID of the contact to update",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Updated name of the contact",
                ),
                "email": ParameterDef(
                    type="string",
                    description="Updated email address",
                ),
                "phone": ParameterDef(
                    type="string",
                    description="Updated phone number",
                ),
                "company_id": ParameterDef(
                    type="integer",
                    description="ID of the company to associate with the contact",
                ),
            },
        ),
        ActionDefinition(
            name="create_company",
            description="Create a new company in Freshdesk",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Name of the company",
                    required=True,
                ),
                "domains": ParameterDef(
                    type="array",
                    description="List of domain names associated with the company (e.g. ['example.com'])",
                ),
                "description": ParameterDef(
                    type="string",
                    description="Description of the company",
                ),
            },
        ),
        ActionDefinition(
            name="create_agent",
            description="Create a new agent in Freshdesk",
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="Email address of the agent",
                    required=True,
                ),
                "ticket_scope": ParameterDef(
                    type="integer",
                    description="Ticket permission: 1 (Global Access), 2 (Group Access), 3 (Restricted Access)",
                    required=True,
                ),
                "occasional": ParameterDef(
                    type="boolean",
                    description="Set to true if this is an occasional agent",
                ),
                "agent_type": ParameterDef(
                    type="integer",
                    description="Type: 1 (Support Agent), 2 (Field Agent), 3 (Collaborator)",
                ),
            },
        ),
        ActionDefinition(
            name="update_agent",
            description="Update an existing agent's properties",
            parameters={
                "agent_id": ParameterDef(
                    type="integer",
                    description="ID of the agent to update",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="Updated email address",
                ),
                "ticket_scope": ParameterDef(
                    type="integer",
                    description="Ticket permission: 1 (Global Access), 2 (Group Access), 3 (Restricted Access)",
                ),
                "occasional": ParameterDef(
                    type="boolean",
                    description="Set to true if this is an occasional agent",
                ),
            },
        ),
        ActionDefinition(
            name="get_agent",
            description="Retrieve a single agent by their ID",
            parameters={
                "agent_id": ParameterDef(
                    type="integer",
                    description="ID of the agent to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_agents",
            description="List all agents in Freshdesk with optional filtering",
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="Filter agents by email address",
                ),
                "state": ParameterDef(
                    type="string",
                    description="Filter by state: fulltime, occasional",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="create_reply",
            description="Create a reply to a ticket",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket to reply to",
                    required=True,
                ),
                "body": ParameterDef(
                    type="string",
                    description="Content of the reply in HTML format",
                    required=True,
                ),
                "cc_emails": ParameterDef(
                    type="array",
                    description="List of email addresses to CC",
                ),
                "bcc_emails": ParameterDef(
                    type="array",
                    description="List of email addresses to BCC",
                ),
            },
        ),
        ActionDefinition(
            name="forward_ticket",
            description="Forward a ticket to an external email address",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket to forward",
                    required=True,
                ),
                "body": ParameterDef(
                    type="string",
                    description="Content of the forward in HTML format",
                    required=True,
                ),
                "to_emails": ParameterDef(
                    type="array",
                    description="List of email addresses to forward to",
                    required=True,
                ),
                "cc_emails": ParameterDef(
                    type="array",
                    description="List of email addresses to CC",
                ),
                "bcc_emails": ParameterDef(
                    type="array",
                    description="List of email addresses to BCC",
                ),
            },
        ),
        ActionDefinition(
            name="reply_to_forward",
            description="Reply to a previously forwarded ticket email",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket",
                    required=True,
                ),
                "body": ParameterDef(
                    type="string",
                    description="Content of the reply in HTML format",
                    required=True,
                ),
                "to_emails": ParameterDef(
                    type="array",
                    description="List of email addresses to reply to",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_thread",
            description="Create a collaboration thread on a ticket",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket to create the thread for",
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description="Type of thread: forward, discussion",
                    required=True,
                ),
                "email_config_id": ParameterDef(
                    type="integer",
                    description="ID of the email config to use for the thread",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_message_for_thread",
            description="Create a message in a collaboration thread",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket",
                    required=True,
                ),
                "thread_id": ParameterDef(
                    type="string",
                    description="ID of the thread to post the message in",
                    required=True,
                ),
                "body": ParameterDef(
                    type="string",
                    description="Content of the message in HTML format",
                    required=True,
                ),
                "subject": ParameterDef(
                    type="string",
                    description="Subject of the email",
                ),
            },
        ),
        ActionDefinition(
            name="list_ticket_conversations",
            description="List all conversations (notes, replies) for a ticket",
            parameters={
                "ticket_id": ParameterDef(
                    type="integer",
                    description="ID of the ticket",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="list_ticket_fields",
            description="List all ticket fields configured in Freshdesk",
            parameters={
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="create_ticket_field",
            description="Create a new custom ticket field",
            parameters={
                "label": ParameterDef(
                    type="string",
                    description="Display name of the ticket field",
                    required=True,
                ),
                "label_for_customers": ParameterDef(
                    type="string",
                    description="Label for the field as seen by customers",
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description="Field type: custom_dropdown, custom_checkbox, custom_text, custom_paragraph, custom_number, custom_date, custom_decimal, custom_url",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_ticket_field",
            description="Update a custom ticket field",
            parameters={
                "ticket_field_id": ParameterDef(
                    type="string",
                    description="ID of the ticket field to update",
                    required=True,
                ),
                "label": ParameterDef(
                    type="string",
                    description="Updated display name",
                ),
                "label_for_customers": ParameterDef(
                    type="string",
                    description="Updated label for customers",
                ),
            },
        ),
        ActionDefinition(
            name="create_solution_article",
            description="Create a knowledge base article in a folder",
            parameters={
                "folder_id": ParameterDef(
                    type="integer",
                    description="ID of the folder to create the article in",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="Title of the article",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string",
                    description="HTML content of the article",
                    required=True,
                ),
                "status": ParameterDef(
                    type="integer",
                    description="Status: 1 (Draft), 2 (Published)",
                    required=True,
                ),
                "tags": ParameterDef(
                    type="array",
                    description="List of tags for the article",
                ),
            },
        ),
        ActionDefinition(
            name="get_solution_article",
            description="Retrieve a knowledge base article by its ID",
            parameters={
                "article_id": ParameterDef(
                    type="integer",
                    description="ID of the article to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_solution_article",
            description="Update a knowledge base article",
            parameters={
                "article_id": ParameterDef(
                    type="integer",
                    description="ID of the article to update",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="Updated title",
                ),
                "description": ParameterDef(
                    type="string",
                    description="Updated HTML content",
                ),
                "status": ParameterDef(
                    type="integer",
                    description="Status: 1 (Draft), 2 (Published)",
                ),
                "tags": ParameterDef(
                    type="array",
                    description="Updated tags for the article",
                ),
            },
        ),
        ActionDefinition(
            name="delete_solution_article",
            description="Delete a knowledge base article",
            parameters={
                "article_id": ParameterDef(
                    type="integer",
                    description="ID of the article to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search_solution_article",
            description="Search knowledge base articles by keyword",
            parameters={
                "term": ParameterDef(
                    type="string",
                    description="Search keyword to find matching articles",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_solution_categories",
            description="List all knowledge base solution categories",
            parameters={},
        ),
        ActionDefinition(
            name="list_category_folders",
            description="List all folders within a solution category",
            parameters={
                "category_id": ParameterDef(
                    type="integer",
                    description="ID of the solution category",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_folder_articles",
            description="List all articles within a solution folder",
            parameters={
                "folder_id": ParameterDef(
                    type="integer",
                    description="ID of the solution folder",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="list_all_folders",
            description="List all canned response folders",
            parameters={
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="list_folder_canned_responses",
            description="List all canned responses in a specific folder",
            parameters={
                "canned_response_folder_id": ParameterDef(
                    type="integer",
                    description="ID of the canned response folder",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_canned_response",
            description="Retrieve a specific canned response by ID",
            parameters={
                "canned_response_id": ParameterDef(
                    type="integer",
                    description="ID of the canned response",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_folder_canned_responses",
            description="Get detailed canned responses from a folder",
            parameters={
                "canned_response_folder_id": ParameterDef(
                    type="integer",
                    description="ID of the canned response folder",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="list_companies",
            description="List all companies in Freshdesk",
            parameters={},
        ),
        ActionDefinition(
            name="list_email_configs",
            description="List all email configurations",
            parameters={},
        ),
        ActionDefinition(
            name="list_roles",
            description="List all agent roles",
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Freshdesk API key and subdomain",
            setup_instructions=[
                "Log in to your Freshdesk account",
                "Click your profile picture in the top right corner",
                "Go to Profile Settings",
                "Your API key is displayed on the right side of the page",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="FRESHDESK_DOMAIN",
                    display_name="Freshdesk Domain",
                    description="Your Freshdesk subdomain (e.g. 'mycompany' for mycompany.freshdesk.com)",
                    required=True,
                    sensitive=False,
                    sample_format="mycompany",
                    about_url="https://support.freshdesk.com/en/support/solutions/articles/215517-how-to-find-your-freshdesk-domain-name",
                ),
                EnvVar(
                    name="FRESHDESK_API_KEY",
                    display_name="Freshdesk API Key",
                    description="Your Freshdesk API key from Profile Settings",
                    required=True,
                    sensitive=True,
                    sample_format="xXxXxXxXxXxXxXxXxXxX",
                    about_url="https://support.freshdesk.com/en/support/solutions/articles/215517-how-to-find-your-api-key",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://{domain}.freshdesk.com/api/v2/tickets?per_page=1",
                method="GET",
                headers={"Authorization": "Basic {api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                ),
                cost_level="free",
                description="Validates credentials by listing one ticket",
            ),
        ),
    ],
)

"""Freshdesk LangChain @tool functions."""
from __future__ import annotations

import base64
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.freshdesk.outputs import (
    AddNoteToTicketOutput,
    AddTicketTagsOutput,
    AssignTicketToAgentOutput,
    AssignTicketToGroupOutput,
    CloseTicketOutput,
    CreateAgentOutput,
    CreateCompanyOutput,
    CreateContactOutput,
    CreateMessageForThreadOutput,
    CreateReplyOutput,
    CreateSolutionArticleOutput,
    CreateThreadOutput,
    CreateTicketFieldOutput,
    CreateTicketOutput,
    DeleteSolutionArticleOutput,
    ForwardTicketOutput,
    GetAgentOutput,
    GetCannedResponseOutput,
    GetContactOutput,
    GetFolderCannedResponsesOutput,
    GetSolutionArticleOutput,
    GetTicketOutput,
    ListAgentsOutput,
    ListAllFoldersOutput,
    ListAllTicketsOutput,
    ListCategoryFoldersOutput,
    ListCompaniesOutput,
    ListEmailConfigsOutput,
    ListFolderArticlesOutput,
    ListFolderCannedResponsesOutput,
    ListRolesOutput,
    ListSolutionCategoriesOutput,
    ListTicketConversationsOutput,
    ListTicketFieldsOutput,
    RemoveTicketTagsOutput,
    ReplyToForwardOutput,
    SearchSolutionArticleOutput,
    SetTicketPriorityOutput,
    SetTicketStatusOutput,
    SetTicketTagsOutput,
    UpdateAgentOutput,
    UpdateContactOutput,
    UpdateSolutionArticleOutput,
    UpdateTicketFieldOutput,
    UpdateTicketOutput,
)

__all__ = [
    "add_note_to_ticket",
    "add_ticket_tags",
    "assign_ticket_to_agent",
    "assign_ticket_to_group",
    "close_ticket",
    "create_agent",
    "create_company",
    "create_contact",
    "create_message_for_thread",
    "create_reply",
    "create_solution_article",
    "create_thread",
    "create_ticket",
    "create_ticket_field",
    "delete_solution_article",
    "forward_ticket",
    "get_agent",
    "get_canned_response",
    "get_contact",
    "get_folder_canned_responses",
    "get_solution_article",
    "get_ticket",
    "list_agents",
    "list_all_folders",
    "list_all_tickets",
    "list_category_folders",
    "list_companies",
    "list_email_configs",
    "list_folder_articles",
    "list_folder_canned_responses",
    "list_roles",
    "list_solution_categories",
    "list_ticket_conversations",
    "list_ticket_fields",
    "remove_ticket_tags",
    "reply_to_forward",
    "search_solution_article",
    "set_ticket_priority",
    "set_ticket_status",
    "set_ticket_tags",
    "update_agent",
    "update_contact",
    "update_solution_article",
    "update_ticket",
    "update_ticket_field",
]

_TIMEOUT = 30.0


def _base_url(domain: str) -> str:
    return f"https://{domain}.freshdesk.com/api/v2"


def _headers(api_key: str) -> dict[str, str]:
    encoded = base64.b64encode(f"{api_key}:X".encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
    }


def _check_creds(domain: str, api_key: str) -> str | None:
    if not domain or not domain.strip():
        return "Freshdesk domain is empty. Please configure a valid credential."
    if not api_key or not api_key.strip():
        return "API key is empty. Please configure a valid credential."
    return None


# --- Input schemas --------------------------------------------------------


class CreateTicketInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    subject: str = Field(description="Subject of the ticket")
    description: str = Field(description="HTML content of the ticket")
    email: str = Field(description="Email address of the requester")
    priority: int = Field(default=1, description="Priority: 1 (Low), 2 (Medium), 3 (High), 4 (Urgent)")
    status: int = Field(default=2, description="Status: 2 (Open), 3 (Pending), 4 (Resolved), 5 (Closed)")
    company_id: int | None = Field(default=None, description="ID of the company")


class GetTicketInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket to retrieve")


class UpdateTicketInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket to update")
    subject: str | None = Field(default=None, description="New subject")
    description: str | None = Field(default=None, description="New HTML content")
    priority: int | None = Field(default=None, description="Priority: 1-4")
    status: int | None = Field(default=None, description="Status: 2-5")
    group_id: int | None = Field(default=None, description="Group ID to assign to")
    responder_id: int | None = Field(default=None, description="Agent ID to assign to")


class ListAllTicketsInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    filter: str | None = Field(default=None, description="Predefined filter")
    requester_id: int | None = Field(default=None, description="Filter by requester ID")
    email: str | None = Field(default=None, description="Filter by email")
    company_id: int | None = Field(default=None, description="Filter by company ID")
    max_results: int = Field(default=100, description="Maximum results to return")


class CloseTicketInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket to close")


class AddNoteToTicketInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket")
    body: str = Field(description="Content of the note in HTML format")
    private: bool = Field(default=True, description="Whether the note is private")
    notify_emails: list[str] | None = Field(default=None, description="Emails to notify")


class AddTicketTagsInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket")
    tags: list[str] = Field(description="Tags to add")


class RemoveTicketTagsInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket")
    tags: list[str] = Field(description="Tags to remove")


class SetTicketTagsInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket")
    tags: list[str] = Field(description="Tags to set (replaces existing)")


class SetTicketPriorityInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket")
    priority: int = Field(description="Priority: 1 (Low), 2 (Medium), 3 (High), 4 (Urgent)")


class SetTicketStatusInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket")
    status: int = Field(description="Status: 2 (Open), 3 (Pending), 4 (Resolved), 5 (Closed)")


class AssignTicketToAgentInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket")
    agent_id: int = Field(description="ID of the agent")


class AssignTicketToGroupInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket")
    group_id: int = Field(description="ID of the group")


class CreateContactInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    email: str = Field(description="Email address of the contact")
    name: str = Field(description="Name of the contact")
    phone: str | None = Field(default=None, description="Phone number")
    company_id: int | None = Field(default=None, description="Company ID")


class GetContactInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    contact_id: int = Field(description="ID of the contact")


class UpdateContactInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    contact_id: int = Field(description="ID of the contact to update")
    name: str | None = Field(default=None, description="Updated name")
    email: str | None = Field(default=None, description="Updated email")
    phone: str | None = Field(default=None, description="Updated phone")
    company_id: int | None = Field(default=None, description="Company ID")


class CreateCompanyInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    name: str = Field(description="Name of the company")
    domains: list[str] | None = Field(default=None, description="Domain names")
    description: str | None = Field(default=None, description="Description")


class CreateAgentInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    email: str = Field(description="Email of the agent")
    ticket_scope: int = Field(description="Ticket permission: 1 (Global), 2 (Group), 3 (Restricted)")
    occasional: bool | None = Field(default=None, description="Occasional agent flag")
    agent_type: int | None = Field(default=None, description="Type: 1 (Support), 2 (Field), 3 (Collaborator)")


class UpdateAgentInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    agent_id: int = Field(description="ID of the agent to update")
    email: str | None = Field(default=None, description="Updated email")
    ticket_scope: int | None = Field(default=None, description="Ticket permission")
    occasional: bool | None = Field(default=None, description="Occasional agent flag")


class GetAgentInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    agent_id: int = Field(description="ID of the agent")


class ListAgentsInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    email: str | None = Field(default=None, description="Filter by email")
    state: str | None = Field(default=None, description="Filter: fulltime, occasional")
    max_results: int = Field(default=100, description="Maximum results")


class CreateReplyInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket")
    body: str = Field(description="Reply content in HTML format")
    cc_emails: list[str] | None = Field(default=None, description="CC email addresses")
    bcc_emails: list[str] | None = Field(default=None, description="BCC email addresses")


class ForwardTicketInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket")
    body: str = Field(description="Forward content in HTML format")
    to_emails: list[str] = Field(description="Email addresses to forward to")
    cc_emails: list[str] | None = Field(default=None, description="CC email addresses")
    bcc_emails: list[str] | None = Field(default=None, description="BCC email addresses")


class ReplyToForwardInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket")
    body: str = Field(description="Reply content in HTML format")
    to_emails: list[str] = Field(description="Email addresses to reply to")


class CreateThreadInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket")
    type: str = Field(description="Thread type: forward, discussion")
    email_config_id: int = Field(description="Email config ID")


class CreateMessageForThreadInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket")
    thread_id: str = Field(description="ID of the thread")
    body: str = Field(description="Message content in HTML format")
    subject: str | None = Field(default=None, description="Subject of the email")


class ListTicketConversationsInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_id: int = Field(description="ID of the ticket")
    max_results: int = Field(default=100, description="Maximum results")


class ListTicketFieldsInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    max_results: int = Field(default=100, description="Maximum results")


class CreateTicketFieldInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    label: str = Field(description="Display name of the field")
    label_for_customers: str = Field(description="Label seen by customers")
    type: str = Field(description="Field type: custom_dropdown, custom_checkbox, custom_text, etc.")


class UpdateTicketFieldInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    ticket_field_id: str = Field(description="ID of the ticket field")
    label: str | None = Field(default=None, description="Updated display name")
    label_for_customers: str | None = Field(default=None, description="Updated label for customers")


class CreateSolutionArticleInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    folder_id: int = Field(description="ID of the folder")
    title: str = Field(description="Title of the article")
    description: str = Field(description="HTML content of the article")
    status: int = Field(description="Status: 1 (Draft), 2 (Published)")
    tags: list[str] | None = Field(default=None, description="Tags for the article")


class GetSolutionArticleInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    article_id: int = Field(description="ID of the article")


class UpdateSolutionArticleInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    article_id: int = Field(description="ID of the article")
    title: str | None = Field(default=None, description="Updated title")
    description: str | None = Field(default=None, description="Updated HTML content")
    status: int | None = Field(default=None, description="Status: 1 (Draft), 2 (Published)")
    tags: list[str] | None = Field(default=None, description="Updated tags")


class DeleteSolutionArticleInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    article_id: int = Field(description="ID of the article to delete")


class SearchSolutionArticleInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    term: str = Field(description="Search keyword")


class ListSolutionCategoriesInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")


class ListCategoryFoldersInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    category_id: int = Field(description="ID of the category")


class ListFolderArticlesInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    folder_id: int = Field(description="ID of the folder")
    max_results: int = Field(default=100, description="Maximum results")


class ListAllFoldersInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    max_results: int = Field(default=100, description="Maximum results")


class ListFolderCannedResponsesInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    canned_response_folder_id: int = Field(description="ID of the folder")


class GetCannedResponseInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    canned_response_id: int = Field(description="ID of the canned response")


class GetFolderCannedResponsesInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")
    canned_response_folder_id: int = Field(description="ID of the folder")
    max_results: int = Field(default=100, description="Maximum results")


class ListCompaniesInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")


class ListEmailConfigsInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")


class ListRolesInput(BaseModel):
    domain: str = Field(description="Freshdesk subdomain")
    api_key: str = Field(description="Freshdesk API key")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateTicketInput)
@serialize_pydantic_return
async def create_ticket(
    domain: str,
    api_key: str,
    subject: str,
    description: str,
    email: str,
    priority: int = 1,
    status: int = 2,
    company_id: int | None = None,
) -> CreateTicketOutput:
    """Create a new support ticket in Freshdesk"""
    if err := _check_creds(domain, api_key):
        return CreateTicketOutput(success=False, error=err)
    payload: dict[str, Any] = {
        "subject": subject,
        "description": description,
        "email": email,
        "priority": priority,
        "status": status,
    }
    if company_id is not None:
        payload["company_id"] = company_id
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{_base_url(domain)}/tickets",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code not in (200, 201):
            return CreateTicketOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return CreateTicketOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return CreateTicketOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateTicketOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=GetTicketInput)
@serialize_pydantic_return
async def get_ticket(
    domain: str,
    api_key: str,
    ticket_id: int,
) -> GetTicketOutput:
    """Retrieve a specific ticket by its ID"""
    if err := _check_creds(domain, api_key):
        return GetTicketOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/tickets/{ticket_id}",
                headers=_headers(api_key),
            )
        if resp.status_code != 200:
            return GetTicketOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return GetTicketOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return GetTicketOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetTicketOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=UpdateTicketInput)
@serialize_pydantic_return
async def update_ticket(
    domain: str,
    api_key: str,
    ticket_id: int,
    subject: str | None = None,
    description: str | None = None,
    priority: int | None = None,
    status: int | None = None,
    group_id: int | None = None,
    responder_id: int | None = None,
) -> UpdateTicketOutput:
    """Update an existing ticket's properties"""
    if err := _check_creds(domain, api_key):
        return UpdateTicketOutput(success=False, error=err)
    payload: dict[str, Any] = {}
    if subject is not None:
        payload["subject"] = subject
    if description is not None:
        payload["description"] = description
    if priority is not None:
        payload["priority"] = priority
    if status is not None:
        payload["status"] = status
    if group_id is not None:
        payload["group_id"] = group_id
    if responder_id is not None:
        payload["responder_id"] = responder_id
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.put(
                f"{_base_url(domain)}/tickets/{ticket_id}",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code != 200:
            return UpdateTicketOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return UpdateTicketOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return UpdateTicketOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateTicketOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=ListAllTicketsInput)
@serialize_pydantic_return
async def list_all_tickets(
    domain: str,
    api_key: str,
    filter: str | None = None,
    requester_id: int | None = None,
    email: str | None = None,
    company_id: int | None = None,
    max_results: int = 100,
) -> ListAllTicketsOutput:
    """List tickets in Freshdesk with optional filtering"""
    if err := _check_creds(domain, api_key):
        return ListAllTicketsOutput(success=False, error=err)
    params: dict[str, Any] = {"per_page": min(max_results, 100)}
    if filter is not None:
        params["filter"] = filter
    if requester_id is not None:
        params["requester_id"] = requester_id
    if email is not None:
        params["email"] = email
    if company_id is not None:
        params["company_id"] = company_id
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/tickets",
                headers=_headers(api_key),
                params=params,
            )
        if resp.status_code != 200:
            return ListAllTicketsOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return ListAllTicketsOutput(success=True, items=resp.json())
    except httpx.TimeoutException:
        return ListAllTicketsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAllTicketsOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=CloseTicketInput)
@serialize_pydantic_return
async def close_ticket(
    domain: str,
    api_key: str,
    ticket_id: int,
) -> CloseTicketOutput:
    """Close a ticket by setting its status to Closed (5)"""
    if err := _check_creds(domain, api_key):
        return CloseTicketOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.put(
                f"{_base_url(domain)}/tickets/{ticket_id}",
                headers=_headers(api_key),
                json={"status": 5},
            )
        if resp.status_code != 200:
            return CloseTicketOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return CloseTicketOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return CloseTicketOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CloseTicketOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=AddNoteToTicketInput)
@serialize_pydantic_return
async def add_note_to_ticket(
    domain: str,
    api_key: str,
    ticket_id: int,
    body: str,
    private: bool = True,
    notify_emails: list[str] | None = None,
) -> AddNoteToTicketOutput:
    """Add a private or public note to a ticket"""
    if err := _check_creds(domain, api_key):
        return AddNoteToTicketOutput(success=False, error=err)
    payload: dict[str, Any] = {"body": body, "private": private}
    if notify_emails:
        payload["notify_emails"] = notify_emails
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{_base_url(domain)}/tickets/{ticket_id}/notes",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code not in (200, 201):
            return AddNoteToTicketOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return AddNoteToTicketOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return AddNoteToTicketOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddNoteToTicketOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=AddTicketTagsInput)
@serialize_pydantic_return
async def add_ticket_tags(
    domain: str,
    api_key: str,
    ticket_id: int,
    tags: list[str],
) -> AddTicketTagsOutput:
    """Add tags to an existing ticket"""
    if err := _check_creds(domain, api_key):
        return AddTicketTagsOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/tickets/{ticket_id}",
                headers=_headers(api_key),
            )
            if resp.status_code != 200:
                return AddTicketTagsOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
            existing_tags: list[str] = resp.json().get("tags", [])
            merged = list(set(existing_tags + tags))
            resp = await client.put(
                f"{_base_url(domain)}/tickets/{ticket_id}",
                headers=_headers(api_key),
                json={"tags": merged},
            )
        if resp.status_code != 200:
            return AddTicketTagsOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return AddTicketTagsOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return AddTicketTagsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddTicketTagsOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=RemoveTicketTagsInput)
@serialize_pydantic_return
async def remove_ticket_tags(
    domain: str,
    api_key: str,
    ticket_id: int,
    tags: list[str],
) -> RemoveTicketTagsOutput:
    """Remove tags from an existing ticket"""
    if err := _check_creds(domain, api_key):
        return RemoveTicketTagsOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/tickets/{ticket_id}",
                headers=_headers(api_key),
            )
            if resp.status_code != 200:
                return RemoveTicketTagsOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
            existing_tags: list[str] = resp.json().get("tags", [])
            remaining = [t for t in existing_tags if t not in tags]
            resp = await client.put(
                f"{_base_url(domain)}/tickets/{ticket_id}",
                headers=_headers(api_key),
                json={"tags": remaining},
            )
        if resp.status_code != 200:
            return RemoveTicketTagsOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return RemoveTicketTagsOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return RemoveTicketTagsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RemoveTicketTagsOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=SetTicketTagsInput)
@serialize_pydantic_return
async def set_ticket_tags(
    domain: str,
    api_key: str,
    ticket_id: int,
    tags: list[str],
) -> SetTicketTagsOutput:
    """Replace all tags on a ticket with the specified set"""
    if err := _check_creds(domain, api_key):
        return SetTicketTagsOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.put(
                f"{_base_url(domain)}/tickets/{ticket_id}",
                headers=_headers(api_key),
                json={"tags": tags},
            )
        if resp.status_code != 200:
            return SetTicketTagsOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return SetTicketTagsOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return SetTicketTagsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SetTicketTagsOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=SetTicketPriorityInput)
@serialize_pydantic_return
async def set_ticket_priority(
    domain: str,
    api_key: str,
    ticket_id: int,
    priority: int,
) -> SetTicketPriorityOutput:
    """Set the priority of a ticket"""
    if err := _check_creds(domain, api_key):
        return SetTicketPriorityOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.put(
                f"{_base_url(domain)}/tickets/{ticket_id}",
                headers=_headers(api_key),
                json={"priority": priority},
            )
        if resp.status_code != 200:
            return SetTicketPriorityOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return SetTicketPriorityOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return SetTicketPriorityOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SetTicketPriorityOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=SetTicketStatusInput)
@serialize_pydantic_return
async def set_ticket_status(
    domain: str,
    api_key: str,
    ticket_id: int,
    status: int,
) -> SetTicketStatusOutput:
    """Set the status of a ticket"""
    if err := _check_creds(domain, api_key):
        return SetTicketStatusOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.put(
                f"{_base_url(domain)}/tickets/{ticket_id}",
                headers=_headers(api_key),
                json={"status": status},
            )
        if resp.status_code != 200:
            return SetTicketStatusOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return SetTicketStatusOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return SetTicketStatusOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SetTicketStatusOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=AssignTicketToAgentInput)
@serialize_pydantic_return
async def assign_ticket_to_agent(
    domain: str,
    api_key: str,
    ticket_id: int,
    agent_id: int,
) -> AssignTicketToAgentOutput:
    """Assign a ticket to a specific agent"""
    if err := _check_creds(domain, api_key):
        return AssignTicketToAgentOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.put(
                f"{_base_url(domain)}/tickets/{ticket_id}",
                headers=_headers(api_key),
                json={"responder_id": agent_id},
            )
        if resp.status_code != 200:
            return AssignTicketToAgentOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return AssignTicketToAgentOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return AssignTicketToAgentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AssignTicketToAgentOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=AssignTicketToGroupInput)
@serialize_pydantic_return
async def assign_ticket_to_group(
    domain: str,
    api_key: str,
    ticket_id: int,
    group_id: int,
) -> AssignTicketToGroupOutput:
    """Assign a ticket to a specific group"""
    if err := _check_creds(domain, api_key):
        return AssignTicketToGroupOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.put(
                f"{_base_url(domain)}/tickets/{ticket_id}",
                headers=_headers(api_key),
                json={"group_id": group_id},
            )
        if resp.status_code != 200:
            return AssignTicketToGroupOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return AssignTicketToGroupOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return AssignTicketToGroupOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AssignTicketToGroupOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=CreateContactInput)
@serialize_pydantic_return
async def create_contact(
    domain: str,
    api_key: str,
    email: str,
    name: str,
    phone: str | None = None,
    company_id: int | None = None,
) -> CreateContactOutput:
    """Create a new contact in Freshdesk"""
    if err := _check_creds(domain, api_key):
        return CreateContactOutput(success=False, error=err)
    payload: dict[str, Any] = {"email": email, "name": name}
    if phone is not None:
        payload["phone"] = phone
    if company_id is not None:
        payload["company_id"] = company_id
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{_base_url(domain)}/contacts",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code not in (200, 201):
            return CreateContactOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return CreateContactOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return CreateContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateContactOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=GetContactInput)
@serialize_pydantic_return
async def get_contact(
    domain: str,
    api_key: str,
    contact_id: int,
) -> GetContactOutput:
    """Retrieve a contact by their ID"""
    if err := _check_creds(domain, api_key):
        return GetContactOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/contacts/{contact_id}",
                headers=_headers(api_key),
            )
        if resp.status_code != 200:
            return GetContactOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return GetContactOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return GetContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetContactOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=UpdateContactInput)
@serialize_pydantic_return
async def update_contact(
    domain: str,
    api_key: str,
    contact_id: int,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    company_id: int | None = None,
) -> UpdateContactOutput:
    """Update an existing contact's properties"""
    if err := _check_creds(domain, api_key):
        return UpdateContactOutput(success=False, error=err)
    payload: dict[str, Any] = {}
    if name is not None:
        payload["name"] = name
    if email is not None:
        payload["email"] = email
    if phone is not None:
        payload["phone"] = phone
    if company_id is not None:
        payload["company_id"] = company_id
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.put(
                f"{_base_url(domain)}/contacts/{contact_id}",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code != 200:
            return UpdateContactOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return UpdateContactOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return UpdateContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateContactOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=CreateCompanyInput)
@serialize_pydantic_return
async def create_company(
    domain: str,
    api_key: str,
    name: str,
    domains: list[str] | None = None,
    description: str | None = None,
) -> CreateCompanyOutput:
    """Create a new company in Freshdesk"""
    if err := _check_creds(domain, api_key):
        return CreateCompanyOutput(success=False, error=err)
    payload: dict[str, Any] = {"name": name}
    if domains is not None:
        payload["domains"] = domains
    if description is not None:
        payload["description"] = description
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{_base_url(domain)}/companies",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code not in (200, 201):
            return CreateCompanyOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return CreateCompanyOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return CreateCompanyOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateCompanyOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=CreateAgentInput)
@serialize_pydantic_return
async def create_agent(
    domain: str,
    api_key: str,
    email: str,
    ticket_scope: int,
    occasional: bool | None = None,
    agent_type: int | None = None,
) -> CreateAgentOutput:
    """Create a new agent in Freshdesk"""
    if err := _check_creds(domain, api_key):
        return CreateAgentOutput(success=False, error=err)
    payload: dict[str, Any] = {"email": email, "ticket_scope": ticket_scope}
    if occasional is not None:
        payload["occasional"] = occasional
    if agent_type is not None:
        payload["agent_type"] = agent_type
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{_base_url(domain)}/agents",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code not in (200, 201):
            return CreateAgentOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return CreateAgentOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return CreateAgentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateAgentOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=UpdateAgentInput)
@serialize_pydantic_return
async def update_agent(
    domain: str,
    api_key: str,
    agent_id: int,
    email: str | None = None,
    ticket_scope: int | None = None,
    occasional: bool | None = None,
) -> UpdateAgentOutput:
    """Update an existing agent's properties"""
    if err := _check_creds(domain, api_key):
        return UpdateAgentOutput(success=False, error=err)
    payload: dict[str, Any] = {}
    if email is not None:
        payload["email"] = email
    if ticket_scope is not None:
        payload["ticket_scope"] = ticket_scope
    if occasional is not None:
        payload["occasional"] = occasional
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.put(
                f"{_base_url(domain)}/agents/{agent_id}",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code != 200:
            return UpdateAgentOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return UpdateAgentOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return UpdateAgentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateAgentOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=GetAgentInput)
@serialize_pydantic_return
async def get_agent(
    domain: str,
    api_key: str,
    agent_id: int,
) -> GetAgentOutput:
    """Retrieve a single agent by their ID"""
    if err := _check_creds(domain, api_key):
        return GetAgentOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/agents/{agent_id}",
                headers=_headers(api_key),
            )
        if resp.status_code != 200:
            return GetAgentOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return GetAgentOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return GetAgentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetAgentOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=ListAgentsInput)
@serialize_pydantic_return
async def list_agents(
    domain: str,
    api_key: str,
    email: str | None = None,
    state: str | None = None,
    max_results: int = 100,
) -> ListAgentsOutput:
    """List all agents in Freshdesk with optional filtering"""
    if err := _check_creds(domain, api_key):
        return ListAgentsOutput(success=False, error=err)
    params: dict[str, Any] = {"per_page": min(max_results, 100)}
    if email is not None:
        params["email"] = email
    if state is not None:
        params["state"] = state
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/agents",
                headers=_headers(api_key),
                params=params,
            )
        if resp.status_code != 200:
            return ListAgentsOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return ListAgentsOutput(success=True, items=resp.json())
    except httpx.TimeoutException:
        return ListAgentsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAgentsOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=CreateReplyInput)
@serialize_pydantic_return
async def create_reply(
    domain: str,
    api_key: str,
    ticket_id: int,
    body: str,
    cc_emails: list[str] | None = None,
    bcc_emails: list[str] | None = None,
) -> CreateReplyOutput:
    """Create a reply to a ticket"""
    if err := _check_creds(domain, api_key):
        return CreateReplyOutput(success=False, error=err)
    payload: dict[str, Any] = {"body": body}
    if cc_emails:
        payload["cc_emails"] = cc_emails
    if bcc_emails:
        payload["bcc_emails"] = bcc_emails
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{_base_url(domain)}/tickets/{ticket_id}/reply",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code not in (200, 201):
            return CreateReplyOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return CreateReplyOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return CreateReplyOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateReplyOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=ForwardTicketInput)
@serialize_pydantic_return
async def forward_ticket(
    domain: str,
    api_key: str,
    ticket_id: int,
    body: str,
    to_emails: list[str],
    cc_emails: list[str] | None = None,
    bcc_emails: list[str] | None = None,
) -> ForwardTicketOutput:
    """Forward a ticket to an external email address"""
    if err := _check_creds(domain, api_key):
        return ForwardTicketOutput(success=False, error=err)
    payload: dict[str, Any] = {"body": body, "to_emails": to_emails}
    if cc_emails:
        payload["cc_emails"] = cc_emails
    if bcc_emails:
        payload["bcc_emails"] = bcc_emails
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{_base_url(domain)}/tickets/{ticket_id}/forward",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code not in (200, 201):
            return ForwardTicketOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return ForwardTicketOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return ForwardTicketOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ForwardTicketOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=ReplyToForwardInput)
@serialize_pydantic_return
async def reply_to_forward(
    domain: str,
    api_key: str,
    ticket_id: int,
    body: str,
    to_emails: list[str],
) -> ReplyToForwardOutput:
    """Reply to a previously forwarded ticket email"""
    if err := _check_creds(domain, api_key):
        return ReplyToForwardOutput(success=False, error=err)
    payload: dict[str, Any] = {"body": body, "to_emails": to_emails}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{_base_url(domain)}/tickets/{ticket_id}/reply_to_forward",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code not in (200, 201):
            return ReplyToForwardOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return ReplyToForwardOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return ReplyToForwardOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ReplyToForwardOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=CreateThreadInput)
@serialize_pydantic_return
async def create_thread(
    domain: str,
    api_key: str,
    ticket_id: int,
    type: str,
    email_config_id: int,
) -> CreateThreadOutput:
    """Create a collaboration thread on a ticket"""
    if err := _check_creds(domain, api_key):
        return CreateThreadOutput(success=False, error=err)
    payload: dict[str, Any] = {
        "type": type,
        "ticket_id": ticket_id,
        "email_config_id": email_config_id,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{_base_url(domain)}/collaboration/threads",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code not in (200, 201):
            return CreateThreadOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return CreateThreadOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return CreateThreadOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateThreadOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=CreateMessageForThreadInput)
@serialize_pydantic_return
async def create_message_for_thread(
    domain: str,
    api_key: str,
    ticket_id: int,
    thread_id: str,
    body: str,
    subject: str | None = None,
) -> CreateMessageForThreadOutput:
    """Create a message in a collaboration thread"""
    if err := _check_creds(domain, api_key):
        return CreateMessageForThreadOutput(success=False, error=err)
    payload: dict[str, Any] = {
        "ticket_id": ticket_id,
        "thread_id": thread_id,
        "body": body,
    }
    if subject is not None:
        payload["subject"] = subject
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{_base_url(domain)}/collaboration/messages",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code not in (200, 201):
            return CreateMessageForThreadOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return CreateMessageForThreadOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return CreateMessageForThreadOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateMessageForThreadOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=ListTicketConversationsInput)
@serialize_pydantic_return
async def list_ticket_conversations(
    domain: str,
    api_key: str,
    ticket_id: int,
    max_results: int = 100,
) -> ListTicketConversationsOutput:
    """List all conversations (notes, replies) for a ticket"""
    if err := _check_creds(domain, api_key):
        return ListTicketConversationsOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/tickets/{ticket_id}/conversations",
                headers=_headers(api_key),
                params={"per_page": min(max_results, 100)},
            )
        if resp.status_code != 200:
            return ListTicketConversationsOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return ListTicketConversationsOutput(success=True, items=resp.json())
    except httpx.TimeoutException:
        return ListTicketConversationsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTicketConversationsOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=ListTicketFieldsInput)
@serialize_pydantic_return
async def list_ticket_fields(
    domain: str,
    api_key: str,
    max_results: int = 100,
) -> ListTicketFieldsOutput:
    """List all ticket fields configured in Freshdesk"""
    if err := _check_creds(domain, api_key):
        return ListTicketFieldsOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/ticket_fields",
                headers=_headers(api_key),
                params={"per_page": min(max_results, 100)},
            )
        if resp.status_code != 200:
            return ListTicketFieldsOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return ListTicketFieldsOutput(success=True, items=resp.json())
    except httpx.TimeoutException:
        return ListTicketFieldsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTicketFieldsOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=CreateTicketFieldInput)
@serialize_pydantic_return
async def create_ticket_field(
    domain: str,
    api_key: str,
    label: str,
    label_for_customers: str,
    type: str,
) -> CreateTicketFieldOutput:
    """Create a new custom ticket field"""
    if err := _check_creds(domain, api_key):
        return CreateTicketFieldOutput(success=False, error=err)
    payload: dict[str, Any] = {
        "label": label,
        "label_for_customers": label_for_customers,
        "type": type,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{_base_url(domain)}/admin/ticket_fields",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code not in (200, 201):
            return CreateTicketFieldOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return CreateTicketFieldOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return CreateTicketFieldOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateTicketFieldOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=UpdateTicketFieldInput)
@serialize_pydantic_return
async def update_ticket_field(
    domain: str,
    api_key: str,
    ticket_field_id: str,
    label: str | None = None,
    label_for_customers: str | None = None,
) -> UpdateTicketFieldOutput:
    """Update a custom ticket field"""
    if err := _check_creds(domain, api_key):
        return UpdateTicketFieldOutput(success=False, error=err)
    payload: dict[str, Any] = {}
    if label is not None:
        payload["label"] = label
    if label_for_customers is not None:
        payload["label_for_customers"] = label_for_customers
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.put(
                f"{_base_url(domain)}/admin/ticket_fields/{ticket_field_id}",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code != 200:
            return UpdateTicketFieldOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return UpdateTicketFieldOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return UpdateTicketFieldOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateTicketFieldOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=CreateSolutionArticleInput)
@serialize_pydantic_return
async def create_solution_article(
    domain: str,
    api_key: str,
    folder_id: int,
    title: str,
    description: str,
    status: int,
    tags: list[str] | None = None,
) -> CreateSolutionArticleOutput:
    """Create a knowledge base article in a folder"""
    if err := _check_creds(domain, api_key):
        return CreateSolutionArticleOutput(success=False, error=err)
    payload: dict[str, Any] = {
        "title": title,
        "description": description,
        "status": status,
    }
    if tags:
        payload["tags"] = tags
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{_base_url(domain)}/solutions/folders/{folder_id}/articles",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code not in (200, 201):
            return CreateSolutionArticleOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return CreateSolutionArticleOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return CreateSolutionArticleOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateSolutionArticleOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=GetSolutionArticleInput)
@serialize_pydantic_return
async def get_solution_article(
    domain: str,
    api_key: str,
    article_id: int,
) -> GetSolutionArticleOutput:
    """Retrieve a knowledge base article by its ID"""
    if err := _check_creds(domain, api_key):
        return GetSolutionArticleOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/solutions/articles/{article_id}",
                headers=_headers(api_key),
            )
        if resp.status_code != 200:
            return GetSolutionArticleOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return GetSolutionArticleOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return GetSolutionArticleOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSolutionArticleOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=UpdateSolutionArticleInput)
@serialize_pydantic_return
async def update_solution_article(
    domain: str,
    api_key: str,
    article_id: int,
    title: str | None = None,
    description: str | None = None,
    status: int | None = None,
    tags: list[str] | None = None,
) -> UpdateSolutionArticleOutput:
    """Update a knowledge base article"""
    if err := _check_creds(domain, api_key):
        return UpdateSolutionArticleOutput(success=False, error=err)
    payload: dict[str, Any] = {}
    if title is not None:
        payload["title"] = title
    if description is not None:
        payload["description"] = description
    if status is not None:
        payload["status"] = status
    if tags is not None:
        payload["tags"] = tags
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.put(
                f"{_base_url(domain)}/solutions/articles/{article_id}",
                headers=_headers(api_key),
                json=payload,
            )
        if resp.status_code != 200:
            return UpdateSolutionArticleOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return UpdateSolutionArticleOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return UpdateSolutionArticleOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateSolutionArticleOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=DeleteSolutionArticleInput)
@serialize_pydantic_return
async def delete_solution_article(
    domain: str,
    api_key: str,
    article_id: int,
) -> DeleteSolutionArticleOutput:
    """Delete a knowledge base article"""
    if err := _check_creds(domain, api_key):
        return DeleteSolutionArticleOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.delete(
                f"{_base_url(domain)}/solutions/articles/{article_id}",
                headers=_headers(api_key),
            )
        if resp.status_code not in (200, 204):
            return DeleteSolutionArticleOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return DeleteSolutionArticleOutput(success=True)
    except httpx.TimeoutException:
        return DeleteSolutionArticleOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteSolutionArticleOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=SearchSolutionArticleInput)
@serialize_pydantic_return
async def search_solution_article(
    domain: str,
    api_key: str,
    term: str,
) -> SearchSolutionArticleOutput:
    """Search knowledge base articles by keyword"""
    if err := _check_creds(domain, api_key):
        return SearchSolutionArticleOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/search/solutions",
                headers=_headers(api_key),
                params={"term": term},
            )
        if resp.status_code != 200:
            return SearchSolutionArticleOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return SearchSolutionArticleOutput(success=True, items=resp.json())
    except httpx.TimeoutException:
        return SearchSolutionArticleOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchSolutionArticleOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=ListSolutionCategoriesInput)
@serialize_pydantic_return
async def list_solution_categories(
    domain: str,
    api_key: str,
) -> ListSolutionCategoriesOutput:
    """List all knowledge base solution categories"""
    if err := _check_creds(domain, api_key):
        return ListSolutionCategoriesOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/solutions/categories",
                headers=_headers(api_key),
            )
        if resp.status_code != 200:
            return ListSolutionCategoriesOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return ListSolutionCategoriesOutput(success=True, items=resp.json())
    except httpx.TimeoutException:
        return ListSolutionCategoriesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListSolutionCategoriesOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=ListCategoryFoldersInput)
@serialize_pydantic_return
async def list_category_folders(
    domain: str,
    api_key: str,
    category_id: int,
) -> ListCategoryFoldersOutput:
    """List all folders within a solution category"""
    if err := _check_creds(domain, api_key):
        return ListCategoryFoldersOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/solutions/categories/{category_id}/folders",
                headers=_headers(api_key),
            )
        if resp.status_code != 200:
            return ListCategoryFoldersOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return ListCategoryFoldersOutput(success=True, items=resp.json())
    except httpx.TimeoutException:
        return ListCategoryFoldersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListCategoryFoldersOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=ListFolderArticlesInput)
@serialize_pydantic_return
async def list_folder_articles(
    domain: str,
    api_key: str,
    folder_id: int,
    max_results: int = 100,
) -> ListFolderArticlesOutput:
    """List all articles within a solution folder"""
    if err := _check_creds(domain, api_key):
        return ListFolderArticlesOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/solutions/folders/{folder_id}/articles",
                headers=_headers(api_key),
                params={"per_page": min(max_results, 100)},
            )
        if resp.status_code != 200:
            return ListFolderArticlesOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return ListFolderArticlesOutput(success=True, items=resp.json())
    except httpx.TimeoutException:
        return ListFolderArticlesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListFolderArticlesOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=ListAllFoldersInput)
@serialize_pydantic_return
async def list_all_folders(
    domain: str,
    api_key: str,
    max_results: int = 100,
) -> ListAllFoldersOutput:
    """List all canned response folders"""
    if err := _check_creds(domain, api_key):
        return ListAllFoldersOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/canned_response_folders",
                headers=_headers(api_key),
                params={"per_page": min(max_results, 100)},
            )
        if resp.status_code != 200:
            return ListAllFoldersOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return ListAllFoldersOutput(success=True, items=resp.json())
    except httpx.TimeoutException:
        return ListAllFoldersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAllFoldersOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=ListFolderCannedResponsesInput)
@serialize_pydantic_return
async def list_folder_canned_responses(
    domain: str,
    api_key: str,
    canned_response_folder_id: int,
) -> ListFolderCannedResponsesOutput:
    """List all canned responses in a specific folder"""
    if err := _check_creds(domain, api_key):
        return ListFolderCannedResponsesOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/canned_response_folders/{canned_response_folder_id}",
                headers=_headers(api_key),
            )
        if resp.status_code != 200:
            return ListFolderCannedResponsesOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        data = resp.json()
        items = data.get("canned_responses", []) if isinstance(data, dict) else data
        return ListFolderCannedResponsesOutput(success=True, items=items)
    except httpx.TimeoutException:
        return ListFolderCannedResponsesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListFolderCannedResponsesOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=GetCannedResponseInput)
@serialize_pydantic_return
async def get_canned_response(
    domain: str,
    api_key: str,
    canned_response_id: int,
) -> GetCannedResponseOutput:
    """Retrieve a specific canned response by ID"""
    if err := _check_creds(domain, api_key):
        return GetCannedResponseOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/canned_responses/{canned_response_id}",
                headers=_headers(api_key),
            )
        if resp.status_code != 200:
            return GetCannedResponseOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return GetCannedResponseOutput(success=True, data=resp.json())
    except httpx.TimeoutException:
        return GetCannedResponseOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCannedResponseOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=GetFolderCannedResponsesInput)
@serialize_pydantic_return
async def get_folder_canned_responses(
    domain: str,
    api_key: str,
    canned_response_folder_id: int,
    max_results: int = 100,
) -> GetFolderCannedResponsesOutput:
    """Get detailed canned responses from a folder"""
    if err := _check_creds(domain, api_key):
        return GetFolderCannedResponsesOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/canned_response_folders/{canned_response_folder_id}/responses",
                headers=_headers(api_key),
                params={"per_page": min(max_results, 100)},
            )
        if resp.status_code != 200:
            return GetFolderCannedResponsesOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return GetFolderCannedResponsesOutput(success=True, items=resp.json())
    except httpx.TimeoutException:
        return GetFolderCannedResponsesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetFolderCannedResponsesOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=ListCompaniesInput)
@serialize_pydantic_return
async def list_companies(
    domain: str,
    api_key: str,
) -> ListCompaniesOutput:
    """List all companies in Freshdesk"""
    if err := _check_creds(domain, api_key):
        return ListCompaniesOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/companies",
                headers=_headers(api_key),
            )
        if resp.status_code != 200:
            return ListCompaniesOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return ListCompaniesOutput(success=True, items=resp.json())
    except httpx.TimeoutException:
        return ListCompaniesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListCompaniesOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=ListEmailConfigsInput)
@serialize_pydantic_return
async def list_email_configs(
    domain: str,
    api_key: str,
) -> ListEmailConfigsOutput:
    """List all email configurations"""
    if err := _check_creds(domain, api_key):
        return ListEmailConfigsOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/email_configs",
                headers=_headers(api_key),
            )
        if resp.status_code != 200:
            return ListEmailConfigsOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return ListEmailConfigsOutput(success=True, items=resp.json())
    except httpx.TimeoutException:
        return ListEmailConfigsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListEmailConfigsOutput(success=False, error=f"Call failed: {exc}")


@tool(args_schema=ListRolesInput)
@serialize_pydantic_return
async def list_roles(
    domain: str,
    api_key: str,
) -> ListRolesOutput:
    """List all agent roles"""
    if err := _check_creds(domain, api_key):
        return ListRolesOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_base_url(domain)}/roles",
                headers=_headers(api_key),
            )
        if resp.status_code != 200:
            return ListRolesOutput(success=False, error=f"API error ({resp.status_code}): {resp.text}")
        return ListRolesOutput(success=True, items=resp.json())
    except httpx.TimeoutException:
        return ListRolesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListRolesOutput(success=False, error=f"Call failed: {exc}")

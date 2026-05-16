"""Zendesk LangChain ``@tool`` functions.

Pure HTTP integration against the Zendesk v2 REST API. **Triple-
credential pattern**: every action accepts ``subdomain``, ``email``,
``api_key`` as separate parameters — together they form a Basic Auth
header (`{email}/token:{api_key}` base64-encoded).

17 actions across ticket CRUD + tags + comments, custom fields, users,
locales, macros, and help-center articles. All actions wrap in
try/except → unified ``success=False`` envelope.
"""
from __future__ import annotations

import base64
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.zendesk.outputs import (
    AddTicketTagsOutput,
    CreateTicketOutput,
    DeleteTicketOutput,
    GetArticleOutput,
    GetMacroOutput,
    GetTicketOutput,
    GetUserOutput,
    ListArticlesOutput,
    ListLocalesOutput,
    ListMacrosOutput,
    ListTicketCommentsOutput,
    ListTicketsOutput,
    RemoveTicketTagsOutput,
    SearchTicketsOutput,
    SetCustomFieldsOutput,
    SetTicketTagsOutput,
    UpdateTicketOutput,
)

__all__ = [
    "add_ticket_tags",
    "create_ticket",
    "delete_ticket",
    "get_article",
    "get_macro",
    "get_ticket",
    "get_user",
    "list_articles",
    "list_locales",
    "list_macros",
    "list_ticket_comments",
    "list_tickets",
    "remove_ticket_tags",
    "search_tickets",
    "set_custom_fields",
    "set_ticket_tags",
    "update_ticket",
]

_TIMEOUT = 30.0


def _headers(email: str, api_key: str) -> dict[str, str]:
    encoded = base64.b64encode(f"{email}/token:{api_key}".encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _base_url(subdomain: str) -> str:
    return f"https://{subdomain}.zendesk.com/api/v2"


def _api_err(status: int, body: str) -> str:
    return f"API error {status}: {body}"


async def _call(
    method: str,
    subdomain: str,
    email: str,
    api_key: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    success_codes: tuple[int, ...] = (200,),
) -> tuple[bool, str | None, dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.request(
                method,
                f"{_base_url(subdomain)}{path}",
                headers=_headers(email, api_key),
                json=json_body,
                params=params,
            )
        if response.status_code not in success_codes:
            return False, _api_err(response.status_code, response.text), {}
        # 204 No Content → empty body
        if response.status_code == 204:
            return True, None, {}
        return True, None, response.json() or {}
    except httpx.TimeoutException:
        return False, "Request timed out", {}
    except Exception as exc:
        return False, str(exc), {}


# --- Input schemas ---------------------------------------------------------


class _CredFields(BaseModel):
    subdomain: str = Field(description="Zendesk subdomain")
    email: str = Field(description="Zendesk user email")
    api_key: str = Field(description="Zendesk API token")


class CreateTicketInput(_CredFields):
    subject: str = Field(description="Ticket subject")
    comment_body: str = Field(description="Initial comment body")
    priority: str | None = None
    status: str | None = None
    requester_email: str | None = None
    assignee_id: int | None = None
    tags: list[str] | None = None
    custom_fields: list[dict[str, Any]] | None = None


class UpdateTicketInput(_CredFields):
    ticket_id: int = Field(description="Ticket ID")
    subject: str | None = None
    comment_body: str | None = None
    comment_public: bool | None = True
    priority: str | None = None
    status: str | None = None
    assignee_id: int | None = None
    tags: list[str] | None = None


class DeleteTicketInput(_CredFields):
    ticket_id: int = Field(description="Ticket ID")


class GetTicketInput(_CredFields):
    ticket_id: int = Field(description="Ticket ID")


class ListTicketsInput(_CredFields):
    sort_by: str | None = None
    sort_order: str | None = "desc"
    per_page: int | None = 25


class SearchTicketsInput(_CredFields):
    query: str = Field(description="Search query")
    sort_by: str | None = None
    sort_order: str | None = "desc"
    per_page: int | None = 25


class _TicketTagsInput(_CredFields):
    ticket_id: int = Field(description="Ticket ID")
    tags: list[str] = Field(description="Tags")


class ListTicketCommentsInput(_CredFields):
    ticket_id: int = Field(description="Ticket ID")
    sort_order: str | None = "asc"
    per_page: int | None = 25


class SetCustomFieldsInput(_CredFields):
    ticket_id: int = Field(description="Ticket ID")
    custom_fields: list[dict[str, Any]] = Field(description="Custom field objects")


class GetUserInput(_CredFields):
    user_id: int = Field(description="User ID")


class ListLocalesInput(_CredFields):
    pass


class ListMacrosInput(_CredFields):
    access: str | None = None
    active: bool | None = None
    category: int | None = None
    group_id: int | None = None
    sort_by: str | None = None
    sort_order: str | None = "asc"
    per_page: int | None = 25


class GetMacroInput(_CredFields):
    macro_id: int = Field(description="Macro ID")


class ListArticlesInput(_CredFields):
    locale: str | None = None
    category_id: int | None = None
    section_id: int | None = None
    per_page: int | None = 25


class GetArticleInput(_CredFields):
    article_id: int = Field(description="Article ID")
    locale: str | None = None


# --- Tools — tickets -------------------------------------------------------


@tool(args_schema=CreateTicketInput)
@serialize_pydantic_return
async def create_ticket(
    subdomain: str,
    email: str,
    api_key: str,
    subject: str,
    comment_body: str,
    priority: str | None = None,
    status: str | None = None,
    requester_email: str | None = None,
    assignee_id: int | None = None,
    tags: list[str] | None = None,
    custom_fields: list[dict[str, Any]] | None = None,
) -> CreateTicketOutput:
    """Create a new support ticket."""
    ticket_data: dict[str, Any] = {
        "subject": subject,
        "comment": {"body": comment_body},
    }
    if priority:
        ticket_data["priority"] = priority
    if status:
        ticket_data["status"] = status
    if requester_email:
        ticket_data["requester"] = {"email": requester_email}
    if assignee_id:
        ticket_data["assignee_id"] = assignee_id
    if tags:
        ticket_data["tags"] = tags
    if custom_fields:
        ticket_data["custom_fields"] = custom_fields

    ok, e, data = await _call(
        "POST",
        subdomain,
        email,
        api_key,
        "/tickets.json",
        json_body={"ticket": ticket_data},
        success_codes=(200, 201),
    )
    if not ok:
        return CreateTicketOutput(success=False, error=e)
    ticket = data.get("ticket") or {}
    return CreateTicketOutput(
        success=True,
        id=ticket.get("id"),
        subject=ticket.get("subject"),
        status=ticket.get("status"),
        priority=ticket.get("priority"),
        created_at=ticket.get("created_at"),
        ticket=ticket,
    )


@tool(args_schema=UpdateTicketInput)
@serialize_pydantic_return
async def update_ticket(
    subdomain: str,
    email: str,
    api_key: str,
    ticket_id: int,
    subject: str | None = None,
    comment_body: str | None = None,
    comment_public: bool | None = True,
    priority: str | None = None,
    status: str | None = None,
    assignee_id: int | None = None,
    tags: list[str] | None = None,
) -> UpdateTicketOutput:
    """Update an existing ticket."""
    ticket_data: dict[str, Any] = {}
    if subject:
        ticket_data["subject"] = subject
    if comment_body:
        ticket_data["comment"] = {
            "body": comment_body,
            "public": comment_public,
        }
    if priority:
        ticket_data["priority"] = priority
    if status:
        ticket_data["status"] = status
    if assignee_id:
        ticket_data["assignee_id"] = assignee_id
    if tags is not None:
        ticket_data["tags"] = tags

    if not ticket_data:
        return UpdateTicketOutput(
            success=False, error="No update parameters provided"
        )

    ok, e, data = await _call(
        "PUT",
        subdomain,
        email,
        api_key,
        f"/tickets/{ticket_id}.json",
        json_body={"ticket": ticket_data},
    )
    if not ok:
        return UpdateTicketOutput(success=False, error=e)
    ticket = data.get("ticket") or {}
    return UpdateTicketOutput(
        success=True,
        id=ticket.get("id"),
        subject=ticket.get("subject"),
        status=ticket.get("status"),
        priority=ticket.get("priority"),
        updated_at=ticket.get("updated_at"),
        ticket=ticket,
    )


@tool(args_schema=DeleteTicketInput)
@serialize_pydantic_return
async def delete_ticket(
    subdomain: str, email: str, api_key: str, ticket_id: int
) -> DeleteTicketOutput:
    """Delete a ticket."""
    ok, e, _ = await _call(
        "DELETE",
        subdomain,
        email,
        api_key,
        f"/tickets/{ticket_id}.json",
        success_codes=(200, 204),
    )
    if not ok:
        return DeleteTicketOutput(success=False, error=e)
    return DeleteTicketOutput(success=True, id=ticket_id, deleted=True)


@tool(args_schema=GetTicketInput)
@serialize_pydantic_return
async def get_ticket(
    subdomain: str, email: str, api_key: str, ticket_id: int
) -> GetTicketOutput:
    """Get a ticket by ID."""
    ok, e, data = await _call(
        "GET", subdomain, email, api_key, f"/tickets/{ticket_id}.json"
    )
    if not ok:
        return GetTicketOutput(success=False, error=e)
    return GetTicketOutput(success=True, result=data.get("ticket") or {})


@tool(args_schema=ListTicketsInput)
@serialize_pydantic_return
async def list_tickets(
    subdomain: str,
    email: str,
    api_key: str,
    sort_by: str | None = None,
    sort_order: str | None = "desc",
    per_page: int | None = 25,
) -> ListTicketsOutput:
    """List tickets with optional sorting."""
    params: dict[str, Any] = {"per_page": min(per_page or 25, 100)}
    if sort_by:
        params["sort_by"] = sort_by
    if sort_order:
        params["sort_order"] = sort_order
    ok, e, data = await _call(
        "GET", subdomain, email, api_key, "/tickets.json", params=params
    )
    if not ok:
        return ListTicketsOutput(success=False, error=e)
    tickets = data.get("tickets") or []
    return ListTicketsOutput(
        success=True,
        tickets=tickets,
        count=len(tickets),
        next_page=data.get("next_page"),
        previous_page=data.get("previous_page"),
    )


@tool(args_schema=SearchTicketsInput)
@serialize_pydantic_return
async def search_tickets(
    subdomain: str,
    email: str,
    api_key: str,
    query: str,
    sort_by: str | None = None,
    sort_order: str | None = "desc",
    per_page: int | None = 25,
) -> SearchTicketsOutput:
    """Search tickets using Zendesk search syntax."""
    params: dict[str, Any] = {
        "query": query,
        "per_page": min(per_page or 25, 100),
    }
    if sort_by:
        params["sort_by"] = sort_by
    if sort_order:
        params["sort_order"] = sort_order
    ok, e, data = await _call(
        "GET", subdomain, email, api_key, "/search.json", params=params
    )
    if not ok:
        return SearchTicketsOutput(success=False, error=e)
    results = data.get("results") or []
    return SearchTicketsOutput(
        success=True,
        results=results,
        count=data.get("count", len(results)),
        next_page=data.get("next_page"),
        previous_page=data.get("previous_page"),
    )


# --- Tools — ticket tags ---------------------------------------------------


@tool(args_schema=_TicketTagsInput)
@serialize_pydantic_return
async def add_ticket_tags(
    subdomain: str,
    email: str,
    api_key: str,
    ticket_id: int,
    tags: list[str],
) -> AddTicketTagsOutput:
    """Append tags to a ticket (additive)."""
    ok, e, data = await _call(
        "PUT",
        subdomain,
        email,
        api_key,
        f"/tickets/{ticket_id}/tags.json",
        json_body={"tags": tags},
    )
    if not ok:
        return AddTicketTagsOutput(success=False, error=e)
    return AddTicketTagsOutput(
        success=True,
        ticket_id=ticket_id,
        tags=data.get("tags") or [],
        added_count=len(tags),
    )


@tool(args_schema=_TicketTagsInput)
@serialize_pydantic_return
async def set_ticket_tags(
    subdomain: str,
    email: str,
    api_key: str,
    ticket_id: int,
    tags: list[str],
) -> SetTicketTagsOutput:
    """Replace all tags on a ticket."""
    ok, e, data = await _call(
        "POST",
        subdomain,
        email,
        api_key,
        f"/tickets/{ticket_id}/tags.json",
        json_body={"tags": tags},
    )
    if not ok:
        return SetTicketTagsOutput(success=False, error=e)
    return SetTicketTagsOutput(
        success=True,
        ticket_id=ticket_id,
        tags=data.get("tags") or [],
    )


@tool(args_schema=_TicketTagsInput)
@serialize_pydantic_return
async def remove_ticket_tags(
    subdomain: str,
    email: str,
    api_key: str,
    ticket_id: int,
    tags: list[str],
) -> RemoveTicketTagsOutput:
    """Remove specific tags from a ticket."""
    ok, e, data = await _call(
        "DELETE",
        subdomain,
        email,
        api_key,
        f"/tickets/{ticket_id}/tags.json",
        json_body={"tags": tags},
    )
    if not ok:
        return RemoveTicketTagsOutput(success=False, error=e)
    return RemoveTicketTagsOutput(
        success=True,
        ticket_id=ticket_id,
        tags=data.get("tags") or [],
        removed_count=len(tags),
    )


@tool(args_schema=ListTicketCommentsInput)
@serialize_pydantic_return
async def list_ticket_comments(
    subdomain: str,
    email: str,
    api_key: str,
    ticket_id: int,
    sort_order: str | None = "asc",
    per_page: int | None = 25,
) -> ListTicketCommentsOutput:
    """List comments on a ticket."""
    params: dict[str, Any] = {"per_page": min(per_page or 25, 100)}
    if sort_order:
        params["sort_order"] = sort_order
    ok, e, data = await _call(
        "GET",
        subdomain,
        email,
        api_key,
        f"/tickets/{ticket_id}/comments.json",
        params=params,
    )
    if not ok:
        return ListTicketCommentsOutput(success=False, error=e)
    comments = data.get("comments") or []
    return ListTicketCommentsOutput(
        success=True,
        ticket_id=ticket_id,
        comments=comments,
        count=len(comments),
        next_page=data.get("next_page"),
    )


@tool(args_schema=SetCustomFieldsInput)
@serialize_pydantic_return
async def set_custom_fields(
    subdomain: str,
    email: str,
    api_key: str,
    ticket_id: int,
    custom_fields: list[dict[str, Any]],
) -> SetCustomFieldsOutput:
    """Set custom field values on a ticket."""
    ok, e, data = await _call(
        "PUT",
        subdomain,
        email,
        api_key,
        f"/tickets/{ticket_id}.json",
        json_body={"ticket": {"custom_fields": custom_fields}},
    )
    if not ok:
        return SetCustomFieldsOutput(success=False, error=e)
    ticket = data.get("ticket") or {}
    return SetCustomFieldsOutput(
        success=True,
        id=ticket.get("id", ticket_id),
        custom_fields=ticket.get("custom_fields") or custom_fields,
    )


# --- Tools — users / locales / macros / articles --------------------------


@tool(args_schema=GetUserInput)
@serialize_pydantic_return
async def get_user(
    subdomain: str, email: str, api_key: str, user_id: int
) -> GetUserOutput:
    """Get a Zendesk user by ID."""
    ok, e, data = await _call(
        "GET", subdomain, email, api_key, f"/users/{user_id}.json"
    )
    if not ok:
        return GetUserOutput(success=False, error=e)
    return GetUserOutput(success=True, result=data.get("user") or {})


@tool(args_schema=ListLocalesInput)
@serialize_pydantic_return
async def list_locales(
    subdomain: str, email: str, api_key: str
) -> ListLocalesOutput:
    """List supported locales."""
    ok, e, data = await _call("GET", subdomain, email, api_key, "/locales.json")
    if not ok:
        return ListLocalesOutput(success=False, error=e)
    locales = data.get("locales") or []
    return ListLocalesOutput(success=True, locales=locales, count=len(locales))


@tool(args_schema=ListMacrosInput)
@serialize_pydantic_return
async def list_macros(
    subdomain: str,
    email: str,
    api_key: str,
    access: str | None = None,
    active: bool | None = None,
    category: int | None = None,
    group_id: int | None = None,
    sort_by: str | None = None,
    sort_order: str | None = "asc",
    per_page: int | None = 25,
) -> ListMacrosOutput:
    """List macros with filtering / sorting."""
    params: dict[str, Any] = {"per_page": min(per_page or 25, 100)}
    if access:
        params["access"] = access
    if active is not None:
        params["active"] = "true" if active else "false"
    if category is not None:
        params["category"] = category
    if group_id is not None:
        params["group_id"] = group_id
    if sort_by:
        params["sort_by"] = sort_by
    if sort_order:
        params["sort_order"] = sort_order
    ok, e, data = await _call(
        "GET", subdomain, email, api_key, "/macros.json", params=params
    )
    if not ok:
        return ListMacrosOutput(success=False, error=e)
    macros = data.get("macros") or []
    return ListMacrosOutput(
        success=True,
        macros=macros,
        count=len(macros),
        next_page=data.get("next_page"),
    )


@tool(args_schema=GetMacroInput)
@serialize_pydantic_return
async def get_macro(
    subdomain: str, email: str, api_key: str, macro_id: int
) -> GetMacroOutput:
    """Get a macro by ID."""
    ok, e, data = await _call(
        "GET", subdomain, email, api_key, f"/macros/{macro_id}.json"
    )
    if not ok:
        return GetMacroOutput(success=False, error=e)
    return GetMacroOutput(success=True, result=data.get("macro") or {})


@tool(args_schema=ListArticlesInput)
@serialize_pydantic_return
async def list_articles(
    subdomain: str,
    email: str,
    api_key: str,
    locale: str | None = None,
    category_id: int | None = None,
    section_id: int | None = None,
    per_page: int | None = 25,
) -> ListArticlesOutput:
    """List help-center articles."""
    base_path = (
        f"/help_center/{locale}/articles.json"
        if locale
        else "/help_center/articles.json"
    )
    params: dict[str, Any] = {"per_page": min(per_page or 25, 100)}
    if category_id is not None:
        params["category"] = category_id
    if section_id is not None:
        params["section"] = section_id
    ok, e, data = await _call(
        "GET", subdomain, email, api_key, base_path, params=params
    )
    if not ok:
        return ListArticlesOutput(success=False, error=e)
    articles = data.get("articles") or []
    return ListArticlesOutput(
        success=True,
        articles=articles,
        count=len(articles),
        next_page=data.get("next_page"),
    )


@tool(args_schema=GetArticleInput)
@serialize_pydantic_return
async def get_article(
    subdomain: str,
    email: str,
    api_key: str,
    article_id: int,
    locale: str | None = None,
) -> GetArticleOutput:
    """Get a help-center article by ID."""
    path = (
        f"/help_center/{locale}/articles/{article_id}.json"
        if locale
        else f"/help_center/articles/{article_id}.json"
    )
    ok, e, data = await _call("GET", subdomain, email, api_key, path)
    if not ok:
        return GetArticleOutput(success=False, error=e)
    return GetArticleOutput(success=True, result=data.get("article") or {})

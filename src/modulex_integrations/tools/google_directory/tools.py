"""Google Directory LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_directory.outputs import (
    AddMemberToGroupOutput,
    CreateGroupOutput,
    CreateUserOutput,
    GetGroupOutput,
    GetUserOutput,
    GroupResource,
    ListGroupsOutput,
    ListUsersOutput,
    MemberResource,
    UserResource,
)

__all__ = [
    "add_member_to_group",
    "create_group",
    "create_user",
    "get_group",
    "get_user",
    "list_groups",
    "list_users",
]

_BASE_URL = "https://admin.googleapis.com/admin/directory/v1"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Google Admin SDK API."""
    headers: dict[str, str] = {"Accept": "application/json", "Content-Type": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _parse_member(data: dict[str, Any]) -> MemberResource:
    return MemberResource(
        id=data.get("id"),
        email=data.get("email"),
        role=data.get("role"),
        type=data.get("type"),
        status=data.get("status"),
        kind=data.get("kind"),
        etag=data.get("etag"),
    )


def _parse_group(data: dict[str, Any]) -> GroupResource:
    return GroupResource(
        id=data.get("id"),
        email=data.get("email"),
        name=data.get("name"),
        description=data.get("description"),
        direct_members_count=data.get("directMembersCount"),
        kind=data.get("kind"),
        etag=data.get("etag"),
        admin_created=data.get("adminCreated"),
    )


def _parse_user(data: dict[str, Any]) -> UserResource:
    name_obj = data.get("name") or {}
    return UserResource(
        id=data.get("id"),
        primary_email=data.get("primaryEmail"),
        given_name=name_obj.get("givenName"),
        family_name=name_obj.get("familyName"),
        is_admin=data.get("isAdmin"),
        is_delegated_admin=data.get("isDelegatedAdmin"),
        kind=data.get("kind"),
        etag=data.get("etag"),
        creation_time=data.get("creationTime"),
        org_unit_path=data.get("orgUnitPath"),
    )


# --- Input schemas --------------------------------------------------------


class AddMemberToGroupInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    group_id: str = Field(description="The group ID or email address of the target group")
    email: str = Field(description="The email address of the member to add")
    role: str = Field(default="MEMBER", description="The role of the member: MEMBER, OWNER, or MANAGER")


class CreateGroupInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    email: str = Field(description="The group's email address (domain must be associated with the account)")
    name: str = Field(description="The group name")
    description: str | None = Field(default=None, description="Description of the group")


class CreateUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    email: str = Field(description="The user's primary email address (domain must be associated with the account)")
    password: str = Field(description="The password for the user account")
    first_name: str = Field(description="First name of the user")
    last_name: str = Field(description="Last name of the user")
    phone: str | None = Field(default=None, description="Phone number of the user")
    notes: str | None = Field(default=None, description="Notes for the user")


class GetGroupInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    group_id: str = Field(description="The group ID or email address of the group to retrieve")


class GetUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_id: str = Field(description="The user ID or primary email address of the user to retrieve")


class ListGroupsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    max_results: int | None = Field(default=None, description="Maximum number of groups to return (default returns all)")
    page_token: str | None = Field(default=None, description="Token for fetching the next page of results")


class ListUsersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    max_results: int | None = Field(default=None, description="Maximum number of users to return (default returns all)")
    page_token: str | None = Field(default=None, description="Token for fetching the next page of results")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AddMemberToGroupInput)
@serialize_pydantic_return
async def add_member_to_group(
    auth_type: str,
    auth_data: dict[str, Any],
    group_id: str,
    email: str,
    role: str = "MEMBER",
) -> AddMemberToGroupOutput:
    """Adds a member to a Google Workspace group"""
    headers = _get_auth_headers(auth_type, auth_data)
    payload = {"email": email, "role": role}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/groups/{group_id}/members",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
    return AddMemberToGroupOutput(success=True, member=_parse_member(data))


@tool(args_schema=CreateGroupInput)
@serialize_pydantic_return
async def create_group(
    auth_type: str,
    auth_data: dict[str, Any],
    email: str,
    name: str,
    description: str | None = None,
) -> CreateGroupOutput:
    """Creates a new Google Workspace group"""
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {"email": email, "name": name}
    if description is not None:
        payload["description"] = description
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/groups",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
    return CreateGroupOutput(success=True, group=_parse_group(data))


@tool(args_schema=CreateUserInput)
@serialize_pydantic_return
async def create_user(
    auth_type: str,
    auth_data: dict[str, Any],
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    phone: str | None = None,
    notes: str | None = None,
) -> CreateUserOutput:
    """Creates a new Google Workspace user"""
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {
        "primaryEmail": email,
        "password": password,
        "name": {"givenName": first_name, "familyName": last_name},
    }
    if phone is not None:
        payload["phones"] = [{"value": phone, "type": "work"}]
    if notes is not None:
        payload["notes"] = {"contentType": "text_plain", "value": notes}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/users",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
    return CreateUserOutput(success=True, user=_parse_user(data))


@tool(args_schema=GetGroupInput)
@serialize_pydantic_return
async def get_group(
    auth_type: str,
    auth_data: dict[str, Any],
    group_id: str,
) -> GetGroupOutput:
    """Retrieves information about a Google Workspace group"""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/groups/{group_id}",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    return GetGroupOutput(success=True, group=_parse_group(data))


@tool(args_schema=GetUserInput)
@serialize_pydantic_return
async def get_user(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str,
) -> GetUserOutput:
    """Retrieves information about a Google Workspace user"""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/users/{user_id}",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    return GetUserOutput(success=True, user=_parse_user(data))


@tool(args_schema=ListGroupsInput)
@serialize_pydantic_return
async def list_groups(
    auth_type: str,
    auth_data: dict[str, Any],
    max_results: int | None = None,
    page_token: str | None = None,
) -> ListGroupsOutput:
    """Retrieves a list of all groups in the Google Workspace directory"""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"customer": "my_customer"}
    if max_results is not None:
        params["maxResults"] = max_results
    if page_token is not None:
        params["pageToken"] = page_token
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/groups",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()
    groups = [_parse_group(g) for g in data.get("groups", [])]
    return ListGroupsOutput(success=True, groups=groups)


@tool(args_schema=ListUsersInput)
@serialize_pydantic_return
async def list_users(
    auth_type: str,
    auth_data: dict[str, Any],
    max_results: int | None = None,
    page_token: str | None = None,
) -> ListUsersOutput:
    """Retrieves a list of all users in the Google Workspace directory"""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"customer": "my_customer"}
    if max_results is not None:
        params["maxResults"] = max_results
    if page_token is not None:
        params["pageToken"] = page_token
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/users",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()
    users = [_parse_user(u) for u in data.get("users", [])]
    return ListUsersOutput(success=True, users=users)

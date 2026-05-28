"""Microsoft Entra ID LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.microsoft_entra_id.outputs import (
    AddMemberToGroupOutput,
    CreateGroupOutput,
    DeleteGroupOutput,
    GetManagerOutput,
    GetMs365GroupsOutput,
    GetOrganizationGroupsOutput,
    GetOrganizationUsersOutput,
    GetProfileOutput,
    GroupSummary,
    ManagerInfo,
    RemoveMemberFromGroupOutput,
    SearchGroupsOutput,
    UpdateGroupOutput,
    UpdateUserOutput,
    UserSummary,
)

__all__ = [
    "add_member_to_group",
    "create_group",
    "delete_group",
    "get_manager",
    "get_ms365_groups",
    "get_organization_groups",
    "get_organization_users",
    "get_profile",
    "remove_member_from_group",
    "search_groups",
    "update_group",
    "update_user",
]

_BASE_URL = "https://graph.microsoft.com/v1.0"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for Microsoft Graph API based on auth_type/auth_data."""
    headers: dict[str, str] = {
        "Content-Type": "application/json",
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


async def _collect_odata_values(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    params: dict[str, str] | None = None,
    max_items: int | None = None,
    max_pages: int = 50,
) -> list[dict[str, Any]]:
    """Page through OData @odata.nextLink responses."""
    results: list[dict[str, Any]] = []
    next_url: str | None = url
    pages_seen = 0
    while next_url and pages_seen < max_pages:
        pages_seen += 1
        response = await client.get(next_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        values = data.get("value", [])
        results.extend(values)
        if max_items and len(results) >= max_items:
            results = results[:max_items]
            break
        next_url = data.get("@odata.nextLink")
        params = None
    return results


# --- Input schemas --------------------------------------------------------


class AddMemberToGroupInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    group_id: str = Field(description="Identifier of the group")
    user_id: str = Field(description="Identifier of the user to add")


class CreateGroupInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    display_name: str = Field(description="The name to display in the address book for the group")
    mail_enabled: bool = Field(description="Set to true for mail-enabled groups")
    mail_nickname: str = Field(description="The mail alias for the group, unique for groups in the organization. Maximum length is 64 characters.")
    security_enabled: bool = Field(description="Set to true for security-enabled groups")


class DeleteGroupInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    group_id: str = Field(description="Identifier of the group to delete")


class GetManagerInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_id: str | None = Field(default=None, description="Identifier of the user. Leave empty to use the signed-in user.")


class GetMs365GroupsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_id: str | None = Field(default=None, description="Identifier of the user. Leave empty to use the signed-in user.")


class GetOrganizationGroupsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class GetOrganizationUsersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    max_users: int | None = Field(default=None, description="Maximum number of users to return. Omit for no limit.")
    filter: str | None = Field(default="accountEnabled eq true", description="OData filter expression, e.g. 'accountEnabled eq true'")
    search: str | None = Field(default=None, description="OData search expression, e.g. '\"displayName:John\"'")


class GetProfileInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_id: str | None = Field(default=None, description="Identifier of the user. Leave empty to use the signed-in user.")


class RemoveMemberFromGroupInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    group_id: str = Field(description="Identifier of the group")
    user_id: str = Field(description="Identifier of the user to remove")


class SearchGroupsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    query: str = Field(description="Keywords to search by")
    max_results: int = Field(default=100, description="The maximum number of groups to return")


class UpdateGroupInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    group_id: str = Field(description="Identifier of the group to update")
    allow_external_senders: bool | None = Field(default=None, description="Whether people external to the organization can send messages to the group")
    auto_subscribe_new_members: bool | None = Field(default=None, description="Whether new members added to the group will be auto-subscribed to receive email notifications")
    description: str | None = Field(default=None, description="An optional description for the group")
    display_name: str | None = Field(default=None, description="The name to display in the address book for the group")
    mail_nickname: str | None = Field(default=None, description="The mail alias for the group. Maximum length is 64 characters.")
    security_enabled: bool | None = Field(default=None, description="Set to true for security-enabled groups")
    visibility: str | None = Field(default=None, description="Specifies the visibility of the group. Allowed values: Public, Private.")


class UpdateUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_id: str = Field(description="Identifier of the user to update")
    display_name: str | None = Field(default=None, description="The name to display in the address book for the user")
    mail: str | None = Field(default=None, description="The SMTP address for the user")
    mail_nickname: str | None = Field(default=None, description="The mail alias for the user")
    account_enabled: bool | None = Field(default=True, description="Whether the account is enabled")
    street_address: str | None = Field(default=None, description="The street address of the user's place of business")
    city: str | None = Field(default=None, description="The city in which the user is located")
    state: str | None = Field(default=None, description="The state or province in the user's address")
    postal_code: str | None = Field(default=None, description="The postal code for the user's postal address")
    country: str | None = Field(default=None, description="The country/region in which the user is located")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AddMemberToGroupInput)
@serialize_pydantic_return
async def add_member_to_group(
    auth_type: str,
    auth_data: dict[str, Any],
    group_id: str,
    user_id: str,
) -> AddMemberToGroupOutput:
    """Add a user as a member to a Microsoft Entra ID group."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return AddMemberToGroupOutput(success=False, error="Missing access token. Please re-authenticate.")
    headers = _get_auth_headers(auth_type, auth_data)
    body = {"@odata.id": f"{_BASE_URL}/directoryObjects/{user_id}"}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/groups/{group_id}/members/$ref",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 204):
            return AddMemberToGroupOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return AddMemberToGroupOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddMemberToGroupOutput(success=False, error=f"Call failed: {exc}")
    return AddMemberToGroupOutput(success=True)


@tool(args_schema=CreateGroupInput)
@serialize_pydantic_return
async def create_group(
    auth_type: str,
    auth_data: dict[str, Any],
    display_name: str,
    mail_enabled: bool,
    mail_nickname: str,
    security_enabled: bool,
) -> CreateGroupOutput:
    """Create a new group in Microsoft Entra ID."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return CreateGroupOutput(success=False, error="Missing access token. Please re-authenticate.")
    headers = _get_auth_headers(auth_type, auth_data)
    body = {
        "displayName": display_name,
        "mailEnabled": mail_enabled,
        "mailNickname": mail_nickname,
        "securityEnabled": security_enabled,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/groups",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateGroupOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateGroupOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateGroupOutput(success=False, error=f"Call failed: {exc}")
    return CreateGroupOutput(
        success=True,
        group=GroupSummary(
            id=data.get("id"),
            display_name=data.get("displayName"),
            description=data.get("description"),
            mail_enabled=data.get("mailEnabled"),
            mail_nickname=data.get("mailNickname"),
            security_enabled=data.get("securityEnabled"),
            group_types=data.get("groupTypes", []),
        ),
    )


@tool(args_schema=DeleteGroupInput)
@serialize_pydantic_return
async def delete_group(
    auth_type: str,
    auth_data: dict[str, Any],
    group_id: str,
) -> DeleteGroupOutput:
    """Delete a group in Microsoft Entra ID."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return DeleteGroupOutput(success=False, error="Missing access token. Please re-authenticate.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/groups/{group_id}",
                headers=headers,
            )
        if response.status_code not in (200, 204):
            return DeleteGroupOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteGroupOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteGroupOutput(success=False, error=f"Call failed: {exc}")
    return DeleteGroupOutput(success=True)


@tool(args_schema=GetManagerInput)
@serialize_pydantic_return
async def get_manager(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str | None = None,
) -> GetManagerOutput:
    """Get the user's manager information. Returns the user or organizational contact assigned as the user's manager."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return GetManagerOutput(success=False, error="Missing access token. Please re-authenticate.")
    headers = _get_auth_headers(auth_type, auth_data)
    path = f"/users/{user_id}/manager" if user_id else "/me/manager"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}{path}",
                headers=headers,
            )
        if response.status_code == 404:
            return GetManagerOutput(
                success=True,
                message="No manager assigned for this user.",
            )
        if response.status_code != 200:
            return GetManagerOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetManagerOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetManagerOutput(success=False, error=f"Call failed: {exc}")
    return GetManagerOutput(
        success=True,
        manager=ManagerInfo(
            id=data.get("id"),
            display_name=data.get("displayName"),
            email=data.get("mail"),
            job_title=data.get("jobTitle"),
            mobile_phone=data.get("mobilePhone"),
        ),
    )


@tool(args_schema=GetMs365GroupsInput)
@serialize_pydantic_return
async def get_ms365_groups(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str | None = None,
) -> GetMs365GroupsOutput:
    """Get the user's Microsoft 365 groups (unified groups). Returns groups the user is a direct member of."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return GetMs365GroupsOutput(success=False, error="Missing access token. Please re-authenticate.")
    headers = _get_auth_headers(auth_type, auth_data)
    path = f"/users/{user_id}/memberOf/microsoft.graph.group" if user_id else "/me/memberOf/microsoft.graph.group"
    params = {"$filter": "groupTypes/any(a:a eq 'Unified')"}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            values = await _collect_odata_values(
                client, f"{_BASE_URL}{path}", headers, params=params,
            )
    except httpx.HTTPStatusError as exc:
        return GetMs365GroupsOutput(
            success=False,
            error=f"API error ({exc.response.status_code}): {exc.response.text}",
        )
    except httpx.TimeoutException:
        return GetMs365GroupsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetMs365GroupsOutput(success=False, error=f"Call failed: {exc}")
    groups = [
        GroupSummary(
            id=g.get("id"),
            display_name=g.get("displayName"),
            description=g.get("description"),
            group_types=g.get("groupTypes", []),
        )
        for g in values
    ]
    return GetMs365GroupsOutput(success=True, groups=groups)


@tool(args_schema=GetOrganizationGroupsInput)
@serialize_pydantic_return
async def get_organization_groups(
    auth_type: str,
    auth_data: dict[str, Any],
) -> GetOrganizationGroupsOutput:
    """List all groups in the organization (excluding dynamic distribution groups)."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return GetOrganizationGroupsOutput(success=False, error="Missing access token. Please re-authenticate.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            values = await _collect_odata_values(
                client, f"{_BASE_URL}/groups", headers,
            )
    except httpx.HTTPStatusError as exc:
        return GetOrganizationGroupsOutput(
            success=False,
            error=f"API error ({exc.response.status_code}): {exc.response.text}",
        )
    except httpx.TimeoutException:
        return GetOrganizationGroupsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetOrganizationGroupsOutput(success=False, error=f"Call failed: {exc}")
    groups = [
        GroupSummary(
            id=g.get("id"),
            display_name=g.get("displayName"),
            description=g.get("description"),
            mail_enabled=g.get("mailEnabled"),
            deleted_date_time=g.get("deletedDateTime"),
        )
        for g in values
    ]
    return GetOrganizationGroupsOutput(success=True, groups=groups)


@tool(args_schema=GetOrganizationUsersInput)
@serialize_pydantic_return
async def get_organization_users(
    auth_type: str,
    auth_data: dict[str, Any],
    max_users: int | None = None,
    filter: str | None = "accountEnabled eq true",
    search: str | None = None,
) -> GetOrganizationUsersOutput:
    """List all users in the organization. By default returns only enabled accounts."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return GetOrganizationUsersOutput(success=False, error="Missing access token. Please re-authenticate.")
    headers = _get_auth_headers(auth_type, auth_data)
    if search:
        headers["ConsistencyLevel"] = "eventual"
    params: dict[str, str] = {}
    if filter:
        params["$filter"] = filter
    if search:
        params["$search"] = search
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            values = await _collect_odata_values(
                client,
                f"{_BASE_URL}/users",
                headers,
                params=params if params else None,
                max_items=max_users,
            )
    except httpx.HTTPStatusError as exc:
        return GetOrganizationUsersOutput(
            success=False,
            error=f"API error ({exc.response.status_code}): {exc.response.text}",
        )
    except httpx.TimeoutException:
        return GetOrganizationUsersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetOrganizationUsersOutput(success=False, error=f"Call failed: {exc}")
    users = [
        UserSummary(
            id=u.get("id"),
            full_name=u.get("displayName"),
            email=u.get("mail"),
            user_principal_name=u.get("userPrincipalName"),
            surname=u.get("surname"),
            given_name=u.get("givenName"),
            job_title=u.get("jobTitle"),
            mobile_phone=u.get("mobilePhone"),
        )
        for u in values
    ]
    return GetOrganizationUsersOutput(success=True, users=users)


@tool(args_schema=GetProfileInput)
@serialize_pydantic_return
async def get_profile(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str | None = None,
) -> GetProfileOutput:
    """Get the user's profile information from Microsoft Entra ID."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return GetProfileOutput(success=False, error="Missing access token. Please re-authenticate.")
    headers = _get_auth_headers(auth_type, auth_data)
    path = f"/users/{user_id}" if user_id else "/me"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}{path}",
                headers=headers,
            )
        if response.status_code != 200:
            return GetProfileOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetProfileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetProfileOutput(success=False, error=f"Call failed: {exc}")
    return GetProfileOutput(success=True, data=data)


@tool(args_schema=RemoveMemberFromGroupInput)
@serialize_pydantic_return
async def remove_member_from_group(
    auth_type: str,
    auth_data: dict[str, Any],
    group_id: str,
    user_id: str,
) -> RemoveMemberFromGroupOutput:
    """Remove a member from a Microsoft Entra ID group."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return RemoveMemberFromGroupOutput(success=False, error="Missing access token. Please re-authenticate.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/groups/{group_id}/members/{user_id}/$ref",
                headers=headers,
            )
        if response.status_code not in (200, 204):
            return RemoveMemberFromGroupOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return RemoveMemberFromGroupOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RemoveMemberFromGroupOutput(success=False, error=f"Call failed: {exc}")
    return RemoveMemberFromGroupOutput(success=True)


@tool(args_schema=SearchGroupsInput)
@serialize_pydantic_return
async def search_groups(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
    max_results: int = 100,
) -> SearchGroupsOutput:
    """Search for groups by name or description in Microsoft Entra ID."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return SearchGroupsOutput(success=False, error="Missing access token. Please re-authenticate.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["ConsistencyLevel"] = "eventual"
    params = {
        "$search": f'"displayName:{query}" OR "description:{query}"',
        "$top": str(max_results),
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/groups",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return SearchGroupsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchGroupsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchGroupsOutput(success=False, error=f"Call failed: {exc}")
    groups = [
        GroupSummary(
            id=g.get("id"),
            display_name=g.get("displayName"),
            description=g.get("description"),
            mail_enabled=g.get("mailEnabled"),
            security_enabled=g.get("securityEnabled"),
            group_types=g.get("groupTypes", []),
        )
        for g in data.get("value", [])
    ]
    return SearchGroupsOutput(success=True, groups=groups)


@tool(args_schema=UpdateGroupInput)
@serialize_pydantic_return
async def update_group(
    auth_type: str,
    auth_data: dict[str, Any],
    group_id: str,
    allow_external_senders: bool | None = None,
    auto_subscribe_new_members: bool | None = None,
    description: str | None = None,
    display_name: str | None = None,
    mail_nickname: str | None = None,
    security_enabled: bool | None = None,
    visibility: str | None = None,
) -> UpdateGroupOutput:
    """Update an existing group in Microsoft Entra ID."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return UpdateGroupOutput(success=False, error="Missing access token. Please re-authenticate.")
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {}
    if allow_external_senders is not None:
        body["allowExternalSenders"] = allow_external_senders
    if auto_subscribe_new_members is not None:
        body["autoSubscribeNewMembers"] = auto_subscribe_new_members
    if description is not None:
        body["description"] = description
    if display_name is not None:
        body["displayName"] = display_name
    if mail_nickname is not None:
        body["mailNickname"] = mail_nickname
    if security_enabled is not None:
        body["securityEnabled"] = security_enabled
    if visibility is not None:
        body["visibility"] = visibility
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/groups/{group_id}",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 204):
            return UpdateGroupOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return UpdateGroupOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateGroupOutput(success=False, error=f"Call failed: {exc}")
    return UpdateGroupOutput(success=True)


@tool(args_schema=UpdateUserInput)
@serialize_pydantic_return
async def update_user(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str,
    display_name: str | None = None,
    mail: str | None = None,
    mail_nickname: str | None = None,
    account_enabled: bool | None = True,
    street_address: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country: str | None = None,
) -> UpdateUserOutput:
    """Update an existing user in Microsoft Entra ID."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return UpdateUserOutput(success=False, error="Missing access token. Please re-authenticate.")
    headers = _get_auth_headers(auth_type, auth_data)
    field_map: dict[str, tuple[str, Any]] = {
        "displayName": ("display_name", display_name),
        "mail": ("mail", mail),
        "mailNickname": ("mail_nickname", mail_nickname),
        "accountEnabled": ("account_enabled", account_enabled),
        "streetAddress": ("street_address", street_address),
        "city": ("city", city),
        "state": ("state", state),
        "postalCode": ("postal_code", postal_code),
        "country": ("country", country),
    }
    body: dict[str, Any] = {}
    for graph_key, (_, value) in field_map.items():
        if value is not None:
            body[graph_key] = value
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/users/{user_id}",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 204):
            return UpdateUserOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return UpdateUserOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateUserOutput(success=False, error=f"Call failed: {exc}")
    return UpdateUserOutput(success=True)

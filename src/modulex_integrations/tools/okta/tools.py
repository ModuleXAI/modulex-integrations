"""Okta LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.okta.outputs import (
    CreateUserOutput,
    GetUserOutput,
    ListTypeIdOptionsOutput,
    TypeIdOption,
    UpdateUserOutput,
    UserResource,
)

__all__ = [
    "create_user",
    "get_user",
    "list_type_id_options",
    "update_user",
]

_TIMEOUT = 30.0


def _resolve_credentials(auth_data: dict[str, Any]) -> tuple[str, str]:
    """Pull (subdomain, api_token) out of the runtime-injected auth_data."""
    subdomain = str(auth_data.get("subdomain") or "").strip()
    api_token = str(auth_data.get("api_token") or "").strip()
    return subdomain, api_token


def _base_url(subdomain: str) -> str:
    """Build the tenant-scoped REST base URL."""
    return f"https://{subdomain}.okta.com/api/v1"


def _headers(api_token: str) -> dict[str, str]:
    return {
        "Authorization": f"SSWS {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json; okta-version=1.0.0",
    }


def _missing_creds_message() -> str:
    return (
        "Missing Okta credentials. Configure both 'subdomain' (e.g. 'acme' "
        "for acme.okta.com) and 'api_token' (an SSWS token from the Okta "
        "admin console)."
    )


def _coerce_user(data: dict[str, Any] | None) -> UserResource | None:
    if not isinstance(data, dict):
        return None
    return UserResource.model_validate(data)


# --- Input schemas --------------------------------------------------------


class CreateUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type (custom for Okta)")
    auth_data: dict[str, Any] = Field(
        description=(
            "Authentication data containing 'subdomain' and 'api_token' "
            "fields for the Okta tenant."
        )
    )
    first_name: str = Field(description="The first name of the user.")
    last_name: str = Field(description="The last name of the user.")
    email: str = Field(description="The email address of the user.")
    login: str = Field(description="The login for the user.")
    mobile_phone: str | None = Field(
        default=None, description="Optional mobile phone number."
    )
    type_id: str | None = Field(
        default=None,
        description="Optional user type ID (see list_type_id_options).",
    )
    activate: bool = Field(
        default=True,
        description="Execute the activation lifecycle on creation.",
    )


class GetUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type (custom for Okta)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data with 'subdomain' and 'api_token'."
    )
    user_id: str = Field(
        description="The Okta user ID, login, or email of the user."
    )


class ListTypeIdOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (custom for Okta)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data with 'subdomain' and 'api_token'."
    )


class UpdateUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type (custom for Okta)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data with 'subdomain' and 'api_token'."
    )
    user_id: str = Field(
        description="The Okta user ID of the user to update."
    )
    first_name: str | None = Field(default=None, description="New first name.")
    last_name: str | None = Field(default=None, description="New last name.")
    email: str | None = Field(default=None, description="New email address.")
    login: str | None = Field(default=None, description="New login.")
    mobile_phone: str | None = Field(
        default=None, description="New mobile phone number."
    )
    type_id: str | None = Field(
        default=None, description="Optional new user type ID."
    )


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateUserInput)
@serialize_pydantic_return
async def create_user(
    auth_type: str,
    auth_data: dict[str, Any],
    first_name: str,
    last_name: str,
    email: str,
    login: str,
    mobile_phone: str | None = None,
    type_id: str | None = None,
    activate: bool = True,
) -> CreateUserOutput:
    """Create a new user in the Okta tenant."""
    del auth_type  # custom auth — fields read out of auth_data directly
    subdomain, api_token = _resolve_credentials(auth_data)
    if not subdomain or not api_token:
        return CreateUserOutput(success=False, error=_missing_creds_message())

    profile: dict[str, Any] = {
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "login": login,
    }
    if mobile_phone:
        profile["mobilePhone"] = mobile_phone
    body: dict[str, Any] = {"profile": profile}
    if type_id:
        body["type"] = {"id": type_id}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(subdomain)}/users",
                headers=_headers(api_token),
                params={"activate": "true" if activate else "false"},
                json=body,
            )
        if response.status_code >= 400:
            return CreateUserOutput(
                success=False,
                error=f"Okta API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateUserOutput(success=False, error="Request to Okta timed out.")
    except Exception as exc:
        return CreateUserOutput(success=False, error=f"Call to Okta failed: {exc}")

    return CreateUserOutput(success=True, user=_coerce_user(data))


@tool(args_schema=GetUserInput)
@serialize_pydantic_return
async def get_user(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str,
) -> GetUserOutput:
    """Fetch a single Okta user by ID, login, or email."""
    del auth_type
    subdomain, api_token = _resolve_credentials(auth_data)
    if not subdomain or not api_token:
        return GetUserOutput(success=False, error=_missing_creds_message())

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(subdomain)}/users/{user_id}",
                headers=_headers(api_token),
            )
        if response.status_code >= 400:
            return GetUserOutput(
                success=False,
                error=f"Okta API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetUserOutput(success=False, error="Request to Okta timed out.")
    except Exception as exc:
        return GetUserOutput(success=False, error=f"Call to Okta failed: {exc}")

    return GetUserOutput(success=True, user=_coerce_user(data))


@tool(args_schema=ListTypeIdOptionsInput)
@serialize_pydantic_return
async def list_type_id_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListTypeIdOptionsOutput:
    """List available user-type options (id + display name)."""
    del auth_type
    subdomain, api_token = _resolve_credentials(auth_data)
    if not subdomain or not api_token:
        return ListTypeIdOptionsOutput(
            success=False, error=_missing_creds_message()
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(subdomain)}/meta/types/user",
                headers=_headers(api_token),
            )
        if response.status_code >= 400:
            return ListTypeIdOptionsOutput(
                success=False,
                error=f"Okta API error ({response.status_code}): {response.text}",
            )
        rows = response.json()
    except httpx.TimeoutException:
        return ListTypeIdOptionsOutput(
            success=False, error="Request to Okta timed out."
        )
    except Exception as exc:
        return ListTypeIdOptionsOutput(
            success=False, error=f"Call to Okta failed: {exc}"
        )

    options: list[TypeIdOption] = []
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            options.append(
                TypeIdOption(
                    label=row.get("displayName"),
                    value=row.get("id"),
                )
            )
    return ListTypeIdOptionsOutput(success=True, options=options)


@tool(args_schema=UpdateUserInput)
@serialize_pydantic_return
async def update_user(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    login: str | None = None,
    mobile_phone: str | None = None,
    type_id: str | None = None,
) -> UpdateUserOutput:
    """Update the profile of an existing Okta user.

    The existing profile is fetched first and merged with the caller's
    updates so unspecified fields are preserved (the Okta PUT endpoint
    replaces the whole profile otherwise).
    """
    del auth_type
    subdomain, api_token = _resolve_credentials(auth_data)
    if not subdomain or not api_token:
        return UpdateUserOutput(success=False, error=_missing_creds_message())

    headers = _headers(api_token)
    base = _base_url(subdomain)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            existing = await client.get(f"{base}/users/{user_id}", headers=headers)
            if existing.status_code >= 400:
                return UpdateUserOutput(
                    success=False,
                    error=(
                        "Okta API error fetching existing user "
                        f"({existing.status_code}): {existing.text}"
                    ),
                )
            existing_profile = (existing.json() or {}).get("profile") or {}

            merged_profile: dict[str, Any] = dict(existing_profile)
            updates: dict[str, Any] = {
                "firstName": first_name,
                "lastName": last_name,
                "email": email,
                "login": login,
                "mobilePhone": mobile_phone,
            }
            for key, value in updates.items():
                if value is not None:
                    merged_profile[key] = value

            body: dict[str, Any] = {"profile": merged_profile}
            if type_id:
                body["type"] = {"id": type_id}

            response = await client.put(
                f"{base}/users/{user_id}", headers=headers, json=body
            )
        if response.status_code >= 400:
            return UpdateUserOutput(
                success=False,
                error=f"Okta API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateUserOutput(success=False, error="Request to Okta timed out.")
    except Exception as exc:
        return UpdateUserOutput(success=False, error=f"Call to Okta failed: {exc}")

    return UpdateUserOutput(success=True, user=_coerce_user(data))

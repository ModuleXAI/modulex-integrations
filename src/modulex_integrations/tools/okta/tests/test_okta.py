"""Happy-path tests for every okta @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.okta import (
    TOOLS,
    create_user,
    get_user,
    list_type_id_options,
    manifest,
    update_user,
)
from modulex_integrations.tools.okta.outputs import (
    CreateUserOutput,
    GetUserOutput,
    ListTypeIdOptionsOutput,
    UpdateUserOutput,
)

_SUBDOMAIN = "acme"
API = f"https://{_SUBDOMAIN}.okta.com/api/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "subdomain": _SUBDOMAIN,
        "api_token": "00fake-okta-ssws-token",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_four_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_user(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users?activate=true",
        json={
            # TODO: fill in a representative Okta create-user response shape.
            # Reference: https://developer.okta.com/docs/api/openapi/okta-management/management/tag/User/#tag/User/operation/createUser
            "id": "00u1abcdEFGHijklMNOP",
            "status": "PROVISIONED",
            "profile": {
                "firstName": "Ada",
                "lastName": "Lovelace",
                "email": "ada@example.com",
                "login": "ada@example.com",
            },
        },
    )

    result_dict = await create_user.ainvoke(
        _args(
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            login="ada@example.com",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.user is not None
    assert result.user.id == "00u1abcdEFGHijklMNOP"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "SSWS 00fake-okta-ssws-token"


@pytest.mark.asyncio
async def test_get_user(httpx_mock):  # type: ignore[no-untyped-def]
    user_id = "00u1abcdEFGHijklMNOP"
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/{user_id}",
        json={
            # TODO: fill in a representative Okta get-user response shape.
            "id": user_id,
            "status": "ACTIVE",
            "profile": {
                "firstName": "Ada",
                "lastName": "Lovelace",
                "email": "ada@example.com",
                "login": "ada@example.com",
            },
        },
    )

    result_dict = await get_user.ainvoke(_args(user_id=user_id))

    assert isinstance(result_dict, dict)
    result = GetUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.user is not None
    assert result.user.status == "ACTIVE"


@pytest.mark.asyncio
async def test_list_type_id_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/meta/types/user",
        json=[
            # TODO: replace with a representative /meta/types/user response.
            {"id": "otyfnjfba4ye7pgjB0g4", "displayName": "User"},
            {"id": "otyabcdEFGHijklMNOP", "displayName": "Contractor"},
        ],
    )

    result_dict = await list_type_id_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListTypeIdOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.options) == 2
    assert result.options[0].label == "User"
    assert result.options[0].value == "otyfnjfba4ye7pgjB0g4"


@pytest.mark.asyncio
async def test_update_user(httpx_mock):  # type: ignore[no-untyped-def]
    user_id = "00u1abcdEFGHijklMNOP"
    # update_user first fetches the existing profile, then PUTs the merge.
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/{user_id}",
        json={
            # TODO: representative existing-user payload.
            "id": user_id,
            "profile": {
                "firstName": "Ada",
                "lastName": "Lovelace",
                "email": "ada@example.com",
                "login": "ada@example.com",
            },
        },
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/users/{user_id}",
        json={
            # TODO: representative updated-user response.
            "id": user_id,
            "status": "ACTIVE",
            "profile": {
                "firstName": "Ada",
                "lastName": "Byron",
                "email": "ada@example.com",
                "login": "ada@example.com",
            },
        },
    )

    result_dict = await update_user.ainvoke(
        _args(user_id=user_id, last_name="Byron")
    )

    assert isinstance(result_dict, dict)
    result = UpdateUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.user is not None
    assert (result.user.profile or {}).get("lastName") == "Byron"


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    user_id = "00uNOSUCH"
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/{user_id}",
        status_code=404,
        text="Not Found",
    )

    result_dict = await get_user.ainvoke(_args(user_id=user_id))
    result = GetUserOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "404" in result.error


@pytest.mark.asyncio
async def test_get_user_validates_missing_credentials() -> None:
    """Empty subdomain or api_token short-circuits before the HTTP call."""
    result_dict = await get_user.ainvoke(
        {
            "auth_type": "custom",
            "auth_data": {"subdomain": "", "api_token": ""},
            "user_id": "x",
        }
    )
    result = GetUserOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Missing Okta credentials" in result.error

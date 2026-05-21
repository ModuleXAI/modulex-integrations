"""Happy-path tests for every google_directory @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_directory import (
    TOOLS,
    add_member_to_group,
    create_group,
    create_user,
    get_group,
    get_user,
    list_groups,
    list_users,
    manifest,
)
from modulex_integrations.tools.google_directory.outputs import (
    AddMemberToGroupOutput,
    CreateGroupOutput,
    CreateUserOutput,
    GetGroupOutput,
    GetUserOutput,
    ListGroupsOutput,
    ListUsersOutput,
)

API = "https://admin.googleapis.com/admin/directory/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_7_actions(self) -> None:
        assert len(manifest.actions) == 7

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_add_member_to_group(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/groups/group123@example.com/members",
        json={
            # TODO: fill in a representative response from Google Admin SDK docs
            "id": "member123",
            "email": "user@example.com",
            "role": "MEMBER",
            "type": "USER",
            "status": "ACTIVE",
            "kind": "admin#directory#member",
            "etag": "\"abc123\"",
        },
    )

    result_dict = await add_member_to_group.ainvoke(
        _args(group_id="group123@example.com", email="user@example.com", role="MEMBER")
    )

    assert isinstance(result_dict, dict)
    result = AddMemberToGroupOutput.model_validate(result_dict)
    assert result.success is True
    assert result.member is not None
    assert result.member.email == "user@example.com"


@pytest.mark.asyncio
async def test_create_group(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/groups",
        json={
            # TODO: fill in a representative response from Google Admin SDK docs
            "id": "group456",
            "email": "newgroup@example.com",
            "name": "New Group",
            "description": "A test group",
            "directMembersCount": "0",
            "kind": "admin#directory#group",
            "etag": "\"def456\"",
            "adminCreated": True,
        },
    )

    result_dict = await create_group.ainvoke(
        _args(email="newgroup@example.com", name="New Group", description="A test group")
    )

    assert isinstance(result_dict, dict)
    result = CreateGroupOutput.model_validate(result_dict)
    assert result.success is True
    assert result.group is not None
    assert result.group.email == "newgroup@example.com"


@pytest.mark.asyncio
async def test_create_user(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users",
        json={
            # TODO: fill in a representative response from Google Admin SDK docs
            "id": "user789",
            "primaryEmail": "john@example.com",
            "name": {"givenName": "John", "familyName": "Doe"},
            "isAdmin": False,
            "isDelegatedAdmin": False,
            "kind": "admin#directory#user",
            "etag": "\"ghi789\"",
            "creationTime": "2024-01-01T00:00:00.000Z",
            "orgUnitPath": "/",
        },
    )

    result_dict = await create_user.ainvoke(
        _args(
            email="john@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Doe",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.user is not None
    assert result.user.primary_email == "john@example.com"


@pytest.mark.asyncio
async def test_get_group(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/groups/group123@example.com",
        json={
            # TODO: fill in a representative response from Google Admin SDK docs
            "id": "group123",
            "email": "group123@example.com",
            "name": "Test Group",
            "description": "A test group",
            "directMembersCount": "5",
            "kind": "admin#directory#group",
            "etag": "\"jkl012\"",
            "adminCreated": True,
        },
    )

    result_dict = await get_group.ainvoke(_args(group_id="group123@example.com"))

    assert isinstance(result_dict, dict)
    result = GetGroupOutput.model_validate(result_dict)
    assert result.success is True
    assert result.group is not None
    assert result.group.email == "group123@example.com"


@pytest.mark.asyncio
async def test_get_user(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/user@example.com",
        json={
            # TODO: fill in a representative response from Google Admin SDK docs
            "id": "user001",
            "primaryEmail": "user@example.com",
            "name": {"givenName": "Jane", "familyName": "Smith"},
            "isAdmin": True,
            "isDelegatedAdmin": False,
            "kind": "admin#directory#user",
            "etag": "\"mno345\"",
            "creationTime": "2023-06-15T10:00:00.000Z",
            "orgUnitPath": "/Engineering",
        },
    )

    result_dict = await get_user.ainvoke(_args(user_id="user@example.com"))

    assert isinstance(result_dict, dict)
    result = GetUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.user is not None
    assert result.user.primary_email == "user@example.com"


@pytest.mark.asyncio
async def test_list_groups(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/groups?customer=my_customer",
        json={
            # TODO: fill in a representative response from Google Admin SDK docs
            "kind": "admin#directory#groups",
            "groups": [
                {
                    "id": "g1",
                    "email": "group1@example.com",
                    "name": "Group 1",
                    "directMembersCount": "3",
                    "kind": "admin#directory#group",
                    "adminCreated": True,
                },
            ],
        },
    )

    result_dict = await list_groups.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListGroupsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.groups) == 1
    assert result.groups[0].email == "group1@example.com"


@pytest.mark.asyncio
async def test_list_users(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users?customer=my_customer",
        json={
            # TODO: fill in a representative response from Google Admin SDK docs
            "kind": "admin#directory#users",
            "users": [
                {
                    "id": "u1",
                    "primaryEmail": "admin@example.com",
                    "name": {"givenName": "Admin", "familyName": "User"},
                    "isAdmin": True,
                    "isDelegatedAdmin": False,
                    "kind": "admin#directory#user",
                    "creationTime": "2022-01-01T00:00:00.000Z",
                    "orgUnitPath": "/",
                },
            ],
        },
    )

    result_dict = await list_users.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListUsersOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.users) == 1
    assert result.users[0].primary_email == "admin@example.com"

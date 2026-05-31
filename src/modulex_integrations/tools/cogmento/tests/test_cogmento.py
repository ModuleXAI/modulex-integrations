"""Happy-path tests for every cogmento @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.cogmento import (
    TOOLS,
    create_contact,
    create_deal,
    create_task,
    list_user_ids_options,
    manifest,
)
from modulex_integrations.tools.cogmento.outputs import (
    CreateContactOutput,
    CreateDealOutput,
    CreateTaskOutput,
    ListUserIdsOptionsOutput,
)

API = "https://api.cogmento.com/api/1"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_4_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts/",
        json={
            # TODO: fill in a representative response shape from Cogmento API docs
            "id": "abc123",
            "first_name": "John",
            "last_name": "Doe",
        },
    )

    result_dict = await create_contact.ainvoke(
        _args(first_name="John", last_name="Doe")
    )

    assert isinstance(result_dict, dict)
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.contact is not None


@pytest.mark.asyncio
async def test_create_deal(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/deals/",
        json={
            # TODO: fill in a representative response shape from Cogmento API docs
            "id": "deal456",
            "title": "New Deal",
        },
    )

    result_dict = await create_deal.ainvoke(_args(title="New Deal"))

    assert isinstance(result_dict, dict)
    result = CreateDealOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deal is not None


@pytest.mark.asyncio
async def test_create_task(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/tasks/",
        json={
            # TODO: fill in a representative response shape from Cogmento API docs
            "id": "task789",
            "title": "Follow up",
        },
    )

    result_dict = await create_task.ainvoke(_args(title="Follow up"))

    assert isinstance(result_dict, dict)
    result = CreateTaskOutput.model_validate(result_dict)
    assert result.success is True
    assert result.task is not None


@pytest.mark.asyncio
async def test_list_user_ids_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/auth/user",
        json=[
            # TODO: fill in a representative response shape from Cogmento API docs
            {"id": "u1", "name": "Alice", "email": "alice@example.com"},
            {"id": "u2", "name": "Bob", "email": "bob@example.com"},
        ],
    )

    result_dict = await list_user_ids_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListUserIdsOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.users) == 2


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_create_contact_empty_credential():  # type: ignore[no-untyped-def]
    """Empty access_token should return success=False without hitting the network."""
    result_dict = await create_contact.ainvoke(
        _args(auth_data={"access_token": ""}, first_name="Jane", last_name="Doe")
    )

    assert isinstance(result_dict, dict)
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None

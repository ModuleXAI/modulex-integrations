"""Happy-path tests for every insightly @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.insightly import (
    TOOLS,
    create_contact,
    create_task,
    manifest,
)
from modulex_integrations.tools.insightly.outputs import (
    CreateContactOutput,
    CreateTaskOutput,
)

API = "https://api.na1.insightly.com/v3.1"

_POD = "na1"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(pod=_POD, api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_2_actions(self) -> None:
        assert len(manifest.actions) == 2

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/Contacts",
        json={
            # TODO: fill in a representative response shape from the Insightly API docs
            "CONTACT_ID": 12345,
            "FIRST_NAME": "John",
            "LAST_NAME": "Doe",
            "TITLE": None,
        },
    )

    result_dict = await create_contact.ainvoke(
        _args(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.contact_id == 12345
    assert result.first_name == "John"


@pytest.mark.asyncio
async def test_create_task(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/Tasks",
        json={
            # TODO: fill in a representative response shape from the Insightly API docs
            "TASK_ID": 67890,
            "TITLE": "Follow up",
            "STATUS": "Not Started",
            "DUE_DATE": "2024-01-15",
            "CATEGORY_ID": None,
        },
    )

    result_dict = await create_task.ainvoke(
        _args(
            title="Follow up",
            status="Not Started",
            due_date="2024-01-15",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateTaskOutput.model_validate(result_dict)
    assert result.success is True
    assert result.task_id == 67890
    assert result.title == "Follow up"


@pytest.mark.asyncio
async def test_create_contact_validates_empty_api_key() -> None:
    result_dict = await create_contact.ainvoke(
        {"first_name": "X", "last_name": "Y", "email": "x@y.com", "pod": "na1", "api_key": ""}
    )
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")


@pytest.mark.asyncio
async def test_create_task_validates_empty_api_key() -> None:
    result_dict = await create_task.ainvoke(
        {"title": "X", "status": "Not Started", "due_date": "2024-01-01", "pod": "na1", "api_key": ""}
    )
    result = CreateTaskOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")

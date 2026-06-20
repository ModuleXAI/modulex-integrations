"""Happy-path tests per action + failure-path + empty-credential tests.

Loops does not raise on non-2xx — the tools wrap everything in
try/except and return ``success=False`` + ``error``. Mutating
endpoints also carry their own ``success`` flag in the JSON body.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.loops import (
    TOOLS,
    create_contact,
    create_contact_property,
    delete_contact,
    find_contact,
    list_contact_properties,
    list_mailing_lists,
    list_transactional_emails,
    manifest,
    send_event,
    send_transactional_email,
    update_contact,
)
from modulex_integrations.tools.loops.outputs import (
    CreateContactOutput,
    CreateContactPropertyOutput,
    DeleteContactOutput,
    FindContactOutput,
    ListContactPropertiesOutput,
    ListMailingListsOutput,
    ListTransactionalEmailsOutput,
    SendEventOutput,
    SendTransactionalEmailOutput,
    UpdateContactOutput,
)

API = "https://app.loops.so/api/v1"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_10_actions(self) -> None:
        assert len(manifest.actions) == 10

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_logo(self) -> None:
        assert manifest.logo == "modulex:loops-themed"


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_create_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts/create",
        json={"success": True, "id": "contact-123"},
    )

    result_dict = await create_contact.ainvoke(
        _args(email="bob@example.com", first_name="Bob", custom_properties={"plan": "pro"})
    )

    assert isinstance(result_dict, dict)
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "contact-123"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


@pytest.mark.asyncio
async def test_update_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/contacts/update",
        json={"success": True, "id": "contact-456"},
    )

    result_dict = await update_contact.ainvoke(
        _args(email="bob@example.com", user_group="dormant")
    )

    assert isinstance(result_dict, dict)
    result = UpdateContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "contact-456"


@pytest.mark.asyncio
async def test_find_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/contacts/find?email=bob%40example.com",
        json=[
            {
                "id": "cll6b3i8901a9jx0oyktl2m4u",
                "email": "bob@example.com",
                "firstName": "Bob",
                "lastName": None,
                "source": "API",
                "subscribed": True,
                "userGroup": "",
                "userId": None,
                "mailingLists": {"cm06f5v0e45nf0ml5754o9cix": True},
                "optInStatus": "accepted",
            }
        ],
    )

    result_dict = await find_contact.ainvoke(_args(email="bob@example.com"))

    assert isinstance(result_dict, dict)
    result = FindContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.contacts[0].email == "bob@example.com"
    assert result.contacts[0].opt_in_status == "accepted"
    assert result.contacts[0].mailing_lists == {"cm06f5v0e45nf0ml5754o9cix": True}


@pytest.mark.asyncio
async def test_delete_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts/delete",
        json={"success": True, "message": "Contact deleted."},
    )

    result_dict = await delete_contact.ainvoke(_args(email="bob@example.com"))

    assert isinstance(result_dict, dict)
    result = DeleteContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message == "Contact deleted."


@pytest.mark.asyncio
async def test_send_transactional_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/transactional",
        json={"success": True},
    )

    result_dict = await send_transactional_email.ainvoke(
        _args(
            email="bob@example.com",
            transactional_id="clx123",
            data_variables={"name": "Bob"},
        )
    )

    assert isinstance(result_dict, dict)
    result = SendTransactionalEmailOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_send_event(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/events/send",
        json={"success": True},
    )

    result_dict = await send_event.ainvoke(
        _args(
            event_name="signup_completed",
            email="bob@example.com",
            event_properties={"plan": "pro"},
        )
    )

    assert isinstance(result_dict, dict)
    result = SendEventOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_mailing_lists(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/lists",
        json=[
            {
                "id": "clxf1nxlb000t0ml79ajwcsj0",
                "name": "Mailing List Beta",
                "description": None,
                "isPublic": True,
            }
        ],
    )

    result_dict = await list_mailing_lists.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListMailingListsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.mailing_lists[0].name == "Mailing List Beta"
    assert result.mailing_lists[0].is_public is True


@pytest.mark.asyncio
async def test_list_transactional_emails(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/transactional?perPage=20",
        json={
            "pagination": {
                "totalResults": 23,
                "returnedResults": 20,
                "perPage": 20,
                "totalPages": 2,
                "nextCursor": "cursor-2",
                "nextPage": "https://app.loops.so/api/v1/transactional?cursor=cursor-2",
            },
            "data": [
                {
                    "id": "tmpl-1",
                    "name": "Welcome",
                    "lastUpdated": "2024-01-15T00:00:00Z",
                    "dataVariables": ["firstName", "lastName"],
                }
            ],
        },
    )

    result_dict = await list_transactional_emails.ainvoke(_args(per_page="20"))

    assert isinstance(result_dict, dict)
    result = ListTransactionalEmailsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.transactional_emails[0].name == "Welcome"
    assert result.transactional_emails[0].data_variables == ["firstName", "lastName"]
    assert result.pagination is not None
    assert result.pagination.total_results == 23
    assert result.pagination.next_cursor == "cursor-2"


@pytest.mark.asyncio
async def test_create_contact_property(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts/properties",
        json={"success": True},
    )

    result_dict = await create_contact_property.ainvoke(
        _args(name="favoriteColor", type="string")
    )

    assert isinstance(result_dict, dict)
    result = CreateContactPropertyOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_contact_properties(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/contacts/properties",
        json=[
            {"key": "firstName", "label": "First Name", "type": "string"},
            {"key": "favoriteColor", "label": "Favorite Color", "type": "string"},
        ],
    )

    result_dict = await list_contact_properties.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListContactPropertiesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.properties[1].key == "favoriteColor"


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_create_contact_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts/create",
        status_code=401,
        text="Invalid API key",
    )

    result_dict = await create_contact.ainvoke(_args(email="bob@example.com"))

    assert isinstance(result_dict, dict)
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_create_contact_returns_error_on_body_success_false(httpx_mock):  # type: ignore[no-untyped-def]
    """Loops returns HTTP 200 with ``{"success": false, "message": ...}`` for
    business-logic failures (e.g. contact already exists)."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts/create",
        json={"success": False, "message": "Contact already exists."},
    )

    result_dict = await create_contact.ainvoke(_args(email="bob@example.com"))

    assert isinstance(result_dict, dict)
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "Contact already exists."


@pytest.mark.asyncio
async def test_update_contact_requires_identifier() -> None:
    """At least one of email/user_id is required — short-circuits before HTTP."""
    result_dict = await update_contact.ainvoke({"api_key": _API_KEY})

    assert isinstance(result_dict, dict)
    result = UpdateContactOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "email or user_id" in result.error


# --- Empty-credential paths ------------------------------------------------


@pytest.mark.asyncio
async def test_create_contact_validates_empty_api_key() -> None:
    result_dict = await create_contact.ainvoke({"email": "x@example.com", "api_key": ""})

    assert isinstance(result_dict, dict)
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_list_mailing_lists_validates_empty_api_key() -> None:
    result_dict = await list_mailing_lists.ainvoke({"api_key": "   "})

    assert isinstance(result_dict, dict)
    result = ListMailingListsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error

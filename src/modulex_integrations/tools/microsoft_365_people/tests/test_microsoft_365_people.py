"""Happy-path tests for every microsoft_365_people @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import httpx
import pytest

from modulex_integrations.tools.microsoft_365_people import (
    TOOLS,
    create_contact,
    create_contact_folder,
    manifest,
    update_contact,
)
from modulex_integrations.tools.microsoft_365_people.outputs import (
    CreateContactFolderOutput,
    CreateContactOutput,
    UpdateContactOutput,
)

API = "https://graph.microsoft.com/v1.0"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/me/contacts",
        json={
            # TODO: fill in a representative response shape from Microsoft Graph API docs
            "id": "AAMkAGI2THVSAAA=",
            "displayName": "Jane Doe",
            "givenName": "Jane",
            "surname": "Doe",
            "emailAddresses": [{"name": "jane@example.com", "address": "jane@example.com"}],
            "mobilePhone": "+1234567890",
            "homePhones": [],
            "homeAddress": {},
            "createdDateTime": "2024-01-01T00:00:00Z",
            "lastModifiedDateTime": "2024-01-01T00:00:00Z",
        },
    )

    result_dict = await create_contact.ainvoke(
        _args(email="jane@example.com", first_name="Jane", last_name="Doe")
    )

    assert isinstance(result_dict, dict)
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.contact is not None
    assert result.contact.given_name == "Jane"


@pytest.mark.asyncio
async def test_create_contact_folder(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/me/contactFolders",
        json={
            # TODO: fill in a representative response shape from Microsoft Graph API docs
            "id": "AAMkAGI2THFOLDER=",
            "displayName": "Work Contacts",
            "parentFolderId": "AAMkAGI2THPARENT=",
        },
    )

    result_dict = await create_contact_folder.ainvoke(
        _args(display_name="Work Contacts")
    )

    assert isinstance(result_dict, dict)
    result = CreateContactFolderOutput.model_validate(result_dict)
    assert result.success is True
    assert result.folder is not None
    assert result.folder.display_name == "Work Contacts"


@pytest.mark.asyncio
async def test_update_contact(httpx_mock):  # type: ignore[no-untyped-def]
    contact_id = "AAMkAGI2THVSAAA="
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/me/contacts/{contact_id}",
        json={
            # TODO: fill in a representative response shape from Microsoft Graph API docs
            "id": contact_id,
            "displayName": "Jane Smith",
            "givenName": "Jane",
            "surname": "Smith",
            "emailAddresses": [{"name": "jane@example.com", "address": "jane@example.com"}],
            "mobilePhone": "+1234567890",
            "homePhones": [],
            "homeAddress": {},
            "lastModifiedDateTime": "2024-01-02T00:00:00Z",
        },
    )

    result_dict = await update_contact.ainvoke(
        _args(contact_id=contact_id, last_name="Smith")
    )

    assert isinstance(result_dict, dict)
    result = UpdateContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.contact is not None
    assert result.contact.surname == "Smith"


@pytest.mark.asyncio
async def test_create_contact_http_error(httpx_mock):  # type: ignore[no-untyped-def]
    """Verify non-2xx responses raise httpx.HTTPStatusError (Pattern A)."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/me/contacts",
        status_code=401,
        json={"error": {"code": "InvalidAuthenticationToken", "message": "Access token is empty."}},
    )

    with pytest.raises(httpx.HTTPStatusError):
        await create_contact.ainvoke(
            _args(email="test@example.com", first_name="Test")
        )

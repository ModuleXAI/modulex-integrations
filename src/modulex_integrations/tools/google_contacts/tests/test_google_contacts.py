"""Happy-path tests for every google_contacts @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_contacts import (
    TOOLS,
    create_contact,
    delete_contact,
    get_contact,
    list_contacts,
    list_directory_contacts,
    manifest,
    update_contact,
)
from modulex_integrations.tools.google_contacts.outputs import (
    CreateContactOutput,
    DeleteContactOutput,
    GetContactOutput,
    ListContactsOutput,
    ListDirectoryContactsOutput,
    UpdateContactOutput,
)

API = "https://people.googleapis.com/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_6_actions(self) -> None:
        assert len(manifest.actions) == 6

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/people:createContact?personFields=names%2CemailAddresses",
        json={
            # TODO: replace with a representative Person response body — see
            # https://developers.google.com/people/api/rest/v1/people/createContact
            "resourceName": "people/c1234567890",
            "etag": "%EgUBAj0BNy4=",
            "names": [
                {
                    "displayName": "Ada Lovelace",
                    "givenName": "Ada",
                    "familyName": "Lovelace",
                }
            ],
            "emailAddresses": [{"value": "ada@example.com"}],
        },
    )

    result_dict = await create_contact.ainvoke(
        _args(
            person_fields=["names", "emailAddresses"],
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.contact is not None
    assert result.contact.resource_name == "people/c1234567890"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer fake_access_token"


@pytest.mark.asyncio
async def test_delete_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/people/c1234567890:deleteContact",
        status_code=200,
        json={},
    )

    result_dict = await delete_contact.ainvoke(_args(resource_name="people/c1234567890"))

    assert isinstance(result_dict, dict)
    result = DeleteContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.resource_name == "people/c1234567890"


@pytest.mark.asyncio
async def test_get_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/people/c1234567890?personFields=names%2CemailAddresses",
        json={
            # TODO: replace with a representative Person response shape.
            "resourceName": "people/c1234567890",
            "etag": "%EgUBAj0BNy4=",
            "names": [{"displayName": "Ada Lovelace", "givenName": "Ada"}],
            "emailAddresses": [{"value": "ada@example.com"}],
        },
    )

    result_dict = await get_contact.ainvoke(
        _args(
            resource_name="people/c1234567890",
            fields=["names", "emailAddresses"],
        )
    )

    assert isinstance(result_dict, dict)
    result = GetContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.contact is not None
    assert result.contact.email_addresses == ["ada@example.com"]


@pytest.mark.asyncio
async def test_list_contacts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/people/me/connections?personFields=names",
        json={
            # TODO: replace with a representative connections.list page.
            "connections": [
                {
                    "resourceName": "people/c1",
                    "etag": "x",
                    "names": [{"displayName": "Alpha"}],
                },
                {
                    "resourceName": "people/c2",
                    "etag": "y",
                    "names": [{"displayName": "Beta"}],
                },
            ]
        },
    )

    result_dict = await list_contacts.ainvoke(_args(fields=["names"]))

    assert isinstance(result_dict, dict)
    result = ListContactsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 2
    assert [c.display_name for c in result.contacts] == ["Alpha", "Beta"]


@pytest.mark.asyncio
async def test_list_directory_contacts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}/people:listDirectoryPeople"
            "?readMask=names%2CemailAddresses"
            "&sources=DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE"
            "&pageSize=10"
        ),
        json={
            # TODO: replace with a representative listDirectoryPeople response.
            "people": [
                {
                    "resourceName": "people/c1",
                    "etag": "x",
                    "names": [{"displayName": "Director One"}],
                    "emailAddresses": [{"value": "one@corp.com"}],
                }
            ],
            "nextPageToken": "tok-next",
        },
    )

    result_dict = await list_directory_contacts.ainvoke(
        _args(
            fields=["names", "emailAddresses"],
            source="DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE",
            page_size=10,
        )
    )

    assert isinstance(result_dict, dict)
    result = ListDirectoryContactsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 1
    assert result.next_page_token == "tok-next"
    assert result.people[0].display_name == "Director One"


@pytest.mark.asyncio
async def test_update_contact(httpx_mock):  # type: ignore[no-untyped-def]
    # 1) Fetch latest etag (names only).
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/people/c1234567890?personFields=names",
        json={
            "resourceName": "people/c1234567890",
            "etag": "%EgUBAj0BNy4=",
            "names": [{"displayName": "Ada Lovelace"}],
        },
    )
    # 2) PATCH the updateContact call.
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/people/c1234567890:updateContact?updatePersonFields=names",
        json={
            # TODO: replace with a representative updateContact response.
            "resourceName": "people/c1234567890",
            "etag": "%EgUBAj0BNy5=",
            "names": [
                {
                    "displayName": "Augusta Ada Lovelace",
                    "givenName": "Augusta",
                    "familyName": "Lovelace",
                }
            ],
        },
    )

    result_dict = await update_contact.ainvoke(
        _args(
            resource_name="people/c1234567890",
            update_person_fields=["names"],
            first_name="Augusta",
            last_name="Lovelace",
        )
    )

    assert isinstance(result_dict, dict)
    result = UpdateContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.contact is not None
    assert result.contact.given_name == "Augusta"

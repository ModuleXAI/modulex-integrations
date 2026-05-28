"""Happy-path tests for every postgrid @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.postgrid import (
    TOOLS,
    create_contact,
    create_letter,
    create_postcard,
    manifest,
)
from modulex_integrations.tools.postgrid.outputs import (
    CreateContactOutput,
    CreateLetterOutput,
    CreatePostcardOutput,
)

API = "https://api.postgrid.com/print-mail/v1"

_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "contact_abc123",
            "object": "contact",
            "live": True,
            "firstName": "John",
            "lastName": "Doe",
            "companyName": None,
            "addressLine1": "123 Main St",
            "addressLine2": None,
            "city": "Toronto",
            "provinceOrState": "ON",
            "postalOrZip": "M5V 1A1",
            "country": "Canada",
            "countryCode": "CA",
            "email": "john@example.com",
            "phoneNumber": None,
            "jobTitle": None,
            "description": None,
            "addressStatus": "verified",
        },
    )

    result_dict = await create_contact.ainvoke(
        _args(first_name="John", address_line1="123 Main St", last_name="Doe", city="Toronto")
    )

    assert isinstance(result_dict, dict)
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.contact is not None
    assert result.contact.id == "contact_abc123"
    assert result.contact.first_name == "John"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-api-key"] == _API_KEY


@pytest.mark.asyncio
async def test_create_letter(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/letters",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "letter_abc123",
            "object": "letter",
            "live": True,
            "sendDate": "2023-02-16T15:40:35.873Z",
            "status": "ready",
            "url": "https://pg-prod-bucket.s3.amazonaws.com/letters/letter_abc123.pdf",
        },
    )

    result_dict = await create_letter.ainvoke(
        _args(to="contact_receiver", from_contact="contact_sender", html="<p>Hello</p>")
    )

    assert isinstance(result_dict, dict)
    result = CreateLetterOutput.model_validate(result_dict)
    assert result.success is True
    assert result.letter is not None
    assert result.letter.id == "letter_abc123"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-api-key"] == _API_KEY


@pytest.mark.asyncio
async def test_create_postcard(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/postcards",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "postcard_abc123",
            "object": "postcard",
            "live": True,
            "sendDate": "2023-02-16T15:40:35.873Z",
            "status": "ready",
            "size": "6x4",
            "url": "https://pg-prod-bucket.s3.amazonaws.com/postcards/postcard_abc123.pdf",
        },
    )

    result_dict = await create_postcard.ainvoke(
        _args(
            to="contact_receiver",
            from_contact="contact_sender",
            front_html="<p>Front</p>",
            back_html="<p>Back</p>",
            size="6x4",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreatePostcardOutput.model_validate(result_dict)
    assert result.success is True
    assert result.postcard is not None
    assert result.postcard.id == "postcard_abc123"
    assert result.postcard.size == "6x4"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-api-key"] == _API_KEY


@pytest.mark.asyncio
async def test_create_contact_validates_empty_api_key() -> None:
    result_dict = await create_contact.ainvoke(
        {"first_name": "Test", "address_line1": "123 St", "api_key": ""}
    )
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error

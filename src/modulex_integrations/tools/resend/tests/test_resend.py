"""Happy-path tests per action + failure-path and empty-credential tests
(Resend tools never raise on errors — they return success=False)."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.resend import (
    TOOLS,
    create_contact,
    delete_contact,
    get_contact,
    get_email,
    list_contacts,
    list_domains,
    manifest,
    send,
    update_contact,
)
from modulex_integrations.tools.resend.outputs import (
    CreateContactOutput,
    DeleteContactOutput,
    GetContactOutput,
    GetEmailOutput,
    ListContactsOutput,
    ListDomainsOutput,
    SendOutput,
    UpdateContactOutput,
)

API = "https://api.resend.com"
_API_KEY = "re_fake_api_key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_8_actions(self) -> None:
        assert len(manifest.actions) == 8

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_does_not_ship_modulex_key(self) -> None:
        assert "modulex_key" not in {a.auth_type for a in manifest.auth_schemas}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_send(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/emails",
        json={"id": "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794"},
    )

    result_dict = await send.ainvoke(
        _args(
            from_address="sender@example.com",
            to="recipient@example.com",
            subject="Hello",
            body="<p>Hi</p>",
            content_type="html",
            tags="category:welcome,type:onboarding",
        )
    )

    assert isinstance(result_dict, dict)
    result = SendOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794"
    assert result.to == "recipient@example.com"
    assert result.subject == "Hello"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"
    import json

    body = json.loads(sent.content)
    assert body["html"] == "<p>Hi</p>"
    assert body["tags"] == [
        {"name": "category", "value": "welcome"},
        {"name": "type", "value": "onboarding"},
    ]


@pytest.mark.asyncio
async def test_send_plain_text(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/emails", json={"id": "abc123"})

    result_dict = await send.ainvoke(
        _args(
            from_address="sender@example.com",
            to="recipient@example.com",
            subject="Plain",
            body="Hello there",
        )
    )

    result = SendOutput.model_validate(result_dict)
    assert result.success is True
    import json

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["text"] == "Hello there"
    assert "html" not in body


@pytest.mark.asyncio
async def test_get_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/emails/email-1",
        json={
            "object": "email",
            "id": "email-1",
            "from": "sender@example.com",
            "to": ["recipient@example.com"],
            "subject": "Subject",
            "html": "<p>Body</p>",
            "text": None,
            "cc": [],
            "bcc": [],
            "reply_to": ["reply@example.com"],
            "last_event": "delivered",
            "created_at": "2024-08-05T11:52:01.858Z",
            "scheduled_at": None,
            "tags": [{"name": "category", "value": "welcome"}],
        },
    )

    result_dict = await get_email.ainvoke(_args(email_id="email-1"))

    assert isinstance(result_dict, dict)
    result = GetEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "email-1"
    assert result.sender == "sender@example.com"
    assert result.to == ["recipient@example.com"]
    assert result.last_event == "delivered"
    assert result.tags[0].name == "category"
    assert result.tags[0].value == "welcome"


@pytest.mark.asyncio
async def test_create_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts",
        json={"object": "contact", "id": "contact-1"},
    )

    result_dict = await create_contact.ainvoke(
        _args(email="john@example.com", first_name="John", last_name="Doe", unsubscribed=False)
    )

    assert isinstance(result_dict, dict)
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "contact-1"

    import json

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["email"] == "john@example.com"
    assert body["first_name"] == "John"
    assert body["unsubscribed"] is False


@pytest.mark.asyncio
async def test_list_contacts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/contacts",
        json={
            "object": "list",
            "has_more": False,
            "data": [
                {
                    "id": "contact-1",
                    "email": "john@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "created_at": "2024-08-05T11:52:01.858Z",
                    "unsubscribed": False,
                }
            ],
        },
    )

    result_dict = await list_contacts.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListContactsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.contacts[0].email == "john@example.com"
    assert result.has_more is False


@pytest.mark.asyncio
async def test_get_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/contacts/contact-1",
        json={
            "object": "contact",
            "id": "contact-1",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "created_at": "2024-08-05T11:52:01.858Z",
            "unsubscribed": True,
        },
    )

    result_dict = await get_contact.ainvoke(_args(contact_id="contact-1"))

    assert isinstance(result_dict, dict)
    result = GetContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "contact-1"
    assert result.unsubscribed is True


@pytest.mark.asyncio
async def test_update_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/contacts/contact-1",
        json={"object": "contact", "id": "contact-1"},
    )

    result_dict = await update_contact.ainvoke(
        _args(contact_id="contact-1", first_name="Jane", unsubscribed=True)
    )

    assert isinstance(result_dict, dict)
    result = UpdateContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "contact-1"

    import json

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["first_name"] == "Jane"
    assert body["unsubscribed"] is True


@pytest.mark.asyncio
async def test_delete_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/contacts/contact-1",
        json={"object": "contact", "contact": "contact-1", "deleted": True},
    )

    result_dict = await delete_contact.ainvoke(_args(contact_id="contact-1"))

    assert isinstance(result_dict, dict)
    result = DeleteContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "contact-1"
    assert result.deleted is True


@pytest.mark.asyncio
async def test_list_domains(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/domains",
        json={
            "object": "list",
            "has_more": False,
            "data": [
                {
                    "id": "domain-1",
                    "name": "example.com",
                    "status": "verified",
                    "region": "us-east-1",
                    "created_at": "2024-08-05T11:52:01.858Z",
                }
            ],
        },
    )

    result_dict = await list_domains.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListDomainsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.domains[0].name == "example.com"
    assert result.domains[0].status == "verified"


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_send_http_error(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/emails",
        status_code=422,
        json={"message": "Invalid from address"},
    )

    result_dict = await send.ainvoke(
        _args(
            from_address="bad",
            to="recipient@example.com",
            subject="x",
            body="y",
        )
    )

    result = SendOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "422" in result.error


@pytest.mark.asyncio
async def test_get_email_not_found(httpx_mock):  # type: ignore[no-untyped-def]
    # 200 with no id is treated as a logical failure by Resend's body shape.
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/emails/missing",
        json={"message": "Email not found"},
    )

    result_dict = await get_email.ainvoke(_args(email_id="missing"))

    result = GetEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "Email not found"


# --- Empty-credential tests ------------------------------------------------


@pytest.mark.asyncio
async def test_send_empty_api_key() -> None:
    result_dict = await send.ainvoke(
        {
            "from_address": "sender@example.com",
            "to": "recipient@example.com",
            "subject": "x",
            "body": "y",
            "api_key": "",
        }
    )
    result = SendOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_list_domains_empty_api_key() -> None:
    result_dict = await list_domains.ainvoke({"api_key": "   "})
    result = ListDomainsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "empty" in result.error.lower()

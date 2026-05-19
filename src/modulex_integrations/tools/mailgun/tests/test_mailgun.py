"""Happy-path tests for every mailgun @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.mailgun import (
    TOOLS,
    create_mailinglist_member,
    create_route,
    delete_mailinglist_member,
    list_domains,
    list_mailinglist_members,
    manifest,
    retrieve_mailinglist_member,
    send_email,
    suppress_email,
    verify_email,
)
from modulex_integrations.tools.mailgun.outputs import (
    CreateMailinglistMemberOutput,
    CreateRouteOutput,
    DeleteMailinglistMemberOutput,
    ListDomainsOutput,
    ListMailinglistMembersOutput,
    RetrieveMailinglistMemberOutput,
    SendEmailOutput,
    SuppressEmailOutput,
    VerifyEmailOutput,
)

API = "https://api.mailgun.net"

_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, region="US", **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_9_actions(self) -> None:
        assert len(manifest.actions) == 9

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_send_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v3/test.example.com/messages",
        json={
            # TODO: fill in a representative response from the Mailgun API
            "id": "<20230101000000.1234567890@test.example.com>",
            "message": "Queued. Thank you.",
        },
    )

    result_dict = await send_email.ainvoke(
        _args(
            domain="test.example.com",
            from_name="Test",
            from_email="test@test.example.com",
            to=["recipient@example.com"],
            subject="Hello",
            text="World",
        )
    )

    assert isinstance(result_dict, dict)
    result = SendEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id is not None


@pytest.mark.asyncio
async def test_verify_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v4/address/validate?address=test%40example.com",
        json={
            # TODO: fill in a representative response from the Mailgun validation API
            "address": "test@example.com",
            "is_disposable_address": False,
            "is_role_address": False,
            "reason": [],
            "result": "deliverable",
            "risk": "low",
        },
    )

    result_dict = await verify_email.ainvoke(_args(email="test@example.com"))

    assert isinstance(result_dict, dict)
    result = VerifyEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.verification is not None
    assert result.verification.risk == "low"


@pytest.mark.asyncio
async def test_create_mailinglist_member(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v3/lists/list@example.com/members",
        json={
            # TODO: fill in a representative response from the Mailgun API
            "member": {
                "address": "new@example.com",
                "name": "New Member",
                "subscribed": True,
                "vars": {},
            },
            "message": "Mailing list member has been created",
        },
    )

    result_dict = await create_mailinglist_member.ainvoke(
        _args(list_address="list@example.com", address="new@example.com", name="New Member")
    )

    assert isinstance(result_dict, dict)
    result = CreateMailinglistMemberOutput.model_validate(result_dict)
    assert result.success is True
    assert result.member is not None
    assert result.member.address == "new@example.com"


@pytest.mark.asyncio
async def test_create_route(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v3/routes",
        json={
            # TODO: fill in a representative response from the Mailgun API
            "message": "Route has been created",
            "route": {
                "id": "route123",
            },
        },
    )

    result_dict = await create_route.ainvoke(
        _args(
            priority=0,
            description="Test route",
            expression="match_recipient('.*@example.com')",
            action=["forward('dest@example.com')", "stop()"],
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateRouteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.route_id == "route123"


@pytest.mark.asyncio
async def test_delete_mailinglist_member(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/v3/lists/list@example.com/members/old@example.com",
        json={
            # TODO: fill in a representative response from the Mailgun API
            "member": {"address": "old@example.com"},
            "message": "Mailing list member has been deleted",
        },
    )

    result_dict = await delete_mailinglist_member.ainvoke(
        _args(list_address="list@example.com", address="old@example.com")
    )

    assert isinstance(result_dict, dict)
    result = DeleteMailinglistMemberOutput.model_validate(result_dict)
    assert result.success is True
    assert result.member_address == "old@example.com"


@pytest.mark.asyncio
async def test_list_domains(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v3/domains?state=active",
        json={
            # TODO: fill in a representative response from the Mailgun API
            "items": [
                {
                    "name": "example.com",
                    "state": "active",
                    "type": "sandbox",
                    "created_at": "2023-01-01T00:00:00Z",
                    "smtp_login": "postmaster@example.com",
                    "web_prefix": "email",
                },
            ],
            "total_count": 1,
        },
    )

    result_dict = await list_domains.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListDomainsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.domains) == 1
    assert result.domains[0].name == "example.com"


@pytest.mark.asyncio
async def test_list_mailinglist_members(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v3/lists/list@example.com/members/pages",
        json={
            # TODO: fill in a representative response from the Mailgun API
            "items": [
                {
                    "address": "member1@example.com",
                    "name": "Member One",
                    "subscribed": True,
                    "vars": {},
                },
            ],
        },
    )

    result_dict = await list_mailinglist_members.ainvoke(
        _args(list_address="list@example.com")
    )

    assert isinstance(result_dict, dict)
    result = ListMailinglistMembersOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.members) == 1
    assert result.members[0].address == "member1@example.com"


@pytest.mark.asyncio
async def test_retrieve_mailinglist_member(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v3/lists/list@example.com/members/member@example.com",
        json={
            # TODO: fill in a representative response from the Mailgun API
            "member": {
                "address": "member@example.com",
                "name": "Test Member",
                "subscribed": True,
                "vars": {"age": 30},
            },
        },
    )

    result_dict = await retrieve_mailinglist_member.ainvoke(
        _args(list_address="list@example.com", address="member@example.com")
    )

    assert isinstance(result_dict, dict)
    result = RetrieveMailinglistMemberOutput.model_validate(result_dict)
    assert result.success is True
    assert result.member is not None
    assert result.member.address == "member@example.com"


@pytest.mark.asyncio
async def test_suppress_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v3/example.com/bounces",
        json={
            # TODO: fill in a representative response from the Mailgun API
            "message": "Address has been added to the bounces table",
            "address": "bad@example.com",
        },
    )

    result_dict = await suppress_email.ainvoke(
        _args(
            domain="example.com",
            email="bad@example.com",
            category="bounces",
        )
    )

    assert isinstance(result_dict, dict)
    result = SuppressEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message is not None


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_send_email_empty_credential() -> None:
    """Empty API key returns success=False without hitting the network."""
    result_dict = await send_email.ainvoke(
        {
            "api_key": "",
            "region": "US",
            "domain": "test.example.com",
            "from_name": "Test",
            "from_email": "test@test.example.com",
            "to": ["recipient@example.com"],
            "subject": "Hello",
            "text": "World",
        }
    )
    assert isinstance(result_dict, dict)
    result = SendEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "empty" in result.error.lower() or "credential" in result.error.lower()

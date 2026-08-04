"""Happy-path tests for every Zoho Desk @tool, plus manifest + failure paths."""
from __future__ import annotations

import json
from typing import Any
from urllib.parse import parse_qs

import pytest

from modulex_integrations.tools.zoho_desk import (
    TOOLS,
    add_comment,
    get_contact,
    get_thread,
    get_ticket,
    list_comments,
    list_organizations,
    list_threads,
    list_tickets,
    manifest,
    update_ticket,
)
from modulex_integrations.tools.zoho_desk.outputs import (
    AddCommentOutput,
    GetContactOutput,
    GetThreadOutput,
    GetTicketOutput,
    ListCommentsOutput,
    ListOrganizationsOutput,
    ListThreadsOutput,
    ListTicketsOutput,
    UpdateTicketOutput,
)
from modulex_integrations.tools.zoho_desk.tools import (
    _ACCOUNTS_URLS,
    _DATA_CENTER_TLDS,
    _DESK_HOSTS,
)

API = "https://desk.zoho.com/api/v1"
ACCOUNTS = "https://accounts.zoho.com"
TOKEN_URL = f"{ACCOUNTS}/oauth/v2/token"
ORG_ID = "123456789"
ACCESS_TOKEN = "1000.minted_access_token"

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "client_id": "1000.FAKECLIENTID",
        "client_secret": "fake_client_secret",
        "org_id": ORG_ID,
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


def _mock_token(
    httpx_mock: Any,
    api_domain: str = "https://www.zohoapis.com",
    url: str = TOKEN_URL,
) -> None:
    """Register the client-credentials token mint every action performs."""
    httpx_mock.add_response(
        method="POST",
        url=url,
        json={
            "access_token": ACCESS_TOKEN,
            "api_domain": api_domain,
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )


def _form(request: Any) -> dict[str, list[str]]:
    return parse_qs(request.content.decode())


_TICKET: dict[str, Any] = {
    "id": "1892000000042001",
    "ticketNumber": "101",
    "subject": "Cannot log in",
    "description": "<div>Login fails with a 500</div>",
    "status": "Open",
    "statusType": "Open",
    "priority": "High",
    "category": "Access",
    "subCategory": "Login",
    "classification": "Problem",
    "channel": "Email",
    "departmentId": "1892000000006907",
    "contactId": "1892000000042003",
    "accountId": None,
    "assigneeId": "1892000000056007",
    "email": "customer@example.com",
    "phone": None,
    "dueDate": "2026-08-10T09:00:00.000Z",
    "responseDueDate": None,
    "createdTime": "2026-08-01T09:00:00.000Z",
    "modifiedTime": "2026-08-02T09:00:00.000Z",
    "closedTime": None,
    "resolution": None,
    "threadCount": "2",
    "commentCount": "1",
    "webUrl": "https://desk.zoho.com/agent/acme/support/tickets/details/1892000000042001",
    "isEscalated": False,
    "isOverDue": False,
    "isSpam": False,
    "cf": {"cf_severity": "Sev2"},
}

_COMMENT: dict[str, Any] = {
    "id": "1892000000078001",
    "content": "<p>Checked the auth logs</p>",
    "contentType": "html",
    "isPublic": False,
    "commenterId": "1892000000056007",
    "commenter": {
        "name": "Dana Agent",
        "firstName": "Dana",
        "lastName": "Agent",
        "email": "dana@example.com",
        "type": "AGENT",
        "roleName": "Support",
        "photoURL": None,
    },
    "commentedTime": "2026-08-02T10:00:00.000Z",
    "modifiedTime": None,
    "attachments": [
        {
            "id": "1892000000079001",
            "name": "trace.log",
            "size": "12",
            "href": "/api/v1/tickets/1892000000042001/attachments/1892000000079001/content",
        }
    ],
}

_THREAD: dict[str, Any] = {
    "id": "1892000000088001",
    "channel": "EMAIL",
    "direction": "in",
    "content": "<div>Still broken &amp; urgent</div>",
    "contentType": "text/html",
    "summary": "Still broken",
    "responderId": None,
    "createdTime": "2026-08-02T11:00:00.000Z",
    "hasAttach": False,
    "attachmentCount": "0",
    "fromEmailAddress": "customer@example.com",
    "to": "support@example.com",
    "cc": None,
    "bcc": None,
    "replyTo": None,
    "isForward": False,
    "isContentTruncated": False,
    "fullContentURL": None,
    "plainText": None,
    "status": "SUCCESS",
    "isDescriptionThread": False,
    "visibility": "public",
    "canReply": True,
    "author": {
        "name": "Casey Customer",
        "firstName": "Casey",
        "lastName": "Customer",
        "email": "customer@example.com",
        "type": "END_USER",
        "photoURL": None,
    },
    "attachments": [],
}

_CONTACT: dict[str, Any] = {
    "id": "1892000000042003",
    "firstName": "Casey",
    "lastName": "Customer",
    "email": "customer@example.com",
    "secondaryEmail": None,
    "phone": "+15550100",
    "mobile": None,
    "accountId": "1892000000042009",
    "ownerId": None,
    "type": "Contact",
    "title": "Ops Lead",
    "street": "1 Main St",
    "city": "Austin",
    "state": "TX",
    "country": "US",
    "zip": "73301",
    "description": None,
    "cf": {},
}


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_9_actions(self) -> None:
        assert len(manifest.actions) == 9

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}

    def test_manifest_declares_one_auth_schema(self) -> None:
        assert len(manifest.auth_schemas) == 1

    def test_manifest_logo_and_name(self) -> None:
        assert manifest.name == "zoho_desk"
        assert manifest.logo == "modulex:zoho_desk"


# --- Token minting ----------------------------------------------------------


@pytest.mark.asyncio
async def test_token_mint_request_shape(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", url=f"{API}/tickets", json={"data": []})

    await list_tickets.ainvoke(_args())

    mint = httpx_mock.get_requests()[0]
    assert str(mint.url) == TOKEN_URL
    assert mint.method == "POST"
    form = _form(mint)
    assert form["grant_type"] == ["client_credentials"]
    assert form["client_id"] == ["1000.FAKECLIENTID"]
    assert form["client_secret"] == ["fake_client_secret"]
    assert form["soid"] == [f"ZohoDesk.{ORG_ID}"]
    assert form["scope"] == [
        "Desk.tickets.READ,Desk.tickets.UPDATE,Desk.contacts.READ,Desk.basic.READ"
    ]


@pytest.mark.asyncio
async def test_token_mint_uses_the_overriding_org_in_soid(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", url=f"{API}/tickets", json={"data": []})

    await list_tickets.ainvoke(_args(org_id="999888777"))

    assert _form(httpx_mock.get_requests()[0])["soid"] == ["ZohoDesk.999888777"]


@pytest.mark.asyncio
async def test_token_mint_failure_short_circuits(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    # Zoho answers a rejected credential with HTTP 200 and an `error` key.
    httpx_mock.add_response(
        method="POST", url=TOKEN_URL, json={"error": "invalid_client"}
    )

    result_dict = await list_tickets.ainvoke(_args())

    result = ListTicketsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "invalid_client" in result.error
    # the Desk API was never called
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_token_mint_http_error_short_circuits(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=TOKEN_URL,
        status_code=400,
        json={"message": "invalid_code"},
    )

    result_dict = await get_ticket.ainvoke(_args(ticket_id="1"))

    result = GetTicketOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "invalid_code"
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_token_response_without_access_token(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=TOKEN_URL, json={"expires_in": 3600})

    result_dict = await list_tickets.ainvoke(_args())

    result = ListTicketsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access_token" in result.error


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_list_tickets(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tickets?from=0&limit=2&status=Open",
        json={"data": [_TICKET]},
    )

    result_dict = await list_tickets.ainvoke(_args(from_index=0, limit=2, status="Open"))

    assert isinstance(result_dict, dict)
    result = ListTicketsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.tickets[0].subject == "Cannot log in"
    assert result.tickets[0].ticket_number == "101"
    # description is HTML -> the derived plain text strips the markup
    assert result.tickets[0].description_text == "Login fails with a 500"


@pytest.mark.asyncio
async def test_list_tickets_sends_org_header(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", url=f"{API}/tickets", json={"data": []})

    await list_tickets.ainvoke(_args())

    request = httpx_mock.get_requests()[1]
    assert request.headers["orgId"] == ORG_ID
    assert request.headers["Authorization"] == f"Zoho-oauthtoken {ACCESS_TOKEN}"


@pytest.mark.asyncio
async def test_get_ticket(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tickets/1892000000042001?include=contacts",
        json={**_TICKET, "contact": {"id": "1892000000042003", "email": "customer@example.com"}},
    )

    result_dict = await get_ticket.ainvoke(
        _args(ticket_id="1892000000042001", include="contacts")
    )

    assert isinstance(result_dict, dict)
    result = GetTicketOutput.model_validate(result_dict)
    assert result.success is True
    assert result.ticket is not None
    assert result.ticket.id == "1892000000042001"
    assert result.ticket.status_type == "Open"
    assert result.ticket.cf == {"cf_severity": "Sev2"}
    assert result.ticket.contact is not None
    # the untouched payload is preserved for anything the model does not name
    assert result.raw is not None
    assert result.raw["webUrl"] == _TICKET["webUrl"]


@pytest.mark.asyncio
async def test_update_ticket(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/tickets/1892000000042001",
        json={**_TICKET, "status": "Closed", "resolution": "Password reset"},
    )

    result_dict = await update_ticket.ainvoke(
        _args(
            ticket_id="1892000000042001",
            status="Closed",
            resolution="Password reset",
            custom_fields={"cf_severity": "Sev3"},
        )
    )

    assert isinstance(result_dict, dict)
    result = UpdateTicketOutput.model_validate(result_dict)
    assert result.success is True
    assert result.ticket is not None
    assert result.ticket.status == "Closed"
    assert result.ticket.resolution == "Password reset"

    sent = json.loads(httpx_mock.get_requests()[1].content)
    # untouched fields are omitted; custom fields go out under `cf`
    assert sent == {
        "status": "Closed",
        "resolution": "Password reset",
        "cf": {"cf_severity": "Sev3"},
    }


@pytest.mark.asyncio
async def test_list_comments(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tickets/1892000000042001/comments?from=0&limit=50",
        json={"data": [_COMMENT]},
    )

    result_dict = await list_comments.ainvoke(
        _args(ticket_id="1892000000042001", from_index=0, limit=50)
    )

    assert isinstance(result_dict, dict)
    result = ListCommentsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    comment = result.comments[0]
    assert comment.content_text == "Checked the auth logs"
    assert comment.commenter is not None
    assert comment.commenter.role_name == "Support"
    assert comment.attachments[0].name == "trace.log"


@pytest.mark.asyncio
async def test_add_comment(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/tickets/1892000000042001/comments",
        json={**_COMMENT, "content": "Escalating to tier 2", "contentType": "plainText"},
    )

    result_dict = await add_comment.ainvoke(
        _args(ticket_id="1892000000042001", content="Escalating to tier 2")
    )

    assert isinstance(result_dict, dict)
    result = AddCommentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.comment is not None
    assert result.comment.content_text == "Escalating to tier 2"

    sent = json.loads(httpx_mock.get_requests()[1].content)
    assert sent == {
        "content": "Escalating to tier 2",
        "contentType": "plainText",
        "isPublic": False,
    }


@pytest.mark.asyncio
async def test_list_threads(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tickets/1892000000042001/threads?limit=100",
        json={"data": [_THREAD]},
    )

    result_dict = await list_threads.ainvoke(_args(ticket_id="1892000000042001", limit=100))

    assert isinstance(result_dict, dict)
    result = ListThreadsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.threads[0].direction == "in"
    # contentType is the MIME spelling -> still stripped, entity decoded
    assert result.threads[0].content_text == "Still broken & urgent"


@pytest.mark.asyncio
async def test_get_thread(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tickets/1892000000042001/threads/1892000000088001",
        json=_THREAD,
    )

    result_dict = await get_thread.ainvoke(
        _args(ticket_id="1892000000042001", thread_id="1892000000088001")
    )

    assert isinstance(result_dict, dict)
    result = GetThreadOutput.model_validate(result_dict)
    assert result.success is True
    assert result.thread is not None
    assert result.thread.id == "1892000000088001"
    assert result.thread.author is not None
    assert result.thread.author.email == "customer@example.com"
    assert result.thread.summary == "Still broken"


@pytest.mark.asyncio
async def test_get_contact(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/contacts/1892000000042003",
        json=_CONTACT,
    )

    result_dict = await get_contact.ainvoke(_args(contact_id="1892000000042003"))

    assert isinstance(result_dict, dict)
    result = GetContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.contact is not None
    assert result.contact.last_name == "Customer"
    assert result.contact.secondary_email is None
    assert result.contact.zip == "73301"


@pytest.mark.asyncio
async def test_list_organizations(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/organizations",
        json={
            "data": [
                {"id": ORG_ID, "companyName": "Acme Inc", "portalName": "acme"},
            ]
        },
    )

    result_dict = await list_organizations.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListOrganizationsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.organizations[0].company_name == "Acme Inc"
    assert result.organizations[0].portal_name == "acme"
    # no orgId header on the bootstrap endpoint
    assert "orgId" not in httpx_mock.get_requests()[1].headers


# --- Data-center resolution -------------------------------------------------


@pytest.mark.asyncio
async def test_api_domain_drives_the_desk_host(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    """The token response's api_domain selects the Desk REST host."""
    _mock_token(httpx_mock, api_domain="https://www.zohoapis.in")
    httpx_mock.add_response(
        method="GET",
        url="https://desk.zoho.in/api/v1/tickets",
        json={"data": []},
    )

    result_dict = await list_tickets.ainvoke(_args())

    assert ListTicketsOutput.model_validate(result_dict).success is True


@pytest.mark.asyncio
async def test_data_center_selects_accounts_server(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    """The configured data center picks the accounts host that mints the token."""
    _mock_token(
        httpx_mock,
        api_domain="https://www.zohoapis.eu",
        url="https://accounts.zoho.eu/oauth/v2/token",
    )
    httpx_mock.add_response(
        method="GET",
        url="https://desk.zoho.eu/api/v1/tickets",
        json={"data": []},
    )

    result_dict = await list_tickets.ainvoke(
        {
            "auth_type": "custom",
            "auth_data": {
                "client_id": "1000.FAKECLIENTID",
                "client_secret": "fake_client_secret",
                "org_id": ORG_ID,
                "data_center": "eu",
            },
        }
    )

    assert ListTicketsOutput.model_validate(result_dict).success is True


@pytest.mark.asyncio
async def test_canada_uses_zohocloud_hosts(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    """Canada lives on ``zohocloud.ca``; ``zoho.ca`` does not resolve at all."""
    _mock_token(
        httpx_mock,
        api_domain="https://www.zohoapis.ca",
        url="https://accounts.zohocloud.ca/oauth/v2/token",
    )
    httpx_mock.add_response(
        method="GET",
        url="https://desk.zohocloud.ca/api/v1/tickets",
        json={"data": []},
    )

    result_dict = await list_tickets.ainvoke(
        {
            "auth_type": "custom",
            "auth_data": {
                "client_id": "1000.FAKECLIENTID",
                "client_secret": "fake_client_secret",
                "org_id": ORG_ID,
                "data_center": "ca",
            },
        }
    )

    assert ListTicketsOutput.model_validate(result_dict).success is True


def test_every_data_center_maps_to_a_confirmed_host() -> None:
    """Both host maps cover exactly the accepted data centers, no gaps."""
    assert set(_DESK_HOSTS) == set(_DATA_CENTER_TLDS)
    assert set(_ACCOUNTS_URLS) == set(_DATA_CENTER_TLDS)
    # The Canadian hosts are the ones that break a `desk.zoho.<tld>` pattern.
    assert _DESK_HOSTS["ca"] == "https://desk.zohocloud.ca"
    assert _ACCOUNTS_URLS["ca"] == "https://accounts.zohocloud.ca"


@pytest.mark.asyncio
async def test_unknown_data_center_falls_back_to_us(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", url=f"{API}/tickets", json={"data": []})

    result_dict = await list_tickets.ainvoke(
        {
            "auth_type": "custom",
            "auth_data": {
                "client_id": "1000.FAKECLIENTID",
                "client_secret": "fake_client_secret",
                "org_id": ORG_ID,
                "data_center": "not-a-zoho-dc",
            },
        }
    )

    assert ListTicketsOutput.model_validate(result_dict).success is True


@pytest.mark.asyncio
async def test_untrusted_api_domain_falls_back_to_us(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    """A look-alike api_domain must never receive the access token."""
    _mock_token(httpx_mock, api_domain="https://desk.zoho.com.attacker.example")
    httpx_mock.add_response(method="GET", url=f"{API}/tickets", json={"data": []})

    result_dict = await list_tickets.ainvoke(_args())

    assert ListTicketsOutput.model_validate(result_dict).success is True


# --- Failure paths ----------------------------------------------------------


@pytest.mark.asyncio
async def test_get_ticket_api_error(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tickets/999",
        status_code=422,
        json={"errorCode": "INVALID_DATA", "message": "The ticket id is invalid"},
    )

    result_dict = await get_ticket.ainvoke(_args(ticket_id="999"))

    result = GetTicketOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "The ticket id is invalid"
    assert result.ticket is None


@pytest.mark.asyncio
async def test_missing_credentials_makes_no_request(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result_dict = await list_tickets.ainvoke(
        {"auth_type": "custom", "auth_data": {"org_id": ORG_ID}}
    )

    result = ListTicketsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "client ID and client secret are required" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_blank_client_secret_is_rejected(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result_dict = await list_organizations.ainvoke(
        {
            "auth_type": "custom",
            "auth_data": {
                "client_id": "1000.FAKECLIENTID",
                "client_secret": "   ",
                "org_id": ORG_ID,
            },
        }
    )

    result = ListOrganizationsOutput.model_validate(result_dict)
    assert result.success is False
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_list_tickets_missing_org_id(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result_dict = await list_tickets.ainvoke(
        {
            "auth_type": "custom",
            "auth_data": {
                "client_id": "1000.FAKECLIENTID",
                "client_secret": "fake_client_secret",
            },
        }
    )

    result = ListTicketsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "organization ID is required" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_list_organizations_needs_an_org_for_the_soid(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result_dict = await list_organizations.ainvoke(
        {
            "auth_type": "custom",
            "auth_data": {
                "client_id": "1000.FAKECLIENTID",
                "client_secret": "fake_client_secret",
            },
        }
    )

    result = ListOrganizationsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "soid" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_update_ticket_without_fields_is_rejected(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result_dict = await update_ticket.ainvoke(_args(ticket_id="1892000000042001"))

    result = UpdateTicketOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "No fields to update" in result.error
    # rejected before any token is minted
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_get_thread_requires_thread_id(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result_dict = await get_thread.ainvoke(
        _args(ticket_id="1892000000042001", thread_id="   ")
    )

    result = GetThreadOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "Thread ID is required."
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_plain_text_comment_is_not_mangled(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tickets/1/comments",
        json={
            "data": [
                {
                    "id": "1",
                    "content": "replace <username> with the real name",
                    "contentType": "plainText",
                }
            ]
        },
    )

    result_dict = await list_comments.ainvoke(_args(ticket_id="1"))

    result = ListCommentsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.comments[0].content_text == "replace <username> with the real name"

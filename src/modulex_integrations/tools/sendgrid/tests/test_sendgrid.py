"""Tests for the SendGrid integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.sendgrid import (
    TOOLS,
    add_email_to_global_suppression,
    add_or_update_contact,
    create_contact_list,
    delete_blocks,
    delete_bounces,
    delete_contacts,
    delete_global_suppression,
    get_all_bounces,
    get_contact_lists,
    list_blocks,
    list_global_suppressions,
    manifest,
    remove_contact_from_list,
    search_contacts,
    send_email,
    send_email_multiple_recipients,
)
from modulex_integrations.tools.sendgrid.outputs import (
    AddEmailToGlobalSuppressionOutput,
    AddOrUpdateContactOutput,
    CreateContactListOutput,
    DeleteBlocksOutput,
    DeleteBouncesOutput,
    DeleteContactsOutput,
    DeleteGlobalSuppressionOutput,
    GetAllBouncesOutput,
    GetContactListsOutput,
    ListBlocksOutput,
    ListGlobalSuppressionsOutput,
    RemoveContactFromListOutput,
    SearchContactsOutput,
    SendEmailMultipleRecipientsOutput,
    SendEmailOutput,
)

API = "https://api.sendgrid.com/v3"
KEY = "SG.fake-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=KEY, **extra)


class TestManifest:
    def test_manifest_exposes_fifteen_actions(self) -> None:
        assert len(manifest.actions) == 15

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]


@pytest.mark.asyncio
async def test_send_email_success(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/mail/send",
        status_code=202,
        headers={"X-Message-Id": "msg-1"},
    )
    result_dict = await send_email.ainvoke(
        _args(
            to_email="a@x.io",
            from_email="b@x.io",
            subject="Hi",
            content="Hello",
        )
    )
    assert isinstance(result_dict, dict)
    result = SendEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message_id == "msg-1"


@pytest.mark.asyncio
async def test_send_email_api_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST", url=f"{API}/mail/send", status_code=401, text="invalid key"
    )
    result = SendEmailOutput.model_validate(
        await send_email.ainvoke(
            _args(to_email="a@x.io", from_email="b@x.io", subject="Hi", content="Hi")
        )
    )
    assert result.success is False
    assert result.error is not None and "401" in result.error


@pytest.mark.asyncio
async def test_send_email_multiple_recipients(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST", url=f"{API}/mail/send", status_code=202
    )
    result = SendEmailMultipleRecipientsOutput.model_validate(
        await send_email_multiple_recipients.ainvoke(
            _args(
                to_emails=["x@y.io", "z@y.io"],
                from_email="b@x.io",
                subject="Hi",
                content="Hello",
            )
        )
    )
    assert result.success is True
    assert result.recipient_count == 2


@pytest.mark.asyncio
async def test_add_or_update_contact(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/marketing/contacts",
        status_code=202,
        json={"job_id": "JOB-1"},
    )
    result = AddOrUpdateContactOutput.model_validate(
        await add_or_update_contact.ainvoke(
            _args(email="x@y.io", first_name="X", list_ids=["L1"])
        )
    )
    assert result.success is True
    assert result.job_id == "JOB-1"


@pytest.mark.asyncio
async def test_search_contacts(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/marketing/contacts/search",
        json={
            "result": [{"id": "c1", "email": "x@y.io", "first_name": "X"}],
            "contact_count": 1,
        },
    )
    result = SearchContactsOutput.model_validate(
        await search_contacts.ainvoke(_args(query="email LIKE 'x%'"))
    )
    assert result.success is True
    assert result.count == 1
    assert result.contacts[0].email == "x@y.io"


@pytest.mark.asyncio
async def test_create_contact_list(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/marketing/lists",
        status_code=201,
        json={"id": "L1", "name": "VIP"},
    )
    result = CreateContactListOutput.model_validate(
        await create_contact_list.ainvoke(_args(name="VIP"))
    )
    assert result.success is True
    assert result.id == "L1"


@pytest.mark.asyncio
async def test_get_contact_lists(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/marketing/lists?page_size=100",
        json={"result": [{"id": "L1", "name": "Main", "contact_count": 5}]},
    )
    result = GetContactListsOutput.model_validate(
        await get_contact_lists.ainvoke(_args())
    )
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_remove_contact_from_list(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/marketing/lists/L1/contacts?contact_ids=C1%2CC2",
        status_code=202,
    )
    result = RemoveContactFromListOutput.model_validate(
        await remove_contact_from_list.ainvoke(
            _args(list_id="L1", contact_ids=["C1", "C2"])
        )
    )
    assert result.success is True
    assert result.contacts_removed == 2


@pytest.mark.asyncio
async def test_delete_contacts_validates_xor() -> None:
    result = DeleteContactsOutput.model_validate(await delete_contacts.ainvoke(_args()))
    assert result.success is False
    assert result.error is not None and "delete_all" in result.error


@pytest.mark.asyncio
async def test_delete_contacts_by_id(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/marketing/contacts?ids=C1",
        status_code=202,
        json={"job_id": "JOB-2"},
    )
    result = DeleteContactsOutput.model_validate(
        await delete_contacts.ainvoke(_args(contact_ids=["C1"]))
    )
    assert result.success is True
    assert result.job_id == "JOB-2"


@pytest.mark.asyncio
async def test_add_global_suppression(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/asm/suppressions/global",
        status_code=201,
        json={"recipient_emails": ["x@y.io"]},
    )
    result = AddEmailToGlobalSuppressionOutput.model_validate(
        await add_email_to_global_suppression.ainvoke(
            _args(recipient_emails=["x@y.io"])
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_global_suppression(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/asm/suppressions/global/x@y.io",
        status_code=204,
    )
    result = DeleteGlobalSuppressionOutput.model_validate(
        await delete_global_suppression.ainvoke(_args(email="x@y.io"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_global_suppressions(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/suppression/unsubscribes?limit=100",
        json=[{"email": "x@y.io", "created": 1700000000}],
    )
    result = ListGlobalSuppressionsOutput.model_validate(
        await list_global_suppressions.ainvoke(_args())
    )
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_get_all_bounces(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/suppression/bounces",
        json=[{"email": "x@y.io", "reason": "550", "status": "5.1.1"}],
    )
    result = GetAllBouncesOutput.model_validate(
        await get_all_bounces.ainvoke(_args())
    )
    assert result.success is True
    assert result.bounces[0].reason == "550"


@pytest.mark.asyncio
async def test_delete_bounces(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/suppression/bounces", status_code=204
    )
    result = DeleteBouncesOutput.model_validate(
        await delete_bounces.ainvoke(_args(emails=["a@x.io"]))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_blocks(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/suppression/blocks?limit=100",
        json=[{"email": "x@y.io"}],
    )
    result = ListBlocksOutput.model_validate(
        await list_blocks.ainvoke(_args())
    )
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_delete_blocks(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/suppression/blocks", status_code=204
    )
    result = DeleteBlocksOutput.model_validate(
        await delete_blocks.ainvoke(_args(delete_all=True))
    )
    assert result.success is True

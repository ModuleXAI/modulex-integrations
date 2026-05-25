"""Tests for the Mailchimp integration."""
from __future__ import annotations

import hashlib
import re
from typing import Any

import pytest

from modulex_integrations.tools.mailchimp import (
    TOOLS,
    add_member_to_segment,
    add_note_to_subscriber,
    add_or_update_subscriber,
    create_campaign,
    create_list,
    delete_campaign,
    delete_list,
    delete_subscriber,
    get_campaign,
    get_campaign_report,
    get_campaigns,
    get_list,
    get_list_members,
    get_lists,
    get_member_tags,
    get_segments,
    get_subscriber,
    manifest,
    send_campaign,
    update_member_tags,
)
from modulex_integrations.tools.mailchimp.outputs import (
    AddMemberToSegmentOutput,
    AddNoteToSubscriberOutput,
    AddOrUpdateSubscriberOutput,
    CreateCampaignOutput,
    CreateListOutput,
    DeleteCampaignOutput,
    DeleteListOutput,
    DeleteSubscriberOutput,
    GetCampaignOutput,
    GetCampaignReportOutput,
    GetCampaignsOutput,
    GetListMembersOutput,
    GetListOutput,
    GetListsOutput,
    GetMemberTagsOutput,
    GetSegmentsOutput,
    GetSubscriberOutput,
    SendCampaignOutput,
    UpdateMemberTagsOutput,
)
from modulex_integrations.tools.mailchimp.tools import (
    _datacenter,
    _subscriber_hash,
)

# Use a fake key with us10 datacenter to keep URLs predictable.
KEY = "fake_api_key-us10"
API = "https://us10.api.mailchimp.com/3.0"
EMAIL = "alice@example.com"
HASH = hashlib.md5(EMAIL.encode()).hexdigest()


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=KEY, **extra)


class TestManifest:
    def test_manifest_exposes_19_actions(self) -> None:
        assert len(manifest.actions) == 19

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_and_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == [
            "oauth2",
            "api_key",
        ]


def test_datacenter_extraction() -> None:
    assert _datacenter("xxx-us10") == "us10"
    assert _datacenter("foo-eu1") == "eu1"
    assert _datacenter("no_dash") == "us10"  # default


def test_subscriber_hash_lowercases() -> None:
    assert _subscriber_hash("Alice@Example.com") == _subscriber_hash(
        "alice@example.com"
    )


@pytest.mark.asyncio
async def test_get_lists_empty_key() -> None:
    result = GetListsOutput.model_validate(
        await get_lists.ainvoke({"api_key": ""})
    )
    assert result.success is False


@pytest.mark.asyncio
async def test_get_lists(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/lists\?.*"),
        json={
            "lists": [
                {
                    "id": "L1",
                    "name": "Newsletter",
                    "stats": {"member_count": 100, "unsubscribe_count": 2},
                    "date_created": "2024-01-01",
                }
            ],
            "total_items": 1,
        },
    )
    result = GetListsOutput.model_validate(await get_lists.ainvoke(_args()))
    assert result.success is True
    assert result.lists[0]["member_count"] == 100


@pytest.mark.asyncio
async def test_get_list(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/lists/L1",
        json={"id": "L1", "name": "Newsletter", "stats": {"member_count": 5}},
    )
    result = GetListOutput.model_validate(
        await get_list.ainvoke(_args(list_id="L1"))
    )
    assert result.success is True
    assert result.id == "L1"


@pytest.mark.asyncio
async def test_create_list_flattens_payload(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json as _json

        from httpx import Response

        captured.update(_json.loads(request.content.decode()))
        return Response(201, json={"id": "L_new", "name": "X"})

    httpx_mock.add_callback(_capture, method="POST", url=f"{API}/lists")
    result = CreateListOutput.model_validate(
        await create_list.ainvoke(
            _args(
                name="X",
                contact_company="Acme",
                contact_address1="1 St",
                contact_city="SF",
                contact_state="CA",
                contact_zip="94000",
                contact_country="US",
                permission_reminder="You signed up",
                from_name="Acme",
                from_email="hi@acme.io",
                subject="Welcome",
            )
        )
    )
    assert result.success is True
    assert captured["contact"]["company"] == "Acme"
    assert captured["campaign_defaults"]["from_email"] == "hi@acme.io"


@pytest.mark.asyncio
async def test_delete_list(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/lists/L1", status_code=204
    )
    result = DeleteListOutput.model_validate(
        await delete_list.ainvoke(_args(list_id="L1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_list_members(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/lists/L1/members\?.*"),
        json={"members": [{"id": "m1"}], "total_items": 1},
    )
    result = GetListMembersOutput.model_validate(
        await get_list_members.ainvoke(_args(list_id="L1"))
    )
    assert result.success is True
    assert result.total_items == 1


@pytest.mark.asyncio
async def test_get_subscriber_uses_md5_hash(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/lists/L1/members/{HASH}",
        json={
            "id": "m1",
            "email_address": EMAIL,
            "status": "subscribed",
            "tags": [{"name": "vip"}, {"name": "early"}],
        },
    )
    result = GetSubscriberOutput.model_validate(
        await get_subscriber.ainvoke(_args(list_id="L1", email=EMAIL))
    )
    assert result.success is True
    assert result.tags == ["vip", "early"]


@pytest.mark.asyncio
async def test_add_or_update_subscriber(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/lists/L1/members/{HASH}",
        status_code=200,
        json={"id": "m1", "email_address": EMAIL, "status": "subscribed"},
    )
    result = AddOrUpdateSubscriberOutput.model_validate(
        await add_or_update_subscriber.ainvoke(
            _args(list_id="L1", email=EMAIL, merge_fields={"FNAME": "Alice"})
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_add_or_update_subscriber_with_tags_makes_two_calls(
    httpx_mock: Any,
) -> None:
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/lists/L1/members/{HASH}",
        status_code=200,
        json={"id": "m1", "email_address": EMAIL, "status": "subscribed"},
    )
    captured_tags: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json as _json

        from httpx import Response

        captured_tags.update(_json.loads(request.content.decode()))
        return Response(204)

    httpx_mock.add_callback(
        _capture,
        method="POST",
        url=f"{API}/lists/L1/members/{HASH}/tags",
    )
    result = AddOrUpdateSubscriberOutput.model_validate(
        await add_or_update_subscriber.ainvoke(
            _args(list_id="L1", email=EMAIL, tags=["vip"])
        )
    )
    assert result.success is True
    # Tag payload uses {name, status: 'active'} shape.
    assert captured_tags["tags"][0]["name"] == "vip"
    assert captured_tags["tags"][0]["status"] == "active"


@pytest.mark.asyncio
async def test_delete_subscriber_uses_permanent_path(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/lists/L1/members/{HASH}/actions/delete-permanent",
        status_code=204,
    )
    result = DeleteSubscriberOutput.model_validate(
        await delete_subscriber.ainvoke(_args(list_id="L1", email=EMAIL))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_campaigns(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/campaigns\?.*"),
        json={
            "campaigns": [
                {
                    "id": "C1",
                    "type": "regular",
                    "status": "sent",
                    "settings": {
                        "subject_line": "Hi",
                        "title": "Title",
                        "from_name": "Acme",
                    },
                    "emails_sent": 100,
                }
            ],
            "total_items": 1,
        },
    )
    result = GetCampaignsOutput.model_validate(
        await get_campaigns.ainvoke(_args(status="sent"))
    )
    assert result.success is True
    assert result.campaigns[0]["emails_sent"] == 100


@pytest.mark.asyncio
async def test_get_campaign(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/campaigns/C1", json={"id": "C1"}
    )
    result = GetCampaignOutput.model_validate(
        await get_campaign.ainvoke(_args(campaign_id="C1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_campaign(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json as _json

        from httpx import Response

        captured.update(_json.loads(request.content.decode()))
        return Response(201, json={"id": "C_new", "type": "regular", "status": "save"})

    httpx_mock.add_callback(_capture, method="POST", url=f"{API}/campaigns")
    result = CreateCampaignOutput.model_validate(
        await create_campaign.ainvoke(
            _args(
                list_id="L1",
                subject_line="Hello",
                from_name="Acme",
                reply_to="hi@acme.io",
                title="Title",
            )
        )
    )
    assert result.success is True
    # Verify the body structure (recipients + settings).
    assert captured["recipients"]["list_id"] == "L1"
    assert captured["settings"]["subject_line"] == "Hello"
    assert captured["settings"]["title"] == "Title"


@pytest.mark.asyncio
async def test_delete_campaign(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/campaigns/C1", status_code=204
    )
    result = DeleteCampaignOutput.model_validate(
        await delete_campaign.ainvoke(_args(campaign_id="C1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_send_campaign(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/campaigns/C1/actions/send",
        status_code=204,
    )
    result = SendCampaignOutput.model_validate(
        await send_campaign.ainvoke(_args(campaign_id="C1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_campaign_report(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/reports/C1",
        json={"id": "C1", "send_time": "2024-01-01", "emails_sent": 100},
    )
    result = GetCampaignReportOutput.model_validate(
        await get_campaign_report.ainvoke(_args(campaign_id="C1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_member_tags(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/lists/L1/members/{HASH}/tags",
        json={"tags": [{"id": 1, "name": "vip"}], "total_items": 1},
    )
    result = GetMemberTagsOutput.model_validate(
        await get_member_tags.ainvoke(_args(list_id="L1", email=EMAIL))
    )
    assert result.success is True
    assert result.total_items == 1


@pytest.mark.asyncio
async def test_update_member_tags(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/lists/L1/members/{HASH}/tags",
        status_code=204,
    )
    result = UpdateMemberTagsOutput.model_validate(
        await update_member_tags.ainvoke(
            _args(
                list_id="L1",
                email=EMAIL,
                tags=[{"name": "vip", "status": "active"}],
            )
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_add_note_to_subscriber(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/lists/L1/members/{HASH}/notes",
        status_code=201,
        json={"id": 1, "note": "Likes coffee", "created_at": "2024-01-01"},
    )
    result = AddNoteToSubscriberOutput.model_validate(
        await add_note_to_subscriber.ainvoke(
            _args(list_id="L1", email=EMAIL, note="Likes coffee")
        )
    )
    assert result.success is True
    assert result.note == "Likes coffee"


@pytest.mark.asyncio
async def test_get_segments(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/lists/L1/segments\?.*"),
        json={"segments": [{"id": "S1", "name": "VIPs"}], "total_items": 1},
    )
    result = GetSegmentsOutput.model_validate(
        await get_segments.ainvoke(_args(list_id="L1"))
    )
    assert result.success is True
    assert result.total_items == 1


@pytest.mark.asyncio
async def test_add_member_to_segment(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/lists/L1/segments/S1/members",
        status_code=200,
        json={"id": "m1"},
    )
    result = AddMemberToSegmentOutput.model_validate(
        await add_member_to_segment.ainvoke(
            _args(list_id="L1", segment_id="S1", email=EMAIL)
        )
    )
    assert result.success is True

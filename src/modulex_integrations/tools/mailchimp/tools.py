"""Mailchimp LangChain ``@tool`` functions.

Pure HTTP integration against Mailchimp's Marketing API v3.0. Key-based
runtime convention (``api_key: str`` first arg).

Mailchimp quirks preserved verbatim:

- **Datacenter is embedded in the API key suffix** (`xxx-us10`). We
  extract it and route to `https://{dc}.api.mailchimp.com/3.0`.
- **Basic Auth** with a literal `anystring` username and the API key
  as the password.
- **Subscribers are addressed by MD5 hash of lowercase email** —
  `members/{md5_hash}` paths.
- **`add_or_update_subscriber`** is a 2-call workflow when tags are
  given: PUT the subscriber then POST tags.
- **`delete_subscriber`** uses the permanent-delete action path:
  `/members/{md5}/actions/delete-permanent`.
- All actions wrap in try/except → unified ``success=False`` envelope.
"""
from __future__ import annotations

import base64
import hashlib
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
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

__all__ = [
    "add_member_to_segment",
    "add_note_to_subscriber",
    "add_or_update_subscriber",
    "create_campaign",
    "create_list",
    "delete_campaign",
    "delete_list",
    "delete_subscriber",
    "get_campaign",
    "get_campaign_report",
    "get_campaigns",
    "get_list",
    "get_list_members",
    "get_lists",
    "get_member_tags",
    "get_segments",
    "get_subscriber",
    "send_campaign",
    "update_member_tags",
]

_TIMEOUT = 30.0


def _datacenter(api_key: str) -> str:
    return api_key.rsplit("-", 1)[-1] if "-" in api_key else "us10"


def _base_url(api_key: str) -> str:
    return f"https://{_datacenter(api_key)}.api.mailchimp.com/3.0"


def _headers(api_key: str) -> dict[str, str]:
    encoded = base64.b64encode(f"anystring:{api_key}".encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _subscriber_hash(email: str) -> str:
    return hashlib.md5(email.lower().encode()).hexdigest()


def _validate(api_key: str, action: str) -> str | None:
    if not api_key or not api_key.strip():
        return f"Mailchimp API key is empty for {action}"
    return None


def _api_err(status: int, body: str) -> str:
    return f"API error {status}: {body}"


async def _call(
    method: str,
    api_key: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    success_codes: tuple[int, ...] = (200,),
) -> tuple[bool, str | None, dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.request(
                method,
                f"{_base_url(api_key)}{path}",
                headers=_headers(api_key),
                json=json_body,
                params=params,
            )
        if response.status_code not in success_codes:
            return False, _api_err(response.status_code, response.text), {}
        if response.status_code == 204 or not response.content:
            return True, None, {}
        return True, None, response.json() or {}
    except httpx.TimeoutException:
        return False, "Request timed out", {}
    except Exception as exc:
        return False, str(exc), {}


# --- Input schemas ---------------------------------------------------------


class _KeyField(BaseModel):
    api_key: str = Field(description="Mailchimp API key")


class GetListsInput(_KeyField):
    count: int = 10
    offset: int = 0


class GetListInput(_KeyField):
    list_id: str


class CreateListInput(_KeyField):
    name: str
    contact_company: str
    contact_address1: str
    contact_city: str
    contact_state: str
    contact_zip: str
    contact_country: str
    permission_reminder: str
    from_name: str
    from_email: str
    subject: str
    language: str = "en"
    email_type_option: bool = False


class DeleteListInput(_KeyField):
    list_id: str


class GetListMembersInput(_KeyField):
    list_id: str
    count: int = 10
    offset: int = 0
    status: str | None = None


class GetSubscriberInput(_KeyField):
    list_id: str
    email: str


class AddOrUpdateSubscriberInput(_KeyField):
    list_id: str
    email: str
    status_if_new: str = "subscribed"
    status: str | None = None
    email_type: str | None = None
    merge_fields: dict[str, Any] | None = None
    language: str | None = None
    vip: bool | None = None
    tags: list[str] | None = None


class DeleteSubscriberInput(_KeyField):
    list_id: str
    email: str


class GetCampaignsInput(_KeyField):
    count: int = 10
    offset: int = 0
    type: str | None = None
    status: str | None = None


class GetCampaignInput(_KeyField):
    campaign_id: str


class CreateCampaignInput(_KeyField):
    type: str = "regular"
    list_id: str
    subject_line: str
    from_name: str
    reply_to: str
    title: str | None = None
    preview_text: str | None = None


class DeleteCampaignInput(_KeyField):
    campaign_id: str


class SendCampaignInput(_KeyField):
    campaign_id: str


class GetCampaignReportInput(_KeyField):
    campaign_id: str


class GetMemberTagsInput(_KeyField):
    list_id: str
    email: str


class UpdateMemberTagsInput(_KeyField):
    list_id: str
    email: str
    tags: list[dict[str, str]]


class AddNoteToSubscriberInput(_KeyField):
    list_id: str
    email: str
    note: str


class GetSegmentsInput(_KeyField):
    list_id: str
    count: int = 10
    offset: int = 0


class AddMemberToSegmentInput(_KeyField):
    list_id: str
    segment_id: str
    email: str


# --- Tools — lists --------------------------------------------------------


@tool(args_schema=GetListsInput)
@serialize_pydantic_return
async def get_lists(
    api_key: str, count: int = 10, offset: int = 0
) -> GetListsOutput:
    """List all audiences."""
    err = _validate(api_key, "get_lists")
    if err:
        return GetListsOutput(success=False, error=err)
    ok, e, data = await _call(
        "GET",
        api_key,
        "/lists",
        params={"count": min(count, 1000), "offset": offset},
    )
    if not ok:
        return GetListsOutput(success=False, error=e)
    lists = [
        {
            "id": lst.get("id"),
            "name": lst.get("name"),
            "member_count": (lst.get("stats") or {}).get("member_count", 0),
            "unsubscribe_count": (lst.get("stats") or {}).get(
                "unsubscribe_count", 0
            ),
            "date_created": lst.get("date_created"),
        }
        for lst in data.get("lists") or []
    ]
    return GetListsOutput(
        success=True,
        lists=lists,
        total_items=data.get("total_items", len(lists)),
    )


@tool(args_schema=GetListInput)
@serialize_pydantic_return
async def get_list(api_key: str, list_id: str) -> GetListOutput:
    """Get details for a specific list/audience."""
    err = _validate(api_key, "get_list")
    if err:
        return GetListOutput(success=False, error=err)
    ok, e, data = await _call("GET", api_key, f"/lists/{list_id}")
    if not ok:
        return GetListOutput(success=False, error=e)
    return GetListOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        permission_reminder=data.get("permission_reminder"),
        contact=data.get("contact") or {},
        campaign_defaults=data.get("campaign_defaults") or {},
        stats=data.get("stats") or {},
        date_created=data.get("date_created"),
    )


@tool(args_schema=CreateListInput)
@serialize_pydantic_return
async def create_list(
    api_key: str,
    name: str,
    contact_company: str,
    contact_address1: str,
    contact_city: str,
    contact_state: str,
    contact_zip: str,
    contact_country: str,
    permission_reminder: str,
    from_name: str,
    from_email: str,
    subject: str,
    language: str = "en",
    email_type_option: bool = False,
) -> CreateListOutput:
    """Create a new audience."""
    err = _validate(api_key, "create_list")
    if err:
        return CreateListOutput(success=False, error=err)
    payload = {
        "name": name,
        "contact": {
            "company": contact_company,
            "address1": contact_address1,
            "city": contact_city,
            "state": contact_state,
            "zip": contact_zip,
            "country": contact_country,
        },
        "permission_reminder": permission_reminder,
        "campaign_defaults": {
            "from_name": from_name,
            "from_email": from_email,
            "subject": subject,
            "language": language,
        },
        "email_type_option": email_type_option,
    }
    ok, e, data = await _call(
        "POST", api_key, "/lists", json_body=payload, success_codes=(200, 201)
    )
    if not ok:
        return CreateListOutput(success=False, error=e)
    return CreateListOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        date_created=data.get("date_created"),
        message="List created successfully",
    )


@tool(args_schema=DeleteListInput)
@serialize_pydantic_return
async def delete_list(api_key: str, list_id: str) -> DeleteListOutput:
    """Delete an audience permanently."""
    err = _validate(api_key, "delete_list")
    if err:
        return DeleteListOutput(success=False, error=err)
    ok, e, _ = await _call(
        "DELETE", api_key, f"/lists/{list_id}", success_codes=(204,)
    )
    if not ok:
        return DeleteListOutput(success=False, error=e)
    return DeleteListOutput(
        success=True, message="List deleted successfully", list_id=list_id
    )


# --- Tools — subscribers --------------------------------------------------


@tool(args_schema=GetListMembersInput)
@serialize_pydantic_return
async def get_list_members(
    api_key: str,
    list_id: str,
    count: int = 10,
    offset: int = 0,
    status: str | None = None,
) -> GetListMembersOutput:
    """List members in an audience."""
    err = _validate(api_key, "get_list_members")
    if err:
        return GetListMembersOutput(success=False, error=err)
    params: dict[str, Any] = {"count": min(count, 1000), "offset": offset}
    if status:
        params["status"] = status
    ok, e, data = await _call(
        "GET", api_key, f"/lists/{list_id}/members", params=params
    )
    if not ok:
        return GetListMembersOutput(success=False, error=e)
    members = data.get("members") or []
    return GetListMembersOutput(
        success=True,
        members=members,
        total_items=data.get("total_items", len(members)),
    )


@tool(args_schema=GetSubscriberInput)
@serialize_pydantic_return
async def get_subscriber(
    api_key: str, list_id: str, email: str
) -> GetSubscriberOutput:
    """Get a subscriber by email (MD5 hash lookup)."""
    err = _validate(api_key, "get_subscriber")
    if err:
        return GetSubscriberOutput(success=False, error=err)
    ok, e, data = await _call(
        "GET",
        api_key,
        f"/lists/{list_id}/members/{_subscriber_hash(email)}",
    )
    if not ok:
        return GetSubscriberOutput(success=False, error=e)
    return GetSubscriberOutput(
        success=True,
        id=data.get("id"),
        email_address=data.get("email_address"),
        status=data.get("status"),
        merge_fields=data.get("merge_fields") or {},
        tags=[t.get("name") for t in data.get("tags") or []],
        vip=bool(data.get("vip", False)),
        language=data.get("language"),
        timestamp_signup=data.get("timestamp_signup"),
        last_changed=data.get("last_changed"),
    )


@tool(args_schema=AddOrUpdateSubscriberInput)
@serialize_pydantic_return
async def add_or_update_subscriber(
    api_key: str,
    list_id: str,
    email: str,
    status_if_new: str = "subscribed",
    status: str | None = None,
    email_type: str | None = None,
    merge_fields: dict[str, Any] | None = None,
    language: str | None = None,
    vip: bool | None = None,
    tags: list[str] | None = None,
) -> AddOrUpdateSubscriberOutput:
    """Upsert a subscriber (PUT); if tags are given, follow up with POST tags."""
    err = _validate(api_key, "add_or_update_subscriber")
    if err:
        return AddOrUpdateSubscriberOutput(success=False, error=err)
    subscriber_hash = _subscriber_hash(email)
    payload: dict[str, Any] = {
        "email_address": email,
        "status_if_new": status_if_new,
    }
    if status:
        payload["status"] = status
    if email_type:
        payload["email_type"] = email_type
    if merge_fields:
        payload["merge_fields"] = merge_fields
    if language:
        payload["language"] = language
    if vip is not None:
        payload["vip"] = vip

    ok, e, data = await _call(
        "PUT",
        api_key,
        f"/lists/{list_id}/members/{subscriber_hash}",
        json_body=payload,
        success_codes=(200, 201),
    )
    if not ok:
        return AddOrUpdateSubscriberOutput(success=False, error=e)
    if tags:
        await _call(
            "POST",
            api_key,
            f"/lists/{list_id}/members/{subscriber_hash}/tags",
            json_body={
                "tags": [{"name": tag, "status": "active"} for tag in tags]
            },
            success_codes=(200, 201, 204),
        )
    return AddOrUpdateSubscriberOutput(
        success=True,
        id=data.get("id"),
        email_address=data.get("email_address"),
        status=data.get("status"),
        merge_fields=data.get("merge_fields") or {},
        message="Subscriber added/updated successfully",
    )


@tool(args_schema=DeleteSubscriberInput)
@serialize_pydantic_return
async def delete_subscriber(
    api_key: str, list_id: str, email: str
) -> DeleteSubscriberOutput:
    """Permanently delete a subscriber."""
    err = _validate(api_key, "delete_subscriber")
    if err:
        return DeleteSubscriberOutput(success=False, error=err)
    ok, e, _ = await _call(
        "DELETE",
        api_key,
        f"/lists/{list_id}/members/{_subscriber_hash(email)}/actions/delete-permanent",
        success_codes=(204,),
    )
    if not ok:
        return DeleteSubscriberOutput(success=False, error=e)
    return DeleteSubscriberOutput(
        success=True,
        message="Subscriber deleted successfully",
        email=email,
        list_id=list_id,
    )


# --- Tools — campaigns ----------------------------------------------------


@tool(args_schema=GetCampaignsInput)
@serialize_pydantic_return
async def get_campaigns(
    api_key: str,
    count: int = 10,
    offset: int = 0,
    type: str | None = None,
    status: str | None = None,
) -> GetCampaignsOutput:
    """List campaigns."""
    err = _validate(api_key, "get_campaigns")
    if err:
        return GetCampaignsOutput(success=False, error=err)
    params: dict[str, Any] = {"count": min(count, 1000), "offset": offset}
    if type:
        params["type"] = type
    if status:
        params["status"] = status
    ok, e, data = await _call("GET", api_key, "/campaigns", params=params)
    if not ok:
        return GetCampaignsOutput(success=False, error=e)
    campaigns = [
        {
            "id": c.get("id"),
            "type": c.get("type"),
            "status": c.get("status"),
            "subject_line": (c.get("settings") or {}).get("subject_line"),
            "title": (c.get("settings") or {}).get("title"),
            "from_name": (c.get("settings") or {}).get("from_name"),
            "send_time": c.get("send_time"),
            "emails_sent": c.get("emails_sent", 0),
            "create_time": c.get("create_time"),
        }
        for c in data.get("campaigns") or []
    ]
    return GetCampaignsOutput(
        success=True,
        campaigns=campaigns,
        total_items=data.get("total_items", len(campaigns)),
    )


@tool(args_schema=GetCampaignInput)
@serialize_pydantic_return
async def get_campaign(
    api_key: str, campaign_id: str
) -> GetCampaignOutput:
    """Get a specific campaign."""
    err = _validate(api_key, "get_campaign")
    if err:
        return GetCampaignOutput(success=False, error=err)
    ok, e, data = await _call("GET", api_key, f"/campaigns/{campaign_id}")
    if not ok:
        return GetCampaignOutput(success=False, error=e)
    return GetCampaignOutput(success=True, result=data)


@tool(args_schema=CreateCampaignInput)
@serialize_pydantic_return
async def create_campaign(
    api_key: str,
    list_id: str,
    subject_line: str,
    from_name: str,
    reply_to: str,
    type: str = "regular",
    title: str | None = None,
    preview_text: str | None = None,
) -> CreateCampaignOutput:
    """Create a campaign."""
    err = _validate(api_key, "create_campaign")
    if err:
        return CreateCampaignOutput(success=False, error=err)
    settings: dict[str, Any] = {
        "subject_line": subject_line,
        "from_name": from_name,
        "reply_to": reply_to,
    }
    if title:
        settings["title"] = title
    if preview_text:
        settings["preview_text"] = preview_text
    payload = {
        "type": type,
        "recipients": {"list_id": list_id},
        "settings": settings,
    }
    ok, e, data = await _call(
        "POST", api_key, "/campaigns", json_body=payload, success_codes=(200, 201)
    )
    if not ok:
        return CreateCampaignOutput(success=False, error=e)
    return CreateCampaignOutput(
        success=True,
        id=data.get("id"),
        type=data.get("type"),
        status=data.get("status"),
        message="Campaign created successfully",
    )


@tool(args_schema=DeleteCampaignInput)
@serialize_pydantic_return
async def delete_campaign(
    api_key: str, campaign_id: str
) -> DeleteCampaignOutput:
    """Delete a campaign."""
    err = _validate(api_key, "delete_campaign")
    if err:
        return DeleteCampaignOutput(success=False, error=err)
    ok, e, _ = await _call(
        "DELETE",
        api_key,
        f"/campaigns/{campaign_id}",
        success_codes=(204,),
    )
    if not ok:
        return DeleteCampaignOutput(success=False, error=e)
    return DeleteCampaignOutput(
        success=True,
        message="Campaign deleted successfully",
        campaign_id=campaign_id,
    )


@tool(args_schema=SendCampaignInput)
@serialize_pydantic_return
async def send_campaign(
    api_key: str, campaign_id: str
) -> SendCampaignOutput:
    """Send a campaign."""
    err = _validate(api_key, "send_campaign")
    if err:
        return SendCampaignOutput(success=False, error=err)
    ok, e, _ = await _call(
        "POST",
        api_key,
        f"/campaigns/{campaign_id}/actions/send",
        success_codes=(204,),
    )
    if not ok:
        return SendCampaignOutput(success=False, error=e)
    return SendCampaignOutput(
        success=True,
        message="Campaign sent successfully",
        campaign_id=campaign_id,
    )


@tool(args_schema=GetCampaignReportInput)
@serialize_pydantic_return
async def get_campaign_report(
    api_key: str, campaign_id: str
) -> GetCampaignReportOutput:
    """Get a campaign's send/open/click report."""
    err = _validate(api_key, "get_campaign_report")
    if err:
        return GetCampaignReportOutput(success=False, error=err)
    ok, e, data = await _call(
        "GET", api_key, f"/reports/{campaign_id}"
    )
    if not ok:
        return GetCampaignReportOutput(success=False, error=e)
    return GetCampaignReportOutput(success=True, result=data)


# --- Tools — tags / notes / segments --------------------------------------


@tool(args_schema=GetMemberTagsInput)
@serialize_pydantic_return
async def get_member_tags(
    api_key: str, list_id: str, email: str
) -> GetMemberTagsOutput:
    """Get tags attached to a subscriber."""
    err = _validate(api_key, "get_member_tags")
    if err:
        return GetMemberTagsOutput(success=False, error=err)
    ok, e, data = await _call(
        "GET",
        api_key,
        f"/lists/{list_id}/members/{_subscriber_hash(email)}/tags",
    )
    if not ok:
        return GetMemberTagsOutput(success=False, error=e)
    tags = data.get("tags") or []
    return GetMemberTagsOutput(
        success=True,
        tags=tags,
        total_items=data.get("total_items", len(tags)),
    )


@tool(args_schema=UpdateMemberTagsInput)
@serialize_pydantic_return
async def update_member_tags(
    api_key: str,
    list_id: str,
    email: str,
    tags: list[dict[str, str]],
) -> UpdateMemberTagsOutput:
    """Update tags on a subscriber."""
    err = _validate(api_key, "update_member_tags")
    if err:
        return UpdateMemberTagsOutput(success=False, error=err)
    ok, e, _ = await _call(
        "POST",
        api_key,
        f"/lists/{list_id}/members/{_subscriber_hash(email)}/tags",
        json_body={"tags": tags},
        success_codes=(200, 204),
    )
    if not ok:
        return UpdateMemberTagsOutput(success=False, error=e)
    return UpdateMemberTagsOutput(
        success=True,
        message="Tags updated successfully",
        email=email,
    )


@tool(args_schema=AddNoteToSubscriberInput)
@serialize_pydantic_return
async def add_note_to_subscriber(
    api_key: str, list_id: str, email: str, note: str
) -> AddNoteToSubscriberOutput:
    """Add an internal note to a subscriber."""
    err = _validate(api_key, "add_note_to_subscriber")
    if err:
        return AddNoteToSubscriberOutput(success=False, error=err)
    ok, e, data = await _call(
        "POST",
        api_key,
        f"/lists/{list_id}/members/{_subscriber_hash(email)}/notes",
        json_body={"note": note},
        success_codes=(200, 201),
    )
    if not ok:
        return AddNoteToSubscriberOutput(success=False, error=e)
    return AddNoteToSubscriberOutput(
        success=True,
        id=data.get("id"),
        note=data.get("note"),
        email=email,
        created_at=data.get("created_at"),
    )


@tool(args_schema=GetSegmentsInput)
@serialize_pydantic_return
async def get_segments(
    api_key: str, list_id: str, count: int = 10, offset: int = 0
) -> GetSegmentsOutput:
    """List segments in an audience."""
    err = _validate(api_key, "get_segments")
    if err:
        return GetSegmentsOutput(success=False, error=err)
    ok, e, data = await _call(
        "GET",
        api_key,
        f"/lists/{list_id}/segments",
        params={"count": min(count, 1000), "offset": offset},
    )
    if not ok:
        return GetSegmentsOutput(success=False, error=e)
    segments = data.get("segments") or []
    return GetSegmentsOutput(
        success=True,
        segments=segments,
        total_items=data.get("total_items", len(segments)),
    )


@tool(args_schema=AddMemberToSegmentInput)
@serialize_pydantic_return
async def add_member_to_segment(
    api_key: str, list_id: str, segment_id: str, email: str
) -> AddMemberToSegmentOutput:
    """Add a subscriber email to a static segment."""
    err = _validate(api_key, "add_member_to_segment")
    if err:
        return AddMemberToSegmentOutput(success=False, error=err)
    ok, e, _ = await _call(
        "POST",
        api_key,
        f"/lists/{list_id}/segments/{segment_id}/members",
        json_body={"email_address": email},
        success_codes=(200, 201, 204),
    )
    if not ok:
        return AddMemberToSegmentOutput(success=False, error=e)
    return AddMemberToSegmentOutput(
        success=True,
        message="Member added to segment successfully",
        email=email,
        segment_id=segment_id,
    )

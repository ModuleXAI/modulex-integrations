"""GoHighLevel LangChain ``@tool`` functions.

Pure HTTP integration against the GoHighLevel (LeadConnector) v2 API.
Credentials arrive as ``auth_type, auth_data`` (first args); ``auth_data``
carries the OAuth 2.0 ``access_token`` plus the ``location_id`` of the
sub-account the token was issued for.

Almost every v2 endpoint is scoped to a sub-account. The location ID is a
credential-level fact, not a per-call decision, so it is read from
``auth_data`` rather than exposed as an action parameter — the same shape
``azure_storage`` uses for its storage-account name. Endpoints whose path
template contains ``{locationId}`` receive it from the same helper.

Every request carries a ``Version`` header — GoHighLevel rejects v2 calls
without one — but not the same value everywhere: the conversations and
calendars families are pinned to ``2021-04-15`` and the rest to
``2021-07-28``, so ``_request`` resolves it from the path.

Error model: nothing raises past the ``@tool`` boundary. Transport failures,
non-2xx responses and malformed bodies all fold into one ``success=False`` +
``error`` envelope produced by ``_request``. Response values are routed
through the ``_as_*`` coercers before reaching a pydantic model, so a field
that arrives with an unexpected *type* degrades to ``None`` instead of
raising ``ValidationError`` after the request already succeeded.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.gohighlevel.outputs import (
    AddContactFollowersOutput,
    AddContactTagsOutput,
    AddContactToCampaignOutput,
    AddContactToWorkflowOutput,
    AddInboundMessageOutput,
    AddMessageAttachmentsOutput,
    AddOpportunityFollowersOutput,
    AddOutboundMessageOutput,
    AppointmentDetails,
    AppointmentNoteCreator,
    AppointmentNoteDetails,
    AttachScheduleToCalendarOutput,
    AvailabilityScheduleDetails,
    AvailabilityScheduleInterval,
    AvailabilityScheduleRule,
    BlockSlotDetails,
    BulkUpdateContactsBusinessOutput,
    BulkUpdateContactTagsOutput,
    CalendarDetails,
    CalendarEventCreator,
    CalendarEventDetails,
    CalendarFreeSlotDay,
    CalendarGroupDetails,
    CalendarNotificationDetails,
    CalendarNotificationSchedule,
    CalendarResourceDetails,
    CampaignResource,
    CancelScheduledEmailMessageOutput,
    CancelScheduledMessageOutput,
    CompleteContactTaskOutput,
    CompleteMessageFileUploadOutput,
    ContactAppointmentResource,
    ContactAttribution,
    ContactCustomField,
    ContactDndSetting,
    ContactDndSettings,
    ContactNoteResource,
    ContactResource,
    ContactTaskResource,
    ConversationResource,
    CreateAppointmentNoteOutput,
    CreateAppointmentOutput,
    CreateAvailabilityScheduleOutput,
    CreateBlockSlotOutput,
    CreateCalendarGroupOutput,
    CreateCalendarNotificationOutput,
    CreateCalendarOutput,
    CreateCalendarResourceOutput,
    CreateContactNoteOutput,
    CreateContactOutput,
    CreateContactTaskOutput,
    CreateConversationOutput,
    CreateCustomSubtypeOutput,
    CreateEmailTemplateOutput,
    CreateOpportunityOutput,
    DeleteAppointmentNoteOutput,
    DeleteAvailabilityScheduleOutput,
    DeleteCalendarGroupOutput,
    DeleteCalendarNotificationOutput,
    DeleteCalendarOutput,
    DeleteCalendarResourceOutput,
    DeleteContactFromWorkflowOutput,
    DeleteContactNoteOutput,
    DeleteContactOutput,
    DeleteContactTaskOutput,
    DeleteConversationOutput,
    DeleteEmailTemplateOutput,
    DeleteEventOutput,
    DeleteOpportunityOutput,
    DetachScheduleFromCalendarOutput,
    EmailMessageResource,
    EmailScheduleResource,
    EmailTemplateResource,
    ExportMessagesOutput,
    GetAppointmentOutput,
    GetAvailabilityScheduleOutput,
    GetCalendarFreeSlotsOutput,
    GetCalendarNotificationOutput,
    GetCalendarOutput,
    GetCalendarResourceOutput,
    GetContactNoteOutput,
    GetContactOutput,
    GetContactTaskOutput,
    GetContactUnsubscriptionStatusOutput,
    GetConversationOutput,
    GetDuplicateContactOutput,
    GetEmailByIdOutput,
    GetMessageOutput,
    GetMessageTranscriptionOutput,
    GetOpportunityOutput,
    InitiateMessageFileUploadOutput,
    ListAppointmentNotesOutput,
    ListAvailabilitySchedulesOutput,
    ListBlockedSlotsOutput,
    ListBusinessContactsOutput,
    ListCalendarEventsOutput,
    ListCalendarGroupsOutput,
    ListCalendarNotificationsOutput,
    ListCalendarResourcesOutput,
    ListCalendarsOutput,
    ListCampaignsOutput,
    ListContactAppointmentsOutput,
    ListContactNotesOutput,
    ListContactsOutput,
    ListContactTasksOutput,
    ListConversationMessagesOutput,
    ListCustomSubtypesOutput,
    ListEmailTemplatesOutput,
    ListOpportunityLostReasonsOutput,
    ListPipelinesOutput,
    ListScheduledEmailsOutput,
    LiveChatAgentTypingOutput,
    MessageForwardResource,
    MessageMetaResource,
    MessageResource,
    MessageTranscriptSegmentResource,
    OpportunityContactResource,
    OpportunityCustomField,
    OpportunityLostReasonResource,
    OpportunityResource,
    OpportunitySearchMeta,
    PipelineResource,
    RemoveContactFollowersOutput,
    RemoveContactFromCampaignOutput,
    RemoveContactFromEveryCampaignOutput,
    RemoveContactTagsOutput,
    RemoveOpportunityFollowersOutput,
    SearchContactsOutput,
    SearchConversationsOutput,
    SearchOpportunitiesAdvancedOutput,
    SearchOpportunitiesOutput,
    SendMessageOutput,
    SendReviewReplyOutput,
    SetCalendarGroupStatusOutput,
    UpdateAppointmentNoteOutput,
    UpdateAppointmentOutput,
    UpdateAvailabilityScheduleOutput,
    UpdateBlockSlotOutput,
    UpdateCalendarGroupOutput,
    UpdateCalendarNotificationOutput,
    UpdateCalendarOutput,
    UpdateCalendarResourceOutput,
    UpdateContactNoteOutput,
    UpdateContactOutput,
    UpdateContactTaskOutput,
    UpdateConversationOutput,
    UpdateCustomSubtypeOutput,
    UpdateEmailTemplateOutput,
    UpdateMessageStatusOutput,
    UpdateOpportunityOutput,
    UpdateOpportunityStatusOutput,
    UpdateSubscriptionPreferenceOutput,
    UpsertContactOutput,
    UpsertOpportunityOutput,
    ValidateCalendarGroupSlugOutput,
)

__all__ = [
    "add_contact_followers",
    "add_contact_tags",
    "add_contact_to_campaign",
    "add_contact_to_workflow",
    "add_inbound_message",
    "add_message_attachments",
    "add_opportunity_followers",
    "add_outbound_message",
    "attach_schedule_to_calendar",
    "bulk_update_contact_tags",
    "bulk_update_contacts_business",
    "cancel_scheduled_email_message",
    "cancel_scheduled_message",
    "complete_contact_task",
    "complete_message_file_upload",
    "create_appointment",
    "create_appointment_note",
    "create_availability_schedule",
    "create_block_slot",
    "create_calendar",
    "create_calendar_group",
    "create_calendar_notification",
    "create_calendar_resource",
    "create_contact",
    "create_contact_note",
    "create_contact_task",
    "create_conversation",
    "create_custom_subtype",
    "create_email_template",
    "create_opportunity",
    "delete_appointment_note",
    "delete_availability_schedule",
    "delete_calendar",
    "delete_calendar_group",
    "delete_calendar_notification",
    "delete_calendar_resource",
    "delete_contact",
    "delete_contact_from_workflow",
    "delete_contact_note",
    "delete_contact_task",
    "delete_conversation",
    "delete_email_template",
    "delete_event",
    "delete_opportunity",
    "detach_schedule_from_calendar",
    "export_messages",
    "get_appointment",
    "get_availability_schedule",
    "get_calendar",
    "get_calendar_free_slots",
    "get_calendar_notification",
    "get_calendar_resource",
    "get_contact",
    "get_contact_note",
    "get_contact_task",
    "get_contact_unsubscription_status",
    "get_conversation",
    "get_duplicate_contact",
    "get_email_by_id",
    "get_message",
    "get_message_transcription",
    "get_opportunity",
    "initiate_message_file_upload",
    "list_appointment_notes",
    "list_availability_schedules",
    "list_blocked_slots",
    "list_business_contacts",
    "list_calendar_events",
    "list_calendar_groups",
    "list_calendar_notifications",
    "list_calendar_resources",
    "list_calendars",
    "list_campaigns",
    "list_contact_appointments",
    "list_contact_notes",
    "list_contact_tasks",
    "list_contacts",
    "list_conversation_messages",
    "list_custom_subtypes",
    "list_email_templates",
    "list_opportunity_lost_reasons",
    "list_pipelines",
    "list_scheduled_emails",
    "live_chat_agent_typing",
    "remove_contact_followers",
    "remove_contact_from_campaign",
    "remove_contact_from_every_campaign",
    "remove_contact_tags",
    "remove_opportunity_followers",
    "search_contacts",
    "search_conversations",
    "search_opportunities",
    "search_opportunities_advanced",
    "send_message",
    "send_review_reply",
    "set_calendar_group_status",
    "update_appointment",
    "update_appointment_note",
    "update_availability_schedule",
    "update_block_slot",
    "update_calendar",
    "update_calendar_group",
    "update_calendar_notification",
    "update_calendar_resource",
    "update_contact",
    "update_contact_note",
    "update_contact_task",
    "update_conversation",
    "update_custom_subtype",
    "update_email_template",
    "update_message_status",
    "update_opportunity",
    "update_opportunity_status",
    "update_subscription_preference",
    "upsert_contact",
    "upsert_opportunity",
    "validate_calendar_group_slug",
]

_BASE_URL = "https://services.leadconnectorhq.com"
_TIMEOUT = 30.0

# GoHighLevel versions its v2 API per endpoint family through a mandatory
# ``Version`` header, and the families are NOT all on the same date. Each
# operation's OpenAPI definition declares the accepted value as a
# single-entry enum: ``/conversations`` and ``/calendars`` pin
# ``2021-04-15`` while ``/contacts``, ``/opportunities``, ``/emails`` and
# ``/campaigns`` pin ``2021-07-28``. Sending one blanket version — as the
# many clients do — contradicts the spec for the two older
# families, so the header is resolved per request path instead.
_API_VERSION = "2021-07-28"
_LEGACY_VERSION = "2021-04-15"
_LEGACY_VERSION_PREFIXES = ("/conversations", "/calendars")

_MISSING_TOKEN = "GoHighLevel access token is missing. Reconnect the integration."
_MISSING_LOCATION = (
    "GoHighLevel location ID is missing. Set GOHIGHLEVEL_LOCATION_ID on the "
    "credential."
)


# --- Credentials ------------------------------------------------------------


def _api_version(path: str) -> str:
    """Resolve the ``Version`` header value this endpoint family accepts."""
    return (
        _LEGACY_VERSION
        if path.startswith(_LEGACY_VERSION_PREFIXES)
        else _API_VERSION
    )


def _get_auth_headers(
    auth_type: str, auth_data: dict[str, Any], path: str = ""
) -> dict[str, str]:
    """Build the standard v2 header set. Empty dict when the token is absent."""
    token = _as_str(auth_data.get("access_token")) or ""
    if not token:
        return {}
    return {
        "Authorization": f"Bearer {token}",
        "Version": _api_version(path),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _location_id(auth_data: dict[str, Any]) -> str:
    """Resolve the sub-account ID.

    ``inject_into_auth_data`` normalizes ``GOHIGHLEVEL_LOCATION_ID`` to the
    ``location_id`` key. The ``locationId`` fallback covers the raw field
    name GoHighLevel returns in its token-exchange response, in case the
    runtime ever persists it verbatim.
    """
    raw = auth_data.get("location_id") or auth_data.get("locationId")
    return (_as_str(raw) or "").strip()


def _seg(value: Any) -> str:
    """URL-encode one path segment.

    Resource identifiers are chosen by the caller and interpolated straight
    into the request path. httpx resolves dot segments while building the
    URL, so an unencoded ``../../oauth/token`` would silently retarget the
    call at a different endpoint — escaping the action allow-list the
    manifest advertises. Encoding keeps any value a single segment.

    Encoding alone is not enough: ``quote`` treats ``.`` as always-safe, so
    a bare ``.`` or ``..`` survives as a dot segment and httpx resolves it
    while building the URL — ``.`` collapses ``/contacts/{id}`` onto the
    ``/contacts`` collection and ``..`` drops the entity segment entirely.
    An empty identifier collapses the same way. All three become a segment
    that cannot name a record, so the call 404s through the normal error
    envelope instead of addressing something the caller never asked for.
    """
    encoded = quote(str(value), safe="")
    return "-" if encoded in {"", ".", ".."} else encoded


# --- Response coercion ------------------------------------------------------
#
# The envelope invariant: no code path between ``response.json()`` and the
# ``return`` may raise. ``_request`` guards the parse; these guard the types.


def _as_dict(payload: Any) -> dict[str, Any]:
    """A non-object value degrades to empty rather than raising."""
    return payload if isinstance(payload, dict) else {}


def _as_list(payload: Any) -> list[Any]:
    """A non-array value degrades to empty rather than raising."""
    return payload if isinstance(payload, list) else []


def _as_str(value: Any) -> str | None:
    if value is None or isinstance(value, (dict, list, bool)):
        return None
    return value if isinstance(value, str) else str(value)


def _as_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _as_int(value: Any) -> int | None:
    """Coerce a JSON number to ``int``.

    GoHighLevel declares every numeric field as ``number`` and never as
    ``integer``, so counters, page markers and epoch timestamps can arrive
    as ``7.0`` just as easily as ``7``. An integral float is accepted; a
    genuinely fractional value degrades to ``None`` rather than being
    silently truncated.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _as_str_list(value: Any) -> list[str]:
    return [item for item in _as_list(value) if isinstance(item, str)]


def _as_dict_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in _as_list(value) if isinstance(item, dict)]


# --- Request ----------------------------------------------------------------


def _clean_params(params: dict[str, Any] | None) -> dict[str, Any]:
    """Drop unset query params; GoHighLevel 400s on empty-string filters."""
    if not params:
        return {}
    return {k: v for k, v in params.items() if v is not None and v != ""}


def _clean_body(body: dict[str, Any] | None) -> dict[str, Any]:
    """Drop unset body fields so a partial update never blanks a value."""
    if not body:
        return {}
    return {k: v for k, v in body.items() if v is not None}


def _error_text(response: httpx.Response) -> str:
    """Turn a non-2xx into one readable sentence.

    GoHighLevel returns ``{"message": "..."}`` or ``{"message": [...]}`` and
    echoes a ``traceId`` that support asks for, so both are surfaced.
    """
    detail = ""
    try:
        payload = response.json()
    except (ValueError, httpx.DecodingError):
        payload = None
    if isinstance(payload, dict):
        message = payload.get("message")
        if isinstance(message, list):
            detail = ", ".join(str(item) for item in message)
        elif message is not None:
            detail = str(message)
        trace_id = _as_str(payload.get("traceId"))
        if trace_id:
            detail = f"{detail} (traceId: {trace_id})" if detail else f"traceId: {trace_id}"
    if not detail:
        detail = (response.text or "").strip()[:300]
    return (
        f"GoHighLevel API error {response.status_code}: {detail}"
        if detail
        else f"GoHighLevel API error {response.status_code}"
    )


async def _request(
    auth_type: str,
    auth_data: dict[str, Any],
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | list[Any] | None = None,
    send_body: bool = False,
    keep_nulls: bool = False,
) -> tuple[Any, str | None]:
    """Perform one v2 call.

    Returns ``(payload, None)`` on success or ``(None, error)`` on any
    failure — transport, non-2xx, or an unparseable body. Never raises, so
    every caller can build its success model unconditionally after the
    ``error is not None`` early return.

    ``send_body`` forces a JSON body even when it cleans down to ``{}``
    (some endpoints require a body object to be present at all).

    ``json_body`` may also be a list: a couple of endpoints — notably
    ``POST /calendars/{calendarId}/notifications`` — declare a top-level
    JSON *array* as their request body. Lists are passed through as-is
    (there are no unset keys to strip) and always sent, empty or not.

    ``keep_nulls`` disables the unset-key stripping for endpoints where an
    explicit ``null`` is *meaningful* rather than absent — GoHighLevel has a
    few fields that are both required and nullable, where omitting the key
    and sending ``null`` mean different things.
    """
    headers = _get_auth_headers(auth_type, auth_data, path)
    if not headers:
        return None, _MISSING_TOKEN

    is_array_body = isinstance(json_body, list)
    if isinstance(json_body, list) or keep_nulls:
        body: Any = json_body
    else:
        body = _clean_body(json_body)
    kwargs: dict[str, Any] = {
        "headers": headers,
        "params": _clean_params(params),
    }
    if send_body or is_array_body or body:
        kwargs["json"] = body

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.request(method, f"{_BASE_URL}{path}", **kwargs)
    except httpx.HTTPError as exc:
        return None, f"GoHighLevel request failed: {exc}"

    if response.status_code >= 400:
        return None, _error_text(response)

    if not response.content:
        return {}, None
    try:
        return response.json(), None
    except (ValueError, httpx.DecodingError):
        return None, "GoHighLevel returned a non-JSON response body."


def _parse_contact_custom_field(raw: Any) -> ContactCustomField:
    """Core CRM parse helper.

    Upstream keys are camelCase; the output models use snake_case. Every
    mapping lives in a ``_parse_*`` helper so that no code path between
    ``_request`` returning and the ``return`` statement can raise.
    """
    data = _as_dict(raw)
    return ContactCustomField(
        id=_as_str(data.get("id")),
        value=_as_str(data.get("value")),
    )


def _parse_contact_dnd_setting(raw: Any) -> ContactDndSetting:
    data = _as_dict(raw)
    return ContactDndSetting(
        status=_as_str(data.get("status")),
        message=_as_str(data.get("message")),
        code=_as_str(data.get("code")),
    )


def _parse_contact_dnd_setting_opt(raw: Any) -> ContactDndSetting | None:
    return _parse_contact_dnd_setting(raw) if isinstance(raw, dict) else None


def _parse_contact_dnd_settings(raw: Any) -> ContactDndSettings:
    data = _as_dict(raw)
    return ContactDndSettings(
        call=_parse_contact_dnd_setting_opt(data.get("Call")),
        email=_parse_contact_dnd_setting_opt(data.get("Email")),
        sms=_parse_contact_dnd_setting_opt(data.get("SMS")),
        whatsapp=_parse_contact_dnd_setting_opt(data.get("WhatsApp")),
        gmb=_parse_contact_dnd_setting_opt(data.get("GMB")),
        fb=_parse_contact_dnd_setting_opt(data.get("FB")),
    )


def _parse_contact_dnd_settings_opt(raw: Any) -> ContactDndSettings | None:
    return _parse_contact_dnd_settings(raw) if isinstance(raw, dict) else None


def _parse_contact_attribution(raw: Any) -> ContactAttribution:
    data = _as_dict(raw)
    return ContactAttribution(
        url=_as_str(data.get("url")),
        campaign=_as_str(data.get("campaign")),
        campaign_id=_as_str(data.get("campaignId")),
        utm_source=_as_str(data.get("utmSource")),
        utm_medium=_as_str(data.get("utmMedium")),
        utm_content=_as_str(data.get("utmContent")),
        referrer=_as_str(data.get("referrer")),
        fbclid=_as_str(data.get("fbclid")),
        gclid=_as_str(data.get("gclid")),
        msclikid=_as_str(data.get("msclikid")),
        dclid=_as_str(data.get("dclid")),
        fbc=_as_str(data.get("fbc")),
        fbp=_as_str(data.get("fbp")),
        fb_event_id=_as_str(data.get("fbEventId")),
        user_agent=_as_str(data.get("userAgent")),
        ip=_as_str(data.get("ip")),
        medium=_as_str(data.get("medium")),
        medium_id=_as_str(data.get("mediumId")),
    )


def _parse_contact_attribution_opt(raw: Any) -> ContactAttribution | None:
    return _parse_contact_attribution(raw) if isinstance(raw, dict) else None


def _parse_contact(raw: Any) -> ContactResource:
    data = _as_dict(raw)
    custom_fields = _as_dict_list(data.get("customFields"))
    attributions = _as_dict_list(data.get("attributions"))
    return ContactResource(
        id=_as_str(data.get("id")),
        name=_as_str(data.get("name")),
        first_name=_as_str(data.get("firstName")),
        last_name=_as_str(data.get("lastName")),
        email=_as_str(data.get("email")),
        phone=_as_str(data.get("phone")),
        company_name=_as_str(data.get("companyName")),
        location_id=_as_str(data.get("locationId")),
        timezone=_as_str(data.get("timezone")),
        source=_as_str(data.get("source")),
        type=_as_str(data.get("type")),
        assigned_to=_as_str(data.get("assignedTo")),
        address1=_as_str(data.get("address1")),
        city=_as_str(data.get("city")),
        state=_as_str(data.get("state")),
        country=_as_str(data.get("country")),
        postal_code=_as_str(data.get("postalCode")),
        website=_as_str(data.get("website")),
        tags=_as_str_list(data.get("tags")),
        date_of_birth=_as_str(data.get("dateOfBirth")),
        date_added=_as_str(data.get("dateAdded")),
        date_updated=_as_str(data.get("dateUpdated")),
        last_activity=_as_str(data.get("lastActivity")),
        dnd=_as_bool(data.get("dnd")),
        dnd_settings=_parse_contact_dnd_settings_opt(data.get("dndSettings")),
        business_id=_as_str(data.get("businessId")),
        custom_fields=[_parse_contact_custom_field(item) for item in custom_fields],
        followers=_as_str_list(data.get("followers")),
        deleted=_as_bool(data.get("deleted")),
        attribution_source=_parse_contact_attribution_opt(data.get("attributionSource")),
        last_attribution_source=_parse_contact_attribution_opt(
            data.get("lastAttributionSource")
        ),
        attributions=[_parse_contact_attribution(item) for item in attributions],
    )


def _parse_contact_opt(raw: Any) -> ContactResource | None:
    return _parse_contact(raw) if isinstance(raw, dict) else None


def _parse_contact_note(raw: Any) -> ContactNoteResource:
    data = _as_dict(raw)
    return ContactNoteResource(
        id=_as_str(data.get("id")),
        body=_as_str(data.get("body")),
        title=_as_str(data.get("title")),
        color=_as_str(data.get("color")),
        pinned=_as_bool(data.get("pinned")),
        user_id=_as_str(data.get("userId")),
        contact_id=_as_str(data.get("contactId")),
        date_added=_as_str(data.get("dateAdded")),
    )


def _parse_contact_note_opt(raw: Any) -> ContactNoteResource | None:
    return _parse_contact_note(raw) if isinstance(raw, dict) else None


def _parse_contact_task(raw: Any) -> ContactTaskResource:
    data = _as_dict(raw)
    return ContactTaskResource(
        id=_as_str(data.get("id")),
        title=_as_str(data.get("title")),
        body=_as_str(data.get("body")),
        assigned_to=_as_str(data.get("assignedTo")),
        due_date=_as_str(data.get("dueDate")),
        completed=_as_bool(data.get("completed")),
        contact_id=_as_str(data.get("contactId")),
    )


def _parse_contact_task_opt(raw: Any) -> ContactTaskResource | None:
    return _parse_contact_task(raw) if isinstance(raw, dict) else None


def _parse_contact_appointment(raw: Any) -> ContactAppointmentResource:
    data = _as_dict(raw)
    return ContactAppointmentResource(
        id=_as_str(data.get("id")),
        calendar_id=_as_str(data.get("calendarId")),
        status=_as_str(data.get("status")),
        title=_as_str(data.get("title")),
        assigned_user_id=_as_str(data.get("assignedUserId")),
        notes=_as_str(data.get("notes")),
        start_time=_as_str(data.get("startTime")),
        end_time=_as_str(data.get("endTime")),
        address=_as_str(data.get("address")),
        location_id=_as_str(data.get("locationId")),
        contact_id=_as_str(data.get("contactId")),
        group_id=_as_str(data.get("groupId")),
        appointment_status=_as_str(data.get("appointmentStatus")),
        users=_as_str_list(data.get("users")),
        assigned_resources=_as_str_list(data.get("assignedResources")),
        date_added=_as_str(data.get("dateAdded")),
        date_updated=_as_str(data.get("dateUpdated")),
    )


def _parse_opportunity_custom_field(raw: Any) -> OpportunityCustomField:
    data = _as_dict(raw)
    return OpportunityCustomField(
        id=_as_str(data.get("id")),
        field_value=data.get("fieldValue"),
    )


def _parse_opportunity_contact(raw: Any) -> OpportunityContactResource:
    data = _as_dict(raw)
    return OpportunityContactResource(
        id=_as_str(data.get("id")),
        name=_as_str(data.get("name")),
        company_name=_as_str(data.get("companyName")),
        email=_as_str(data.get("email")),
        phone=_as_str(data.get("phone")),
        tags=_as_str_list(data.get("tags")),
    )


def _parse_opportunity_contact_opt(raw: Any) -> OpportunityContactResource | None:
    return _parse_opportunity_contact(raw) if isinstance(raw, dict) else None


def _parse_opportunity(raw: Any) -> OpportunityResource:
    data = _as_dict(raw)
    custom_fields = _as_dict_list(data.get("customFields"))
    return OpportunityResource(
        id=_as_str(data.get("id")),
        name=_as_str(data.get("name")),
        monetary_value=_as_float(data.get("monetaryValue")),
        pipeline_id=_as_str(data.get("pipelineId")),
        pipeline_stage_id=_as_str(data.get("pipelineStageId")),
        assigned_to=_as_str(data.get("assignedTo")),
        status=_as_str(data.get("status")),
        source=_as_str(data.get("source")),
        contact_id=_as_str(data.get("contactId")),
        location_id=_as_str(data.get("locationId")),
        lost_reason_id=_as_str(data.get("lostReasonId")),
        external_object_id=_as_str(data.get("externalObjectId")),
        index_version=_as_str(data.get("indexVersion")),
        last_status_change_at=_as_str(data.get("lastStatusChangeAt")),
        last_stage_change_at=_as_str(data.get("lastStageChangeAt")),
        last_action_date=_as_str(data.get("lastActionDate")),
        created_at=_as_str(data.get("createdAt")),
        updated_at=_as_str(data.get("updatedAt")),
        contact=_parse_opportunity_contact_opt(data.get("contact")),
        custom_fields=[_parse_opportunity_custom_field(item) for item in custom_fields],
        notes=_as_list(data.get("notes")),
        tasks=_as_list(data.get("tasks")),
        calendar_events=_as_list(data.get("calendarEvents")),
        followers=_as_list(data.get("followers")),
    )


def _parse_opportunity_opt(raw: Any) -> OpportunityResource | None:
    return _parse_opportunity(raw) if isinstance(raw, dict) else None


def _parse_opportunity_search_meta(raw: Any) -> OpportunitySearchMeta:
    data = _as_dict(raw)
    return OpportunitySearchMeta(
        total=_as_int(data.get("total")),
        next_page_url=_as_str(data.get("nextPageUrl")),
        start_after_id=_as_str(data.get("startAfterId")),
        start_after=_as_int(data.get("startAfter")),
        current_page=_as_int(data.get("currentPage")),
        next_page=_as_int(data.get("nextPage")),
        prev_page=_as_int(data.get("prevPage")),
    )


def _parse_opportunity_search_meta_opt(raw: Any) -> OpportunitySearchMeta | None:
    return _parse_opportunity_search_meta(raw) if isinstance(raw, dict) else None


def _parse_pipeline(raw: Any) -> PipelineResource:
    data = _as_dict(raw)
    return PipelineResource(
        id=_as_str(data.get("id")),
        name=_as_str(data.get("name")),
        location_id=_as_str(data.get("locationId")),
        stages=_as_list(data.get("stages")),
        show_in_funnel=_as_bool(data.get("showInFunnel")),
        show_in_pie_chart=_as_bool(data.get("showInPieChart")),
        color_render_mode=_as_str(data.get("colorRenderMode")),
    )


def _parse_opportunity_lost_reason(raw: Any) -> OpportunityLostReasonResource:
    data = _as_dict(raw)
    return OpportunityLostReasonResource(
        id=_as_str(data.get("id")),
        name=_as_str(data.get("name")),
        location_id=_as_str(data.get("locationId")),
        created_at=_as_str(data.get("createdAt")),
        updated_at=_as_str(data.get("updatedAt")),
    )


# --- Contacts ---------------------------------------------------------------


class CreateContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    first_name: str | None = Field(default=None, description="The contact's first name")
    last_name: str | None = Field(default=None, description="The contact's last name")
    name: str | None = Field(default=None, description="The contact's full name")
    email: str | None = Field(default=None, description="The contact's email address")
    phone: str | None = Field(
        default=None, description="The contact's phone number in E.164 format"
    )
    gender: str | None = Field(default=None, description="The contact's gender")
    address1: str | None = Field(default=None, description="The contact's street address")
    city: str | None = Field(default=None, description="The contact's city")
    state: str | None = Field(default=None, description="The contact's state or region")
    postal_code: str | None = Field(default=None, description="The contact's postal/ZIP code")
    country: str | None = Field(
        default=None, description="The contact's country as a two-letter ISO code"
    )
    website: str | None = Field(default=None, description="The contact's website URL")
    timezone: str | None = Field(default=None, description="The contact's timezone")
    company_name: str | None = Field(default=None, description="The contact's company name")
    source: str | None = Field(default=None, description="The source attributed to the contact")
    date_of_birth: str | None = Field(
        default=None,
        description="Birth date of the contact. Supported formats include YYYY-MM-DD",
    )
    assigned_to: str | None = Field(
        default=None, description="Unique identifier of the user the contact is assigned to"
    )
    dnd: bool | None = Field(
        default=None,
        description="When true, enables Do Not Disturb across all channels for this contact",
    )
    dnd_settings: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Per-channel Do Not Disturb settings (keys: Call, Email, SMS, WhatsApp, "
            "GMB, FB), each an object with status/message/code"
        ),
    )
    inbound_dnd_settings: dict[str, Any] | None = Field(
        default=None, description="Inbound Do Not Disturb settings for the contact"
    )
    tags: list[str] | None = Field(
        default=None, description="Tags to associate with the contact"
    )
    custom_fields: list[dict[str, Any]] | None = Field(
        default=None,
        description="Custom field values; each item is an object with an id (or key) and a value",
    )


@tool(args_schema=CreateContactInput)
@serialize_pydantic_return
async def create_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    first_name: str | None = None,
    last_name: str | None = None,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    gender: str | None = None,
    address1: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country: str | None = None,
    website: str | None = None,
    timezone: str | None = None,
    company_name: str | None = None,
    source: str | None = None,
    date_of_birth: str | None = None,
    assigned_to: str | None = None,
    dnd: bool | None = None,
    dnd_settings: dict[str, Any] | None = None,
    inbound_dnd_settings: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    custom_fields: list[dict[str, Any]] | None = None,
) -> CreateContactOutput:
    """Create a new contact in the connected GoHighLevel sub-account."""
    location_id = _location_id(auth_data)
    if not location_id:
        return CreateContactOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "locationId": location_id,
        "firstName": first_name,
        "lastName": last_name,
        "name": name,
        "email": email,
        "phone": phone,
        "gender": gender,
        "address1": address1,
        "city": city,
        "state": state,
        "postalCode": postal_code,
        "country": country,
        "website": website,
        "timezone": timezone,
        "companyName": company_name,
        "source": source,
        "dateOfBirth": date_of_birth,
        "assignedTo": assigned_to,
        "dnd": dnd,
        "dndSettings": dnd_settings,
        "inboundDndSettings": inbound_dnd_settings,
        "tags": tags,
        "customFields": custom_fields,
    }
    payload, error = await _request(auth_type, auth_data, "POST", "/contacts/", json_body=body)
    if error is not None:
        return CreateContactOutput(success=False, error=error)
    return CreateContactOutput(
        success=True,
        contact=_parse_contact_opt(_as_dict(payload).get("contact")),
    )


class ListContactsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    query: str | None = Field(
        default=None, description="Search text matched against name, email or phone"
    )
    limit: int | None = Field(
        default=None, description="Maximum number of contacts to return"
    )
    start_after: int | None = Field(
        default=None,
        description="Timestamp cursor for pagination; use the value from a previous response",
    )
    start_after_id: str | None = Field(
        default=None,
        description="Contact id cursor for pagination; use the value from a previous response",
    )


@tool(args_schema=ListContactsInput)
@serialize_pydantic_return
async def list_contacts(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str | None = None,
    limit: int | None = None,
    start_after: int | None = None,
    start_after_id: str | None = None,
) -> ListContactsOutput:
    """List contacts in the connected GoHighLevel sub-account."""
    location_id = _location_id(auth_data)
    if not location_id:
        return ListContactsOutput(success=False, error=_MISSING_LOCATION)
    params: dict[str, Any] = {
        "locationId": location_id,
        "query": query,
        "limit": limit,
        "startAfter": start_after,
        "startAfterId": start_after_id,
    }
    payload, error = await _request(auth_type, auth_data, "GET", "/contacts/", params=params)
    if error is not None:
        return ListContactsOutput(success=False, error=error)
    body = _as_dict(payload)
    return ListContactsOutput(
        success=True,
        contacts=[_parse_contact(item) for item in _as_dict_list(body.get("contacts"))],
        count=_as_int(body.get("count")),
    )


class BulkUpdateContactsBusinessInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_ids: list[str] = Field(
        description="Unique identifiers of the contacts to add to or remove from the business"
    )
    business_id: str | None = Field(
        default=None,
        description=(
            "Unique identifier of the business to associate the contacts with. "
            "Omit to detach the contacts from their business"
        ),
    )


@tool(args_schema=BulkUpdateContactsBusinessInput)
@serialize_pydantic_return
async def bulk_update_contacts_business(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_ids: list[str],
    business_id: str | None = None,
) -> BulkUpdateContactsBusinessOutput:
    """Add or remove many contacts from a business in one bulk call."""
    location_id = _location_id(auth_data)
    if not location_id:
        return BulkUpdateContactsBusinessOutput(success=False, error=_MISSING_LOCATION)
    # `businessId` is declared both required and nullable: an explicit null
    # is how contacts are detached from a business, and that is NOT the same
    # as omitting the key. `keep_nulls` stops the usual unset-key stripping
    # from turning a removal into a request that is missing a required field.
    body: dict[str, Any] = {
        "locationId": location_id,
        "ids": contact_ids,
        "businessId": business_id,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/contacts/bulk/business",
        json_body=body,
        keep_nulls=True,
    )
    if error is not None:
        return BulkUpdateContactsBusinessOutput(success=False, error=error)
    data = _as_dict(payload)
    return BulkUpdateContactsBusinessOutput(
        success=True,
        succeeded=_as_bool(data.get("success")),
        ids=_as_str_list(data.get("ids")),
    )


class BulkUpdateContactTagsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    operation: str = Field(
        description="The bulk tag operation to perform on the contacts: 'add' or 'remove'"
    )
    contact_ids: list[str] = Field(description="List of contact ids to be processed")
    tags: list[str] = Field(description="List of tags to be added or removed")
    remove_all_tags: bool | None = Field(
        default=None,
        description=(
            "When true, removes every tag from the contacts. Can only be used with "
            "the 'remove' operation"
        ),
    )


@tool(args_schema=BulkUpdateContactTagsInput)
@serialize_pydantic_return
async def bulk_update_contact_tags(
    auth_type: str,
    auth_data: dict[str, Any],
    operation: str,
    contact_ids: list[str],
    tags: list[str],
    remove_all_tags: bool | None = None,
) -> BulkUpdateContactTagsOutput:
    """Add or remove tags across many contacts at once."""
    location_id = _location_id(auth_data)
    if not location_id:
        return BulkUpdateContactTagsOutput(success=False, error=_MISSING_LOCATION)
    # TODO (unverified): the `{type}` path segment is not declared in the
    # OpenAPI `parameters` block; 'add' / 'remove' come from the vendor's
    # published action catalogue.
    #
    # It is still interpolated straight into the request path, so it is
    # validated against the closed set rather than trusted — an unchecked
    # value would let a caller reach a different endpoint entirely.
    resolved_operation = operation.strip().lower()
    if resolved_operation not in ("add", "remove"):
        return BulkUpdateContactTagsOutput(
            success=False,
            error="operation must be either 'add' or 'remove'.",
        )
    body: dict[str, Any] = {
        "locationId": location_id,
        "contacts": contact_ids,
        "tags": tags,
        "removeAllTags": remove_all_tags,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        f"/contacts/bulk/tags/update/{_seg(resolved_operation)}",
        json_body=body,
    )
    if error is not None:
        return BulkUpdateContactTagsOutput(success=False, error=error)
    data = _as_dict(payload)
    return BulkUpdateContactTagsOutput(
        success=True,
        succeeded=_as_bool(data.get("succeded")),
        error_count=_as_int(data.get("errorCount")),
        responses=_as_list(data.get("responses")),
    )


class ListBusinessContactsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    business_id: str = Field(
        description="Unique identifier of the business whose contacts are to be retrieved"
    )
    query: str | None = Field(
        default=None, description="A search query to filter the returned contacts"
    )
    limit: int | None = Field(
        default=None, description="Maximum number of contacts to return in a single page"
    )
    skip: int | None = Field(
        default=None, description="Number of contacts to skip, used for pagination"
    )


@tool(args_schema=ListBusinessContactsInput)
@serialize_pydantic_return
async def list_business_contacts(
    auth_type: str,
    auth_data: dict[str, Any],
    business_id: str,
    query: str | None = None,
    limit: int | None = None,
    skip: int | None = None,
) -> ListBusinessContactsOutput:
    """List the contacts that belong to a specific business."""
    location_id = _location_id(auth_data)
    if not location_id:
        return ListBusinessContactsOutput(success=False, error=_MISSING_LOCATION)
    params: dict[str, Any] = {
        "locationId": location_id,
        "query": query,
        "limit": limit,
        "skip": skip,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "GET",
        f"/contacts/business/{_seg(business_id)}",
        params=params,
    )
    if error is not None:
        return ListBusinessContactsOutput(success=False, error=error)
    body = _as_dict(payload)
    return ListBusinessContactsOutput(
        success=True,
        contacts=[_parse_contact(item) for item in _as_dict_list(body.get("contacts"))],
        count=_as_int(body.get("count")),
    )


class SearchContactsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    page_limit: int = Field(
        default=20, description="Maximum number of contacts to return per page"
    )
    page: int | None = Field(default=None, description="The page number of results to retrieve")
    filters: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Filter objects used to narrow the search; each describes a field, "
            "operator and value to match"
        ),
    )
    sort: list[dict[str, Any]] | None = Field(
        default=None,
        description="Sort objects defining result ordering; each has a field and direction",
    )
    search_after: list[Any] | None = Field(
        default=None,
        description=(
            "Cursor values for deep pagination; pass the searchAfter value of the "
            "last contact of the previous page"
        ),
    )


@tool(args_schema=SearchContactsInput)
@serialize_pydantic_return
async def search_contacts(
    auth_type: str,
    auth_data: dict[str, Any],
    page_limit: int = 20,
    page: int | None = None,
    filters: list[dict[str, Any]] | None = None,
    sort: list[dict[str, Any]] | None = None,
    search_after: list[Any] | None = None,
) -> SearchContactsOutput:
    """Search contacts using advanced filters, sorting and deep pagination."""
    location_id = _location_id(auth_data)
    if not location_id:
        return SearchContactsOutput(success=False, error=_MISSING_LOCATION)
    # TODO (unverified): the request body (`SearchBodyV2DTO`) and the 200
    # response carry no schema in the published contacts API spec. Field
    # names come from the vendor's published action catalogue; the response
    # envelope (`contacts`, `total`) follows the GET /contacts/ sibling,
    # which is what existing clients read.
    body: dict[str, Any] = {
        "locationId": location_id,
        "pageLimit": page_limit,
        "page": page,
        "filters": filters,
        "sort": sort,
        "searchAfter": search_after,
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/contacts/search", json_body=body
    )
    if error is not None:
        return SearchContactsOutput(success=False, error=error)
    data = _as_dict(payload)
    return SearchContactsOutput(
        success=True,
        contacts=[_parse_contact(item) for item in _as_dict_list(data.get("contacts"))],
        total=_as_int(data.get("total")),
    )


class GetDuplicateContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    email: str | None = Field(
        default=None, description="Email address to search for a duplicate contact"
    )
    number: str | None = Field(
        default=None, description="Phone number to search for a duplicate contact"
    )


@tool(args_schema=GetDuplicateContactInput)
@serialize_pydantic_return
async def get_duplicate_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    email: str | None = None,
    number: str | None = None,
) -> GetDuplicateContactOutput:
    """Find an existing duplicate contact by email or phone before creating one."""
    location_id = _location_id(auth_data)
    if not location_id:
        return GetDuplicateContactOutput(success=False, error=_MISSING_LOCATION)
    params: dict[str, Any] = {
        "locationId": location_id,
        "email": email,
        "number": number,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/contacts/search/duplicate", params=params
    )
    if error is not None:
        return GetDuplicateContactOutput(success=False, error=error)
    # TODO (unverified): the 200 response of GET /contacts/search/duplicate
    # carries no schema in the published contacts API spec; the `contact` envelope mirrors
    # GET /contacts/{contactId}.
    return GetDuplicateContactOutput(
        success=True,
        contact=_parse_contact_opt(_as_dict(payload).get("contact")),
    )


class UpsertContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    first_name: str | None = Field(default=None, description="The contact's first name")
    last_name: str | None = Field(default=None, description="The contact's last name")
    name: str | None = Field(default=None, description="The contact's full name")
    email: str | None = Field(default=None, description="The contact's email address")
    phone: str | None = Field(
        default=None, description="The contact's phone number in E.164 format"
    )
    gender: str | None = Field(default=None, description="The contact's gender")
    address1: str | None = Field(default=None, description="The contact's street address")
    city: str | None = Field(default=None, description="The contact's city")
    state: str | None = Field(default=None, description="The contact's state or region")
    postal_code: str | None = Field(default=None, description="The contact's postal/ZIP code")
    country: str | None = Field(
        default=None, description="The contact's country as a two-letter ISO code"
    )
    website: str | None = Field(default=None, description="The contact's website URL")
    timezone: str | None = Field(default=None, description="The contact's timezone")
    company_name: str | None = Field(default=None, description="The contact's company name")
    source: str | None = Field(default=None, description="The source attributed to the contact")
    date_of_birth: str | None = Field(
        default=None,
        description="Birth date of the contact. Supported formats include YYYY-MM-DD",
    )
    assigned_to: str | None = Field(
        default=None, description="Unique identifier of the user the contact is assigned to"
    )
    dnd: bool | None = Field(
        default=None,
        description="When true, enables Do Not Disturb across all channels for this contact",
    )
    dnd_settings: dict[str, Any] | None = Field(
        default=None, description="Per-channel Do Not Disturb settings for the contact"
    )
    inbound_dnd_settings: dict[str, Any] | None = Field(
        default=None, description="Inbound Do Not Disturb settings for the contact"
    )
    tags: list[str] | None = Field(
        default=None,
        description="Tags for the contact; this overwrites all tags currently on the contact",
    )
    custom_fields: list[dict[str, Any]] | None = Field(
        default=None,
        description="Custom field values; each item is an object with an id (or key) and a value",
    )
    create_new_if_duplicate_allowed: bool | None = Field(
        default=None,
        description=(
            "When true and the sub-account allows duplicates, always create a new "
            "contact instead of updating the duplicate"
        ),
    )


@tool(args_schema=UpsertContactInput)
@serialize_pydantic_return
async def upsert_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    first_name: str | None = None,
    last_name: str | None = None,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    gender: str | None = None,
    address1: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country: str | None = None,
    website: str | None = None,
    timezone: str | None = None,
    company_name: str | None = None,
    source: str | None = None,
    date_of_birth: str | None = None,
    assigned_to: str | None = None,
    dnd: bool | None = None,
    dnd_settings: dict[str, Any] | None = None,
    inbound_dnd_settings: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    custom_fields: list[dict[str, Any]] | None = None,
    create_new_if_duplicate_allowed: bool | None = None,
) -> UpsertContactOutput:
    """Create a contact, or update the matching duplicate if one already exists."""
    location_id = _location_id(auth_data)
    if not location_id:
        return UpsertContactOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "locationId": location_id,
        "firstName": first_name,
        "lastName": last_name,
        "name": name,
        "email": email,
        "phone": phone,
        "gender": gender,
        "address1": address1,
        "city": city,
        "state": state,
        "postalCode": postal_code,
        "country": country,
        "website": website,
        "timezone": timezone,
        "companyName": company_name,
        "source": source,
        "dateOfBirth": date_of_birth,
        "assignedTo": assigned_to,
        "dnd": dnd,
        "dndSettings": dnd_settings,
        "inboundDndSettings": inbound_dnd_settings,
        "tags": tags,
        "customFields": custom_fields,
        "createNewIfDuplicateAllowed": create_new_if_duplicate_allowed,
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/contacts/upsert", json_body=body
    )
    if error is not None:
        return UpsertContactOutput(success=False, error=error)
    data = _as_dict(payload)
    return UpsertContactOutput(
        success=True,
        contact=_parse_contact_opt(data.get("contact")),
        new=_as_bool(data.get("new")),
        trace_id=_as_str(data.get("traceId")),
    )


class GetContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact to retrieve")


@tool(args_schema=GetContactInput)
@serialize_pydantic_return
async def get_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
) -> GetContactOutput:
    """Retrieve the full details of a single contact by its id."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/contacts/{_seg(contact_id)}"
    )
    if error is not None:
        return GetContactOutput(success=False, error=error)
    return GetContactOutput(
        success=True,
        contact=_parse_contact_opt(_as_dict(payload).get("contact")),
    )


class UpdateContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact to update")
    first_name: str | None = Field(default=None, description="Updated first name")
    last_name: str | None = Field(default=None, description="Updated last name")
    name: str | None = Field(default=None, description="Updated full name")
    email: str | None = Field(default=None, description="Updated email address")
    phone: str | None = Field(default=None, description="Updated phone number in E.164 format")
    address1: str | None = Field(default=None, description="Updated street address")
    city: str | None = Field(default=None, description="Updated city")
    state: str | None = Field(default=None, description="Updated state or region")
    postal_code: str | None = Field(default=None, description="Updated postal/ZIP code")
    country: str | None = Field(default=None, description="Updated two-letter ISO country code")
    website: str | None = Field(default=None, description="Updated website URL")
    timezone: str | None = Field(default=None, description="Updated timezone")
    source: str | None = Field(default=None, description="Updated lead source")
    date_of_birth: str | None = Field(
        default=None, description="Updated birth date, e.g. YYYY-MM-DD"
    )
    assigned_to: str | None = Field(
        default=None, description="Unique identifier of the user the contact is assigned to"
    )
    dnd: bool | None = Field(default=None, description="Updated do-not-disturb state")
    dnd_settings: dict[str, Any] | None = Field(
        default=None, description="Per-channel Do Not Disturb settings for the contact"
    )
    inbound_dnd_settings: dict[str, Any] | None = Field(
        default=None, description="Inbound Do Not Disturb settings for the contact"
    )
    tags: list[str] | None = Field(
        default=None,
        description=(
            "Tags for the contact; this overwrites all current tags. Prefer "
            "add_contact_tags / remove_contact_tags for incremental changes"
        ),
    )
    custom_fields: list[dict[str, Any]] | None = Field(
        default=None,
        description="Custom field values; each item is an object with an id (or key) and a value",
    )


@tool(args_schema=UpdateContactInput)
@serialize_pydantic_return
async def update_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    first_name: str | None = None,
    last_name: str | None = None,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    address1: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country: str | None = None,
    website: str | None = None,
    timezone: str | None = None,
    source: str | None = None,
    date_of_birth: str | None = None,
    assigned_to: str | None = None,
    dnd: bool | None = None,
    dnd_settings: dict[str, Any] | None = None,
    inbound_dnd_settings: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    custom_fields: list[dict[str, Any]] | None = None,
) -> UpdateContactOutput:
    """Update the fields of an existing contact."""
    body: dict[str, Any] = {
        "firstName": first_name,
        "lastName": last_name,
        "name": name,
        "email": email,
        "phone": phone,
        "address1": address1,
        "city": city,
        "state": state,
        "postalCode": postal_code,
        "country": country,
        "website": website,
        "timezone": timezone,
        "source": source,
        "dateOfBirth": date_of_birth,
        "assignedTo": assigned_to,
        "dnd": dnd,
        "dndSettings": dnd_settings,
        "inboundDndSettings": inbound_dnd_settings,
        "tags": tags,
        "customFields": custom_fields,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/contacts/{_seg(contact_id)}",
        json_body=body,
        send_body=True,
    )
    if error is not None:
        return UpdateContactOutput(success=False, error=error)
    data = _as_dict(payload)
    return UpdateContactOutput(
        success=True,
        succeeded=_as_bool(data.get("succeded")),
        contact=_parse_contact_opt(data.get("contact")),
    )


class DeleteContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact to delete")


@tool(args_schema=DeleteContactInput)
@serialize_pydantic_return
async def delete_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
) -> DeleteContactOutput:
    """Permanently delete a contact from the sub-account."""
    payload, error = await _request(
        auth_type, auth_data, "DELETE", f"/contacts/{_seg(contact_id)}"
    )
    if error is not None:
        return DeleteContactOutput(success=False, error=error)
    return DeleteContactOutput(
        success=True,
        succeeded=_as_bool(_as_dict(payload).get("succeded")),
    )


class ListContactAppointmentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(
        description="Unique identifier of the contact whose appointments to retrieve"
    )


@tool(args_schema=ListContactAppointmentsInput)
@serialize_pydantic_return
async def list_contact_appointments(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
) -> ListContactAppointmentsOutput:
    """List every calendar appointment booked for a contact."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/contacts/{_seg(contact_id)}/appointments"
    )
    if error is not None:
        return ListContactAppointmentsOutput(success=False, error=error)
    events = _as_dict_list(_as_dict(payload).get("events"))
    return ListContactAppointmentsOutput(
        success=True,
        events=[_parse_contact_appointment(item) for item in events],
    )


class RemoveContactFromEveryCampaignInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(
        description="Unique identifier of the contact to remove from all campaigns"
    )


@tool(args_schema=RemoveContactFromEveryCampaignInput)
@serialize_pydantic_return
async def remove_contact_from_every_campaign(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
) -> RemoveContactFromEveryCampaignOutput:
    """Unenroll a contact from every campaign it is currently enrolled in."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "DELETE",
        f"/contacts/{_seg(contact_id)}/campaigns/removeAll",
    )
    if error is not None:
        return RemoveContactFromEveryCampaignOutput(success=False, error=error)
    return RemoveContactFromEveryCampaignOutput(
        success=True,
        succeeded=_as_bool(_as_dict(payload).get("succeded")),
    )


class AddContactToCampaignInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact to enroll")
    campaign_id: str = Field(description="Unique identifier of the campaign to enroll into")


@tool(args_schema=AddContactToCampaignInput)
@serialize_pydantic_return
async def add_contact_to_campaign(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    campaign_id: str,
) -> AddContactToCampaignOutput:
    """Enroll a contact into a campaign."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        f"/contacts/{_seg(contact_id)}/campaigns/{_seg(campaign_id)}",
        send_body=True,
    )
    if error is not None:
        return AddContactToCampaignOutput(success=False, error=error)
    return AddContactToCampaignOutput(
        success=True,
        succeeded=_as_bool(_as_dict(payload).get("succeded")),
    )


class RemoveContactFromCampaignInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact to unenroll")
    campaign_id: str = Field(description="Unique identifier of the campaign to unenroll from")


@tool(args_schema=RemoveContactFromCampaignInput)
@serialize_pydantic_return
async def remove_contact_from_campaign(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    campaign_id: str,
) -> RemoveContactFromCampaignOutput:
    """Unenroll a contact from one specific campaign."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "DELETE",
        f"/contacts/{_seg(contact_id)}/campaigns/{_seg(campaign_id)}",
    )
    if error is not None:
        return RemoveContactFromCampaignOutput(success=False, error=error)
    return RemoveContactFromCampaignOutput(
        success=True,
        succeeded=_as_bool(_as_dict(payload).get("succeded")),
    )


class AddContactFollowersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact to add followers to")
    followers: list[str] = Field(
        description="List of user IDs to add as followers of the contact"
    )


@tool(args_schema=AddContactFollowersInput)
@serialize_pydantic_return
async def add_contact_followers(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    followers: list[str],
) -> AddContactFollowersOutput:
    """Add one or more users as followers of a contact."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        f"/contacts/{_seg(contact_id)}/followers",
        json_body={"followers": followers},
    )
    if error is not None:
        return AddContactFollowersOutput(success=False, error=error)
    data = _as_dict(payload)
    return AddContactFollowersOutput(
        success=True,
        followers=_as_str_list(data.get("followers")),
        followers_added=_as_str_list(data.get("followersAdded")),
    )


class RemoveContactFollowersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(
        description="Unique identifier of the contact to remove followers from"
    )
    followers: list[str] = Field(
        description="List of user IDs to remove as followers of the contact"
    )


@tool(args_schema=RemoveContactFollowersInput)
@serialize_pydantic_return
async def remove_contact_followers(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    followers: list[str],
) -> RemoveContactFollowersOutput:
    """Remove one or more users from a contact's followers."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "DELETE",
        f"/contacts/{_seg(contact_id)}/followers",
        json_body={"followers": followers},
    )
    if error is not None:
        return RemoveContactFollowersOutput(success=False, error=error)
    data = _as_dict(payload)
    return RemoveContactFollowersOutput(
        success=True,
        followers=_as_str_list(data.get("followers")),
        followers_removed=_as_str_list(data.get("followersRemoved")),
    )


class ListContactNotesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(
        description="Unique identifier of the contact whose notes should be listed"
    )


@tool(args_schema=ListContactNotesInput)
@serialize_pydantic_return
async def list_contact_notes(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
) -> ListContactNotesOutput:
    """List every note attached to a contact."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/contacts/{_seg(contact_id)}/notes"
    )
    if error is not None:
        return ListContactNotesOutput(success=False, error=error)
    notes = _as_dict_list(_as_dict(payload).get("notes"))
    return ListContactNotesOutput(
        success=True,
        notes=[_parse_contact_note(item) for item in notes],
    )


class CreateContactNoteInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact to add the note to")
    body: str = Field(description="The text content of the note")
    title: str | None = Field(default=None, description="The title of the note")
    color: str | None = Field(default=None, description="The color associated with the note")
    pinned: bool | None = Field(
        default=None, description="When true, the note is pinned to the contact"
    )
    user_id: str | None = Field(
        default=None, description="The user the note is attributed to"
    )


@tool(args_schema=CreateContactNoteInput)
@serialize_pydantic_return
async def create_contact_note(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    body: str,
    title: str | None = None,
    color: str | None = None,
    pinned: bool | None = None,
    user_id: str | None = None,
) -> CreateContactNoteOutput:
    """Attach a new note to a contact."""
    json_body: dict[str, Any] = {
        "body": body,
        "title": title,
        "color": color,
        "pinned": pinned,
        "userId": user_id,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        f"/contacts/{_seg(contact_id)}/notes",
        json_body=json_body,
    )
    if error is not None:
        return CreateContactNoteOutput(success=False, error=error)
    return CreateContactNoteOutput(
        success=True,
        note=_parse_contact_note_opt(_as_dict(payload).get("note")),
    )


class GetContactNoteInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact the note belongs to")
    note_id: str = Field(description="Unique identifier of the note to retrieve")


@tool(args_schema=GetContactNoteInput)
@serialize_pydantic_return
async def get_contact_note(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    note_id: str,
) -> GetContactNoteOutput:
    """Retrieve a single note attached to a contact."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/contacts/{_seg(contact_id)}/notes/{_seg(note_id)}"
    )
    if error is not None:
        return GetContactNoteOutput(success=False, error=error)
    return GetContactNoteOutput(
        success=True,
        note=_parse_contact_note_opt(_as_dict(payload).get("note")),
    )


class UpdateContactNoteInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact the note belongs to")
    note_id: str = Field(description="Unique identifier of the note to update")
    body: str | None = Field(default=None, description="The updated text content of the note")
    title: str | None = Field(default=None, description="The updated title of the note")
    color: str | None = Field(default=None, description="The updated color of the note")
    pinned: bool | None = Field(
        default=None, description="When true, the note is pinned to the contact"
    )
    user_id: str | None = Field(
        default=None, description="The user the note is attributed to"
    )


@tool(args_schema=UpdateContactNoteInput)
@serialize_pydantic_return
async def update_contact_note(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    note_id: str,
    body: str | None = None,
    title: str | None = None,
    color: str | None = None,
    pinned: bool | None = None,
    user_id: str | None = None,
) -> UpdateContactNoteOutput:
    """Update the content or metadata of a note attached to a contact."""
    json_body: dict[str, Any] = {
        "body": body,
        "title": title,
        "color": color,
        "pinned": pinned,
        "userId": user_id,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/contacts/{_seg(contact_id)}/notes/{_seg(note_id)}",
        json_body=json_body,
        send_body=True,
    )
    if error is not None:
        return UpdateContactNoteOutput(success=False, error=error)
    return UpdateContactNoteOutput(
        success=True,
        note=_parse_contact_note_opt(_as_dict(payload).get("note")),
    )


class DeleteContactNoteInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact the note belongs to")
    note_id: str = Field(description="Unique identifier of the note to delete")


@tool(args_schema=DeleteContactNoteInput)
@serialize_pydantic_return
async def delete_contact_note(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    note_id: str,
) -> DeleteContactNoteOutput:
    """Delete a note attached to a contact."""
    payload, error = await _request(
        auth_type, auth_data, "DELETE", f"/contacts/{_seg(contact_id)}/notes/{_seg(note_id)}"
    )
    if error is not None:
        return DeleteContactNoteOutput(success=False, error=error)
    return DeleteContactNoteOutput(
        success=True,
        succeeded=_as_bool(_as_dict(payload).get("succeded")),
    )


class AddContactTagsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact to tag")
    tags: list[str] = Field(description="The tags to add to the contact")


@tool(args_schema=AddContactTagsInput)
@serialize_pydantic_return
async def add_contact_tags(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    tags: list[str],
) -> AddContactTagsOutput:
    """Add one or more tags to a contact."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        f"/contacts/{_seg(contact_id)}/tags",
        json_body={"tags": tags},
    )
    if error is not None:
        return AddContactTagsOutput(success=False, error=error)
    return AddContactTagsOutput(
        success=True,
        tags=_as_str_list(_as_dict(payload).get("tags")),
    )


class RemoveContactTagsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact to untag")
    tags: list[str] = Field(description="The tags to remove from the contact")


@tool(args_schema=RemoveContactTagsInput)
@serialize_pydantic_return
async def remove_contact_tags(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    tags: list[str],
) -> RemoveContactTagsOutput:
    """Remove one or more tags from a contact."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "DELETE",
        f"/contacts/{_seg(contact_id)}/tags",
        json_body={"tags": tags},
    )
    if error is not None:
        return RemoveContactTagsOutput(success=False, error=error)
    return RemoveContactTagsOutput(
        success=True,
        tags=_as_str_list(_as_dict(payload).get("tags")),
    )


class ListContactTasksInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(
        description="Unique identifier of the contact whose tasks to retrieve"
    )


@tool(args_schema=ListContactTasksInput)
@serialize_pydantic_return
async def list_contact_tasks(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
) -> ListContactTasksOutput:
    """List every task attached to a contact."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/contacts/{_seg(contact_id)}/tasks"
    )
    if error is not None:
        return ListContactTasksOutput(success=False, error=error)
    tasks = _as_dict_list(_as_dict(payload).get("tasks"))
    return ListContactTasksOutput(
        success=True,
        tasks=[_parse_contact_task(item) for item in tasks],
    )


class CreateContactTaskInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(
        description="Unique identifier of the contact to create the task for"
    )
    title: str = Field(description="The title/subject of the task")
    due_date: str = Field(description="ISO 8601 due date for the task")
    completed: bool = Field(
        default=False, description="Whether the task starts out marked as completed"
    )
    body: str | None = Field(
        default=None, description="The description or body text of the task"
    )
    assigned_to: str | None = Field(
        default=None, description="Unique identifier of the user assigned to the task"
    )


@tool(args_schema=CreateContactTaskInput)
@serialize_pydantic_return
async def create_contact_task(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    title: str,
    due_date: str,
    completed: bool = False,
    body: str | None = None,
    assigned_to: str | None = None,
) -> CreateContactTaskOutput:
    """Create a task on a contact, such as a follow-up or reminder."""
    json_body: dict[str, Any] = {
        "title": title,
        "dueDate": due_date,
        "completed": completed,
        "body": body,
        "assignedTo": assigned_to,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        f"/contacts/{_seg(contact_id)}/tasks",
        json_body=json_body,
    )
    if error is not None:
        return CreateContactTaskOutput(success=False, error=error)
    return CreateContactTaskOutput(
        success=True,
        task=_parse_contact_task_opt(_as_dict(payload).get("task")),
    )


class GetContactTaskInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact the task belongs to")
    task_id: str = Field(description="Unique identifier of the task to retrieve")


@tool(args_schema=GetContactTaskInput)
@serialize_pydantic_return
async def get_contact_task(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    task_id: str,
) -> GetContactTaskOutput:
    """Retrieve a single task attached to a contact."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/contacts/{_seg(contact_id)}/tasks/{_seg(task_id)}"
    )
    if error is not None:
        return GetContactTaskOutput(success=False, error=error)
    return GetContactTaskOutput(
        success=True,
        task=_parse_contact_task_opt(_as_dict(payload).get("task")),
    )


class UpdateContactTaskInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact the task belongs to")
    task_id: str = Field(description="Unique identifier of the task to update")
    title: str | None = Field(default=None, description="The updated title/subject of the task")
    due_date: str | None = Field(default=None, description="The updated ISO 8601 due date")
    completed: bool | None = Field(
        default=None, description="Whether the task is marked as completed"
    )
    body: str | None = Field(
        default=None, description="The updated description or body text of the task"
    )
    assigned_to: str | None = Field(
        default=None, description="Unique identifier of the user assigned to the task"
    )


@tool(args_schema=UpdateContactTaskInput)
@serialize_pydantic_return
async def update_contact_task(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    task_id: str,
    title: str | None = None,
    due_date: str | None = None,
    completed: bool | None = None,
    body: str | None = None,
    assigned_to: str | None = None,
) -> UpdateContactTaskOutput:
    """Update the fields of a task attached to a contact."""
    json_body: dict[str, Any] = {
        "title": title,
        "dueDate": due_date,
        "completed": completed,
        "body": body,
        "assignedTo": assigned_to,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/contacts/{_seg(contact_id)}/tasks/{_seg(task_id)}",
        json_body=json_body,
        send_body=True,
    )
    if error is not None:
        return UpdateContactTaskOutput(success=False, error=error)
    return UpdateContactTaskOutput(
        success=True,
        task=_parse_contact_task_opt(_as_dict(payload).get("task")),
    )


class DeleteContactTaskInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact the task belongs to")
    task_id: str = Field(description="Unique identifier of the task to delete")


@tool(args_schema=DeleteContactTaskInput)
@serialize_pydantic_return
async def delete_contact_task(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    task_id: str,
) -> DeleteContactTaskOutput:
    """Delete a task attached to a contact."""
    payload, error = await _request(
        auth_type, auth_data, "DELETE", f"/contacts/{_seg(contact_id)}/tasks/{_seg(task_id)}"
    )
    if error is not None:
        return DeleteContactTaskOutput(success=False, error=error)
    return DeleteContactTaskOutput(
        success=True,
        succeeded=_as_bool(_as_dict(payload).get("succeded")),
    )


class CompleteContactTaskInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact the task belongs to")
    task_id: str = Field(description="Unique identifier of the task to update")
    completed: bool = Field(
        default=True, description="True to mark the task complete, false to reopen it"
    )


@tool(args_schema=CompleteContactTaskInput)
@serialize_pydantic_return
async def complete_contact_task(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    task_id: str,
    completed: bool = True,
) -> CompleteContactTaskOutput:
    """Mark a contact's task as completed or reopen it."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/contacts/{_seg(contact_id)}/tasks/{_seg(task_id)}/completed",
        json_body={"completed": completed},
    )
    if error is not None:
        return CompleteContactTaskOutput(success=False, error=error)
    return CompleteContactTaskOutput(
        success=True,
        task=_parse_contact_task_opt(_as_dict(payload).get("task")),
    )


class AddContactToWorkflowInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact to add")
    workflow_id: str = Field(description="Unique identifier of the workflow to add the contact to")
    event_start_time: str | None = Field(
        default=None,
        description="ISO 8601 time at which the workflow should start for this contact",
    )


@tool(args_schema=AddContactToWorkflowInput)
@serialize_pydantic_return
async def add_contact_to_workflow(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    workflow_id: str,
    event_start_time: str | None = None,
) -> AddContactToWorkflowOutput:
    """Add a contact to a workflow, optionally scheduling when it starts."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        f"/contacts/{_seg(contact_id)}/workflow/{_seg(workflow_id)}",
        json_body={"eventStartTime": event_start_time},
        send_body=True,
    )
    if error is not None:
        return AddContactToWorkflowOutput(success=False, error=error)
    return AddContactToWorkflowOutput(
        success=True,
        succeeded=_as_bool(_as_dict(payload).get("succeded")),
    )


class DeleteContactFromWorkflowInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Unique identifier of the contact to remove")
    workflow_id: str = Field(
        description="Unique identifier of the workflow to remove the contact from"
    )
    event_start_time: str | None = Field(
        default=None, description="ISO 8601 time of the workflow event to remove"
    )


@tool(args_schema=DeleteContactFromWorkflowInput)
@serialize_pydantic_return
async def delete_contact_from_workflow(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    workflow_id: str,
    event_start_time: str | None = None,
) -> DeleteContactFromWorkflowOutput:
    """Remove a contact from a workflow."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "DELETE",
        f"/contacts/{_seg(contact_id)}/workflow/{_seg(workflow_id)}",
        json_body={"eventStartTime": event_start_time},
        send_body=True,
    )
    if error is not None:
        return DeleteContactFromWorkflowOutput(success=False, error=error)
    return DeleteContactFromWorkflowOutput(
        success=True,
        succeeded=_as_bool(_as_dict(payload).get("succeded")),
    )


# --- Opportunities ----------------------------------------------------------


class CreateOpportunityInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    pipeline_id: str = Field(description="Unique identifier of the pipeline")
    name: str = Field(description="The name of the opportunity")
    status: str = Field(
        description="The status of the opportunity: open, won, lost or abandoned"
    )
    contact_id: str = Field(
        description="Unique identifier of the contact associated with the opportunity"
    )
    pipeline_stage_id: str | None = Field(
        default=None, description="Unique identifier of the pipeline stage"
    )
    monetary_value: float | None = Field(
        default=None, description="The monetary value of the opportunity"
    )
    assigned_to: str | None = Field(
        default=None, description="Unique identifier of the user the opportunity is assigned to"
    )
    custom_fields: list[dict[str, Any]] | None = Field(
        default=None, description="Custom field values to set on the opportunity"
    )


@tool(args_schema=CreateOpportunityInput)
@serialize_pydantic_return
async def create_opportunity(
    auth_type: str,
    auth_data: dict[str, Any],
    pipeline_id: str,
    name: str,
    status: str,
    contact_id: str,
    pipeline_stage_id: str | None = None,
    monetary_value: float | None = None,
    assigned_to: str | None = None,
    custom_fields: list[dict[str, Any]] | None = None,
) -> CreateOpportunityOutput:
    """Create an opportunity in a pipeline for a contact."""
    location_id = _location_id(auth_data)
    if not location_id:
        return CreateOpportunityOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "locationId": location_id,
        "pipelineId": pipeline_id,
        "name": name,
        "status": status,
        "contactId": contact_id,
        "pipelineStageId": pipeline_stage_id,
        "monetaryValue": monetary_value,
        "assignedTo": assigned_to,
        "customFields": custom_fields,
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/opportunities/", json_body=body
    )
    if error is not None:
        return CreateOpportunityOutput(success=False, error=error)
    return CreateOpportunityOutput(
        success=True,
        opportunity=_parse_opportunity_opt(_as_dict(payload).get("opportunity")),
    )


class ListOpportunityLostReasonsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str | None = Field(
        default=None, description="Filter lost reasons by their exact name"
    )
    query: str | None = Field(default=None, description="A search string to filter lost reasons")
    deleted: bool | None = Field(
        default=None, description="Whether to include deleted lost reasons in the results"
    )
    skip: int | None = Field(
        default=None, description="Number of lost reasons to skip for pagination"
    )
    limit: int | None = Field(
        default=None, description="Maximum number of lost reasons to return"
    )
    get_count: bool | None = Field(
        default=None, description="Whether to include the total count in the response"
    )


@tool(args_schema=ListOpportunityLostReasonsInput)
@serialize_pydantic_return
async def list_opportunity_lost_reasons(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str | None = None,
    query: str | None = None,
    deleted: bool | None = None,
    skip: int | None = None,
    limit: int | None = None,
    get_count: bool | None = None,
) -> ListOpportunityLostReasonsOutput:
    """List the opportunity "lost" reasons configured for the sub-account."""
    location_id = _location_id(auth_data)
    if not location_id:
        return ListOpportunityLostReasonsOutput(success=False, error=_MISSING_LOCATION)
    params: dict[str, Any] = {
        "locationId": location_id,
        "name": name,
        "query": query,
        "deleted": deleted,
        "skip": skip,
        "limit": limit,
        "getCount": get_count,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/opportunities/lost-reason", params=params
    )
    if error is not None:
        return ListOpportunityLostReasonsOutput(success=False, error=error)
    body = _as_dict(payload)
    reasons = _as_dict_list(body.get("lostReasons"))
    return ListOpportunityLostReasonsOutput(
        success=True,
        lost_reasons=[_parse_opportunity_lost_reason(item) for item in reasons],
        total=_as_int(body.get("total")),
    )


class ListPipelinesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


@tool(args_schema=ListPipelinesInput)
@serialize_pydantic_return
async def list_pipelines(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListPipelinesOutput:
    """List the opportunity pipelines and their stages for the sub-account."""
    location_id = _location_id(auth_data)
    if not location_id:
        return ListPipelinesOutput(success=False, error=_MISSING_LOCATION)
    payload, error = await _request(
        auth_type,
        auth_data,
        "GET",
        "/opportunities/pipelines",
        params={"locationId": location_id},
    )
    if error is not None:
        return ListPipelinesOutput(success=False, error=error)
    pipelines = _as_dict_list(_as_dict(payload).get("pipelines"))
    return ListPipelinesOutput(
        success=True,
        pipelines=[_parse_pipeline(item) for item in pipelines],
    )


class SearchOpportunitiesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    query: str | None = Field(
        default=None, description="A free-text search query to filter opportunities"
    )
    opportunity_id: str | None = Field(
        default=None, description="Unique identifier of a specific opportunity to fetch"
    )
    pipeline_id: str | None = Field(
        default=None, description="Unique identifier of the pipeline to filter by"
    )
    pipeline_stage_id: str | None = Field(
        default=None, description="Unique identifier of the pipeline stage to filter by"
    )
    contact_id: str | None = Field(
        default=None, description="Unique identifier of the contact to filter by"
    )
    assigned_to: str | None = Field(
        default=None, description="Unique identifier of the assigned user to filter by"
    )
    campaign_id: str | None = Field(
        default=None, description="Unique identifier of the campaign to filter by"
    )
    status: str | None = Field(
        default=None,
        description="Status filter: open, won, lost, abandoned or all",
    )
    country: str | None = Field(default=None, description="Filter opportunities by country")
    date: str | None = Field(default=None, description="Filter opportunities by a specific date")
    end_date: str | None = Field(
        default=None, description="Filter opportunities up to this end date"
    )
    order: str | None = Field(default=None, description="The sort order for the results")
    page: int | None = Field(default=None, description="The page number of results to retrieve")
    limit: int | None = Field(
        default=None, description="Maximum number of opportunities to return per page"
    )
    start_after: str | None = Field(
        default=None, description="Cursor timestamp used for pagination"
    )
    start_after_id: str | None = Field(
        default=None, description="Cursor id used for pagination"
    )
    get_tasks: bool | None = Field(
        default=None, description="When true, includes related tasks in the response"
    )
    get_notes: bool | None = Field(
        default=None, description="When true, includes related notes in the response"
    )
    get_calendar_events: bool | None = Field(
        default=None, description="When true, includes related calendar events in the response"
    )


@tool(args_schema=SearchOpportunitiesInput)
@serialize_pydantic_return
async def search_opportunities(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str | None = None,
    opportunity_id: str | None = None,
    pipeline_id: str | None = None,
    pipeline_stage_id: str | None = None,
    contact_id: str | None = None,
    assigned_to: str | None = None,
    campaign_id: str | None = None,
    status: str | None = None,
    country: str | None = None,
    date: str | None = None,
    end_date: str | None = None,
    order: str | None = None,
    page: int | None = None,
    limit: int | None = None,
    start_after: str | None = None,
    start_after_id: str | None = None,
    get_tasks: bool | None = None,
    get_notes: bool | None = None,
    get_calendar_events: bool | None = None,
) -> SearchOpportunitiesOutput:
    """Search opportunities by pipeline, stage, contact, assignee, status or date."""
    location_id = _location_id(auth_data)
    if not location_id:
        return SearchOpportunitiesOutput(success=False, error=_MISSING_LOCATION)
    # This endpoint is the one place the API uses snake_case query keys
    # (`location_id`, `pipeline_id`, ...) alongside camelCase ones
    # (`campaignId`, `endDate`, ...). Both spellings below are copied
    # verbatim from the OpenAPI `parameters` block.
    params: dict[str, Any] = {
        "location_id": location_id,
        "q": query,
        "id": opportunity_id,
        "pipeline_id": pipeline_id,
        "pipeline_stage_id": pipeline_stage_id,
        "contact_id": contact_id,
        "assigned_to": assigned_to,
        "campaignId": campaign_id,
        "status": status,
        "country": country,
        "date": date,
        "endDate": end_date,
        "order": order,
        "page": page,
        "limit": limit,
        "startAfter": start_after,
        "startAfterId": start_after_id,
        "getTasks": get_tasks,
        "getNotes": get_notes,
        "getCalendarEvents": get_calendar_events,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/opportunities/search", params=params
    )
    if error is not None:
        return SearchOpportunitiesOutput(success=False, error=error)
    body = _as_dict(payload)
    opportunities = _as_dict_list(body.get("opportunities"))
    return SearchOpportunitiesOutput(
        success=True,
        opportunities=[_parse_opportunity(item) for item in opportunities],
        meta=_parse_opportunity_search_meta_opt(body.get("meta")),
        aggregations=_as_dict(body.get("aggregations")),
    )


class SearchOpportunitiesAdvancedInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    query: str = Field(
        default="", description="The search query string used to match opportunities"
    )
    limit: int = Field(
        default=20, description="Maximum number of opportunities to return per page"
    )
    page: int = Field(default=1, description="The page number of results to retrieve")
    search_after: list[str] | None = Field(
        default=None,
        description="Cursor values for deep pagination, returned by a previous search",
    )
    include_notes: bool = Field(
        default=False, description="When true, include related notes for each opportunity"
    )
    include_tasks: bool = Field(
        default=False, description="When true, include related tasks for each opportunity"
    )
    include_calendar_events: bool = Field(
        default=False,
        description="When true, include related calendar events for each opportunity",
    )
    include_unread_conversations: bool = Field(
        default=False,
        description="When true, include unread conversation counts for each opportunity",
    )


@tool(args_schema=SearchOpportunitiesAdvancedInput)
@serialize_pydantic_return
async def search_opportunities_advanced(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str = "",
    limit: int = 20,
    page: int = 1,
    search_after: list[str] | None = None,
    include_notes: bool = False,
    include_tasks: bool = False,
    include_calendar_events: bool = False,
    include_unread_conversations: bool = False,
) -> SearchOpportunitiesAdvancedOutput:
    """Search opportunities and optionally pull their notes, tasks and events."""
    location_id = _location_id(auth_data)
    if not location_id:
        return SearchOpportunitiesAdvancedOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "locationId": location_id,
        "query": query,
        "limit": limit,
        "page": page,
        "searchAfter": search_after,
        "additionalDetails": {
            "notes": include_notes,
            "tasks": include_tasks,
            "calendarEvents": include_calendar_events,
            "unReadConversations": include_unread_conversations,
        },
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/opportunities/search", json_body=body
    )
    if error is not None:
        return SearchOpportunitiesAdvancedOutput(success=False, error=error)
    data = _as_dict(payload)
    opportunities = _as_dict_list(data.get("opportunities"))
    return SearchOpportunitiesAdvancedOutput(
        success=True,
        opportunities=[_parse_opportunity(item) for item in opportunities],
        total=_as_int(data.get("total")),
        aggregations=_as_dict(data.get("aggregations")),
    )


class UpsertOpportunityInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    pipeline_id: str = Field(
        description="Unique identifier of the pipeline the opportunity belongs to"
    )
    opportunity_id: str | None = Field(
        default=None,
        description="When provided, updates that opportunity instead of creating a new one",
    )
    contact_id: str | None = Field(
        default=None,
        description="Unique identifier of the contact associated with the opportunity",
    )
    name: str | None = Field(default=None, description="The name of the opportunity")
    status: str | None = Field(
        default=None, description="The status of the opportunity: open, won, lost or abandoned"
    )
    pipeline_stage_id: str | None = Field(
        default=None, description="Unique identifier of the pipeline stage"
    )
    monetary_value: float | None = Field(
        default=None, description="The monetary value of the opportunity"
    )
    assigned_to: str | None = Field(
        default=None, description="Unique identifier of the user the opportunity is assigned to"
    )
    lost_reason_id: str | None = Field(
        default=None, description="Unique identifier of the reason the opportunity was lost"
    )
    followers: list[str] | None = Field(
        default=None, description="User identifiers to set as followers of the opportunity"
    )
    followers_action_type: str | None = Field(
        default=None, description="Action to apply to the followers list: 'add' or 'remove'"
    )
    is_remove_all_followers: bool | None = Field(
        default=None, description="When true, removes all followers from the opportunity"
    )


@tool(args_schema=UpsertOpportunityInput)
@serialize_pydantic_return
async def upsert_opportunity(
    auth_type: str,
    auth_data: dict[str, Any],
    pipeline_id: str,
    opportunity_id: str | None = None,
    contact_id: str | None = None,
    name: str | None = None,
    status: str | None = None,
    pipeline_stage_id: str | None = None,
    monetary_value: float | None = None,
    assigned_to: str | None = None,
    lost_reason_id: str | None = None,
    followers: list[str] | None = None,
    followers_action_type: str | None = None,
    is_remove_all_followers: bool | None = None,
) -> UpsertOpportunityOutput:
    """Create an opportunity, or update it when an opportunity id is supplied."""
    location_id = _location_id(auth_data)
    if not location_id:
        return UpsertOpportunityOutput(success=False, error=_MISSING_LOCATION)
    # TODO (unverified): `contactId` is absent from `UpsertOpportunityDto` in
    # the published opportunities API spec but is documented as required by the vendor's published
    # "Upsert Opportunity" action; sent only when the caller supplies it.
    body: dict[str, Any] = {
        "locationId": location_id,
        "pipelineId": pipeline_id,
        "id": opportunity_id,
        "contactId": contact_id,
        "name": name,
        "status": status,
        "pipelineStageId": pipeline_stage_id,
        "monetaryValue": monetary_value,
        "assignedTo": assigned_to,
        "lostReasonId": lost_reason_id,
        "followers": followers,
        "followersActionType": followers_action_type,
        "isRemoveAllFollowers": is_remove_all_followers,
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/opportunities/upsert", json_body=body
    )
    if error is not None:
        return UpsertOpportunityOutput(success=False, error=error)
    data = _as_dict(payload)
    return UpsertOpportunityOutput(
        success=True,
        opportunity=_parse_opportunity_opt(data.get("opportunity")),
        new=_as_bool(data.get("new")),
    )


class GetOpportunityInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    opportunity_id: str = Field(description="Unique identifier of the opportunity to retrieve")


@tool(args_schema=GetOpportunityInput)
@serialize_pydantic_return
async def get_opportunity(
    auth_type: str,
    auth_data: dict[str, Any],
    opportunity_id: str,
) -> GetOpportunityOutput:
    """Retrieve a single opportunity by its id."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/opportunities/{_seg(opportunity_id)}"
    )
    if error is not None:
        return GetOpportunityOutput(success=False, error=error)
    return GetOpportunityOutput(
        success=True,
        opportunity=_parse_opportunity_opt(_as_dict(payload).get("opportunity")),
    )


class DeleteOpportunityInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    opportunity_id: str = Field(description="Unique identifier of the opportunity to delete")


@tool(args_schema=DeleteOpportunityInput)
@serialize_pydantic_return
async def delete_opportunity(
    auth_type: str,
    auth_data: dict[str, Any],
    opportunity_id: str,
) -> DeleteOpportunityOutput:
    """Permanently delete an opportunity."""
    payload, error = await _request(
        auth_type, auth_data, "DELETE", f"/opportunities/{_seg(opportunity_id)}"
    )
    if error is not None:
        return DeleteOpportunityOutput(success=False, error=error)
    return DeleteOpportunityOutput(
        success=True,
        succeeded=_as_bool(_as_dict(payload).get("succeded")),
    )


class UpdateOpportunityInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    opportunity_id: str = Field(description="Unique identifier of the opportunity to update")
    name: str | None = Field(default=None, description="The name of the opportunity")
    status: str | None = Field(
        default=None, description="The status of the opportunity: open, won, lost or abandoned"
    )
    pipeline_id: str | None = Field(
        default=None, description="Unique identifier of the pipeline the opportunity belongs to"
    )
    pipeline_stage_id: str | None = Field(
        default=None, description="Unique identifier of the pipeline stage"
    )
    monetary_value: float | None = Field(
        default=None, description="The monetary value of the opportunity"
    )
    assigned_to: str | None = Field(
        default=None, description="Unique identifier of the user the opportunity is assigned to"
    )
    custom_fields: list[dict[str, Any]] | None = Field(
        default=None, description="Custom field values to set on the opportunity"
    )


@tool(args_schema=UpdateOpportunityInput)
@serialize_pydantic_return
async def update_opportunity(
    auth_type: str,
    auth_data: dict[str, Any],
    opportunity_id: str,
    name: str | None = None,
    status: str | None = None,
    pipeline_id: str | None = None,
    pipeline_stage_id: str | None = None,
    monetary_value: float | None = None,
    assigned_to: str | None = None,
    custom_fields: list[dict[str, Any]] | None = None,
) -> UpdateOpportunityOutput:
    """Update an opportunity's name, pipeline, stage, value or assignee."""
    body: dict[str, Any] = {
        "name": name,
        "status": status,
        "pipelineId": pipeline_id,
        "pipelineStageId": pipeline_stage_id,
        "monetaryValue": monetary_value,
        "assignedTo": assigned_to,
        "customFields": custom_fields,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/opportunities/{_seg(opportunity_id)}",
        json_body=body,
        send_body=True,
    )
    if error is not None:
        return UpdateOpportunityOutput(success=False, error=error)
    return UpdateOpportunityOutput(
        success=True,
        opportunity=_parse_opportunity_opt(_as_dict(payload).get("opportunity")),
    )


class AddOpportunityFollowersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    opportunity_id: str = Field(
        description="Unique identifier of the opportunity to add followers to"
    )
    followers: list[str] = Field(
        description="List of user IDs to add as followers of the opportunity"
    )


@tool(args_schema=AddOpportunityFollowersInput)
@serialize_pydantic_return
async def add_opportunity_followers(
    auth_type: str,
    auth_data: dict[str, Any],
    opportunity_id: str,
    followers: list[str],
) -> AddOpportunityFollowersOutput:
    """Add one or more users as followers of an opportunity."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        f"/opportunities/{_seg(opportunity_id)}/followers",
        json_body={"followers": followers},
    )
    if error is not None:
        return AddOpportunityFollowersOutput(success=False, error=error)
    data = _as_dict(payload)
    return AddOpportunityFollowersOutput(
        success=True,
        followers=_as_str_list(data.get("followers")),
        followers_added=_as_str_list(data.get("followersAdded")),
    )


class RemoveOpportunityFollowersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    opportunity_id: str = Field(
        description="Unique identifier of the opportunity to remove followers from"
    )
    followers: list[str] = Field(
        description="List of user IDs to remove as followers of the opportunity"
    )
    is_remove_all_followers: bool | None = Field(
        default=None,
        description="When true, removes every follower regardless of the followers list",
    )


@tool(args_schema=RemoveOpportunityFollowersInput)
@serialize_pydantic_return
async def remove_opportunity_followers(
    auth_type: str,
    auth_data: dict[str, Any],
    opportunity_id: str,
    followers: list[str],
    is_remove_all_followers: bool | None = None,
) -> RemoveOpportunityFollowersOutput:
    """Remove one or more users from an opportunity's followers."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "DELETE",
        f"/opportunities/{_seg(opportunity_id)}/followers",
        params={"isRemoveAllFollowers": is_remove_all_followers},
        json_body={"followers": followers},
    )
    if error is not None:
        return RemoveOpportunityFollowersOutput(success=False, error=error)
    data = _as_dict(payload)
    return RemoveOpportunityFollowersOutput(
        success=True,
        followers=_as_str_list(data.get("followers")),
        followers_removed=_as_str_list(data.get("followersRemoved")),
    )


class UpdateOpportunityStatusInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    opportunity_id: str = Field(
        description="Unique identifier of the opportunity whose status is being updated"
    )
    status: str = Field(
        description="The new status: open, won, lost or abandoned"
    )
    lost_reason_id: str | None = Field(
        default=None,
        description="Unique identifier of the lost reason, used when the status is 'lost'",
    )


@tool(args_schema=UpdateOpportunityStatusInput)
@serialize_pydantic_return
async def update_opportunity_status(
    auth_type: str,
    auth_data: dict[str, Any],
    opportunity_id: str,
    status: str,
    lost_reason_id: str | None = None,
) -> UpdateOpportunityStatusOutput:
    """Move an opportunity to open, won, lost or abandoned."""
    body: dict[str, Any] = {"status": status, "lostReasonId": lost_reason_id}
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/opportunities/{_seg(opportunity_id)}/status",
        json_body=body,
    )
    if error is not None:
        return UpdateOpportunityStatusOutput(success=False, error=error)
    return UpdateOpportunityStatusOutput(
        success=True,
        succeeded=_as_bool(_as_dict(payload).get("succeded")),
    )


# --- Communication parsers --------------------------------------------------


def _parse_conversation(value: Any) -> ConversationResource:
    """Map any of the four upstream conversation shapes onto one model."""
    item = _as_dict(value)
    return ConversationResource(
        id=_as_str(item.get("id")),
        contact_id=_as_str(item.get("contactId")),
        location_id=_as_str(item.get("locationId")),
        assigned_to=_as_str(item.get("assignedTo")),
        user_id=_as_str(item.get("userId")),
        conversation_type=_as_str(item.get("type")),
        unread_count=_as_int(item.get("unreadCount")),
        last_message_body=_as_str(item.get("lastMessageBody")),
        last_message_type=_as_str(item.get("lastMessageType")),
        last_message_date=_as_str(item.get("lastMessageDate")),
        full_name=_as_str(item.get("fullName")),
        contact_name=_as_str(item.get("contactName")),
        email=_as_str(item.get("email")),
        phone=_as_str(item.get("phone")),
        inbox=_as_bool(item.get("inbox")),
        starred=_as_bool(item.get("starred")),
        deleted=_as_bool(item.get("deleted")),
        date_added=_as_str(item.get("dateAdded")),
        date_updated=_as_str(item.get("dateUpdated")),
    )


def _parse_message_meta(value: Any) -> MessageMetaResource | None:
    """Channel metadata is optional; absent metadata stays ``None``."""
    item = _as_dict(value)
    if not item:
        return None
    email = item.get("email")
    return MessageMetaResource(
        call_duration=_as_str(item.get("callDuration")),
        call_status=_as_str(item.get("callStatus")),
        email=email if isinstance(email, dict) else None,
    )


def _parse_message(value: Any) -> MessageResource:
    item = _as_dict(value)
    return MessageResource(
        id=_as_str(item.get("id")),
        message_type_code=_as_int(item.get("type")),
        message_type=_as_str(item.get("messageType")),
        location_id=_as_str(item.get("locationId")),
        contact_id=_as_str(item.get("contactId")),
        conversation_id=_as_str(item.get("conversationId")),
        date_added=_as_str(item.get("dateAdded")),
        body=_as_str(item.get("body")),
        direction=_as_str(item.get("direction")),
        status=_as_str(item.get("status")),
        content_type=_as_str(item.get("contentType")),
        attachments=_as_str_list(item.get("attachments")),
        meta=_parse_message_meta(item.get("meta")),
        source=_as_str(item.get("source")),
        user_id=_as_str(item.get("userId")),
        conversation_provider_id=_as_str(item.get("conversationProviderId")),
        chat_widget_id=_as_str(item.get("chatWidgetId")),
    )


def _parse_email_message(value: Any) -> EmailMessageResource:
    item = _as_dict(value)
    return EmailMessageResource(
        id=_as_str(item.get("id")),
        alt_id=_as_str(item.get("altId")),
        thread_id=_as_str(item.get("threadId")),
        location_id=_as_str(item.get("locationId")),
        contact_id=_as_str(item.get("contactId")),
        conversation_id=_as_str(item.get("conversationId")),
        date_added=_as_str(item.get("dateAdded")),
        subject=_as_str(item.get("subject")),
        body=_as_str(item.get("body")),
        direction=_as_str(item.get("direction")),
        status=_as_str(item.get("status")),
        content_type=_as_str(item.get("contentType")),
        attachments=_as_str_list(item.get("attachments")),
        provider=_as_str(item.get("provider")),
        from_address=_as_str(item.get("from")),
        to=_as_str_list(item.get("to")),
        cc=_as_str_list(item.get("cc")),
        bcc=_as_str_list(item.get("bcc")),
        reply_to_message_id=_as_str(item.get("replyToMessageId")),
        source=_as_str(item.get("source")),
        conversation_provider_id=_as_str(item.get("conversationProviderId")),
    )


def _parse_message_forward(value: Any) -> MessageForwardResource | None:
    """Forward metadata only appears on forwarded email sends."""
    item = _as_dict(value)
    if not item:
        return None
    return MessageForwardResource(
        forward_whole_thread=_as_bool(item.get("forwardWholeThread")),
        message_id=_as_str(item.get("messageId")),
        email_message_id=_as_str(item.get("emailMessageId")),
        source_contact_id=_as_str(item.get("sourceContactId")),
        source_conversation_id=_as_str(item.get("sourceConversationId")),
        forward_to_email=_as_str(item.get("forwardToEmail")),
        recipient_contact_id=_as_str(item.get("recipientContactId")),
        recipient_conversation_id=_as_str(item.get("recipientConversationId")),
    )


def _parse_message_transcript_segment(value: Any) -> MessageTranscriptSegmentResource:
    item = _as_dict(value)
    return MessageTranscriptSegmentResource(
        media_channel=_as_int(item.get("mediaChannel")),
        sentence_index=_as_int(item.get("sentenceIndex")),
        start_time=_as_float(item.get("startTime")),
        end_time=_as_float(item.get("endTime")),
        transcript=_as_str(item.get("transcript")),
        confidence=_as_float(item.get("confidence")),
    )


def _parse_email_template(value: Any) -> EmailTemplateResource:
    item = _as_dict(value)
    return EmailTemplateResource(
        id=_as_str(item.get("id")),
        name=_as_str(item.get("name")),
        template_type=_as_str(item.get("templateType")),
        version=_as_str(item.get("version")),
        is_plain_text=_as_bool(item.get("isPlainText")),
        preview_url=_as_str(item.get("previewUrl")),
        updated_by=_as_str(item.get("updatedBy")),
        last_updated=_as_str(item.get("lastUpdated")),
        date_added=_as_str(item.get("dateAdded")),
    )


def _parse_email_schedule(value: Any) -> EmailScheduleResource:
    item = _as_dict(value)
    return EmailScheduleResource(
        id=_as_str(item.get("id")),
        name=_as_str(item.get("name")),
        status=_as_str(item.get("status")),
        location_id=_as_str(item.get("locationId")),
        parent_id=_as_str(item.get("parentId")),
        child_count=_as_int(item.get("childCount")),
        child=_as_str_list(item.get("child")),
        campaign_type=_as_str(item.get("campaignType")),
        bulk_action_version=_as_str(item.get("bulkActionVersion")),
        repeat_after=_as_str(item.get("repeatAfter")),
        send_days=_as_str_list(item.get("sendDays")),
        template_id=_as_str(item.get("templateId")),
        template_type=_as_str(item.get("templateType")),
        document_id=_as_str(item.get("documentId")),
        download_url=_as_str(item.get("downloadUrl")),
        template_data_download_url=_as_str(item.get("templateDataDownloadUrl")),
        deleted=_as_bool(item.get("deleted")),
        migrated=_as_bool(item.get("migrated")),
        archived=_as_bool(item.get("archived")),
        has_tracking=_as_bool(item.get("hasTracking")),
        has_utm_tracking=_as_bool(item.get("hasUtmTracking")),
        is_plain_text=_as_bool(item.get("isPlainText")),
        enable_resend_to_unopened=_as_bool(item.get("enableResendToUnopened")),
        created_at=_as_str(item.get("createdAt")),
        updated_at=_as_str(item.get("updatedAt")),
    )


def _parse_email_total(value: Any) -> list[str]:
    """``total`` is declared as a string array upstream but can arrive scalar."""
    values = _as_str_list(value)
    if values:
        return values
    single = _as_str(value)
    return [single] if single is not None else []


def _parse_campaign(value: Any) -> CampaignResource:
    item = _as_dict(value)
    return CampaignResource(
        id=_as_str(item.get("id")),
        name=_as_str(item.get("name")),
        status=_as_str(item.get("status")),
        location_id=_as_str(item.get("locationId")),
    )


# --- Campaigns --------------------------------------------------------------


class ListCampaignsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    status: str | None = Field(
        default=None,
        description="Filter campaigns by status, for example published or draft",
    )


@tool(args_schema=ListCampaignsInput)
@serialize_pydantic_return
async def list_campaigns(
    auth_type: str,
    auth_data: dict[str, Any],
    status: str | None = None,
) -> ListCampaignsOutput:
    """List the marketing campaigns configured in the GoHighLevel sub-account."""
    location_id = _location_id(auth_data)
    if not location_id:
        return ListCampaignsOutput(success=False, error=_MISSING_LOCATION)
    payload, error = await _request(
        auth_type,
        auth_data,
        "GET",
        "/campaigns/",
        params={"locationId": location_id, "status": status},
    )
    if error is not None:
        return ListCampaignsOutput(success=False, error=error)
    body = _as_dict(payload)
    return ListCampaignsOutput(
        success=True,
        campaigns=[_parse_campaign(item) for item in _as_dict_list(body.get("campaigns"))],
    )


# --- Conversations ----------------------------------------------------------


class CreateConversationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(
        description="The unique identifier of the contact the conversation is with"
    )


@tool(args_schema=CreateConversationInput)
@serialize_pydantic_return
async def create_conversation(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
) -> CreateConversationOutput:
    """Start a new conversation thread with a contact in the sub-account."""
    location_id = _location_id(auth_data)
    if not location_id:
        return CreateConversationOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {"locationId": location_id, "contactId": contact_id}
    payload, error = await _request(
        auth_type, auth_data, "POST", "/conversations/", json_body=body
    )
    if error is not None:
        return CreateConversationOutput(success=False, error=error)
    result = _as_dict(payload)
    return CreateConversationOutput(
        success=True,
        conversation=_parse_conversation(result.get("conversation")),
    )


class GetMessageTranscriptionInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_id: str = Field(
        description="The unique identifier of the call message to transcribe"
    )


@tool(args_schema=GetMessageTranscriptionInput)
@serialize_pydantic_return
async def get_message_transcription(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
) -> GetMessageTranscriptionOutput:
    """Get the call-recording transcription for a message, sentence by sentence."""
    location_id = _location_id(auth_data)
    if not location_id:
        return GetMessageTranscriptionOutput(success=False, error=_MISSING_LOCATION)
    path = f"/conversations/locations/{_seg(location_id)}/messages/{_seg(message_id)}/transcription"
    payload, error = await _request(auth_type, auth_data, "GET", path)
    if error is not None:
        return GetMessageTranscriptionOutput(success=False, error=error)
    # TODO (unverified): the published conversations API spec declares a single
    # GetMessageTranscriptionResponseDto object, but its sentenceIndex field
    # implies one entry per sentence. Both shapes are accepted.
    segments = _as_dict_list(payload)
    if not segments:
        single = _as_dict(payload)
        segments = [single] if single else []
    return GetMessageTranscriptionOutput(
        success=True,
        segments=[_parse_message_transcript_segment(item) for item in segments],
    )


class SendMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_type: str = Field(
        description=(
            "Channel to send on: SMS, RCS, Email, WhatsApp, IG, FB, Custom, "
            "Live_Chat or TIKTOK"
        )
    )
    contact_id: str = Field(description="ID of the contact receiving the message")
    message: str | None = Field(
        default=None, description="Text content of the message"
    )
    subject: str | None = Field(
        default=None, description="Subject line — Email messages only"
    )
    html: str | None = Field(
        default=None, description="HTML body of the message — Email messages only"
    )
    attachments: list[str] | None = Field(
        default=None, description="Array of publicly reachable attachment URLs"
    )
    email_from: str | None = Field(
        default=None, description="Sender email address — Email messages only"
    )
    email_to: str | None = Field(
        default=None,
        description=(
            "Recipient email address when it differs from the contact's primary "
            "email — Email messages only"
        ),
    )
    email_cc: list[str] | None = Field(
        default=None, description="Array of CC email addresses — Email messages only"
    )
    email_bcc: list[str] | None = Field(
        default=None, description="Array of BCC email addresses — Email messages only"
    )
    email_reply_mode: str | None = Field(
        default=None,
        description="Reply mode for email replies: reply or reply_all — Email only",
    )
    from_number: str | None = Field(
        default=None,
        description="Sender phone number — SMS, RCS and WhatsApp messages only",
    )
    to_number: str | None = Field(
        default=None,
        description="Recipient phone number — SMS, RCS and WhatsApp messages only",
    )
    appointment_id: str | None = Field(
        default=None, description="ID of the associated appointment"
    )
    reply_message_id: str | None = Field(
        default=None, description="ID of the message being replied to"
    )
    template_id: str | None = Field(default=None, description="ID of a message template")
    thread_id: str | None = Field(
        default=None,
        description=(
            "ID of the message thread; for email this is the message ID holding "
            "the whole thread"
        ),
    )
    scheduled_timestamp: int | None = Field(
        default=None,
        description="UTC timestamp in seconds at which the message should be sent",
    )
    conversation_provider_id: str | None = Field(
        default=None, description="ID of the conversation provider"
    )
    custom_subtype_id: str | None = Field(
        default=None,
        description="Custom subtype ID for unsubscribe preferences — Email only",
    )
    sub_type: dict[str, Any] | None = Field(
        default=None, description="Subtype object of the message being sent"
    )
    forward: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Email forwarding config with keys isForwarded, forwardWholeThread, "
            "messageId, emailMessageId, toEmail, recipientContactId"
        ),
    )
    status: str | None = Field(
        default=None,
        description="Message status: delivered, failed, pending or read",
    )
    uses_native_scheduling_ai: bool | None = Field(
        default=None,
        description="Whether the scheduled email uses native send-time AI",
    )
    optimization_period: str | None = Field(
        default=None,
        description="Send-time optimization window: 24h, 48h or 72h",
    )


@tool(args_schema=SendMessageInput)
@serialize_pydantic_return
async def send_message(
    auth_type: str,
    auth_data: dict[str, Any],
    message_type: str,
    contact_id: str,
    message: str | None = None,
    subject: str | None = None,
    html: str | None = None,
    attachments: list[str] | None = None,
    email_from: str | None = None,
    email_to: str | None = None,
    email_cc: list[str] | None = None,
    email_bcc: list[str] | None = None,
    email_reply_mode: str | None = None,
    from_number: str | None = None,
    to_number: str | None = None,
    appointment_id: str | None = None,
    reply_message_id: str | None = None,
    template_id: str | None = None,
    thread_id: str | None = None,
    scheduled_timestamp: int | None = None,
    conversation_provider_id: str | None = None,
    custom_subtype_id: str | None = None,
    sub_type: dict[str, Any] | None = None,
    forward: dict[str, Any] | None = None,
    status: str | None = None,
    uses_native_scheduling_ai: bool | None = None,
    optimization_period: str | None = None,
) -> SendMessageOutput:
    """Send an SMS, email, WhatsApp, Instagram or Facebook message to a contact."""
    # TODO (unverified): SendMessageBodyDto marks `subType` and `status`
    # required, but neither is meaningful on an outbound send and existing
    # clients omit both; exposed as optional here.
    body: dict[str, Any] = {
        "type": message_type,
        "contactId": contact_id,
        "message": message,
        "subject": subject,
        "html": html,
        "attachments": attachments,
        "emailFrom": email_from,
        "emailTo": email_to,
        "emailCc": email_cc,
        "emailBcc": email_bcc,
        "emailReplyMode": email_reply_mode,
        "fromNumber": from_number,
        "toNumber": to_number,
        "appointmentId": appointment_id,
        "replyMessageId": reply_message_id,
        "templateId": template_id,
        "threadId": thread_id,
        "scheduledTimestamp": scheduled_timestamp,
        "conversationProviderId": conversation_provider_id,
        "customSubtypeId": custom_subtype_id,
        "subType": sub_type,
        "forward": forward,
        "status": status,
        "usesNativeSchedulingAi": uses_native_scheduling_ai,
        "optimizationPeriod": optimization_period,
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/conversations/messages", json_body=body
    )
    if error is not None:
        return SendMessageOutput(success=False, error=error)
    result = _as_dict(payload)
    return SendMessageOutput(
        success=True,
        conversation_id=_as_str(result.get("conversationId")),
        message_id=_as_str(result.get("messageId")),
        message_ids=_as_str_list(result.get("messageIds")),
        email_message_id=_as_str(result.get("emailMessageId")),
        status=_as_str(result.get("status")),
        msg=_as_str(result.get("msg")),
        forward_data=_parse_message_forward(result.get("forwardData")),
    )


class CancelScheduledEmailMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    email_message_id: str = Field(
        description="The unique identifier of the scheduled email message to cancel"
    )


@tool(args_schema=CancelScheduledEmailMessageInput)
@serialize_pydantic_return
async def cancel_scheduled_email_message(
    auth_type: str,
    auth_data: dict[str, Any],
    email_message_id: str,
) -> CancelScheduledEmailMessageOutput:
    """Cancel a scheduled email message so it is never delivered."""
    path = f"/conversations/messages/email/{_seg(email_message_id)}/schedule"
    payload, error = await _request(auth_type, auth_data, "DELETE", path)
    if error is not None:
        return CancelScheduledEmailMessageOutput(success=False, error=error)
    result = _as_dict(payload)
    return CancelScheduledEmailMessageOutput(
        success=True,
        status_code=_as_int(result.get("status")),
        message=_as_str(result.get("message")),
    )


class GetEmailByIdInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    email_message_id: str = Field(
        description="The unique identifier of the email message to retrieve"
    )


@tool(args_schema=GetEmailByIdInput)
@serialize_pydantic_return
async def get_email_by_id(
    auth_type: str,
    auth_data: dict[str, Any],
    email_message_id: str,
) -> GetEmailByIdOutput:
    """Get one email message with its subject, body, recipients and attachments."""
    path = f"/conversations/messages/email/{_seg(email_message_id)}"
    payload, error = await _request(auth_type, auth_data, "GET", path)
    if error is not None:
        return GetEmailByIdOutput(success=False, error=error)
    return GetEmailByIdOutput(success=True, email=_parse_email_message(payload))


class ExportMessagesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    limit: int | None = Field(
        default=None,
        description="Maximum number of messages to include in one page of results",
    )
    cursor: str | None = Field(
        default=None,
        description="Cursor from a previous response used to fetch the next page",
    )
    sort_by: str | None = Field(
        default=None, description="Field to sort by: createdAt or updatedAt"
    )
    sort_order: str | None = Field(
        default=None, description="Sort order: asc or desc"
    )
    conversation_id: str | None = Field(
        default=None, description="Only export messages from this conversation"
    )
    contact_id: str | None = Field(
        default=None, description="Only export messages belonging to this contact"
    )
    channel: str | None = Field(
        default=None,
        description=(
            "Only export this channel: Call, SMS, Email, WhatsApp, Instagram or "
            "Facebook. Omit to include activity messages too"
        ),
    )
    start_date: str | None = Field(
        default=None, description="Only export messages created on or after this date"
    )
    end_date: str | None = Field(
        default=None, description="Only export messages created on or before this date"
    )


@tool(args_schema=ExportMessagesInput)
@serialize_pydantic_return
async def export_messages(
    auth_type: str,
    auth_data: dict[str, Any],
    limit: int | None = None,
    cursor: str | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
    conversation_id: str | None = None,
    contact_id: str | None = None,
    channel: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> ExportMessagesOutput:
    """Export the sub-account's messages page by page, with optional filters."""
    location_id = _location_id(auth_data)
    if not location_id:
        return ExportMessagesOutput(success=False, error=_MISSING_LOCATION)
    params: dict[str, Any] = {
        "locationId": location_id,
        "limit": limit,
        "cursor": cursor,
        "sortBy": sort_by,
        "sortOrder": sort_order,
        "conversationId": conversation_id,
        "contactId": contact_id,
        "channel": channel,
        "startDate": start_date,
        "endDate": end_date,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/conversations/messages/export", params=params
    )
    if error is not None:
        return ExportMessagesOutput(success=False, error=error)
    body = _as_dict(payload)
    return ExportMessagesOutput(
        success=True,
        messages=[_parse_message(item) for item in _as_dict_list(body.get("messages"))],
        next_cursor=_as_str(body.get("nextCursor")),
        total=_as_int(body.get("total")),
    )


class AddInboundMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_type: str = Field(
        description=(
            "Message type: SMS, RCS, Email, WhatsApp, GMB, IG, FB, Custom, "
            "WebChat, Live_Chat, Call, IVR_Call, Campaign_Call, "
            "Campaign_VoiceMail, TIKTOK, ALL_IN_ONE_CHAT or FORM_SUBMISSION"
        )
    )
    conversation_id: str | None = Field(
        default=None,
        description="Conversation ID; either this or contact_id is required",
    )
    contact_id: str | None = Field(
        default=None,
        description="Contact ID; either this or conversation_id is required",
    )
    conversation_provider_id: str | None = Field(
        default=None,
        description="Conversation provider ID; required for custom providers",
    )
    message: str | None = Field(default=None, description="Message body")
    html: str | None = Field(default=None, description="HTML body of the email")
    subject: str | None = Field(default=None, description="Subject of the email")
    email_from: str | None = Field(
        default=None,
        description=(
            "Sender email address; tied to the contact record and cannot be "
            "changed dynamically"
        ),
    )
    email_to: str | None = Field(
        default=None,
        description=(
            "Recipient email address; tied to the contact record and cannot be "
            "changed dynamically"
        ),
    )
    email_cc: list[str] | None = Field(
        default=None, description="List of email addresses to CC"
    )
    email_bcc: list[str] | None = Field(
        default=None, description="List of email addresses to BCC"
    )
    email_message_id: str | None = Field(
        default=None,
        description="Email message ID this message should be threaded under",
    )
    alt_id: str | None = Field(
        default=None, description="The external mail provider's message ID"
    )
    attachments: list[str] | None = Field(
        default=None, description="Array of attachment URLs"
    )
    direction: str | None = Field(
        default=None,
        description="Message direction: inbound or outbound. Defaults to outbound",
    )
    date: str | None = Field(
        default=None, description="ISO 8601 date-time of the inbound message"
    )
    call: dict[str, Any] | None = Field(
        default=None,
        description="Call details with keys to, from and status — Call types only",
    )


@tool(args_schema=AddInboundMessageInput)
@serialize_pydantic_return
async def add_inbound_message(
    auth_type: str,
    auth_data: dict[str, Any],
    message_type: str,
    conversation_id: str | None = None,
    contact_id: str | None = None,
    conversation_provider_id: str | None = None,
    message: str | None = None,
    html: str | None = None,
    subject: str | None = None,
    email_from: str | None = None,
    email_to: str | None = None,
    email_cc: list[str] | None = None,
    email_bcc: list[str] | None = None,
    email_message_id: str | None = None,
    alt_id: str | None = None,
    attachments: list[str] | None = None,
    direction: str | None = None,
    date: str | None = None,
    call: dict[str, Any] | None = None,
) -> AddInboundMessageOutput:
    """Record a message received from a contact into a conversation."""
    # TODO (unverified): ProcessMessageBodyDto marks conversationId, contactId
    # and conversationProviderId all required, yet the vendor's own action
    # catalogue documents conversationId/contactId as "either one" and the
    # provider ID as custom-provider-only; all three stay optional here.
    # TODO (unverified): the same schema types `direction` as an object with a
    # default of "outbound" and an example of ["outbound", "inbound"]; it is
    # sent as a plain string.
    body: dict[str, Any] = {
        "type": message_type,
        "conversationId": conversation_id,
        "contactId": contact_id,
        "conversationProviderId": conversation_provider_id,
        "message": message,
        "html": html,
        "subject": subject,
        "emailFrom": email_from,
        "emailTo": email_to,
        "emailCc": email_cc,
        "emailBcc": email_bcc,
        "emailMessageId": email_message_id,
        "altId": alt_id,
        "attachments": attachments,
        "direction": direction,
        "date": date,
        "call": call,
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/conversations/messages/inbound", json_body=body
    )
    if error is not None:
        return AddInboundMessageOutput(success=False, error=error)
    result = _as_dict(payload)
    return AddInboundMessageOutput(
        success=True,
        conversation_id=_as_str(result.get("conversationId")),
        message_id=_as_str(result.get("messageId")),
        email_message_id=_as_str(result.get("emailMessageId")),
        contact_id=_as_str(result.get("contactId")),
        message=_as_str(result.get("message")),
        date_added=_as_str(result.get("dateAdded")),
    )


class AddOutboundMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    conversation_id: str = Field(
        description="The conversation the outbound call belongs to"
    )
    conversation_provider_id: str = Field(description="Conversation provider ID")
    message_type: str | None = Field(
        default="Call",
        description='Message type; the endpoint only accepts "Call"',
    )
    call: dict[str, Any] | None = Field(
        default=None, description="Call details with keys to, from and status"
    )
    attachments: list[str] | None = Field(
        default=None, description="Array of attachment URLs such as a recording"
    )
    alt_id: str | None = Field(
        default=None, description="The external provider's message ID"
    )
    date: str | None = Field(
        default=None, description="ISO 8601 date-time of the outbound call"
    )


@tool(args_schema=AddOutboundMessageInput)
@serialize_pydantic_return
async def add_outbound_message(
    auth_type: str,
    auth_data: dict[str, Any],
    conversation_id: str,
    conversation_provider_id: str,
    message_type: str | None = None,
    call: dict[str, Any] | None = None,
    attachments: list[str] | None = None,
    alt_id: str | None = None,
    date: str | None = None,
) -> AddOutboundMessageOutput:
    """Record an externally placed outbound call against a conversation."""
    body: dict[str, Any] = {
        # ProcessOutboundMessageBodyDto's `type` enum has exactly one member.
        "type": message_type or "Call",
        "conversationId": conversation_id,
        "conversationProviderId": conversation_provider_id,
        "call": call,
        "attachments": attachments,
        "altId": alt_id,
        "date": date,
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/conversations/messages/outbound", json_body=body
    )
    if error is not None:
        return AddOutboundMessageOutput(success=False, error=error)
    result = _as_dict(payload)
    return AddOutboundMessageOutput(
        success=True,
        conversation_id=_as_str(result.get("conversationId")),
        message_id=_as_str(result.get("messageId")),
        email_message_id=_as_str(result.get("emailMessageId")),
        contact_id=_as_str(result.get("contactId")),
        message=_as_str(result.get("message")),
        date_added=_as_str(result.get("dateAdded")),
    )


class SendReviewReplyInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    conversation_id: str = Field(
        description="The review conversation to reply to; it must carry a reviewId"
    )
    message: str = Field(description="Text of the review reply")


@tool(args_schema=SendReviewReplyInput)
@serialize_pydantic_return
async def send_review_reply(
    auth_type: str,
    auth_data: dict[str, Any],
    conversation_id: str,
    message: str,
) -> SendReviewReplyOutput:
    """Reply to a Google My Business customer review."""
    location_id = _location_id(auth_data)
    if not location_id:
        return SendReviewReplyOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "conversationId": conversation_id,
        "locationId": location_id,
        "message": message,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/conversations/messages/review-reply",
        json_body=body,
    )
    if error is not None:
        return SendReviewReplyOutput(success=False, error=error)
    result = _as_dict(payload)
    return SendReviewReplyOutput(
        success=True,
        conversation_id=_as_str(result.get("conversationId")),
        message_id=_as_str(result.get("messageId")),
        message_ids=_as_str_list(result.get("messageIds")),
        email_message_id=_as_str(result.get("emailMessageId")),
        status=_as_str(result.get("status")),
        msg=_as_str(result.get("msg")),
    )


class CompleteMessageFileUploadInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    upload_id: str = Field(description="Upload ID returned by the initiate step")
    file_path: str = Field(description="File path returned by the initiate step")
    conversation_id: str = Field(description="Conversation the file belongs to")
    filename: str = Field(
        description="Original filename; it becomes the uploaded_files response key"
    )


@tool(args_schema=CompleteMessageFileUploadInput)
@serialize_pydantic_return
async def complete_message_file_upload(
    auth_type: str,
    auth_data: dict[str, Any],
    upload_id: str,
    file_path: str,
    conversation_id: str,
    filename: str,
) -> CompleteMessageFileUploadOutput:
    """Finalize a message file upload and get the file's public URL.

    Call this only after the file bytes have been PUT to the signed URL that
    initiate_message_file_upload returned; the binary transfer itself is the
    caller's responsibility.
    """
    location_id = _location_id(auth_data)
    if not location_id:
        return CompleteMessageFileUploadOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "uploadId": upload_id,
        "filePath": file_path,
        "locationId": location_id,
        "conversationId": conversation_id,
        "filename": filename,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/conversations/messages/upload/complete",
        json_body=body,
    )
    if error is not None:
        return CompleteMessageFileUploadOutput(success=False, error=error)
    result = _as_dict(payload)
    uploaded = _as_dict(result.get("uploadedFiles"))
    metadata = _as_dict(result.get("metadata"))
    return CompleteMessageFileUploadOutput(
        success=True,
        uploaded_files=uploaded or None,
        metadata=metadata or None,
    )


class InitiateMessageFileUploadInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    conversation_id: str = Field(description="Conversation the file belongs to")
    filename: str = Field(description="Original filename including its extension")
    content_type: str = Field(description="MIME type of the file, e.g. video/mp4")
    channel: str = Field(
        description=(
            "Channel the file is for; WHATSAPP raises the size limit to 100MB, "
            "everything else is capped at 5MB"
        )
    )
    file_size: int | None = Field(
        default=None, description="File size in bytes, for pre-validation"
    )


@tool(args_schema=InitiateMessageFileUploadInput)
@serialize_pydantic_return
async def initiate_message_file_upload(
    auth_type: str,
    auth_data: dict[str, Any],
    conversation_id: str,
    filename: str,
    content_type: str,
    channel: str,
    file_size: int | None = None,
) -> InitiateMessageFileUploadOutput:
    """Request a signed Google Cloud Storage URL for a message attachment.

    Returns an upload URL valid for 15 minutes. The caller PUTs the file bytes
    to that URL themselves, then calls complete_message_file_upload.
    """
    location_id = _location_id(auth_data)
    if not location_id:
        return InitiateMessageFileUploadOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "locationId": location_id,
        "conversationId": conversation_id,
        "filename": filename,
        "contentType": content_type,
        "channel": channel,
        "fileSize": file_size,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/conversations/messages/upload/initiate",
        json_body=body,
    )
    if error is not None:
        return InitiateMessageFileUploadOutput(success=False, error=error)
    result = _as_dict(payload)
    return InitiateMessageFileUploadOutput(
        success=True,
        upload_url=_as_str(result.get("uploadUrl")),
        upload_id=_as_str(result.get("uploadId")),
        file_path=_as_str(result.get("filePath")),
        expires_at=_as_int(result.get("expiresAt")),
        max_file_size=_as_int(result.get("maxFileSize")),
    )


class GetMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_id: str = Field(description="The unique identifier of the message")


@tool(args_schema=GetMessageInput)
@serialize_pydantic_return
async def get_message(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
) -> GetMessageOutput:
    """Get one conversation message by its ID."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/conversations/messages/{_seg(message_id)}"
    )
    if error is not None:
        return GetMessageOutput(success=False, error=error)
    return GetMessageOutput(success=True, message=_parse_message(payload))


class AddMessageAttachmentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_id: str = Field(description="The message to set attachments on")
    attachments: list[str] = Field(
        description=(
            "Attachment URLs to set on the message, replacing any existing ones. "
            "Maximum 5"
        )
    )


@tool(args_schema=AddMessageAttachmentsInput)
@serialize_pydantic_return
async def add_message_attachments(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
    attachments: list[str],
) -> AddMessageAttachmentsOutput:
    """Replace the attachment URLs on an existing call message.

    Only supported for TYPE_CUSTOM_CALL and for TYPE_CALL with the
    EXTERNAL_CALL subtype.
    """
    body: dict[str, Any] = {"attachments": attachments}
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/conversations/messages/{_seg(message_id)}/attachments",
        json_body=body,
        send_body=True,
    )
    if error is not None:
        return AddMessageAttachmentsOutput(success=False, error=error)
    # TODO (unverified): the published conversations API spec declares no 200 response body
    # for this endpoint, so whatever arrives is surfaced verbatim.
    return AddMessageAttachmentsOutput(success=True, data=_as_dict(payload) or None)


class CancelScheduledMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_id: str = Field(
        description="The unique identifier of the scheduled message to cancel"
    )


@tool(args_schema=CancelScheduledMessageInput)
@serialize_pydantic_return
async def cancel_scheduled_message(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
) -> CancelScheduledMessageOutput:
    """Cancel a scheduled message so it is never delivered."""
    path = f"/conversations/messages/{_seg(message_id)}/schedule"
    payload, error = await _request(auth_type, auth_data, "DELETE", path)
    if error is not None:
        return CancelScheduledMessageOutput(success=False, error=error)
    result = _as_dict(payload)
    return CancelScheduledMessageOutput(
        success=True,
        status_code=_as_int(result.get("status")),
        message=_as_str(result.get("message")),
    )


class UpdateMessageStatusInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_id: str = Field(description="The message whose status should change")
    status: str = Field(
        description="New message status: delivered, failed, pending or read"
    )
    email_message_id: str | None = Field(
        default=None, description="Email message ID the status applies to"
    )
    recipients: list[str] | None = Field(
        default=None,
        description="Additional email recipients the delivery status applies to",
    )
    provider_error: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Error reported by the conversation provider, with keys code, type "
            "and message"
        ),
    )


@tool(args_schema=UpdateMessageStatusInput)
@serialize_pydantic_return
async def update_message_status(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
    status: str,
    email_message_id: str | None = None,
    recipients: list[str] | None = None,
    provider_error: dict[str, Any] | None = None,
) -> UpdateMessageStatusOutput:
    """Update the delivery status of a message sent through a conversation provider."""
    body: dict[str, Any] = {
        "status": status,
        "emailMessageId": email_message_id,
        "recipients": recipients,
        "error": provider_error,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/conversations/messages/{_seg(message_id)}/status",
        json_body=body,
    )
    if error is not None:
        return UpdateMessageStatusOutput(success=False, error=error)
    result = _as_dict(payload)
    return UpdateMessageStatusOutput(
        success=True,
        conversation_id=_as_str(result.get("conversationId")),
        message_id=_as_str(result.get("messageId")),
        message_ids=_as_str_list(result.get("messageIds")),
        email_message_id=_as_str(result.get("emailMessageId")),
        status=_as_str(result.get("status")),
        msg=_as_str(result.get("msg")),
    )


class ListCustomSubtypesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


@tool(args_schema=ListCustomSubtypesInput)
@serialize_pydantic_return
async def list_custom_subtypes(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListCustomSubtypesOutput:
    """List the sub-account's custom message subtypes used for subscriptions."""
    location_id = _location_id(auth_data)
    if not location_id:
        return ListCustomSubtypesOutput(success=False, error=_MISSING_LOCATION)
    payload, error = await _request(
        auth_type,
        auth_data,
        "GET",
        "/conversations/preferences/custom-subtypes",
        params={"locationId": location_id},
    )
    if error is not None:
        return ListCustomSubtypesOutput(success=False, error=error)
    # TODO (unverified): the published conversations API spec declares no 200 response body,
    # so neither the wrapper key nor the item shape can be modelled; the array
    # form and the object form are both surfaced verbatim.
    return ListCustomSubtypesOutput(
        success=True,
        custom_subtypes=_as_dict_list(payload),
        data=_as_dict(payload) or None,
    )


class CreateCustomSubtypeInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="Name of the custom subtype, max 100 characters")
    channel: str = Field(description="Communication channel: email or sms")
    language: str = Field(description="Language code, for example en")
    description: str | None = Field(
        default=None,
        description="Description of the custom subtype, max 100 characters",
    )


@tool(args_schema=CreateCustomSubtypeInput)
@serialize_pydantic_return
async def create_custom_subtype(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    channel: str,
    language: str,
    description: str | None = None,
) -> CreateCustomSubtypeOutput:
    """Create a custom message subtype contacts can subscribe to.

    Requires an agency or account admin role.
    """
    location_id = _location_id(auth_data)
    if not location_id:
        return CreateCustomSubtypeOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "name": name,
        "channel": channel,
        "language": language,
        "description": description,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/conversations/preferences/custom-subtypes",
        params={"locationId": location_id},
        json_body=body,
    )
    if error is not None:
        return CreateCustomSubtypeOutput(success=False, error=error)
    # TODO (unverified): the published conversations API spec declares no 200/201 response
    # body for this endpoint, so whatever arrives is surfaced verbatim.
    return CreateCustomSubtypeOutput(success=True, data=_as_dict(payload) or None)


class UpdateCustomSubtypeInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    custom_subtype_id: str = Field(
        description="The unique identifier of the custom subtype to update"
    )
    name: str | None = Field(
        default=None, description="New name for the subtype, max 100 characters"
    )
    description: str | None = Field(
        default=None, description="New description for the subtype, max 100 characters"
    )
    archived: bool | None = Field(
        default=None, description="Whether the custom subtype is archived"
    )
    resubscription_legal_form_id: str | None = Field(
        default=None,
        description="Resubscription legal form ID, optional when archiving",
    )


@tool(args_schema=UpdateCustomSubtypeInput)
@serialize_pydantic_return
async def update_custom_subtype(
    auth_type: str,
    auth_data: dict[str, Any],
    custom_subtype_id: str,
    name: str | None = None,
    description: str | None = None,
    archived: bool | None = None,
    resubscription_legal_form_id: str | None = None,
) -> UpdateCustomSubtypeOutput:
    """Rename or archive a custom message subtype.

    Requires an agency or account admin role.
    """
    location_id = _location_id(auth_data)
    if not location_id:
        return UpdateCustomSubtypeOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "name": name,
        "description": description,
        "archived": archived,
        "resubscription_legal_form_id": resubscription_legal_form_id,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/conversations/preferences/custom-subtypes/{_seg(custom_subtype_id)}",
        params={"locationId": location_id},
        json_body=body,
        send_body=True,
    )
    if error is not None:
        return UpdateCustomSubtypeOutput(success=False, error=error)
    # TODO (unverified): the published conversations API spec declares no 200 response body
    # for this endpoint, so whatever arrives is surfaced verbatim.
    return UpdateCustomSubtypeOutput(success=True, data=_as_dict(payload) or None)


class GetContactUnsubscriptionStatusInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="The contact whose subscriptions to read")
    email: str | None = Field(
        default=None,
        description="One email address to check; omit to get every email on the contact",
    )


@tool(args_schema=GetContactUnsubscriptionStatusInput)
@serialize_pydantic_return
async def get_contact_unsubscription_status(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    email: str | None = None,
) -> GetContactUnsubscriptionStatusOutput:
    """Read a contact's email subscription and unsubscribe statuses."""
    location_id = _location_id(auth_data)
    if not location_id:
        return GetContactUnsubscriptionStatusOutput(
            success=False, error=_MISSING_LOCATION
        )
    params: dict[str, Any] = {
        "locationId": location_id,
        "contactId": contact_id,
        "email": email,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "GET",
        "/conversations/preferences/unsubscriptions/status",
        params=params,
    )
    if error is not None:
        return GetContactUnsubscriptionStatusOutput(success=False, error=error)
    # TODO (unverified): the published conversations API spec declares no 200 response body,
    # so neither the wrapper key nor the item shape can be modelled; the array
    # form and the object form are both surfaced verbatim.
    return GetContactUnsubscriptionStatusOutput(
        success=True,
        subscriptions=_as_dict_list(payload),
        data=_as_dict(payload) or None,
    )


class UpdateSubscriptionPreferenceInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="The contact whose subscription is changing")
    email: str = Field(description="Email address the change applies to")
    subscription_type: str = Field(
        description="Type of change: default, custom or resub_all"
    )
    subscription_status: str = Field(
        description="Resulting status: subscribed or unsubscribed"
    )
    subtype_name: str | None = Field(
        default=None,
        description='Subscription name for default types, e.g. "One on One"',
    )
    subtype_id: str | None = Field(
        default=None, description="Custom subscription type ID, for custom types"
    )
    legal_reason: str | None = Field(
        default=None,
        description="Legal reason; required for resubscribe and resub_all changes",
    )
    legal_description: str | None = Field(
        default=None, description="Supporting detail for the legal reason"
    )


@tool(args_schema=UpdateSubscriptionPreferenceInput)
@serialize_pydantic_return
async def update_subscription_preference(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    email: str,
    subscription_type: str,
    subscription_status: str,
    subtype_name: str | None = None,
    subtype_id: str | None = None,
    legal_reason: str | None = None,
    legal_description: str | None = None,
) -> UpdateSubscriptionPreferenceOutput:
    """Subscribe or unsubscribe a contact's email address on behalf of an agent."""
    location_id = _location_id(auth_data)
    if not location_id:
        return UpdateSubscriptionPreferenceOutput(
            success=False, error=_MISSING_LOCATION
        )
    action: dict[str, Any] = {
        "type": subscription_type,
        "subtype_status": subscription_status,
        "subtype_name": subtype_name,
        "subtype_id": subtype_id,
    }
    body: dict[str, Any] = {
        "locationId": location_id,
        "contactId": contact_id,
        "email": email,
        "subscription_action": {k: v for k, v in action.items() if v is not None},
        "legal_reason": legal_reason,
        "legal_description": legal_description,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/conversations/preferences/unsubscriptions/user-change",
        json_body=body,
    )
    if error is not None:
        return UpdateSubscriptionPreferenceOutput(success=False, error=error)
    # TODO (unverified): the published conversations API spec declares no 200/201 response
    # body for this endpoint, so whatever arrives is surfaced verbatim.
    return UpdateSubscriptionPreferenceOutput(
        success=True, data=_as_dict(payload) or None
    )


class LiveChatAgentTypingInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    conversation_id: str = Field(description="The live-chat conversation ID")
    visitor_id: str = Field(
        description="Unique ID assigned to the live-chat visitor being replied to"
    )
    is_typing: str = Field(description='Typing status, "true" or "false"')


@tool(args_schema=LiveChatAgentTypingInput)
@serialize_pydantic_return
async def live_chat_agent_typing(
    auth_type: str,
    auth_data: dict[str, Any],
    conversation_id: str,
    visitor_id: str,
    is_typing: str,
) -> LiveChatAgentTypingOutput:
    """Show or hide the agent typing indicator in a live-chat conversation."""
    location_id = _location_id(auth_data)
    if not location_id:
        return LiveChatAgentTypingOutput(success=False, error=_MISSING_LOCATION)
    # TODO (unverified): UserTypingBody types `isTyping` as a string while its
    # own example is the boolean true; the declared string type is used.
    body: dict[str, Any] = {
        "locationId": location_id,
        "conversationId": conversation_id,
        "visitorId": visitor_id,
        "isTyping": is_typing,
    }
    _, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/conversations/providers/live-chat/typing",
        json_body=body,
    )
    if error is not None:
        return LiveChatAgentTypingOutput(success=False, error=error)
    return LiveChatAgentTypingOutput(success=True)


class SearchConversationsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    query: str | None = Field(default=None, description="Free-text search string")
    contact_id: str | None = Field(
        default=None, description="Only return conversations with this contact"
    )
    conversation_id: str | None = Field(
        default=None, description="Only return the conversation with this ID"
    )
    assigned_to: str | None = Field(
        default=None,
        description=(
            'Comma-separated user IDs the conversations are assigned to; use '
            '"unassigned" for conversations with no owner'
        ),
    )
    followers: str | None = Field(
        default=None, description="Comma-separated user IDs of followers to filter by"
    )
    mentions: str | None = Field(
        default=None, description="Comma-separated user IDs mentioned in the thread"
    )
    status: str | None = Field(
        default=None,
        description="Conversation status: all, read, unread, starred or recents",
    )
    sort: str | None = Field(default=None, description="Sort direction: asc or desc")
    sort_by: str | None = Field(
        default=None,
        description=(
            "Sort field: last_manual_message_date, last_message_date, "
            "score_profile, overdue_at or due_at"
        ),
    )
    limit: int | None = Field(
        default=None, description="Number of conversations to return. Default is 20"
    )
    start_after_date: str | None = Field(
        default=None,
        description="Resume after this sort value, taken from the last document",
    )
    last_message_type: str | None = Field(
        default=None,
        description="Filter by the last message type, e.g. TYPE_SMS or TYPE_EMAIL",
    )
    last_message_action: str | None = Field(
        default=None,
        description="Action of the last outbound message: automated or manual",
    )
    last_message_direction: str | None = Field(
        default=None,
        description="Direction of the last message: inbound or outbound",
    )
    score_profile: str | None = Field(
        default=None,
        description="Score profile ID to filter on, with score_profile_min/max",
    )
    sort_score_profile: str | None = Field(
        default=None, description="Score profile ID that score_profile sorting uses"
    )
    score_profile_min: int | None = Field(
        default=None, description="Minimum score profile value"
    )
    score_profile_max: int | None = Field(
        default=None, description="Maximum score profile value"
    )
    start_date: int | None = Field(
        default=None,
        description="Only conversations added at or after this Unix timestamp in ms",
    )
    end_date: int | None = Field(
        default=None,
        description="Only conversations added at or before this Unix timestamp in ms",
    )


@tool(args_schema=SearchConversationsInput)
@serialize_pydantic_return
async def search_conversations(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str | None = None,
    contact_id: str | None = None,
    conversation_id: str | None = None,
    assigned_to: str | None = None,
    followers: str | None = None,
    mentions: str | None = None,
    status: str | None = None,
    sort: str | None = None,
    sort_by: str | None = None,
    limit: int | None = None,
    start_after_date: str | None = None,
    last_message_type: str | None = None,
    last_message_action: str | None = None,
    last_message_direction: str | None = None,
    score_profile: str | None = None,
    sort_score_profile: str | None = None,
    score_profile_min: int | None = None,
    score_profile_max: int | None = None,
    start_date: int | None = None,
    end_date: int | None = None,
) -> SearchConversationsOutput:
    """Search the sub-account's conversations by text, contact, owner or status."""
    location_id = _location_id(auth_data)
    if not location_id:
        return SearchConversationsOutput(success=False, error=_MISSING_LOCATION)
    # TODO (unverified): the published conversations API spec types `startAfterDate` as
    # "any"; it is passed through as an opaque string.
    params: dict[str, Any] = {
        "locationId": location_id,
        "query": query,
        "contactId": contact_id,
        "id": conversation_id,
        "assignedTo": assigned_to,
        "followers": followers,
        "mentions": mentions,
        "status": status,
        "sort": sort,
        "sortBy": sort_by,
        "limit": limit,
        "startAfterDate": start_after_date,
        "lastMessageType": last_message_type,
        "lastMessageAction": last_message_action,
        "lastMessageDirection": last_message_direction,
        "scoreProfile": score_profile,
        "sortScoreProfile": sort_score_profile,
        "scoreProfileMin": score_profile_min,
        "scoreProfileMax": score_profile_max,
        "startDate": start_date,
        "endDate": end_date,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/conversations/search", params=params
    )
    if error is not None:
        return SearchConversationsOutput(success=False, error=error)
    body = _as_dict(payload)
    return SearchConversationsOutput(
        success=True,
        conversations=[
            _parse_conversation(item) for item in _as_dict_list(body.get("conversations"))
        ],
        total=_as_int(body.get("total")),
    )


class GetConversationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    conversation_id: str = Field(
        description="The unique identifier of the conversation to retrieve"
    )


@tool(args_schema=GetConversationInput)
@serialize_pydantic_return
async def get_conversation(
    auth_type: str,
    auth_data: dict[str, Any],
    conversation_id: str,
) -> GetConversationOutput:
    """Get one conversation with its contact, owner, unread count and flags."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/conversations/{_seg(conversation_id)}"
    )
    if error is not None:
        return GetConversationOutput(success=False, error=error)
    return GetConversationOutput(success=True, conversation=_parse_conversation(payload))


class UpdateConversationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    conversation_id: str = Field(
        description="The unique identifier of the conversation to update"
    )
    unread_count: int | None = Field(
        default=None, description="Count of unread messages in the conversation"
    )
    starred: bool | None = Field(
        default=None, description="Whether the conversation is starred"
    )
    feedback: dict[str, Any] | None = Field(
        default=None, description="Feedback object to store on the conversation"
    )


@tool(args_schema=UpdateConversationInput)
@serialize_pydantic_return
async def update_conversation(
    auth_type: str,
    auth_data: dict[str, Any],
    conversation_id: str,
    unread_count: int | None = None,
    starred: bool | None = None,
    feedback: dict[str, Any] | None = None,
) -> UpdateConversationOutput:
    """Star a conversation, change its unread count, or attach feedback to it."""
    location_id = _location_id(auth_data)
    if not location_id:
        return UpdateConversationOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "locationId": location_id,
        "unreadCount": unread_count,
        "starred": starred,
        "feedback": feedback,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/conversations/{_seg(conversation_id)}",
        json_body=body,
    )
    if error is not None:
        return UpdateConversationOutput(success=False, error=error)
    result = _as_dict(payload)
    return UpdateConversationOutput(
        success=True,
        conversation=_parse_conversation(result.get("conversation")),
    )


class DeleteConversationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    conversation_id: str = Field(
        description="The unique identifier of the conversation to delete"
    )


@tool(args_schema=DeleteConversationInput)
@serialize_pydantic_return
async def delete_conversation(
    auth_type: str,
    auth_data: dict[str, Any],
    conversation_id: str,
) -> DeleteConversationOutput:
    """Delete a conversation. This cannot be undone."""
    _, error = await _request(
        auth_type, auth_data, "DELETE", f"/conversations/{_seg(conversation_id)}"
    )
    if error is not None:
        return DeleteConversationOutput(success=False, error=error)
    return DeleteConversationOutput(success=True)


class ListConversationMessagesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    conversation_id: str = Field(
        description="The conversation whose messages should be listed"
    )
    limit: int | None = Field(
        default=None, description="Number of messages to fetch. Default is 20"
    )
    last_message_id: str | None = Field(
        default=None,
        description="ID of the last message already seen, used to page forward",
    )
    message_types: str | None = Field(
        default=None,
        description=(
            "Comma-separated message types to include, e.g. TYPE_SMS,TYPE_EMAIL"
        ),
    )


@tool(args_schema=ListConversationMessagesInput)
@serialize_pydantic_return
async def list_conversation_messages(
    auth_type: str,
    auth_data: dict[str, Any],
    conversation_id: str,
    limit: int | None = None,
    last_message_id: str | None = None,
    message_types: str | None = None,
) -> ListConversationMessagesOutput:
    """List the messages in a conversation, newest first, with paging support."""
    params: dict[str, Any] = {
        "limit": limit,
        "lastMessageId": last_message_id,
        "type": message_types,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "GET",
        f"/conversations/{_seg(conversation_id)}/messages",
        params=params,
    )
    if error is not None:
        return ListConversationMessagesOutput(success=False, error=error)
    body = _as_dict(payload)
    return ListConversationMessagesOutput(
        success=True,
        messages=[_parse_message(item) for item in _as_dict_list(body.get("messages"))],
        last_message_id=_as_str(body.get("lastMessageId")),
        next_page=_as_bool(body.get("nextPage")),
    )


# --- Email builder ----------------------------------------------------------


class CreateEmailTemplateInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    template_type: str = Field(
        description="Template type: html, folder, import, builder or blank"
    )
    name: str | None = Field(default=None, description="Name of the new template")
    title: str | None = Field(default=None, description="Title of the new template")
    parent_id: str | None = Field(
        default=None, description="ID of the folder the template belongs to"
    )
    builder_version: str | None = Field(
        default=None, description='Email builder version, "1" or "2". Defaults to 2'
    )
    import_provider: str | None = Field(
        default=None,
        description=(
            "Provider to import from: mailchimp, active_campaign or kajabi. "
            'Only used when template_type is "import"'
        ),
    )
    import_url: str | None = Field(
        default=None, description="URL to import the template from"
    )
    template_data_url: str | None = Field(
        default=None, description="URL of the template data to seed the template with"
    )
    template_source: str | None = Field(
        default=None, description="Source of the template, e.g. template_library"
    )
    is_plain_text: bool | None = Field(
        default=None, description="Whether the template is plain text"
    )
    updated_by: str | None = Field(
        default=None, description="ID of the user creating the template"
    )


@tool(args_schema=CreateEmailTemplateInput)
@serialize_pydantic_return
async def create_email_template(
    auth_type: str,
    auth_data: dict[str, Any],
    template_type: str,
    name: str | None = None,
    title: str | None = None,
    parent_id: str | None = None,
    builder_version: str | None = None,
    import_provider: str | None = None,
    import_url: str | None = None,
    template_data_url: str | None = None,
    template_source: str | None = None,
    is_plain_text: bool | None = None,
    updated_by: str | None = None,
) -> CreateEmailTemplateOutput:
    """Create an email-builder template or template folder in the sub-account."""
    location_id = _location_id(auth_data)
    if not location_id:
        return CreateEmailTemplateOutput(success=False, error=_MISSING_LOCATION)
    # TODO (unverified): CreateBuilderDto lists `importProvider` as required,
    # but it is only meaningful when type is "import"; kept optional.
    body: dict[str, Any] = {
        "locationId": location_id,
        "type": template_type,
        "name": name,
        "title": title,
        "parentId": parent_id,
        "builderVersion": builder_version,
        "importProvider": import_provider,
        "importURL": import_url,
        "templateDataUrl": template_data_url,
        "templateSource": template_source,
        "isPlainText": is_plain_text,
        "updatedBy": updated_by,
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/emails/builder", json_body=body
    )
    if error is not None:
        return CreateEmailTemplateOutput(success=False, error=error)
    result = _as_dict(payload)
    return CreateEmailTemplateOutput(
        success=True,
        template_id=_as_str(result.get("redirect")),
        trace_id=_as_str(result.get("traceId")),
    )


class ListEmailTemplatesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    limit: int | None = Field(
        default=None, description="Maximum number of templates to return"
    )
    offset: int | None = Field(
        default=None, description="Number of templates to skip for pagination"
    )
    search: str | None = Field(
        default=None, description="Free-text search across template names"
    )
    name: str | None = Field(default=None, description="Filter templates by name")
    parent_id: str | None = Field(
        default=None, description="Only templates inside this folder"
    )
    origin_id: str | None = Field(
        default=None, description="Filter templates by their origin ID"
    )
    builder_version: str | None = Field(
        default=None, description='Filter by email builder version, "1" or "2"'
    )
    sort_by_date: str | None = Field(
        default=None, description="Sort direction by date, asc or desc"
    )
    archived: bool | None = Field(
        default=None, description="Whether to return archived templates"
    )
    templates_only: bool | None = Field(
        default=None, description="Return only templates, excluding folders"
    )


@tool(args_schema=ListEmailTemplatesInput)
@serialize_pydantic_return
async def list_email_templates(
    auth_type: str,
    auth_data: dict[str, Any],
    limit: int | None = None,
    offset: int | None = None,
    search: str | None = None,
    name: str | None = None,
    parent_id: str | None = None,
    origin_id: str | None = None,
    builder_version: str | None = None,
    sort_by_date: str | None = None,
    archived: bool | None = None,
    templates_only: bool | None = None,
) -> ListEmailTemplatesOutput:
    """List the email-builder templates and folders in the sub-account."""
    location_id = _location_id(auth_data)
    if not location_id:
        return ListEmailTemplatesOutput(success=False, error=_MISSING_LOCATION)
    params: dict[str, Any] = {
        "locationId": location_id,
        "limit": limit,
        "offset": offset,
        "search": search,
        "name": name,
        "parentId": parent_id,
        "originId": origin_id,
        "builderVersion": builder_version,
        "sortByDate": sort_by_date,
        "archived": archived,
        "templatesOnly": templates_only,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/emails/builder", params=params
    )
    if error is not None:
        return ListEmailTemplatesOutput(success=False, error=error)
    # TODO (unverified): the published email API spec declares the 200 body
    # of this plural endpoint as a single FetchBuilderSuccesfulResponseDto
    # object. The bare array is read first; the "templates" wrapper that
    # existing clients expect is the fallback.
    items = _as_dict_list(payload)
    if not items:
        items = _as_dict_list(_as_dict(payload).get("templates"))
    return ListEmailTemplatesOutput(
        success=True,
        templates=[_parse_email_template(item) for item in items],
    )


class UpdateEmailTemplateInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    template_id: str = Field(
        description="The unique identifier of the email template to update"
    )
    updated_by: str = Field(description="ID of the user making the change")
    html: str = Field(description="HTML body of the template")
    editor_type: str = Field(description="Editor the template uses: html or builder")
    dnd: dict[str, Any] = Field(
        description=(
            "Drag-and-drop builder document with keys elements, attrs and "
            "templateSettings"
        )
    )
    preview_text: str | None = Field(
        default=None, description="Preview text shown in the inbox"
    )
    is_plain_text: bool | None = Field(
        default=None, description="Whether the template is plain text"
    )


@tool(args_schema=UpdateEmailTemplateInput)
@serialize_pydantic_return
async def update_email_template(
    auth_type: str,
    auth_data: dict[str, Any],
    template_id: str,
    updated_by: str,
    html: str,
    editor_type: str,
    dnd: dict[str, Any],
    preview_text: str | None = None,
    is_plain_text: bool | None = None,
) -> UpdateEmailTemplateOutput:
    """Save new content onto an existing email-builder template."""
    location_id = _location_id(auth_data)
    if not location_id:
        return UpdateEmailTemplateOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "locationId": location_id,
        "templateId": template_id,
        "updatedBy": updated_by,
        "dnd": dnd,
        "html": html,
        "editorType": editor_type,
        "previewText": preview_text,
        "isPlainText": is_plain_text,
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/emails/builder/data", json_body=body
    )
    if error is not None:
        return UpdateEmailTemplateOutput(success=False, error=error)
    result = _as_dict(payload)
    return UpdateEmailTemplateOutput(
        success=True,
        ok=_as_str(result.get("ok")),
        trace_id=_as_str(result.get("traceId")),
        preview_url=_as_str(result.get("previewUrl")),
        template_download_url=_as_str(result.get("templateDownloadUrl")),
    )


class DeleteEmailTemplateInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    template_id: str = Field(
        description="The unique identifier of the email template to delete"
    )


@tool(args_schema=DeleteEmailTemplateInput)
@serialize_pydantic_return
async def delete_email_template(
    auth_type: str,
    auth_data: dict[str, Any],
    template_id: str,
) -> DeleteEmailTemplateOutput:
    """Permanently delete an email-builder template. This cannot be undone."""
    location_id = _location_id(auth_data)
    if not location_id:
        return DeleteEmailTemplateOutput(success=False, error=_MISSING_LOCATION)
    path = f"/emails/builder/{_seg(location_id)}/{_seg(template_id)}"
    payload, error = await _request(auth_type, auth_data, "DELETE", path)
    if error is not None:
        return DeleteEmailTemplateOutput(success=False, error=error)
    result = _as_dict(payload)
    return DeleteEmailTemplateOutput(
        success=True,
        ok=_as_str(result.get("ok")),
        trace_id=_as_str(result.get("traceId")),
    )


class ListScheduledEmailsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    limit: int | None = Field(
        default=None,
        description="Maximum number to return. Defaults to 10, maximum is 100",
    )
    offset: int | None = Field(
        default=None, description="Number of entries to skip for pagination"
    )
    status: str | None = Field(
        default=None,
        description=(
            "Schedule status: active, pause, complete, cancelled, retry, draft "
            "or resend-scheduled"
        ),
    )
    email_status: str | None = Field(
        default=None,
        description=(
            "Email delivery status: all, not-started, paused, cancelled, "
            "processing, resumed, next-drip, complete, success, error, waiting, "
            "queued, queueing, reading or scheduled"
        ),
    )
    name: str | None = Field(default=None, description="Filter by name")
    parent_id: str | None = Field(
        default=None, description="Only entries inside this parent folder"
    )
    limited_fields: bool | None = Field(
        default=None,
        description="Return only the essential fields instead of full campaign data",
    )
    archived: bool | None = Field(
        default=None, description="Whether to include archived entries"
    )
    campaigns_only: bool | None = Field(
        default=None, description="Return only campaigns, excluding folders"
    )
    show_stats: bool | None = Field(
        default=None,
        description="Include delivered, opened, clicked counts and revenue",
    )


@tool(args_schema=ListScheduledEmailsInput)
@serialize_pydantic_return
async def list_scheduled_emails(
    auth_type: str,
    auth_data: dict[str, Any],
    limit: int | None = None,
    offset: int | None = None,
    status: str | None = None,
    email_status: str | None = None,
    name: str | None = None,
    parent_id: str | None = None,
    limited_fields: bool | None = None,
    archived: bool | None = None,
    campaigns_only: bool | None = None,
    show_stats: bool | None = None,
) -> ListScheduledEmailsOutput:
    """List the sub-account's scheduled email campaigns and their send status."""
    location_id = _location_id(auth_data)
    if not location_id:
        return ListScheduledEmailsOutput(success=False, error=_MISSING_LOCATION)
    params: dict[str, Any] = {
        "locationId": location_id,
        "limit": limit,
        "offset": offset,
        "status": status,
        "emailStatus": email_status,
        "name": name,
        "parentId": parent_id,
        "limitedFields": limited_fields,
        "archived": archived,
        "campaignsOnly": campaigns_only,
        "showStats": show_stats,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/emails/schedule", params=params
    )
    if error is not None:
        return ListScheduledEmailsOutput(success=False, error=error)
    body = _as_dict(payload)
    # TODO (unverified): the published email API spec types `total` as an array of strings
    # even though it describes a count; both forms are accepted.
    return ListScheduledEmailsOutput(
        success=True,
        schedules=[
            _parse_email_schedule(item) for item in _as_dict_list(body.get("schedules"))
        ],
        total=_parse_email_total(body.get("total")),
        trace_id=_as_str(body.get("traceId")),
    )


# --- Scheduling helpers -----------------------------------------------------
#
# Every path in this family starts with ``/calendars``, so ``_request``
# resolves the mandatory ``Version`` header to the ``2021-04-15`` value these
# operations declare.
#
# ``{resourceType}`` is a closed enum in the path template, so an unknown value
# is rejected before it can reach the URL.

_CALENDAR_RESOURCE_TYPES = ("equipments", "rooms")
_BAD_CALENDAR_RESOURCE_TYPE = (
    "resource_type must be one of: equipments, rooms."
)


def _bad_calendar_resource_type(resource_type: str) -> bool:
    """True when the caller passed a resource type the API does not accept.

    Callers normalize (``strip().lower()``) before checking, so a model
    emitting ``"Rooms"`` succeeds rather than getting a hard error — and the
    normalized value is what reaches the request path.
    """
    return resource_type not in _CALENDAR_RESOURCE_TYPES


def _parse_calendar_event_creator(raw: Any) -> CalendarEventCreator | None:
    """Build the created/updated-by stanza, or None when absent."""
    item = _as_dict(raw)
    if not item:
        return None
    return CalendarEventCreator(
        user_id=_as_str(item.get("userId")),
        source=_as_str(item.get("source")),
    )


def _parse_calendar_event(raw: Any) -> CalendarEventDetails:
    """Map one ``CalendarEventDTO`` onto its model."""
    item = _as_dict(raw)
    return CalendarEventDetails(
        id=_as_str(item.get("id")),
        address=_as_str(item.get("address")),
        title=_as_str(item.get("title")),
        calendar_id=_as_str(item.get("calendarId")),
        location_id=_as_str(item.get("locationId")),
        contact_id=_as_str(item.get("contactId")),
        group_id=_as_str(item.get("groupId")),
        appointment_status=_as_str(item.get("appointmentStatus")),
        assigned_user_id=_as_str(item.get("assignedUserId")),
        users=_as_str_list(item.get("users")),
        notes=_as_str(item.get("notes")),
        description=_as_str(item.get("description")),
        is_recurring=_as_bool(item.get("isRecurring")),
        rrule=_as_str(item.get("rrule")),
        start_time=_as_str(item.get("startTime")),
        end_time=_as_str(item.get("endTime")),
        date_added=_as_str(item.get("dateAdded")),
        date_updated=_as_str(item.get("dateUpdated")),
        assigned_resources=_as_str_list(item.get("assignedResources")),
        created_by=_parse_calendar_event_creator(item.get("createdBy")),
        master_event_id=_as_str(item.get("masterEventId")),
    )


def _parse_appointment(raw: Any) -> AppointmentDetails:
    """Map one ``AppointmentSchemaResponse`` onto its model."""
    item = _as_dict(raw)
    return AppointmentDetails(
        id=_as_str(item.get("id")),
        calendar_id=_as_str(item.get("calendarId")),
        location_id=_as_str(item.get("locationId")),
        contact_id=_as_str(item.get("contactId")),
        start_time=_as_str(item.get("startTime")),
        end_time=_as_str(item.get("endTime")),
        title=_as_str(item.get("title")),
        meeting_location_type=_as_str(item.get("meetingLocationType")),
        appointment_status=_as_str(item.get("appointmentStatus")),
        assigned_user_id=_as_str(item.get("assignedUserId")),
        address=_as_str(item.get("address")),
        is_recurring=_as_bool(item.get("isRecurring")),
        rrule=_as_str(item.get("rrule")),
    )


def _parse_appointment_note_creator(raw: Any) -> AppointmentNoteCreator | None:
    """Build the note author stanza, or None when absent."""
    item = _as_dict(raw)
    if not item:
        return None
    return AppointmentNoteCreator(
        id=_as_str(item.get("id")),
        name=_as_str(item.get("name")),
    )


def _parse_appointment_note(raw: Any) -> AppointmentNoteDetails:
    """Map one ``GetNoteSchema`` onto its model."""
    item = _as_dict(raw)
    return AppointmentNoteDetails(
        id=_as_str(item.get("id")),
        body=_as_str(item.get("body")),
        user_id=_as_str(item.get("userId")),
        date_added=_as_str(item.get("dateAdded")),
        contact_id=_as_str(item.get("contactId")),
        created_by=_parse_appointment_note_creator(item.get("createdBy")),
    )


def _parse_block_slot(raw: Any) -> BlockSlotDetails:
    """Map one ``BlockedSlotSuccessfulResponseDto`` onto its model."""
    item = _as_dict(raw)
    return BlockSlotDetails(
        id=_as_str(item.get("id")),
        location_id=_as_str(item.get("locationId")),
        title=_as_str(item.get("title")),
        start_time=_as_str(item.get("startTime")),
        end_time=_as_str(item.get("endTime")),
        calendar_id=_as_str(item.get("calendarId")),
        assigned_user_id=_as_str(item.get("assignedUserId")),
    )


def _parse_calendar_group(raw: Any) -> CalendarGroupDetails:
    """Map one ``GroupDTO`` onto its model."""
    item = _as_dict(raw)
    return CalendarGroupDetails(
        id=_as_str(item.get("id")),
        location_id=_as_str(item.get("locationId")),
        name=_as_str(item.get("name")),
        description=_as_str(item.get("description")),
        slug=_as_str(item.get("slug")),
        is_active=_as_bool(item.get("isActive")),
    )


def _parse_calendar_resource(raw: Any) -> CalendarResourceDetails:
    """Map one room/equipment resource onto its model."""
    # TODO (unverified): the documented resource schema declares no identifier
    # field at all, yet the get/update/delete paths all take a resource ID.
    # Both the plain and Mongo-style keys are read so the ID is not lost.
    item = _as_dict(raw)
    return CalendarResourceDetails(
        id=_as_str(item.get("id")) or _as_str(item.get("_id")),
        location_id=_as_str(item.get("locationId")),
        name=_as_str(item.get("name")),
        resource_type=_as_str(item.get("resourceType")),
        is_active=_as_bool(item.get("isActive")),
        description=_as_str(item.get("description")),
        quantity=_as_float(item.get("quantity")),
        out_of_service=_as_float(item.get("outOfService")),
        capacity=_as_float(item.get("capacity")),
        calendar_ids=_as_str_list(item.get("calendarIds")),
    )


def _parse_calendar_notification_schedule(raw: Any) -> CalendarNotificationSchedule:
    """Map one ``SchedulesDTO`` offset onto its model."""
    item = _as_dict(raw)
    return CalendarNotificationSchedule(
        time_offset=_as_float(item.get("timeOffset")),
        unit=_as_str(item.get("unit")),
    )


def _parse_calendar_notification(raw: Any) -> CalendarNotificationDetails:
    """Map one ``CalendarNotificationResponseDTO`` onto its model."""
    item = _as_dict(raw)
    after = _as_dict_list(item.get("afterTime"))
    before = _as_dict_list(item.get("beforeTime"))
    return CalendarNotificationDetails(
        id=_as_str(item.get("_id")) or _as_str(item.get("id")),
        receiver_type=_as_str(item.get("receiverType")),
        additional_email_ids=_as_str_list(item.get("additionalEmailIds")),
        additional_phone_numbers=_as_str_list(item.get("additionalPhoneNumbers")),
        additional_whatsapp_numbers=_as_str_list(item.get("additionalWhatsappNumbers")),
        channel=_as_str(item.get("channel")),
        notification_type=_as_str(item.get("notificationType")),
        is_active=_as_bool(item.get("isActive")),
        template_id=_as_str(item.get("templateId")),
        body=_as_str(item.get("body")),
        subject=_as_str(item.get("subject")),
        after_time=[_parse_calendar_notification_schedule(entry) for entry in after],
        before_time=[_parse_calendar_notification_schedule(entry) for entry in before],
        selected_users=_as_str_list(item.get("selectedUsers")),
        deleted=_as_bool(item.get("deleted")),
    )


def _parse_availability_schedule_interval(raw: Any) -> AvailabilityScheduleInterval:
    """Map one ``ScheduleIntervalDTO`` onto its model."""
    item = _as_dict(raw)
    return AvailabilityScheduleInterval(
        from_time=_as_str(item.get("from")),
        to_time=_as_str(item.get("to")),
    )


def _parse_availability_schedule_rule(raw: Any) -> AvailabilityScheduleRule:
    """Map one ``ScheduleRuleDTO`` onto its model."""
    item = _as_dict(raw)
    intervals = _as_dict_list(item.get("intervals"))
    return AvailabilityScheduleRule(
        type=_as_str(item.get("type")),
        intervals=[_parse_availability_schedule_interval(entry) for entry in intervals],
        date=_as_str(item.get("date")),
        day=_as_str(item.get("day")),
    )


def _parse_availability_schedule(raw: Any) -> AvailabilityScheduleDetails:
    """Map one ``ScheduleObjectResponseDTO`` onto its model."""
    item = _as_dict(raw)
    rules = _as_dict_list(item.get("rules"))
    return AvailabilityScheduleDetails(
        id=_as_str(item.get("id")),
        name=_as_str(item.get("name")),
        location_id=_as_str(item.get("locationId")),
        rules=[_parse_availability_schedule_rule(entry) for entry in rules],
        timezone=_as_str(item.get("timezone")),
        date_added=_as_str(item.get("dateAdded")),
        date_updated=_as_str(item.get("dateUpdated")),
        user_id=_as_str(item.get("userId")),
        calendar_ids=_as_str_list(item.get("calendarIds")),
        deleted=_as_bool(item.get("deleted")),
    )


def _parse_calendar_free_slots(payload: Any) -> list[CalendarFreeSlotDay]:
    """Flatten the ``{"YYYY-MM-DD": {"slots": [...]}}`` availability map.

    Keys whose value is not a slots object (for example a ``traceId`` echo)
    are ignored rather than raising.
    """
    days: list[CalendarFreeSlotDay] = []
    for date_key, value in sorted(_as_dict(payload).items()):
        entry = _as_dict(value)
        if "slots" not in entry:
            continue
        days.append(
            CalendarFreeSlotDay(date=date_key, slots=_as_str_list(entry.get("slots")))
        )
    return days


def _parse_calendar(raw: Any) -> CalendarDetails:
    """Map one ``CalendarDTO`` onto its model."""
    item = _as_dict(raw)
    return CalendarDetails(
        id=_as_str(item.get("id")),
        location_id=_as_str(item.get("locationId")),
        group_id=_as_str(item.get("groupId")),
        name=_as_str(item.get("name")),
        description=_as_str(item.get("description")),
        slug=_as_str(item.get("slug")),
        widget_slug=_as_str(item.get("widgetSlug")),
        calendar_type=_as_str(item.get("calendarType")),
        widget_type=_as_str(item.get("widgetType")),
        event_type=_as_str(item.get("eventType")),
        event_title=_as_str(item.get("eventTitle")),
        event_color=_as_str(item.get("eventColor")),
        is_active=_as_bool(item.get("isActive")),
        meeting_location=_as_str(item.get("meetingLocation")),
        slot_duration=_as_float(item.get("slotDuration")),
        slot_duration_unit=_as_str(item.get("slotDurationUnit")),
        slot_interval=_as_float(item.get("slotInterval")),
        slot_interval_unit=_as_str(item.get("slotIntervalUnit")),
        slot_buffer=_as_float(item.get("slotBuffer")),
        slot_buffer_unit=_as_str(item.get("slotBufferUnit")),
        pre_buffer=_as_float(item.get("preBuffer")),
        pre_buffer_unit=_as_str(item.get("preBufferUnit")),
        # "appoinment" (sic) is the upstream spelling of these two keys.
        appointment_per_slot=_as_float(item.get("appoinmentPerSlot")),
        appointment_per_day=_as_float(item.get("appoinmentPerDay")),
        allow_booking_after=_as_float(item.get("allowBookingAfter")),
        allow_booking_after_unit=_as_str(item.get("allowBookingAfterUnit")),
        allow_booking_for=_as_float(item.get("allowBookingFor")),
        allow_booking_for_unit=_as_str(item.get("allowBookingForUnit")),
        enable_recurring=_as_bool(item.get("enableRecurring")),
        form_id=_as_str(item.get("formId")),
        sticky_contact=_as_bool(item.get("stickyContact")),
        is_live_payment_mode=_as_bool(item.get("isLivePaymentMode")),
        auto_confirm=_as_bool(item.get("autoConfirm")),
        should_send_alert_emails_to_assigned_member=_as_bool(
            item.get("shouldSendAlertEmailsToAssignedMember")
        ),
        alert_email=_as_str(item.get("alertEmail")),
        google_invitation_emails=_as_bool(item.get("googleInvitationEmails")),
        allow_reschedule=_as_bool(item.get("allowReschedule")),
        allow_cancellation=_as_bool(item.get("allowCancellation")),
        should_assign_contact_to_team_member=_as_bool(
            item.get("shouldAssignContactToTeamMember")
        ),
        should_skip_assigning_contact_for_existing=_as_bool(
            item.get("shouldSkipAssigningContactForExisting")
        ),
        notes=_as_str(item.get("notes")),
        pixel_id=_as_str(item.get("pixelId")),
        form_submit_type=_as_str(item.get("formSubmitType")),
        form_submit_redirect_url=_as_str(item.get("formSubmitRedirectURL")),
        form_submit_thanks_message=_as_str(item.get("formSubmitThanksMessage")),
        availability_type=_as_float(item.get("availabilityType")),
        guest_type=_as_str(item.get("guestType")),
        consent_label=_as_str(item.get("consentLabel")),
        calendar_cover_image=_as_str(item.get("calendarCoverImage")),
        team_members=_as_dict_list(item.get("teamMembers")),
        location_configurations=_as_dict_list(item.get("locationConfigurations")),
        open_hours=_as_dict_list(item.get("openHours")),
        availabilities=_as_dict_list(item.get("availabilities")),
        notifications=_as_dict_list(item.get("notifications")),
        recurring=_as_dict(item.get("recurring")),
        look_busy_config=_as_dict(item.get("lookBusyConfig")),
    )


# --- Calendars --------------------------------------------------------------


class ListCalendarsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    group_id: str | None = Field(
        default=None, description="Filter calendars by a specific calendar group ID"
    )
    show_drafted: bool | None = Field(
        default=None,
        description="Whether to include draft (inactive) calendars in the response",
    )


@tool(args_schema=ListCalendarsInput)
@serialize_pydantic_return
async def list_calendars(
    auth_type: str,
    auth_data: dict[str, Any],
    group_id: str | None = None,
    show_drafted: bool | None = None,
) -> ListCalendarsOutput:
    """List every booking calendar in the connected GoHighLevel sub-account."""
    location_id = _location_id(auth_data)
    if not location_id:
        return ListCalendarsOutput(success=False, error=_MISSING_LOCATION)
    params: dict[str, Any] = {
        "locationId": location_id,
        "groupId": group_id,
        "showDrafted": show_drafted,
    }
    payload, error = await _request(auth_type, auth_data, "GET", "/calendars/", params=params)
    if error is not None:
        return ListCalendarsOutput(success=False, error=error)
    body = _as_dict(payload)
    return ListCalendarsOutput(
        success=True,
        calendars=[_parse_calendar(item) for item in _as_dict_list(body.get("calendars"))],
    )


class CreateCalendarInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="The name of the calendar")
    calendar_type: str | None = Field(
        default=None,
        description=(
            "Calendar type: round_robin, event, class_booking, collective, "
            "service_booking or personal"
        ),
    )
    description: str | None = Field(default=None, description="A description of the calendar")
    slug: str | None = Field(default=None, description="URL slug for the booking page")
    widget_slug: str | None = Field(default=None, description="Slug for the booking widget")
    widget_type: str | None = Field(
        default=None,
        description="Widget layout: 'default' for the neo layout, 'classic' for classic",
    )
    group_id: str | None = Field(default=None, description="Calendar group ID")
    event_type: str | None = Field(
        default=None,
        description=(
            "Round-robin strategy: RoundRobin_OptimizeForAvailability or "
            "RoundRobin_OptimizeForEqualDistribution"
        ),
    )
    event_title: str | None = Field(
        default=None, description="Template for the event title (supports merge fields)"
    )
    event_color: str | None = Field(default=None, description="Colour used for events")
    is_active: bool | None = Field(
        default=None, description="Whether the calendar is active (published) or a draft"
    )
    meeting_location: str | None = Field(
        default=None,
        description="Deprecated upstream; prefer location_configurations",
    )
    location_configurations: list[dict[str, Any]] | None = Field(
        default=None,
        description="Meeting location configurations, each with 'kind' and 'location'",
    )
    team_members: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Team members assigned to the calendar; required for round_robin, "
            "collective, class_booking and service_booking calendars"
        ),
    )
    slot_duration: float | None = Field(default=None, description="Duration of the meeting")
    slot_duration_unit: str | None = Field(
        default=None, description="Unit for slot duration: mins or hours"
    )
    slot_interval: float | None = Field(
        default=None, description="Time between the booking slots shown on the calendar"
    )
    slot_interval_unit: str | None = Field(
        default=None, description="Unit for slot interval: mins or hours"
    )
    slot_buffer: float | None = Field(
        default=None, description="Extra time added after an appointment"
    )
    slot_buffer_unit: str | None = Field(
        default=None, description="Unit for slot buffer: mins or hours"
    )
    pre_buffer: float | None = Field(
        default=None, description="Extra time added before an appointment"
    )
    pre_buffer_unit: str | None = Field(
        default=None, description="Unit for pre-buffer: mins or hours"
    )
    appointment_per_slot: float | None = Field(
        default=None, description="Maximum bookings per slot (seats per slot for class booking)"
    )
    appointment_per_day: float | None = Field(
        default=None, description="Number of appointments bookable on a given day"
    )
    allow_booking_after: float | None = Field(
        default=None, description="Minimum scheduling notice for events"
    )
    allow_booking_after_unit: str | None = Field(
        default=None, description="Unit for minimum scheduling notice: hours, days, weeks or months"
    )
    allow_booking_for: float | None = Field(
        default=None, description="How far ahead events may be booked"
    )
    allow_booking_for_unit: str | None = Field(
        default=None, description="Unit for the booking window: days, weeks or months"
    )
    open_hours: list[dict[str, Any]] | None = Field(
        default=None,
        description="Standard availability windows; use availabilities for custom dates",
    )
    availabilities: list[dict[str, Any]] | None = Field(
        default=None, description="Custom date availability; use open_hours for standard hours"
    )
    availability_type: float | None = Field(
        default=None,
        description="1 uses only custom availabilities, 0 uses only open hours",
    )
    enable_recurring: bool | None = Field(
        default=None, description="Enable recurring appointments on this calendar"
    )
    recurring: dict[str, Any] | None = Field(
        default=None, description="Recurring appointment configuration"
    )
    form_id: str | None = Field(default=None, description="Custom intake form ID")
    sticky_contact: bool | None = Field(default=None, description="Enable sticky contact")
    is_live_payment_mode: bool | None = Field(
        default=None, description="Whether payments are taken in live mode"
    )
    auto_confirm: bool | None = Field(
        default=None, description="Automatically confirm bookings without manual approval"
    )
    should_send_alert_emails_to_assigned_member: bool | None = Field(
        default=None, description="Send booking alert emails to the assigned member"
    )
    alert_email: str | None = Field(default=None, description="Email address to receive alerts")
    google_invitation_emails: bool | None = Field(
        default=None, description="Send Google calendar invitation emails"
    )
    allow_reschedule: bool | None = Field(
        default=None, description="Allow bookers to reschedule"
    )
    allow_cancellation: bool | None = Field(
        default=None, description="Allow bookers to cancel"
    )
    should_assign_contact_to_team_member: bool | None = Field(
        default=None, description="Assign the booking contact to the team member"
    )
    should_skip_assigning_contact_for_existing: bool | None = Field(
        default=None, description="Skip contact assignment when the contact already exists"
    )
    notes: str | None = Field(default=None, description="Internal notes about the calendar")
    pixel_id: str | None = Field(default=None, description="Tracking pixel ID")
    form_submit_type: str | None = Field(
        default=None, description="After submit behaviour: RedirectURL or ThankYouMessage"
    )
    form_submit_redirect_url: str | None = Field(
        default=None, description="Redirect URL used when form_submit_type is RedirectURL"
    )
    form_submit_thanks_message: str | None = Field(
        default=None, description="Thank-you message shown after submission"
    )
    guest_type: str | None = Field(
        default=None, description="Guest handling: count_only or collect_detail"
    )
    consent_label: str | None = Field(default=None, description="Consent checkbox label")
    calendar_cover_image: str | None = Field(default=None, description="Cover image URL")
    look_busy_config: dict[str, Any] | None = Field(
        default=None,
        description="Look-busy settings with 'enabled' and 'LookBusyPercentage'",
    )
    notifications: list[dict[str, Any]] | None = Field(
        default=None,
        description="Deprecated upstream; prefer the calendar notification actions",
    )


@tool(args_schema=CreateCalendarInput)
@serialize_pydantic_return
async def create_calendar(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    calendar_type: str | None = None,
    description: str | None = None,
    slug: str | None = None,
    widget_slug: str | None = None,
    widget_type: str | None = None,
    group_id: str | None = None,
    event_type: str | None = None,
    event_title: str | None = None,
    event_color: str | None = None,
    is_active: bool | None = None,
    meeting_location: str | None = None,
    location_configurations: list[dict[str, Any]] | None = None,
    team_members: list[dict[str, Any]] | None = None,
    slot_duration: float | None = None,
    slot_duration_unit: str | None = None,
    slot_interval: float | None = None,
    slot_interval_unit: str | None = None,
    slot_buffer: float | None = None,
    slot_buffer_unit: str | None = None,
    pre_buffer: float | None = None,
    pre_buffer_unit: str | None = None,
    appointment_per_slot: float | None = None,
    appointment_per_day: float | None = None,
    allow_booking_after: float | None = None,
    allow_booking_after_unit: str | None = None,
    allow_booking_for: float | None = None,
    allow_booking_for_unit: str | None = None,
    open_hours: list[dict[str, Any]] | None = None,
    availabilities: list[dict[str, Any]] | None = None,
    availability_type: float | None = None,
    enable_recurring: bool | None = None,
    recurring: dict[str, Any] | None = None,
    form_id: str | None = None,
    sticky_contact: bool | None = None,
    is_live_payment_mode: bool | None = None,
    auto_confirm: bool | None = None,
    should_send_alert_emails_to_assigned_member: bool | None = None,
    alert_email: str | None = None,
    google_invitation_emails: bool | None = None,
    allow_reschedule: bool | None = None,
    allow_cancellation: bool | None = None,
    should_assign_contact_to_team_member: bool | None = None,
    should_skip_assigning_contact_for_existing: bool | None = None,
    notes: str | None = None,
    pixel_id: str | None = None,
    form_submit_type: str | None = None,
    form_submit_redirect_url: str | None = None,
    form_submit_thanks_message: str | None = None,
    guest_type: str | None = None,
    consent_label: str | None = None,
    calendar_cover_image: str | None = None,
    look_busy_config: dict[str, Any] | None = None,
    notifications: list[dict[str, Any]] | None = None,
) -> CreateCalendarOutput:
    """Create a booking calendar in the connected GoHighLevel sub-account."""
    location_id = _location_id(auth_data)
    if not location_id:
        return CreateCalendarOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "locationId": location_id,
        "name": name,
        "calendarType": calendar_type,
        "description": description,
        "slug": slug,
        "widgetSlug": widget_slug,
        "widgetType": widget_type,
        "groupId": group_id,
        "eventType": event_type,
        "eventTitle": event_title,
        "eventColor": event_color,
        "isActive": is_active,
        "meetingLocation": meeting_location,
        "locationConfigurations": location_configurations,
        "teamMembers": team_members,
        "slotDuration": slot_duration,
        "slotDurationUnit": slot_duration_unit,
        "slotInterval": slot_interval,
        "slotIntervalUnit": slot_interval_unit,
        "slotBuffer": slot_buffer,
        "slotBufferUnit": slot_buffer_unit,
        "preBuffer": pre_buffer,
        "preBufferUnit": pre_buffer_unit,
        "appoinmentPerSlot": appointment_per_slot,
        "appoinmentPerDay": appointment_per_day,
        "allowBookingAfter": allow_booking_after,
        "allowBookingAfterUnit": allow_booking_after_unit,
        "allowBookingFor": allow_booking_for,
        "allowBookingForUnit": allow_booking_for_unit,
        "openHours": open_hours,
        "availabilities": availabilities,
        "availabilityType": availability_type,
        "enableRecurring": enable_recurring,
        "recurring": recurring,
        "formId": form_id,
        "stickyContact": sticky_contact,
        "isLivePaymentMode": is_live_payment_mode,
        "autoConfirm": auto_confirm,
        "shouldSendAlertEmailsToAssignedMember": should_send_alert_emails_to_assigned_member,
        "alertEmail": alert_email,
        "googleInvitationEmails": google_invitation_emails,
        "allowReschedule": allow_reschedule,
        "allowCancellation": allow_cancellation,
        "shouldAssignContactToTeamMember": should_assign_contact_to_team_member,
        "shouldSkipAssigningContactForExisting": should_skip_assigning_contact_for_existing,
        "notes": notes,
        "pixelId": pixel_id,
        "formSubmitType": form_submit_type,
        "formSubmitRedirectURL": form_submit_redirect_url,
        "formSubmitThanksMessage": form_submit_thanks_message,
        "guestType": guest_type,
        "consentLabel": consent_label,
        "calendarCoverImage": calendar_cover_image,
        "lookBusyConfig": look_busy_config,
        "notifications": notifications,
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/calendars/", json_body=body
    )
    if error is not None:
        return CreateCalendarOutput(success=False, error=error)
    return CreateCalendarOutput(
        success=True,
        calendar=_parse_calendar(_as_dict(payload).get("calendar")),
    )


# --- Appointment notes ------------------------------------------------------


class ListAppointmentNotesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    appointment_id: str = Field(description="The unique identifier of the appointment")
    limit: int = Field(description="Number of notes to fetch")
    offset: int = Field(description="Number of notes to skip before collecting results")


@tool(args_schema=ListAppointmentNotesInput)
@serialize_pydantic_return
async def list_appointment_notes(
    auth_type: str,
    auth_data: dict[str, Any],
    appointment_id: str,
    limit: int,
    offset: int,
) -> ListAppointmentNotesOutput:
    """List the notes attached to a GoHighLevel appointment."""
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    payload, error = await _request(
        auth_type,
        auth_data,
        "GET",
        f"/calendars/appointments/{_seg(appointment_id)}/notes",
        params=params,
    )
    if error is not None:
        return ListAppointmentNotesOutput(success=False, error=error)
    body = _as_dict(payload)
    return ListAppointmentNotesOutput(
        success=True,
        notes=[_parse_appointment_note(item) for item in _as_dict_list(body.get("notes"))],
        has_more=_as_bool(body.get("hasMore")),
    )


class CreateAppointmentNoteInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    appointment_id: str = Field(
        description="The unique identifier of the appointment to attach the note to"
    )
    body: str = Field(description="Note body. Maximum length is 5000 characters")
    user_id: str | None = Field(
        default=None, description="The unique identifier of the user creating the note"
    )


@tool(args_schema=CreateAppointmentNoteInput)
@serialize_pydantic_return
async def create_appointment_note(
    auth_type: str,
    auth_data: dict[str, Any],
    appointment_id: str,
    body: str,
    user_id: str | None = None,
) -> CreateAppointmentNoteOutput:
    """Attach a free-form note to a GoHighLevel appointment."""
    json_body: dict[str, Any] = {"body": body, "userId": user_id}
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        f"/calendars/appointments/{_seg(appointment_id)}/notes",
        json_body=json_body,
    )
    if error is not None:
        return CreateAppointmentNoteOutput(success=False, error=error)
    return CreateAppointmentNoteOutput(
        success=True,
        note=_parse_appointment_note(_as_dict(payload).get("note")),
    )


class UpdateAppointmentNoteInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    appointment_id: str = Field(description="The unique identifier of the appointment")
    note_id: str = Field(description="The unique identifier of the note to update")
    body: str = Field(description="Note body. Maximum length is 5000 characters")
    user_id: str | None = Field(
        default=None, description="The unique identifier of the user updating the note"
    )


@tool(args_schema=UpdateAppointmentNoteInput)
@serialize_pydantic_return
async def update_appointment_note(
    auth_type: str,
    auth_data: dict[str, Any],
    appointment_id: str,
    note_id: str,
    body: str,
    user_id: str | None = None,
) -> UpdateAppointmentNoteOutput:
    """Update the body of a note attached to a GoHighLevel appointment."""
    # TODO (unverified): the upstream document declares only `appointmentId`
    # for this operation even though the path template also carries
    # `{noteId}`; the note ID is sent because the path requires it.
    json_body: dict[str, Any] = {"body": body, "userId": user_id}
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/calendars/appointments/{_seg(appointment_id)}/notes/{_seg(note_id)}",
        json_body=json_body,
    )
    if error is not None:
        return UpdateAppointmentNoteOutput(success=False, error=error)
    return UpdateAppointmentNoteOutput(
        success=True,
        note=_parse_appointment_note(_as_dict(payload).get("note")),
    )


class DeleteAppointmentNoteInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    appointment_id: str = Field(
        description="The unique identifier of the appointment whose note is deleted"
    )
    note_id: str = Field(description="The unique identifier of the note to delete")


@tool(args_schema=DeleteAppointmentNoteInput)
@serialize_pydantic_return
async def delete_appointment_note(
    auth_type: str,
    auth_data: dict[str, Any],
    appointment_id: str,
    note_id: str,
) -> DeleteAppointmentNoteOutput:
    """Permanently delete a note from a GoHighLevel appointment."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "DELETE",
        f"/calendars/appointments/{_seg(appointment_id)}/notes/{_seg(note_id)}",
    )
    if error is not None:
        return DeleteAppointmentNoteOutput(success=False, error=error)
    return DeleteAppointmentNoteOutput(
        success=True,
        deleted=_as_bool(_as_dict(payload).get("success")),
    )


# --- Events, appointments and block slots -----------------------------------


class ListBlockedSlotsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    start_time: str = Field(
        description="Start of the time range, in milliseconds since the epoch"
    )
    end_time: str = Field(description="End of the time range, in milliseconds since the epoch")
    user_id: str | None = Field(default=None, description="Filter by the owning user ID")
    calendar_id: str | None = Field(default=None, description="Filter by calendar ID")
    group_id: str | None = Field(default=None, description="Filter by calendar group ID")


@tool(args_schema=ListBlockedSlotsInput)
@serialize_pydantic_return
async def list_blocked_slots(
    auth_type: str,
    auth_data: dict[str, Any],
    start_time: str,
    end_time: str,
    user_id: str | None = None,
    calendar_id: str | None = None,
    group_id: str | None = None,
) -> ListBlockedSlotsOutput:
    """List blocked (unbookable) slots in a time range for the sub-account."""
    location_id = _location_id(auth_data)
    if not location_id:
        return ListBlockedSlotsOutput(success=False, error=_MISSING_LOCATION)
    params: dict[str, Any] = {
        "locationId": location_id,
        "startTime": start_time,
        "endTime": end_time,
        "userId": user_id,
        "calendarId": calendar_id,
        "groupId": group_id,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/calendars/blocked-slots", params=params
    )
    if error is not None:
        return ListBlockedSlotsOutput(success=False, error=error)
    body = _as_dict(payload)
    return ListBlockedSlotsOutput(
        success=True,
        events=[_parse_calendar_event(item) for item in _as_dict_list(body.get("events"))],
    )


class ListCalendarEventsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    start_time: str = Field(
        description="Start of the time range, in milliseconds since the epoch"
    )
    end_time: str = Field(description="End of the time range, in milliseconds since the epoch")
    user_id: str | None = Field(default=None, description="Filter by the owning user ID")
    calendar_id: str | None = Field(default=None, description="Filter by calendar ID")
    group_id: str | None = Field(default=None, description="Filter by calendar group ID")


@tool(args_schema=ListCalendarEventsInput)
@serialize_pydantic_return
async def list_calendar_events(
    auth_type: str,
    auth_data: dict[str, Any],
    start_time: str,
    end_time: str,
    user_id: str | None = None,
    calendar_id: str | None = None,
    group_id: str | None = None,
) -> ListCalendarEventsOutput:
    """List calendar events (appointments) in a time range for the sub-account."""
    location_id = _location_id(auth_data)
    if not location_id:
        return ListCalendarEventsOutput(success=False, error=_MISSING_LOCATION)
    params: dict[str, Any] = {
        "locationId": location_id,
        "startTime": start_time,
        "endTime": end_time,
        "userId": user_id,
        "calendarId": calendar_id,
        "groupId": group_id,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/calendars/events", params=params
    )
    if error is not None:
        return ListCalendarEventsOutput(success=False, error=error)
    body = _as_dict(payload)
    return ListCalendarEventsOutput(
        success=True,
        events=[_parse_calendar_event(item) for item in _as_dict_list(body.get("events"))],
    )


class CreateAppointmentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    calendar_id: str = Field(description="The calendar the appointment is booked on")
    contact_id: str = Field(description="The contact the appointment is booked for")
    start_time: str = Field(description="ISO 8601 start time of the appointment")
    end_time: str | None = Field(
        default=None, description="ISO 8601 end time of the appointment"
    )
    title: str | None = Field(default=None, description="The title of the appointment")
    appointment_status: str | None = Field(
        default=None,
        description="One of: new, confirmed, cancelled, showed, noshow, invalid",
    )
    assigned_user_id: str | None = Field(
        default=None, description="The user the appointment is assigned to"
    )
    address: str | None = Field(default=None, description="The address of the appointment")
    description: str | None = Field(
        default=None, description="The description of the appointment"
    )
    meeting_location_type: str | None = Field(
        default=None,
        description="One of: custom, zoom, gmeet, phone, address, ms_teams, google",
    )
    meeting_location_id: str | None = Field(
        default=None,
        description="Meeting location ID from calendar.locationConfigurations",
    )
    override_location_config: bool | None = Field(
        default=None, description="Override the calendar's meeting location configuration"
    )
    ignore_date_range: bool | None = Field(
        default=None,
        description="Ignore the minimum scheduling notice and date range",
    )
    to_notify: bool | None = Field(
        default=None, description="If false, automations will not run for this appointment"
    )
    ignore_free_slot_validation: bool | None = Field(
        default=None, description="Skip the free-slot validation when booking"
    )
    rrule: str | None = Field(
        default=None,
        description="iCalendar (RFC 5545) RRULE for a recurring appointment",
    )


@tool(args_schema=CreateAppointmentInput)
@serialize_pydantic_return
async def create_appointment(
    auth_type: str,
    auth_data: dict[str, Any],
    calendar_id: str,
    contact_id: str,
    start_time: str,
    end_time: str | None = None,
    title: str | None = None,
    appointment_status: str | None = None,
    assigned_user_id: str | None = None,
    address: str | None = None,
    description: str | None = None,
    meeting_location_type: str | None = None,
    meeting_location_id: str | None = None,
    override_location_config: bool | None = None,
    ignore_date_range: bool | None = None,
    to_notify: bool | None = None,
    ignore_free_slot_validation: bool | None = None,
    rrule: str | None = None,
) -> CreateAppointmentOutput:
    """Book a contact onto a GoHighLevel calendar as a new appointment."""
    location_id = _location_id(auth_data)
    if not location_id:
        return CreateAppointmentOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "locationId": location_id,
        "calendarId": calendar_id,
        "contactId": contact_id,
        "startTime": start_time,
        "endTime": end_time,
        "title": title,
        "appointmentStatus": appointment_status,
        "assignedUserId": assigned_user_id,
        "address": address,
        "description": description,
        "meetingLocationType": meeting_location_type,
        "meetingLocationId": meeting_location_id,
        "overrideLocationConfig": override_location_config,
        "ignoreDateRange": ignore_date_range,
        "toNotify": to_notify,
        "ignoreFreeSlotValidation": ignore_free_slot_validation,
        "rrule": rrule,
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/calendars/events/appointments", json_body=body
    )
    if error is not None:
        return CreateAppointmentOutput(success=False, error=error)
    return CreateAppointmentOutput(success=True, appointment=_parse_appointment(payload))


class UpdateAppointmentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    event_id: str = Field(
        description=(
            "The appointment event ID. For a recurring series send the "
            "masterEventId to modify the original series"
        )
    )
    calendar_id: str | None = Field(
        default=None, description="Move the appointment to this calendar"
    )
    start_time: str | None = Field(default=None, description="ISO 8601 start time")
    end_time: str | None = Field(default=None, description="ISO 8601 end time")
    title: str | None = Field(default=None, description="The title of the appointment")
    appointment_status: str | None = Field(
        default=None,
        description="One of: new, confirmed, cancelled, showed, noshow, invalid",
    )
    assigned_user_id: str | None = Field(
        default=None, description="The user the appointment is assigned to"
    )
    address: str | None = Field(default=None, description="The address of the appointment")
    description: str | None = Field(
        default=None, description="The description of the appointment"
    )
    meeting_location_type: str | None = Field(
        default=None,
        description="One of: custom, zoom, gmeet, phone, address, ms_teams, google",
    )
    meeting_location_id: str | None = Field(
        default=None,
        description="Meeting location ID from calendar.locationConfigurations",
    )
    override_location_config: bool | None = Field(
        default=None, description="Override the calendar's meeting location configuration"
    )
    ignore_date_range: bool | None = Field(
        default=None,
        description="Ignore the minimum scheduling notice and date range",
    )
    to_notify: bool | None = Field(
        default=None, description="If false, automations will not run for this appointment"
    )
    ignore_free_slot_validation: bool | None = Field(
        default=None, description="Skip the free-slot validation when rescheduling"
    )
    rrule: str | None = Field(
        default=None,
        description="iCalendar (RFC 5545) RRULE for a recurring appointment",
    )


@tool(args_schema=UpdateAppointmentInput)
@serialize_pydantic_return
async def update_appointment(
    auth_type: str,
    auth_data: dict[str, Any],
    event_id: str,
    calendar_id: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    title: str | None = None,
    appointment_status: str | None = None,
    assigned_user_id: str | None = None,
    address: str | None = None,
    description: str | None = None,
    meeting_location_type: str | None = None,
    meeting_location_id: str | None = None,
    override_location_config: bool | None = None,
    ignore_date_range: bool | None = None,
    to_notify: bool | None = None,
    ignore_free_slot_validation: bool | None = None,
    rrule: str | None = None,
) -> UpdateAppointmentOutput:
    """Update an existing GoHighLevel appointment; only supplied fields change."""
    body: dict[str, Any] = {
        "calendarId": calendar_id,
        "startTime": start_time,
        "endTime": end_time,
        "title": title,
        "appointmentStatus": appointment_status,
        "assignedUserId": assigned_user_id,
        "address": address,
        "description": description,
        "meetingLocationType": meeting_location_type,
        "meetingLocationId": meeting_location_id,
        "overrideLocationConfig": override_location_config,
        "ignoreDateRange": ignore_date_range,
        "toNotify": to_notify,
        "ignoreFreeSlotValidation": ignore_free_slot_validation,
        "rrule": rrule,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/calendars/events/appointments/{_seg(event_id)}",
        json_body=body,
        send_body=True,
    )
    if error is not None:
        return UpdateAppointmentOutput(success=False, error=error)
    return UpdateAppointmentOutput(success=True, appointment=_parse_appointment(payload))


class GetAppointmentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    event_id: str = Field(
        description="The appointment event ID, or the instance ID of a recurring series"
    )


@tool(args_schema=GetAppointmentInput)
@serialize_pydantic_return
async def get_appointment(
    auth_type: str,
    auth_data: dict[str, Any],
    event_id: str,
) -> GetAppointmentOutput:
    """Fetch one GoHighLevel appointment by its event ID."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/calendars/events/appointments/{_seg(event_id)}"
    )
    if error is not None:
        return GetAppointmentOutput(success=False, error=error)
    return GetAppointmentOutput(
        success=True,
        event=_parse_calendar_event(_as_dict(payload).get("event")),
    )


class CreateBlockSlotInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    start_time: str | None = Field(default=None, description="ISO 8601 start time")
    end_time: str | None = Field(default=None, description="ISO 8601 end time")
    title: str | None = Field(default=None, description="Title of the block slot")
    calendar_id: str | None = Field(
        default=None,
        description="Calendar to block. Set either calendar_id or assigned_user_id",
    )
    assigned_user_id: str | None = Field(
        default=None,
        description="User to block. Set either calendar_id or assigned_user_id",
    )


@tool(args_schema=CreateBlockSlotInput)
@serialize_pydantic_return
async def create_block_slot(
    auth_type: str,
    auth_data: dict[str, Any],
    start_time: str | None = None,
    end_time: str | None = None,
    title: str | None = None,
    calendar_id: str | None = None,
    assigned_user_id: str | None = None,
) -> CreateBlockSlotOutput:
    """Reserve time on a GoHighLevel calendar so it cannot be booked."""
    location_id = _location_id(auth_data)
    if not location_id:
        return CreateBlockSlotOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "locationId": location_id,
        "startTime": start_time,
        "endTime": end_time,
        "title": title,
        "calendarId": calendar_id,
        "assignedUserId": assigned_user_id,
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/calendars/events/block-slots", json_body=body
    )
    if error is not None:
        return CreateBlockSlotOutput(success=False, error=error)
    return CreateBlockSlotOutput(success=True, block_slot=_parse_block_slot(payload))


class UpdateBlockSlotInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    event_id: str = Field(description="The unique identifier of the block slot to update")
    start_time: str | None = Field(default=None, description="ISO 8601 start time")
    end_time: str | None = Field(default=None, description="ISO 8601 end time")
    title: str | None = Field(default=None, description="Title of the block slot")
    calendar_id: str | None = Field(
        default=None,
        description="Calendar to block. Set either calendar_id or assigned_user_id",
    )
    assigned_user_id: str | None = Field(
        default=None,
        description="User to block. Set either calendar_id or assigned_user_id",
    )


@tool(args_schema=UpdateBlockSlotInput)
@serialize_pydantic_return
async def update_block_slot(
    auth_type: str,
    auth_data: dict[str, Any],
    event_id: str,
    start_time: str | None = None,
    end_time: str | None = None,
    title: str | None = None,
    calendar_id: str | None = None,
    assigned_user_id: str | None = None,
) -> UpdateBlockSlotOutput:
    """Update the time, title or owner of a GoHighLevel block slot."""
    location_id = _location_id(auth_data)
    if not location_id:
        return UpdateBlockSlotOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "locationId": location_id,
        "startTime": start_time,
        "endTime": end_time,
        "title": title,
        "calendarId": calendar_id,
        "assignedUserId": assigned_user_id,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/calendars/events/block-slots/{_seg(event_id)}",
        json_body=body,
    )
    if error is not None:
        return UpdateBlockSlotOutput(success=False, error=error)
    return UpdateBlockSlotOutput(success=True, block_slot=_parse_block_slot(payload))


class DeleteEventInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    event_id: str = Field(
        description="The event ID of the appointment or block slot to delete"
    )


@tool(args_schema=DeleteEventInput)
@serialize_pydantic_return
async def delete_event(
    auth_type: str,
    auth_data: dict[str, Any],
    event_id: str,
) -> DeleteEventOutput:
    """Delete a GoHighLevel calendar event (appointment or block slot)."""
    # The upstream operation declares a required request body whose schema has
    # no properties, so an empty JSON object is always sent.
    payload, error = await _request(
        auth_type,
        auth_data,
        "DELETE",
        f"/calendars/events/{_seg(event_id)}",
        send_body=True,
    )
    if error is not None:
        return DeleteEventOutput(success=False, error=error)
    return DeleteEventOutput(
        success=True,
        deleted=_as_bool(_as_dict(payload).get("succeeded")),
    )


# --- Calendar groups --------------------------------------------------------


class ListCalendarGroupsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


@tool(args_schema=ListCalendarGroupsInput)
@serialize_pydantic_return
async def list_calendar_groups(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListCalendarGroupsOutput:
    """List every calendar group in the connected GoHighLevel sub-account."""
    location_id = _location_id(auth_data)
    if not location_id:
        return ListCalendarGroupsOutput(success=False, error=_MISSING_LOCATION)
    params: dict[str, Any] = {"locationId": location_id}
    payload, error = await _request(
        auth_type, auth_data, "GET", "/calendars/groups", params=params
    )
    if error is not None:
        return ListCalendarGroupsOutput(success=False, error=error)
    body = _as_dict(payload)
    return ListCalendarGroupsOutput(
        success=True,
        groups=[_parse_calendar_group(item) for item in _as_dict_list(body.get("groups"))],
    )


class CreateCalendarGroupInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="The name of the calendar group")
    description: str = Field(description="A description of the calendar group")
    slug: str = Field(description="The URL-friendly slug identifying the calendar group")
    is_active: bool | None = Field(
        default=None, description="Whether the calendar group is active"
    )


@tool(args_schema=CreateCalendarGroupInput)
@serialize_pydantic_return
async def create_calendar_group(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    description: str,
    slug: str,
    is_active: bool | None = None,
) -> CreateCalendarGroupOutput:
    """Create a calendar group that organises related calendars under one slug."""
    location_id = _location_id(auth_data)
    if not location_id:
        return CreateCalendarGroupOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "locationId": location_id,
        "name": name,
        "description": description,
        "slug": slug,
        "isActive": is_active,
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/calendars/groups", json_body=body
    )
    if error is not None:
        return CreateCalendarGroupOutput(success=False, error=error)
    return CreateCalendarGroupOutput(
        success=True,
        group=_parse_calendar_group(_as_dict(payload).get("group")),
    )


class ValidateCalendarGroupSlugInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    slug: str = Field(description="The slug to validate for availability in the sub-account")


@tool(args_schema=ValidateCalendarGroupSlugInput)
@serialize_pydantic_return
async def validate_calendar_group_slug(
    auth_type: str,
    auth_data: dict[str, Any],
    slug: str,
) -> ValidateCalendarGroupSlugOutput:
    """Check whether a calendar group slug is still available."""
    location_id = _location_id(auth_data)
    if not location_id:
        return ValidateCalendarGroupSlugOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {"locationId": location_id, "slug": slug}
    payload, error = await _request(
        auth_type, auth_data, "POST", "/calendars/groups/validate-slug", json_body=body
    )
    if error is not None:
        return ValidateCalendarGroupSlugOutput(success=False, error=error)
    return ValidateCalendarGroupSlugOutput(
        success=True,
        available=_as_bool(_as_dict(payload).get("available")),
    )


class DeleteCalendarGroupInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    group_id: str = Field(description="The unique identifier of the calendar group to delete")


@tool(args_schema=DeleteCalendarGroupInput)
@serialize_pydantic_return
async def delete_calendar_group(
    auth_type: str,
    auth_data: dict[str, Any],
    group_id: str,
) -> DeleteCalendarGroupOutput:
    """Permanently delete a GoHighLevel calendar group."""
    payload, error = await _request(
        auth_type, auth_data, "DELETE", f"/calendars/groups/{_seg(group_id)}"
    )
    if error is not None:
        return DeleteCalendarGroupOutput(success=False, error=error)
    return DeleteCalendarGroupOutput(
        success=True,
        deleted=_as_bool(_as_dict(payload).get("success")),
    )


class UpdateCalendarGroupInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    group_id: str = Field(description="The unique identifier of the calendar group to edit")
    name: str = Field(description="The name of the calendar group")
    description: str = Field(description="The description of the calendar group")
    slug: str = Field(description="The URL slug of the calendar group")


@tool(args_schema=UpdateCalendarGroupInput)
@serialize_pydantic_return
async def update_calendar_group(
    auth_type: str,
    auth_data: dict[str, Any],
    group_id: str,
    name: str,
    description: str,
    slug: str,
) -> UpdateCalendarGroupOutput:
    """Rename a GoHighLevel calendar group or change its description and slug."""
    body: dict[str, Any] = {"name": name, "description": description, "slug": slug}
    payload, error = await _request(
        auth_type, auth_data, "PUT", f"/calendars/groups/{_seg(group_id)}", json_body=body
    )
    if error is not None:
        return UpdateCalendarGroupOutput(success=False, error=error)
    return UpdateCalendarGroupOutput(
        success=True,
        group=_parse_calendar_group(_as_dict(payload).get("group")),
    )


class SetCalendarGroupStatusInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    group_id: str = Field(
        description="The unique identifier of the calendar group to enable or disable"
    )
    is_active: bool = Field(
        description="True to enable the calendar group, false to disable it"
    )


@tool(args_schema=SetCalendarGroupStatusInput)
@serialize_pydantic_return
async def set_calendar_group_status(
    auth_type: str,
    auth_data: dict[str, Any],
    group_id: str,
    is_active: bool,
) -> SetCalendarGroupStatusOutput:
    """Enable or disable a GoHighLevel calendar group."""
    body: dict[str, Any] = {"isActive": is_active}
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/calendars/groups/{_seg(group_id)}/status",
        json_body=body,
    )
    if error is not None:
        return SetCalendarGroupStatusOutput(success=False, error=error)
    return SetCalendarGroupStatusOutput(
        success=True,
        updated=_as_bool(_as_dict(payload).get("success")),
    )


# --- Calendar resources (rooms / equipment) ---------------------------------


class ListCalendarResourcesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    resource_type: str = Field(
        description="The resource type to list: 'equipments' or 'rooms'"
    )
    limit: int = Field(description="Maximum number of resources to return per page")
    skip: int = Field(description="Number of resources to skip before collecting results")


@tool(args_schema=ListCalendarResourcesInput)
@serialize_pydantic_return
async def list_calendar_resources(
    auth_type: str,
    auth_data: dict[str, Any],
    resource_type: str,
    limit: int,
    skip: int,
) -> ListCalendarResourcesOutput:
    """List the bookable rooms or equipment in the GoHighLevel sub-account."""
    resource_type = resource_type.strip().lower()
    if _bad_calendar_resource_type(resource_type):
        return ListCalendarResourcesOutput(success=False, error=_BAD_CALENDAR_RESOURCE_TYPE)
    location_id = _location_id(auth_data)
    if not location_id:
        return ListCalendarResourcesOutput(success=False, error=_MISSING_LOCATION)
    params: dict[str, Any] = {"locationId": location_id, "limit": limit, "skip": skip}
    payload, error = await _request(
        auth_type,
        auth_data,
        "GET",
        f"/calendars/resources/{_seg(resource_type)}",
        params=params,
    )
    if error is not None:
        return ListCalendarResourcesOutput(success=False, error=error)
    return ListCalendarResourcesOutput(
        success=True,
        resources=[_parse_calendar_resource(item) for item in _as_dict_list(payload)],
    )


class CreateCalendarResourceInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    resource_type: str = Field(
        description="The resource type to create: 'equipments' or 'rooms'"
    )
    name: str = Field(description="Name of the resource")
    description: str = Field(description="Description of the resource")
    quantity: float = Field(description="Quantity of the equipment")
    out_of_service: float = Field(description="Quantity of the equipment out of service")
    capacity: float = Field(description="Capacity of the room")
    calendar_ids: list[str] = Field(
        description="Service calendar IDs the resource is mapped to"
    )


@tool(args_schema=CreateCalendarResourceInput)
@serialize_pydantic_return
async def create_calendar_resource(
    auth_type: str,
    auth_data: dict[str, Any],
    resource_type: str,
    name: str,
    description: str,
    quantity: float,
    out_of_service: float,
    capacity: float,
    calendar_ids: list[str],
) -> CreateCalendarResourceOutput:
    """Create a bookable room or piece of equipment for service calendars."""
    resource_type = resource_type.strip().lower()
    if _bad_calendar_resource_type(resource_type):
        return CreateCalendarResourceOutput(success=False, error=_BAD_CALENDAR_RESOURCE_TYPE)
    location_id = _location_id(auth_data)
    if not location_id:
        return CreateCalendarResourceOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "locationId": location_id,
        "name": name,
        "description": description,
        "quantity": quantity,
        "outOfService": out_of_service,
        "capacity": capacity,
        "calendarIds": calendar_ids,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        f"/calendars/resources/{_seg(resource_type)}",
        json_body=body,
    )
    if error is not None:
        return CreateCalendarResourceOutput(success=False, error=error)
    return CreateCalendarResourceOutput(
        success=True, resource=_parse_calendar_resource(payload)
    )


class GetCalendarResourceInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    resource_type: str = Field(description="The resource type: 'equipments' or 'rooms'")
    resource_id: str = Field(description="The unique identifier of the calendar resource")


@tool(args_schema=GetCalendarResourceInput)
@serialize_pydantic_return
async def get_calendar_resource(
    auth_type: str,
    auth_data: dict[str, Any],
    resource_type: str,
    resource_id: str,
) -> GetCalendarResourceOutput:
    """Fetch one bookable room or piece of equipment by its ID."""
    resource_type = resource_type.strip().lower()
    if _bad_calendar_resource_type(resource_type):
        return GetCalendarResourceOutput(success=False, error=_BAD_CALENDAR_RESOURCE_TYPE)
    payload, error = await _request(
        auth_type,
        auth_data,
        "GET",
        f"/calendars/resources/{_seg(resource_type)}/{_seg(resource_id)}",
    )
    if error is not None:
        return GetCalendarResourceOutput(success=False, error=error)
    return GetCalendarResourceOutput(success=True, resource=_parse_calendar_resource(payload))


class UpdateCalendarResourceInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    resource_type: str = Field(description="The resource type: 'equipments' or 'rooms'")
    resource_id: str = Field(description="The unique identifier of the calendar resource")
    name: str | None = Field(default=None, description="Name of the resource")
    description: str | None = Field(default=None, description="Description of the resource")
    quantity: float | None = Field(default=None, description="Quantity of the equipment")
    out_of_service: float | None = Field(
        default=None, description="Quantity of the equipment out of service"
    )
    capacity: float | None = Field(default=None, description="Capacity of the room")
    calendar_ids: list[str] | None = Field(
        default=None, description="Service calendar IDs the resource is mapped to"
    )
    is_active: bool | None = Field(default=None, description="Whether the resource is active")


@tool(args_schema=UpdateCalendarResourceInput)
@serialize_pydantic_return
async def update_calendar_resource(
    auth_type: str,
    auth_data: dict[str, Any],
    resource_type: str,
    resource_id: str,
    name: str | None = None,
    description: str | None = None,
    quantity: float | None = None,
    out_of_service: float | None = None,
    capacity: float | None = None,
    calendar_ids: list[str] | None = None,
    is_active: bool | None = None,
) -> UpdateCalendarResourceOutput:
    """Update a bookable room or piece of equipment; only supplied fields change."""
    resource_type = resource_type.strip().lower()
    if _bad_calendar_resource_type(resource_type):
        return UpdateCalendarResourceOutput(success=False, error=_BAD_CALENDAR_RESOURCE_TYPE)
    body: dict[str, Any] = {
        "name": name,
        "description": description,
        "quantity": quantity,
        "outOfService": out_of_service,
        "capacity": capacity,
        "calendarIds": calendar_ids,
        "isActive": is_active,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/calendars/resources/{_seg(resource_type)}/{_seg(resource_id)}",
        json_body=body,
        send_body=True,
    )
    if error is not None:
        return UpdateCalendarResourceOutput(success=False, error=error)
    return UpdateCalendarResourceOutput(
        success=True, resource=_parse_calendar_resource(payload)
    )


class DeleteCalendarResourceInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    resource_type: str = Field(description="The resource type: 'equipments' or 'rooms'")
    resource_id: str = Field(
        description="The unique identifier of the calendar resource to delete"
    )


@tool(args_schema=DeleteCalendarResourceInput)
@serialize_pydantic_return
async def delete_calendar_resource(
    auth_type: str,
    auth_data: dict[str, Any],
    resource_type: str,
    resource_id: str,
) -> DeleteCalendarResourceOutput:
    """Permanently delete a bookable room or piece of equipment."""
    resource_type = resource_type.strip().lower()
    if _bad_calendar_resource_type(resource_type):
        return DeleteCalendarResourceOutput(success=False, error=_BAD_CALENDAR_RESOURCE_TYPE)
    payload, error = await _request(
        auth_type,
        auth_data,
        "DELETE",
        f"/calendars/resources/{_seg(resource_type)}/{_seg(resource_id)}",
    )
    if error is not None:
        return DeleteCalendarResourceOutput(success=False, error=error)
    return DeleteCalendarResourceOutput(
        success=True,
        deleted=_as_bool(_as_dict(payload).get("success")),
    )


# --- Availability schedules -------------------------------------------------


class CreateAvailabilityScheduleInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="Human-readable name for the schedule")
    user_id: str = Field(description="User ID the schedule belongs to")
    timezone: str = Field(description="IANA timezone identifier, e.g. America/New_York")
    rules: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Availability rules, each with 'type' (wday or date), 'intervals' "
            "of {from,to} in HH:MM, plus 'day' or 'date'"
        ),
    )
    calendar_ids: list[str] | None = Field(
        default=None, description="Calendar IDs the schedule applies to"
    )


@tool(args_schema=CreateAvailabilityScheduleInput)
@serialize_pydantic_return
async def create_availability_schedule(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    user_id: str,
    timezone: str,
    rules: list[dict[str, Any]] | None = None,
    calendar_ids: list[str] | None = None,
) -> CreateAvailabilityScheduleOutput:
    """Create a user availability schedule for GoHighLevel calendars."""
    location_id = _location_id(auth_data)
    if not location_id:
        return CreateAvailabilityScheduleOutput(success=False, error=_MISSING_LOCATION)
    body: dict[str, Any] = {
        "locationId": location_id,
        "name": name,
        "userId": user_id,
        "timezone": timezone,
        "rules": rules,
        "calendarIds": calendar_ids,
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/calendars/schedules", json_body=body
    )
    if error is not None:
        return CreateAvailabilityScheduleOutput(success=False, error=error)
    return CreateAvailabilityScheduleOutput(
        success=True,
        schedule=_parse_availability_schedule(_as_dict(payload).get("schedule")),
    )


class ListAvailabilitySchedulesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_id: str = Field(description="User ID whose schedules are fetched")
    calendar_id: str | None = Field(
        default=None, description="Only return schedules linked to this calendar"
    )
    skip: int | None = Field(default=None, description="Number of schedules to skip")
    limit: int | None = Field(
        default=None, description="Maximum number of schedules to return (max 500)"
    )


@tool(args_schema=ListAvailabilitySchedulesInput)
@serialize_pydantic_return
async def list_availability_schedules(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str,
    calendar_id: str | None = None,
    skip: int | None = None,
    limit: int | None = None,
) -> ListAvailabilitySchedulesOutput:
    """List the availability schedules configured for a GoHighLevel user."""
    location_id = _location_id(auth_data)
    if not location_id:
        return ListAvailabilitySchedulesOutput(success=False, error=_MISSING_LOCATION)
    params: dict[str, Any] = {
        "locationId": location_id,
        "userId": user_id,
        "calendarId": calendar_id,
        "skip": skip,
        "limit": limit,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/calendars/schedules/search", params=params
    )
    if error is not None:
        return ListAvailabilitySchedulesOutput(success=False, error=error)
    body = _as_dict(payload)
    schedules = _as_dict_list(body.get("schedules"))
    return ListAvailabilitySchedulesOutput(
        success=True,
        schedules=[_parse_availability_schedule(item) for item in schedules],
    )


class GetAvailabilityScheduleInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    schedule_id: str = Field(description="The unique identifier of the schedule")


@tool(args_schema=GetAvailabilityScheduleInput)
@serialize_pydantic_return
async def get_availability_schedule(
    auth_type: str,
    auth_data: dict[str, Any],
    schedule_id: str,
) -> GetAvailabilityScheduleOutput:
    """Fetch one GoHighLevel user availability schedule by its ID."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/calendars/schedules/{_seg(schedule_id)}"
    )
    if error is not None:
        return GetAvailabilityScheduleOutput(success=False, error=error)
    return GetAvailabilityScheduleOutput(
        success=True,
        schedule=_parse_availability_schedule(_as_dict(payload).get("schedule")),
    )


class UpdateAvailabilityScheduleInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    schedule_id: str = Field(description="The unique identifier of the schedule to update")
    name: str | None = Field(default=None, description="Human-readable name for the schedule")
    timezone: str | None = Field(
        default=None, description="IANA timezone identifier, e.g. America/New_York"
    )
    rules: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Availability rules, each with 'type' (wday or date), 'intervals' "
            "of {from,to} in HH:MM, plus 'day' or 'date'"
        ),
    )


@tool(args_schema=UpdateAvailabilityScheduleInput)
@serialize_pydantic_return
async def update_availability_schedule(
    auth_type: str,
    auth_data: dict[str, Any],
    schedule_id: str,
    name: str | None = None,
    timezone: str | None = None,
    rules: list[dict[str, Any]] | None = None,
) -> UpdateAvailabilityScheduleOutput:
    """Update a user availability schedule; only supplied fields change."""
    body: dict[str, Any] = {"name": name, "timezone": timezone, "rules": rules}
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/calendars/schedules/{_seg(schedule_id)}",
        json_body=body,
        send_body=True,
    )
    if error is not None:
        return UpdateAvailabilityScheduleOutput(success=False, error=error)
    return UpdateAvailabilityScheduleOutput(
        success=True,
        schedule=_parse_availability_schedule(_as_dict(payload).get("schedule")),
    )


class DeleteAvailabilityScheduleInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    schedule_id: str = Field(description="The unique identifier of the schedule to delete")


@tool(args_schema=DeleteAvailabilityScheduleInput)
@serialize_pydantic_return
async def delete_availability_schedule(
    auth_type: str,
    auth_data: dict[str, Any],
    schedule_id: str,
) -> DeleteAvailabilityScheduleOutput:
    """Permanently delete a GoHighLevel user availability schedule."""
    payload, error = await _request(
        auth_type, auth_data, "DELETE", f"/calendars/schedules/{_seg(schedule_id)}"
    )
    if error is not None:
        return DeleteAvailabilityScheduleOutput(success=False, error=error)
    return DeleteAvailabilityScheduleOutput(
        success=True,
        deleted=_as_bool(_as_dict(payload).get("success")),
    )


class AttachScheduleToCalendarInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    schedule_id: str = Field(description="The unique identifier of the schedule")
    calendar_id: str = Field(
        description="The unique identifier of the team calendar to add to the schedule"
    )


@tool(args_schema=AttachScheduleToCalendarInput)
@serialize_pydantic_return
async def attach_schedule_to_calendar(
    auth_type: str,
    auth_data: dict[str, Any],
    schedule_id: str,
    calendar_id: str,
) -> AttachScheduleToCalendarOutput:
    """Apply a user availability schedule to a GoHighLevel team calendar."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/calendars/schedules/{_seg(schedule_id)}/associations/{_seg(calendar_id)}",
    )
    if error is not None:
        return AttachScheduleToCalendarOutput(success=False, error=error)
    return AttachScheduleToCalendarOutput(
        success=True,
        attached=_as_bool(_as_dict(payload).get("success")),
    )


class DetachScheduleFromCalendarInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    schedule_id: str = Field(description="The unique identifier of the schedule")
    calendar_id: str = Field(
        description="The unique identifier of the calendar to remove from the schedule"
    )


@tool(args_schema=DetachScheduleFromCalendarInput)
@serialize_pydantic_return
async def detach_schedule_from_calendar(
    auth_type: str,
    auth_data: dict[str, Any],
    schedule_id: str,
    calendar_id: str,
) -> DetachScheduleFromCalendarOutput:
    """Remove a user availability schedule from a GoHighLevel calendar."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "DELETE",
        f"/calendars/schedules/{_seg(schedule_id)}/associations/{_seg(calendar_id)}",
    )
    if error is not None:
        return DetachScheduleFromCalendarOutput(success=False, error=error)
    return DetachScheduleFromCalendarOutput(
        success=True,
        detached=_as_bool(_as_dict(payload).get("success")),
    )


# --- Single calendar CRUD ---------------------------------------------------


class UpdateCalendarInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    calendar_id: str = Field(description="The unique identifier of the calendar to update")
    name: str | None = Field(default=None, description="The name of the calendar")
    description: str | None = Field(default=None, description="A description of the calendar")
    slug: str | None = Field(default=None, description="URL slug for the booking page")
    widget_slug: str | None = Field(default=None, description="Slug for the booking widget")
    widget_type: str | None = Field(
        default=None,
        description="Widget layout: 'default' for the neo layout, 'classic' for classic",
    )
    group_id: str | None = Field(default=None, description="Calendar group ID")
    event_type: str | None = Field(
        default=None,
        description=(
            "Round-robin strategy: RoundRobin_OptimizeForAvailability or "
            "RoundRobin_OptimizeForEqualDistribution"
        ),
    )
    event_title: str | None = Field(
        default=None, description="Template for the event title (supports merge fields)"
    )
    event_color: str | None = Field(default=None, description="Colour used for events")
    is_active: bool | None = Field(
        default=None, description="Whether the calendar is active (published) or a draft"
    )
    meeting_location: str | None = Field(
        default=None,
        description="Deprecated upstream; prefer location_configurations",
    )
    location_configurations: list[dict[str, Any]] | None = Field(
        default=None,
        description="Meeting location configurations, each with 'kind' and 'location'",
    )
    team_members: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Team members assigned to the calendar; required for round_robin, "
            "collective, class_booking and service_booking calendars"
        ),
    )
    slot_duration: float | None = Field(default=None, description="Duration of the meeting")
    slot_duration_unit: str | None = Field(
        default=None, description="Unit for slot duration: mins or hours"
    )
    slot_interval: float | None = Field(
        default=None, description="Time between the booking slots shown on the calendar"
    )
    slot_interval_unit: str | None = Field(
        default=None, description="Unit for slot interval: mins or hours"
    )
    slot_buffer: float | None = Field(
        default=None, description="Extra time added after an appointment"
    )
    pre_buffer: float | None = Field(
        default=None, description="Extra time added before an appointment"
    )
    pre_buffer_unit: str | None = Field(
        default=None, description="Unit for pre-buffer: mins or hours"
    )
    appointment_per_slot: float | None = Field(
        default=None, description="Maximum bookings per slot (seats per slot for class booking)"
    )
    appointment_per_day: float | None = Field(
        default=None, description="Number of appointments bookable on a given day"
    )
    allow_booking_after: float | None = Field(
        default=None, description="Minimum scheduling notice for events"
    )
    allow_booking_after_unit: str | None = Field(
        default=None, description="Unit for minimum scheduling notice: hours, days, weeks or months"
    )
    allow_booking_for: float | None = Field(
        default=None, description="How far ahead events may be booked"
    )
    allow_booking_for_unit: str | None = Field(
        default=None, description="Unit for the booking window: days, weeks or months"
    )
    open_hours: list[dict[str, Any]] | None = Field(
        default=None,
        description="Standard availability windows; use availabilities for custom dates",
    )
    availabilities: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Custom date availability; include the entry 'id' to modify or "
            "delete an existing custom date"
        ),
    )
    availability_type: float | None = Field(
        default=None,
        description="1 uses only custom availabilities, 0 uses only open hours",
    )
    enable_recurring: bool | None = Field(
        default=None, description="Enable recurring appointments on this calendar"
    )
    recurring: dict[str, Any] | None = Field(
        default=None, description="Recurring appointment configuration"
    )
    form_id: str | None = Field(default=None, description="Custom intake form ID")
    sticky_contact: bool | None = Field(default=None, description="Enable sticky contact")
    is_live_payment_mode: bool | None = Field(
        default=None, description="Whether payments are taken in live mode"
    )
    auto_confirm: bool | None = Field(
        default=None, description="Automatically confirm bookings without manual approval"
    )
    should_send_alert_emails_to_assigned_member: bool | None = Field(
        default=None, description="Send booking alert emails to the assigned member"
    )
    alert_email: str | None = Field(default=None, description="Email address to receive alerts")
    google_invitation_emails: bool | None = Field(
        default=None, description="Send Google calendar invitation emails"
    )
    allow_reschedule: bool | None = Field(
        default=None, description="Allow bookers to reschedule"
    )
    allow_cancellation: bool | None = Field(
        default=None, description="Allow bookers to cancel"
    )
    should_assign_contact_to_team_member: bool | None = Field(
        default=None, description="Assign the booking contact to the team member"
    )
    should_skip_assigning_contact_for_existing: bool | None = Field(
        default=None, description="Skip contact assignment when the contact already exists"
    )
    notes: str | None = Field(default=None, description="Internal notes about the calendar")
    pixel_id: str | None = Field(default=None, description="Tracking pixel ID")
    form_submit_type: str | None = Field(
        default=None, description="After submit behaviour: RedirectURL or ThankYouMessage"
    )
    form_submit_redirect_url: str | None = Field(
        default=None, description="Redirect URL used when form_submit_type is RedirectURL"
    )
    form_submit_thanks_message: str | None = Field(
        default=None, description="Thank-you message shown after submission"
    )
    guest_type: str | None = Field(
        default=None, description="Guest handling: count_only or collect_detail"
    )
    consent_label: str | None = Field(default=None, description="Consent checkbox label")
    calendar_cover_image: str | None = Field(default=None, description="Cover image URL")
    look_busy_config: dict[str, Any] | None = Field(
        default=None,
        description="Look-busy settings with 'enabled' and 'LookBusyPercentage'",
    )
    notifications: list[dict[str, Any]] | None = Field(
        default=None,
        description="Deprecated upstream; prefer the calendar notification actions",
    )


@tool(args_schema=UpdateCalendarInput)
@serialize_pydantic_return
async def update_calendar(
    auth_type: str,
    auth_data: dict[str, Any],
    calendar_id: str,
    name: str | None = None,
    description: str | None = None,
    slug: str | None = None,
    widget_slug: str | None = None,
    widget_type: str | None = None,
    group_id: str | None = None,
    event_type: str | None = None,
    event_title: str | None = None,
    event_color: str | None = None,
    is_active: bool | None = None,
    meeting_location: str | None = None,
    location_configurations: list[dict[str, Any]] | None = None,
    team_members: list[dict[str, Any]] | None = None,
    slot_duration: float | None = None,
    slot_duration_unit: str | None = None,
    slot_interval: float | None = None,
    slot_interval_unit: str | None = None,
    slot_buffer: float | None = None,
    pre_buffer: float | None = None,
    pre_buffer_unit: str | None = None,
    appointment_per_slot: float | None = None,
    appointment_per_day: float | None = None,
    allow_booking_after: float | None = None,
    allow_booking_after_unit: str | None = None,
    allow_booking_for: float | None = None,
    allow_booking_for_unit: str | None = None,
    open_hours: list[dict[str, Any]] | None = None,
    availabilities: list[dict[str, Any]] | None = None,
    availability_type: float | None = None,
    enable_recurring: bool | None = None,
    recurring: dict[str, Any] | None = None,
    form_id: str | None = None,
    sticky_contact: bool | None = None,
    is_live_payment_mode: bool | None = None,
    auto_confirm: bool | None = None,
    should_send_alert_emails_to_assigned_member: bool | None = None,
    alert_email: str | None = None,
    google_invitation_emails: bool | None = None,
    allow_reschedule: bool | None = None,
    allow_cancellation: bool | None = None,
    should_assign_contact_to_team_member: bool | None = None,
    should_skip_assigning_contact_for_existing: bool | None = None,
    notes: str | None = None,
    pixel_id: str | None = None,
    form_submit_type: str | None = None,
    form_submit_redirect_url: str | None = None,
    form_submit_thanks_message: str | None = None,
    guest_type: str | None = None,
    consent_label: str | None = None,
    calendar_cover_image: str | None = None,
    look_busy_config: dict[str, Any] | None = None,
    notifications: list[dict[str, Any]] | None = None,
) -> UpdateCalendarOutput:
    """Update a GoHighLevel booking calendar; only supplied fields change.

    Note that ``slot_buffer_unit`` is not accepted by the upstream update
    operation even though the create operation accepts it.
    """
    body: dict[str, Any] = {
        "name": name,
        "description": description,
        "slug": slug,
        "widgetSlug": widget_slug,
        "widgetType": widget_type,
        "groupId": group_id,
        "eventType": event_type,
        "eventTitle": event_title,
        "eventColor": event_color,
        "isActive": is_active,
        "meetingLocation": meeting_location,
        "locationConfigurations": location_configurations,
        "teamMembers": team_members,
        "slotDuration": slot_duration,
        "slotDurationUnit": slot_duration_unit,
        "slotInterval": slot_interval,
        "slotIntervalUnit": slot_interval_unit,
        "slotBuffer": slot_buffer,
        "preBuffer": pre_buffer,
        "preBufferUnit": pre_buffer_unit,
        "appoinmentPerSlot": appointment_per_slot,
        "appoinmentPerDay": appointment_per_day,
        "allowBookingAfter": allow_booking_after,
        "allowBookingAfterUnit": allow_booking_after_unit,
        "allowBookingFor": allow_booking_for,
        "allowBookingForUnit": allow_booking_for_unit,
        "openHours": open_hours,
        "availabilities": availabilities,
        "availabilityType": availability_type,
        "enableRecurring": enable_recurring,
        "recurring": recurring,
        "formId": form_id,
        "stickyContact": sticky_contact,
        "isLivePaymentMode": is_live_payment_mode,
        "autoConfirm": auto_confirm,
        "shouldSendAlertEmailsToAssignedMember": should_send_alert_emails_to_assigned_member,
        "alertEmail": alert_email,
        "googleInvitationEmails": google_invitation_emails,
        "allowReschedule": allow_reschedule,
        "allowCancellation": allow_cancellation,
        "shouldAssignContactToTeamMember": should_assign_contact_to_team_member,
        "shouldSkipAssigningContactForExisting": should_skip_assigning_contact_for_existing,
        "notes": notes,
        "pixelId": pixel_id,
        "formSubmitType": form_submit_type,
        "formSubmitRedirectURL": form_submit_redirect_url,
        "formSubmitThanksMessage": form_submit_thanks_message,
        "guestType": guest_type,
        "consentLabel": consent_label,
        "calendarCoverImage": calendar_cover_image,
        "lookBusyConfig": look_busy_config,
        "notifications": notifications,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/calendars/{_seg(calendar_id)}",
        json_body=body,
        send_body=True,
    )
    if error is not None:
        return UpdateCalendarOutput(success=False, error=error)
    return UpdateCalendarOutput(
        success=True,
        calendar=_parse_calendar(_as_dict(payload).get("calendar")),
    )


class GetCalendarInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    calendar_id: str = Field(description="The unique identifier of the calendar to retrieve")


@tool(args_schema=GetCalendarInput)
@serialize_pydantic_return
async def get_calendar(
    auth_type: str,
    auth_data: dict[str, Any],
    calendar_id: str,
) -> GetCalendarOutput:
    """Fetch the full configuration of one GoHighLevel booking calendar."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/calendars/{_seg(calendar_id)}"
    )
    if error is not None:
        return GetCalendarOutput(success=False, error=error)
    return GetCalendarOutput(
        success=True,
        calendar=_parse_calendar(_as_dict(payload).get("calendar")),
    )


class DeleteCalendarInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    calendar_id: str = Field(description="The unique identifier of the calendar to delete")


@tool(args_schema=DeleteCalendarInput)
@serialize_pydantic_return
async def delete_calendar(
    auth_type: str,
    auth_data: dict[str, Any],
    calendar_id: str,
) -> DeleteCalendarOutput:
    """Permanently delete a GoHighLevel booking calendar."""
    payload, error = await _request(
        auth_type, auth_data, "DELETE", f"/calendars/{_seg(calendar_id)}"
    )
    if error is not None:
        return DeleteCalendarOutput(success=False, error=error)
    return DeleteCalendarOutput(
        success=True,
        deleted=_as_bool(_as_dict(payload).get("success")),
    )


class GetCalendarFreeSlotsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    calendar_id: str = Field(description="The calendar to read free slots from")
    start_date: int = Field(
        description="Start of the range, epoch milliseconds. Range must be 31 days or less"
    )
    end_date: int = Field(
        description="End of the range, epoch milliseconds. Range must be 31 days or less"
    )
    timezone: str | None = Field(
        default=None, description="Timezone the free slots are returned in"
    )
    user_id: str | None = Field(
        default=None, description="Return free slots for this single user"
    )
    user_ids: list[str] | None = Field(
        default=None, description="Return free slots for these users"
    )


@tool(args_schema=GetCalendarFreeSlotsInput)
@serialize_pydantic_return
async def get_calendar_free_slots(
    auth_type: str,
    auth_data: dict[str, Any],
    calendar_id: str,
    start_date: int,
    end_date: int,
    timezone: str | None = None,
    user_id: str | None = None,
    user_ids: list[str] | None = None,
) -> GetCalendarFreeSlotsOutput:
    """Find bookable free slots on a GoHighLevel calendar in a date range."""
    params: dict[str, Any] = {
        "startDate": start_date,
        "endDate": end_date,
        "timezone": timezone,
        "userId": user_id,
        "userIds": user_ids,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "GET",
        f"/calendars/{_seg(calendar_id)}/free-slots",
        params=params,
    )
    if error is not None:
        return GetCalendarFreeSlotsOutput(success=False, error=error)
    return GetCalendarFreeSlotsOutput(success=True, days=_parse_calendar_free_slots(payload))


# --- Calendar notifications -------------------------------------------------


class ListCalendarNotificationsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    calendar_id: str = Field(description="The calendar whose notifications are listed")
    is_active: bool | None = Field(
        default=None, description="Filter notifications by their active status"
    )
    deleted: bool | None = Field(
        default=None, description="Filter notifications by their deleted status"
    )
    limit: int | None = Field(
        default=None, description="Maximum number of notifications to return"
    )
    skip: int | None = Field(default=None, description="Number of notifications to skip")


@tool(args_schema=ListCalendarNotificationsInput)
@serialize_pydantic_return
async def list_calendar_notifications(
    auth_type: str,
    auth_data: dict[str, Any],
    calendar_id: str,
    is_active: bool | None = None,
    deleted: bool | None = None,
    limit: int | None = None,
    skip: int | None = None,
) -> ListCalendarNotificationsOutput:
    """List the notification rules configured on a GoHighLevel calendar."""
    params: dict[str, Any] = {
        "isActive": is_active,
        "deleted": deleted,
        "limit": limit,
        "skip": skip,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "GET",
        f"/calendars/{_seg(calendar_id)}/notifications",
        params=params,
    )
    if error is not None:
        return ListCalendarNotificationsOutput(success=False, error=error)
    return ListCalendarNotificationsOutput(
        success=True,
        notifications=[_parse_calendar_notification(item) for item in _as_dict_list(payload)],
    )


class CreateCalendarNotificationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    calendar_id: str = Field(description="The calendar to create notifications for")
    notifications: list[dict[str, Any]] = Field(
        description=(
            "Notification configurations. Each entry needs 'receiverType' "
            "(contact, guest, assignedUser, emails, phoneNumbers, business), "
            "'channel' (email, inApp, sms, whatsapp) and 'notificationType' "
            "(booked, confirmation, cancellation, reminder, followup, "
            "reschedule); optional keys include isActive, templateId, body, "
            "subject, beforeTime, afterTime, additionalEmailIds, "
            "additionalPhoneNumbers, selectedUsers, fromAddress, fromName "
            "and fromNumber"
        )
    )


@tool(args_schema=CreateCalendarNotificationInput)
@serialize_pydantic_return
async def create_calendar_notification(
    auth_type: str,
    auth_data: dict[str, Any],
    calendar_id: str,
    notifications: list[dict[str, Any]],
) -> CreateCalendarNotificationOutput:
    """Create one or more notification rules on a GoHighLevel calendar."""
    # The upstream operation takes a top-level JSON array, not an object.
    body = [_clean_body(item) for item in notifications]
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        f"/calendars/{_seg(calendar_id)}/notifications",
        json_body=body,
    )
    if error is not None:
        return CreateCalendarNotificationOutput(success=False, error=error)
    return CreateCalendarNotificationOutput(
        success=True,
        notifications=[_parse_calendar_notification(item) for item in _as_dict_list(payload)],
    )


class GetCalendarNotificationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    calendar_id: str = Field(description="The calendar that owns the notification")
    notification_id: str = Field(description="The unique identifier of the notification")


@tool(args_schema=GetCalendarNotificationInput)
@serialize_pydantic_return
async def get_calendar_notification(
    auth_type: str,
    auth_data: dict[str, Any],
    calendar_id: str,
    notification_id: str,
) -> GetCalendarNotificationOutput:
    """Fetch one notification rule from a GoHighLevel calendar."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "GET",
        f"/calendars/{_seg(calendar_id)}/notifications/{_seg(notification_id)}",
    )
    if error is not None:
        return GetCalendarNotificationOutput(success=False, error=error)
    return GetCalendarNotificationOutput(
        success=True,
        notification=_parse_calendar_notification(payload),
    )


class UpdateCalendarNotificationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    calendar_id: str = Field(description="The calendar that owns the notification")
    notification_id: str = Field(
        description="The unique identifier of the notification to update"
    )
    receiver_type: str | None = Field(
        default=None,
        description=(
            "Recipient type: contact, guest, assignedUser, emails, "
            "phoneNumbers or business"
        ),
    )
    channel: str | None = Field(
        default=None, description="Notification channel: email, inApp, sms or whatsapp"
    )
    notification_type: str | None = Field(
        default=None,
        description=(
            "Notification type: booked, confirmation, cancellation, reminder, "
            "followup or reschedule"
        ),
    )
    is_active: bool | None = Field(default=None, description="Whether the rule is active")
    deleted: bool | None = Field(
        default=None, description="Marks the notification as deleted (soft delete)"
    )
    template_id: str | None = Field(
        default=None, description="Template ID for an email notification"
    )
    body: str | None = Field(default=None, description="Body for an email notification")
    subject: str | None = Field(default=None, description="Subject for an email notification")
    before_time: list[dict[str, Any]] | None = Field(
        default=None,
        description="Reminder offsets before the event, each {timeOffset, unit}",
    )
    after_time: list[dict[str, Any]] | None = Field(
        default=None,
        description="Follow-up offsets after the event, each {timeOffset, unit}",
    )
    additional_email_ids: list[str] | None = Field(
        default=None, description="Extra email addresses to notify"
    )
    additional_phone_numbers: list[str] | None = Field(
        default=None, description="Extra phone numbers to notify"
    )
    selected_users: list[str] | None = Field(
        default=None,
        description="User IDs for in-App and business email notifications",
    )
    from_address: str | None = Field(
        default=None, description="From address for an email notification"
    )
    from_name: str | None = Field(
        default=None, description="From name for an email or SMS notification"
    )
    from_number: str | None = Field(
        default=None, description="From number for an SMS notification"
    )


@tool(args_schema=UpdateCalendarNotificationInput)
@serialize_pydantic_return
async def update_calendar_notification(
    auth_type: str,
    auth_data: dict[str, Any],
    calendar_id: str,
    notification_id: str,
    receiver_type: str | None = None,
    channel: str | None = None,
    notification_type: str | None = None,
    is_active: bool | None = None,
    deleted: bool | None = None,
    template_id: str | None = None,
    body: str | None = None,
    subject: str | None = None,
    before_time: list[dict[str, Any]] | None = None,
    after_time: list[dict[str, Any]] | None = None,
    additional_email_ids: list[str] | None = None,
    additional_phone_numbers: list[str] | None = None,
    selected_users: list[str] | None = None,
    from_address: str | None = None,
    from_name: str | None = None,
    from_number: str | None = None,
) -> UpdateCalendarNotificationOutput:
    """Update one notification rule on a GoHighLevel calendar."""
    json_body: dict[str, Any] = {
        "receiverType": receiver_type,
        "channel": channel,
        "notificationType": notification_type,
        "isActive": is_active,
        "deleted": deleted,
        "templateId": template_id,
        "body": body,
        "subject": subject,
        "beforeTime": before_time,
        "afterTime": after_time,
        "additionalEmailIds": additional_email_ids,
        "additionalPhoneNumbers": additional_phone_numbers,
        "selectedUsers": selected_users,
        "fromAddress": from_address,
        "fromName": from_name,
        "fromNumber": from_number,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "PUT",
        f"/calendars/{_seg(calendar_id)}/notifications/{_seg(notification_id)}",
        json_body=json_body,
        send_body=True,
    )
    if error is not None:
        return UpdateCalendarNotificationOutput(success=False, error=error)
    return UpdateCalendarNotificationOutput(
        success=True,
        message=_as_str(_as_dict(payload).get("message")),
    )


class DeleteCalendarNotificationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    calendar_id: str = Field(description="The calendar that owns the notification")
    notification_id: str = Field(
        description="The unique identifier of the notification to delete"
    )


@tool(args_schema=DeleteCalendarNotificationInput)
@serialize_pydantic_return
async def delete_calendar_notification(
    auth_type: str,
    auth_data: dict[str, Any],
    calendar_id: str,
    notification_id: str,
) -> DeleteCalendarNotificationOutput:
    """Permanently delete a notification rule from a GoHighLevel calendar."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "DELETE",
        f"/calendars/{_seg(calendar_id)}/notifications/{_seg(notification_id)}",
    )
    if error is not None:
        return DeleteCalendarNotificationOutput(success=False, error=error)
    return DeleteCalendarNotificationOutput(
        success=True,
        message=_as_str(_as_dict(payload).get("message")),
    )

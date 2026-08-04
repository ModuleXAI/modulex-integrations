"""Happy-path tests for every GoHighLevel action, plus the failure paths.

Beyond one success test per action, the suite pins the behaviours that are
easy to regress across 117 actions sharing one request helper: a non-2xx
folds into ``success=False`` instead of raising, a missing location ID is
caught before any HTTP call, and a 200 whose fields carry the wrong *types*
still returns ``success=True`` rather than escaping as a ValidationError.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from modulex_integrations.tools.gohighlevel import (
    TOOLS,
    manifest,
)
from modulex_integrations.tools.gohighlevel.outputs import (
    AddContactFollowersOutput,
    AddContactTagsOutput,
    AddContactToCampaignOutput,
    AddContactToWorkflowOutput,
    AddInboundMessageOutput,
    AddMessageAttachmentsOutput,
    AddOpportunityFollowersOutput,
    AddOutboundMessageOutput,
    AttachScheduleToCalendarOutput,
    BulkUpdateContactsBusinessOutput,
    BulkUpdateContactTagsOutput,
    CancelScheduledEmailMessageOutput,
    CancelScheduledMessageOutput,
    CompleteContactTaskOutput,
    CompleteMessageFileUploadOutput,
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
from modulex_integrations.tools.gohighlevel.tools import (
    _api_version,
    add_contact_followers,
    add_contact_tags,
    add_contact_to_campaign,
    add_contact_to_workflow,
    add_inbound_message,
    add_message_attachments,
    add_opportunity_followers,
    add_outbound_message,
    attach_schedule_to_calendar,
    bulk_update_contact_tags,
    bulk_update_contacts_business,
    cancel_scheduled_email_message,
    cancel_scheduled_message,
    complete_contact_task,
    complete_message_file_upload,
    create_appointment,
    create_appointment_note,
    create_availability_schedule,
    create_block_slot,
    create_calendar,
    create_calendar_group,
    create_calendar_notification,
    create_calendar_resource,
    create_contact,
    create_contact_note,
    create_contact_task,
    create_conversation,
    create_custom_subtype,
    create_email_template,
    create_opportunity,
    delete_appointment_note,
    delete_availability_schedule,
    delete_calendar,
    delete_calendar_group,
    delete_calendar_notification,
    delete_calendar_resource,
    delete_contact,
    delete_contact_from_workflow,
    delete_contact_note,
    delete_contact_task,
    delete_conversation,
    delete_email_template,
    delete_event,
    delete_opportunity,
    detach_schedule_from_calendar,
    export_messages,
    get_appointment,
    get_availability_schedule,
    get_calendar,
    get_calendar_free_slots,
    get_calendar_notification,
    get_calendar_resource,
    get_contact,
    get_contact_note,
    get_contact_task,
    get_contact_unsubscription_status,
    get_conversation,
    get_duplicate_contact,
    get_email_by_id,
    get_message,
    get_message_transcription,
    get_opportunity,
    initiate_message_file_upload,
    list_appointment_notes,
    list_availability_schedules,
    list_blocked_slots,
    list_business_contacts,
    list_calendar_events,
    list_calendar_groups,
    list_calendar_notifications,
    list_calendar_resources,
    list_calendars,
    list_campaigns,
    list_contact_appointments,
    list_contact_notes,
    list_contact_tasks,
    list_contacts,
    list_conversation_messages,
    list_custom_subtypes,
    list_email_templates,
    list_opportunity_lost_reasons,
    list_pipelines,
    list_scheduled_emails,
    live_chat_agent_typing,
    remove_contact_followers,
    remove_contact_from_campaign,
    remove_contact_from_every_campaign,
    remove_contact_tags,
    remove_opportunity_followers,
    search_contacts,
    search_conversations,
    search_opportunities,
    search_opportunities_advanced,
    send_message,
    send_review_reply,
    set_calendar_group_status,
    update_appointment,
    update_appointment_note,
    update_availability_schedule,
    update_block_slot,
    update_calendar,
    update_calendar_group,
    update_calendar_notification,
    update_calendar_resource,
    update_contact,
    update_contact_note,
    update_contact_task,
    update_conversation,
    update_custom_subtype,
    update_email_template,
    update_message_status,
    update_opportunity,
    update_opportunity_status,
    update_subscription_preference,
    upsert_contact,
    upsert_opportunity,
    validate_calendar_group_slug,
)

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {
        "access_token": "test-access-token",
        "location_id": "ve9EPM428h8vShlRW1KT",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    """Bypass mypy's TypedDict-spread check on LangChain's .ainvoke()."""
    return dict(_AUTH, **extra)


def _no_location(**extra: Any) -> dict[str, Any]:
    """Same credential set with the location ID stripped."""
    return dict(
        _AUTH,
        auth_data={"access_token": "test-access-token"},
        **extra,
    )


class TestManifest:
    def test_manifest_exposes_all_actions(self) -> None:
        assert len(manifest.actions) == 117

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}

    def test_no_action_declares_a_credential_parameter(self) -> None:
        reserved = {"auth_type", "auth_data", "access_token", "token", "api_key",
                    "location_id"}
        for action in manifest.actions:
            assert not (set(action.parameters) & reserved), action.name


_BATCH1_API = "https://services.leadconnectorhq.com"

_BATCH1_NO_LOCATION: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}

_BATCH1_CONTACT: dict[str, Any] = {
    "id": "ct_1",
    "locationId": "loc_1",
    "firstName": "Ada",
    "lastName": "Lovelace",
    "email": "ada@example.com",
    "phone": "+15550001111",
    "tags": ["vip"],
    "customFields": [{"id": "cf_1", "value": "gold"}],
    "dnd": False,
    "dndSettings": {"SMS": {"status": "inactive"}},
}

_BATCH1_TASK: dict[str, Any] = {
    "id": "tk_1",
    "title": "Follow up",
    "dueDate": "2026-01-01T10:00:00Z",
    "completed": False,
    "contactId": "ct_1",
}

_BATCH1_NOTE: dict[str, Any] = {
    "id": "nt_1",
    "body": "Called the lead",
    "contactId": "ct_1",
    "pinned": False,
}

_BATCH1_OPPORTUNITY: dict[str, Any] = {
    "id": "op_1",
    "name": "New roof",
    "monetaryValue": 1500.5,
    "pipelineId": "pl_1",
    "pipelineStageId": "st_1",
    "status": "open",
    "contactId": "ct_1",
    "locationId": "loc_1",
    "contact": {"id": "ct_1", "name": "Ada Lovelace", "tags": ["vip"]},
    "customFields": [{"id": "cf_9", "fieldValue": ["a", "b"]}],
}


class TestContactRecords:
    @pytest.mark.asyncio
    async def test_create_contact(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/contacts/",
            json={"contact": _BATCH1_CONTACT},
        )

        result_dict = await create_contact.ainvoke(_args(first_name="Ada", email="ada@example.com"))

        assert isinstance(result_dict, dict)
        result = CreateContactOutput.model_validate(result_dict)
        assert result.success is True
        assert result.contact is not None
        assert result.contact.id == "ct_1"

    @pytest.mark.asyncio
    async def test_list_contacts(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            json={"contacts": [_BATCH1_CONTACT], "count": 1},
        )

        result_dict = await list_contacts.ainvoke(_args(limit=5))

        assert isinstance(result_dict, dict)
        result = ListContactsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.count == 1
        assert result.contacts[0].first_name == "Ada"

    @pytest.mark.asyncio
    async def test_get_contact(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_BATCH1_API}/contacts/ct_1",
            json={"contact": _BATCH1_CONTACT},
        )

        result_dict = await get_contact.ainvoke(_args(contact_id="ct_1"))

        assert isinstance(result_dict, dict)
        result = GetContactOutput.model_validate(result_dict)
        assert result.success is True
        assert result.contact is not None
        assert result.contact.tags == ["vip"]

    @pytest.mark.asyncio
    async def test_update_contact(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_BATCH1_API}/contacts/ct_1",
            json={"succeded": True, "contact": _BATCH1_CONTACT},
        )

        result_dict = await update_contact.ainvoke(_args(contact_id="ct_1", city="London"))

        assert isinstance(result_dict, dict)
        result = UpdateContactOutput.model_validate(result_dict)
        assert result.success is True
        assert result.succeeded is True

    @pytest.mark.asyncio
    async def test_delete_contact(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_BATCH1_API}/contacts/ct_1",
            json={"succeded": True},
        )

        result_dict = await delete_contact.ainvoke(_args(contact_id="ct_1"))

        assert isinstance(result_dict, dict)
        result = DeleteContactOutput.model_validate(result_dict)
        assert result.success is True
        assert result.succeeded is True

    @pytest.mark.asyncio
    async def test_upsert_contact(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/contacts/upsert",
            json={"new": True, "contact": _BATCH1_CONTACT, "traceId": "tr_1"},
        )

        result_dict = await upsert_contact.ainvoke(_args(email="ada@example.com"))

        assert isinstance(result_dict, dict)
        result = UpsertContactOutput.model_validate(result_dict)
        assert result.success is True
        assert result.new is True
        assert result.trace_id == "tr_1"

    @pytest.mark.asyncio
    async def test_search_contacts(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/contacts/search",
            json={"contacts": [_BATCH1_CONTACT], "total": 1},
        )

        result_dict = await search_contacts.ainvoke(_args(page_limit=10))

        assert isinstance(result_dict, dict)
        result = SearchContactsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_get_duplicate_contact(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(method="GET", json={"contact": _BATCH1_CONTACT})

        result_dict = await get_duplicate_contact.ainvoke(_args(email="ada@example.com"))

        assert isinstance(result_dict, dict)
        result = GetDuplicateContactOutput.model_validate(result_dict)
        assert result.success is True
        assert result.contact is not None

    @pytest.mark.asyncio
    async def test_list_business_contacts(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            json={"contacts": [_BATCH1_CONTACT], "count": 1},
        )

        result_dict = await list_business_contacts.ainvoke(_args(business_id="bz_1", limit=2))

        assert isinstance(result_dict, dict)
        result = ListBusinessContactsOutput.model_validate(result_dict)
        assert result.success is True
        assert len(result.contacts) == 1

    @pytest.mark.asyncio
    async def test_bulk_update_contacts_business(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/contacts/bulk/business",
            json={"success": True, "ids": ["ct_1", "ct_2"]},
        )

        result_dict = await bulk_update_contacts_business.ainvoke(
            _args(contact_ids=["ct_1", "ct_2"], business_id="bz_1")
        )

        assert isinstance(result_dict, dict)
        result = BulkUpdateContactsBusinessOutput.model_validate(result_dict)
        assert result.success is True
        assert result.ids == ["ct_1", "ct_2"]

    @pytest.mark.asyncio
    async def test_bulk_update_contact_tags(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/contacts/bulk/tags/update/add",
            json={"succeded": True, "errorCount": 0, "responses": ["ok"]},
        )

        result_dict = await bulk_update_contact_tags.ainvoke(
            _args(operation="add", contact_ids=["ct_1"], tags=["vip"])
        )

        assert isinstance(result_dict, dict)
        result = BulkUpdateContactTagsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.error_count == 0

    @pytest.mark.asyncio
    async def test_list_contact_appointments(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_BATCH1_API}/contacts/ct_1/appointments",
            json={"events": [{"id": "ev_1", "calendarId": "cal_1", "title": "Intro call"}]},
        )

        result_dict = await list_contact_appointments.ainvoke(_args(contact_id="ct_1"))

        assert isinstance(result_dict, dict)
        result = ListContactAppointmentsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.events[0].calendar_id == "cal_1"


class TestContactTags:
    @pytest.mark.asyncio
    async def test_add_contact_tags(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/contacts/ct_1/tags",
            json={"tags": ["vip", "new"]},
        )

        result_dict = await add_contact_tags.ainvoke(_args(contact_id="ct_1", tags=["new"]))

        assert isinstance(result_dict, dict)
        result = AddContactTagsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.tags == ["vip", "new"]

    @pytest.mark.asyncio
    async def test_remove_contact_tags(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_BATCH1_API}/contacts/ct_1/tags",
            json={"tags": ["vip"]},
        )

        result_dict = await remove_contact_tags.ainvoke(_args(contact_id="ct_1", tags=["new"]))

        assert isinstance(result_dict, dict)
        result = RemoveContactTagsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.tags == ["vip"]


class TestContactFollowers:
    @pytest.mark.asyncio
    async def test_add_contact_followers(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/contacts/ct_1/followers",
            json={"followers": ["us_1"], "followersAdded": ["us_1"]},
        )

        result_dict = await add_contact_followers.ainvoke(
            _args(contact_id="ct_1", followers=["us_1"])
        )

        assert isinstance(result_dict, dict)
        result = AddContactFollowersOutput.model_validate(result_dict)
        assert result.success is True
        assert result.followers_added == ["us_1"]

    @pytest.mark.asyncio
    async def test_remove_contact_followers(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_BATCH1_API}/contacts/ct_1/followers",
            json={"followers": [], "followersRemoved": ["us_1"]},
        )

        result_dict = await remove_contact_followers.ainvoke(
            _args(contact_id="ct_1", followers=["us_1"])
        )

        assert isinstance(result_dict, dict)
        result = RemoveContactFollowersOutput.model_validate(result_dict)
        assert result.success is True
        assert result.followers_removed == ["us_1"]


class TestContactCampaigns:
    @pytest.mark.asyncio
    async def test_add_contact_to_campaign(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/contacts/ct_1/campaigns/cp_1",
            json={"succeded": True},
        )

        result_dict = await add_contact_to_campaign.ainvoke(
            _args(contact_id="ct_1", campaign_id="cp_1")
        )

        assert isinstance(result_dict, dict)
        result = AddContactToCampaignOutput.model_validate(result_dict)
        assert result.success is True
        assert result.succeeded is True

    @pytest.mark.asyncio
    async def test_remove_contact_from_campaign(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_BATCH1_API}/contacts/ct_1/campaigns/cp_1",
            json={"succeded": True},
        )

        result_dict = await remove_contact_from_campaign.ainvoke(
            _args(contact_id="ct_1", campaign_id="cp_1")
        )

        assert isinstance(result_dict, dict)
        result = RemoveContactFromCampaignOutput.model_validate(result_dict)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_remove_contact_from_every_campaign(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_BATCH1_API}/contacts/ct_1/campaigns/removeAll",
            json={"succeded": True},
        )

        result_dict = await remove_contact_from_every_campaign.ainvoke(_args(contact_id="ct_1"))

        assert isinstance(result_dict, dict)
        result = RemoveContactFromEveryCampaignOutput.model_validate(result_dict)
        assert result.success is True


class TestContactWorkflows:
    @pytest.mark.asyncio
    async def test_add_contact_to_workflow(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/contacts/ct_1/workflow/wf_1",
            json={"succeded": True},
        )

        result_dict = await add_contact_to_workflow.ainvoke(
            _args(contact_id="ct_1", workflow_id="wf_1")
        )

        assert isinstance(result_dict, dict)
        result = AddContactToWorkflowOutput.model_validate(result_dict)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_delete_contact_from_workflow(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_BATCH1_API}/contacts/ct_1/workflow/wf_1",
            json={"succeded": True},
        )

        result_dict = await delete_contact_from_workflow.ainvoke(
            _args(contact_id="ct_1", workflow_id="wf_1")
        )

        assert isinstance(result_dict, dict)
        result = DeleteContactFromWorkflowOutput.model_validate(result_dict)
        assert result.success is True


class TestContactNotes:
    @pytest.mark.asyncio
    async def test_list_contact_notes(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_BATCH1_API}/contacts/ct_1/notes",
            json={"notes": [_BATCH1_NOTE]},
        )

        result_dict = await list_contact_notes.ainvoke(_args(contact_id="ct_1"))

        assert isinstance(result_dict, dict)
        result = ListContactNotesOutput.model_validate(result_dict)
        assert result.success is True
        assert result.notes[0].id == "nt_1"

    @pytest.mark.asyncio
    async def test_create_contact_note(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/contacts/ct_1/notes",
            json={"note": _BATCH1_NOTE},
        )

        result_dict = await create_contact_note.ainvoke(
            _args(contact_id="ct_1", body="Called the lead")
        )

        assert isinstance(result_dict, dict)
        result = CreateContactNoteOutput.model_validate(result_dict)
        assert result.success is True
        assert result.note is not None
        assert result.note.body == "Called the lead"

    @pytest.mark.asyncio
    async def test_get_contact_note(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_BATCH1_API}/contacts/ct_1/notes/nt_1",
            json={"note": _BATCH1_NOTE},
        )

        result_dict = await get_contact_note.ainvoke(_args(contact_id="ct_1", note_id="nt_1"))

        assert isinstance(result_dict, dict)
        result = GetContactNoteOutput.model_validate(result_dict)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_update_contact_note(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_BATCH1_API}/contacts/ct_1/notes/nt_1",
            json={"note": _BATCH1_NOTE},
        )

        result_dict = await update_contact_note.ainvoke(
            _args(contact_id="ct_1", note_id="nt_1", body="Updated")
        )

        assert isinstance(result_dict, dict)
        result = UpdateContactNoteOutput.model_validate(result_dict)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_delete_contact_note(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_BATCH1_API}/contacts/ct_1/notes/nt_1",
            json={"succeded": True},
        )

        result_dict = await delete_contact_note.ainvoke(_args(contact_id="ct_1", note_id="nt_1"))

        assert isinstance(result_dict, dict)
        result = DeleteContactNoteOutput.model_validate(result_dict)
        assert result.success is True


class TestContactTasks:
    @pytest.mark.asyncio
    async def test_list_contact_tasks(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_BATCH1_API}/contacts/ct_1/tasks",
            json={"tasks": [_BATCH1_TASK]},
        )

        result_dict = await list_contact_tasks.ainvoke(_args(contact_id="ct_1"))

        assert isinstance(result_dict, dict)
        result = ListContactTasksOutput.model_validate(result_dict)
        assert result.success is True
        assert result.tasks[0].title == "Follow up"

    @pytest.mark.asyncio
    async def test_create_contact_task(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/contacts/ct_1/tasks",
            json={"task": _BATCH1_TASK},
        )

        result_dict = await create_contact_task.ainvoke(
            _args(contact_id="ct_1", title="Follow up", due_date="2026-01-01T10:00:00Z")
        )

        assert isinstance(result_dict, dict)
        result = CreateContactTaskOutput.model_validate(result_dict)
        assert result.success is True
        assert result.task is not None
        assert result.task.id == "tk_1"

    @pytest.mark.asyncio
    async def test_get_contact_task(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_BATCH1_API}/contacts/ct_1/tasks/tk_1",
            json={"task": _BATCH1_TASK},
        )

        result_dict = await get_contact_task.ainvoke(_args(contact_id="ct_1", task_id="tk_1"))

        assert isinstance(result_dict, dict)
        result = GetContactTaskOutput.model_validate(result_dict)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_update_contact_task(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_BATCH1_API}/contacts/ct_1/tasks/tk_1",
            json={"task": _BATCH1_TASK},
        )

        result_dict = await update_contact_task.ainvoke(
            _args(contact_id="ct_1", task_id="tk_1", title="Follow up again")
        )

        assert isinstance(result_dict, dict)
        result = UpdateContactTaskOutput.model_validate(result_dict)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_delete_contact_task(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_BATCH1_API}/contacts/ct_1/tasks/tk_1",
            json={"succeded": True},
        )

        result_dict = await delete_contact_task.ainvoke(_args(contact_id="ct_1", task_id="tk_1"))

        assert isinstance(result_dict, dict)
        result = DeleteContactTaskOutput.model_validate(result_dict)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_complete_contact_task(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_BATCH1_API}/contacts/ct_1/tasks/tk_1/completed",
            json={"task": dict(_BATCH1_TASK, completed=True)},
        )

        result_dict = await complete_contact_task.ainvoke(_args(contact_id="ct_1", task_id="tk_1"))

        assert isinstance(result_dict, dict)
        result = CompleteContactTaskOutput.model_validate(result_dict)
        assert result.success is True
        assert result.task is not None
        assert result.task.completed is True


class TestOpportunityRecords:
    @pytest.mark.asyncio
    async def test_create_opportunity(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/opportunities/",
            json={"opportunity": _BATCH1_OPPORTUNITY},
        )

        result_dict = await create_opportunity.ainvoke(
            _args(pipeline_id="pl_1", name="New roof", status="open", contact_id="ct_1")
        )

        assert isinstance(result_dict, dict)
        result = CreateOpportunityOutput.model_validate(result_dict)
        assert result.success is True
        assert result.opportunity is not None
        assert result.opportunity.monetary_value == 1500.5

    @pytest.mark.asyncio
    async def test_get_opportunity(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_BATCH1_API}/opportunities/op_1",
            json={"opportunity": _BATCH1_OPPORTUNITY},
        )

        result_dict = await get_opportunity.ainvoke(_args(opportunity_id="op_1"))

        assert isinstance(result_dict, dict)
        result = GetOpportunityOutput.model_validate(result_dict)
        assert result.success is True
        assert result.opportunity is not None
        assert result.opportunity.contact is not None
        assert result.opportunity.contact.name == "Ada Lovelace"

    @pytest.mark.asyncio
    async def test_update_opportunity(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_BATCH1_API}/opportunities/op_1",
            json={"opportunity": _BATCH1_OPPORTUNITY},
        )

        result_dict = await update_opportunity.ainvoke(
            _args(opportunity_id="op_1", name="New roof v2")
        )

        assert isinstance(result_dict, dict)
        result = UpdateOpportunityOutput.model_validate(result_dict)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_delete_opportunity(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_BATCH1_API}/opportunities/op_1",
            json={"succeded": True},
        )

        result_dict = await delete_opportunity.ainvoke(_args(opportunity_id="op_1"))

        assert isinstance(result_dict, dict)
        result = DeleteOpportunityOutput.model_validate(result_dict)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_upsert_opportunity(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/opportunities/upsert",
            json={"opportunity": _BATCH1_OPPORTUNITY, "new": False},
        )

        result_dict = await upsert_opportunity.ainvoke(
            _args(pipeline_id="pl_1", opportunity_id="op_1", contact_id="ct_1")
        )

        assert isinstance(result_dict, dict)
        result = UpsertOpportunityOutput.model_validate(result_dict)
        assert result.success is True
        assert result.new is False

    @pytest.mark.asyncio
    async def test_update_opportunity_status(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_BATCH1_API}/opportunities/op_1/status",
            json={"succeded": True},
        )

        result_dict = await update_opportunity_status.ainvoke(
            _args(opportunity_id="op_1", status="won")
        )

        assert isinstance(result_dict, dict)
        result = UpdateOpportunityStatusOutput.model_validate(result_dict)
        assert result.success is True
        assert result.succeeded is True

    @pytest.mark.asyncio
    async def test_search_opportunities(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            json={
                "opportunities": [_BATCH1_OPPORTUNITY],
                "meta": {"total": 1, "currentPage": 1},
                "aggregations": {"byStatus": {"open": 1}},
            },
        )

        result_dict = await search_opportunities.ainvoke(_args(status="open", limit=10))

        assert isinstance(result_dict, dict)
        result = SearchOpportunitiesOutput.model_validate(result_dict)
        assert result.success is True
        assert result.meta is not None
        assert result.meta.total == 1

    @pytest.mark.asyncio
    async def test_search_opportunities_advanced(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/opportunities/search",
            json={"opportunities": [_BATCH1_OPPORTUNITY], "total": 1},
        )

        result_dict = await search_opportunities_advanced.ainvoke(
            _args(query="roof", include_notes=True)
        )

        assert isinstance(result_dict, dict)
        result = SearchOpportunitiesAdvancedOutput.model_validate(result_dict)
        assert result.success is True
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_list_pipelines(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            json={
                "pipelines": [
                    {"id": "pl_1", "name": "Sales", "stages": [{"id": "st_1"}]},
                ]
            },
        )

        result_dict = await list_pipelines.ainvoke(_args())

        assert isinstance(result_dict, dict)
        result = ListPipelinesOutput.model_validate(result_dict)
        assert result.success is True
        assert result.pipelines[0].name == "Sales"

    @pytest.mark.asyncio
    async def test_list_opportunity_lost_reasons(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            json={"lostReasons": [{"id": "lr_1", "name": "Too expensive"}], "total": 1},
        )

        result_dict = await list_opportunity_lost_reasons.ainvoke(_args(limit=10))

        assert isinstance(result_dict, dict)
        result = ListOpportunityLostReasonsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.lost_reasons[0].name == "Too expensive"


class TestOpportunityFollowers:
    @pytest.mark.asyncio
    async def test_add_opportunity_followers(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/opportunities/op_1/followers",
            json={"followers": ["us_1"], "followersAdded": ["us_1"]},
        )

        result_dict = await add_opportunity_followers.ainvoke(
            _args(opportunity_id="op_1", followers=["us_1"])
        )

        assert isinstance(result_dict, dict)
        result = AddOpportunityFollowersOutput.model_validate(result_dict)
        assert result.success is True
        assert result.followers_added == ["us_1"]

    @pytest.mark.asyncio
    async def test_remove_opportunity_followers(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_BATCH1_API}/opportunities/op_1/followers",
            json={"followers": [], "followersRemoved": ["us_1"]},
        )

        result_dict = await remove_opportunity_followers.ainvoke(
            _args(opportunity_id="op_1", followers=["us_1"])
        )

        assert isinstance(result_dict, dict)
        result = RemoveOpportunityFollowersOutput.model_validate(result_dict)
        assert result.success is True
        assert result.followers_removed == ["us_1"]


class TestBatch1Envelope:
    @pytest.mark.asyncio
    async def test_non_2xx_returns_error_envelope(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_BATCH1_API}/contacts/missing",
            status_code=404,
            json={"message": "Contact not found", "traceId": "tr_9"},
        )

        result_dict = await get_contact.ainvoke(_args(contact_id="missing"))

        assert isinstance(result_dict, dict)
        result = GetContactOutput.model_validate(result_dict)
        assert result.success is False
        assert result.contact is None
        assert result.error is not None
        assert "404" in result.error
        assert "Contact not found" in result.error

    @pytest.mark.asyncio
    async def test_missing_location_short_circuits(self) -> None:
        result_dict = await list_contacts.ainvoke(dict(_BATCH1_NO_LOCATION))

        assert isinstance(result_dict, dict)
        result = ListContactsOutput.model_validate(result_dict)
        assert result.success is False
        assert result.error is not None
        assert "location" in result.error.lower()

    @pytest.mark.asyncio
    async def test_wrongly_typed_fields_do_not_raise(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            json={"contacts": "not-a-list", "count": "many"},
        )

        result_dict = await list_contacts.ainvoke(_args())

        assert isinstance(result_dict, dict)
        result = ListContactsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.contacts == []
        assert result.count is None

    @pytest.mark.asyncio
    async def test_wrongly_typed_nested_fields_do_not_raise(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_BATCH1_API}/contacts/ct_1",
            json={
                "contact": {
                    "id": 12345,
                    "tags": "vip",
                    "dnd": "yes",
                    "customFields": {"id": "cf_1"},
                    "dndSettings": "off",
                }
            },
        )

        result_dict = await get_contact.ainvoke(_args(contact_id="ct_1"))

        assert isinstance(result_dict, dict)
        result = GetContactOutput.model_validate(result_dict)
        assert result.success is True
        assert result.contact is not None
        assert result.contact.id == "12345"
        assert result.contact.tags == []
        assert result.contact.dnd is None
        assert result.contact.custom_fields == []
        assert result.contact.dnd_settings is None

    @pytest.mark.asyncio
    async def test_bulk_tag_object_responses_are_not_dropped(
        self, httpx_mock: Any
    ) -> None:
        """The spec says responses is a string array; its own example is objects."""
        httpx_mock.add_response(
            method="POST",
            url=f"{_BATCH1_API}/contacts/bulk/tags/update/add",
            json={
                "succeded": True,
                "errorCount": 0,
                "responses": [
                    {
                        "contactId": "ct_1",
                        "message": "Tags updated",
                        "type": "success",
                        "tagsAdded": ["vip"],
                    }
                ],
            },
        )

        result_dict = await bulk_update_contact_tags.ainvoke(
            _args(operation="add", contact_ids=["ct_1"], tags=["vip"])
        )

        assert isinstance(result_dict, dict)
        result = BulkUpdateContactTagsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.responses == [
            {
                "contactId": "ct_1",
                "message": "Tags updated",
                "type": "success",
                "tagsAdded": ["vip"],
            }
        ]

    @pytest.mark.asyncio
    async def test_bulk_tag_rejects_operation_outside_the_closed_set(self) -> None:
        """`operation` lands in the request path, so it is never trusted."""
        result_dict = await bulk_update_contact_tags.ainvoke(
            _args(operation="../../workflows", contact_ids=["ct_1"], tags=["vip"])
        )

        assert isinstance(result_dict, dict)
        result = BulkUpdateContactTagsOutput.model_validate(result_dict)
        assert result.success is False
        assert result.error is not None
        assert "add" in result.error and "remove" in result.error


# --- Communication: conversations, messages, emails, campaigns -------------

_B2_API = "https://services.leadconnectorhq.com"
_B2_LOCATION = str(_AUTH["auth_data"]["location_id"])


def _b2_args_no_location(**extra: Any) -> dict[str, Any]:
    """Same call shape as ``_args`` but with the location ID stripped out."""
    return dict(_args(**extra), auth_data={"access_token": "fake_access_token"})


class TestCommunicationCampaigns:
    @pytest.mark.asyncio
    async def test_list_campaigns(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B2_API}/campaigns/?locationId={_B2_LOCATION}",
            json={
                "campaigns": [
                    {
                        "id": "camp_1",
                        "name": "Spring promo",
                        "status": "published",
                        "locationId": _B2_LOCATION,
                    }
                ]
            },
        )
        result_dict = await list_campaigns.ainvoke(_args())
        assert isinstance(result_dict, dict)
        result = ListCampaignsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.campaigns[0].name == "Spring promo"


class TestConversations:
    @pytest.mark.asyncio
    async def test_create_conversation(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B2_API}/conversations/",
            status_code=201,
            json={
                "success": True,
                "conversation": {
                    "id": "conv_1",
                    "contactId": "cont_1",
                    "locationId": _B2_LOCATION,
                    "deleted": False,
                },
            },
        )
        result_dict = await create_conversation.ainvoke(_args(contact_id="cont_1"))
        assert isinstance(result_dict, dict)
        result = CreateConversationOutput.model_validate(result_dict)
        assert result.success is True
        assert result.conversation is not None
        assert result.conversation.id == "conv_1"

    @pytest.mark.asyncio
    async def test_search_conversations(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B2_API}/conversations/search?locationId={_B2_LOCATION}&query=hello",
            json={
                "conversations": [
                    {
                        "id": "conv_1",
                        "contactId": "cont_1",
                        "locationId": _B2_LOCATION,
                        "lastMessageBody": "hello there",
                        "lastMessageType": "TYPE_SMS",
                        "type": "TYPE_PHONE",
                        "unreadCount": 2,
                        "fullName": "John Doe",
                        "email": "john@example.com",
                        "phone": "+15550001234",
                    }
                ],
                "total": 1,
            },
        )
        result_dict = await search_conversations.ainvoke(_args(query="hello"))
        assert isinstance(result_dict, dict)
        result = SearchConversationsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.total == 1
        assert result.conversations[0].unread_count == 2

    @pytest.mark.asyncio
    async def test_get_conversation(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B2_API}/conversations/conv_1",
            json={
                "id": "conv_1",
                "contactId": "cont_1",
                "locationId": _B2_LOCATION,
                "deleted": False,
                "inbox": True,
                "type": 1,
                "unreadCount": 0,
                "starred": True,
            },
        )
        result_dict = await get_conversation.ainvoke(_args(conversation_id="conv_1"))
        assert isinstance(result_dict, dict)
        result = GetConversationOutput.model_validate(result_dict)
        assert result.success is True
        assert result.conversation is not None
        assert result.conversation.conversation_type == "1"

    @pytest.mark.asyncio
    async def test_update_conversation(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_B2_API}/conversations/conv_1",
            json={
                "success": True,
                "conversation": {
                    "id": "conv_1",
                    "locationId": _B2_LOCATION,
                    "contactId": "cont_1",
                    "starred": True,
                    "deleted": False,
                },
            },
        )
        result_dict = await update_conversation.ainvoke(
            _args(conversation_id="conv_1", starred=True)
        )
        assert isinstance(result_dict, dict)
        result = UpdateConversationOutput.model_validate(result_dict)
        assert result.success is True
        assert result.conversation is not None
        assert result.conversation.starred is True

    @pytest.mark.asyncio
    async def test_delete_conversation(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_B2_API}/conversations/conv_1",
            json={"success": True},
        )
        result_dict = await delete_conversation.ainvoke(_args(conversation_id="conv_1"))
        assert isinstance(result_dict, dict)
        result = DeleteConversationOutput.model_validate(result_dict)
        assert result.success is True


class TestConversationMessages:
    @pytest.mark.asyncio
    async def test_list_conversation_messages(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B2_API}/conversations/conv_1/messages",
            json={
                "lastMessageId": "msg_9",
                "nextPage": False,
                "messages": [
                    {
                        "id": "msg_1",
                        "type": 1,
                        "messageType": "TYPE_SMS",
                        "conversationId": "conv_1",
                        "contactId": "cont_1",
                        "locationId": _B2_LOCATION,
                        "body": "hi",
                        "direction": "inbound",
                        "contentType": "text/plain",
                        "attachments": ["https://cdn.example.com/a.png"],
                        "meta": {"callDuration": "120", "callStatus": "completed"},
                    }
                ],
            },
        )
        result_dict = await list_conversation_messages.ainvoke(
            _args(conversation_id="conv_1")
        )
        assert isinstance(result_dict, dict)
        result = ListConversationMessagesOutput.model_validate(result_dict)
        assert result.success is True
        assert result.next_page is False
        assert result.messages[0].message_type == "TYPE_SMS"
        assert result.messages[0].meta is not None
        assert result.messages[0].meta.call_status == "completed"

    @pytest.mark.asyncio
    async def test_get_message(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B2_API}/conversations/messages/msg_1",
            json={
                "id": "msg_1",
                "type": 3,
                "messageType": "TYPE_EMAIL",
                "conversationId": "conv_1",
                "contactId": "cont_1",
                "locationId": _B2_LOCATION,
                "direction": "outbound",
                "contentType": "text/html",
            },
        )
        result_dict = await get_message.ainvoke(_args(message_id="msg_1"))
        assert isinstance(result_dict, dict)
        result = GetMessageOutput.model_validate(result_dict)
        assert result.success is True
        assert result.message is not None
        assert result.message.message_type_code == 3

    @pytest.mark.asyncio
    async def test_send_message(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B2_API}/conversations/messages",
            json={
                "conversationId": "conv_1",
                "messageId": "msg_1",
                "emailMessageId": "em_1",
                "status": "delivered",
                "msg": "Message queued successfully.",
            },
        )
        result_dict = await send_message.ainvoke(
            _args(message_type="SMS", contact_id="cont_1", message="Hello")
        )
        assert isinstance(result_dict, dict)
        result = SendMessageOutput.model_validate(result_dict)
        assert result.success is True
        assert result.message_id == "msg_1"
        assert result.status == "delivered"

    @pytest.mark.asyncio
    async def test_add_inbound_message(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B2_API}/conversations/messages/inbound",
            json={
                "success": True,
                "conversationId": "conv_1",
                "messageId": "msg_2",
                "message": "logged",
                "contactId": "cont_1",
            },
        )
        result_dict = await add_inbound_message.ainvoke(
            _args(message_type="SMS", conversation_id="conv_1", message="Hi back")
        )
        assert isinstance(result_dict, dict)
        result = AddInboundMessageOutput.model_validate(result_dict)
        assert result.success is True
        assert result.message_id == "msg_2"

    @pytest.mark.asyncio
    async def test_add_outbound_message(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B2_API}/conversations/messages/outbound",
            json={
                "success": True,
                "conversationId": "conv_1",
                "messageId": "msg_3",
                "message": "call logged",
            },
        )
        result_dict = await add_outbound_message.ainvoke(
            _args(conversation_id="conv_1", conversation_provider_id="prov_1")
        )
        assert isinstance(result_dict, dict)
        result = AddOutboundMessageOutput.model_validate(result_dict)
        assert result.success is True
        assert result.message_id == "msg_3"

    @pytest.mark.asyncio
    async def test_send_review_reply(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B2_API}/conversations/messages/review-reply",
            json={
                "conversationId": "conv_1",
                "messageId": "msg_4",
                "status": "delivered",
            },
        )
        result_dict = await send_review_reply.ainvoke(
            _args(conversation_id="conv_1", message="Thank you for your review!")
        )
        assert isinstance(result_dict, dict)
        result = SendReviewReplyOutput.model_validate(result_dict)
        assert result.success is True
        assert result.message_id == "msg_4"

    @pytest.mark.asyncio
    async def test_update_message_status(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_B2_API}/conversations/messages/msg_1/status",
            json={
                "conversationId": "conv_1",
                "messageId": "msg_1",
                "status": "read",
            },
        )
        result_dict = await update_message_status.ainvoke(
            _args(message_id="msg_1", status="read")
        )
        assert isinstance(result_dict, dict)
        result = UpdateMessageStatusOutput.model_validate(result_dict)
        assert result.success is True
        assert result.status == "read"

    @pytest.mark.asyncio
    async def test_add_message_attachments(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_B2_API}/conversations/messages/msg_1/attachments",
            json={"updated": True},
        )
        result_dict = await add_message_attachments.ainvoke(
            _args(
                message_id="msg_1",
                attachments=["https://provider.com/recordings/call-123.mp3"],
            )
        )
        assert isinstance(result_dict, dict)
        result = AddMessageAttachmentsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.data == {"updated": True}

    @pytest.mark.asyncio
    async def test_cancel_scheduled_message(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_B2_API}/conversations/messages/msg_1/schedule",
            json={"status": 200, "message": "Scheduled message cancelled"},
        )
        result_dict = await cancel_scheduled_message.ainvoke(_args(message_id="msg_1"))
        assert isinstance(result_dict, dict)
        result = CancelScheduledMessageOutput.model_validate(result_dict)
        assert result.success is True
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_cancel_scheduled_email_message(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_B2_API}/conversations/messages/email/em_1/schedule",
            json={"status": 200, "message": "Scheduled email cancelled"},
        )
        result_dict = await cancel_scheduled_email_message.ainvoke(
            _args(email_message_id="em_1")
        )
        assert isinstance(result_dict, dict)
        result = CancelScheduledEmailMessageOutput.model_validate(result_dict)
        assert result.success is True
        assert result.message == "Scheduled email cancelled"

    @pytest.mark.asyncio
    async def test_get_email_by_id(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B2_API}/conversations/messages/email/em_1",
            json={
                "id": "em_1",
                "threadId": "th_1",
                "locationId": _B2_LOCATION,
                "contactId": "cont_1",
                "conversationId": "conv_1",
                "dateAdded": "2024-03-27T18:13:49.000Z",
                "subject": "Order confirm",
                "body": "Hi there",
                "direction": "outbound",
                "contentType": "text/plain",
                "from": "Sales <sales@example.com>",
                "to": ["john@example.com"],
                "cc": [],
            },
        )
        result_dict = await get_email_by_id.ainvoke(_args(email_message_id="em_1"))
        assert isinstance(result_dict, dict)
        result = GetEmailByIdOutput.model_validate(result_dict)
        assert result.success is True
        assert result.email is not None
        assert result.email.from_address == "Sales <sales@example.com>"
        assert result.email.to == ["john@example.com"]

    @pytest.mark.asyncio
    async def test_export_messages(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B2_API}/conversations/messages/export?locationId={_B2_LOCATION}",
            json={
                "messages": [
                    {
                        "id": "msg_1",
                        "type": 1,
                        "messageType": "TYPE_SMS",
                        "conversationId": "conv_1",
                        "contactId": "cont_1",
                        "locationId": _B2_LOCATION,
                        "direction": "inbound",
                        "contentType": "text/plain",
                    }
                ],
                "nextCursor": "cursor_2",
                "total": 42,
            },
        )
        result_dict = await export_messages.ainvoke(_args())
        assert isinstance(result_dict, dict)
        result = ExportMessagesOutput.model_validate(result_dict)
        assert result.success is True
        assert result.next_cursor == "cursor_2"
        assert result.total == 42

    @pytest.mark.asyncio
    async def test_get_message_transcription(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=(
                f"{_B2_API}/conversations/locations/{_B2_LOCATION}"
                "/messages/msg_1/transcription"
            ),
            json=[
                {
                    "mediaChannel": 1,
                    "sentenceIndex": 0,
                    "startTime": 34,
                    "endTime": 45,
                    "transcript": "This call may be recorded.",
                    "confidence": 0.92,
                }
            ],
        )
        result_dict = await get_message_transcription.ainvoke(_args(message_id="msg_1"))
        assert isinstance(result_dict, dict)
        result = GetMessageTranscriptionOutput.model_validate(result_dict)
        assert result.success is True
        assert result.segments[0].transcript == "This call may be recorded."
        assert result.segments[0].confidence == 0.92

    @pytest.mark.asyncio
    async def test_initiate_message_file_upload(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B2_API}/conversations/messages/upload/initiate",
            json={
                "uploadUrl": "https://storage.googleapis.com/bucket/path?X-Goog=1",
                "uploadId": "up_1",
                "filePath": "location/loc/conversations/conv_1/uuid.mp4",
                "expiresAt": 1701619200000,
                "maxFileSize": 104857600,
            },
        )
        result_dict = await initiate_message_file_upload.ainvoke(
            _args(
                conversation_id="conv_1",
                filename="video.mp4",
                content_type="video/mp4",
                channel="WHATSAPP",
            )
        )
        assert isinstance(result_dict, dict)
        result = InitiateMessageFileUploadOutput.model_validate(result_dict)
        assert result.success is True
        assert result.upload_id == "up_1"
        assert result.max_file_size == 104857600

    @pytest.mark.asyncio
    async def test_complete_message_file_upload(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B2_API}/conversations/messages/upload/complete",
            json={
                "uploadedFiles": {"video.mp4": "https://cdn.example.com/video.mp4"},
                "metadata": {"size": 52428800, "contentType": "video/mp4"},
            },
        )
        result_dict = await complete_message_file_upload.ainvoke(
            _args(
                upload_id="up_1",
                file_path="location/loc/conversations/conv_1/uuid.mp4",
                conversation_id="conv_1",
                filename="video.mp4",
            )
        )
        assert isinstance(result_dict, dict)
        result = CompleteMessageFileUploadOutput.model_validate(result_dict)
        assert result.success is True
        assert result.uploaded_files == {
            "video.mp4": "https://cdn.example.com/video.mp4"
        }


class TestConversationPreferences:
    @pytest.mark.asyncio
    async def test_list_custom_subtypes(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=(
                f"{_B2_API}/conversations/preferences/custom-subtypes"
                f"?locationId={_B2_LOCATION}"
            ),
            json=[{"id": "cs_1", "name": "Newsletter", "channel": "email"}],
        )
        result_dict = await list_custom_subtypes.ainvoke(_args())
        assert isinstance(result_dict, dict)
        result = ListCustomSubtypesOutput.model_validate(result_dict)
        assert result.success is True
        assert result.custom_subtypes[0]["name"] == "Newsletter"

    @pytest.mark.asyncio
    async def test_create_custom_subtype(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=(
                f"{_B2_API}/conversations/preferences/custom-subtypes"
                f"?locationId={_B2_LOCATION}"
            ),
            status_code=201,
            json={"id": "cs_1"},
        )
        result_dict = await create_custom_subtype.ainvoke(
            _args(name="Newsletter", channel="email", language="en")
        )
        assert isinstance(result_dict, dict)
        result = CreateCustomSubtypeOutput.model_validate(result_dict)
        assert result.success is True
        assert result.data == {"id": "cs_1"}

    @pytest.mark.asyncio
    async def test_update_custom_subtype(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=(
                f"{_B2_API}/conversations/preferences/custom-subtypes/cs_1"
                f"?locationId={_B2_LOCATION}"
            ),
            json={"id": "cs_1", "archived": True},
        )
        result_dict = await update_custom_subtype.ainvoke(
            _args(custom_subtype_id="cs_1", archived=True)
        )
        assert isinstance(result_dict, dict)
        result = UpdateCustomSubtypeOutput.model_validate(result_dict)
        assert result.success is True
        assert result.data == {"id": "cs_1", "archived": True}

    @pytest.mark.asyncio
    async def test_get_contact_unsubscription_status(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=(
                f"{_B2_API}/conversations/preferences/unsubscriptions/status"
                f"?locationId={_B2_LOCATION}&contactId=cont_1"
            ),
            json=[{"email": "john@example.com", "status": "subscribed"}],
        )
        result_dict = await get_contact_unsubscription_status.ainvoke(
            _args(contact_id="cont_1")
        )
        assert isinstance(result_dict, dict)
        result = GetContactUnsubscriptionStatusOutput.model_validate(result_dict)
        assert result.success is True
        assert result.subscriptions[0]["status"] == "subscribed"

    @pytest.mark.asyncio
    async def test_update_subscription_preference(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B2_API}/conversations/preferences/unsubscriptions/user-change",
            status_code=201,
            json={"updated": True},
        )
        result_dict = await update_subscription_preference.ainvoke(
            _args(
                contact_id="cont_1",
                email="john@example.com",
                subscription_type="custom",
                subscription_status="unsubscribed",
                subtype_id="cs_1",
            )
        )
        assert isinstance(result_dict, dict)
        result = UpdateSubscriptionPreferenceOutput.model_validate(result_dict)
        assert result.success is True
        assert result.data == {"updated": True}

    @pytest.mark.asyncio
    async def test_live_chat_agent_typing(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B2_API}/conversations/providers/live-chat/typing",
            status_code=201,
            json={"success": True},
        )
        result_dict = await live_chat_agent_typing.ainvoke(
            _args(conversation_id="conv_1", visitor_id="vis_1", is_typing="true")
        )
        assert isinstance(result_dict, dict)
        result = LiveChatAgentTypingOutput.model_validate(result_dict)
        assert result.success is True


class TestEmailBuilder:
    @pytest.mark.asyncio
    async def test_create_email_template(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B2_API}/emails/builder",
            status_code=201,
            json={"redirect": "tpl_1", "traceId": "trace_1"},
        )
        result_dict = await create_email_template.ainvoke(
            _args(template_type="builder", name="Welcome")
        )
        assert isinstance(result_dict, dict)
        result = CreateEmailTemplateOutput.model_validate(result_dict)
        assert result.success is True
        assert result.template_id == "tpl_1"

    @pytest.mark.asyncio
    async def test_list_email_templates(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B2_API}/emails/builder?locationId={_B2_LOCATION}",
            json=[
                {
                    "id": "tpl_1",
                    "name": "New Template",
                    "templateType": "builder",
                    "version": "1",
                    "isPlainText": False,
                    "previewUrl": "https://example.com",
                }
            ],
        )
        result_dict = await list_email_templates.ainvoke(_args())
        assert isinstance(result_dict, dict)
        result = ListEmailTemplatesOutput.model_validate(result_dict)
        assert result.success is True
        assert result.templates[0].id == "tpl_1"

    @pytest.mark.asyncio
    async def test_list_email_templates_wrapped(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B2_API}/emails/builder?locationId={_B2_LOCATION}",
            json={"templates": [{"id": "tpl_2", "name": "Wrapped"}]},
        )
        result_dict = await list_email_templates.ainvoke(_args())
        assert isinstance(result_dict, dict)
        result = ListEmailTemplatesOutput.model_validate(result_dict)
        assert result.success is True
        assert result.templates[0].name == "Wrapped"

    @pytest.mark.asyncio
    async def test_update_email_template(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B2_API}/emails/builder/data",
            status_code=201,
            json={
                "ok": "true",
                "traceId": "trace_2",
                "previewUrl": "https://example.com/preview",
                "templateDownloadUrl": "https://example.com/data.json",
            },
        )
        result_dict = await update_email_template.ainvoke(
            _args(
                template_id="tpl_1",
                updated_by="user_1",
                html="<p>Hi</p>",
                editor_type="builder",
                dnd={"elements": [], "attrs": {}, "templateSettings": {}},
            )
        )
        assert isinstance(result_dict, dict)
        result = UpdateEmailTemplateOutput.model_validate(result_dict)
        assert result.success is True
        assert result.preview_url == "https://example.com/preview"

    @pytest.mark.asyncio
    async def test_delete_email_template(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_B2_API}/emails/builder/{_B2_LOCATION}/tpl_1",
            json={"ok": "true", "traceId": "trace_3"},
        )
        result_dict = await delete_email_template.ainvoke(_args(template_id="tpl_1"))
        assert isinstance(result_dict, dict)
        result = DeleteEmailTemplateOutput.model_validate(result_dict)
        assert result.success is True
        assert result.ok == "true"

    @pytest.mark.asyncio
    async def test_list_scheduled_emails(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B2_API}/emails/schedule?locationId={_B2_LOCATION}",
            json={
                "schedules": [
                    {
                        "id": "sch_1",
                        "name": "Untitled new campaign",
                        "status": "active",
                        "locationId": _B2_LOCATION,
                        "childCount": 0,
                        "sendDays": ["mon", "tue"],
                        "archived": False,
                    }
                ],
                "total": ["1"],
                "traceId": "trace_4",
            },
        )
        result_dict = await list_scheduled_emails.ainvoke(_args())
        assert isinstance(result_dict, dict)
        result = ListScheduledEmailsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.total == ["1"]
        assert result.schedules[0].send_days == ["mon", "tue"]


class TestCommunicationEnvelope:
    @pytest.mark.asyncio
    async def test_non_2xx_returns_error_envelope(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B2_API}/campaigns/?locationId={_B2_LOCATION}",
            status_code=401,
            json={"message": "Invalid token", "traceId": "trace_err"},
        )
        result_dict = await list_campaigns.ainvoke(_args())
        assert isinstance(result_dict, dict)
        result = ListCampaignsOutput.model_validate(result_dict)
        assert result.success is False
        assert result.error is not None
        assert "401" in result.error
        assert "Invalid token" in result.error
        assert result.campaigns == []

    @pytest.mark.asyncio
    async def test_missing_location_short_circuits(self) -> None:
        result_dict = await search_conversations.ainvoke(_b2_args_no_location())
        assert isinstance(result_dict, dict)
        result = SearchConversationsOutput.model_validate(result_dict)
        assert result.success is False
        assert result.error is not None
        assert "location" in result.error.lower()

    @pytest.mark.asyncio
    async def test_missing_token_short_circuits(self) -> None:
        args = dict(_args(conversation_id="conv_1"), auth_data={})
        result_dict = await get_conversation.ainvoke(args)
        assert isinstance(result_dict, dict)
        result = GetConversationOutput.model_validate(result_dict)
        assert result.success is False
        assert result.error is not None
        assert "token" in result.error.lower()

    @pytest.mark.asyncio
    async def test_wrong_field_types_still_succeed(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B2_API}/conversations/conv_1",
            json={
                "id": 12345,
                "contactId": ["not", "a", "string"],
                "unreadCount": "many",
                "starred": "yes",
                "type": 2,
                "deleted": None,
            },
        )
        result_dict = await get_conversation.ainvoke(_args(conversation_id="conv_1"))
        assert isinstance(result_dict, dict)
        result = GetConversationOutput.model_validate(result_dict)
        assert result.success is True
        assert result.conversation is not None
        assert result.conversation.id == "12345"
        assert result.conversation.contact_id is None
        assert result.conversation.unread_count is None
        assert result.conversation.starred is None
        assert result.conversation.conversation_type == "2"


_B3_API = "https://services.leadconnectorhq.com"
_B3_AUTH_DATA: dict[str, Any] = _AUTH["auth_data"]
_B3_LOC = str(_B3_AUTH_DATA.get("location_id") or _B3_AUTH_DATA.get("locationId") or "")

_B3_CALENDAR: dict[str, Any] = {
    "id": "cal-1",
    "locationId": _B3_LOC,
    "name": "Discovery Call",
    "slug": "discovery",
    "calendarType": "round_robin",
    "isActive": True,
    "slotDuration": 30,
    "teamMembers": [{"userId": "usr-1"}],
}

_B3_EVENT: dict[str, Any] = {
    "id": "evt-1",
    "title": "Discovery Call",
    "calendarId": "cal-1",
    "locationId": _B3_LOC,
    "contactId": "con-1",
    "groupId": "grp-1",
    "appointmentStatus": "confirmed",
    "assignedUserId": "usr-1",
    "users": ["usr-1"],
    "startTime": "2024-10-28T10:00:00-05:00",
    "endTime": "2024-10-28T10:30:00-05:00",
    "dateAdded": "2024-10-01T09:00:00.000Z",
    "dateUpdated": "2024-10-02T09:00:00.000Z",
    "createdBy": {"userId": "usr-1", "source": "api"},
}

_B3_APPOINTMENT: dict[str, Any] = {
    "id": "evt-1",
    "calendarId": "cal-1",
    "locationId": _B3_LOC,
    "contactId": "con-1",
    "startTime": "2024-10-28T10:00:00-05:00",
    "endTime": "2024-10-28T10:30:00-05:00",
    "title": "Discovery Call",
    "appointmentStatus": "confirmed",
    "assignedUserId": "usr-1",
}

_B3_NOTE: dict[str, Any] = {
    "id": "note-1",
    "body": "Called the lead",
    "userId": "usr-1",
    "dateAdded": "2024-10-01T09:00:00.000Z",
    "contactId": "con-1",
    "createdBy": {"id": "usr-1", "name": "Jane Doe"},
}

_B3_GROUP: dict[str, Any] = {
    "id": "grp-1",
    "locationId": _B3_LOC,
    "name": "Sales",
    "description": "Sales calendars",
    "slug": "sales",
    "isActive": True,
}

_B3_RESOURCE: dict[str, Any] = {
    "id": "res-1",
    "locationId": _B3_LOC,
    "name": "Meeting Room A",
    "resourceType": "rooms",
    "isActive": True,
    "description": "Ground floor",
    "capacity": 8,
    "quantity": 1,
    "outOfService": 0,
    "calendarIds": ["cal-1"],
}

_B3_SCHEDULE: dict[str, Any] = {
    "id": "sch-1",
    "name": "Business Hours",
    "locationId": _B3_LOC,
    "timezone": "America/New_York",
    "userId": "usr-1",
    "dateAdded": "2023-01-15T10:30:00.000Z",
    "dateUpdated": "2023-01-20T14:45:00.000Z",
    "calendarIds": ["cal-1"],
    "deleted": False,
    "rules": [
        {
            "type": "wday",
            "day": "monday",
            "intervals": [{"from": "09:00", "to": "17:00"}],
        }
    ],
}

_B3_NOTIFICATION: dict[str, Any] = {
    "_id": "ntf-1",
    "receiverType": "contact",
    "channel": "email",
    "notificationType": "reminder",
    "isActive": True,
    "templateId": "tpl-1",
    "subject": "Your appointment",
    "body": "See you soon",
    "beforeTime": [{"timeOffset": 30, "unit": "mins"}],
    "afterTime": [],
    "selectedUsers": ["usr-1"],
    "additionalEmailIds": [],
    "additionalPhoneNumbers": [],
    "additionalWhatsappNumbers": [],
    "deleted": False,
}


def _b3_args_without_location(**extra: Any) -> dict[str, Any]:
    """Same call arguments, but with the location ID stripped from auth_data."""
    args = _args(**extra)
    args["auth_data"] = {"access_token": "tok-b3"}
    return args


class TestCalendars:
    @pytest.mark.asyncio
    async def test_list_calendars(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B3_API}/calendars/?locationId={_B3_LOC}",
            json={"calendars": [_B3_CALENDAR]},
        )

        result_dict = await list_calendars.ainvoke(_args())

        assert isinstance(result_dict, dict)
        result = ListCalendarsOutput.model_validate(result_dict)
        assert result.success is True
        assert len(result.calendars) == 1
        assert result.calendars[0].id == "cal-1"
        assert result.calendars[0].calendar_type == "round_robin"
        assert result.calendars[0].team_members == [{"userId": "usr-1"}]

    @pytest.mark.asyncio
    async def test_create_calendar(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B3_API}/calendars/",
            json={"calendar": _B3_CALENDAR},
        )

        result_dict = await create_calendar.ainvoke(
            _args(name="Discovery Call", calendar_type="round_robin", slot_duration=30)
        )

        assert isinstance(result_dict, dict)
        result = CreateCalendarOutput.model_validate(result_dict)
        assert result.success is True
        assert result.calendar is not None
        assert result.calendar.name == "Discovery Call"

    @pytest.mark.asyncio
    async def test_get_calendar(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B3_API}/calendars/cal-1",
            json={"calendar": _B3_CALENDAR},
        )

        result_dict = await get_calendar.ainvoke(_args(calendar_id="cal-1"))

        assert isinstance(result_dict, dict)
        result = GetCalendarOutput.model_validate(result_dict)
        assert result.success is True
        assert result.calendar is not None
        assert result.calendar.slot_duration == 30.0

    @pytest.mark.asyncio
    async def test_update_calendar(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_B3_API}/calendars/cal-1",
            json={"calendar": dict(_B3_CALENDAR, name="Renamed")},
        )

        result_dict = await update_calendar.ainvoke(_args(calendar_id="cal-1", name="Renamed"))

        assert isinstance(result_dict, dict)
        result = UpdateCalendarOutput.model_validate(result_dict)
        assert result.success is True
        assert result.calendar is not None
        assert result.calendar.name == "Renamed"

    @pytest.mark.asyncio
    async def test_delete_calendar(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_B3_API}/calendars/cal-1",
            json={"success": True},
        )

        result_dict = await delete_calendar.ainvoke(_args(calendar_id="cal-1"))

        assert isinstance(result_dict, dict)
        result = DeleteCalendarOutput.model_validate(result_dict)
        assert result.success is True
        assert result.deleted is True

    @pytest.mark.asyncio
    async def test_get_calendar_free_slots(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=(
                f"{_B3_API}/calendars/cal-1/free-slots"
                "?startDate=1730000000000&endDate=1730100000000"
            ),
            json={
                "2024-10-28": {"slots": ["2024-10-28T10:00:00-05:00"]},
                "2024-10-29": {"slots": []},
                "traceId": "abc",
            },
        )

        result_dict = await get_calendar_free_slots.ainvoke(
            _args(calendar_id="cal-1", start_date=1730000000000, end_date=1730100000000)
        )

        assert isinstance(result_dict, dict)
        result = GetCalendarFreeSlotsOutput.model_validate(result_dict)
        assert result.success is True
        assert [day.date for day in result.days] == ["2024-10-28", "2024-10-29"]
        assert result.days[0].slots == ["2024-10-28T10:00:00-05:00"]


class TestAppointmentNotes:
    @pytest.mark.asyncio
    async def test_list_appointment_notes(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B3_API}/calendars/appointments/apt-1/notes?limit=10&offset=0",
            json={"notes": [_B3_NOTE], "hasMore": False},
        )

        result_dict = await list_appointment_notes.ainvoke(
            _args(appointment_id="apt-1", limit=10, offset=0)
        )

        assert isinstance(result_dict, dict)
        result = ListAppointmentNotesOutput.model_validate(result_dict)
        assert result.success is True
        assert result.has_more is False
        assert result.notes[0].created_by is not None
        assert result.notes[0].created_by.name == "Jane Doe"

    @pytest.mark.asyncio
    async def test_create_appointment_note(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B3_API}/calendars/appointments/apt-1/notes",
            json={"note": _B3_NOTE},
        )

        result_dict = await create_appointment_note.ainvoke(
            _args(appointment_id="apt-1", body="Called the lead", user_id="usr-1")
        )

        assert isinstance(result_dict, dict)
        result = CreateAppointmentNoteOutput.model_validate(result_dict)
        assert result.success is True
        assert result.note is not None
        assert result.note.body == "Called the lead"

    @pytest.mark.asyncio
    async def test_update_appointment_note(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_B3_API}/calendars/appointments/apt-1/notes/note-1",
            json={"note": dict(_B3_NOTE, body="Updated")},
        )

        result_dict = await update_appointment_note.ainvoke(
            _args(appointment_id="apt-1", note_id="note-1", body="Updated")
        )

        assert isinstance(result_dict, dict)
        result = UpdateAppointmentNoteOutput.model_validate(result_dict)
        assert result.success is True
        assert result.note is not None
        assert result.note.body == "Updated"

    @pytest.mark.asyncio
    async def test_delete_appointment_note(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_B3_API}/calendars/appointments/apt-1/notes/note-1",
            json={"success": True},
        )

        result_dict = await delete_appointment_note.ainvoke(
            _args(appointment_id="apt-1", note_id="note-1")
        )

        assert isinstance(result_dict, dict)
        result = DeleteAppointmentNoteOutput.model_validate(result_dict)
        assert result.success is True
        assert result.deleted is True


class TestCalendarEvents:
    @pytest.mark.asyncio
    async def test_list_calendar_events(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=(
                f"{_B3_API}/calendars/events?locationId={_B3_LOC}"
                "&startTime=1730000000000&endTime=1730100000000"
            ),
            json={"events": [_B3_EVENT]},
        )

        result_dict = await list_calendar_events.ainvoke(
            _args(start_time="1730000000000", end_time="1730100000000")
        )

        assert isinstance(result_dict, dict)
        result = ListCalendarEventsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.events[0].id == "evt-1"
        assert result.events[0].created_by is not None
        assert result.events[0].created_by.source == "api"

    @pytest.mark.asyncio
    async def test_list_blocked_slots(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=(
                f"{_B3_API}/calendars/blocked-slots?locationId={_B3_LOC}"
                "&startTime=1730000000000&endTime=1730100000000&calendarId=cal-1"
            ),
            json={"events": [_B3_EVENT]},
        )

        result_dict = await list_blocked_slots.ainvoke(
            _args(
                start_time="1730000000000",
                end_time="1730100000000",
                calendar_id="cal-1",
            )
        )

        assert isinstance(result_dict, dict)
        result = ListBlockedSlotsOutput.model_validate(result_dict)
        assert result.success is True
        assert len(result.events) == 1

    @pytest.mark.asyncio
    async def test_get_appointment(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B3_API}/calendars/events/appointments/evt-1",
            json={"event": _B3_EVENT},
        )

        result_dict = await get_appointment.ainvoke(_args(event_id="evt-1"))

        assert isinstance(result_dict, dict)
        result = GetAppointmentOutput.model_validate(result_dict)
        assert result.success is True
        assert result.event is not None
        assert result.event.appointment_status == "confirmed"

    @pytest.mark.asyncio
    async def test_delete_event(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_B3_API}/calendars/events/evt-1",
            json={"succeeded": True},
        )

        result_dict = await delete_event.ainvoke(_args(event_id="evt-1"))

        assert isinstance(result_dict, dict)
        result = DeleteEventOutput.model_validate(result_dict)
        assert result.success is True
        assert result.deleted is True


class TestAppointments:
    @pytest.mark.asyncio
    async def test_create_appointment(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B3_API}/calendars/events/appointments",
            json=_B3_APPOINTMENT,
        )

        result_dict = await create_appointment.ainvoke(
            _args(
                calendar_id="cal-1",
                contact_id="con-1",
                start_time="2024-10-28T10:00:00-05:00",
                title="Discovery Call",
                appointment_status="confirmed",
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateAppointmentOutput.model_validate(result_dict)
        assert result.success is True
        assert result.appointment is not None
        assert result.appointment.id == "evt-1"
        assert result.appointment.contact_id == "con-1"

    @pytest.mark.asyncio
    async def test_update_appointment(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_B3_API}/calendars/events/appointments/evt-1",
            json=dict(_B3_APPOINTMENT, appointmentStatus="cancelled"),
        )

        result_dict = await update_appointment.ainvoke(
            _args(event_id="evt-1", appointment_status="cancelled")
        )

        assert isinstance(result_dict, dict)
        result = UpdateAppointmentOutput.model_validate(result_dict)
        assert result.success is True
        assert result.appointment is not None
        assert result.appointment.appointment_status == "cancelled"


class TestBlockSlots:
    @pytest.mark.asyncio
    async def test_create_block_slot(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B3_API}/calendars/events/block-slots",
            json={
                "id": "blk-1",
                "locationId": _B3_LOC,
                "title": "Lunch",
                "startTime": "2024-10-28T12:00:00-05:00",
                "endTime": "2024-10-28T13:00:00-05:00",
                "calendarId": "cal-1",
            },
        )

        result_dict = await create_block_slot.ainvoke(
            _args(
                title="Lunch",
                calendar_id="cal-1",
                start_time="2024-10-28T12:00:00-05:00",
                end_time="2024-10-28T13:00:00-05:00",
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateBlockSlotOutput.model_validate(result_dict)
        assert result.success is True
        assert result.block_slot is not None
        assert result.block_slot.id == "blk-1"

    @pytest.mark.asyncio
    async def test_update_block_slot(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_B3_API}/calendars/events/block-slots/blk-1",
            json={
                "id": "blk-1",
                "locationId": _B3_LOC,
                "title": "Long lunch",
                "startTime": "2024-10-28T12:00:00-05:00",
                "endTime": "2024-10-28T14:00:00-05:00",
                "calendarId": "cal-1",
            },
        )

        result_dict = await update_block_slot.ainvoke(
            _args(event_id="blk-1", title="Long lunch", calendar_id="cal-1")
        )

        assert isinstance(result_dict, dict)
        result = UpdateBlockSlotOutput.model_validate(result_dict)
        assert result.success is True
        assert result.block_slot is not None
        assert result.block_slot.title == "Long lunch"


class TestCalendarGroups:
    @pytest.mark.asyncio
    async def test_list_calendar_groups(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B3_API}/calendars/groups?locationId={_B3_LOC}",
            json={"groups": [_B3_GROUP]},
        )

        result_dict = await list_calendar_groups.ainvoke(_args())

        assert isinstance(result_dict, dict)
        result = ListCalendarGroupsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.groups[0].slug == "sales"

    @pytest.mark.asyncio
    async def test_create_calendar_group(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B3_API}/calendars/groups",
            json={"group": _B3_GROUP},
        )

        result_dict = await create_calendar_group.ainvoke(
            _args(name="Sales", description="Sales calendars", slug="sales")
        )

        assert isinstance(result_dict, dict)
        result = CreateCalendarGroupOutput.model_validate(result_dict)
        assert result.success is True
        assert result.group is not None
        assert result.group.id == "grp-1"

    @pytest.mark.asyncio
    async def test_validate_calendar_group_slug(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B3_API}/calendars/groups/validate-slug",
            json={"available": False},
        )

        result_dict = await validate_calendar_group_slug.ainvoke(_args(slug="sales"))

        assert isinstance(result_dict, dict)
        result = ValidateCalendarGroupSlugOutput.model_validate(result_dict)
        assert result.success is True
        assert result.available is False

    @pytest.mark.asyncio
    async def test_delete_calendar_group(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_B3_API}/calendars/groups/grp-1",
            json={"success": True},
        )

        result_dict = await delete_calendar_group.ainvoke(_args(group_id="grp-1"))

        assert isinstance(result_dict, dict)
        result = DeleteCalendarGroupOutput.model_validate(result_dict)
        assert result.success is True
        assert result.deleted is True

    @pytest.mark.asyncio
    async def test_update_calendar_group(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_B3_API}/calendars/groups/grp-1",
            json={"group": dict(_B3_GROUP, name="Sales EMEA")},
        )

        result_dict = await update_calendar_group.ainvoke(
            _args(
                group_id="grp-1",
                name="Sales EMEA",
                description="Sales calendars",
                slug="sales",
            )
        )

        assert isinstance(result_dict, dict)
        result = UpdateCalendarGroupOutput.model_validate(result_dict)
        assert result.success is True
        assert result.group is not None
        assert result.group.name == "Sales EMEA"

    @pytest.mark.asyncio
    async def test_set_calendar_group_status(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_B3_API}/calendars/groups/grp-1/status",
            json={"success": True},
        )

        result_dict = await set_calendar_group_status.ainvoke(
            _args(group_id="grp-1", is_active=False)
        )

        assert isinstance(result_dict, dict)
        result = SetCalendarGroupStatusOutput.model_validate(result_dict)
        assert result.success is True
        assert result.updated is True


class TestCalendarResources:
    @pytest.mark.asyncio
    async def test_list_calendar_resources(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B3_API}/calendars/resources/rooms?locationId={_B3_LOC}&limit=10&skip=0",
            json=[_B3_RESOURCE],
        )

        result_dict = await list_calendar_resources.ainvoke(
            _args(resource_type="rooms", limit=10, skip=0)
        )

        assert isinstance(result_dict, dict)
        result = ListCalendarResourcesOutput.model_validate(result_dict)
        assert result.success is True
        assert result.resources[0].name == "Meeting Room A"
        assert result.resources[0].calendar_ids == ["cal-1"]

    @pytest.mark.asyncio
    async def test_create_calendar_resource(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B3_API}/calendars/resources/rooms",
            json=_B3_RESOURCE,
        )

        result_dict = await create_calendar_resource.ainvoke(
            _args(
                resource_type="rooms",
                name="Meeting Room A",
                description="Ground floor",
                quantity=1,
                out_of_service=0,
                capacity=8,
                calendar_ids=["cal-1"],
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateCalendarResourceOutput.model_validate(result_dict)
        assert result.success is True
        assert result.resource is not None
        assert result.resource.capacity == 8.0

    @pytest.mark.asyncio
    async def test_get_calendar_resource(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B3_API}/calendars/resources/rooms/res-1",
            json=_B3_RESOURCE,
        )

        result_dict = await get_calendar_resource.ainvoke(
            _args(resource_type="rooms", resource_id="res-1")
        )

        assert isinstance(result_dict, dict)
        result = GetCalendarResourceOutput.model_validate(result_dict)
        assert result.success is True
        assert result.resource is not None
        assert result.resource.id == "res-1"

    @pytest.mark.asyncio
    async def test_update_calendar_resource(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_B3_API}/calendars/resources/rooms/res-1",
            json=dict(_B3_RESOURCE, name="Meeting Room B"),
        )

        result_dict = await update_calendar_resource.ainvoke(
            _args(resource_type="rooms", resource_id="res-1", name="Meeting Room B")
        )

        assert isinstance(result_dict, dict)
        result = UpdateCalendarResourceOutput.model_validate(result_dict)
        assert result.success is True
        assert result.resource is not None
        assert result.resource.name == "Meeting Room B"

    @pytest.mark.asyncio
    async def test_delete_calendar_resource(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_B3_API}/calendars/resources/equipments/res-2",
            json={"success": True},
        )

        result_dict = await delete_calendar_resource.ainvoke(
            _args(resource_type="equipments", resource_id="res-2")
        )

        assert isinstance(result_dict, dict)
        result = DeleteCalendarResourceOutput.model_validate(result_dict)
        assert result.success is True
        assert result.deleted is True


class TestAvailabilitySchedules:
    @pytest.mark.asyncio
    async def test_create_availability_schedule(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B3_API}/calendars/schedules",
            json={"schedule": _B3_SCHEDULE},
        )

        result_dict = await create_availability_schedule.ainvoke(
            _args(
                name="Business Hours",
                user_id="usr-1",
                timezone="America/New_York",
                rules=[
                    {
                        "type": "wday",
                        "day": "monday",
                        "intervals": [{"from": "09:00", "to": "17:00"}],
                    }
                ],
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateAvailabilityScheduleOutput.model_validate(result_dict)
        assert result.success is True
        assert result.schedule is not None
        assert result.schedule.rules[0].intervals[0].from_time == "09:00"

    @pytest.mark.asyncio
    async def test_list_availability_schedules(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B3_API}/calendars/schedules/search?locationId={_B3_LOC}&userId=usr-1",
            json={"schedules": [_B3_SCHEDULE]},
        )

        result_dict = await list_availability_schedules.ainvoke(_args(user_id="usr-1"))

        assert isinstance(result_dict, dict)
        result = ListAvailabilitySchedulesOutput.model_validate(result_dict)
        assert result.success is True
        assert result.schedules[0].timezone == "America/New_York"

    @pytest.mark.asyncio
    async def test_get_availability_schedule(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B3_API}/calendars/schedules/sch-1",
            json={"schedule": _B3_SCHEDULE},
        )

        result_dict = await get_availability_schedule.ainvoke(_args(schedule_id="sch-1"))

        assert isinstance(result_dict, dict)
        result = GetAvailabilityScheduleOutput.model_validate(result_dict)
        assert result.success is True
        assert result.schedule is not None
        assert result.schedule.id == "sch-1"

    @pytest.mark.asyncio
    async def test_update_availability_schedule(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_B3_API}/calendars/schedules/sch-1",
            json={"schedule": dict(_B3_SCHEDULE, name="Extended Hours")},
        )

        result_dict = await update_availability_schedule.ainvoke(
            _args(schedule_id="sch-1", name="Extended Hours")
        )

        assert isinstance(result_dict, dict)
        result = UpdateAvailabilityScheduleOutput.model_validate(result_dict)
        assert result.success is True
        assert result.schedule is not None
        assert result.schedule.name == "Extended Hours"

    @pytest.mark.asyncio
    async def test_delete_availability_schedule(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_B3_API}/calendars/schedules/sch-1",
            json={"success": True},
        )

        result_dict = await delete_availability_schedule.ainvoke(_args(schedule_id="sch-1"))

        assert isinstance(result_dict, dict)
        result = DeleteAvailabilityScheduleOutput.model_validate(result_dict)
        assert result.success is True
        assert result.deleted is True

    @pytest.mark.asyncio
    async def test_attach_schedule_to_calendar(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_B3_API}/calendars/schedules/sch-1/associations/cal-1",
            json={"success": True},
        )

        result_dict = await attach_schedule_to_calendar.ainvoke(
            _args(schedule_id="sch-1", calendar_id="cal-1")
        )

        assert isinstance(result_dict, dict)
        result = AttachScheduleToCalendarOutput.model_validate(result_dict)
        assert result.success is True
        assert result.attached is True

    @pytest.mark.asyncio
    async def test_detach_schedule_from_calendar(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_B3_API}/calendars/schedules/sch-1/associations/cal-1",
            json={"success": True},
        )

        result_dict = await detach_schedule_from_calendar.ainvoke(
            _args(schedule_id="sch-1", calendar_id="cal-1")
        )

        assert isinstance(result_dict, dict)
        result = DetachScheduleFromCalendarOutput.model_validate(result_dict)
        assert result.success is True
        assert result.detached is True


class TestCalendarNotifications:
    @pytest.mark.asyncio
    async def test_list_calendar_notifications(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B3_API}/calendars/cal-1/notifications",
            json=[_B3_NOTIFICATION],
        )

        result_dict = await list_calendar_notifications.ainvoke(_args(calendar_id="cal-1"))

        assert isinstance(result_dict, dict)
        result = ListCalendarNotificationsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.notifications[0].id == "ntf-1"
        assert result.notifications[0].before_time[0].unit == "mins"

    @pytest.mark.asyncio
    async def test_create_calendar_notification(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            url=f"{_B3_API}/calendars/cal-1/notifications",
            json=[_B3_NOTIFICATION],
        )

        result_dict = await create_calendar_notification.ainvoke(
            _args(
                calendar_id="cal-1",
                notifications=[
                    {
                        "receiverType": "contact",
                        "channel": "email",
                        "notificationType": "reminder",
                    }
                ],
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateCalendarNotificationOutput.model_validate(result_dict)
        assert result.success is True
        assert len(result.notifications) == 1
        assert result.notifications[0].channel == "email"

    @pytest.mark.asyncio
    async def test_get_calendar_notification(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B3_API}/calendars/cal-1/notifications/ntf-1",
            json=_B3_NOTIFICATION,
        )

        result_dict = await get_calendar_notification.ainvoke(
            _args(calendar_id="cal-1", notification_id="ntf-1")
        )

        assert isinstance(result_dict, dict)
        result = GetCalendarNotificationOutput.model_validate(result_dict)
        assert result.success is True
        assert result.notification is not None
        assert result.notification.notification_type == "reminder"

    @pytest.mark.asyncio
    async def test_update_calendar_notification(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="PUT",
            url=f"{_B3_API}/calendars/cal-1/notifications/ntf-1",
            json={"message": "Notification updated"},
        )

        result_dict = await update_calendar_notification.ainvoke(
            _args(calendar_id="cal-1", notification_id="ntf-1", is_active=False)
        )

        assert isinstance(result_dict, dict)
        result = UpdateCalendarNotificationOutput.model_validate(result_dict)
        assert result.success is True
        assert result.message == "Notification updated"

    @pytest.mark.asyncio
    async def test_delete_calendar_notification(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="DELETE",
            url=f"{_B3_API}/calendars/cal-1/notifications/ntf-1",
            json={"message": "Notification deleted"},
        )

        result_dict = await delete_calendar_notification.ainvoke(
            _args(calendar_id="cal-1", notification_id="ntf-1")
        )

        assert isinstance(result_dict, dict)
        result = DeleteCalendarNotificationOutput.model_validate(result_dict)
        assert result.success is True
        assert result.message == "Notification deleted"


class TestSchedulingEnvelopes:
    @pytest.mark.asyncio
    async def test_non_2xx_returns_error_envelope(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B3_API}/calendars/cal-missing",
            status_code=404,
            json={"message": "Calendar not found", "traceId": "trace-1"},
        )

        result_dict = await get_calendar.ainvoke(_args(calendar_id="cal-missing"))

        assert isinstance(result_dict, dict)
        result = GetCalendarOutput.model_validate(result_dict)
        assert result.success is False
        assert result.calendar is None
        assert result.error is not None
        assert "404" in result.error
        assert "Calendar not found" in result.error

    @pytest.mark.asyncio
    async def test_missing_location_short_circuits(self) -> None:
        result_dict = await list_calendars.ainvoke(_b3_args_without_location())

        assert isinstance(result_dict, dict)
        result = ListCalendarsOutput.model_validate(result_dict)
        assert result.success is False
        assert result.calendars == []
        assert result.error is not None
        assert "location" in result.error.lower()

    @pytest.mark.asyncio
    async def test_invalid_resource_type_short_circuits(self) -> None:
        result_dict = await list_calendar_resources.ainvoke(
            _args(resource_type="vehicles", limit=10, skip=0)
        )

        assert isinstance(result_dict, dict)
        result = ListCalendarResourcesOutput.model_validate(result_dict)
        assert result.success is False
        assert result.resources == []
        assert result.error is not None
        assert "equipments" in result.error

    @pytest.mark.asyncio
    async def test_wrongly_typed_fields_do_not_raise(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B3_API}/calendars/?locationId={_B3_LOC}",
            json={
                "calendars": [
                    {
                        "id": 42,
                        "name": {"unexpected": "object"},
                        "isActive": "yes",
                        "slotDuration": "30",
                        "teamMembers": "not-a-list",
                        "recurring": ["not-an-object"],
                    }
                ]
            },
        )

        result_dict = await list_calendars.ainvoke(_args())

        assert isinstance(result_dict, dict)
        result = ListCalendarsOutput.model_validate(result_dict)
        assert result.success is True
        calendar = result.calendars[0]
        assert calendar.id == "42"
        assert calendar.name is None
        assert calendar.is_active is None
        assert calendar.slot_duration is None
        assert calendar.team_members == []
        assert calendar.recurring == {}

    @pytest.mark.asyncio
    async def test_non_object_payload_does_not_raise(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{_B3_API}/calendars/cal-1",
            json=["unexpected", "array"],
        )

        result_dict = await get_calendar.ainvoke(_args(calendar_id="cal-1"))

        assert isinstance(result_dict, dict)
        result = GetCalendarOutput.model_validate(result_dict)
        assert result.success is True
        assert result.calendar is not None
        assert result.calendar.id is None

class TestSharedTransport:
    """The header contract every one of the actions shares."""

    def test_version_header_is_resolved_per_endpoint_family(self) -> None:
        # The published spec declares Version as a single-entry enum per
        # endpoint family, and the two
        # families disagree. Sending one blanket value — as some
        # clients do — is wrong for conversations and calendars.
        assert _api_version("/contacts/") == "2021-07-28"
        assert _api_version("/opportunities/search") == "2021-07-28"
        assert _api_version("/emails/builder") == "2021-07-28"
        assert _api_version("/campaigns/") == "2021-07-28"
        assert _api_version("/conversations/messages") == "2021-04-15"
        assert _api_version("/calendars/events") == "2021-04-15"

    @pytest.mark.asyncio
    async def test_calendar_request_sends_the_legacy_version(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(method="GET", json={"calendars": []})

        await list_calendars.ainvoke(_args())

        request = httpx_mock.get_requests()[0]
        assert request.headers["Version"] == "2021-04-15"

    @pytest.mark.asyncio
    async def test_contact_request_sends_the_current_version(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(method="GET", json={"contacts": []})

        await list_contacts.ainvoke(_args())

        request = httpx_mock.get_requests()[0]
        assert request.headers["Version"] == "2021-07-28"

    @pytest.mark.asyncio
    async def test_missing_token_short_circuits_before_any_request(self) -> None:
        result_dict = await list_contacts.ainvoke(
            {"auth_type": "oauth2", "auth_data": {"location_id": "loc_1"}}
        )

        assert isinstance(result_dict, dict)
        assert result_dict["success"] is False
        assert "token" in str(result_dict["error"]).lower()



class TestRequestSafety:
    """Guards that keep an LLM-supplied value from changing what is called."""

    @pytest.mark.asyncio
    async def test_path_traversal_in_an_id_cannot_retarget_the_call(
        self, httpx_mock: Any
    ) -> None:
        # httpx resolves dot segments while building the URL, so an
        # unencoded id would turn GET /contacts/{id} into GET /oauth/token.
        httpx_mock.add_response(json={"contact": {"id": "x"}})

        await get_contact.ainvoke(_args(contact_id="../../oauth/token"))

        url = str(httpx_mock.get_requests()[0].url)
        assert "/oauth/token" not in url
        assert url.startswith("https://services.leadconnectorhq.com/contacts/")

    @pytest.mark.asyncio
    async def test_query_injection_in_an_id_is_encoded(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"contact": {"id": "x"}})

        await get_contact.ainvoke(_args(contact_id="ct_1?limit=100"))

        request = httpx_mock.get_requests()[0]
        assert "limit" not in dict(request.url.params)

    @pytest.mark.asyncio
    async def test_a_dot_id_cannot_reach_the_parent_collection(
        self, httpx_mock: Any
    ) -> None:
        # `.` and `..` are in quote()'s always-safe set, so encoding alone
        # leaves them as dot segments that httpx resolves away.
        httpx_mock.add_response(json={"contact": {"id": "x"}})

        await get_contact.ainvoke(_args(contact_id="."))

        path = httpx_mock.get_requests()[0].url.path
        assert not path.endswith("/contacts")
        assert path.endswith("/contacts/-")

    @pytest.mark.asyncio
    async def test_a_double_dot_id_cannot_drop_the_entity_segment(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json={"contact": {"id": "x"}})

        await get_contact.ainvoke(_args(contact_id=".."))

        assert httpx_mock.get_requests()[0].url.path.endswith("/contacts/-")

    @pytest.mark.asyncio
    async def test_empty_id_does_not_collapse_onto_the_collection(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json={"contact": {"id": "x"}})

        await get_contact.ainvoke(_args(contact_id=""))

        assert not str(httpx_mock.get_requests()[0].url).endswith("/contacts/")

    @pytest.mark.asyncio
    async def test_calendar_resource_type_is_case_insensitive(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json=[])

        result_dict = await list_calendar_resources.ainvoke(
            _args(resource_type="Rooms", limit=10, skip=0)
        )

        assert result_dict["success"] is True
        assert "/calendars/resources/rooms" in str(httpx_mock.get_requests()[0].url)

    @pytest.mark.asyncio
    async def test_unknown_calendar_resource_type_is_rejected(self) -> None:
        result_dict = await list_calendar_resources.ainvoke(
            _args(resource_type="chairs", limit=10, skip=0)
        )

        assert result_dict["success"] is False
        assert "equipments" in str(result_dict["error"])


class TestCoercionFidelity:
    """Coercers must not silently discard data the vendor really sends."""

    @pytest.mark.asyncio
    async def test_integral_floats_survive_as_counts(self, httpx_mock: Any) -> None:
        # Every numeric field in the published spec is declared "number",
        # never "integer", so a count can legitimately arrive as 100.0.
        httpx_mock.add_response(json={"contacts": [], "total": 100.0})

        result_dict = await search_contacts.ainvoke(_args(page_limit=20))

        assert result_dict["total"] == 100

    @pytest.mark.asyncio
    async def test_fractional_numbers_are_not_truncated(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"contacts": [], "total": 100.5})

        result_dict = await search_contacts.ainvoke(_args(page_limit=20))

        assert result_dict["total"] is None

    @pytest.mark.asyncio
    async def test_business_removal_sends_an_explicit_null(
        self, httpx_mock: Any
    ) -> None:
        # businessId is declared required AND nullable: omitting the key and
        # sending null mean different things, and null is how you detach.
        httpx_mock.add_response(json={"success": True, "ids": ["ct_1"]})

        await bulk_update_contacts_business.ainvoke(_args(contact_ids=["ct_1"]))

        body = json.loads(httpx_mock.get_requests()[0].content)
        assert "businessId" in body
        assert body["businessId"] is None

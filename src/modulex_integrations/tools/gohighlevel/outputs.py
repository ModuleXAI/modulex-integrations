"""Pydantic response models for the GoHighLevel integration.

One ``<Action>Output`` per action, each carrying ``success`` and ``error``
alongside its payload. Payload fields are deliberately permissive
(``<type> | None``) — the v2 API is loosely typed and routinely omits
fields, so the tool functions coerce every value before it lands here.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ContactCustomField(BaseModel):
    """One custom-field value on a contact.

    Core CRM resources mirror the GoHighLevel Contacts and Opportunities
    schemas. Field names are snake_case renderings of the upstream camelCase
    keys; the mapping happens in the ``_parse_*`` helpers in ``tools.py``.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    value: str | None = None


class ContactDndSetting(BaseModel):
    """Do-not-disturb state for a single channel (``DndSettingSchema``)."""

    model_config = ConfigDict(extra="forbid")

    status: str | None = None
    message: str | None = None
    code: str | None = None


class ContactDndSettings(BaseModel):
    """Per-channel do-not-disturb map (``DndSettingsSchema``)."""

    model_config = ConfigDict(extra="forbid")

    call: ContactDndSetting | None = None
    email: ContactDndSetting | None = None
    sms: ContactDndSetting | None = None
    whatsapp: ContactDndSetting | None = None
    gmb: ContactDndSetting | None = None
    fb: ContactDndSetting | None = None


class ContactAttribution(BaseModel):
    """Marketing attribution payload (``AttributionSource``)."""

    model_config = ConfigDict(extra="forbid")

    url: str | None = None
    campaign: str | None = None
    campaign_id: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_content: str | None = None
    referrer: str | None = None
    fbclid: str | None = None
    gclid: str | None = None
    msclikid: str | None = None
    dclid: str | None = None
    fbc: str | None = None
    fbp: str | None = None
    fb_event_id: str | None = None
    user_agent: str | None = None
    ip: str | None = None
    medium: str | None = None
    medium_id: str | None = None


class ContactResource(BaseModel):
    """A GoHighLevel contact.

    Union of the three contact shapes the Contacts API documents:
    ``GetContectByIdSchema``, ``CreateContactSchema`` and
    ``ContactsSearchSchema``. Every field is optional because which subset
    an endpoint returns depends on the endpoint.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    company_name: str | None = None
    location_id: str | None = None
    timezone: str | None = None
    source: str | None = None
    type: str | None = None
    assigned_to: str | None = None
    address1: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    website: str | None = None
    tags: list[str] = Field(default_factory=list)
    date_of_birth: str | None = None
    date_added: str | None = None
    date_updated: str | None = None
    last_activity: str | None = None
    dnd: bool | None = None
    dnd_settings: ContactDndSettings | None = None
    business_id: str | None = None
    custom_fields: list[ContactCustomField] = Field(default_factory=list)
    followers: list[str] = Field(default_factory=list)
    deleted: bool | None = None
    attribution_source: ContactAttribution | None = None
    last_attribution_source: ContactAttribution | None = None
    attributions: list[ContactAttribution] = Field(default_factory=list)


class ContactNoteResource(BaseModel):
    """A note attached to a contact (``GetNoteSchema``)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    body: str | None = None
    title: str | None = None
    color: str | None = None
    pinned: bool | None = None
    user_id: str | None = None
    contact_id: str | None = None
    date_added: str | None = None


class ContactTaskResource(BaseModel):
    """A task attached to a contact (``TaskSchema``)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    title: str | None = None
    body: str | None = None
    assigned_to: str | None = None
    due_date: str | None = None
    completed: bool | None = None
    contact_id: str | None = None


class ContactAppointmentResource(BaseModel):
    """A calendar event booked for a contact (``GetEventSchema``)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    calendar_id: str | None = None
    status: str | None = None
    title: str | None = None
    assigned_user_id: str | None = None
    notes: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    address: str | None = None
    location_id: str | None = None
    contact_id: str | None = None
    group_id: str | None = None
    appointment_status: str | None = None
    users: list[str] = Field(default_factory=list)
    assigned_resources: list[str] = Field(default_factory=list)
    date_added: str | None = None
    date_updated: str | None = None


class OpportunityCustomField(BaseModel):
    """One custom-field value on an opportunity (``CustomFieldResponseSchema``).

    ``field_value`` is a ``oneOf`` upstream (string, object, array of string,
    array of object), so it is passed through untouched.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    field_value: Any = None


class OpportunityContactResource(BaseModel):
    """The contact embedded in an opportunity search hit."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    name: str | None = None
    company_name: str | None = None
    email: str | None = None
    phone: str | None = None
    tags: list[str] = Field(default_factory=list)


class OpportunityResource(BaseModel):
    """An opportunity (``SearchOpportunitiesResponseSchema``)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    name: str | None = None
    monetary_value: float | None = None
    pipeline_id: str | None = None
    pipeline_stage_id: str | None = None
    assigned_to: str | None = None
    status: str | None = None
    source: str | None = None
    contact_id: str | None = None
    location_id: str | None = None
    lost_reason_id: str | None = None
    external_object_id: str | None = None
    index_version: str | None = None
    last_status_change_at: str | None = None
    last_stage_change_at: str | None = None
    last_action_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    contact: OpportunityContactResource | None = None
    custom_fields: list[OpportunityCustomField] = Field(default_factory=list)
    notes: list[Any] = Field(default_factory=list)
    tasks: list[Any] = Field(default_factory=list)
    calendar_events: list[Any] = Field(default_factory=list)
    followers: list[Any] = Field(default_factory=list)


class OpportunitySearchMeta(BaseModel):
    """Pagination cursor block of an opportunity search (``SearchMetaResponseSchema``)."""

    model_config = ConfigDict(extra="forbid")

    total: int | None = None
    next_page_url: str | None = None
    start_after_id: str | None = None
    start_after: int | None = None
    current_page: int | None = None
    next_page: int | None = None
    prev_page: int | None = None


class PipelineResource(BaseModel):
    """An opportunity pipeline (``PipelinesResponseSchema``)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    name: str | None = None
    location_id: str | None = None
    stages: list[Any] = Field(default_factory=list)
    show_in_funnel: bool | None = None
    show_in_pie_chart: bool | None = None
    color_render_mode: str | None = None


class OpportunityLostReasonResource(BaseModel):
    """A configured "lost" reason (``LostReasonResponseSchema``)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    name: str | None = None
    location_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


# --- Contacts action outputs ------------------------------------------------


class CreateContactOutput(BaseModel):
    """Result of creating a contact."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    contact: ContactResource | None = None


class ListContactsOutput(BaseModel):
    """A page of contacts for the connected sub-account."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    contacts: list[ContactResource] = Field(default_factory=list)
    count: int | None = None


class BulkUpdateContactsBusinessOutput(BaseModel):
    """Result of a bulk add/remove of contacts to a business."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    succeeded: bool | None = None
    ids: list[str] = Field(default_factory=list)


class BulkUpdateContactTagsOutput(BaseModel):
    """Result of a bulk contact tag add/remove."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    succeeded: bool | None = None
    error_count: int | None = None
    # The spec declares ``items: {type: string}`` but its own example is an
    # array of per-contact objects (contactId, message, type, oldTags,
    # tagsAdded, tagsRemoved). Typed permissively so neither shape is
    # silently dropped — a string-only coercer would return [] for the
    # documented example.
    responses: list[Any] = Field(default_factory=list)


class ListBusinessContactsOutput(BaseModel):
    """A page of contacts belonging to one business."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    contacts: list[ContactResource] = Field(default_factory=list)
    count: int | None = None


class SearchContactsOutput(BaseModel):
    """Contacts matching an advanced filter search."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    contacts: list[ContactResource] = Field(default_factory=list)
    total: int | None = None


class GetDuplicateContactOutput(BaseModel):
    """The duplicate contact matched by email or phone, if any."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    contact: ContactResource | None = None


class UpsertContactOutput(BaseModel):
    """Result of creating or updating a contact by duplicate match."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    contact: ContactResource | None = None
    new: bool | None = None
    trace_id: str | None = None


class GetContactOutput(BaseModel):
    """A single contact."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    contact: ContactResource | None = None


class UpdateContactOutput(BaseModel):
    """Result of updating a contact."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    succeeded: bool | None = None
    contact: ContactResource | None = None


class DeleteContactOutput(BaseModel):
    """Result of deleting a contact."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    succeeded: bool | None = None


class ListContactAppointmentsOutput(BaseModel):
    """Calendar events booked for a contact."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    events: list[ContactAppointmentResource] = Field(default_factory=list)


class RemoveContactFromEveryCampaignOutput(BaseModel):
    """Result of unenrolling a contact from every campaign."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    succeeded: bool | None = None


class AddContactToCampaignOutput(BaseModel):
    """Result of enrolling a contact in a campaign."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    succeeded: bool | None = None


class RemoveContactFromCampaignOutput(BaseModel):
    """Result of unenrolling a contact from one campaign."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    succeeded: bool | None = None


class AddContactFollowersOutput(BaseModel):
    """Followers after adding users to a contact."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    followers: list[str] = Field(default_factory=list)
    followers_added: list[str] = Field(default_factory=list)


class RemoveContactFollowersOutput(BaseModel):
    """Followers after removing users from a contact."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    followers: list[str] = Field(default_factory=list)
    followers_removed: list[str] = Field(default_factory=list)


class ListContactNotesOutput(BaseModel):
    """All notes on a contact."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    notes: list[ContactNoteResource] = Field(default_factory=list)


class CreateContactNoteOutput(BaseModel):
    """The note created on a contact."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    note: ContactNoteResource | None = None


class GetContactNoteOutput(BaseModel):
    """A single note on a contact."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    note: ContactNoteResource | None = None


class UpdateContactNoteOutput(BaseModel):
    """The updated note."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    note: ContactNoteResource | None = None


class DeleteContactNoteOutput(BaseModel):
    """Result of deleting a note."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    succeeded: bool | None = None


class AddContactTagsOutput(BaseModel):
    """Tags on the contact after the add."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    tags: list[str] = Field(default_factory=list)


class RemoveContactTagsOutput(BaseModel):
    """Tags on the contact after the removal."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    tags: list[str] = Field(default_factory=list)


class ListContactTasksOutput(BaseModel):
    """All tasks on a contact."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    tasks: list[ContactTaskResource] = Field(default_factory=list)


class CreateContactTaskOutput(BaseModel):
    """The task created on a contact."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    task: ContactTaskResource | None = None


class GetContactTaskOutput(BaseModel):
    """A single task on a contact."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    task: ContactTaskResource | None = None


class UpdateContactTaskOutput(BaseModel):
    """The updated task."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    task: ContactTaskResource | None = None


class DeleteContactTaskOutput(BaseModel):
    """Result of deleting a task."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    succeeded: bool | None = None


class CompleteContactTaskOutput(BaseModel):
    """The task after its completed flag was changed."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    task: ContactTaskResource | None = None


class AddContactToWorkflowOutput(BaseModel):
    """Result of adding a contact to a workflow."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    succeeded: bool | None = None


class DeleteContactFromWorkflowOutput(BaseModel):
    """Result of removing a contact from a workflow."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    succeeded: bool | None = None


# --- Opportunity action outputs ---------------------------------------------


class CreateOpportunityOutput(BaseModel):
    """The opportunity that was created."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    opportunity: OpportunityResource | None = None


class ListOpportunityLostReasonsOutput(BaseModel):
    """Configured lost reasons for the sub-account."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    lost_reasons: list[OpportunityLostReasonResource] = Field(default_factory=list)
    total: int | None = None


class ListPipelinesOutput(BaseModel):
    """Opportunity pipelines with their stages."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    pipelines: list[PipelineResource] = Field(default_factory=list)


class SearchOpportunitiesOutput(BaseModel):
    """Opportunities matching the filter query."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    opportunities: list[OpportunityResource] = Field(default_factory=list)
    meta: OpportunitySearchMeta | None = None
    aggregations: dict[str, Any] = Field(default_factory=dict)


class SearchOpportunitiesAdvancedOutput(BaseModel):
    """Opportunities matching an advanced search, with optional related records."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    opportunities: list[OpportunityResource] = Field(default_factory=list)
    total: int | None = None
    aggregations: dict[str, Any] = Field(default_factory=dict)


class UpsertOpportunityOutput(BaseModel):
    """The opportunity that was created or updated."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    opportunity: OpportunityResource | None = None
    new: bool | None = None


class GetOpportunityOutput(BaseModel):
    """A single opportunity."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    opportunity: OpportunityResource | None = None


class DeleteOpportunityOutput(BaseModel):
    """Result of deleting an opportunity."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    succeeded: bool | None = None


class UpdateOpportunityOutput(BaseModel):
    """The updated opportunity."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    opportunity: OpportunityResource | None = None


class AddOpportunityFollowersOutput(BaseModel):
    """Followers after adding users to an opportunity."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    followers: list[str] = Field(default_factory=list)
    followers_added: list[str] = Field(default_factory=list)


class RemoveOpportunityFollowersOutput(BaseModel):
    """Followers after removing users from an opportunity."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    followers: list[str] = Field(default_factory=list)
    followers_removed: list[str] = Field(default_factory=list)


class UpdateOpportunityStatusOutput(BaseModel):
    """Result of changing an opportunity's status."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    succeeded: bool | None = None


# --- Communication: conversations, messages, emails, campaigns -------------
#
# Every model below is derived from the 200/201 response ``$ref`` of its
# endpoint in the published conversations API spec, the published email API spec or
# the published campaigns API spec. Fields stay permissive because the upstream
# ``required`` lists routinely disagree with what the API actually sends.


class ConversationResource(BaseModel):
    """A conversation thread.

    Union of the four conversation shapes the API returns: ``ConversationSchema``
    (search), ``ConversationCreateResponseDto`` (create),
    ``GetConversationByIdResponse`` (get) and ``ConversationDto`` (update).
    ``conversation_type`` is a string because the search response sends the
    ``TYPE_PHONE`` enum while the get-by-id response sends the numeric code.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    contact_id: str | None = None
    location_id: str | None = None
    assigned_to: str | None = None
    user_id: str | None = None
    conversation_type: str | None = None
    unread_count: int | None = None
    last_message_body: str | None = None
    last_message_type: str | None = None
    last_message_date: str | None = None
    full_name: str | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    inbox: bool | None = None
    starred: bool | None = None
    deleted: bool | None = None
    date_added: str | None = None
    date_updated: str | None = None


class MessageMetaResource(BaseModel):
    """Channel-specific metadata attached to a message (``MessageMeta``)."""

    model_config = ConfigDict(extra="forbid")

    call_duration: str | None = None
    call_status: str | None = None
    email: dict[str, Any] | None = None


class MessageResource(BaseModel):
    """One conversation message (``GetMessageResponseDto``).

    ``message_type_code`` is the numeric ``type`` field; ``message_type`` is
    the ``TYPE_*`` string form of the same value.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    message_type_code: int | None = None
    message_type: str | None = None
    location_id: str | None = None
    contact_id: str | None = None
    conversation_id: str | None = None
    date_added: str | None = None
    body: str | None = None
    direction: str | None = None
    status: str | None = None
    content_type: str | None = None
    attachments: list[str] = Field(default_factory=list)
    meta: MessageMetaResource | None = None
    source: str | None = None
    user_id: str | None = None
    conversation_provider_id: str | None = None
    chat_widget_id: str | None = None


class EmailMessageResource(BaseModel):
    """A single email message (``GetEmailMessageResponseDto``).

    ``from_address`` carries the upstream ``from`` field, which cannot be a
    Python attribute name.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    alt_id: str | None = None
    thread_id: str | None = None
    location_id: str | None = None
    contact_id: str | None = None
    conversation_id: str | None = None
    date_added: str | None = None
    subject: str | None = None
    body: str | None = None
    direction: str | None = None
    status: str | None = None
    content_type: str | None = None
    attachments: list[str] = Field(default_factory=list)
    provider: str | None = None
    from_address: str | None = None
    to: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    reply_to_message_id: str | None = None
    source: str | None = None
    conversation_provider_id: str | None = None


class MessageForwardResource(BaseModel):
    """Metadata returned when an email send was a forward (``ForwardResponseDto``)."""

    model_config = ConfigDict(extra="forbid")

    forward_whole_thread: bool | None = None
    message_id: str | None = None
    email_message_id: str | None = None
    source_contact_id: str | None = None
    source_conversation_id: str | None = None
    forward_to_email: str | None = None
    recipient_contact_id: str | None = None
    recipient_conversation_id: str | None = None


class MessageTranscriptSegmentResource(BaseModel):
    """One transcribed sentence (``GetMessageTranscriptionResponseDto``)."""

    model_config = ConfigDict(extra="forbid")

    media_channel: int | None = None
    sentence_index: int | None = None
    start_time: float | None = None
    end_time: float | None = None
    transcript: str | None = None
    confidence: float | None = None


class EmailTemplateResource(BaseModel):
    """An email-builder template (``FetchBuilderSuccesfulResponseDto``)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    name: str | None = None
    template_type: str | None = None
    version: str | None = None
    is_plain_text: bool | None = None
    preview_url: str | None = None
    updated_by: str | None = None
    last_updated: str | None = None
    date_added: str | None = None


class EmailScheduleResource(BaseModel):
    """A scheduled email campaign (``ScheduleDto``).

    The upstream Mongo internals ``_id`` and ``__v`` are dropped: a leading
    underscore cannot be a pydantic field name.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    name: str | None = None
    status: str | None = None
    location_id: str | None = None
    parent_id: str | None = None
    child_count: int | None = None
    child: list[str] = Field(default_factory=list)
    campaign_type: str | None = None
    bulk_action_version: str | None = None
    repeat_after: str | None = None
    send_days: list[str] = Field(default_factory=list)
    template_id: str | None = None
    template_type: str | None = None
    document_id: str | None = None
    download_url: str | None = None
    template_data_download_url: str | None = None
    deleted: bool | None = None
    migrated: bool | None = None
    archived: bool | None = None
    has_tracking: bool | None = None
    has_utm_tracking: bool | None = None
    is_plain_text: bool | None = None
    enable_resend_to_unopened: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CampaignResource(BaseModel):
    """A campaign summary (``campaignsSchema``)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    name: str | None = None
    status: str | None = None
    location_id: str | None = None


class ListCampaignsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    campaigns: list[CampaignResource] = Field(default_factory=list)


class CreateConversationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    conversation: ConversationResource | None = None


class GetMessageTranscriptionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    segments: list[MessageTranscriptSegmentResource] = Field(default_factory=list)


class SendMessageOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    conversation_id: str | None = None
    message_id: str | None = None
    message_ids: list[str] = Field(default_factory=list)
    email_message_id: str | None = None
    status: str | None = None
    msg: str | None = None
    forward_data: MessageForwardResource | None = None


class CancelScheduledEmailMessageOutput(BaseModel):
    """``CancelScheduledResponseDto`` — ``status_code`` is the upstream ``status``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    status_code: int | None = None
    message: str | None = None


class GetEmailByIdOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    email: EmailMessageResource | None = None


class ExportMessagesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    messages: list[MessageResource] = Field(default_factory=list)
    next_cursor: str | None = None
    total: int | None = None


class AddInboundMessageOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    conversation_id: str | None = None
    message_id: str | None = None
    email_message_id: str | None = None
    contact_id: str | None = None
    message: str | None = None
    date_added: str | None = None


class AddOutboundMessageOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    conversation_id: str | None = None
    message_id: str | None = None
    email_message_id: str | None = None
    contact_id: str | None = None
    message: str | None = None
    date_added: str | None = None


class SendReviewReplyOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    conversation_id: str | None = None
    message_id: str | None = None
    message_ids: list[str] = Field(default_factory=list)
    email_message_id: str | None = None
    status: str | None = None
    msg: str | None = None


class CompleteMessageFileUploadOutput(BaseModel):
    """``CompleteFileUploadResponseDto`` — ``uploaded_files`` maps filename to URL."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    uploaded_files: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class InitiateMessageFileUploadOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    upload_url: str | None = None
    upload_id: str | None = None
    file_path: str | None = None
    expires_at: int | None = None
    max_file_size: int | None = None


class GetMessageOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    message: MessageResource | None = None


class AddMessageAttachmentsOutput(BaseModel):
    """the published conversations API spec declares no 200 body, so ``data`` is verbatim."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CancelScheduledMessageOutput(BaseModel):
    """``CancelScheduledResponseDto`` — ``status_code`` is the upstream ``status``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    status_code: int | None = None
    message: str | None = None


class UpdateMessageStatusOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    conversation_id: str | None = None
    message_id: str | None = None
    message_ids: list[str] = Field(default_factory=list)
    email_message_id: str | None = None
    status: str | None = None
    msg: str | None = None


class ListCustomSubtypesOutput(BaseModel):
    """the published conversations API spec declares no 200 body, so both shapes are kept."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    custom_subtypes: list[dict[str, Any]] = Field(default_factory=list)
    data: dict[str, Any] | None = None


class CreateCustomSubtypeOutput(BaseModel):
    """the published conversations API spec declares no 200/201 body, so ``data`` is verbatim."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class UpdateCustomSubtypeOutput(BaseModel):
    """the published conversations API spec declares no 200 body, so ``data`` is verbatim."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetContactUnsubscriptionStatusOutput(BaseModel):
    """the published conversations API spec declares no 200 body, so both shapes are kept."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    subscriptions: list[dict[str, Any]] = Field(default_factory=list)
    data: dict[str, Any] | None = None


class UpdateSubscriptionPreferenceOutput(BaseModel):
    """the published conversations API spec declares no 200/201 body, so ``data`` is verbatim."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class LiveChatAgentTypingOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None


class SearchConversationsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    conversations: list[ConversationResource] = Field(default_factory=list)
    total: int | None = None


class GetConversationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    conversation: ConversationResource | None = None


class UpdateConversationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    conversation: ConversationResource | None = None


class DeleteConversationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None


class ListConversationMessagesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    messages: list[MessageResource] = Field(default_factory=list)
    last_message_id: str | None = None
    next_page: bool | None = None


class CreateEmailTemplateOutput(BaseModel):
    """``CreateBuilderSuccesfulResponseDto`` — upstream ``redirect`` is the new id."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    template_id: str | None = None
    trace_id: str | None = None


class ListEmailTemplatesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    templates: list[EmailTemplateResource] = Field(default_factory=list)


class UpdateEmailTemplateOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    ok: str | None = None
    trace_id: str | None = None
    preview_url: str | None = None
    template_download_url: str | None = None


class DeleteEmailTemplateOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    ok: str | None = None
    trace_id: str | None = None


class ListScheduledEmailsOutput(BaseModel):
    """``ScheduleFetchSuccessfulDTO`` — upstream types ``total`` as a string array."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    schedules: list[EmailScheduleResource] = Field(default_factory=list)
    total: list[str] = Field(default_factory=list)
    trace_id: str | None = None


class CalendarEventCreator(BaseModel):
    """Who created or last updated a calendar event (``CreatedOrUpdatedBy``).

    First of the scheduling entity models. Each one mirrors a schema in the
    GoHighLevel calendars API document; JSON keys are camelCase upstream while
    the Python fields are snake_case, and the mapping happens in the matching
    ``_parse_*`` helper in ``tools.py``.
    """

    model_config = ConfigDict(extra="forbid")

    user_id: str | None = None
    source: str | None = None


class CalendarEventDetails(BaseModel):
    """One calendar event / appointment record (``CalendarEventDTO``)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    address: str | None = None
    title: str | None = None
    calendar_id: str | None = None
    location_id: str | None = None
    contact_id: str | None = None
    group_id: str | None = None
    appointment_status: str | None = None
    assigned_user_id: str | None = None
    users: list[str] = Field(default_factory=list)
    notes: str | None = None
    description: str | None = None
    is_recurring: bool | None = None
    rrule: str | None = None
    # Upstream declares startTime/endTime/dateAdded/dateUpdated as `type:
    # object` even though the documented examples are ISO-8601 strings; the
    # coercers degrade any non-scalar to None rather than raising.
    start_time: str | None = None
    end_time: str | None = None
    date_added: str | None = None
    date_updated: str | None = None
    assigned_resources: list[str] = Field(default_factory=list)
    created_by: CalendarEventCreator | None = None
    master_event_id: str | None = None


class AppointmentDetails(BaseModel):
    """An appointment as returned by the create/update endpoints.

    Mirrors ``AppointmentSchemaResponse`` — a flatter shape than
    ``CalendarEventDetails``, which is what the read endpoints return.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    calendar_id: str | None = None
    location_id: str | None = None
    contact_id: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    title: str | None = None
    meeting_location_type: str | None = None
    appointment_status: str | None = None
    assigned_user_id: str | None = None
    address: str | None = None
    is_recurring: bool | None = None
    rrule: str | None = None


class AppointmentNoteCreator(BaseModel):
    """Author of an appointment note (``NoteCreatedBySchema``)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    name: str | None = None


class AppointmentNoteDetails(BaseModel):
    """A note attached to an appointment (``GetNoteSchema``)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    body: str | None = None
    user_id: str | None = None
    date_added: str | None = None
    contact_id: str | None = None
    created_by: AppointmentNoteCreator | None = None


class BlockSlotDetails(BaseModel):
    """A blocked (unbookable) slot (``BlockedSlotSuccessfulResponseDto``)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    location_id: str | None = None
    title: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    calendar_id: str | None = None
    assigned_user_id: str | None = None


class CalendarGroupDetails(BaseModel):
    """A calendar group (``GroupDTO``)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    location_id: str | None = None
    name: str | None = None
    description: str | None = None
    slug: str | None = None
    is_active: bool | None = None


class CalendarResourceDetails(BaseModel):
    """A bookable room or piece of equipment.

    Mirrors ``CalendarResourceByIdResponseDTO``. ``id`` is surfaced from the
    response's ``id``/``_id`` key: the upstream schema omits an identifier even
    though every single-resource path requires one.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    location_id: str | None = None
    name: str | None = None
    resource_type: str | None = None
    is_active: bool | None = None
    description: str | None = None
    quantity: float | None = None
    out_of_service: float | None = None
    capacity: float | None = None
    calendar_ids: list[str] = Field(default_factory=list)


class CalendarNotificationSchedule(BaseModel):
    """A relative notification offset (``SchedulesDTO``)."""

    model_config = ConfigDict(extra="forbid")

    time_offset: float | None = None
    unit: str | None = None


class CalendarNotificationDetails(BaseModel):
    """A calendar notification rule (``CalendarNotificationResponseDTO``)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    receiver_type: str | None = None
    additional_email_ids: list[str] = Field(default_factory=list)
    additional_phone_numbers: list[str] = Field(default_factory=list)
    additional_whatsapp_numbers: list[str] = Field(default_factory=list)
    channel: str | None = None
    notification_type: str | None = None
    is_active: bool | None = None
    template_id: str | None = None
    body: str | None = None
    subject: str | None = None
    after_time: list[CalendarNotificationSchedule] = Field(default_factory=list)
    before_time: list[CalendarNotificationSchedule] = Field(default_factory=list)
    selected_users: list[str] = Field(default_factory=list)
    deleted: bool | None = None


class AvailabilityScheduleInterval(BaseModel):
    """One open time window (``ScheduleIntervalDTO``).

    Upstream calls the bounds ``from``/``to``; ``from`` is a Python keyword, so
    the fields are exposed as ``from_time``/``to_time``.
    """

    model_config = ConfigDict(extra="forbid")

    from_time: str | None = None
    to_time: str | None = None


class AvailabilityScheduleRule(BaseModel):
    """One availability rule (``ScheduleRuleDTO``)."""

    model_config = ConfigDict(extra="forbid")

    type: str | None = None
    intervals: list[AvailabilityScheduleInterval] = Field(default_factory=list)
    date: str | None = None
    day: str | None = None


class AvailabilityScheduleDetails(BaseModel):
    """A user availability schedule (``ScheduleObjectResponseDTO``)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    name: str | None = None
    location_id: str | None = None
    rules: list[AvailabilityScheduleRule] = Field(default_factory=list)
    timezone: str | None = None
    date_added: str | None = None
    date_updated: str | None = None
    user_id: str | None = None
    calendar_ids: list[str] = Field(default_factory=list)
    deleted: bool | None = None


class CalendarFreeSlotDay(BaseModel):
    """Free slots for one calendar day.

    The free-slots endpoint returns a map keyed by ``YYYY-MM-DD`` whose values
    are ``SlotsSchema`` objects; this flattens one entry of that map.
    """

    model_config = ConfigDict(extra="forbid")

    date: str | None = None
    slots: list[str] = Field(default_factory=list)


class CalendarDetails(BaseModel):
    """A booking calendar (``CalendarDTO``).

    Nested settings that upstream models as objects/arrays of objects
    (``teamMembers``, ``openHours``, ``availabilities``, ``recurring``,
    ``lookBusyConfig``, ``locationConfigurations``, ``notifications``) are kept
    as raw JSON so no upstream field is silently dropped.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    location_id: str | None = None
    group_id: str | None = None
    name: str | None = None
    description: str | None = None
    slug: str | None = None
    widget_slug: str | None = None
    calendar_type: str | None = None
    widget_type: str | None = None
    event_type: str | None = None
    event_title: str | None = None
    event_color: str | None = None
    is_active: bool | None = None
    meeting_location: str | None = None
    slot_duration: float | None = None
    slot_duration_unit: str | None = None
    slot_interval: float | None = None
    slot_interval_unit: str | None = None
    slot_buffer: float | None = None
    slot_buffer_unit: str | None = None
    pre_buffer: float | None = None
    pre_buffer_unit: str | None = None
    appointment_per_slot: float | None = None
    appointment_per_day: float | None = None
    allow_booking_after: float | None = None
    allow_booking_after_unit: str | None = None
    allow_booking_for: float | None = None
    allow_booking_for_unit: str | None = None
    enable_recurring: bool | None = None
    form_id: str | None = None
    sticky_contact: bool | None = None
    is_live_payment_mode: bool | None = None
    auto_confirm: bool | None = None
    should_send_alert_emails_to_assigned_member: bool | None = None
    alert_email: str | None = None
    google_invitation_emails: bool | None = None
    allow_reschedule: bool | None = None
    allow_cancellation: bool | None = None
    should_assign_contact_to_team_member: bool | None = None
    should_skip_assigning_contact_for_existing: bool | None = None
    notes: str | None = None
    pixel_id: str | None = None
    form_submit_type: str | None = None
    form_submit_redirect_url: str | None = None
    form_submit_thanks_message: str | None = None
    availability_type: float | None = None
    guest_type: str | None = None
    consent_label: str | None = None
    calendar_cover_image: str | None = None
    team_members: list[dict[str, Any]] = Field(default_factory=list)
    location_configurations: list[dict[str, Any]] = Field(default_factory=list)
    open_hours: list[dict[str, Any]] = Field(default_factory=list)
    availabilities: list[dict[str, Any]] = Field(default_factory=list)
    notifications: list[dict[str, Any]] = Field(default_factory=list)
    recurring: dict[str, Any] = Field(default_factory=dict)
    look_busy_config: dict[str, Any] = Field(default_factory=dict)


# --- Calendars --------------------------------------------------------------


class ListCalendarsOutput(BaseModel):
    """Result of ``list_calendars``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    calendars: list[CalendarDetails] = Field(default_factory=list)


class CreateCalendarOutput(BaseModel):
    """Result of ``create_calendar``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    calendar: CalendarDetails | None = None


class GetCalendarOutput(BaseModel):
    """Result of ``get_calendar``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    calendar: CalendarDetails | None = None


class UpdateCalendarOutput(BaseModel):
    """Result of ``update_calendar``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    calendar: CalendarDetails | None = None


class DeleteCalendarOutput(BaseModel):
    """Result of ``delete_calendar``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    deleted: bool | None = None


class GetCalendarFreeSlotsOutput(BaseModel):
    """Result of ``get_calendar_free_slots``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    days: list[CalendarFreeSlotDay] = Field(default_factory=list)


# --- Appointment notes ------------------------------------------------------


class ListAppointmentNotesOutput(BaseModel):
    """Result of ``list_appointment_notes``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    notes: list[AppointmentNoteDetails] = Field(default_factory=list)
    has_more: bool | None = None


class CreateAppointmentNoteOutput(BaseModel):
    """Result of ``create_appointment_note``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    note: AppointmentNoteDetails | None = None


class UpdateAppointmentNoteOutput(BaseModel):
    """Result of ``update_appointment_note``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    note: AppointmentNoteDetails | None = None


class DeleteAppointmentNoteOutput(BaseModel):
    """Result of ``delete_appointment_note``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    deleted: bool | None = None


# --- Events, appointments and block slots -----------------------------------


class ListBlockedSlotsOutput(BaseModel):
    """Result of ``list_blocked_slots``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    events: list[CalendarEventDetails] = Field(default_factory=list)


class ListCalendarEventsOutput(BaseModel):
    """Result of ``list_calendar_events``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    events: list[CalendarEventDetails] = Field(default_factory=list)


class CreateAppointmentOutput(BaseModel):
    """Result of ``create_appointment``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    appointment: AppointmentDetails | None = None


class UpdateAppointmentOutput(BaseModel):
    """Result of ``update_appointment``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    appointment: AppointmentDetails | None = None


class GetAppointmentOutput(BaseModel):
    """Result of ``get_appointment``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    event: CalendarEventDetails | None = None


class CreateBlockSlotOutput(BaseModel):
    """Result of ``create_block_slot``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    block_slot: BlockSlotDetails | None = None


class UpdateBlockSlotOutput(BaseModel):
    """Result of ``update_block_slot``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    block_slot: BlockSlotDetails | None = None


class DeleteEventOutput(BaseModel):
    """Result of ``delete_event``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    deleted: bool | None = None


# --- Calendar groups --------------------------------------------------------


class ListCalendarGroupsOutput(BaseModel):
    """Result of ``list_calendar_groups``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    groups: list[CalendarGroupDetails] = Field(default_factory=list)


class CreateCalendarGroupOutput(BaseModel):
    """Result of ``create_calendar_group``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    group: CalendarGroupDetails | None = None


class ValidateCalendarGroupSlugOutput(BaseModel):
    """Result of ``validate_calendar_group_slug``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    available: bool | None = None


class DeleteCalendarGroupOutput(BaseModel):
    """Result of ``delete_calendar_group``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    deleted: bool | None = None


class UpdateCalendarGroupOutput(BaseModel):
    """Result of ``update_calendar_group``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    group: CalendarGroupDetails | None = None


class SetCalendarGroupStatusOutput(BaseModel):
    """Result of ``set_calendar_group_status``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    updated: bool | None = None


# --- Calendar resources (rooms / equipment) ---------------------------------


class ListCalendarResourcesOutput(BaseModel):
    """Result of ``list_calendar_resources``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    resources: list[CalendarResourceDetails] = Field(default_factory=list)


class CreateCalendarResourceOutput(BaseModel):
    """Result of ``create_calendar_resource``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    resource: CalendarResourceDetails | None = None


class GetCalendarResourceOutput(BaseModel):
    """Result of ``get_calendar_resource``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    resource: CalendarResourceDetails | None = None


class UpdateCalendarResourceOutput(BaseModel):
    """Result of ``update_calendar_resource``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    resource: CalendarResourceDetails | None = None


class DeleteCalendarResourceOutput(BaseModel):
    """Result of ``delete_calendar_resource``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    deleted: bool | None = None


# --- Availability schedules -------------------------------------------------


class CreateAvailabilityScheduleOutput(BaseModel):
    """Result of ``create_availability_schedule``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    schedule: AvailabilityScheduleDetails | None = None


class ListAvailabilitySchedulesOutput(BaseModel):
    """Result of ``list_availability_schedules``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    schedules: list[AvailabilityScheduleDetails] = Field(default_factory=list)


class GetAvailabilityScheduleOutput(BaseModel):
    """Result of ``get_availability_schedule``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    schedule: AvailabilityScheduleDetails | None = None


class UpdateAvailabilityScheduleOutput(BaseModel):
    """Result of ``update_availability_schedule``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    schedule: AvailabilityScheduleDetails | None = None


class DeleteAvailabilityScheduleOutput(BaseModel):
    """Result of ``delete_availability_schedule``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    deleted: bool | None = None


class AttachScheduleToCalendarOutput(BaseModel):
    """Result of ``attach_schedule_to_calendar``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    attached: bool | None = None


class DetachScheduleFromCalendarOutput(BaseModel):
    """Result of ``detach_schedule_from_calendar``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    detached: bool | None = None


# --- Calendar notifications -------------------------------------------------


class ListCalendarNotificationsOutput(BaseModel):
    """Result of ``list_calendar_notifications``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    notifications: list[CalendarNotificationDetails] = Field(default_factory=list)


class CreateCalendarNotificationOutput(BaseModel):
    """Result of ``create_calendar_notification``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    notifications: list[CalendarNotificationDetails] = Field(default_factory=list)


class GetCalendarNotificationOutput(BaseModel):
    """Result of ``get_calendar_notification``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    notification: CalendarNotificationDetails | None = None


class UpdateCalendarNotificationOutput(BaseModel):
    """Result of ``update_calendar_notification``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    message: str | None = None


class DeleteCalendarNotificationOutput(BaseModel):
    """Result of ``delete_calendar_notification``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    message: str | None = None

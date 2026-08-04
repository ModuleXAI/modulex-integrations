# GoHighLevel

Run a GoHighLevel sub-account from an agent — create and search contacts with
their notes, tasks and tags, move opportunities through pipelines, read and
send conversation messages across SMS, email and social channels, and manage
calendars, appointments, availability schedules and booking slots via the
GoHighLevel (LeadConnector) v2 API (`services.leadconnectorhq.com`).

## Authentication

### OAuth 2.0 (Marketplace app, sub-account token)

- Create an app in the [GoHighLevel Marketplace](https://marketplace.gohighlevel.com)
  with a **Sub-Account (Location)** distribution type, add your ModuleX
  callback to its Redirect URLs, and select every scope this integration
  requests — the connect flow fails if the app grants fewer scopes than it
  asks for
  ([docs](https://highlevel.stoplight.io/docs/integrations/a04191c0fcf1e-authorization)).
- Env vars: `GOHIGHLEVEL_OAUTH2_CLIENT_ID`, `GOHIGHLEVEL_OAUTH2_CLIENT_SECRET`
  (both app-level), and `GOHIGHLEVEL_LOCATION_ID` (per credential).
- Authorize at
  `https://marketplace.gohighlevel.com/v2/oauth/chooselocation`; exchange at
  `https://services.leadconnectorhq.com/oauth/token` with the client
  credentials in the **form body** (not a Basic header) and
  `user_type=Location`.
- Access tokens are valid for roughly one day; refresh tokens last a year and
  rotate on each use.
- Every request carries `Authorization: Bearer <token>`,
  `Version: 2021-07-28` and `Accept: application/json`. The `Version` header
  is mandatory — v2 rejects requests without it.
- **`GOHIGHLEVEL_LOCATION_ID` is not optional.** Nearly every endpoint is
  scoped to one sub-account, so the location ID is stored on the credential
  and injected into `auth_data`; no action takes it as a parameter. Find it
  under **Settings → Business Profile**, or read the `locationId` the token
  exchange returns.
- The credential is validated by reading a single contact from the configured
  sub-account, which proves the token and the location ID work together.

## Tools

### Contacts, notes, tasks and tags

| name | description | required params |
| --- | --- | --- |
| `create_contact` | Create a new contact in the connected GoHighLevel sub-account. | — |
| `list_contacts` | List contacts in the connected GoHighLevel sub-account. | — |
| `bulk_update_contacts_business` | Add or remove many contacts from a business in one bulk call. | `contact_ids` |
| `bulk_update_contact_tags` | Add or remove tags across many contacts at once. | `operation`, `contact_ids`, `tags` |
| `list_business_contacts` | List the contacts that belong to a specific business. | `business_id` |
| `search_contacts` | Search contacts using advanced filters, sorting and deep pagination. | — |
| `get_duplicate_contact` | Find an existing duplicate contact by email or phone before creating one. | — |
| `upsert_contact` | Create a contact, or update the matching duplicate if one already exists. | — |
| `get_contact` | Retrieve the full details of a single contact by its id. | `contact_id` |
| `update_contact` | Update the fields of an existing contact. | `contact_id` |
| `delete_contact` | Permanently delete a contact from the sub-account. | `contact_id` |
| `list_contact_appointments` | List every calendar appointment booked for a contact. | `contact_id` |
| `remove_contact_from_every_campaign` | Unenroll a contact from every campaign it is currently enrolled in. | `contact_id` |
| `add_contact_to_campaign` | Enroll a contact into a campaign. | `contact_id`, `campaign_id` |
| `remove_contact_from_campaign` | Unenroll a contact from one specific campaign. | `contact_id`, `campaign_id` |
| `add_contact_followers` | Add one or more users as followers of a contact. | `contact_id`, `followers` |
| `remove_contact_followers` | Remove one or more users from a contact's followers. | `contact_id`, `followers` |
| `list_contact_notes` | List every note attached to a contact. | `contact_id` |
| `create_contact_note` | Attach a new note to a contact. | `contact_id`, `body` |
| `get_contact_note` | Retrieve a single note attached to a contact. | `contact_id`, `note_id` |
| `update_contact_note` | Update the content or metadata of a note attached to a contact. | `contact_id`, `note_id` |
| `delete_contact_note` | Delete a note attached to a contact. | `contact_id`, `note_id` |
| `add_contact_tags` | Add one or more tags to a contact. | `contact_id`, `tags` |
| `remove_contact_tags` | Remove one or more tags from a contact. | `contact_id`, `tags` |
| `list_contact_tasks` | List every task attached to a contact. | `contact_id` |
| `create_contact_task` | Create a task on a contact, such as a follow-up or reminder. | `contact_id`, `title`, `due_date` |
| `get_contact_task` | Retrieve a single task attached to a contact. | `contact_id`, `task_id` |
| `update_contact_task` | Update the fields of a task attached to a contact. | `contact_id`, `task_id` |
| `delete_contact_task` | Delete a task attached to a contact. | `contact_id`, `task_id` |
| `complete_contact_task` | Mark a contact's task as completed or reopen it. | `contact_id`, `task_id` |
| `add_contact_to_workflow` | Add a contact to a workflow, optionally scheduling when it starts. | `contact_id`, `workflow_id` |
| `delete_contact_from_workflow` | Remove a contact from a workflow. | `contact_id`, `workflow_id` |

### Opportunities and pipelines

| name | description | required params |
| --- | --- | --- |
| `create_opportunity` | Create an opportunity in a pipeline for a contact. | `pipeline_id`, `name`, `status`, `contact_id` |
| `list_opportunity_lost_reasons` | List the opportunity lost reasons configured for the sub-account. | — |
| `list_pipelines` | List the opportunity pipelines and their stages for the sub-account. | — |
| `search_opportunities` | Search opportunities by pipeline, stage, contact, assignee, status or date. | — |
| `search_opportunities_advanced` | Search opportunities and optionally pull their notes, tasks and events. | — |
| `upsert_opportunity` | Create an opportunity, or update it when an opportunity id is supplied. | `pipeline_id` |
| `get_opportunity` | Retrieve a single opportunity by its id. | `opportunity_id` |
| `delete_opportunity` | Permanently delete an opportunity. | `opportunity_id` |
| `update_opportunity` | Update an opportunity's name, pipeline, stage, value or assignee. | `opportunity_id` |
| `add_opportunity_followers` | Add one or more users as followers of an opportunity. | `opportunity_id`, `followers` |
| `remove_opportunity_followers` | Remove one or more users from an opportunity's followers. | `opportunity_id`, `followers` |
| `update_opportunity_status` | Move an opportunity to open, won, lost or abandoned. | `opportunity_id`, `status` |

### Conversations and messages

| name | description | required params |
| --- | --- | --- |
| `create_conversation` | Start a new conversation thread between the sub-account and a contact. | `contact_id` |
| `get_message_transcription` | Get the call-recording transcription for a message, returned as one entry per transcribed sentence with timings and confidence. | `message_id` |
| `send_message` | Send an outbound message to a contact over SMS, RCS, email, WhatsApp, Instagram, Facebook, live chat or a custom provider. Email-only fields (subject, html, email_cc, email_bcc, email_reply_mode) and phone-only fields (from_number, to_number) are ignored on other channels. Supply scheduled_timestamp to schedule the send instead of delivering immediately. | `message_type`, `contact_id` |
| `cancel_scheduled_email_message` | Cancel a scheduled email message so it is never delivered. This cannot be undone. | `email_message_id` |
| `get_email_by_id` | Get one email message with its subject, body, sender, recipients, attachments and delivery status. | `email_message_id` |
| `export_messages` | Export the sub-account's messages page by page using a cursor, optionally filtered by conversation, contact, channel and date range. | — |
| `add_inbound_message` | Record a message received from a contact into a conversation, for example an SMS, email or WhatsApp message handled by an external provider. Supply either conversation_id or contact_id. | `message_type` |
| `add_outbound_message` | Record an outbound call that was placed outside GoHighLevel against an existing conversation, including its recording URL. | `conversation_id`, `conversation_provider_id` |
| `send_review_reply` | Reply to a Google My Business customer review through its review conversation. | `conversation_id`, `message` |
| `complete_message_file_upload` | Finalize a message file upload and return the file's public URL. Call this only after the file bytes have been PUT to the signed URL returned by initiate_message_file_upload. | `upload_id`, `file_path`, `conversation_id`, `filename` |
| `initiate_message_file_upload` | Request a signed Google Cloud Storage URL for a message attachment. The URL is valid for 15 minutes; the caller PUTs the file bytes to it themselves and then calls complete_message_file_upload. | `conversation_id`, `filename`, `content_type`, `channel` |
| `get_message` | Get one conversation message by ID, with its body, direction, status, attachments and channel metadata. | `message_id` |
| `add_message_attachments` | Replace the attachment URLs on an existing call message. Only supported for TYPE_CUSTOM_CALL and for TYPE_CALL with the EXTERNAL_CALL subtype. Maximum 5 URLs. | `message_id`, `attachments` |
| `cancel_scheduled_message` | Cancel a scheduled message so it is never delivered. This cannot be undone. | `message_id` |
| `update_message_status` | Update the delivery status of a message sent through a conversation provider, optionally attaching the provider's error. | `message_id`, `status` |
| `list_custom_subtypes` | List the sub-account's custom message subtypes, which drive granular email subscription preferences. | — |
| `create_custom_subtype` | Create a custom message subtype contacts can subscribe to. Requires an agency or account admin role. | `name`, `channel`, `language` |
| `update_custom_subtype` | Rename or archive a custom message subtype. Requires an agency or account admin role. | `custom_subtype_id` |
| `get_contact_unsubscription_status` | Read a contact's email subscription and unsubscribe statuses, for one address or for every address on the contact. | `contact_id` |
| `update_subscription_preference` | Subscribe or unsubscribe a contact's email address on behalf of an agent, for a default subscription type, a custom subtype, or all types at once. | `contact_id`, `email`, `subscription_type`, `subscription_status` |
| `live_chat_agent_typing` | Show or hide the agent typing indicator that a live-chat visitor sees while a reply is being written. | `conversation_id`, `visitor_id`, `is_typing` |
| `search_conversations` | Search the sub-account's conversations by free text, contact, assignee, follower, last-message characteristics, score profile or date, with sorting and paging. | — |
| `get_conversation` | Get one conversation with its contact, assignee, unread count and inbox, starred and deleted flags. | `conversation_id` |
| `update_conversation` | Star a conversation, change its unread count, or attach a feedback object to it. | `conversation_id` |
| `delete_conversation` | Delete a conversation and its messages. This cannot be undone. | `conversation_id` |
| `list_conversation_messages` | List the messages in a conversation, optionally restricted to certain message types, with cursor paging via last_message_id. | `conversation_id` |

### Email templates and campaigns

| name | description | required params |
| --- | --- | --- |
| `list_campaigns` | List the marketing campaigns configured in the GoHighLevel sub-account, optionally filtered by status. | — |
| `create_email_template` | Create an email-builder template or template folder in the sub-account, optionally importing it from Mailchimp, ActiveCampaign or Kajabi. | `template_type` |
| `list_email_templates` | List the email-builder templates and folders in the sub-account, with search, folder and archive filters. | — |
| `update_email_template` | Save new content onto an existing email-builder template, replacing its drag-and-drop document and HTML body. | `template_id`, `updated_by`, `html`, `editor_type`, `dnd` |
| `delete_email_template` | Permanently delete an email-builder template. This cannot be undone. | `template_id` |
| `list_scheduled_emails` | List the sub-account's scheduled email campaigns with their schedule status, delivery status and optional send statistics. | — |

### Calendars, appointments and schedules

| name | description | required params |
| --- | --- | --- |
| `list_calendars` | List every booking calendar in the connected GoHighLevel sub-account, optionally filtered by calendar group. | — |
| `create_calendar` | Create a booking calendar (round robin, event, class, collective, service or personal) in the connected GoHighLevel sub-account. | `name` |
| `list_appointment_notes` | List the notes attached to a GoHighLevel appointment. | `appointment_id`, `limit`, `offset` |
| `create_appointment_note` | Attach a free-form note to a GoHighLevel appointment. | `appointment_id`, `body` |
| `update_appointment_note` | Update the body of a note attached to a GoHighLevel appointment. | `appointment_id`, `note_id`, `body` |
| `delete_appointment_note` | Permanently delete a note from a GoHighLevel appointment. | `appointment_id`, `note_id` |
| `list_blocked_slots` | List blocked (unbookable) slots in a time range for the connected GoHighLevel sub-account. | `start_time`, `end_time` |
| `list_calendar_events` | List calendar events (appointments) in a time range for the connected GoHighLevel sub-account. | `start_time`, `end_time` |
| `create_appointment` | Book a contact onto a GoHighLevel calendar as a new appointment. | `calendar_id`, `contact_id`, `start_time` |
| `update_appointment` | Update an existing GoHighLevel appointment — time, status, location or assignment. Only the fields supplied are changed. | `event_id` |
| `get_appointment` | Fetch one GoHighLevel appointment by its event ID. | `event_id` |
| `create_block_slot` | Reserve time on a GoHighLevel calendar or user so it is unavailable for booking. | — |
| `update_block_slot` | Update the time, title or owner of a GoHighLevel block slot. | `event_id` |
| `delete_event` | Delete a GoHighLevel calendar event — an appointment or a block slot. | `event_id` |
| `list_calendar_groups` | List every calendar group in the connected GoHighLevel sub-account. | — |
| `create_calendar_group` | Create a calendar group that organises related calendars under a shared name and slug. | `name`, `description`, `slug` |
| `validate_calendar_group_slug` | Check whether a calendar group slug is still available in the sub-account before creating or renaming a group. | `slug` |
| `delete_calendar_group` | Permanently delete a GoHighLevel calendar group. | `group_id` |
| `update_calendar_group` | Rename a GoHighLevel calendar group or change its description and slug. | `group_id`, `name`, `description`, `slug` |
| `set_calendar_group_status` | Enable or disable a GoHighLevel calendar group. | `group_id`, `is_active` |
| `list_calendar_resources` | List the bookable rooms or equipment available for service calendars in the connected GoHighLevel sub-account. | `resource_type`, `limit`, `skip` |
| `create_calendar_resource` | Create a bookable room or piece of equipment for service calendars. | `resource_type`, `name`, `description`, `quantity`, `out_of_service`, `capacity`, `calendar_ids` |
| `get_calendar_resource` | Fetch one bookable room or piece of equipment by its ID. | `resource_type`, `resource_id` |
| `update_calendar_resource` | Update a bookable room or piece of equipment. Only the fields supplied are changed. | `resource_type`, `resource_id` |
| `delete_calendar_resource` | Permanently delete a bookable room or piece of equipment. | `resource_type`, `resource_id` |
| `create_availability_schedule` | Create a user availability schedule — the working hours and date rules GoHighLevel calendars book against. | `name`, `user_id`, `timezone` |
| `list_availability_schedules` | List the availability schedules configured for a GoHighLevel user. | `user_id` |
| `get_availability_schedule` | Fetch one GoHighLevel user availability schedule by its ID. | `schedule_id` |
| `update_availability_schedule` | Update a user availability schedule's name, timezone or rules. Only the fields supplied are changed. | `schedule_id` |
| `delete_availability_schedule` | Permanently delete a GoHighLevel user availability schedule. | `schedule_id` |
| `attach_schedule_to_calendar` | Apply a user availability schedule to a GoHighLevel team calendar. | `schedule_id`, `calendar_id` |
| `detach_schedule_from_calendar` | Remove a user availability schedule from a GoHighLevel calendar. | `schedule_id`, `calendar_id` |
| `update_calendar` | Update a GoHighLevel booking calendar's settings, availability or team members. Only the fields supplied are changed. | `calendar_id` |
| `get_calendar` | Fetch the full configuration of one GoHighLevel booking calendar. | `calendar_id` |
| `delete_calendar` | Permanently delete a GoHighLevel booking calendar. | `calendar_id` |
| `get_calendar_free_slots` | Find the bookable free slots on a GoHighLevel calendar within a date range, grouped by day. | `calendar_id`, `start_date`, `end_date` |
| `list_calendar_notifications` | List the notification rules configured on a GoHighLevel calendar. | `calendar_id` |
| `create_calendar_notification` | Create one or more notification rules on a GoHighLevel calendar — booking confirmations, reminders or follow-ups across email, SMS, in-app and WhatsApp. | `calendar_id`, `notifications` |
| `get_calendar_notification` | Fetch one notification rule from a GoHighLevel calendar. | `calendar_id`, `notification_id` |
| `update_calendar_notification` | Update one notification rule on a GoHighLevel calendar. Only the fields supplied are changed. | `calendar_id`, `notification_id` |
| `delete_calendar_notification` | Permanently delete a notification rule from a GoHighLevel calendar. | `calendar_id`, `notification_id` |

Every tool additionally takes `auth_type` and `auth_data`, which the runtime
fills in from the resolved credential.

Start from `list_contacts` or `search_contacts` to find contact IDs, then use
the contact-scoped note, task and tag actions. For sales work, `list_pipelines`
first — an opportunity cannot be created or moved without a pipeline stage ID.
For scheduling, `list_calendars` then `get_calendar_free_slots` before
`create_appointment`.

## Limits & Quotas

- **Rate limits** (per Marketplace app, per sub-account): a burst limit of 100
  requests per 10 seconds and a daily limit of 200 000 requests. Responses
  carry `X-RateLimit-Limit-Daily`, `X-RateLimit-Daily-Remaining`,
  `X-RateLimit-Max`, `X-RateLimit-Remaining` and
  `X-RateLimit-Interval-Milliseconds`.
- **Scopes are enforced per endpoint.** A token whose app was configured
  without, say, `calendars/groups.write` gets a 401 on the calendar-group
  actions even though the connection succeeded. If a subset of actions fails
  with an authorization error, check the app's scope selection first.
- **Sub-account only.** Agency-level surfaces (SaaS reseller, affiliate
  manager, snapshots, company settings) need a `user_type=Company` token and
  are deliberately out of scope here.
- **Binary payloads are out of scope.** Uploading a file attachment
  (`multipart/form-data`), downloading a call recording (`audio/x-wav`) and
  downloading a transcription file (`text/plain`) cannot be represented as a
  JSON tool result. `get_message_transcription` returns the same transcription
  data as JSON, and `initiate_message_file_upload` /
  `complete_message_file_upload` hand out a signed URL so the caller can do
  the binary transfer itself.
- **Paging** differs by endpoint family: contacts and conversations search use
  cursor-style continuation, while most list endpoints take `limit`/`offset`
  or `page`. Read each action's parameters rather than assuming one scheme.
- **Error model**: transport failures, non-2xx responses and unparseable
  bodies all fold into `success=False` + `error` rather than raising. The
  error string carries GoHighLevel's `message` and its `traceId` where
  present — quote the trace ID when contacting support.

## Maintainer

ModuleX core team.

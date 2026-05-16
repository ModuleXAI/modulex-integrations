# Mailchimp

Mailchimp marketing platform integration via the v3.0 REST API. Pure
HTTP. 19 actions across lists, subscribers, campaigns, tags, notes,
and segments.

## Authentication

- **`api_key` auth_type.** The Mailchimp API key embeds the
  datacenter as a suffix (e.g. `xxx-us10`); we extract it to route
  requests to `https://{dc}.api.mailchimp.com/3.0`.
- Env var: `MAILCHIMP_API_KEY` (sensitive).
- **Basic Auth** with literal `anystring` username + API key
  password — Mailchimp's documented pattern.

## Runtime convention

Key-based: every `@tool` accepts `(api_key, ...)`.

## Tools

| group | tools |
| --- | --- |
| Lists | `get_lists`, `get_list`, `create_list`, `delete_list` |
| Subscribers | `get_list_members`, `get_subscriber`, `add_or_update_subscriber`, `delete_subscriber` |
| Campaigns | `get_campaigns`, `get_campaign`, `create_campaign`, `delete_campaign`, `send_campaign`, `get_campaign_report` |
| Tags | `get_member_tags`, `update_member_tags` |
| Notes | `add_note_to_subscriber` |
| Segments | `get_segments`, `add_member_to_segment` |

## Notes

- **Subscribers addressed by MD5 hash** of the lowercase email —
  see `_subscriber_hash`. Applies to get/upsert/delete/tags/notes.
- **`add_or_update_subscriber`** is a 2-call workflow when tags are
  provided: PUT the subscriber (success codes 200 or 201), then POST
  tags. The tag POST is fire-and-forget like legacy.
- **`delete_subscriber`** uses the permanent-delete action path:
  `/members/{md5}/actions/delete-permanent` (matches legacy — the
  non-permanent DELETE leaves a tombstone).
- 30s timeout on every request.
- All actions wrap in try/except → `success=False` envelope.

## Maintainer

ModuleX core team.

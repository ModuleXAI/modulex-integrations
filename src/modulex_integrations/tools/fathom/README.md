# Fathom

Access Fathom AI Notetaker meeting data — recorded meetings with their
summaries, transcripts, action items, highlights, and CRM matches, plus
meeting types, teams, and team members — through the Fathom External
API (`api.fathom.ai/external/v1`).

## Authentication

### API Key

- Sign in at <https://fathom.video>, open **User Settings → API
  Access** (<https://fathom.video/customize#api-access-header>) and
  generate a key.
- Required env var: `FATHOM_API_KEY`.
- Sent on every request as the `X-Api-Key` header.
- The credential is validated by listing the organization's teams
  (`GET /external/v1/teams`).
- Keys are scoped to the user who created them: they reach only the
  meetings that user recorded or that were shared with them or their
  team, never another user's private meetings.

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_meetings` | List recent meetings with optional date / recorder / team / meeting-type / invitee-domain filters and optional summary, transcript, action-item, highlight, and CRM blocks | none |
| `list_meeting_types` | List the organization's meeting types (active and inactive) | none |
| `get_summary` | Get the markdown-formatted call summary for one recording | `recording_id` |
| `get_transcript` | Get the full transcript for one recording, with speakers and timestamps | `recording_id` |
| `list_team_members` | List team members, optionally filtered by team name | none |
| `list_teams` | List teams in the organization | none |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential (the modulex `api_key` injection
convention).

## Limits & Quotas

- **Global rate limit**: 60 requests per 60-second window per account.
  Responses carry `RateLimit-Limit`, `RateLimit-Remaining`, and
  `RateLimit-Reset`.
- **Heavy endpoints**: `get_summary`, `get_transcript`, and
  `list_meetings` with `include_summary` / `include_transcript` are
  capped at 30 requests per 60 seconds, and may drop to 5 during
  high-activity periods. On `429`, wait at least `Retry-After` seconds.
- **Pagination**: the list actions are cursor-based. Each call is a
  single request — pass the returned `next_cursor` back in as `cursor`
  to walk further pages. `get_transcript` is not paginated and returns
  the whole transcript at once.
- **Optional blocks**: `transcript`, `action_items`, `highlights`,
  `default_summary`, and `crm_matches` come back as `null` on a meeting
  unless the matching `include_*` flag was set. `crm_matches.error` is
  populated when no CRM is connected to the workspace.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.

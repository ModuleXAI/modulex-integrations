# Fireflies

Work with Fireflies.ai meeting recordings — search and read transcripts with
their summaries, action items and speaker analytics, upload audio for
transcription, send the notetaker bot into a live meeting, clip soundbites,
and look up team users and meeting contacts via the Fireflies GraphQL API
(`api.fireflies.ai/graphql`).

## Authentication

### API Key (bearer token)

- Sign in at <https://app.fireflies.ai>, open **Settings → Integrations** and
  find the **Fireflies API** section
  (<https://app.fireflies.ai/integrations/custom/fireflies>), then click
  *Generate New API Key*
  ([docs](https://docs.fireflies.ai/fundamentals/authorization)).
- Env var: `FIREFLIES_API_KEY` — the Fireflies API key.
- Sent on every request as `Authorization: Bearer <key>`.
- A key acts as its owner: it reaches that user's meetings and the team data
  the user can see. Deleting another team member's meeting requires team
  admin rights.
- The credential is validated by reading the key owner's profile
  (`query { user { user_id } }`).

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_transcripts` | List meetings, filtered by keyword, date range, host, or participant | — |
| `get_transcript` | Get one transcript in full: sentences, summary, action items, analytics | `transcript_id` |
| `get_user` | Get a user's profile and usage (defaults to the API key owner) | — |
| `list_users` | List team users with transcript counts and minutes consumed | — |
| `upload_audio` | Submit a public audio/video URL for transcription | `audio_url` |
| `delete_transcript` | Delete a transcript and return what was removed | `transcript_id` |
| `add_to_live_meeting` | Send the notetaker bot into an ongoing meeting | `meeting_link` |
| `create_bite` | Clip a soundbite from a time range of a transcript | `transcript_id`, `start_time`, `end_time` |
| `list_bites` | List soundbites, optionally for one transcript | — |
| `list_contacts` | List people you have met with and the last meeting date | — |

Every tool takes an additional `api_key` parameter that the runtime fills in
from the resolved credential.

Start from `list_transcripts` to discover transcript IDs, then use
`get_transcript` for the full text, summary, and analytics of one meeting.

## Limits & Quotas

- The API is a single GraphQL endpoint (`POST https://api.fireflies.ai/graphql`)
  and answers **HTTP 200 for failures too**: check the `errors` array, not the
  status code. These tools fold transport failures, non-200 responses, and
  GraphQL errors into `success=false` + `error`.
- **Account rate limits**: 50 requests/day on Free, 500 requests/day on Pro,
  60 requests/minute on Business and Enterprise.
- **`add_to_live_meeting`** is additionally capped at 3 requests per 20
  minutes; exceeding it returns a `too_many_requests` error. `duration` is
  clamped to 15–120 minutes, `title` to 256 characters, `meeting_password` to
  32, and `language` to a 5-character code.
- **`delete_transcript`** is capped at 10 requests per minute.
- **`upload_audio`** takes a public `https://` URL only — Fireflies downloads
  the media itself, so the URL must stay reachable. Supported formats are mp3,
  mp4, wav, m4a and ogg; files must be at least 50 KB, and uploading requires
  a Pro plan or higher.
- **Paging**: `list_transcripts` and `list_bites` are offset-based — `limit`
  is capped at 50 per call, so walk further pages by increasing `skip`.
- **`create_bite`** clips asynchronously: the new soundbite comes back with
  status `pending`, and `list_bites` reflects the finished clip once
  processing completes. `name` is capped at 256 characters and `summary` at
  500.
- Error model: non-200 responses, timeouts, and GraphQL errors are caught and
  returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.

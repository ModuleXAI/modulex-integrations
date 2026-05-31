# HeyGen

AI video generation platform for creating talking avatar videos via the HeyGen REST API (`api.heygen.com`).

## Authentication

### API Key Authentication

- Sign in at <https://app.heygen.com>, go to **Settings > API**, and copy your API key.
- Required env var: `HEYGEN_API_KEY` (format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_talking_photo` | Creates a talking photo video from a provided image, text, and voice | `talking_photo_id`, `text`, `voice_id` |
| `create_video_from_template` | Generates a video from a selected template with optional variable overrides | `template_id` |
| `list_custom_events_options` | Retrieves available options for webhook custom events | |
| `list_voice_id_options` | Retrieves available voice options for video generation | |
| `retrieve_video_link` | Fetches the status and download link for a specific HeyGen video | `video_id` |

Every tool takes an additional `api_key` parameter that the runtime fills in from the resolved credential.

## Limits & Quotas

- Rate limits depend on your HeyGen plan tier (Starter, Business, Enterprise).
- Video generation consumes credits; use `test=true` to avoid credit charges during development.
- No documented per-minute rate limit; excessive requests may trigger throttling.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.

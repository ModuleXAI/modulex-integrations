# YouTube

Search videos, inspect channels and playlists, read trending videos and
video categories, and fetch public comments against the YouTube Data API
v3 (`www.googleapis.com/youtube/v3`).

## Authentication

API key authentication. The key is a public Data-API key sent as a
`key=` query parameter on every request (not an `Authorization` header).
The credential test lists US video categories with a minimal request.

### API Key

- In the [Google Cloud Console](https://console.cloud.google.com),
  create or select a project.
- Under **APIs & Services > Library**, enable the **YouTube Data API
  v3**.
- Under **APIs & Services > Credentials**, create an API key, restrict
  it to the YouTube Data API v3, and copy it.
- Required env var: `YOUTUBE_API_KEY` (format:
  `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`). See the
  [getting-started guide](https://developers.google.com/youtube/v3/getting-started).

## Tools

| name | description | required params |
| --- | --- | --- |
| `search` | Search videos with channel/date/duration/quality/caption/live filters | `query` |
| `trending` | Most popular videos, filterable by region and category | — |
| `video_details` | Full metadata, statistics, and live-stream info for a video | `video_id` |
| `video_categories` | List valid category IDs for a region | — |
| `channel_info` | Channel statistics, branding, and uploads playlist ID | — |
| `channel_videos` | Recent videos from a channel with sort order | `channel_id` |
| `channel_playlists` | Public playlists owned by a channel | `channel_id` |
| `playlist_items` | Videos contained in a playlist | `playlist_id` |
| `comments` | Top-level comments on a video with author and engagement | `video_id` |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential.

## Limits & Quotas

- **Quota model**: the YouTube Data API allocates a daily quota (10,000
  units by default per project). `search` costs ~100 units per call;
  most read endpoints cost ~1 unit. Plan calls accordingly.
- **Result caps**: list endpoints accept `max_results` up to 50 (up to
  100 for `comments`). Use `page_token` / `next_page_token` to paginate.
- **Error model**: the API returns HTTP 200 with an `{"error": {...}}`
  envelope on failure; these (and non-2xx responses and timeouts) are
  caught and returned as `success=False` + `error` rather than raising.
  Plan for retries on the agent side based on the error string.

## Maintainer

ModuleX core team.

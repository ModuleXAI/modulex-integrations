# Google Maps Platform

Search for places and retrieve place details using the Google Places API (New)
(`places.googleapis.com`).

## Authentication

### Google Maps API Key

- Go to [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials)
  and create or select a project.
- Enable the **Places API (New)** for your project.
- Create an API key or use an existing one.
- Required env var: `GOOGLE_MAPS_PLATFORM_API_KEY`
  (format: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`).

## Tools

| name | description | required params |
| --- | --- | --- |
| `search_places` | Search for places based on a text query with optional filters like type, rating, price level, and location bias or restriction | `text_query` |
| `get_place_details` | Retrieve detailed information for a specific place using its Place ID | `place_id` |

Every tool takes an additional `api_key` parameter that the runtime fills in
from the resolved credential.

## Limits & Quotas

- **Text Search**: $32.00 per 1,000 requests (standard SKU pricing).
- **Place Details**: $17.00 per 1,000 requests (standard SKU pricing).
- **Default quota**: 6,000 QPM (queries per minute) per project; can be
  increased via Google Cloud Console.
- **Error model**: non-2xx responses and timeouts are caught and returned as
  `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.

# Google Slides

Create and edit Google Slides presentations from agents — manage slides, shapes, images, tables, and text via the Google Slides REST API (`slides.googleapis.com/v1`), with presentation duplication and discovery powered by the Google Drive REST API (`www.googleapis.com/drive/v3`).

## Authentication

This integration supports a single auth method. Token validation hits Drive `GET /about?fields=user`.

### OAuth2 Authentication

- Create an OAuth 2.0 Client ID in the [Google Cloud Console Credentials page](https://console.cloud.google.com/apis/credentials).
- Register `https://api.modulex.dev/credentials/oauth2/callback` as an authorized redirect URI on the OAuth client.
- Enable the Google Slides API and Google Drive API on the same Google Cloud project (APIs & Services -> Library).
- Required env vars: `GOOGLE_SLIDES_OAUTH2_CLIENT_ID`, `GOOGLE_SLIDES_OAUTH2_CLIENT_SECRET`.
- Scopes requested:
  - `https://www.googleapis.com/auth/presentations` (read/write Slides)
  - `https://www.googleapis.com/auth/drive` (copy template files, look up file metadata)

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_image` | Insert an image (by URL) onto a slide in a presentation. | `presentation_id`, `slide_id`, `url`, `height`, `width` |
| `create_page_element` | Insert a new shape page element (text box, rectangle, ellipse, arrow, etc.) onto a slide. | `presentation_id`, `slide_id`, `type`, `height`, `width` |
| `create_presentation` | Create a blank Google Slides presentation, or duplicate an existing one when `source_presentation_id` is supplied. | `title` |
| `create_slide` | Create a new slide in a presentation, optionally based on a specific layout. | `presentation_id`, `layout_id` |
| `create_table` | Create a new table on a slide with the given rows and columns. | `presentation_id`, `slide_id`, `rows`, `columns`, `height`, `width` |
| `delete_page_element` | Delete a page element (shape, image, table, etc.) from a slide. | `presentation_id`, `page_element_id` |
| `delete_slide` | Delete a slide from a presentation. | `presentation_id`, `slide_id` |
| `delete_table_column` | Delete a single column from an existing table on a slide. | `presentation_id`, `table_id`, `column_index` |
| `delete_table_row` | Delete a single row from an existing table on a slide. | `presentation_id`, `table_id`, `row_index` |
| `find_presentation` | Fetch full metadata about a Google Slides presentation (slides, layouts, masters). | `presentation_id` |
| `insert_table_columns` | Insert new columns into an existing table on a slide (max 20 per request). | `presentation_id`, `table_id` |
| `insert_table_rows` | Insert new rows into an existing table on a slide (max 20 per request). | `presentation_id`, `table_id` |
| `insert_text` | Insert text into a shape (typically a `TEXT_BOX`) on a slide. | `presentation_id`, `shape_id`, `text` |
| `insert_text_into_table` | Insert text into a specific cell of a table on a slide. | `presentation_id`, `table_id`, `text` |
| `merge_data` | Duplicate a template presentation and merge data into it by replacing placeholders with text and/or images. | `source_presentation_id`, `title`, `placeholders_and_texts` |
| `refresh_chart` | Refresh every embedded Sheets chart in a presentation. | `presentation_id` |
| `replace_all_text` | Replace every occurrence of a given text snippet inside a presentation, optionally restricted to specific slide pages. | `presentation_id`, `text`, `replace_text` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- **Per-project quotas**: Google Slides API and Google Drive API default to a few hundred read or write requests per 100 seconds per project; per-user limits also apply (see the [Slides API quotas page](https://developers.google.com/workspace/slides/api/limits)). Quotas are managed in the Google Cloud Console (APIs & Services -> Quotas).
- **batchUpdate body**: Slides `batchUpdate` requests should stay under ~10 MB; for very large merges, batch the work into multiple calls.
- **Insert table rows/columns**: capped at 20 per single request, per Google's documented `InsertTableRowsRequest` / `InsertTableColumnsRequest` limits.
- **Error model**: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising. Plan for retries on the agent side based on the error string. OAuth tokens that have expired surface as HTTP 401 in the `error` field.

## Maintainer

ModuleX core team.

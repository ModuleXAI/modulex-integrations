# Google Drive (+ Docs / Sheets / Slides)

Google Workspace integration via the v3 (Drive) / v1 (Docs, Slides) /
v4 (Sheets) REST APIs. Pure HTTP, no SDK dep. 16 actions.

## Authentication

- **Paired `oauth2 + bearer_token` schemas.** OAuth requests four
  scopes covering Drive (app-created files) + Docs + Sheets + Slides:
  `drive.file`, `documents`, `spreadsheets`, `presentations`. The
  broad `drive` scope was dropped — access is now limited to files
  the app creates or that the user explicitly opens.
- OAuth env vars: `GOOGLE_DRIVE_OAUTH2_CLIENT_ID`,
  `GOOGLE_DRIVE_OAUTH2_CLIENT_SECRET` (both `only_for_custom`).
- Bearer env var: `GOOGLE_ACCESS_TOKEN`.
- Both `test_endpoint`s GET `/drive/v3/about?fields=user`.

## Runtime convention

Token-based: every `@tool` accepts `(auth_type, auth_data, ...)`.

## Tools

| group | tools |
| --- | --- |
| Drive — files | `create_text_file`, `update_text_file` |
| Drive — items | `create_folder` |
| Docs | `create_google_doc`, `read_google_doc`, `update_google_doc`, `append_to_google_doc` |
| Sheets | `create_google_sheet`, `read_google_sheet`, `update_google_sheet`, `format_sheet_cells`, `format_sheet_text` |
| Slides | `create_google_slides`, `read_google_slides`, `add_slide`, `update_slide_content` |

## Multi-call workflows (preserved verbatim)

- **`create_text_file`** — manual `multipart/related` upload to
  `/upload/drive/v3/files` (bypasses `_call` because of the custom
  Content-Type).
- **`update_text_file`** — media-upload PATCH for content + optional
  follow-up rename PATCH on the metadata endpoint.
- **`update_google_doc`** — 2 calls: GET to find end-index, then
  `batchUpdate` with `deleteContentRange` + `insertText`.
- **`append_to_google_doc`** — GET to find end-index, then
  `batchUpdate` with `insertText` at `end_index - 1`.
- **`read_google_sheet` / `update_google_sheet`** — first GET the
  spreadsheet to resolve localized sheet names (e.g. `Sayfa1` in
  Turkish), then call the values endpoint.
- **`format_sheet_cells` / `format_sheet_text`** — convert A1
  notation to `GridRange` for the Sheets batchUpdate API.

## Notes

- 30s timeout for metadata calls; 60s for upload / batchUpdate.
- All actions wrap in try/except → unified `success=False` envelope.
- `_a1_to_grid` parses A1 ranges like `Sheet1!A1:D10`, `A1:B5`, `A1`.

## Maintainer

ModuleX core team.

# ConvertAPI

File-format conversion (PDF, DOCX, JPG, etc.), base64 file conversion,
web-page-to-PDF rendering, and format-discovery against the ConvertAPI
v2 REST endpoints (`v2.convertapi.com`).

## Authentication

### API Key (query parameter)

- Required env var: `CONVERTAPI_API_KEY`.
- Sign up at <https://www.convertapi.com/a>, copy your Secret.
- Sent as `?Secret=<key>` on every request — not a header.

## Tools

| name | description | required params |
| --- | --- | --- |
| `convert_file` | URL → converted file | `file_url`, `format_from`, `format_to` |
| `convert_base64_file` | base64 bytes → converted file | `base64_string`, `format_from`, `format_to` |
| `convert_web_url` | render web page → PDF/JPG | `url` |
| `get_supported_formats` | list available targets for `format_from` | `format_from` |

## Limits & Quotas

- Conversions cost credits; `get_supported_formats` is free.
- Long-running conversions accept a per-call `timeout` (default 300s).
- Failures (non-200, empty `Files`, exceptions) surface as
  `success=False` with `error`.

## Maintainer

ModuleX core team.

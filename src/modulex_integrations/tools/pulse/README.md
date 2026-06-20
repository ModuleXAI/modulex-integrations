# Pulse

Extract text and structured content from PDFs, images, and Office
files using Pulse OCR, against the Pulse REST API
(`api.runpulse.com`).

## Authentication

One method supported — an API key sent as the `x-api-key` header on
every request.

### API Key

- Sign in at <https://www.runpulse.com>, open your dashboard, and
  generate or copy your API key.
- Required env var: `PULSE_API_KEY`.
- See <https://docs.runpulse.com/authentication> for details.

## Tools

| name | description | required params |
| --- | --- | --- |
| `parser` | Parse a document from a public URL and return markdown, page count, bounding boxes, chunks, and figures | `file_url` |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential. `parser` accepts optional
`pages` (1-indexed range), `chunking`, `chunk_size`, `return_html`,
`extract_figure`, and `figure_description` options.

## Limits & Quotas

- **Billing**: Pulse bills in credits; each extraction is billed by
  the number of pages (or tables) processed. API keys can carry
  per-key credit caps.
- **Large documents**: documents above ~70 pages return an
  `extraction_url` pointing at the full results instead of inlining
  the markdown.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.

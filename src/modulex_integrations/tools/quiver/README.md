# Quiver

AI-powered SVG generation and raster vectorization against the QuiverAI
REST API (`api.quiver.ai/v1`). Generate clean, scalable vector graphics
from text prompts or convert raster images into editable SVGs.

## Authentication

Authenticate with a single QuiverAI API key sent as
`Authorization: Bearer <key>`. The credential is validated against
`GET /v1/models`.

### API Key

- Sign in at <https://quiver.ai>, open your account dashboard and
  navigate to API keys, then create or copy your key.
- Required env var: `QUIVER_API_KEY`.
- See <https://docs.quiver.ai/getting-started/quickstart> for setup.

## Tools

| name | description | required params |
| --- | --- | --- |
| `text_to_svg` | Generate SVG images from a text prompt | `prompt` |
| `image_to_svg` | Vectorize a raster image (by URL) into an SVG | `image` |
| `list_models` | List available QuiverAI models | — |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential. `text_to_svg` and `image_to_svg`
return the raw SVG markup as `svg_content` (plus all generated
`artifacts` when `n > 1`); `references` and `image` are supplied as image
URLs.

## Limits & Quotas

- **Models**: `arrow-1.1` is the default; `arrow-1.1-max` offers higher
  fidelity for detailed images and supports more reference images.
- **Generation**: `n` of 1-16 outputs per request; `temperature` 0-2,
  `top_p` 0-1, `presence_penalty` -2 to 2, `max_output_tokens` up to
  65536.
- **Vectorization**: decoded images cannot exceed 4096 x 4096 px;
  `target_size` accepts 128-4096 px.
- **Billing**: each request reports a `credits` debit; `usage` token
  fields are retained for compatibility and may be zeroed.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.

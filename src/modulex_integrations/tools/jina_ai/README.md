# Jina AI

AI-powered search foundation tools against Jina AI's REST surfaces:
embeddings, rerank, web reader, web search, deep search, text
segmentation, and zero-shot classification.

Each capability lives on a different subdomain — the tool code routes
to the correct one per action.

## Authentication

### API Key (Bearer) — and ModuleX Managed Key

- Paired `api_key + modulex_key` schemas (same Bearer header).
- API-key env var: `JINA_API_KEY`. Get one free at
  <https://jina.ai/?sui=apikey>.
- Both schemas' `test_endpoint` POSTs a minimal embeddings request.

## Tools

| name | description | required params |
| --- | --- | --- |
| `generate_embeddings` | Text/image/PDF embeddings | `input` |
| `rerank_documents` | Cross-encoder re-ranking | `query`, `documents` |
| `read_webpage` | Web page → markdown/html/text | `url` |
| `web_search` | LLM-optimized web search | `query` |
| `deep_search` | Multi-step research with reasoning | `query` |
| `segment_text` | Tokenize + chunk text | `content` |
| `classify` | Zero-shot classification | `input`, `labels` |

## Limits & Quotas

- Per-endpoint subdomains:
  `api.jina.ai/v1/embeddings`, `api.jina.ai/v1/rerank`,
  `r.jina.ai/`, `s.jina.ai/`,
  `deepsearch.jina.ai/v1/chat/completions`,
  `segment.jina.ai/`, `api.jina.ai/v1/classify`.
- Reader and Search expect their configuration via `X-*` request
  headers (return format, target selectors, cache bypass, etc.) —
  preserved verbatim from the legacy implementation.
- Deep search timeout is 300s (the API genuinely takes that long for
  high-effort queries); reader/search use 120s; everything else uses
  60s.
- Standard plan rate limits (from the legacy JSON's `rate_limits`
  block): embeddings/rerank 500 RPM, reader 200 RPM, search 40 RPM,
  classify 20 RPM, segment 200 RPM. Premium is 4-10× higher.

## Maintainer

ModuleX core team.

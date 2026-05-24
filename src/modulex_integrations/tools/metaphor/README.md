# Metaphor

AI-powered web search, similarity matching, and document content retrieval via the Metaphor REST API (`api.metaphor.systems`).

## Authentication

### API Key Authentication

- Sign in at <https://dashboard.metaphor.systems> and navigate to the API Keys section.
- Required env var: `METAPHOR_API_KEY` (format: your API key string).
- The key is passed as the `x-api-key` header on every request.

## Tools

| name | description | required params |
| --- | --- | --- |
| `search` | Perform a search with a Metaphor prompt-engineered query and retrieve a list of relevant results | `query`, `use_autoprompt` |
| `find_similar_links` | Find similar links to the link provided | `url` |
| `get_documents_content` | Retrieve contents of documents based on a list of document IDs obtained from search or find_similar_links | `ids` |

Every tool takes an additional `api_key` parameter that the runtime fills in from the resolved credential.

## Limits & Quotas

- No publicly documented rate limits; usage is metered by plan tier.
- Basic plans support up to 30 results per search query; custom plans support thousands.
- Each document content retrieval costs 1 request per document.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.

# Tavily Search

AI-powered web search using the official [`langchain-tavily`](https://pypi.org/project/langchain-tavily/)
SDK. First SDK-based integration in the package — the @tools wrap
`TavilySearch` rather than calling Tavily's HTTP API directly.

## Authentication

Two methods supported.

### API Key (recommended)

- Sign in at <https://tavily.com>, generate or copy your key.
- Required env var: `TAVILY_API_KEY` (format: `tvly-xxxxxxxxxxxxxx...`).

### ModuleX Managed Key

Uses ModuleX's managed Tavily key with usage tracked against the
account's weekly credit limit. No env vars to configure.

## Tools

| name | description | required params |
| --- | --- | --- |
| `web_search` | Comprehensive web search with optional AI answer | `query` |
| `answer_search` | Web search + AI-generated answer with sources | `query` |
| `news_search` | Recent news articles search | `query` |

Each tool takes an additional `api_key` parameter the runtime fills
in (api_key / modulex_key convention — same as exa).

## Limits & Quotas

- Tavily's rate limit varies by plan; consult their dashboard.
- The SDK is imported **lazily** inside each tool: if
  `langchain-tavily` is not installed, the tool returns
  `success=False` with an "install with pip install langchain-tavily"
  message rather than crashing. This matches legacy modulex behavior.

## Installation

To get `langchain-tavily` along with the package:

```bash
pip install "modulex-integrations[tavily]"
```

(Eventually — once the `scripts/assemble_dependencies.py` script
populates per-integration extras from this integration's
`dependencies.toml`.)

## Maintainer

ModuleX core team.

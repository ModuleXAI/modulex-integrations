# Changelog

All notable changes to `modulex-integrations` are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `zoom` integration — 23 actions, auth: oauth2. Video conferencing platform
  for meetings, webinars, recordings, chat, and user management via the Zoom
  REST API. Producer-staged by integration-drafts; consumer-side audit applied
  3 patches before merge.
- `shopify` integration — 39 actions, auth: custom. E-commerce platform for
  managing products, orders, customers, and content via the Shopify Admin
  GraphQL API. Producer-staged by integration-drafts; consumer-side audit
  applied 3 patches before merge.
- `linkedin` integration — 18 actions, auth: oauth2. LinkedIn social
  networking platform for professional connections, posts, and organization
  management: create text/image posts, comment, like, manage organizations,
  fetch profiles, and search via the LinkedIn REST API. Producer-staged by
  integration-drafts; consumer-side audit applied 4 patches before merge.
- `microsoft_bookings` integration — 10 actions, auth: oauth2. Create and
  manage Microsoft Bookings businesses, services, staff members, customers,
  and appointments via the Microsoft Graph API. Producer-staged by
  integration-drafts; consumer-side audit applied 2 patches before merge.
- `jira` integration — 38 actions, auth: oauth2. Atlassian Jira Cloud
  project tracking and issue management: create/update/search issues,
  manage sprints/boards/epics, transition issues, manage comments,
  attachments, watchers, versions, and users via the Jira REST and Agile
  APIs. Producer-staged by integration-drafts; consumer-side audit applied
  1 patch before merge.
- `microsoft_teams` integration -- 12 actions, auth: oauth2. Create channels,
  send channel and chat messages, list teams/channels/chats/messages/shifts,
  search messages, and retrieve the current user via Microsoft Graph.
  Producer-staged by integration-drafts; consumer-side audit applied 8
  patches before merge.
- `google_sheets` integration — 14 actions, auth: oauth2. Read, write, and
  manage Google Sheets spreadsheets and worksheets via the Sheets v4 and
  Drive v3 REST APIs. Producer-staged by integration-drafts; consumer-side
  audit applied 4 patches before merge.
- `google_meet` integration — 2 actions, auth: oauth2. Schedule Google Meet
  video conferences (via Google Calendar events with conferenceData) and list
  available event color options. Producer-staged by integration-drafts;
  consumer-side audit applied 1 patch before merge.
- `google_calendar` integration — 16 actions, auth: oauth2. Manage Google
  Calendar events, calendars, and availability via the Calendar v3 REST
  API: create/update/delete events, list instances, query free/busy,
  quick-add, and manage recurring event series. Producer-staged by
  integration-drafts; consumer-side audit applied 4 patches before merge.
- `monday` integration — 13 actions, auth: api_key. Monday.com work
  management platform for boards, items, columns, groups, and updates via
  the GraphQL API. Producer-staged by integration-drafts; consumer-side
  audit applied 3 patches before merge.
- `google_slides` integration — 17 actions, auth: oauth2. Create and edit
  Google Slides presentations via the Slides and Drive REST APIs: manage
  slides, shapes, images, tables, text, merge data, and refresh charts.
  Producer-staged by integration-drafts; consumer-side audit applied 3
  patches before merge.
- `microsoft_onedrive` integration — 11 actions, auth: oauth2. Access and
  manage files in Microsoft OneDrive via the Microsoft Graph API: search,
  list, upload, download, create folders, and create sharing links.
  Producer-staged by integration-drafts; consumer-side audit applied 6
  patches before merge.
- `microsoft_excel` integration — 9 actions, auth: oauth2. Read, write, and
  manage Excel workbooks stored in OneDrive via the Microsoft Graph API.
  Producer-staged by integration-drafts; consumer-side audit applied 4
  patches before merge.
- `microsoft_outlook` integration — 20 actions, auth: oauth2. Send, draft,
  search, and organize email; manage contacts, folders, and categories via
  Microsoft Graph. Producer-staged by integration-drafts; consumer-side audit
  applied 4 patches before merge.
- `okta` integration — 4 actions (create_user, get_user, list_type_id_options,
  update_user), auth: custom (SSWS API token + subdomain). Pure HTTP, zero new
  runtime deps. Producer-staged by integration-drafts; consumer-side audit
  applied 0 patches before merge.

### Changed (logo polish — 26 manifests, `modulex:*` namespace)

- Migrated `logo` fields across 26 integration manifests to the
  `modulex:*` icon namespace (a ModuleX-side icon resolver). This
  supersedes some of the Iconify identifiers introduced in
  `0.1.0a13` — the `modulex:*` namespace is now the canonical icon
  source. Display-only — no schema delta, no behavior change, no
  test impact.
- Affected: apollo_io, appdrag, calendly, clickup, coinbase,
  convertapi, elevenlabs, exa, firecrawl, github, hackernews,
  hubspot, instacart, jina_ai, klaviyo, lemon_squeezy, linear,
  mailchimp, nasdaq, salesforce, scrape_do, semrush, servicenow,
  short_io, tavily, tinyurl.

### Changed (logo polish — 23 manifests)

- Normalized `logo` fields across 23 integration manifests to use
  Iconify identifiers (`logos:*`, `simple-icons:*`, `cib:*`) instead
  of bespoke CDN URLs or ad-hoc strings (`"bitcoin"`,
  `"elevenlabs"`). Display-only change — no schema delta, no
  behavior change, no test impact.
- Affected: airtable, calendly, clickup, cloudflare, coinbase,
  customerio, elevenlabs, github, gmail, hubspot, instacart,
  intercom, lemon_squeezy, linear, mailchimp, mysql, npm, pinterest,
  semrush, slack, snowflake, telegram, zendesk.

### Added (Wave 9 — Phase 1 closeout)

- **`posthog`** (78 actions) — the largest single integration in
  the package. Two API surfaces in one module:
  - **Project REST** (`{base_url}/api/projects/{project_id}/…`):
    dashboards, experiments, feature flags, insights, surveys,
    cohorts, persons, groups, session recordings, actions,
    annotations, alerts, early-access features, definitions, query.
    Bearer auth with personal API key.
  - **Ingest** (`{ingest_url}/i/v0/e/`, `/batch/`, `/flags`): the
    6 capture / identify / alias / evaluate_feature_flags /
    group_identify / batch actions. `project_api_key` in JSON
    body (no Bearer).
- **`custom` auth_type with 3 env vars** (`POSTHOG_API_KEY`,
  `POSTHOG_PROJECT_ID`, `POSTHOG_BASE_URL`) — same shape as
  PostHog's legacy `custom` schema. Pure HTTP, zero new runtime
  deps.
- Legacy quirks preserved verbatim:
  - `delete_action` falls back to a unique-name rename when
    PostHog's soft-delete PATCH fails (upstream bug).
  - `delete_action_by_name` does a DELETE → soft-delete → rename
    chain; returns success even when the action isn't found.
  - `update_feature_flag` takes a key (not ID), does a search
    lookup first to translate to the ID.
  - `evaluate_feature_flags` uses the `/flags?v=2` endpoint.
  - All 78 actions return the uniform `PostHogResult(success,
    error, result)` envelope; `result` carries raw upstream JSON.
- 39 new tests covering each surface + the multi-step quirks.
  Cumulative: 733 → 772 passing.

### Phase 1 done

**45 integrations / 590 actions** now live in `modulex-integrations`
and discovered via the `modulex.tools` entry-point group. The
original Phase-1 migration scope is complete. Brief #011 bundles
the Waves 6+7+8+9 pin bump for modulex (0.1.0a8 → 0.1.0a12).

### Added (Wave 8 — eighth bulk migration batch)

- **3 large integrations** — 66 LangChain `@tool` actions, all pure
  HTTP and zero new runtime deps:
  - `clickup` (23 actions) — workspaces, spaces, folders, lists,
    tasks, comments, tags, members via the v2 REST API. Raw
    `Authorization: <key>` (no Bearer prefix); `custom_task_ids`
    query-string pattern lets callers address tasks by their
    workspace-prefixed display ID; `search_tasks` filters
    client-side because ClickUp has no full-text search.
  - `google_drive` (24 actions) — **four Google APIs** (Drive v3 +
    Docs v1 + Sheets v4 + Slides v1) in one integration. Paired
    `oauth2 + bearer_token`. Multi-call workflows for
    `create_text_file` (multipart upload), `update_google_doc`
    (read end-index → delete → insert), `read_google_sheet`
    (resolve localized sheet names), and `move_item` (read parents
    first). Custom `_a1_to_grid` helper for Sheets formatting.
  - `mailchimp` (19 actions) — lists, subscribers, campaigns,
    tags, notes, segments. Datacenter extracted from the API key
    suffix (`xxx-us10`) to route to the right per-DC endpoint;
    Basic Auth with literal `anystring` username; subscribers
    addressed by MD5 hash of lowercase email.
- **No schema delta.** All three slot onto the existing surface.
- 90 new tests (clickup 31, google_drive 33, mailchimp 26).
  Cumulative: 643 → 733 passing.
- Drive-by: refactored ClickUp manifest's `ParameterDef`s to be
  multi-line per ruff E501; broke up two long-field-string params
  in google_drive's API calls.

### Added (Wave 7 — seventh bulk migration batch)

- **5 new integrations** — 93 LangChain `@tool` actions (the largest
  wave so far), focused on mid/large CRM/CS/AI platforms:
  - `hubspot` (26 actions) — HubSpot CRM via the **synchronous**
    `hubspot-api-client` SDK. Contacts/companies/deals/tickets CRUD
    (5 shapes × 4 object types) + engagements (note/task/meeting)
    + property introspection. Factored shared helpers
    (`_do_recent`, `_do_search`) collapse the 5×4 boilerplate.
    Paired `oauth2 + bearer_token` schemas. New dep:
    `hubspot-api-client>=11.0.0`.
  - `notion` (19 actions) — Notion REST v1; pure HTTP. Pages,
    databases, blocks, users, comments, search. **N+1 fetch**
    for `get_page` with content (page + block children).
    `_extract_title` walks the three Notion title conventions.
    OAuth uses HTTP Basic token exchange (Notion quirk). Paired
    `oauth2 + bearer_token`.
  - `elevenlabs` (15 actions) — AI voice (TTS/STT/SFX/voice
    cloning/isolation) + Conversational-AI agents +
    knowledge-base + conversations. Wraps the synchronous
    `elevenlabs` SDK in async tools. Audio I/O via base64 or URL
    (shared `_resolve_audio`). Paired `api_key + modulex_key`.
    New dep: `elevenlabs>=2.0.0`.
  - `zendesk` (17 actions) — Zendesk Support v2 REST API; pure
    HTTP. Ticket CRUD + tags + comments, custom fields, users,
    locales, macros, help-center articles. **Triple-credential
    pattern** (subdomain + email + api_key forming a Basic Auth
    header). Tag HTTP semantics non-obvious (PUT=add, POST=set,
    DELETE=remove) — documented in each action's docstring.
    `api_key` auth_type with 3 env vars.
  - `salesforce` (16 actions) — Salesforce REST API v62.0; pure
    HTTP. SOQL/SOSL queries, generic record CRUD, convenience
    creators for Account/Contact/Lead/Opportunity/Task/Case +
    Campaign membership + schema introspection. `auth_data`
    carries both `access_token` AND `instance_url` (per-org).
    Paired `oauth2 + bearer_token`.
- **Schema delta**: none. All five integrations slot onto the
  existing schema. The triple-credential zendesk pattern is just
  three env vars on the same `api_key` auth_schema.
- 116 new tests (notion 26, hubspot 23, elevenlabs 24, zendesk 22,
  salesforce 21). Cumulative: 527 → 643 passing.
- Drive-by: dropped a no-longer-needed `# type: ignore[import-untyped]`
  on elevenlabs (the SDK ships `py.typed`); refactored
  `existing_kb + [kb_locator]` to spread syntax (`[*existing_kb,
  kb_locator]`) per ruff RUF005.

### Added (Wave 6 — sixth bulk migration batch)

- **5 new integrations** — 50 LangChain `@tool` actions; introduces
  the **first SDK-backed DB integrations** to the package and the
  first `custom` auth_type with JWT signing:
  - `sendgrid` (15 actions) — transactional + marketing email via
    SendGrid v3 REST. Pure HTTP, `api_key` auth (Bearer header).
    Every action wraps in try/except → `success=False` envelope
    (exa-style); timeouts surface as a distinct error.
  - `coinbase` (8 actions) — Coinbase Developer Platform v2 + v3
    brokerage. **First `custom` auth_type integration** + first
    JWT-signing implementation (Ed25519 EdDSA or ECDSA ES256 picked
    by secret-format sniff). New runtime dep: `cryptography>=41.0`.
    Test suite exercises a real Ed25519 JWT roundtrip on a locally
    generated key.
  - `postgresql` (10 actions) — DB integration via `asyncpg`. Raw
    SQL, CRUD, upsert (`INSERT ... ON CONFLICT`), introspection.
    `?` placeholders rewritten to `$N`. New runtime dep:
    `asyncpg>=0.29.0`.
  - `mysql` (9 actions) — DB integration via `aiomysql`. Raw SQL,
    CRUD, stored procedures with multi-result-set support, table
    introspection (`SHOW FULL TABLES`, `SHOW COLUMNS`). `?`
    placeholders rewritten to `%s`. New runtime dep:
    `aiomysql>=0.2.0`.
  - `snowflake` (9 actions) — data-warehouse integration via the
    synchronous `snowflake-connector-python` driver. Wraps blocking
    SDK calls in `async def` (matches legacy; refactor deferred).
    Batched inserts with per-batch error tracking. New runtime dep:
    `snowflake-connector-python>=3.0.0`.
- **Schema delta**: none. All five integrations slot onto the
  existing schema. The three DB integrations + coinbase all use
  `CustomAuthSchema` for credential bundles that don't fit
  `api_key`/`oauth2`.
- 87 new tests (3 DB integrations exercise `unittest.mock.patch` on
  the cursor layer — first heavy use of the SDK-mock testing pattern
  in this phase). Cumulative: 440 → 527 passing.
- Drive-by: tightened a coinbase ECDSA branch with an `isinstance`
  guard (mypy complained about the broad `load_pem_private_key`
  return union); added per-test type ignores for `asyncpg` /
  `aiomysql` (no stubs published upstream).

### Added (Wave 5 — fifth bulk migration batch)

- **5 new integrations** — 78 LangChain `@tool` actions across the
  large-action band; one paired oauth2/bearer_token Google integration
  rounds out the pure-HTTP Gmail surface (no Google SDK dep):
  - `scrape_do` (5 actions) — web scraping with JS rendering +
    screenshots + markdown extraction. `api_key` via `?token={key}`
    query param. `_PARAM_MAP` translates snake_case action params
    to scrape.do's camelCase query keys.
  - `apollo_io` (28 actions) — B2B sales/CRM platform; uniform shape
    across all 28 actions backed by one `_call(path, api_key, …)`
    helper. `X-Api-Key` header. `_clean_domain()` strips scheme + path
    + `www.` consistently for domain-keyed enrichment calls.
  - `cloudflare` (13 actions) — DNS, WAF, zones, firewall rules,
    load balancing. Single `_call` helper for the entire surface;
    Cloudflare envelope (`{success, errors, result, result_info}`)
    handled uniformly. `_pagination_from(result_info)` extracts the
    Cloudflare pagination block into a typed sub-model.
  - `semrush` (19 actions) — SEO/marketing intelligence. Two endpoint
    families: legacy CSV (`api.semrush.com/`, semicolon-separated)
    and JSON (`api.semrush.com/analytics/ta/api/v3/`). `_parse_csv()`
    coerces the CSV body into list-of-dicts; `_call_csv` handles the
    `ERROR ...` body-in-200 failure case explicitly.
  - `gmail` (13 actions) — Google Gmail REST v1. Pure HTTP (no
    `google-api-python-client`); MIME messages built locally and
    base64url-encoded. Paired `oauth2 + bearer_token` schemas.
    `search_messages` and `list_messages` use an **N+1 metadata-fetch
    pattern** (list IDs, then per-message metadata GET for
    Subject/From/Date) — preserved verbatim from legacy.
- 103 new tests covering all five integrations (28 for apollo_io
  alone), exercising the `isinstance(result, dict)` + roundtrip-via-
  `model_validate` pattern plus per-integration shape coverage.
- Cumulative test count: 337 → 440 passing.

### Added (Wave 4 — fourth bulk migration batch)

- **5 new integrations** — 60 LangChain `@tool` actions across the
  mid-size band, half on the token-based runtime convention:
  - `linear` (7 actions) — Linear project + issue management.
    **First GraphQL integration** in the package; uses raw
    `Authorization: <key>` (no Bearer prefix). Filter clauses
    interpolated into the GraphQL string verbatim (matching legacy).
  - `airtable` (7 actions) — base discovery + table CRUD. Auto-
    batches at Airtable's 10-records-per-request limit;
    `update_records` accepts both `{id, fields: {…}}` and
    `{id, field_a: v}` shapes (legacy dual-shape preserved). camelCase
    `createdTime` field silenced via per-file N815 ignore.
  - `telegram` (17 actions) — Telegram Bot API for messaging, media,
    chat management, moderation, and long-polling. **Unique
    credential pattern**: bot token lives **inside the URL path**
    (`/bot{token}/...`), not a header.
  - `servicenow` (7 actions) — ITSM Trouble-Ticket API + Table API
    CRUD. Paired `oauth2 + bearer_token` schemas; instance-name
    substitution in URLs (`https://{instance_name}.service-now.com`).
    Token-based runtime convention with `_validate` for instance +
    token both being present.
  - `intercom` (13 actions) — customer-communication CRUD across
    contacts, conversations, tags, admins, and messages. Paired
    `oauth2 + bearer_token` schemas. **Three actions chain two API
    calls internally** — `upsert_contact` (search → PUT/POST),
    `create_note` (/me → POST note), `send_incoming_message`
    (/contacts → POST conversation).
- 90 new tests (`isinstance(result, dict)` + roundtrip-via-
  `model_validate` pattern, plus multi-call coverage for the
  Intercom two-step workflows); total: 247 → 337 passing.

### Added (Wave 3 — third bulk migration batch)

- **5 new integrations** — 43 LangChain `@tool` actions across the
  mid-size band, exercising every remaining auth pattern at least once:
  - `short_io` (8 actions) — URL shortening + analytics + link metadata.
    `api_key` (raw header, no `Bearer` prefix). Per-file `N815` ignore
    for the camelCase outputs (`originalURL`, `shortURL`, etc.).
  - `nasdaq` (7 actions) — financial data via the `nasdaqdatalink` SDK
    (first non-LangChain vendor SDK in this phase). `api_key` via
    `?api_key={api_key}` query string — re-proves the
    `TestEndpoint.params` path introduced in Wave 2. Pandas DataFrames
    coerced to JSON-safe records with NaN→None cleanup (handles
    pandas 3.x behavior change).
  - `firecrawl` (7 actions) — AI web scraping/crawling/search.
    **First integration with paired `api_key + modulex_key` schemas**
    (both Bearer-authed; runtime picks which credential to inject).
    Long-running jobs use 180s timeouts.
  - `jina_ai` (7 actions) — embeddings, rerank, reader, search, deep
    search, segment, classify. Second paired-schemas integration. Six
    distinct subdomains (`api.jina.ai`, `r.jina.ai`, `s.jina.ai`,
    `deepsearch.jina.ai`, `segment.jina.ai`). Reader/Search consume
    configuration via `X-*` request headers (legacy pattern preserved).
  - `calendly` (11 actions) — events, invitees, event types,
    scheduling links, availability, organization members, groups,
    webhook subscriptions. **First `oauth2 + bearer_token` integration
    since github/slack** (token-based runtime convention with
    `auth_type, auth_data` first args). Auto-resolves missing
    `user`/`organization` filters via a side call to `/users/me`.
- 73 new tests (`isinstance(result, dict)` + roundtrip-via-
  `model_validate` pattern, plus SDK-mock + paired-schema coverage);
  total: 174 → 247 passing.
- `nasdaq/dependencies.toml` declares `nasdaq-data-link>=1.0.0`.
  Added to `[project.optional-dependencies] dev` extras so the SDK
  module is importable for `patch.dict(sys.modules)` test mocks.
  Pandas comes in transitively.

### Added (Wave 2 — second bulk migration batch)

- **5 new integrations** — 31 LangChain `@tool` actions, mostly
  small/simple HTTP across `api_key` and one `modulex_key`:
  - `klaviyo` (5 actions) — list/profile/subscription management
    against the Klaviyo REST API (revision `2024-10-15`).
  - `convertapi` (4 actions) — file/base64/web URL conversion plus
    format discovery. First integration to use `test_endpoint.params`
    for query-string credential validation (`?Secret={api_key}`).
  - `appdrag` (3 actions) — cloud function invocation and raw
    INSERT/UPDATE against the AppDrag CloudDB. First integration with
    **two env vars** (`APPDRAG_API_KEY` + `APPDRAG_APP_ID`), both
    auto-injected by the runtime.
  - `hackernews` (10 actions) — search via hnrss.org RSS feeds plus
    direct Firebase JSON API (`top/new/best/ask/show/job` stories,
    item, user). Public API — `modulex_key` auth_schema, no
    `test_endpoint`.
  - `lemon_squeezy` (10 actions) — customers/orders/products/
    subscriptions/stores via the JSON:API v1 endpoints. Each list
    method returns `data` + `meta` page-state unchanged.
- 69 new tests (`isinstance(result, dict)` + roundtrip-via-
  `model_validate` pattern); total: 105 → 174 passing.

### Changed (schema)

- `TestEndpoint.params: dict[str, str]` added — additive, defaults
  to `{}`. Lets integrations whose credential test auths via query
  string (ConvertAPI's `?Secret={api_key}`; nasdaq in Wave 3 follows
  the same pattern) match the modulex runtime, which already reads
  `test_endpoint.get("params", {})` in `credential_service.py`. Fully
  backward-compatible — existing manifests are unaffected.

### Added

- Initial repository skeleton (src/ layout, hatchling build, pytest/ruff/mypy config).
- `IntegrationManifest` pydantic schema with discriminated-union `auth_schemas` covering oauth2, bearer_token, api_key, modulex_key, custom, internal.
- Contract tests on a github-shaped manifest.
- `CLAUDE.md` — project rules for Claude Code sessions in this repo.
- `external-briefs/` workflow scaffold (`README.md` spec + `modulex/` placeholder) for coordinating changes in sibling repos.
- Community meta files: `.github/CODEOWNERS`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/{bug_report.md,integration_request.md,config.yml}`, `SECURITY.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1).
- `.github/workflows/validate.yml` — lint + type-check + test on Python 3.12 and 3.13.
- `.editorconfig` and `.python-version` for consistent local tooling.

### Changed

- `README.md` expanded with "Why this repo exists", badges, per-integration layout, and a roadmap section.
- `.gitignore` no longer ignores `.python-version` (file is now committed); now also ignores the hatch-vcs-generated `src/modulex_integrations/_version.py`.
- `pyproject.toml`: switched to `dynamic = ["version"]` driven by `hatch-vcs`; static `version = "0.0.1"` removed. Static `__version__` in `__init__.py` replaced by `importlib.metadata`-based resolution.

### Added (release infrastructure)

- `.github/workflows/release.yml` — tag-triggered (`v*`) workflow that classifies pre-release vs stable via PEP 440, enforces branch-of-origin (stable from `main`, pre-release from `staging`), builds sdist + wheel, and publishes to PyPI via Trusted Publishing OIDC in the `release-pypi` environment.
- `RELEASING.md` — release process, PyPI Trusted Publisher setup checklist, and the modulex-side per-branch pinning policy.

### Added (Wave 1 — first bulk migration batch)

- **5 new integrations** — 19 LangChain `@tool` actions across simple
  HTTP + validated auth types (`api_key`, `modulex_key`):
  - `instacart` (3 actions) — public Instacart recipe/list/retailer endpoints
  - `tinyurl` (3 actions) — URL shortening + analytics + metadata
  - `customerio` (3 actions) — first integration using HTTP Basic Auth
    (site_id + api_key pair); runtime injects both, tool builds Basic
    header
  - `npm` (6 actions) — public npm registry: info, search, popular,
    versions, deps, downloads. First integration where api_key is
    optional (public registry)
  - `pinterest` (4 actions) — boards + sections + pins; supports both
    `api_key` and `oauth2` auth schemas (both resolve to Bearer)
- 44 new tests (`isinstance(result, dict)` + roundtrip-via-`model_validate`
  pattern); total: 61 → 105 passing.

### Changed (schema)

- `_AuthSchemaBase.test_endpoint` is now optional
  (`TestEndpoint | None = None`). Public-API integrations like
  instacart and hackernews legitimately ship no credential test
  endpoint — the legacy modulex JSON omitted the field. Purely
  additive change.

### Fixed

- **Critical**: `@tool` functions now return plain dicts at runtime
  (via the new `@serialize_pydantic_return` decorator), not pydantic
  ``BaseModel`` instances. modulex's downstream code serializes every
  tool result via plain ``json.dumps()``, which cannot encode pydantic
  models — calling `exa.search` or `tavily.web_search` from a modulex
  agent crashed with ``TypeError: Object of type SearchOutput is not
  JSON serializable``. All four integrations (github, slack, exa,
  tavily) updated. Return-type annotations stay as pydantic classes
  so modulex's ``package_loader.py`` can still derive the LLM-facing
  output_schema via ``typing.get_type_hints``.

### Added

- `modulex_integrations.serialize_pydantic_return` — decorator that
  auto-dumps pydantic returns to dicts. Top-level re-export.
  Implementation in `src/modulex_integrations/_internal/serialize.py`.
- `tests/test_serialize.py` — 4 unit tests pinning down the contract
  (pydantic → dict; non-pydantic → passthrough; annotation preserved
  for `get_type_hints`; nested fields dump correctly).
- All existing tests updated to assert `isinstance(result, dict)` and
  roundtrip through `Model.model_validate(result)` for attribute
  access. Test count: 57 → 61.

### Added (Phase 3 — SDK pattern + further migrations)

- **tavily integration** — 3 LangChain `@tool` async actions:
  `web_search`, `answer_search`, `news_search`. First SDK-based
  integration: wraps `langchain_tavily.TavilySearch` via lazy import
  inside each tool. The lazy import + graceful "install with pip
  install langchain-tavily" fallback matches legacy modulex behavior.
- `tavily/dependencies.toml` declares `langchain-tavily>=0.2.0` for
  the future assemble script.
- `pyproject.toml` `dev` extras include `langchain-tavily` so tests
  can exercise the real SDK class via `unittest.mock.patch` — the
  CONTRIBUTING.md-specified pattern for SDK tools, now validated.
- Tests use `patch.dict(sys.modules, {"langchain_tavily": ...})` to
  both substitute a mock SDK class (happy path) and simulate the
  missing-SDK ImportError (graceful-degradation path).

### Added (Phase 3 — first bulk migrations)

- **slack integration** — 8 LangChain `@tool` async actions:
  `list_channels`, `post_message`, `reply_to_thread`, `add_reaction`,
  `get_channel_history`, `get_thread_replies`, `get_users`,
  `get_user_profile`. OAuth2 + Bot Token auth schemas. Slack's
  HTTP-200-with-`ok:false` error model is preserved as
  `success=False` + `error` on every output model.
- **exa integration** — 4 LangChain `@tool` async actions: `search`,
  `get_contents`, `find_similar`, `answer`. First migration to use
  the `api_key` runtime convention (signature is
  `(query, api_key, ...)` rather than `(auth_type, auth_data, ...)`)
  and to exercise the `api_key` + `modulex_key` auth schema variants.
- `pyproject.toml`: entry-point lines for `slack` and `exa`. End-to-end
  discovery now reports 3 integrations contributing 28 tools.
- 24 new tests (12 slack + 12 exa, includes failure-branch coverage
  for the `ok:false` and non-2xx + empty-key paths). Total package
  test count: **49**.

### Changed (schema)

- `IntegrationManifest.auth_schemas[*].test_endpoint.body` — new
  optional field (`dict[str, Any] | None = None`). Needed for POST-based
  credential checks (e.g. Exa's `POST /search` with a probe payload).
  Purely additive; existing manifests are unaffected.

### Added (github POC migration)

- First integration: `modulex_integrations.tools.github` — 16 LangChain `@tool` async actions ported from the legacy modulex inline implementation:
  `list_repositories`, `create_repository`, `delete_repository`, `get_repository`,
  `list_issues`, `create_issue`, `get_issue`, `update_issue`,
  `list_pull_requests`, `create_pull_request`, `get_pull_request`, `merge_pull_request`,
  `create_branch`, `get_file_content`, `create_commit`, `search_code`.
- `manifest.py` — pydantic `IntegrationManifest` replacing the legacy 1180-line JSON; OAuth2 + Personal Access Token auth schemas with credential test endpoints.
- `outputs.py` — 16 pydantic response models; the runtime derives output JSONSchema via `Model.model_json_schema()` (no `output_schema` field in the manifest).
- `tests/test_github.py` — 16 happy-path tests using `pytest-httpx`'s `httpx_mock` fixture plus three manifest sanity tests. Total package test count: 8 schema + 19 github = 27.
- `pyproject.toml`: entry-point line `github = "modulex_integrations.tools.github"` registered under `[project.entry-points."modulex.tools"]`. Validated end-to-end via `importlib.metadata.entry_points(group="modulex.tools")` — modulex's runtime discovery path works without changes.

## [0.0.1] — 2026-05-15

Project bootstrap.

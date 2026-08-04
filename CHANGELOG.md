# Changelog

All notable changes to `modulex-integrations` are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `agentphone` integration — 22 actions, auth: api_key.
- `fireflies` integration — 10 actions, auth: api_key. Transcript listing and
  retrieval, user and contact directory, audio upload by URL, live-meeting
  join, and bite creation/listing over the Fireflies GraphQL API.
- `gohighlevel` integration — 117 actions, auth: oauth2. Contacts with their
  notes, tasks and tags, opportunities and pipelines, conversations and
  messages across SMS/email/social, email templates and campaigns, plus
  calendars, appointments, availability schedules, booking slots, groups,
  resources and notifications over the GoHighLevel v2 API. Sub-account
  scoped: the location ID is stored on the credential rather than passed per
  action.
- `greenhouse` integration — 11 actions, auth: api_key. Candidates, jobs,
  applications, users, departments, offices, and job stages over the
  Greenhouse Harvest read API.
- `latex` integration — 3 actions, auth: modulex_key. TeX Live package search,
  single-package metadata, and font search. The service takes no credential;
  the managed-key schema is declarative only.
- `reddit` integration — 38 actions, auth: custom. Posts, comments, search,
  user and subreddit surfaces, the inbox, writes and per-thing state toggles,
  plus the six moderator actions. Static script-app credentials, no browser
  redirect.
- `ashby` integration — 28 actions, auth: api_key. Candidates, applications and
  stage changes, jobs, openings and postings, offers, interviews, notes, plus
  the reference-data lists, over the Ashby ATS API.
- `buffer` integration — 10 actions, auth: api_key. Post create/edit/read/
  delete, channel and account lookup, and the ideas surface over Buffer's
  GraphQL API.
- `fathom` integration — 6 actions, auth: api_key. Meeting listing with
  date/team/recorder/invitee-domain filters, meeting-type listing, per-recording
  summary and transcript retrieval, and team/team-member directory lookups over
  the Fathom External API.
- `flint` integration — 3 actions, auth: api_key. Starts prompt-driven and
  template-based page-generation agent tasks on a Flint site and reads back a
  task's status and the pages it created, modified, or deleted.
- `arxiv` integration — 3 actions, auth: modulex_key. Keyword/field search,
  single-paper metadata lookup, and an author's recent submissions over the
  public arXiv API. The API takes no credential; the managed-key schema is
  declarative only.
- `wikipedia` integration — 4 actions, auth: modulex_key. Page summary, article
  search, full page content with HTML, and a random article, across any language
  edition. The API takes no credential; the managed-key schema is declarative
  only.
- `ses` integration — 19 actions, auth: custom. Amazon SES API v2 sending
  (simple, templated, bulk, custom verification), email identity and DKIM
  management, email templates, suppression list, configuration sets, and
  account sending quota. Requests are signed with AWS Signature Version 4
  using the standard library; no AWS SDK dependency.
- `zoho_desk` integration — 9 actions, auth: custom. Ticket listing/read/update,
  ticket comments and threads, contact lookup, and organization (portal)
  discovery over the Zoho Desk REST API, with data-center-aware host
  resolution.

### Changed

- `google_docs`, `google_sheets`, `google_slides`, `google_drive` — OAuth now
  requests only `drive.file` instead of the API-wide `documents`,
  `spreadsheets`, and `presentations` scopes. Access is per-file: actions
  operating on a pre-existing file require that the app created it or that the
  user shared it with the app. No actions were removed.
- `google_tag_manager` — now read-only. Requests only `tagmanager.readonly`;
  the `tagmanager.edit.containers` scope was dropped.

### Removed

- `google_tag_manager` — `create_tag`, `update_tag`, and `update_variable`
  actions (6 actions → 3), along with their output models.

## [0.12.0] - 2026-07-18

### Added

- `mongodb_atlas` integration — 6 actions, auth: custom. Atlas Vector
  Search (`$vectorSearch`) plus database/collection/search-index
  introspection and document insert/delete via the PyMongo async
  driver.
- `pinecone` integration — 9 actions, auth: custom. Vector query,
  raw-text `search_records` (integrated-embedding indexes), index
  CRUD/stats, and vector upsert/delete over the native REST API.
- `qdrant` integration — 7 actions, auth: custom. Universal
  `points/query` search (vector, or text + model on Qdrant Cloud
  inference), collection CRUD/info, and point upsert/delete.
- `weaviate` integration — 7 actions, auth: custom. GraphQL
  nearVector/nearText search, schema management, and object
  insert/delete.

  All four are pure pass-through vector-database tools: they call the
  provider's own HTTP API (or driver) with the integration's own
  credential and return native response shapes — no ModuleX-side
  query embedding or result normalization.

## [0.11.0] - 2026-06-26

### Added

- `linear` — `team_id` on `create_issue`, `create_project`,
  `update_issue`, `search_issues`, and `list_projects` now accepts the
  team's short key (e.g. `ENG`) or name in addition to its UUID.
  Non-UUID references are resolved to the UUID via a teams lookup before
  the request; an unresolvable reference fails clearly and lists the
  available teams. UUID values skip the lookup entirely (no extra
  round-trip).

### Changed

- `elevenlabs`, `firecrawl` — dropped the `modulex_key` managed-key
  auth schema; both now ship a single `api_key` (bring-your-own-key)
  schema. The tool code is unchanged (already auth-agnostic — the
  injected credential is the same `api_key: str` parameter either way).

## [0.10.0] - 2026-06-19

### Changed (schema)

- `EnvVar.inject_into_auth_data: bool = False` added — additive,
  defaults to `False` (today's behavior preserved). When `True`, the
  modulex runtime surfaces the value in `auth_data` at action time:
  per-credential user input (`only_for_custom=False`) is persisted at
  OAuth2 creation; server-level secrets (`only_for_custom=True`) are
  injected from the server environment at tool execution. Fully
  backward-compatible — every other integration dumps it as `False`
  and the runtime injection is a no-op for them.

### Fixed

- `linear` — GraphQL errors now surface Linear's actionable reason.
  The helper previously reported only the top-level `message`, so every
  input-validation failure collapsed to the generic
  `"Argument Validation Error"` with no indication of which field was
  rejected. It now extracts the detail Linear puts in
  `extensions.userPresentableMessage` (falling back to
  `exception.validationErrors[].constraints`, then `extensions.type`),
  e.g. `"Argument Validation Error: teamId must be a UUID"`. Also
  tightened the `create_issue` / `create_project` `team_id` parameter
  descriptions to state it is the team **UUID** (the `id` from
  `get_teams`), not the short team key like `ENG` — the most common
  cause of the error.

- `linear` — `search_issues` / `list_projects` `order_by` is now typed
  `Literal["createdAt", "updatedAt"]` instead of a free-form `str`.
  Linear's `PaginationOrderBy` is an enum with only those two values, so
  any other value previously failed the *entire* query server-side with
  `success=False`; the constraint rejects it at the input boundary with a
  clear validation error and shows the LLM only valid options.

- `linear` — `get_teams` gained an `after` pagination cursor;
  workspaces with more teams than `limit` could previously only return
  the first page even though `page_info` flagged the truncation.

- `linear` — hardened all GraphQL calls against injection. Filter
  objects (`search_issues`'s team/project/assignee/state/labels and the
  free-text `query`; `list_projects`'s team filter) and pagination
  cursors (`after`) are now passed as typed GraphQL variables
  (`$filter: IssueFilter` / `$filter: ProjectFilter`, `$after: String`)
  instead of being string-interpolated into the query body, so an
  LLM-supplied value can no longer alter query structure. The
  highest-risk vector was `search_issues`'s `query` — literal free text
  spliced into the query string. Filter type names and nested shapes
  were verified against Linear's published schema; behavior is
  unchanged for valid inputs.

- `google_ads` / `google_merchant_center` — flagged
  `GOOGLE_ADS_DEVELOPER_TOKEN` (`only_for_custom=True`) and
  `GOOGLE_MERCHANT_CENTER_MERCHANT_ID` (`only_for_custom=False`) with
  `inject_into_auth_data=True` so the developer token and merchant ID
  reach `auth_data` at action time, fixing the "missing from auth_data"
  errors on `list_account_id_options` / `create_product`. Requires the
  matching modulex runtime change (external brief #021).

### Added

- `twilio_voice` integration — 3 actions, auth: api_key.

- `vanta` integration — 29 actions, auth: custom.

- `vercel` integration — 56 actions, auth: api_key. Vercel REST API
  integration spanning deployments, projects, domains, DNS records,
  environment variables, teams, webhooks, and aliases.

- `whatsapp` integration — 1 action, auth: api_key.

- `wiza` integration — 4 actions, auth: api_key.

- `youtube` integration — 9 actions, auth: api_key.

- `zerobounce` integration — 2 actions, auth: api_key.

- `railway` integration — 20 actions, auth: api_key.

- `resend` integration — 8 actions, auth: api_key.

- `revenuecat` integration — 10 actions, auth: api_key. In-app subscription
  and customer management via the RevenueCat REST API v1 (create_purchase,
  defer_google_subscription, delete_customer, get_customer, grant_entitlement,
  list_offerings, refund_google_subscription, revoke_entitlement,
  revoke_google_subscription, update_subscriber_attributes).

- `serper` integration — 1 action, auth: api_key.

- `similarweb` integration — 5 actions, auth: api_key.

- `sixtyfour` integration — 4 actions, auth: api_key.

- `stripe` integration — 50 actions, auth: api_key. Stripe
  payments REST API covering payment intents, customers, subscriptions,
  invoices, charges, products, prices, and events — create / retrieve /
  update / delete / list / search across each resource. Bodies are sent
  form-encoded (`application/x-www-form-urlencoded`) with Stripe's
  bracket notation for nested fields.

- `loops` integration — 10 actions, auth: api_key.

- `mem0` integration — 3 actions, auth: api_key.

- `neverbounce` integration — 2 actions, auth: api_key.

- `new_relic` integration — 4 actions, auth: api_key.

- `obsidian` integration — 15 actions, auth: api_key.

- `pulse` integration — 1 action, auth: api_key.

- `quiver` integration — 3 actions, auth: api_key.

- `greptile` integration — 4 actions, auth: api_key.

- `icypeas` integration — 2 actions, auth: api_key.

- `incidentio` integration — 46 actions, auth: api_key.

- `instantly` integration — 13 actions, auth: api_key.

- `kalshi` integration — 22 actions, auth: api_key. Kalshi Trade API
  for prediction-market data and trading: 13 public market-data actions
  (markets, events, series, trades, orderbook) plus 9 authenticated
  portfolio/order actions signed per-request with the user's RSA private
  key (RSA-PSS over SHA-256, via `cryptography`).

- `lemlist` integration — 3 actions, auth: api_key.

- `linkup` integration — 1 action, auth: api_key.

- `dropcontact` integration — 1 action, auth: api_key.

- `enrow` integration — 2 actions, auth: api_key.

- `findymail` integration — 11 actions, auth: api_key.

- `gamma` integration — 5 actions, auth: api_key.

- `grafana` integration — 25 actions, auth: api_key.

- `grain` integration — 9 actions, auth: api_key.

- `granola` integration — 3 actions, auth: api_key.

- `agentmail` integration — 21 actions, auth: api_key.

- `airweave` integration — 1 action, auth: api_key.

- `amplitude` integration — 11 actions, auth: custom.

- `brandfetch` integration — 2 actions, auth: api_key.

- `clay` integration — 1 action, auth: api_key.

- `crowdstrike` integration — 3 actions, auth: api_key.

- `daytona` integration — 12 actions, auth: api_key.

- `mercury` integration — 1 action, auth: bearer_token. Producer-staged
  by integration-drafts; consumer-side audit applied 1 patch before merge.

- `linear` — OAuth2 authentication alongside the existing API key.
  Adds an `OAuth2AuthSchema` (`auth_url`
  `https://linear.app/oauth/authorize`, `token_url`
  `https://api.linear.app/oauth/token`, scopes `read`/`write`, env vars
  `LINEAR_OAUTH2_CLIENT_ID` / `LINEAR_OAUTH2_CLIENT_SECRET`). All tools
  converted from the key-based `api_key` parameter to the token-based
  `(auth_type, auth_data)` convention (mirroring `monday`): `oauth2`
  tokens use `Authorization: Bearer …`, API keys keep Linear's raw
  `Authorization` header. The runtime already serves both auth families,
  so no modulex code change is required — only the OAuth app
  client_id/secret in the deployment environment.

- `revolt` integration — 3 actions, auth: bearer_token. Revolt open-source
  chat platform — group management and friend requests (create_group,
  add_group_member, send_friend_request). Producer-staged by
  integration-drafts; consumer-side audit applied 5 patches before merge.

- `woocommerce` integration — 17 actions, auth: custom. WooCommerce REST API
  integration for managing orders, products, customers, and refunds on
  self-hosted WooCommerce stores (create_order, get_order, list_orders,
  delete_order, update_order_status, create_product, update_product,
  get_product, list_products, search_customers, get_customer,
  create_customer, add_order_note, get_order_note, list_order_notes,
  create_refund, list_payment_method_options). Producer-staged by
  integration-drafts; consumer-side audit applied 2 patches before merge.

- `coinmarketcap` integration — 4 actions, auth: api_key. Cryptocurrency
  market data, quotes, and metadata from the CoinMarketCap API
  (get_cryptocurrency_metadata, id_map, latest_listings, latest_quotes).
  Producer-staged by integration-drafts; consumer-side audit applied
  2 patches before merge.

- `cogmento` integration — 4 actions, auth: oauth2. CRM platform for
  managing contacts, deals, and tasks via the Cogmento API
  (create_contact, create_deal, create_task, list_user_ids_options).
  Producer-staged by integration-drafts; consumer-side audit applied
  3 patches before merge.

- `fellow` integration — 3 actions, auth: api_key. Meeting productivity
  platform for notes, action items, and meeting management via the Fellow API
  (archive_action_item, complete_action_item, get_note_by_id). Producer-staged
  by integration-drafts; consumer-side audit applied 1 patch before merge.

- `motion` integration — 6 actions, auth: api_key. AI-powered task and
  project management platform for automatic scheduling via the Motion API
  (create_task, delete_task, get_schedules, get_task, move_workspace,
  update_task). Producer-staged by integration-drafts; consumer-side audit
  applied 1 patch before merge.

- `livestorm` integration — 7 actions, auth: oauth2. Video engagement
  platform for webinars and virtual events via the Livestorm REST API
  (create_event, get_event, list_attendees_from_event, list_events,
  list_sessions, register_someone_for_session, update_event).
  Producer-staged by integration-drafts; consumer-side audit applied
  12 patches before merge.

- `heygen` integration — 5 actions, auth: api_key. AI video generation
  platform for creating talking avatar videos via the HeyGen API
  (create_talking_photo, create_video_from_template,
  list_custom_events_options, list_voice_id_options, retrieve_video_link).
  Producer-staged by integration-drafts; consumer-side audit applied
  1 patch before merge.

- `yelp` integration — 4 actions, auth: api_key. Search businesses, read
  reviews, and get business details via the Yelp Fusion API
  (search_businesses, get_business_details, list_business_reviews,
  search_businesses_by_phone_number). Producer-staged by
  integration-drafts; consumer-side audit applied 1 patch before merge.

- `square` integration — 6 actions, auth: oauth2. Payment processing,
  commerce, and business management platform via the Square Connect v2 API
  (create_customer, create_invoice, create_order, list_event_types_options,
  list_location_options, send_invoice). Producer-staged by
  integration-drafts; consumer-side audit applied 4 patches before merge.

- `hunter` integration — 13 actions, auth: api_key. Professional email
  finding and verification via the Hunter.io API (account_information,
  combined_enrichment, create_lead, delete_lead, domain_search,
  email_count, email_finder, email_verifier, get_lead, get_leads_list,
  list_leads, list_leads_lists, update_lead). Producer-staged by
  integration-drafts; consumer-side audit applied 1 patch before merge.

- `gong` integration — 5 actions, auth: oauth2. Revenue intelligence
  platform for recording, transcribing, and analyzing sales conversations
  via the Gong REST API (add_new_call, get_extensive_data, list_calls,
  list_workspace_id_options, retrieve_transcripts_of_calls).
  Producer-staged by integration-drafts; consumer-side audit applied
  3 patches before merge.

- `figma` integration — 3 actions, auth: oauth2. Design collaboration
  platform for creating, sharing, and commenting on design files via the
  Figma REST API (list_comments, delete_comment, post_a_comment).
  Producer-staged by integration-drafts; consumer-side audit applied
  5 patches before merge.
- `postgrid` integration — 3 actions, auth: api_key. Programmatic direct
  mail delivery via the PostGrid Print & Mail API (create_contact,
  create_letter, create_postcard). Producer-staged by integration-drafts;
  consumer-side audit applied 1 patch before merge.
- `product_hunt` integration — 1 action, auth: oauth2. Discover and explore
  tech products and topics via the Product Hunt GraphQL API
  (list_topic_options). Producer-staged by integration-drafts; consumer-side
  audit applied 1 patch before merge.
- `shopify_partner` integration — 1 action, auth: api_key. Shopify Partner
  webhook verification via local HMAC-SHA256 signature validation
  (verify_webhook). Producer-staged by integration-drafts; consumer-side
  audit applied 1 patch before merge.
- `browserbase` integration — 3 actions, auth: api_key. Cloud browser
  infrastructure for running and managing headless browser sessions via
  the Browserbase REST API (create_context, create_session, list_projects).
  Producer-staged by integration-drafts; consumer-side audit applied
  1 patch before merge.
- `pagerduty` integration — 4 actions, auth: oauth2. Incident management
  and on-call scheduling platform via the PagerDuty REST API
  (trigger_incident, acknowledge_incident, resolve_incident,
  find_oncall_user). Producer-staged by integration-drafts; consumer-side
  audit applied 5 patches before merge.
- `netlify` integration — 4 actions, auth: oauth2. Web hosting and
  automation platform for modern web projects via the Netlify REST API
  (get_site, list_files, list_site_deploys, rollback_deploy).
  Producer-staged by integration-drafts; consumer-side audit applied
  4 patches before merge.
- `azure_storage` integration — 4 actions, auth: oauth2. Manage blobs and
  containers in Microsoft Azure Blob Storage via the Azure Blob Storage
  REST API (create_container, delete_blob, list_containers, upload_blob).
  Producer-staged by integration-drafts; consumer-side audit applied
  1 patch before merge.
- `insightly` integration — 2 actions, auth: api_key. CRM and project
  management platform for managing contacts and tasks via the Insightly
  REST API (create_contact, create_task). Producer-staged by
  integration-drafts; consumer-side audit applied 1 patch before merge.
- `reflect` integration — 5 actions, auth: oauth2. Note-taking and
  knowledge management via the Reflect API (append_daily_note, create_link,
  get_user, list_graph_id_options, list_links). Producer-staged by
  integration-drafts; consumer-side audit applied 7 patches before merge.
- `help_scout` integration — 8 actions, auth: oauth2. Customer support
  helpdesk platform with shared inboxes, knowledge base, and live chat
  via the Help Scout REST API. Producer-staged by integration-drafts;
  consumer-side audit applied 3 patches before merge.
- `luma` integration — 8 actions, auth: api_key. Event management platform
  for creating, managing, and tracking events and guests via the Luma
  public API. Producer-staged by integration-drafts; consumer-side audit
  applied 2 patches before merge.
- `typeform` integration — 12 actions, auth: oauth2. Online form builder
  for surveys, quizzes, and interactive forms via the Typeform REST API.
  Producer-staged by integration-drafts; consumer-side audit applied
  3 patches before merge.
- `microsoft_entra_id` integration — 12 actions, auth: oauth2. Identity
  and access management via Microsoft Graph API for users, groups, and
  directory objects. Producer-staged by integration-drafts; consumer-side
  audit applied 4 patches before merge.
- `datadog` integration — 11 actions, auth: api_key. Infrastructure
  monitoring, log management, and application performance platform via
  the Datadog REST API. Producer-staged by integration-drafts;
  consumer-side audit applied 2 patches before merge.
- `browser_use` integration — 25 actions, auth: api_key. AI-powered cloud
  browser automation via the Browser Use API. Producer-staged by
  integration-drafts; consumer-side audit applied 1 patch before merge.
- `freshdesk` integration — 45 actions, auth: api_key. Customer support
  helpdesk platform for managing tickets, contacts, agents, and knowledge
  base articles via the Freshdesk REST API. Producer-staged by
  integration-drafts; consumer-side audit applied 1 patch before merge.

- `amazon_selling_partner` integration — 8 actions, auth: oauth2. Amazon
  Selling Partner API for managing orders, inventory, pricing, and reports
  on Amazon marketplaces (check_fba_inventory_levels,
  fetch_orders_by_date_range, generate_sales_inventory_reports,
  get_order_details, list_inbound_shipments, list_marketplace_id_options,
  optimize_product_pricing, retrieve_sales_performance_reports).
  Producer-staged by integration-drafts; consumer-side audit applied
  4 patches before merge.
- `microsoft_365_people` integration — 3 actions, auth: oauth2. Manage
  contacts and contact folders via the Microsoft Graph API (create_contact,
  create_contact_folder, update_contact). Producer-staged by
  integration-drafts; consumer-side audit applied 2 patches before merge.
- `microsoft_power_bi` integration — 10 actions, auth: oauth2. Business
  intelligence and analytics platform for interactive visualizations,
  reports, and dashboards via the Power BI REST API. Producer-staged by
  integration-drafts; consumer-side audit applied 3 patches before merge.
- `microsoft_dynamics_365_sales` integration — 11 actions, auth: oauth2.
  CRM platform for managing accounts, contacts, appointments, and custom
  entities via the Dynamics 365 Web API. Producer-staged by
  integration-drafts; consumer-side audit applied 5 patches before merge.
- `microsoft_sql_server` integration — 4 actions, auth: custom. Execute
  queries and manage data in Microsoft SQL Server databases via pymssql
  (execute_raw_query, execute_query, insert_row, list_table_options).
  Producer-staged by integration-drafts; consumer-side audit applied
  3 patches before merge.
- `amazon_alexa` integration — 2 actions, auth: oauth2. Simulate and test
  Alexa skills via the Alexa Skills Management API (simulate_skill,
  get_simulation_results). Producer-staged by integration-drafts;
  consumer-side audit applied 4 patches before merge.
- `fal_ai` integration — 4 actions, auth: api_key. Queue-based AI model
  inference via the fal.ai platform (add_request_to_queue, cancel_request,
  get_request_response, get_request_status). Producer-staged by
  integration-drafts; consumer-side audit applied 1 patch before merge.
- `heroku` integration — 1 action, auth: oauth2. Cloud platform management
  via the Heroku Platform API (list_apps). Producer-staged by
  integration-drafts; consumer-side audit applied 1 patch before merge.
- `cal_com` integration — 6 actions, auth: api_key. Scheduling and booking
  management via the Cal.com v2 API (create_booking, delete_booking,
  get_all_bookings, get_bookable_slots, get_booking,
  list_event_type_id_options). Producer-staged by integration-drafts;
  consumer-side audit applied 2 patches before merge.
- `dropbox` integration — 12 actions, auth: oauth2. Cloud file storage,
  sharing, and collaboration platform: create/delete/move/rename folders and
  files, search, list contents, create text files, manage shared links, and
  list file revisions via the Dropbox HTTP API. Producer-staged by
  integration-drafts; consumer-side audit applied 3 patches before merge.

- `etsy` integration — 6 actions, auth: oauth2. Etsy marketplace listing
  management via the Open API v3 (create_draft_listing_product,
  delete_listing, get_listing, get_listing_inventory,
  update_listing_inventory, update_listing_property). Producer-staged
  by integration-drafts; consumer-side audit applied 1 patch before merge.
- `segment` integration — 6 actions, auth: api_key. Customer data
  platform for collecting and routing user analytics via the Segment
  Tracking API (alias, group, identify, page, screen, track).
  Producer-staged by integration-drafts; consumer-side audit applied
  1 patch before merge.
- `mintlify` integration — 3 actions, auth: custom. Documentation platform
  with AI-powered assistant, semantic search, and project update triggers
  (chat_with_assistant, search_documentation, trigger_update). Producer-staged
  by integration-drafts; consumer-side audit applied 2 patches before merge.
- `google_tasks` integration — 8 actions, auth: oauth2. Manage tasks and
  task lists using the Google Tasks API (create_task, create_task_list,
  delete_task, delete_task_list, list_tasks, list_task_lists, update_task,
  update_task_list). Producer-staged by integration-drafts; consumer-side
  audit applied 2 patches before merge.
- `ahrefs` integration — 3 actions, auth: oauth2. SEO backlink analysis
  and referring domain data via the Ahrefs REST API v3 (get_backlinks,
  get_backlinks_one_per_domain, get_referring_domains). Producer-staged
  by integration-drafts; consumer-side audit applied 5 patches before merge.
- `algolia` integration — 4 actions, auth: api_key. Search and indexing
  platform (browse_records, delete_records, list_index_name_options,
  save_records) via the Algolia REST API. Producer-staged by
  integration-drafts; consumer-side audit applied 1 patch before merge.
- `pipedrive` integration — 26 actions, auth: oauth2. Sales CRM and
  pipeline management: deals, contacts, leads, activities, notes,
  organizations, labels, and search. Producer-staged by
  integration-drafts; consumer-side audit applied 6 patches before merge.
- `google_ads` integration — 10 actions, auth: oauth2. Google Ads API
  integration: GAQL reports across Campaigns, Ad Groups, Ads, and
  Customers; Customer Match list management; offline conversion uploads;
  keyword idea generation. Producer-staged by integration-drafts;
  consumer-side audit applied 2 patches before merge.
- `mixpanel` integration — 1 action, auth: api_key. Product analytics
  platform for tracking user events via the Mixpanel /track API
  (emit_event_to). Producer-staged by integration-drafts; consumer-side
  audit applied 1 patch before merge.
- `google_contacts` integration — 6 actions, auth: oauth2. Manage Google
  People (Contacts) via the People API v1 (create_contact, delete_contact,
  get_contact, list_contacts, list_directory_contacts, update_contact).
  Producer-staged by integration-drafts; consumer-side audit applied
  2 patches before merge.
- `google_search_console` integration — 2 actions, auth: oauth2. Access
  Google Search Console search analytics and submit URLs for indexing via
  the Search Console and Indexing APIs (retrieve_site_performance_data,
  submit_url_for_indexing). Producer-staged by integration-drafts;
  consumer-side audit applied 4 patches before merge.
- `google_forms` integration — 6 actions, auth: oauth2. Create, update,
  and read Google Forms and their responses via the Google Forms API
  (create_form, create_text_question, get_form, get_form_response,
  list_form_responses, update_form_title). Producer-staged by
  integration-drafts; consumer-side audit applied 2 patches before merge.
- `google_my_business` integration — 6 actions, auth: oauth2. Manage
  Google Business Profile posts, reviews, and replies via the Google My
  Business API (create_post, create_update_reply_to_review,
  get_reviews_multiple_locations, get_specific_review, list_all_reviews,
  list_posts). Producer-staged by integration-drafts; consumer-side audit
  applied 3 patches before merge.
- `google_merchant_center` integration — 2 actions, auth: oauth2. Manage
  product listings in Google Merchant Center via the Shopping Content API
  (create_product, update_product). Producer-staged by integration-drafts;
  consumer-side audit applied 5 patches before merge.
- `google_maps_platform` integration — 2 actions, auth: api_key. Search for
  places and retrieve place details using the Google Places API (New)
  (search_places, get_place_details). Producer-staged by integration-drafts;
  consumer-side audit applied 1 patch before merge.
- `google_ad_manager` integration — 2 actions, auth: oauth2. Programmatic
  advertising platform for managing ad inventory and reporting via the
  Google Ad Manager API (create_report, list_network_options).
  Producer-staged by integration-drafts; consumer-side audit applied
  4 patches before merge.
- `google_docs` integration — 12 actions, auth: oauth2. Create, read, and
  edit Google Docs documents via the Google Docs API (append_image,
  append_text, create_document, create_document_from_template, find_document,
  get_document, get_tab_content, insert_page_break, insert_table, insert_text,
  replace_image, replace_text). Producer-staged by integration-drafts;
  consumer-side audit applied 3 patches before merge.
- `crunchbase` integration — 2 actions, auth: api_key. Access Crunchbase
  company and organization data for business intelligence and research
  (get_organization, search_organizations) via the Crunchbase REST API v4.
  Producer-staged by integration-drafts; consumer-side audit applied
  1 patch before merge.
- `google_appsheet` integration — 4 actions, auth: api_key. Manage rows
  in Google AppSheet tables (add_row, delete_row, get_rows, update_row)
  via the AppSheet API. Producer-staged by integration-drafts;
  consumer-side audit applied 1 patch before merge.
- `bloomerang` integration — 3 actions, auth: api_key. Nonprofit donor
  management and fundraising CRM platform for creating constituents,
  donations, and interactions via the Bloomerang REST API v2.
  Producer-staged by integration-drafts; consumer-side audit applied
  1 patch before merge.
- `google_cloud` integration — 11 actions, auth: custom (service account key).
  Google Cloud Platform services including Cloud Storage, BigQuery, Compute
  Engine, and Cloud Logging via GCP REST APIs. Producer-staged by
  integration-drafts; consumer-side audit applied 3 patches before merge.
- `hootsuite` integration — 4 actions, auth: oauth2. Social media management
  platform for scheduling posts, uploading media, and managing social profiles
  via the Hootsuite REST API. Producer-staged by integration-drafts;
  consumer-side audit applied 6 patches before merge.
- `apify` integration — 7 actions, auth: bearer_token. Web scraping,
  automation, and data extraction platform via the Apify REST API.
  Producer-staged by integration-drafts; consumer-side audit applied
  9 patches before merge.
- `databricks` integration — 41 actions, auth: custom (personal access token).
  Manage Databricks jobs, runs, SQL warehouses, and vector search indexes.
  Producer-staged by integration-drafts; consumer-side audit applied 4 patches
  before merge.
- `sentry` integration — 4 actions (list_issue_events, list_project_events,
  list_project_issues, update_issue), auth: bearer_token. Error tracking and
  performance monitoring platform via the Sentry REST API. Producer-staged
  by integration-drafts; consumer-side audit applied 6 patches before merge.
- `google_workspace` integration — 4 actions (list_activities_by_admin,
  list_activities_by_event_and_admin, list_activities_by_event_name,
  list_all_activities), auth: oauth2. Retrieve admin audit activity
  reports from Google Workspace via the Admin SDK Reports API.
  Producer-staged by integration-drafts; consumer-side audit applied
  2 patches before merge.
- `postman` integration — 4 actions (create_environment,
  list_workspace_id_options, run_monitor, update_variable), auth:
  api_key. API development and testing platform for building, monitoring,
  and managing APIs via the Postman REST API. Producer-staged by
  integration-drafts; consumer-side audit applied 2 patches before merge.
- `supabase` integration — 8 actions (select_row, insert_row, update_row,
  delete_row, batch_insert_rows, remote_procedure_call, count_rows,
  upsert_row), auth: api_key. Open-source Firebase alternative providing
  Postgres database operations via the Supabase REST API. Producer-staged
  by integration-drafts; consumer-side audit applied 2 patches before merge.
- `canva` integration — 5 actions, auth: oauth2. Design platform for
  creating, importing, exporting, listing, and uploading assets via the
  Canva Connect REST API. Producer-staged by integration-drafts;
  consumer-side audit applied 1 patch before merge.
- `medium` integration — 1 action, auth: oauth2. Publish posts to Medium
  via the Medium REST API. Producer-staged by integration-drafts;
  consumer-side audit applied 3 patches before merge.
- `digital_ocean` integration — 6 actions, auth: oauth2. Cloud
  infrastructure platform for deploying and managing Droplets, domains,
  and SSH keys via the DigitalOcean API. Producer-staged by
  integration-drafts; consumer-side audit applied 3 patches before merge.
- `godaddy` integration — 5 actions, auth: custom (API Key + Secret).
  Domain registration, availability checking, and management via the
  GoDaddy API. Producer-staged by integration-drafts; consumer-side audit
  applied 2 patches before merge.
- `gitlab` integration — 12 actions, auth: oauth2. GitLab repository and
  project management platform: branches, issues, epics, commits, groups,
  and members via the REST v4 API. Producer-staged by integration-drafts;
  consumer-side audit applied 2 patches before merge.
- `mailgun` integration — 9 actions (send_email, verify_email,
  create_mailinglist_member, create_route, delete_mailinglist_member,
  list_domains, list_mailinglist_members, retrieve_mailinglist_member,
  suppress_email), auth: api_key. Transactional email API for sending,
  receiving, and tracking email via the Mailgun REST API. Producer-staged
  by integration-drafts; consumer-side audit applied 2 patches before merge.
- `google_tag_manager` integration — 6 actions, auth: oauth2. Manage tags,
  variables, and workspaces in Google Tag Manager containers via the Tag
  Manager v2 REST API. Producer-staged by integration-drafts; consumer-side
  audit applied 1 patch before merge.
- `google_analytics` integration — 6 actions, auth: oauth2. Manage Google
  Analytics 4 properties, list accounts, configure key events, and run
  analytics reports via the Admin and Data APIs. Producer-staged by
  integration-drafts; consumer-side audit applied 2 patches before merge.
- `docusign` integration — 12 actions, auth: oauth2. Electronic signature and
  agreement management via the DocuSign eSignature REST API. Producer-staged by
  integration-drafts; consumer-side audit applied 3 patches before merge.
- `twilio` integration — 17 actions, auth: custom (Account SID + Auth Token).
  Cloud communications platform for SMS, voice calls, phone number lookup,
  and verification via the Twilio REST API. Producer-staged by
  integration-drafts; consumer-side audit applied 2 patches before merge.
- `aws` integration — 21 actions, auth: custom (access key + secret).
  Interact with AWS services including DynamoDB, S3, Lambda, SNS, SQS,
  EventBridge, CloudWatch Logs, and Redshift via the boto3 SDK.
  Producer-staged by integration-drafts; consumer-side audit applied
  7 patches before merge (2 risky-semantic skipped for human review).
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

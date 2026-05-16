---
name: Integration request
about: Propose a new third-party service to integrate as a tool
title: "[integration] add support for <service name>"
labels: integration-request
assignees: ''
---

## Service

<!-- Name and homepage URL of the service to integrate. -->

## Why this integration

<!-- 1–3 sentences: what AI use case does this unlock? -->

## API documentation

<!-- Direct URL to the relevant API reference. -->

## Authentication

- Auth method(s) the API supports: <!-- oauth2 / bearer token / api key / signed requests / etc. -->
- Where users get credentials (URL to docs):
- OAuth scopes required (if applicable):

## Expected actions

<!--
List the actions (LangChain @tools) this integration should expose
in the first cut. Keep it tight — start with 3–8 high-value actions,
add more in follow-ups.
-->

- `<action_name>` — <!-- 1-line description -->
- ...

## Rate limits & quotas

<!-- Documented per-token / per-app limits, if any. -->

## SDK vs. raw HTTP

<!--
Is there a vendor-maintained Python SDK we'd use, or do we hit the
HTTP API directly with httpx? If a SDK, name + PyPI link.
-->

## Maintainership

<!--
Are you volunteering to maintain this integration after it lands?
"Yes / No / would help if mentored" is fine.
-->

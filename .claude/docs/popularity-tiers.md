# Popularity tiers — preselector scoring input

> Consumed by `integration-preselector` to break ties among
> structurally-ready candidates. **Curated, not algorithmic.** Adjust freely
> as priorities shift; the preselector re-reads this file every run.

The preselector's final score is roughly:

```
score = (tier_points)              # this file
      + (verifier_quality × 50)    # P / (P+F+D) from NOTES.md
      + (drift_cleanliness × 20)   # 1.0 if no extra="allow"/f-string-graphql, else 0.0
      + (log10(action_count) × 5)  # more actions = more LLM surface area
```

Tie-breaker: alphabetical (deterministic across runs).

---

## Tier 1 — high priority (40 points)

These are integrations where ModuleX users have explicit demand or which
fill a "must-have" category. Pick from this tier first.

- `monday` — project management / work tracker (high LLM demand)
- `microsoft_teams` — comms (paired with Microsoft Outlook)
- `microsoft_outlook` — email + calendar (the "Microsoft Workspace" anchor)
- `google_calendar` — scheduling (the "Google Workspace" anchor)
- `microsoft_excel` — spreadsheets (paired with google_sheets)
- `jira` — issue tracking (when staged)
- `asana` — project management (when staged)
- `stripe` — payments (when staged)
- `zoom` — video conferencing (when staged)
- `discord` — comms (when staged)

## Tier 2 — medium priority (20 points)

Useful but not blocking. Pick after Tier 1 candidates are merged or
unavailable.

- `okta` — identity / access management
- `microsoft_onedrive` — file storage (paired with google_drive)
- `microsoft_bookings` — scheduling
- `google_sheets` — spreadsheets (paired with microsoft_excel)
- `google_slides` — presentations
- `google_meet` — video conferencing (paired with zoom)
- `dropbox` — file storage (when staged)
- `box` — file storage (when staged)
- `quickbooks` — accounting (when staged)
- `xero_accounting_api` — accounting (when staged)

## Tier 3 — low priority (5 points)

Niche, marketing, or low-demand. Pick last unless Tier 1/2 are exhausted.

- `google_ads` — paid ads
- `google_analytics` — web analytics
- `google_contacts` — CRM-lite
- `google_forms` — form builder
- `microsoft_advertising` — paid ads (when staged)
- `linkedin_ads` — paid ads (when staged)
- `facebook_marketing` — paid ads (when staged)

## Tier 0 — explicit skip (-100 points)

Block-list. The preselector will refuse these even if staged.

- `upstream` — circular reference; the source itself
- `pipeline` — generic / ambiguous
- Anything where `unsupported_signals[]` was non-empty in the producer's NOTES (OAuth 1.0a, sources-only).

---

## Default tier (10 points)

Anything not listed above. The preselector treats unknown names as
medium-low priority — picks them when nothing higher-scoring is ready.

---

## How to update this file

1. Add the integration name to the appropriate tier (or remove if shifting).
2. Commit the change with a short rationale (`adjust popularity-tiers: bump
   <name> to Tier 1, user demand from <source>`).
3. The next cron run picks up the change without any further coordination.

---

## What this file is NOT

- Not an availability list. The preselector also checks the producer's
  staging area; a tier-1 name that's not staged yet just won't be picked.
- Not an integration roadmap. This is a **tiebreaker**, not a release plan.
- Not exposed to end users. Internal-only; reflects internal sequencing.

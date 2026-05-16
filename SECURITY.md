# Security policy

We take security issues in `modulex-integrations` seriously. This
package ships credential schemas and HTTP/SDK calls to third-party
services, so a bug here can compromise downstream users' tokens.

## Please do NOT file public issues for vulnerabilities

If you believe you have found a security vulnerability — credential
leak, auth bypass, injection into upstream API calls, dependency
CVE, anything that affects confidentiality, integrity, or availability
of downstream installations — **do not open a GitHub issue or PR**.

## How to report

Choose either channel:

1. **Email** — write to `contact@modulex.dev`. Include a clear
   description, reproduction steps, the affected integration(s) and
   version, and any logs or PoC you have (with credentials redacted).
2. **GitHub Security Advisories** — open a private advisory at
   <https://github.com/ModuleXAI/modulex-integrations/security/advisories/new>.

If you do not get a response within 5 business days, please follow
up — your report may have been lost.

## What to expect

- We aim to acknowledge new reports within **5 business days**.
- We will work with you privately on a fix and a disclosure timeline.
- Once a patched release is available we credit reporters in the
  release notes unless you ask to remain anonymous.

## Supported versions

| Version | Supported |
| ------- | --------- |
| `0.x`   | Yes — current pre-1.0 development line |

Once a `1.0` release is cut, this table will be updated to reflect
the active maintenance windows.

## Supported Python versions

CI runs against Python 3.12 and 3.13. Security fixes are produced
for both.

## Out of scope

- Vulnerabilities in upstream third-party APIs we integrate with —
  please report those to the relevant vendor.
- Issues that only affect example code or test fixtures.
- Findings that require an attacker to already have full
  filesystem-level access to the running modulex instance.

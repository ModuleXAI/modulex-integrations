# Releasing modulex-integrations

This document is the single source of truth for the release process.
If a step here disagrees with what CI does, CI wins — fix the doc.

## Mental model

```
                modulex-integrations          modulex (consumer)
                ────────────────────          ──────────────────
    staging  →  v0.X.YaN  (pre-release)  →    staging  (pins ==0.X.YaN)
       │          │                              │
    promote     promote                        promote
       ↓          ↓                              ↓
       main   →  v0.X.Y    (stable)        →    main / prod  (pins ==0.X.Y)
```

- **Pre-release** versions (`v0.X.YaN`, `v0.X.YbN`, `v0.X.YrcN`,
  `v0.X.Y.devN`) are tagged from the `staging` branch of this repo.
  They are published to PyPI as PEP 440 pre-releases — `pip install`
  ignores them unless `--pre` or an exact pin asks for them.
- **Stable** versions (`v0.X.Y`, `v0.X.Y.postN`) are tagged from the
  `main` branch of this repo. They are normal PyPI releases.

The release workflow (`.github/workflows/release.yml`) enforces these
rules at publish time. A stable tag that is not reachable from `main`,
or a pre-release tag that is not reachable from `staging`, fails the
build job before anything is uploaded.

## One-time setup (do these once per fresh checkout)

### 1. Configure the PyPI Trusted Publisher

Trusted Publishing replaces long-lived API tokens with short-lived OIDC
exchanges from GitHub Actions to PyPI. You must register the publisher
on PyPI **before** the first release.

If the project does not yet exist on PyPI:

1. Go to <https://pypi.org/manage/account/publishing/> while signed in
   as a project owner.
2. Add a **Pending Publisher** with:
   - **PyPI Project Name:** `modulex-integrations`
   - **Owner:** `ModuleXAI`
   - **Repository name:** `modulex-integrations`
   - **Workflow filename:** `release.yml`
   - **Environment name:** `release-pypi`
3. The first successful run of `release.yml` will both create the
   project on PyPI and consume the pending publisher.

If the project already exists, skip the pending step and add the
publisher directly under **Manage project → Publishing → Add a
trusted publisher** using the same four fields above.

### 2. Create the `release-pypi` GitHub environment

On GitHub:

1. Go to **Settings → Environments → New environment**.
2. Name it `release-pypi`.
3. (Recommended) Add a **Required reviewers** rule listing the people
   allowed to approve releases. Every release will then wait for an
   approval before the publish job runs.
4. (Recommended) Restrict the environment to the `main` and `staging`
   branches and any `v*` tags so the credential can't be exfiltrated
   from a feature branch.

## Cutting a release

### Pre-release from `staging`

When the next batch of work on `staging` is ready to ship to the
modulex staging environment:

```bash
git checkout staging
git pull --ff-only
git tag v0.2.0a1                  # bump aN within the same target version
git push origin v0.2.0a1
```

The workflow will:

1. Verify the tag matches PEP 440.
2. Verify `v0.2.0a1`'s commit is on `origin/staging`.
3. Build sdist + wheel with `hatch-vcs` → version `0.2.0a1`.
4. Wait for `release-pypi` environment approval (if configured).
5. Publish to PyPI via OIDC.

### Stable release from `main`

Once `staging` has been promoted to `main` (the version was validated
in modulex staging long enough to trust it):

```bash
git checkout main
git pull --ff-only
git tag v0.2.0                    # the stable version that corresponds
git push origin v0.2.0
```

Same workflow, but with the `main` guard. Output is a normal PyPI
release.

### Bumping the next version

There is no central "current version" file — `hatch-vcs` reads the
latest tag. To plan the next version:

- **Patch** (bug fix in a tool): `v0.2.0` → `v0.2.1`
- **Minor** (new integration, additive change to an existing one):
  `v0.2.0` → `v0.3.0`
- **Major** (breaking change to the manifest contract or schema):
  `v0.2.0` → `v1.0.0`

Pre-release counter (`aN`) increments per push to staging:
`v0.3.0a1`, `v0.3.0a2`, …, until graduation to `v0.3.0` stable.

## modulex-side pinning policy

The modulex runtime declares `modulex-integrations` as a hard
dependency in `py/pyproject.toml`. The pin differs by branch:

| modulex branch | pins | example |
| --- | --- | --- |
| `main` | latest stable | `modulex-integrations==0.2.0` |
| `prod` | latest stable | `modulex-integrations==0.2.0` |
| `staging` | latest pre-release | `modulex-integrations==0.3.0a1` |
| `dev` | usually = staging | `modulex-integrations==0.3.0a1` |

### Bump flow

1. Tag a pre-release here (`v0.3.0a1`) — pushed to PyPI.
2. In modulex: open a PR to `staging` that updates the pin to
   `==0.3.0a1`, runs the test suite, deploys to modulex staging.
3. Once validated, tag stable here (`v0.3.0`) — pushed to PyPI.
4. In modulex: open a PR to `main` (and `prod`) that updates the pin
   to `==0.3.0`. Merge as part of the normal release promotion.

The pin lives in modulex/py/pyproject.toml's `dependencies` list. Do
not use range specifiers (`>=`) on the modulex side — we want exact,
reproducible installs.

### Why exact pins

The runtime imports integrations via the `modulex.tools` entry-point
group, so any version of modulex-integrations that contributes the
expected entry points will load. But the *shape* of the manifest
contract (the pydantic schema in `modulex_integrations.schema`) can
shift between minor versions, and `extra="forbid"` means a stale
runtime crashes on import. Exact pins prevent surprise.

## Failure modes (and what to do)

### "tag points at commit X, which is not reachable from origin/main"

You tagged from the wrong branch. Either move the tag (if the right
commit is also on main):

```bash
git tag -d v0.2.0
git push --delete origin v0.2.0
git checkout main && git pull
git tag v0.2.0
git push origin v0.2.0
```

…or rethink whether you meant a pre-release tag from `staging`.

### "tag '...' is not a PEP 440 version"

The regex in `release.yml` rejects anything that isn't
`vX.Y.Z[aN|bN|rcN|.devN|.postN]`. Re-tag with a compliant version.

### Trusted Publisher rejects with `invalid-publisher`

The publisher config on PyPI does not match what the workflow is
sending. Check that all four fields (owner, repo, workflow filename,
environment name) on pypi.org agree with this workflow file and the
GitHub environment.

### Built wheel does not carry the expected version

`hatch-vcs` failed to read the tag. The most common cause is a
shallow checkout — make sure `fetch-depth: 0` is set on the
`actions/checkout` step (it is, in this workflow).

## When *not* to cut a release

- Pure documentation changes that don't touch the package, manifests,
  or any tool code — push to the relevant branch but don't tag.
- CI/workflow changes — same.
- Refactoring with no behavior change — bundle into the next planned
  release.

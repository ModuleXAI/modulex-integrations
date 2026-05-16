"""Happy-path tests for every github @tool, plus a manifest sanity check.

Uses pytest-httpx's ``httpx_mock`` fixture (which patches httpx at the
transport level — same underlying mechanism as ``httpx.MockTransport``,
just with a cleaner per-test API).

Every test wires a fake GitHub API response, invokes the tool with a
bearer-token credential, then asserts:

1. The result validates as the typed pydantic output model.
2. A handful of representative fields are populated from the mocked
   response (proves the field-mapping in tools.py is correct).
"""
from __future__ import annotations

import base64
from typing import Any

import pytest

from modulex_integrations.tools.github import (
    TOOLS,
    create_branch,
    create_commit,
    create_issue,
    create_pull_request,
    create_repository,
    delete_repository,
    get_file_content,
    get_issue,
    get_pull_request,
    get_repository,
    list_issues,
    list_pull_requests,
    list_repositories,
    manifest,
    merge_pull_request,
    search_code,
    update_issue,
)
from modulex_integrations.tools.github.outputs import (
    CreateBranchOutput,
    CreateCommitOutput,
    CreateIssueOutput,
    CreatePullRequestOutput,
    CreateRepositoryOutput,
    DeleteRepositoryOutput,
    GetFileContentOutput,
    GetIssueOutput,
    GetPullRequestOutput,
    GetRepositoryOutput,
    ListIssuesOutput,
    ListPullRequestsOutput,
    ListRepositoriesOutput,
    MergePullRequestOutput,
    SearchCodeOutput,
    UpdateIssueOutput,
)

API = "https://api.github.com"

# Shared bearer-token credential used by every test.
# Annotated as ``dict[str, Any]`` so mypy doesn't try to fit it into
# LangChain's typed StructuredTool.ainvoke input overload.
_AUTH: dict[str, Any] = {
    "auth_type": "bearer_token",
    "auth_data": {"token": "ghp_fake_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: bearer auth + per-test extras.

    Uses ``dict(..., **kwargs)`` instead of ``{**_AUTH, **extra}`` to
    avoid mypy's TypedDict-spread check on LangChain's typed ainvoke
    overloads.
    """
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_16_actions(self) -> None:
        assert len(manifest.actions) == 16

    def test_manifest_actions_match_tools_tuple(self) -> None:
        manifest_action_names = {a.name for a in manifest.actions}
        tool_names = {t.name for t in TOOLS}
        assert manifest_action_names == tool_names

    def test_manifest_has_oauth2_and_bearer_token_auth(self) -> None:
        auth_types = {a.auth_type for a in manifest.auth_schemas}
        assert auth_types == {"oauth2", "bearer_token"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_list_repositories(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/user/repos?visibility=all&affiliation=owner%2Ccollaborator%2Corganization_member&sort=full_name&direction=asc&per_page=30&page=1",
        json=[
            {
                "id": 1,
                "name": "repo-a",
                "full_name": "alice/repo-a",
                "description": "first",
                "private": False,
                "html_url": "https://github.com/alice/repo-a",
                "clone_url": "https://github.com/alice/repo-a.git",
                "ssh_url": "git@github.com:alice/repo-a.git",
                "language": "Python",
                "stargazers_count": 42,
                "forks_count": 3,
                "open_issues_count": 1,
                "default_branch": "main",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-02-01T00:00:00Z",
            }
        ],
    )

    result = await list_repositories.ainvoke(_AUTH)

    assert isinstance(result, ListRepositoriesOutput)
    assert result.success is True
    assert result.total == 1
    assert result.repositories[0].full_name == "alice/repo-a"
    assert result.repositories[0].stars == 42
    # Bearer token reached the GitHub API
    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer ghp_fake_token"
    assert sent.headers["X-GitHub-Api-Version"] == "2022-11-28"


@pytest.mark.asyncio
async def test_create_repository(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/user/repos",
        json={
            "id": 100,
            "name": "new-repo",
            "full_name": "alice/new-repo",
            "html_url": "https://github.com/alice/new-repo",
            "clone_url": "https://github.com/alice/new-repo.git",
            "private": True,
            "default_branch": "main",
        },
        status_code=201,
    )

    result = await create_repository.ainvoke(_args(name="new-repo", private=True))

    assert isinstance(result, CreateRepositoryOutput)
    assert result.success is True
    assert result.repository.full_name == "alice/new-repo"
    assert result.repository.owner == "alice"
    assert result.repository.private is True


@pytest.mark.asyncio
async def test_delete_repository(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/repos/alice/old-repo",
        status_code=204,
    )

    result = await delete_repository.ainvoke(_args(owner="alice", repo="old-repo"))

    assert isinstance(result, DeleteRepositoryOutput)
    assert result.success is True
    assert "alice/old-repo" in result.message


@pytest.mark.asyncio
async def test_get_repository(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/alice/repo-a",
        json={
            "id": 1,
            "name": "repo-a",
            "full_name": "alice/repo-a",
            "description": "first",
            "private": False,
            "html_url": "https://github.com/alice/repo-a",
            "clone_url": "https://github.com/alice/repo-a.git",
            "ssh_url": "git@github.com:alice/repo-a.git",
            "language": "Python",
            "stargazers_count": 42,
            "forks_count": 3,
            "watchers_count": 7,
            "open_issues_count": 1,
            "default_branch": "main",
            "topics": ["ai", "tools"],
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-02-01T00:00:00Z",
            "pushed_at": "2025-02-01T00:00:00Z",
        },
    )

    result = await get_repository.ainvoke(_args(owner="alice", repo="repo-a"))

    assert isinstance(result, GetRepositoryOutput)
    assert result.success is True
    assert result.repository.watchers == 7
    assert result.repository.topics == ["ai", "tools"]


@pytest.mark.asyncio
async def test_list_issues(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/alice/repo-a/issues?state=open&sort=created&direction=desc&per_page=30&page=1",
        json=[
            {
                "number": 7,
                "title": "bug: thing",
                "body": "details",
                "state": "open",
                "html_url": "https://github.com/alice/repo-a/issues/7",
                "user": {"login": "bob"},
                "labels": [{"name": "bug"}, {"name": "p0"}],
                "assignees": [{"login": "alice"}],
                "created_at": "2025-03-01T00:00:00Z",
                "updated_at": "2025-03-02T00:00:00Z",
                "closed_at": None,
                "comments": 4,
            }
        ],
    )

    result = await list_issues.ainvoke(_args(owner="alice", repo="repo-a"))

    assert isinstance(result, ListIssuesOutput)
    assert result.issues[0].labels == ["bug", "p0"]
    assert result.issues[0].assignees == ["alice"]
    assert result.issues[0].user == "bob"


@pytest.mark.asyncio
async def test_create_issue(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/repos/alice/repo-a/issues",
        json={
            "number": 11,
            "title": "new",
            "body": "body",
            "state": "open",
            "html_url": "https://github.com/alice/repo-a/issues/11",
            "created_at": "2025-04-01T00:00:00Z",
        },
        status_code=201,
    )

    result = await create_issue.ainvoke(
        _args(owner="alice", repo="repo-a", title="new", body="body")
    )

    assert isinstance(result, CreateIssueOutput)
    assert result.issue.number == 11
    assert result.issue.url == "https://github.com/alice/repo-a/issues/11"


@pytest.mark.asyncio
async def test_get_issue(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/alice/repo-a/issues/7",
        json={
            "number": 7,
            "title": "bug",
            "body": "details",
            "state": "open",
            "html_url": "https://github.com/alice/repo-a/issues/7",
            "user": {"login": "bob"},
            "labels": [{"name": "bug"}],
            "assignees": [],
            "created_at": "2025-03-01T00:00:00Z",
            "updated_at": "2025-03-02T00:00:00Z",
            "closed_at": None,
            "comments": 0,
        },
    )

    result = await get_issue.ainvoke(
        _args(owner="alice", repo="repo-a", issue_number=7)
    )

    assert isinstance(result, GetIssueOutput)
    assert result.issue.number == 7
    assert result.issue.user == "bob"
    assert result.issue.labels == ["bug"]
    assert result.issue.assignees == []


@pytest.mark.asyncio
async def test_update_issue(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/repos/alice/repo-a/issues/7",
        json={
            "number": 7,
            "title": "renamed",
            "body": "fresh",
            "state": "closed",
            "html_url": "https://github.com/alice/repo-a/issues/7",
            "updated_at": "2025-03-03T00:00:00Z",
        },
    )

    result = await update_issue.ainvoke(
        _args(
            owner="alice",
            repo="repo-a",
            issue_number=7,
            title="renamed",
            state="closed",
        )
    )

    assert isinstance(result, UpdateIssueOutput)
    assert result.issue.state == "closed"
    assert result.issue.title == "renamed"


@pytest.mark.asyncio
async def test_list_pull_requests(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/alice/repo-a/pulls?state=open&sort=created&direction=desc&per_page=30&page=1",
        json=[
            {
                "number": 3,
                "title": "feat: x",
                "body": "implements x",
                "state": "open",
                "html_url": "https://github.com/alice/repo-a/pull/3",
                "user": {"login": "carol"},
                "head": {"ref": "feature/x"},
                "base": {"ref": "main"},
                "draft": False,
                "mergeable": None,
                "created_at": "2025-05-01T00:00:00Z",
                "updated_at": "2025-05-02T00:00:00Z",
                "merged_at": None,
                "closed_at": None,
            }
        ],
    )

    result = await list_pull_requests.ainvoke(_args(owner="alice", repo="repo-a"))

    assert isinstance(result, ListPullRequestsOutput)
    assert result.pull_requests[0].head == "feature/x"
    assert result.pull_requests[0].base == "main"


@pytest.mark.asyncio
async def test_create_pull_request(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/repos/alice/repo-a/pulls",
        json={
            "number": 9,
            "title": "feat: y",
            "body": "implements y",
            "state": "open",
            "html_url": "https://github.com/alice/repo-a/pull/9",
            "head": {"ref": "feature/y"},
            "base": {"ref": "main"},
            "draft": False,
            "created_at": "2025-06-01T00:00:00Z",
        },
        status_code=201,
    )

    result = await create_pull_request.ainvoke(
        _args(
            owner="alice",
            repo="repo-a",
            title="feat: y",
            head="feature/y",
            base="main",
            body="implements y",
        )
    )

    assert isinstance(result, CreatePullRequestOutput)
    assert result.pull_request.number == 9
    assert result.pull_request.head == "feature/y"


@pytest.mark.asyncio
async def test_get_pull_request(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/alice/repo-a/pulls/3",
        json={
            "number": 3,
            "title": "feat: x",
            "body": "implements x",
            "state": "open",
            "html_url": "https://github.com/alice/repo-a/pull/3",
            "user": {"login": "carol"},
            "head": {"ref": "feature/x"},
            "base": {"ref": "main"},
            "draft": False,
            "mergeable": True,
            "merged": False,
            "created_at": "2025-05-01T00:00:00Z",
            "updated_at": "2025-05-02T00:00:00Z",
            "merged_at": None,
            "closed_at": None,
            "commits": 3,
            "additions": 100,
            "deletions": 12,
            "changed_files": 5,
        },
    )

    result = await get_pull_request.ainvoke(
        _args(owner="alice", repo="repo-a", pull_number=3)
    )

    assert isinstance(result, GetPullRequestOutput)
    assert result.pull_request.commits == 3
    assert result.pull_request.changed_files == 5
    assert result.pull_request.mergeable is True


@pytest.mark.asyncio
async def test_merge_pull_request(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/repos/alice/repo-a/pulls/3/merge",
        json={
            "merged": True,
            "message": "Pull Request successfully merged",
            "sha": "deadbeef0001",
        },
    )

    result = await merge_pull_request.ainvoke(
        _args(owner="alice", repo="repo-a", pull_number=3, merge_method="squash")
    )

    assert isinstance(result, MergePullRequestOutput)
    assert result.merged is True
    assert result.sha == "deadbeef0001"


@pytest.mark.asyncio
async def test_create_branch(httpx_mock):  # type: ignore[no-untyped-def]
    # 1) get base branch ref
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/alice/repo-a/git/ref/heads/main",
        json={"ref": "refs/heads/main", "object": {"sha": "cafef00d0001"}},
    )
    # 2) create new branch ref
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/repos/alice/repo-a/git/refs",
        json={
            "ref": "refs/heads/feature/new",
            "object": {"sha": "cafef00d0001"},
        },
        status_code=201,
    )

    result = await create_branch.ainvoke(
        _args(owner="alice", repo="repo-a", branch_name="feature/new")
    )

    assert isinstance(result, CreateBranchOutput)
    assert result.branch.name == "feature/new"
    assert result.branch.sha == "cafef00d0001"


@pytest.mark.asyncio
async def test_get_file_content(httpx_mock):  # type: ignore[no-untyped-def]
    raw = "print('hello')\n"
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/alice/repo-a/contents/src/main.py",
        json={
            "name": "main.py",
            "path": "src/main.py",
            "size": len(raw),
            "content": base64.b64encode(raw.encode()).decode(),
            "sha": "filesha001",
            "download_url": "https://raw.githubusercontent.com/alice/repo-a/main/src/main.py",
        },
    )

    result = await get_file_content.ainvoke(
        _args(owner="alice", repo="repo-a", path="src/main.py")
    )

    assert isinstance(result, GetFileContentOutput)
    assert result.file.path == "src/main.py"
    assert result.file.content == raw  # base64 was decoded for us


@pytest.mark.asyncio
async def test_create_commit(httpx_mock):  # type: ignore[no-untyped-def]
    branch = "main"
    base_sha = "basebase0001"
    base_tree_sha = "treebase0001"
    blob_sha = "blob0001"
    new_tree_sha = "tree0001"
    new_commit_sha = "commit0001"

    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/alice/repo-a/git/ref/heads/{branch}",
        json={"ref": f"refs/heads/{branch}", "object": {"sha": base_sha}},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/alice/repo-a/git/commits/{base_sha}",
        json={"sha": base_sha, "tree": {"sha": base_tree_sha}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/repos/alice/repo-a/git/blobs",
        json={"sha": blob_sha},
        status_code=201,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/repos/alice/repo-a/git/trees",
        json={"sha": new_tree_sha},
        status_code=201,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/repos/alice/repo-a/git/commits",
        json={"sha": new_commit_sha},
        status_code=201,
    )
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/repos/alice/repo-a/git/refs/heads/{branch}",
        json={"ref": f"refs/heads/{branch}", "object": {"sha": new_commit_sha}},
    )

    result = await create_commit.ainvoke(
        _args(
            owner="alice",
            repo="repo-a",
            branch=branch,
            message="ci: tweak",
            files=[{"path": "README.md", "content": "hello"}],
        )
    )

    assert isinstance(result, CreateCommitOutput)
    assert result.commit.sha == new_commit_sha
    assert result.commit.message == "ci: tweak"
    assert result.commit.branch == branch


@pytest.mark.asyncio
async def test_search_code(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/search/code?q=hello+repo%3Aalice%2Frepo-a&order=desc&per_page=30&page=1",
        json={
            "total_count": 1,
            "items": [
                {
                    "name": "main.py",
                    "path": "src/main.py",
                    "repository": {"full_name": "alice/repo-a"},
                    "html_url": "https://github.com/alice/repo-a/blob/main/src/main.py",
                    "sha": "abc123",
                }
            ],
        },
    )

    result = await search_code.ainvoke(_args(query="hello repo:alice/repo-a"))

    assert isinstance(result, SearchCodeOutput)
    assert result.total_count == 1
    assert result.items[0].repository == "alice/repo-a"

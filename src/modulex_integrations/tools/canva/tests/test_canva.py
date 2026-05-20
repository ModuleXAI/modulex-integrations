"""Happy-path tests for every canva @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.canva import (
    TOOLS,
    create_design,
    create_design_import_job,
    export_design,
    list_designs,
    manifest,
    upload_asset,
)
from modulex_integrations.tools.canva.outputs import (
    CreateDesignImportJobOutput,
    CreateDesignOutput,
    ExportDesignOutput,
    ListDesignsOutput,
    UploadAssetOutput,
)

API = "https://api.canva.com/rest/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_5_actions(self) -> None:
        assert len(manifest.actions) == 5

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_design(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/designs",
        json={
            # TODO: fill in a representative response shape from the Canva API docs
            "design": {
                "id": "DAGLzABC123",
                "title": "My Design",
                "urls": {"edit_url": "https://www.canva.com/design/DAGLzABC123/edit"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        },
    )

    result_dict = await create_design.ainvoke(
        _args(design_type="preset", design_type_name="doc", title="My Design")
    )

    assert isinstance(result_dict, dict)
    result = CreateDesignOutput.model_validate(result_dict)
    assert result.success is True
    assert result.design is not None
    assert result.design.id == "DAGLzABC123"


@pytest.mark.asyncio
async def test_create_design_import_job(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/file.pdf",
        content=b"fake-file-content",
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/imports",
        json={
            # TODO: fill in a representative response shape from the Canva API docs
            "job": {
                "id": "job_123",
                "status": {"state": "completed", "design": {"id": "DAGLzABC456"}},
            },
        },
    )

    result_dict = await create_design_import_job.ainvoke(
        _args(title="Imported Design", file_url="https://example.com/file.pdf")
    )

    assert isinstance(result_dict, dict)
    result = CreateDesignImportJobOutput.model_validate(result_dict)
    assert result.success is True
    assert result.job is not None
    assert result.job.id == "job_123"


@pytest.mark.asyncio
async def test_export_design(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/exports",
        json={
            # TODO: fill in a representative response shape from the Canva API docs
            "job": {
                "id": "export_789",
                "status": "completed",
                "urls": ["https://export.canva.com/file1.pdf"],
            },
        },
    )

    result_dict = await export_design.ainvoke(
        _args(design_id="DAGLzABC123", format_type="pdf")
    )

    assert isinstance(result_dict, dict)
    result = ExportDesignOutput.model_validate(result_dict)
    assert result.success is True
    assert result.job is not None
    assert result.job.id == "export_789"


@pytest.mark.asyncio
async def test_list_designs(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/designs?ownership=any&sort_by=relevance&limit=25",
        json={
            # TODO: fill in a representative response shape from the Canva API docs
            "items": [
                {
                    "id": "DAGLzABC123",
                    "title": "My Design",
                    "urls": {"edit_url": "https://www.canva.com/design/DAGLzABC123/edit"},
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                },
            ],
            "continuation": None,
        },
    )

    result_dict = await list_designs.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListDesignsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 1
    assert result.items[0].id == "DAGLzABC123"


@pytest.mark.asyncio
async def test_upload_asset(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/image.png",
        content=b"fake-image-content",
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/asset-uploads",
        json={
            # TODO: fill in a representative response shape from the Canva API docs
            "job": {
                "id": "upload_456",
                "status": "completed",
                "asset": {"id": "asset_789", "name": "My Asset"},
            },
        },
    )

    result_dict = await upload_asset.ainvoke(
        _args(name="My Asset", file_url="https://example.com/image.png")
    )

    assert isinstance(result_dict, dict)
    result = UploadAssetOutput.model_validate(result_dict)
    assert result.success is True
    assert result.job is not None
    assert result.job.id == "upload_456"

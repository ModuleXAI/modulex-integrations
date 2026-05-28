"""Happy-path tests for every azure_storage @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.azure_storage import (
    TOOLS,
    create_container,
    delete_blob,
    list_containers,
    manifest,
    upload_blob,
)
from modulex_integrations.tools.azure_storage.outputs import (
    CreateContainerOutput,
    DeleteBlobOutput,
    ListContainersOutput,
    UploadBlobOutput,
)

_ACCOUNT = "teststorage"
_BASE = f"https://{_ACCOUNT}.blob.core.windows.net"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token", "storage_account_name": _ACCOUNT},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_4_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_container(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{_BASE}/mycontainer?restype=container",
        status_code=201,
    )

    result_dict = await create_container.ainvoke(_args(container_name="mycontainer"))

    assert isinstance(result_dict, dict)
    result = CreateContainerOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_blob(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{_BASE}/mycontainer/myblob.txt",
        status_code=202,
    )

    result_dict = await delete_blob.ainvoke(_args(container_name="mycontainer", blob_name="myblob.txt"))

    assert isinstance(result_dict, dict)
    result = DeleteBlobOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_containers(httpx_mock):  # type: ignore[no-untyped-def]
    xml_body = (
        '<?xml version="1.0" encoding="utf-8"?>'
        "<EnumerationResults>"
        "<Containers>"
        "<Container><Name>container1</Name></Container>"
        "<Container><Name>container2</Name></Container>"
        "</Containers>"
        "</EnumerationResults>"
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{_BASE}?comp=list",
        text=xml_body,
        status_code=200,
    )

    result_dict = await list_containers.ainvoke(_AUTH)

    assert isinstance(result_dict, dict)
    result = ListContainersOutput.model_validate(result_dict)
    assert result.success is True
    assert result.containers == ["container1", "container2"]


@pytest.mark.asyncio
async def test_upload_blob(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/file.txt",
        content=b"hello world",
        status_code=200,
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{_BASE}/mycontainer/file.txt",
        status_code=201,
    )

    result_dict = await upload_blob.ainvoke(
        _args(container_name="mycontainer", blob_name="file.txt", file_url="https://example.com/file.txt")
    )

    assert isinstance(result_dict, dict)
    result = UploadBlobOutput.model_validate(result_dict)
    assert result.success is True

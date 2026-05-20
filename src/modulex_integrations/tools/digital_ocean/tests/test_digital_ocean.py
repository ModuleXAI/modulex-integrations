"""Happy-path tests for every digital_ocean @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.digital_ocean import (
    TOOLS,
    add_ssh_key,
    create_domain,
    create_droplet,
    create_snapshot,
    list_all_droplets,
    manifest,
    turnonoff_droplet,
)
from modulex_integrations.tools.digital_ocean.outputs import (
    AddSshKeyOutput,
    CreateDomainOutput,
    CreateDropletOutput,
    CreateSnapshotOutput,
    ListAllDropletsOutput,
    TurnonoffDropletOutput,
)

API = "https://api.digitalocean.com/v2"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_6_actions(self) -> None:
        assert len(manifest.actions) == 6

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_missing_access_token_returns_error() -> None:
    """Calling with empty auth_data should short-circuit with an error."""
    result_dict = await add_ssh_key.ainvoke(
        {"auth_type": "oauth2", "auth_data": {}, "name": "k", "public_key": "ssh-rsa AAA"}
    )
    assert isinstance(result_dict, dict)
    result = AddSshKeyOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access_token" in result.error


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_add_ssh_key(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/account/keys",
        json={
            # TODO: fill in a representative response from DigitalOcean API docs
            "ssh_key": {
                "id": 12345,
                "fingerprint": "ab:cd:ef:00:11:22:33:44:55:66:77:88:99:aa:bb:cc",
                "public_key": "ssh-rsa AAAAB3...",
                "name": "My SSH Key",
            },
        },
        status_code=201,
    )

    result_dict = await add_ssh_key.ainvoke(_args(name="My SSH Key", public_key="ssh-rsa AAAAB3..."))

    assert isinstance(result_dict, dict)
    result = AddSshKeyOutput.model_validate(result_dict)
    assert result.success is True
    assert result.ssh_key is not None
    assert result.ssh_key.id == 12345


@pytest.mark.asyncio
async def test_create_domain(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/domains",
        json={
            # TODO: fill in a representative response from DigitalOcean API docs
            "domain": {
                "name": "example.com",
                "ttl": 1800,
                "zone_file": "$ORIGIN example.com.",
            },
        },
        status_code=201,
    )

    result_dict = await create_domain.ainvoke(_args(name="example.com", ip_address="1.2.3.4"))

    assert isinstance(result_dict, dict)
    result = CreateDomainOutput.model_validate(result_dict)
    assert result.success is True
    assert result.domain is not None
    assert result.domain.name == "example.com"


@pytest.mark.asyncio
async def test_create_droplet(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/droplets",
        json={
            # TODO: fill in a representative response from DigitalOcean API docs
            "droplet": {
                "id": 99999,
                "name": "my-droplet",
                "memory": 1024,
                "vcpus": 1,
                "disk": 25,
                "status": "new",
                "region": {"slug": "nyc1"},
                "image": {"slug": "ubuntu-22-04-x64"},
                "size_slug": "s-1vcpu-1gb",
            },
        },
        status_code=202,
    )

    result_dict = await create_droplet.ainvoke(
        _args(name="my-droplet", region="nyc1", image="ubuntu-22-04-x64", size="s-1vcpu-1gb")
    )

    assert isinstance(result_dict, dict)
    result = CreateDropletOutput.model_validate(result_dict)
    assert result.success is True
    assert result.droplet is not None
    assert result.droplet.id == 99999


@pytest.mark.asyncio
async def test_create_snapshot(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/droplets/12345/actions",
        json={
            # TODO: fill in a representative response from DigitalOcean API docs
            "action": {
                "id": 555,
                "status": "in-progress",
                "type": "snapshot",
                "started_at": "2026-05-18T00:00:00Z",
                "completed_at": None,
                "resource_id": 12345,
                "resource_type": "droplet",
                "region_slug": "nyc1",
            },
        },
        status_code=201,
    )

    result_dict = await create_snapshot.ainvoke(_args(droplet_id="12345", snapshot_name="my-snap"))

    assert isinstance(result_dict, dict)
    result = CreateSnapshotOutput.model_validate(result_dict)
    assert result.success is True
    assert result.action is not None
    assert result.action.type == "snapshot"


@pytest.mark.asyncio
async def test_list_all_droplets(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/droplets?page=1&per_page=50",
        json={
            # TODO: fill in a representative response from DigitalOcean API docs
            "droplets": [
                {
                    "id": 1001,
                    "name": "web-1",
                    "memory": 2048,
                    "vcpus": 2,
                    "disk": 50,
                    "status": "active",
                    "region": {"slug": "sfo1"},
                    "image": {"slug": "ubuntu-22-04-x64"},
                    "size_slug": "s-2vcpu-2gb",
                },
            ],
            "meta": {"total": 1},
        },
        status_code=200,
    )

    result_dict = await list_all_droplets.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListAllDropletsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.droplets) == 1
    assert result.droplets[0].name == "web-1"


@pytest.mark.asyncio
async def test_turnonoff_droplet(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/droplets/12345/actions",
        json={
            # TODO: fill in a representative response from DigitalOcean API docs
            "action": {
                "id": 777,
                "status": "in-progress",
                "type": "power_off",
                "started_at": "2026-05-18T01:00:00Z",
                "completed_at": None,
                "resource_id": 12345,
                "resource_type": "droplet",
                "region_slug": "nyc1",
            },
        },
        status_code=201,
    )

    result_dict = await turnonoff_droplet.ainvoke(_args(turn_on_off="power_off", droplet_id="12345"))

    assert isinstance(result_dict, dict)
    result = TurnonoffDropletOutput.model_validate(result_dict)
    assert result.success is True
    assert result.action is not None
    assert result.action.type == "power_off"

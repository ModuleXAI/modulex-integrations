"""DigitalOcean LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.digital_ocean.outputs import (
    AddSshKeyOutput,
    CreateDomainOutput,
    CreateDropletOutput,
    CreateSnapshotOutput,
    DomainResource,
    DropletActionResource,
    DropletResource,
    ListAllDropletsOutput,
    MetaResource,
    SshKeyResource,
    TurnonoffDropletOutput,
)

__all__ = [
    "add_ssh_key",
    "create_domain",
    "create_droplet",
    "create_snapshot",
    "list_all_droplets",
    "turnonoff_droplet",
]

_BASE_URL = "https://api.digitalocean.com/v2"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the DigitalOcean API based on auth_type/auth_data."""
    headers: dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class AddSshKeyInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="A human-readable display name for this key")
    public_key: str = Field(description="The entire public key string")


class CreateDomainInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="The domain name in standard domain.TLD format")
    ip_address: str = Field(description="An IP address to create an A record pointing to the apex domain")


class CreateDropletInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="Human-readable Droplet display name")
    region: str = Field(description="Region slug (e.g. nyc1, sfo1, ams3)")
    image: str = Field(description="Image ID or slug for the base image")
    size: str = Field(description="Size slug (e.g. s-1vcpu-1gb)")
    volumes: list[str] | None = Field(default=None, description="List of Block Storage volume IDs to attach")
    ssh_keys: list[str] | None = Field(default=None, description="List of SSH key IDs or fingerprints")
    backups: bool | None = Field(default=None, description="Whether automated backups should be enabled")
    ipv6: bool | None = Field(default=None, description="Whether IPv6 is enabled")
    user_data: str | None = Field(default=None, description="Cloud-init user data or Bash script for first boot")
    private_networking: bool | None = Field(default=None, description="Whether private networking is enabled")
    monitoring: bool | None = Field(default=None, description="Whether to install the monitoring agent")
    tags: list[str] | None = Field(default=None, description="List of tag names to apply after creation")


class CreateSnapshotInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    droplet_id: str = Field(description="The unique identifier of the Droplet to snapshot")
    snapshot_name: str | None = Field(default=None, description="The name to give the new snapshot")


class ListAllDropletsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    tag_name: str | None = Field(default=None, description="Filter Droplets by a specific tag name")
    page: int = Field(default=1, description="Which page of paginated results to return")
    per_page: int = Field(default=50, description="Number of items returned per page")


class TurnonoffDropletInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    turn_on_off: str = Field(description="Power action: power_on or power_off")
    droplet_id: str = Field(description="The unique identifier of the Droplet")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AddSshKeyInput)
@serialize_pydantic_return
async def add_ssh_key(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    public_key: str,
) -> AddSshKeyOutput:
    """Add a new SSH key to your DigitalOcean account."""
    if not auth_data.get("access_token"):
        return AddSshKeyOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/account/keys",
                headers=headers,
                json={"name": name, "public_key": public_key},
            )
        if response.status_code not in (200, 201):
            return AddSshKeyOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return AddSshKeyOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddSshKeyOutput(success=False, error=f"Call failed: {exc}")

    key = data.get("ssh_key", {})
    return AddSshKeyOutput(
        success=True,
        ssh_key=SshKeyResource(
            id=key.get("id"),
            fingerprint=key.get("fingerprint"),
            public_key=key.get("public_key"),
            name=key.get("name"),
        ),
    )


@tool(args_schema=CreateDomainInput)
@serialize_pydantic_return
async def create_domain(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    ip_address: str,
) -> CreateDomainOutput:
    """Create a new domain in DigitalOcean DNS."""
    if not auth_data.get("access_token"):
        return CreateDomainOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/domains",
                headers=headers,
                json={"name": name, "ip_address": ip_address},
            )
        if response.status_code not in (200, 201):
            return CreateDomainOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateDomainOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateDomainOutput(success=False, error=f"Call failed: {exc}")

    d = data.get("domain", {})
    return CreateDomainOutput(
        success=True,
        domain=DomainResource(
            name=d.get("name"),
            ttl=d.get("ttl"),
            zone_file=d.get("zone_file"),
        ),
    )


@tool(args_schema=CreateDropletInput)
@serialize_pydantic_return
async def create_droplet(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    region: str,
    image: str,
    size: str,
    volumes: list[str] | None = None,
    ssh_keys: list[str] | None = None,
    backups: bool | None = None,
    ipv6: bool | None = None,
    user_data: str | None = None,
    private_networking: bool | None = None,
    monitoring: bool | None = None,
    tags: list[str] | None = None,
) -> CreateDropletOutput:
    """Create a new DigitalOcean Droplet (virtual machine)."""
    if not auth_data.get("access_token"):
        return CreateDropletOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {
        "name": name,
        "region": region,
        "image": image,
        "size": size,
    }
    if volumes is not None:
        payload["volumes"] = volumes
    if ssh_keys is not None:
        payload["ssh_keys"] = ssh_keys
    if backups is not None:
        payload["backups"] = backups
    if ipv6 is not None:
        payload["ipv6"] = ipv6
    if user_data is not None:
        payload["user_data"] = user_data
    if private_networking is not None:
        payload["private_networking"] = private_networking
    if monitoring is not None:
        payload["monitoring"] = monitoring
    if tags is not None:
        payload["tags"] = tags

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/droplets",
                headers=headers,
                json=payload,
            )
        if response.status_code not in (200, 201, 202):
            return CreateDropletOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateDropletOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateDropletOutput(success=False, error=f"Call failed: {exc}")

    dr = data.get("droplet", {})
    region_info = dr.get("region")
    region_slug = region_info.get("slug") if isinstance(region_info, dict) else region_info
    image_info = dr.get("image")
    image_slug = image_info.get("slug") if isinstance(image_info, dict) else image_info
    size_info = dr.get("size_slug") or (dr.get("size", {}).get("slug") if isinstance(dr.get("size"), dict) else None)

    return CreateDropletOutput(
        success=True,
        droplet=DropletResource(
            id=dr.get("id"),
            name=dr.get("name"),
            memory=dr.get("memory"),
            vcpus=dr.get("vcpus"),
            disk=dr.get("disk"),
            status=dr.get("status"),
            region=region_slug,
            image=image_slug,
            size_slug=size_info,
        ),
    )


@tool(args_schema=CreateSnapshotInput)
@serialize_pydantic_return
async def create_snapshot(
    auth_type: str,
    auth_data: dict[str, Any],
    droplet_id: str,
    snapshot_name: str | None = None,
) -> CreateSnapshotOutput:
    """Create a snapshot from an existing DigitalOcean Droplet."""
    if not auth_data.get("access_token"):
        return CreateSnapshotOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {"type": "snapshot"}
    if snapshot_name is not None:
        payload["name"] = snapshot_name

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/droplets/{droplet_id}/actions",
                headers=headers,
                json=payload,
            )
        if response.status_code not in (200, 201):
            return CreateSnapshotOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateSnapshotOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateSnapshotOutput(success=False, error=f"Call failed: {exc}")

    a = data.get("action", {})
    return CreateSnapshotOutput(
        success=True,
        action=DropletActionResource(
            id=a.get("id"),
            status=a.get("status"),
            type=a.get("type"),
            started_at=a.get("started_at"),
            completed_at=a.get("completed_at"),
            resource_id=a.get("resource_id"),
            resource_type=a.get("resource_type"),
            region_slug=a.get("region_slug"),
        ),
    )


@tool(args_schema=ListAllDropletsInput)
@serialize_pydantic_return
async def list_all_droplets(
    auth_type: str,
    auth_data: dict[str, Any],
    tag_name: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> ListAllDropletsOutput:
    """List all Droplets in your DigitalOcean account."""
    if not auth_data.get("access_token"):
        return ListAllDropletsOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"page": page, "per_page": per_page}
    if tag_name is not None:
        params["tag_name"] = tag_name

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/droplets",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListAllDropletsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListAllDropletsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAllDropletsOutput(success=False, error=f"Call failed: {exc}")

    droplets = [
        DropletResource(
            id=d.get("id"),
            name=d.get("name"),
            memory=d.get("memory"),
            vcpus=d.get("vcpus"),
            disk=d.get("disk"),
            status=d.get("status"),
            region=d.get("region", {}).get("slug") if isinstance(d.get("region"), dict) else d.get("region"),
            image=d.get("image", {}).get("slug") if isinstance(d.get("image"), dict) else d.get("image"),
            size_slug=d.get("size_slug"),
        )
        for d in data.get("droplets", [])
    ]
    meta_raw = data.get("meta", {})
    meta = MetaResource(total=meta_raw.get("total")) if meta_raw else None

    return ListAllDropletsOutput(
        success=True,
        droplets=droplets,
        meta=meta,
    )


@tool(args_schema=TurnonoffDropletInput)
@serialize_pydantic_return
async def turnonoff_droplet(
    auth_type: str,
    auth_data: dict[str, Any],
    turn_on_off: str,
    droplet_id: str,
) -> TurnonoffDropletOutput:
    """Turn a Droplet's power on or off."""
    if not auth_data.get("access_token"):
        return TurnonoffDropletOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/droplets/{droplet_id}/actions",
                headers=headers,
                json={"type": turn_on_off},
            )
        if response.status_code not in (200, 201):
            return TurnonoffDropletOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return TurnonoffDropletOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return TurnonoffDropletOutput(success=False, error=f"Call failed: {exc}")

    a = data.get("action", {})
    return TurnonoffDropletOutput(
        success=True,
        action=DropletActionResource(
            id=a.get("id"),
            status=a.get("status"),
            type=a.get("type"),
            started_at=a.get("started_at"),
            completed_at=a.get("completed_at"),
            resource_id=a.get("resource_id"),
            resource_type=a.get("resource_type"),
            region_slug=a.get("region_slug"),
        ),
    )

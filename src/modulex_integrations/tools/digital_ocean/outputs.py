"""Pydantic response models for the digital_ocean integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddSshKeyOutput",
    "CreateDomainOutput",
    "CreateDropletOutput",
    "CreateSnapshotOutput",
    "DomainResource",
    "DropletActionResource",
    "DropletResource",
    "ListAllDropletsOutput",
    "MetaResource",
    "SshKeyResource",
    "TurnonoffDropletOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class SshKeyResource(_Base):
    """An SSH key on the DigitalOcean account."""

    id: int | None = None
    fingerprint: str | None = None
    public_key: str | None = None
    name: str | None = None


class DomainResource(_Base):
    """A domain registered in DigitalOcean DNS."""

    name: str | None = None
    ttl: int | None = None
    zone_file: str | None = None


class DropletResource(_Base):
    """A DigitalOcean Droplet summary."""

    id: int | None = None
    name: str | None = None
    memory: int | None = None
    vcpus: int | None = None
    disk: int | None = None
    status: str | None = None
    region: str | None = None
    image: str | None = None
    size_slug: str | None = None


class DropletActionResource(_Base):
    """A DigitalOcean Droplet action."""

    id: int | None = None
    status: str | None = None
    type: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    resource_id: int | None = None
    resource_type: str | None = None
    region_slug: str | None = None


class MetaResource(_Base):
    """Pagination meta from DigitalOcean list responses."""

    total: int | None = None


# --- Per-action output models ----------------------------------------------


class AddSshKeyOutput(_Base):
    success: bool
    error: str | None = None
    ssh_key: SshKeyResource | None = None


class CreateDomainOutput(_Base):
    success: bool
    error: str | None = None
    domain: DomainResource | None = None


class CreateDropletOutput(_Base):
    success: bool
    error: str | None = None
    droplet: DropletResource | None = None


class CreateSnapshotOutput(_Base):
    success: bool
    error: str | None = None
    action: DropletActionResource | None = None


class ListAllDropletsOutput(_Base):
    success: bool
    error: str | None = None
    droplets: list[DropletResource] = Field(default_factory=list)
    meta: MetaResource | None = None


class TurnonoffDropletOutput(_Base):
    success: bool
    error: str | None = None
    action: DropletActionResource | None = None

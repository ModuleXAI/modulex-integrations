"""Pydantic response models for the New Relic integration's @tool functions.

New Relic's tools follow the modulex *api_key* runtime convention: each
function signature takes ``api_key: str`` directly, and the modulex
``ToolExecutor`` injects it from the resolved ``api_key`` credential.

All four actions POST to the NerdGraph GraphQL API. NerdGraph returns a
standard GraphQL envelope (``{"data": ..., "errors": [...]}``); a non-2xx
status or a populated ``errors`` array is surfaced as ``success=False`` +
``error`` rather than raising. Every output model carries both shapes.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ChangeTrackingEntity",
    "ChangeTrackingEvent",
    "CreateDeploymentEventOutput",
    "Entity",
    "GetEntityOutput",
    "NrqlQueryOutput",
    "SearchEntitiesOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class Entity(_Base):
    """A single monitored New Relic entity (guid, name, entityType)."""

    guid: str | None = None
    name: str | None = None
    entity_type: str | None = None


class ChangeTrackingEntity(_Base):
    """The entity a change tracking event is associated with."""

    guid: str | None = None
    name: str | None = None


class ChangeTrackingEvent(_Base):
    """A created New Relic change tracking (deployment) event."""

    category: str | None = None
    category_and_type: str | None = None
    change_tracking_id: str | None = None
    custom_attributes: dict[str, Any] | None = None
    description: str | None = None
    group_id: str | None = None
    short_description: str | None = None
    timestamp: int | None = None
    type: str | None = None
    user: str | None = None
    entity: ChangeTrackingEntity | None = None


# --- Per-action output models ----------------------------------------------


class NrqlQueryOutput(_Base):
    success: bool
    error: str | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)
    result_count: int = 0


class SearchEntitiesOutput(_Base):
    success: bool
    error: str | None = None
    count: int = 0
    query: str | None = None
    entities: list[Entity] = Field(default_factory=list)
    next_cursor: str | None = None


class GetEntityOutput(_Base):
    success: bool
    error: str | None = None
    entity: Entity | None = None


class CreateDeploymentEventOutput(_Base):
    success: bool
    error: str | None = None
    event: ChangeTrackingEvent | None = None
    messages: list[str] = Field(default_factory=list)

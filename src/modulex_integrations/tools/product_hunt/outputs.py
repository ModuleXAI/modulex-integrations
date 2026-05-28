"""Pydantic response models for the product_hunt integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ListTopicOptionsOutput",
    "TopicOption",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class TopicOption(_Base):
    """A single topic option with slug and display name."""

    value: str | None = None
    label: str | None = None


# --- Per-action output models ---------------------------------------------


class ListTopicOptionsOutput(_Base):
    success: bool
    error: str | None = None
    topics: list[TopicOption] = Field(default_factory=list)

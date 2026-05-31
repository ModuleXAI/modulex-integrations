"""Pydantic response models for the revolt integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
    "AddGroupMemberOutput",
    "CreateGroupOutput",
    "SendFriendRequestOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Per-action output models ----------------------------------------------


class CreateGroupOutput(_Base):
    success: bool
    error: str | None = None
    channel_id: str | None = None
    channel_type: str | None = None
    name: str | None = None
    description: str | None = None
    owner: str | None = None
    nsfw: bool | None = None


class AddGroupMemberOutput(_Base):
    success: bool
    error: str | None = None


class SendFriendRequestOutput(_Base):
    success: bool
    error: str | None = None
    user_id: str | None = None
    status: str | None = None

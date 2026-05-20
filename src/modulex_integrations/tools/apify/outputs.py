"""Pydantic response models for the apify integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "GetDatasetItemsOutput",
    "GetKvsRecordOutput",
    "RunActorOutput",
    "RunTaskOutput",
    "RunTaskSynchronouslyOutput",
    "ScrapeSingleUrlOutput",
    "SetKeyValueStoreRecordOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Per-action output models ----------------------------------------------


class RunActorOutput(_Base):
    success: bool
    error: str | None = None
    run_id: str | None = None
    act_id: str | None = None
    status: str | None = None
    started_at: str | None = None
    dataset_id: str | None = None
    key_value_store_id: str | None = None
    data: dict[str, Any] | None = None


class RunTaskOutput(_Base):
    success: bool
    error: str | None = None
    run_id: str | None = None
    act_id: str | None = None
    task_id: str | None = None
    status: str | None = None
    started_at: str | None = None
    dataset_id: str | None = None
    key_value_store_id: str | None = None


class RunTaskSynchronouslyOutput(_Base):
    success: bool
    error: str | None = None
    run_id: str | None = None
    act_id: str | None = None
    status: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    dataset_id: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class GetDatasetItemsOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class GetKvsRecordOutput(_Base):
    success: bool
    error: str | None = None
    content_type: str | None = None
    data: Any | None = None


class ScrapeSingleUrlOutput(_Base):
    success: bool
    error: str | None = None
    url: str | None = None
    text: str | None = None
    html: str | None = None
    markdown: str | None = None


class SetKeyValueStoreRecordOutput(_Base):
    success: bool
    error: str | None = None
    store_id: str | None = None
    key: str | None = None
    content_type: str | None = None

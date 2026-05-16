"""Pydantic response models for the Short.io integration.

Field names mirror Short.io's upstream camelCase wire format
(``originalURL``, ``idString``, ``shortURL``, etc.) — silenced via
the per-file ``N815`` ruff ignore in ``pyproject.toml``.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateLinkOutput",
    "DeleteLinkOutput",
    "ExpireLinkOutput",
    "GetDomainStatisticsOutput",
    "GetLinkInfoOutput",
    "ListDomainsOutput",
    "ListLinksOutput",
    "ShortIODomain",
    "ShortIOLink",
    "UpdateLinkOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ShortIOLink(_Base):
    originalURL: str | None = None
    path: str | None = None
    idString: str | None = None
    id: str | None = None
    shortURL: str | None = None
    secureShortURL: str | None = None
    cloaking: bool | None = None
    title: str | None = None
    tags: list[str] = Field(default_factory=list)
    createdAt: str | None = None
    DomainId: int | None = None
    OwnerId: int | None = None
    # Fields present on update/get_info/list but not create
    skipQS: bool | None = None
    archived: bool | None = None
    hasPassword: bool | None = None
    source: str | None = None
    expiresAt: Any = None
    expiredURL: str | None = None
    User: dict[str, Any] | None = None


class ShortIODomain(_Base):
    id: int | None = None
    hostname: str | None = None
    protocol: str | None = None
    created: str | None = None


class CreateLinkOutput(_Base):
    success: bool
    error: str | None = None
    link: ShortIOLink | None = None


class UpdateLinkOutput(_Base):
    success: bool
    error: str | None = None
    link: ShortIOLink | None = None


class DeleteLinkOutput(_Base):
    success: bool
    error: str | None = None
    link_id: str | None = None
    # Short.io's delete is sometimes empty-bodied; capture whatever it returns.
    response: dict[str, Any] | None = None


class ExpireLinkOutput(_Base):
    success: bool
    error: str | None = None
    link: ShortIOLink | None = None


class GetLinkInfoOutput(_Base):
    success: bool
    error: str | None = None
    link: ShortIOLink | None = None


class ListLinksOutput(_Base):
    success: bool
    error: str | None = None
    links: list[ShortIOLink] = Field(default_factory=list)
    count: int = 0


class ListDomainsOutput(_Base):
    success: bool
    error: str | None = None
    domains: list[ShortIODomain] = Field(default_factory=list)
    count: int = 0


class GetDomainStatisticsOutput(_Base):
    success: bool
    error: str | None = None
    # Short.io's analytics response is very heterogeneous; keep the
    # full upstream body intact (matches legacy `result: full_response`).
    statistics: dict[str, Any] | None = None

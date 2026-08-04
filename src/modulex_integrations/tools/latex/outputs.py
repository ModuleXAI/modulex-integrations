"""Pydantic response models for the LaTeX integration's @tool functions.

Each model describes the *normalized* shape produced by ``tools.py``, not
the raw upstream payload: the LaTeX-on-HTTP API answers with TeX Live's own
key names (``shortdesc``, ``longdesc``, ``cat-license``, ``cat-topics``,
``cat-related``, ``cat-contact-home``, ``url_ctan``), which are mapped onto
readable snake_case fields at parse time.

Error model: HTTP failures (a ``404`` with ``{"error": "Package not
found"}``, a timeout, an unparseable body) are all caught and surfaced as
``success=False`` + ``error`` rather than raising, so every output model
carries the same envelope. Every field stays optional because the upstream
payload is TeX Live metadata whose optional keys vary per package.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "GetPackageOutput",
    "LatexFont",
    "LatexPackageDetails",
    "LatexPackageSummary",
    "ListFontsOutput",
    "SearchPackagesOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class LatexPackageSummary(_Base):
    """One TeX Live package as it appears in the package listing."""

    name: str | None = None
    short_description: str | None = None
    installed: bool | None = None
    ctan_url: str | None = None


class LatexPackageDetails(_Base):
    """Full metadata for a single TeX Live package."""

    name: str | None = None
    installed: bool | None = None
    short_description: str | None = None
    long_description: str | None = None
    category: str | None = None
    license: str | None = None
    topics: list[str] = Field(default_factory=list)
    related_packages: list[str] = Field(default_factory=list)
    homepage: str | None = None
    ctan_url: str | None = None


class LatexFont(_Base):
    """One font installed on the compiler host."""

    family: str | None = None
    name: str | None = None
    styles: list[str] = Field(default_factory=list)


# --- Per-action output models ----------------------------------------------


class SearchPackagesOutput(_Base):
    success: bool
    error: str | None = None
    packages: list[LatexPackageSummary] = Field(default_factory=list)
    total_matches: int = 0


class GetPackageOutput(_Base):
    success: bool
    error: str | None = None
    package: LatexPackageDetails | None = None


class ListFontsOutput(_Base):
    success: bool
    error: str | None = None
    fonts: list[LatexFont] = Field(default_factory=list)
    total_matches: int = 0

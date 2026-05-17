"""Pydantic response models for the Apollo.io integration.

Every action returns ``{success, error, result: <upstream JSON>}`` —
Apollo's response shapes vary so widely per endpoint (enrichment vs
search vs CRUD vs stage lookups) that re-modelling each one
individually would lock the schema down with no real validation
benefit. ``result`` is the raw upstream body, mirroring the legacy
inline tool's `_build_response` behavior.

Each action gets its own typed subclass so the runtime can derive
distinct JSONSchemas, but they all share the same shape.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
    "AddContactsToSequenceOutput",
    "BulkOrganizationEnrichmentOutput",
    "BulkPeopleEnrichmentOutput",
    "CreateAccountOutput",
    "CreateContactOutput",
    "CreateDealOutput",
    "CreateTaskOutput",
    "GetApiUsageOutput",
    "ListAccountStagesOutput",
    "ListContactStagesOutput",
    "ListDealStagesOutput",
    "ListDealsOutput",
    "ListUsersOutput",
    "OrganizationEnrichmentOutput",
    "OrganizationJobPostingsOutput",
    "OrganizationSearchOutput",
    "PeopleEnrichmentOutput",
    "PeopleSearchOutput",
    "SearchAccountsOutput",
    "SearchContactsOutput",
    "SearchSequencesOutput",
    "SearchTasksOutput",
    "UpdateAccountOutput",
    "UpdateContactOutput",
    "UpdateDealOutput",
    "ViewAccountOutput",
    "ViewContactOutput",
    "ViewDealOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None
    result: dict[str, Any] | None = None


class PeopleEnrichmentOutput(_Base):
    pass


class BulkPeopleEnrichmentOutput(_Base):
    pass


class OrganizationEnrichmentOutput(_Base):
    pass


class BulkOrganizationEnrichmentOutput(_Base):
    pass


class PeopleSearchOutput(_Base):
    pass


class OrganizationSearchOutput(_Base):
    pass


class OrganizationJobPostingsOutput(_Base):
    pass


class CreateContactOutput(_Base):
    pass


class UpdateContactOutput(_Base):
    pass


class SearchContactsOutput(_Base):
    pass


class ViewContactOutput(_Base):
    pass


class CreateAccountOutput(_Base):
    pass


class UpdateAccountOutput(_Base):
    pass


class SearchAccountsOutput(_Base):
    pass


class ViewAccountOutput(_Base):
    pass


class CreateDealOutput(_Base):
    pass


class UpdateDealOutput(_Base):
    pass


class ListDealsOutput(_Base):
    pass


class ViewDealOutput(_Base):
    pass


class SearchSequencesOutput(_Base):
    pass


class AddContactsToSequenceOutput(_Base):
    pass


class CreateTaskOutput(_Base):
    pass


class SearchTasksOutput(_Base):
    pass


class GetApiUsageOutput(_Base):
    pass


class ListUsersOutput(_Base):
    pass


class ListContactStagesOutput(_Base):
    pass


class ListAccountStagesOutput(_Base):
    pass


class ListDealStagesOutput(_Base):
    pass

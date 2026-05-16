"""Pydantic response models for the Cloudflare integration.

Cloudflare wraps every response in a uniform envelope:
``{"success": bool, "errors": [...], "messages": [...], "result": ...,
   "result_info": {...}}``. We coerce that into our own envelope —
``success`` from the upstream flag, ``error`` from the first
``errors[].message``, and ``result`` carrying the upstream ``result``
body (which is itself a list or dict depending on the action).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
    "CreateDNSRecordOutput",
    "CreateWAFListOutput",
    "DeleteDNSRecordOutput",
    "DeleteWAFListOutput",
    "ListAccountMembersOutput",
    "ListAccountsOutput",
    "ListFirewallRulesOutput",
    "ListMonitorsOutput",
    "ListPoolsOutput",
    "ListWAFListsOutput",
    "ListZonesOutput",
    "UpdateDNSRecordOutput",
    "UpdateWAFListOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None
    result: Any = None
    # Pagination + count info from Cloudflare's `result_info`.
    total: int | None = None
    page: int | None = None
    per_page: int | None = None


class ListZonesOutput(_Base):
    pass


class CreateDNSRecordOutput(_Base):
    pass


class UpdateDNSRecordOutput(_Base):
    pass


class DeleteDNSRecordOutput(_Base):
    pass


class ListWAFListsOutput(_Base):
    pass


class CreateWAFListOutput(_Base):
    pass


class UpdateWAFListOutput(_Base):
    pass


class DeleteWAFListOutput(_Base):
    pass


class ListAccountsOutput(_Base):
    pass


class ListAccountMembersOutput(_Base):
    pass


class ListFirewallRulesOutput(_Base):
    pass


class ListMonitorsOutput(_Base):
    pass


class ListPoolsOutput(_Base):
    pass

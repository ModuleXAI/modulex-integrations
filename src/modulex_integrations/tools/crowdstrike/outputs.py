"""Pydantic response models for the CrowdStrike integration's @tool functions.

CrowdStrike's tools follow the modulex *api_key* runtime convention: each
function takes ``api_key: str`` directly (the resolved Falcon API client
secret), plus ``client_id`` and ``cloud`` as ordinary action params. Every
call first exchanges an OAuth2 client-credentials token, then hits the
Identity Protection REST endpoint with ``Authorization: Bearer <token>``.

Error model: the Falcon API returns proper HTTP status codes and a
standardized envelope (``meta``/``resources``/``errors``). Every output
model wraps both shapes — non-2xx, timeouts, and unexpected exceptions
surface as ``success=False`` + ``error`` rather than raising.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AggregateBucket",
    "AggregateResult",
    "GetSensorAggregatesOutput",
    "GetSensorDetailsOutput",
    "Pagination",
    "QuerySensorsOutput",
    "Sensor",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class Pagination(_Base):
    """Pagination metadata echoed by the Falcon API (``meta.pagination``)."""

    limit: int | None = None
    offset: int | None = None
    total: int | None = None


class Sensor(_Base):
    """A single Identity Protection sensor/device record.

    The Falcon API returns a rich device object; the most commonly used
    attributes are surfaced as typed fields and the complete upstream
    record is preserved verbatim in ``raw`` so nothing is lost. Field
    names mirror the documented camelCase shape; values are read
    permissively with ``.get()`` (both snake_case and camelCase keys are
    attempted at parse time).
    """

    agent_version: str | None = None
    cid: str | None = None
    device_id: str | None = None
    heartbeat_time: int | None = None
    hostname: str | None = None
    idp_policy_id: str | None = None
    idp_policy_name: str | None = None
    ip_address: str | None = None
    kerberos_config: str | None = None
    ldap_config: str | None = None
    ldaps_config: str | None = None
    machine_domain: str | None = None
    ntlm_config: str | None = None
    os_version: str | None = None
    rdp_to_dc_config: str | None = None
    smb_to_dc_config: str | None = None
    status: str | None = None
    status_causes: list[str] = Field(default_factory=list)
    ti_enabled: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class AggregateBucket(_Base):
    """A single bucket within an aggregate result group."""

    count: int | None = None
    from_: float | None = None
    key: str | None = None
    key_as_string: str | None = None
    label: dict[str, Any] | None = None
    string_from: str | None = None
    string_to: str | None = None
    sub_aggregates: list[dict[str, Any]] = Field(default_factory=list)
    to: float | None = None
    value: float | None = None
    value_as_string: str | None = None


class AggregateResult(_Base):
    """One aggregate result group returned by the aggregates endpoint."""

    name: str | None = None
    buckets: list[AggregateBucket] = Field(default_factory=list)
    doc_count_error_upper_bound: int | None = None
    sum_other_doc_count: int | None = None


# --- Per-action output models ----------------------------------------------


class QuerySensorsOutput(_Base):
    success: bool
    error: str | None = None
    sensors: list[Sensor] = Field(default_factory=list)
    device_ids: list[str] = Field(default_factory=list)
    count: int = 0
    pagination: Pagination | None = None


class GetSensorDetailsOutput(_Base):
    success: bool
    error: str | None = None
    sensors: list[Sensor] = Field(default_factory=list)
    count: int = 0
    pagination: Pagination | None = None


class GetSensorAggregatesOutput(_Base):
    success: bool
    error: str | None = None
    aggregates: list[AggregateResult] = Field(default_factory=list)
    count: int = 0

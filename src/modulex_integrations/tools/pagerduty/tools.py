"""PagerDuty LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.pagerduty.outputs import (
    AcknowledgeIncidentOutput,
    FindOncallUserOutput,
    IncidentSummary,
    OncallUser,
    ResolveIncidentOutput,
    TriggerIncidentOutput,
)

__all__ = [
    "acknowledge_incident",
    "find_oncall_user",
    "resolve_incident",
    "trigger_incident",
]

_BASE_URL = "https://api.pagerduty.com"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the PagerDuty API based on auth_type/auth_data."""
    headers: dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class TriggerIncidentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    title: str = Field(description="A succinct description of the nature, symptoms, cause, or effect of the incident")
    service_id: str = Field(description="The ID of the PagerDuty service to trigger the incident on")
    urgency: str | None = Field(default=None, description="The urgency of the incident: high or low")
    body_details: str | None = Field(default=None, description="Additional incident details")
    incident_key: str | None = Field(default=None, description="A string which identifies the incident")
    escalation_policy_id: str | None = Field(default=None, description="The ID of the escalation policy to assign")
    assignee_ids: list[str] | None = Field(default=None, description="List of user IDs to assign to the incident")
    conference_bridge_number: str | None = Field(default=None, description="Phone number for the conference bridge")
    conference_bridge_url: str | None = Field(default=None, description="URL for the conference bridge")


class AcknowledgeIncidentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    incident_id: str = Field(description="The ID of the incident to acknowledge")


class ResolveIncidentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    incident_id: str = Field(description="The ID of the incident to resolve")


class FindOncallUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    schedule_id: str = Field(description="The ID of the on-call schedule")
    user_id: str = Field(description="The ID of the user to search for in the schedule")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=TriggerIncidentInput)
@serialize_pydantic_return
async def trigger_incident(
    auth_type: str,
    auth_data: dict[str, Any],
    title: str,
    service_id: str,
    urgency: str | None = None,
    body_details: str | None = None,
    incident_key: str | None = None,
    escalation_policy_id: str | None = None,
    assignee_ids: list[str] | None = None,
    conference_bridge_number: str | None = None,
    conference_bridge_url: str | None = None,
) -> TriggerIncidentOutput:
    """Trigger a new incident on a PagerDuty service."""
    if not auth_data.get("access_token"):
        return TriggerIncidentOutput(success=False)
    headers = _get_auth_headers(auth_type, auth_data)

    incident_body: dict[str, Any] = {
        "type": "incident",
        "title": title,
        "service": {
            "id": service_id,
            "type": "service_reference",
        },
    }

    if urgency:
        incident_body["urgency"] = urgency

    if body_details:
        incident_body["body"] = {
            "type": "incident_body",
            "details": body_details,
        }

    if incident_key:
        incident_body["incident_key"] = incident_key

    if escalation_policy_id:
        incident_body["escalation_policy"] = {
            "id": escalation_policy_id,
            "type": "escalation_policy_reference",
        }

    if assignee_ids:
        incident_body["assignments"] = [
            {"assignee": {"id": uid, "type": "user_reference"}}
            for uid in assignee_ids
        ]

    if conference_bridge_number or conference_bridge_url:
        conference_bridge: dict[str, str] = {}
        if conference_bridge_number:
            conference_bridge["conference_number"] = conference_bridge_number
        if conference_bridge_url:
            conference_bridge["conference_url"] = conference_bridge_url
        incident_body["conference_bridge"] = conference_bridge

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/incidents",
            headers=headers,
            json={"incident": incident_body},
        )
        response.raise_for_status()
        data = response.json()

    inc = data.get("incident", {})
    return TriggerIncidentOutput(
        success=True,
        incident=IncidentSummary(
            id=inc.get("id"),
            type=inc.get("type"),
            summary=inc.get("summary"),
            status=inc.get("status"),
            title=inc.get("title"),
            urgency=inc.get("urgency"),
            incident_key=inc.get("incident_key"),
            html_url=inc.get("html_url"),
            created_at=inc.get("created_at"),
            service=inc.get("service"),
            escalation_policy=inc.get("escalation_policy"),
            assignments=inc.get("assignments", []),
        ),
    )


@tool(args_schema=AcknowledgeIncidentInput)
@serialize_pydantic_return
async def acknowledge_incident(
    auth_type: str,
    auth_data: dict[str, Any],
    incident_id: str,
) -> AcknowledgeIncidentOutput:
    """Acknowledge a triggered incident in PagerDuty."""
    if not auth_data.get("access_token"):
        return AcknowledgeIncidentOutput(success=False)
    headers = _get_auth_headers(auth_type, auth_data)

    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{_BASE_URL}/incidents/{incident_id}",
            headers=headers,
            json={
                "incident": {
                    "type": "incident_reference",
                    "status": "acknowledged",
                },
            },
        )
        response.raise_for_status()
        data = response.json()

    inc = data.get("incident", {})
    return AcknowledgeIncidentOutput(
        success=True,
        incident=IncidentSummary(
            id=inc.get("id"),
            type=inc.get("type"),
            summary=inc.get("summary"),
            status=inc.get("status"),
            title=inc.get("title"),
            urgency=inc.get("urgency"),
            incident_key=inc.get("incident_key"),
            html_url=inc.get("html_url"),
            created_at=inc.get("created_at"),
            service=inc.get("service"),
            escalation_policy=inc.get("escalation_policy"),
            assignments=inc.get("assignments", []),
        ),
    )


@tool(args_schema=ResolveIncidentInput)
@serialize_pydantic_return
async def resolve_incident(
    auth_type: str,
    auth_data: dict[str, Any],
    incident_id: str,
) -> ResolveIncidentOutput:
    """Resolve a triggered or acknowledged incident in PagerDuty."""
    if not auth_data.get("access_token"):
        return ResolveIncidentOutput(success=False)
    headers = _get_auth_headers(auth_type, auth_data)

    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{_BASE_URL}/incidents/{incident_id}",
            headers=headers,
            json={
                "incident": {
                    "type": "incident_reference",
                    "status": "resolved",
                },
            },
        )
        response.raise_for_status()
        data = response.json()

    inc = data.get("incident", {})
    return ResolveIncidentOutput(
        success=True,
        incident=IncidentSummary(
            id=inc.get("id"),
            type=inc.get("type"),
            summary=inc.get("summary"),
            status=inc.get("status"),
            title=inc.get("title"),
            urgency=inc.get("urgency"),
            incident_key=inc.get("incident_key"),
            html_url=inc.get("html_url"),
            created_at=inc.get("created_at"),
            service=inc.get("service"),
            escalation_policy=inc.get("escalation_policy"),
            assignments=inc.get("assignments", []),
        ),
    )


@tool(args_schema=FindOncallUserInput)
@serialize_pydantic_return
async def find_oncall_user(
    auth_type: str,
    auth_data: dict[str, Any],
    schedule_id: str,
    user_id: str,
) -> FindOncallUserOutput:
    """Find the user on call for a specific PagerDuty schedule."""
    if not auth_data.get("access_token"):
        return FindOncallUserOutput(success=False)
    headers = _get_auth_headers(auth_type, auth_data)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/schedules/{schedule_id}/users",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

    users = data.get("users", [])
    matched = next((u for u in users if u.get("id") == user_id), None)

    if matched is None:
        return FindOncallUserOutput(success=True, found=False)

    return FindOncallUserOutput(
        success=True,
        found=True,
        user=OncallUser(
            id=matched.get("id"),
            name=matched.get("name"),
            email=matched.get("email"),
            type=matched.get("type"),
            html_url=matched.get("html_url"),
        ),
    )

"""Amazon Alexa LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.amazon_alexa.outputs import (
    GetSimulationResultsOutput,
    SimulateSkillOutput,
)

__all__ = [
    "get_simulation_results",
    "simulate_skill",
]

_BASE_URL = "https://api.amazonalexa.com/v2"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Alexa SMAPI based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas ------------------------------------------------------------


class SimulateSkillInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    skill_id: str = Field(description="The unique identifier for the Alexa skill")
    stage: str = Field(description="The stage of the skill: development or live")
    content: str = Field(description="Utterance text from a user to Alexa")
    locale: str = Field(default="en-US", description="Locale for the virtual device used in the simulation (e.g. en-US, en-GB, de-DE)")


class GetSimulationResultsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    skill_id: str = Field(description="The unique identifier for the Alexa skill")
    stage: str = Field(description="The stage of the skill: development or live")
    simulation_id: str = Field(description="The identifier for the simulation")


# --- @tool functions ----------------------------------------------------------


@tool(args_schema=SimulateSkillInput)
@serialize_pydantic_return
async def simulate_skill(
    auth_type: str,
    auth_data: dict[str, Any],
    skill_id: str,
    stage: str,
    content: str,
    locale: str = "en-US",
) -> SimulateSkillOutput:
    """Simulate a dialog from an Alexa-enabled device and receive the skill response for the specified utterance."""
    if not auth_data.get("access_token"):
        return SimulateSkillOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    payload = {
        "input": {"content": content},
        "device": {"locale": locale},
        "session": {"mode": "DEFAULT"},
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/skills/{skill_id}/stages/{stage}/simulations",
                headers=headers,
                json=payload,
            )
        if response.status_code not in (200, 201):
            return SimulateSkillOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SimulateSkillOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SimulateSkillOutput(success=False, error=f"Call failed: {exc}")

    return SimulateSkillOutput(
        success=True,
        simulation_id=data.get("id"),
        status=data.get("status"),
    )


@tool(args_schema=GetSimulationResultsInput)
@serialize_pydantic_return
async def get_simulation_results(
    auth_type: str,
    auth_data: dict[str, Any],
    skill_id: str,
    stage: str,
    simulation_id: str,
) -> GetSimulationResultsOutput:
    """Get the results of a specified simulation for an Alexa skill."""
    if not auth_data.get("access_token"):
        return GetSimulationResultsOutput(success=False, error="Missing OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/skills/{skill_id}/stages/{stage}/simulations/{simulation_id}",
                headers=headers,
            )
        if response.status_code != 200:
            return GetSimulationResultsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetSimulationResultsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSimulationResultsOutput(success=False, error=f"Call failed: {exc}")

    return GetSimulationResultsOutput(
        success=True,
        simulation_id=data.get("id"),
        status=data.get("status"),
        result=data.get("result"),
    )

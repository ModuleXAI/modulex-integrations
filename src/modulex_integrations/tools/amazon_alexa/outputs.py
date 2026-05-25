"""Pydantic response models for the amazon_alexa integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "GetSimulationResultsOutput",
    "SimulateSkillOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class SimulateSkillOutput(_Base):
    success: bool
    error: str | None = None
    simulation_id: str | None = None
    status: str | None = None


class GetSimulationResultsOutput(_Base):
    success: bool
    error: str | None = None
    simulation_id: str | None = None
    status: str | None = None
    result: dict[str, Any] | None = Field(default=None, description="Simulation result data from the Alexa API")

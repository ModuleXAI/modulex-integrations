"""CrowdStrike integration — discovered by modulex via the
``modulex.tools`` entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.crowdstrike.manifest import manifest
from modulex_integrations.tools.crowdstrike.tools import (
    get_sensor_aggregates,
    get_sensor_details,
    query_sensors,
)

TOOLS = (query_sensors, get_sensor_details, get_sensor_aggregates)

__all__ = [
    "TOOLS",
    "get_sensor_aggregates",
    "get_sensor_details",
    "manifest",
    "query_sensors",
]

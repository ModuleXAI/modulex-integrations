"""Clay LangChain ``@tool`` functions.

A single async tool that pushes a record into a Clay table via that
table's inbound webhook URL. The calling convention is **key-based**:
the modulex ``ToolExecutor`` injects ``api_key: str`` directly. For Clay
webhooks the credential is the *optional* webhook auth token — most
Clay webhooks accept unauthenticated requests, so an empty ``api_key``
is valid and the auth header is only attached when a token is present.

Error model: the HTTP call is wrapped in try/except so non-2xx
responses, timeouts, and unexpected exceptions surface as
``success=False`` + ``error`` rather than raising.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.clay.outputs import PopulateMetadata, PopulateOutput

__all__ = ["populate"]

_POPULATE_TIMEOUT = 30.0


# --- Input schemas (args_schema for each @tool) ----------------------------


class PopulateInput(BaseModel):
    webhook_url: str = Field(
        description="The Clay table webhook URL to send the record to",
    )
    data: dict[str, Any] = Field(
        description=(
            "The record to populate, as a JSON object whose keys map to the "
            "Clay table column names (e.g. name, email, company, domain)"
        ),
    )
    api_key: str = Field(
        default="",
        description=(
            "Optional Clay webhook auth token (provided by the credential "
            "system); sent in the x-clay-webhook-auth header. Most Clay "
            "webhooks do not require this and may be left empty."
        ),
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=PopulateInput)
@serialize_pydantic_return
async def populate(
    webhook_url: str,
    data: dict[str, Any],
    api_key: str = "",
) -> PopulateOutput:
    """Populate a Clay table with a record sent to its webhook URL.

    Posts the record to the table's inbound webhook so Clay can run its
    enrichment waterfall. Enrichment is asynchronous inside Clay, so the
    response is an acknowledgment plus transport metadata, not the
    enriched row.
    """
    if not webhook_url or not webhook_url.strip():
        return PopulateOutput(
            success=False,
            error="webhook_url is empty. Provide the Clay table webhook URL.",
        )

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key and api_key.strip():
        headers["x-clay-webhook-auth"] = api_key

    body: dict[str, Any] = {"data": data}
    timestamp = datetime.now(UTC).isoformat()

    try:
        async with httpx.AsyncClient(timeout=_POPULATE_TIMEOUT) as client:
            response = await client.post(webhook_url, headers=headers, json=body)
    except httpx.TimeoutException:
        return PopulateOutput(
            success=False,
            error="Request timed out while sending data to the Clay webhook.",
        )
    except Exception as exc:
        return PopulateOutput(success=False, error=f"Populate failed: {exc}")

    content_type = response.headers.get("content-type")
    response_headers: dict[str, str] = dict(response.headers)
    metadata = PopulateMetadata(
        status=response.status_code,
        status_text=response.reason_phrase,
        headers=response_headers,
        timestamp=timestamp,
        content_type=content_type or "unknown",
    )

    if response.status_code < 200 or response.status_code >= 300:
        return PopulateOutput(
            success=False,
            error=f"Clay webhook error ({response.status_code}): {response.text}",
            metadata=metadata,
        )

    if content_type and "application/json" in content_type:
        try:
            parsed: Any = response.json()
        except Exception:
            parsed = {"message": response.text}
    else:
        parsed = {"message": response.text}

    return PopulateOutput(success=True, data=parsed, metadata=metadata)

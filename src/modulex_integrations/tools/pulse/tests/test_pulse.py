"""Happy-path test for the parser action + a failure-path test for the
non-2xx -> success=False branch and an empty-credential test (Pulse
does not raise on errors)."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.pulse import TOOLS, manifest, parser
from modulex_integrations.tools.pulse.outputs import ParserOutput

API = "https://api.runpulse.com"
_API_KEY = "fake-api-key"
_FILE_URL = "https://example.com/invoice.pdf"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_1_action(self) -> None:
        assert len(manifest.actions) == 1

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_parser(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/extract",
        json={
            "markdown": "# Invoice\n\nTotal: $42.00",
            "page_count": 3,
            "job_id": "job-001",
            "plan-info": {"pages_used": 3, "tier": "pro"},
            "bounding_boxes": {"page_1": []},
            "extraction_url": None,
            "html": "<h1>Invoice</h1>",
            "structured_output": {"total": 42.0},
            "chunks": [{"text": "Invoice"}],
            "figures": [],
        },
    )

    result_dict = await parser.ainvoke(
        _args(file_url=_FILE_URL, pages="1-3", return_html=True)
    )

    assert isinstance(result_dict, dict)

    result = ParserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.markdown == "# Invoice\n\nTotal: $42.00"
    assert result.page_count == 3
    assert result.job_id == "job-001"
    assert result.plan_info is not None
    assert result.plan_info.pages_used == 3
    assert result.plan_info.tier == "pro"
    assert result.html == "<h1>Invoice</h1>"
    assert result.structured_output == {"total": 42.0}
    assert result.chunks == [{"text": "Invoice"}]

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-api-key"] == _API_KEY


@pytest.mark.asyncio
async def test_parser_reads_plan_info_underscore_alias(httpx_mock):  # type: ignore[no-untyped-def]
    """The current API uses ``plan_info``; the older hyphenated
    ``plan-info`` is a deprecated alias. Both must parse."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/extract",
        json={
            "markdown": "text",
            "page_count": 1,
            "extraction_id": "ext-9",
            "plan_info": {"pages_used": 1, "tier": "free"},
        },
    )

    result_dict = await parser.ainvoke(_args(file_url=_FILE_URL))

    result = ParserOutput.model_validate(result_dict)
    assert result.success is True
    # falls back to extraction_id when job_id absent
    assert result.job_id == "ext-9"
    assert result.plan_info is not None
    assert result.plan_info.tier == "free"


@pytest.mark.asyncio
async def test_parser_nested_output_envelope(httpx_mock):  # type: ignore[no-untyped-def]
    """When the payload nests the extraction under ``output``, it is flattened."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/extract",
        json={"output": {"markdown": "nested", "page_count": 2}},
    )

    result_dict = await parser.ainvoke(_args(file_url=_FILE_URL))

    result = ParserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.markdown == "nested"
    assert result.page_count == 2


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_parser_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Pulse errors come back as HTTP 4xx/5xx; the tool wraps them in
    ``success=False`` + ``error`` rather than raising."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/extract",
        status_code=401,
        text="Invalid API key",
    )

    result_dict = await parser.ainvoke(_args(file_url=_FILE_URL))

    assert isinstance(result_dict, dict)

    result = ParserOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_parser_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await parser.ainvoke({"file_url": _FILE_URL, "api_key": ""})

    assert isinstance(result_dict, dict)

    result = ParserOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_parser_validates_empty_file_url() -> None:
    """Empty file_url short-circuits before the HTTP call."""
    result_dict = await parser.ainvoke(_args(file_url="   "))

    assert isinstance(result_dict, dict)

    result = ParserOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "URL" in result.error

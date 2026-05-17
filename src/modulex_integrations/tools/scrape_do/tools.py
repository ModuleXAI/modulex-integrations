"""Scrape.do LangChain ``@tool`` functions."""
from __future__ import annotations

import base64
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.scrape_do.outputs import (
    GetUsageStatsOutput,
    ScrapeOutput,
    ScrapeToMarkdownOutput,
    ScrapeWithJsOutput,
    TakeScreenshotOutput,
)

__all__ = [
    "get_usage_stats",
    "scrape",
    "scrape_to_markdown",
    "scrape_with_js",
    "take_screenshot",
]

_BASE_URL = "https://api.scrape.do"
_TIMEOUT = 180.0  # scrapes can take a while with JS rendering


# snake_case → camelCase mapping for Scrape.do's wire format.
_PARAM_MAP: dict[str, str] = {
    "body": "body",
    "super_proxy": "super",
    "geo_code": "geoCode",
    "regional_geo_code": "regionalGeoCode",
    "session_id": "sessionId",
    "device": "device",
    "timeout": "timeout",
    "retry_timeout": "retryTimeout",
    "disable_retry": "disableRetry",
    "disable_redirection": "disableRedirection",
    "custom_headers": "customHeaders",
    "extra_headers": "extraHeaders",
    "forward_headers": "forwardHeaders",
    "set_cookies": "setCookies",
    "block_resources": "blockResources",
    "block_ads": "blockAds",
    "output": "output",
    "transparent_response": "transparentResponse",
    "return_json": "returnJSON",
    "wait_until": "waitUntil",
    "wait_selector": "waitSelector",
    "custom_wait": "customWait",
    "width": "width",
    "height": "height",
    "play_with_browser": "playWithBrowser",
    "screen_shot": "screenShot",
    "full_screen_shot": "fullScreenShot",
    "particular_screen_shot": "particularScreenShot",
}


def _empty_key_error(name: str) -> str:
    return (
        f"Scrape.do API key is empty for {name}. "
        "Please configure a valid credential."
    )


def _build_params(
    api_key: str,
    url: str,
    *,
    render: bool = False,
    method: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Translate snake_case args to Scrape.do's camelCase query params."""
    params: dict[str, Any] = {"token": api_key, "url": url}
    if render:
        params["render"] = "true"
    if method and method.upper() != "GET":
        params["method"] = method.upper()
    for py_name, api_name in _PARAM_MAP.items():
        value = kwargs.get(py_name)
        if value is None:
            continue
        if isinstance(value, bool):
            params[api_name] = "true" if value else "false"
        else:
            params[api_name] = str(value)
    return params


async def _scrape_call(params: dict[str, Any]) -> tuple[bool, str | None, dict[str, Any]]:
    """GET ``api.scrape.do`` with the given params. Returns (ok, error, shape).

    The ``shape`` dict carries one of three result patterns:
    - ``{"payload": dict, "content_type": "application/json"}``
    - ``{"data": "<text>", "content_type": "...", "is_binary": False}``
    - ``{"data": "<base64>", "content_type": "image/...", "is_binary": True}``
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(_BASE_URL, params=params)
    except Exception as exc:
        return False, f"Scrape request failed: {exc}", {}

    if response.status_code != 200:
        return False, (
            f"API returned status code {response.status_code}: {response.text[:500]}"
        ), {"status_code": response.status_code}

    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            payload = response.json()
        except Exception as exc:
            return False, f"Failed to parse JSON response: {exc}", {}
        return True, None, {
            "content_type": content_type,
            "payload": payload if isinstance(payload, dict) else {"value": payload},
        }
    if content_type.startswith("image/"):
        return True, None, {
            "content_type": content_type,
            "data": base64.b64encode(response.content).decode("utf-8"),
            "is_binary": True,
        }
    return True, None, {
        "content_type": content_type,
        "data": response.text,
        "is_binary": False,
    }


class _ScrapeCommonInput(BaseModel):
    api_key: str = Field(description="Scrape.do API key (provided by credential system)")
    url: str = Field(description="URL to scrape")
    method: str | None = Field(default="GET", description="HTTP method")
    body: str | None = Field(default=None, description="Request body for POST/PUT")
    super_proxy: bool | None = Field(default=None, description="Use residential proxy")
    geo_code: str | None = Field(default=None, description="Country code")
    regional_geo_code: str | None = Field(default=None, description="Regional proxy location")
    session_id: int | None = Field(default=None, description="Sticky session ID")
    device: str | None = Field(default=None, description="Device emulation")
    timeout: int | None = Field(default=None, description="Timeout ms (5000-120000)")
    retry_timeout: int | None = Field(default=None, description="Retry timeout ms")
    disable_retry: bool | None = Field(default=None, description="Disable retry")
    disable_redirection: bool | None = Field(default=None, description="Disable redirects")
    custom_headers: bool | None = Field(default=None, description="Default headers")
    extra_headers: bool | None = Field(default=None, description="Forward extra headers")
    forward_headers: bool | None = Field(default=None, description="Forward client headers")
    set_cookies: str | None = Field(default=None, description="Cookies to send")
    block_resources: bool | None = Field(default=None, description="Block images/CSS/fonts")
    block_ads: bool | None = Field(default=None, description="Block ads")
    output: str | None = Field(default=None, description="Output format")


class ScrapeInput(_ScrapeCommonInput):
    transparent_response: bool | None = Field(
        default=None, description="Return origin response body with no parsing"
    )


class ScrapeWithJsInput(_ScrapeCommonInput):
    wait_until: str | None = Field(default=None, description="Wait condition")
    wait_selector: str | None = Field(default=None, description="CSS wait selector")
    custom_wait: int | None = Field(default=None, description="Additional wait ms")
    width: int | None = Field(default=None, description="Viewport width")
    height: int | None = Field(default=None, description="Viewport height")
    play_with_browser: str | None = Field(
        default=None, description="JSON Play-with-Browser action list"
    )


class TakeScreenshotInput(BaseModel):
    api_key: str = Field(description="Scrape.do API key (provided by credential system)")
    url: str = Field(description="URL to capture")
    full_page: bool | None = Field(default=False, description="Full-page mode")
    selector: str | None = Field(default=None, description="Element CSS selector")
    super_proxy: bool | None = Field(default=None, description="Use residential proxy")
    geo_code: str | None = Field(default=None, description="Country code")
    regional_geo_code: str | None = Field(default=None, description="Regional proxy")
    session_id: int | None = Field(default=None, description="Sticky session ID")
    device: str | None = Field(default=None, description="Device emulation")
    timeout: int | None = Field(default=None, description="Timeout ms")
    retry_timeout: int | None = Field(default=None, description="Retry timeout ms")
    disable_retry: bool | None = Field(default=None, description="Disable retry")
    disable_redirection: bool | None = Field(default=None, description="Disable redirects")
    width: int | None = Field(default=None, description="Viewport width")
    height: int | None = Field(default=None, description="Viewport height")
    wait_until: str | None = Field(default=None, description="Wait condition")
    wait_selector: str | None = Field(default=None, description="CSS wait selector")
    custom_wait: int | None = Field(default=None, description="Additional wait ms")
    block_ads: bool | None = Field(default=None, description="Block ads")
    custom_headers: bool | None = Field(default=None, description="Default headers")
    set_cookies: str | None = Field(default=None, description="Cookies to send")


class ScrapeToMarkdownInput(BaseModel):
    api_key: str = Field(description="Scrape.do API key (provided by credential system)")
    url: str = Field(description="URL to scrape")
    render: bool | None = Field(default=False, description="Enable JS rendering")
    method: str | None = Field(default="GET", description="HTTP method")
    body: str | None = Field(default=None, description="Request body")
    super_proxy: bool | None = Field(default=None, description="Use residential proxy")
    geo_code: str | None = Field(default=None, description="Country code")
    regional_geo_code: str | None = Field(default=None, description="Regional proxy")
    session_id: int | None = Field(default=None, description="Sticky session ID")
    device: str | None = Field(default=None, description="Device emulation")
    timeout: int | None = Field(default=None, description="Timeout ms")
    retry_timeout: int | None = Field(default=None, description="Retry timeout ms")
    disable_retry: bool | None = Field(default=None, description="Disable retry")
    disable_redirection: bool | None = Field(default=None, description="Disable redirects")
    block_resources: bool | None = Field(default=None, description="Block images/CSS/fonts")
    block_ads: bool | None = Field(default=None, description="Block ads")
    custom_headers: bool | None = Field(default=None, description="Default headers")
    set_cookies: str | None = Field(default=None, description="Cookies to send")
    play_with_browser: str | None = Field(
        default=None, description="JSON Play-with-Browser script"
    )


class GetUsageStatsInput(BaseModel):
    api_key: str = Field(description="Scrape.do API key (provided by credential system)")


# --- Tools -----------------------------------------------------------------


@tool(args_schema=ScrapeInput)
@serialize_pydantic_return
async def scrape(
    api_key: str,
    url: str,
    method: str | None = "GET",
    body: str | None = None,
    super_proxy: bool | None = None,
    geo_code: str | None = None,
    regional_geo_code: str | None = None,
    session_id: int | None = None,
    device: str | None = None,
    timeout: int | None = None,
    retry_timeout: int | None = None,
    disable_retry: bool | None = None,
    disable_redirection: bool | None = None,
    custom_headers: bool | None = None,
    extra_headers: bool | None = None,
    forward_headers: bool | None = None,
    set_cookies: str | None = None,
    block_resources: bool | None = None,
    block_ads: bool | None = None,
    output: str | None = None,
    transparent_response: bool | None = None,
) -> ScrapeOutput:
    """Basic Scrape.do scrape (no JS rendering)."""
    if not api_key or not api_key.strip():
        return ScrapeOutput(success=False, error=_empty_key_error("scrape"))

    params = _build_params(
        api_key,
        url,
        method=method,
        body=body,
        super_proxy=super_proxy,
        geo_code=geo_code,
        regional_geo_code=regional_geo_code,
        session_id=session_id,
        device=device,
        timeout=timeout,
        retry_timeout=retry_timeout,
        disable_retry=disable_retry,
        disable_redirection=disable_redirection,
        custom_headers=custom_headers,
        extra_headers=extra_headers,
        forward_headers=forward_headers,
        set_cookies=set_cookies,
        block_resources=block_resources,
        block_ads=block_ads,
        output=output,
        transparent_response=transparent_response,
    )
    ok, err, shape = await _scrape_call(params)
    return ScrapeOutput(
        success=ok,
        error=err,
        status_code=shape.get("status_code"),
        content_type=shape.get("content_type"),
        data=shape.get("data"),
        is_binary=shape.get("is_binary", False),
        payload=shape.get("payload"),
    )


@tool(args_schema=ScrapeWithJsInput)
@serialize_pydantic_return
async def scrape_with_js(
    api_key: str,
    url: str,
    method: str | None = "GET",
    body: str | None = None,
    super_proxy: bool | None = None,
    geo_code: str | None = None,
    regional_geo_code: str | None = None,
    session_id: int | None = None,
    device: str | None = None,
    timeout: int | None = None,
    retry_timeout: int | None = None,
    disable_retry: bool | None = None,
    disable_redirection: bool | None = None,
    custom_headers: bool | None = None,
    extra_headers: bool | None = None,
    forward_headers: bool | None = None,
    set_cookies: str | None = None,
    block_resources: bool | None = None,
    block_ads: bool | None = None,
    output: str | None = None,
    wait_until: str | None = None,
    wait_selector: str | None = None,
    custom_wait: int | None = None,
    width: int | None = None,
    height: int | None = None,
    play_with_browser: str | None = None,
) -> ScrapeWithJsOutput:
    """Scrape with JavaScript rendering enabled."""
    if not api_key or not api_key.strip():
        return ScrapeWithJsOutput(success=False, error=_empty_key_error("scrape_with_js"))

    params = _build_params(
        api_key,
        url,
        render=True,
        method=method,
        body=body,
        super_proxy=super_proxy,
        geo_code=geo_code,
        regional_geo_code=regional_geo_code,
        session_id=session_id,
        device=device,
        timeout=timeout,
        retry_timeout=retry_timeout,
        disable_retry=disable_retry,
        disable_redirection=disable_redirection,
        custom_headers=custom_headers,
        extra_headers=extra_headers,
        forward_headers=forward_headers,
        set_cookies=set_cookies,
        block_resources=block_resources,
        block_ads=block_ads,
        output=output,
        wait_until=wait_until,
        wait_selector=wait_selector,
        custom_wait=custom_wait,
        width=width,
        height=height,
        play_with_browser=play_with_browser,
    )
    ok, err, shape = await _scrape_call(params)
    return ScrapeWithJsOutput(
        success=ok,
        error=err,
        status_code=shape.get("status_code"),
        content_type=shape.get("content_type"),
        data=shape.get("data"),
        is_binary=shape.get("is_binary", False),
        payload=shape.get("payload"),
    )


@tool(args_schema=TakeScreenshotInput)
@serialize_pydantic_return
async def take_screenshot(
    api_key: str,
    url: str,
    full_page: bool | None = False,
    selector: str | None = None,
    super_proxy: bool | None = None,
    geo_code: str | None = None,
    regional_geo_code: str | None = None,
    session_id: int | None = None,
    device: str | None = None,
    timeout: int | None = None,
    retry_timeout: int | None = None,
    disable_retry: bool | None = None,
    disable_redirection: bool | None = None,
    width: int | None = None,
    height: int | None = None,
    wait_until: str | None = None,
    wait_selector: str | None = None,
    custom_wait: int | None = None,
    block_ads: bool | None = None,
    custom_headers: bool | None = None,
    set_cookies: str | None = None,
) -> TakeScreenshotOutput:
    """Capture a webpage screenshot."""
    if not api_key or not api_key.strip():
        return TakeScreenshotOutput(success=False, error=_empty_key_error("take_screenshot"))
    if full_page and selector:
        return TakeScreenshotOutput(
            success=False,
            error="Choose either full_page or selector mode, not both",
        )

    # Three mutually-exclusive screenshot modes — pick exactly one.
    screen_shot = not full_page and not selector
    full_screen_shot = full_page
    particular_screen_shot = selector

    params = _build_params(
        api_key,
        url,
        render=True,
        return_json=True,
        block_resources=False,
        super_proxy=super_proxy,
        geo_code=geo_code,
        regional_geo_code=regional_geo_code,
        session_id=session_id,
        device=device,
        timeout=timeout,
        retry_timeout=retry_timeout,
        disable_retry=disable_retry,
        disable_redirection=disable_redirection,
        width=width,
        height=height,
        wait_until=wait_until,
        wait_selector=wait_selector,
        custom_wait=custom_wait,
        block_ads=block_ads,
        custom_headers=custom_headers,
        set_cookies=set_cookies,
        screen_shot=screen_shot,
        full_screen_shot=full_screen_shot,
        particular_screen_shot=particular_screen_shot,
    )
    ok, err, shape = await _scrape_call(params)
    return TakeScreenshotOutput(
        success=ok,
        error=err,
        status_code=shape.get("status_code"),
        content_type=shape.get("content_type"),
        data=shape.get("data"),
        is_binary=shape.get("is_binary", False),
        payload=shape.get("payload"),
    )


@tool(args_schema=ScrapeToMarkdownInput)
@serialize_pydantic_return
async def scrape_to_markdown(
    api_key: str,
    url: str,
    render: bool | None = False,
    method: str | None = "GET",
    body: str | None = None,
    super_proxy: bool | None = None,
    geo_code: str | None = None,
    regional_geo_code: str | None = None,
    session_id: int | None = None,
    device: str | None = None,
    timeout: int | None = None,
    retry_timeout: int | None = None,
    disable_retry: bool | None = None,
    disable_redirection: bool | None = None,
    block_resources: bool | None = None,
    block_ads: bool | None = None,
    custom_headers: bool | None = None,
    set_cookies: str | None = None,
    play_with_browser: str | None = None,
) -> ScrapeToMarkdownOutput:
    """Scrape a URL and convert HTML to markdown."""
    if not api_key or not api_key.strip():
        return ScrapeToMarkdownOutput(
            success=False, error=_empty_key_error("scrape_to_markdown")
        )

    params = _build_params(
        api_key,
        url,
        render=bool(render),
        output="markdown",
        method=method,
        body=body,
        super_proxy=super_proxy,
        geo_code=geo_code,
        regional_geo_code=regional_geo_code,
        session_id=session_id,
        device=device,
        timeout=timeout,
        retry_timeout=retry_timeout,
        disable_retry=disable_retry,
        disable_redirection=disable_redirection,
        block_resources=block_resources,
        block_ads=block_ads,
        custom_headers=custom_headers,
        set_cookies=set_cookies,
        play_with_browser=play_with_browser,
    )
    ok, err, shape = await _scrape_call(params)
    if not ok:
        return ScrapeToMarkdownOutput(
            success=False, error=err, status_code=shape.get("status_code")
        )

    markdown_text = shape.get("data")
    payload = shape.get("payload")
    # If the upstream gave JSON, try to lift markdown out of it.
    if payload and isinstance(payload, dict):
        markdown_text = payload.get("data") or payload.get("markdown") or markdown_text

    return ScrapeToMarkdownOutput(
        success=True, markdown=markdown_text, raw=payload
    )


@tool(args_schema=GetUsageStatsInput)
@serialize_pydantic_return
async def get_usage_stats(api_key: str) -> GetUsageStatsOutput:
    """Get Scrape.do API usage statistics for the current account."""
    if not api_key or not api_key.strip():
        return GetUsageStatsOutput(success=False, error=_empty_key_error("get_usage_stats"))

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/info", params={"token": api_key}
            )
        if response.status_code != 200:
            return GetUsageStatsOutput(
                success=False,
                status_code=response.status_code,
                error=(
                    f"API returned status code {response.status_code}: "
                    f"{response.text[:500]}"
                ),
            )
        try:
            body = response.json()
        except Exception:
            body = {"raw_response": response.text}
    except Exception as exc:
        return GetUsageStatsOutput(success=False, error=f"get_usage_stats failed: {exc}")

    return GetUsageStatsOutput(
        success=True,
        stats=body if isinstance(body, dict) else {"value": body},
    )

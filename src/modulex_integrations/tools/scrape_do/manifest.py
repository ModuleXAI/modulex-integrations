"""Scrape.do integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


def _proxy_and_device_params() -> dict[str, ParameterDef]:
    return {
        "super_proxy": ParameterDef(
            type="boolean",
            description="Use residential & mobile proxy network",
        ),
        "geo_code": ParameterDef(
            type="string",
            description="Country code for proxy location (e.g. 'us', 'uk', 'de')",
        ),
        "regional_geo_code": ParameterDef(
            type="string",
            description=(
                "Regional proxy location: 'europe', 'asia', 'africa', "
                "'oceania', 'northamerica', 'southamerica'"
            ),
        ),
        "session_id": ParameterDef(
            type="integer",
            description="Sticky session ID (0-1000000) for IP persistence",
        ),
        "device": ParameterDef(
            type="string",
            description="Device emulation ('desktop', 'mobile', 'tablet')",
        ),
    }


def _retry_params() -> dict[str, ParameterDef]:
    return {
        "timeout": ParameterDef(
            type="integer", description="Request timeout in ms (5000-120000)"
        ),
        "retry_timeout": ParameterDef(
            type="integer", description="Retry timeout in ms (5000-55000)"
        ),
        "disable_retry": ParameterDef(
            type="boolean", description="Disable automatic retry on failure"
        ),
        "disable_redirection": ParameterDef(
            type="boolean", description="Disable following redirects"
        ),
    }


def _scrape_common_params() -> dict[str, ParameterDef]:
    return {
        "url": ParameterDef(
            type="string", description="URL to scrape", required=True
        ),
        "method": ParameterDef(
            type="string",
            description="HTTP method (GET, POST, PUT, DELETE, HEAD)",
            default="GET",
        ),
        "body": ParameterDef(
            type="string", description="Request body for POST/PUT requests"
        ),
        **_proxy_and_device_params(),
        **_retry_params(),
        "custom_headers": ParameterDef(
            type="boolean", description="Let Scrape.do add default headers"
        ),
        "extra_headers": ParameterDef(
            type="boolean", description="Forward extra upstream headers"
        ),
        "forward_headers": ParameterDef(
            type="boolean", description="Forward client headers to target"
        ),
        "set_cookies": ParameterDef(
            type="string", description="Cookies to send (JSON string or header)"
        ),
        "block_resources": ParameterDef(
            type="boolean", description="Block images, CSS, fonts to speed up loading"
        ),
        "block_ads": ParameterDef(type="boolean", description="Block advertisements"),
        "output": ParameterDef(
            type="string", description="Output format ('raw' or 'markdown')"
        ),
    }


manifest = IntegrationManifest(
    name="scrape_do",
    display_name="Scrape.do",
    description=(
        "Enterprise-grade web scraping API with JavaScript rendering, "
        "proxy rotation, geo-targeting, and screenshot capture."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:scrapedo-themed",
    app_url="https://scrape.do",
    categories=["Web Search & Scraping", "data_extraction"],
    actions=[
        ActionDefinition(
            name="scrape",
            description=(
                "Perform basic web scraping without JavaScript rendering. "
                "Ideal for static websites and APIs."
            ),
            parameters={
                **_scrape_common_params(),
                "transparent_response": ParameterDef(
                    type="boolean",
                    description="Return the origin response body with no parsing",
                ),
            },
        ),
        ActionDefinition(
            name="scrape_with_js",
            description=(
                "Scrape JavaScript-rendered pages using headless browser. "
                "Essential for SPAs and dynamic content."
            ),
            parameters={
                **_scrape_common_params(),
                "wait_until": ParameterDef(
                    type="string",
                    description=(
                        "Wait condition: 'domcontentloaded', 'networkidle0', "
                        "'networkidle2', 'load'"
                    ),
                ),
                "wait_selector": ParameterDef(
                    type="string",
                    description="CSS selector to wait for before capturing",
                ),
                "custom_wait": ParameterDef(
                    type="integer", description="Additional wait time in ms"
                ),
                "width": ParameterDef(
                    type="integer", description="Browser viewport width", default=1920
                ),
                "height": ParameterDef(
                    type="integer", description="Browser viewport height", default=1080
                ),
                "play_with_browser": ParameterDef(
                    type="string",
                    description="JSON-encoded Play-with-Browser action list",
                ),
            },
        ),
        ActionDefinition(
            name="take_screenshot",
            description=(
                "Capture webpage screenshots: viewport, full-page, or "
                "element-specific."
            ),
            parameters={
                "url": ParameterDef(
                    type="string", description="URL to capture", required=True
                ),
                "full_page": ParameterDef(
                    type="boolean",
                    description="Capture full page instead of viewport",
                    default=False,
                ),
                "selector": ParameterDef(
                    type="string",
                    description="CSS selector for element-specific screenshot",
                ),
                **_proxy_and_device_params(),
                **_retry_params(),
                "width": ParameterDef(
                    type="integer", description="Viewport width", default=1920
                ),
                "height": ParameterDef(
                    type="integer", description="Viewport height", default=1080
                ),
                "wait_until": ParameterDef(
                    type="string", description="Wait condition for render completion"
                ),
                "wait_selector": ParameterDef(
                    type="string",
                    description="CSS selector to wait for before capturing",
                ),
                "custom_wait": ParameterDef(
                    type="integer", description="Additional wait time in ms"
                ),
                "block_ads": ParameterDef(
                    type="boolean", description="Block advertisements"
                ),
                "custom_headers": ParameterDef(
                    type="boolean",
                    description="Let Scrape.do add default headers",
                ),
                "set_cookies": ParameterDef(
                    type="string", description="Cookies to send"
                ),
            },
        ),
        ActionDefinition(
            name="scrape_to_markdown",
            description=(
                "Scrape web pages and convert content to clean, readable "
                "markdown format."
            ),
            parameters={
                "url": ParameterDef(
                    type="string", description="URL to scrape", required=True
                ),
                "render": ParameterDef(
                    type="boolean",
                    description="Enable JavaScript rendering",
                    default=False,
                ),
                "method": ParameterDef(
                    type="string", description="HTTP method", default="GET"
                ),
                "body": ParameterDef(
                    type="string", description="Request body for POST/PUT"
                ),
                **_proxy_and_device_params(),
                **_retry_params(),
                "block_resources": ParameterDef(
                    type="boolean",
                    description="Block images, CSS, fonts to speed up loading",
                ),
                "block_ads": ParameterDef(
                    type="boolean", description="Block advertisements"
                ),
                "custom_headers": ParameterDef(
                    type="boolean",
                    description="Let Scrape.do inject default headers",
                ),
                "set_cookies": ParameterDef(
                    type="string", description="Cookies to send"
                ),
                "play_with_browser": ParameterDef(
                    type="string",
                    description="JSON-encoded Play-with-Browser script",
                ),
            },
        ),
        ActionDefinition(
            name="get_usage_stats",
            description=(
                "Get API usage statistics and remaining credits for your "
                "Scrape.do account."
            ),
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Scrape.do API key",
            setup_environment_variables=[
                EnvVar(
                    name="SCRAPEDO_API_KEY",
                    display_name="Scrape.do API Key",
                    description="Your Scrape.do API key for authentication",
                    required=True,
                    sensitive=True,
                    sample_format="x" * 32,
                    about_url="https://scrape.do/documentation/",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.scrape.do/info?token={api_key}",
                method="GET",
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description="Validates API key by checking account info (no API cost)",
            ),
        ),
    ],
)

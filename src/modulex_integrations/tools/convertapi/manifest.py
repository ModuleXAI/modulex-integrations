"""ConvertAPI integration manifest."""
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


manifest = IntegrationManifest(
    name="convertapi",
    display_name="ConvertAPI",
    description=(
        "Powerful file conversion service supporting hundreds of format "
        "conversions including documents, images, spreadsheets, and web "
        "pages to PDF/JPG."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:convertapi",
    app_url="https://www.convertapi.com",
    categories=["Utilities", "convert", "documents"],
    actions=[
        ActionDefinition(
            name="convert_file",
            description=(
                "Convert a file from a URL to another format. Supports "
                "hundreds of conversions including PDF, DOCX, JPG, PNG, "
                "XLSX, and more."
            ),
            parameters={
                "file_url": ParameterDef(
                    type="string",
                    description="URL of the file to convert",
                    required=True,
                ),
                "format_from": ParameterDef(
                    type="string",
                    description="Input file format (e.g. 'docx', 'pdf', 'png')",
                    required=True,
                ),
                "format_to": ParameterDef(
                    type="string",
                    description="Output file format (e.g. 'pdf', 'jpg', 'docx')",
                    required=True,
                ),
                "filename": ParameterDef(
                    type="string",
                    description="Output filename without extension",
                ),
                "timeout": ParameterDef(
                    type="integer",
                    description="Conversion timeout in seconds",
                    default=300,
                ),
            },
        ),
        ActionDefinition(
            name="convert_base64_file",
            description=(
                "Convert a base64-encoded file to another format. Useful "
                "when file content is already in memory."
            ),
            parameters={
                "base64_string": ParameterDef(
                    type="string",
                    description="Base64-encoded file content",
                    required=True,
                ),
                "format_from": ParameterDef(
                    type="string",
                    description="Input file format (e.g. 'docx', 'pdf')",
                    required=True,
                ),
                "format_to": ParameterDef(
                    type="string",
                    description="Output file format (e.g. 'pdf', 'jpg')",
                    required=True,
                ),
                "filename": ParameterDef(
                    type="string",
                    description="Output filename without extension",
                    default="converted",
                ),
                "timeout": ParameterDef(
                    type="integer",
                    description="Conversion timeout in seconds",
                    default=300,
                ),
            },
        ),
        ActionDefinition(
            name="convert_web_url",
            description=(
                "Convert a web page URL to PDF or JPG. Renders the page and "
                "captures it as a document or image."
            ),
            parameters={
                "url": ParameterDef(
                    type="string",
                    description="Website URL to convert",
                    required=True,
                ),
                "format_to": ParameterDef(
                    type="string",
                    description="Output format: 'pdf' or 'jpg'",
                    default="pdf",
                ),
                "filename": ParameterDef(
                    type="string",
                    description="Output filename without extension",
                ),
                "timeout": ParameterDef(
                    type="integer",
                    description="Conversion timeout in seconds",
                    default=300,
                ),
                "conversion_delay": ParameterDef(
                    type="integer",
                    description="Delay in seconds to let page fully load before conversion",
                ),
                "page_orientation": ParameterDef(
                    type="string",
                    description="PDF page orientation ('portrait' or 'landscape')",
                ),
                "page_size": ParameterDef(
                    type="string",
                    description="PDF page size (e.g. 'a4', 'letter', 'legal')",
                ),
                "javascript": ParameterDef(
                    type="boolean",
                    description="Allow web pages to run JavaScript",
                    default=True,
                ),
                "ad_block": ParameterDef(
                    type="boolean",
                    description="Block ads in the converting page",
                    default=False,
                ),
                "cookie_consent_block": ParameterDef(
                    type="boolean",
                    description="Try to remove cookie consent popups",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_supported_formats",
            description=(
                "Get the list of supported output formats for a given input "
                "format. Use this to discover available conversions."
            ),
            parameters={
                "format_from": ParameterDef(
                    type="string",
                    description="Input format to check (e.g. 'docx', 'pdf', 'png')",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your ConvertAPI Secret key",
            setup_environment_variables=[
                EnvVar(
                    name="CONVERTAPI_API_KEY",
                    display_name="ConvertAPI Secret",
                    description="Your ConvertAPI Secret key for authentication",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://www.convertapi.com/a",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://v2.convertapi.com/user?Secret={api_key}",
                method="GET",
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["SecondsLeft"]
                ),
                cost_level="free",
                description="Validates API key by checking account status (no conversion cost)",
            ),
        ),
    ],
)

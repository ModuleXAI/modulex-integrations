"""Pulse integration manifest.

Pulse is an OCR / document-parsing service (``api.runpulse.com``) that
extracts clean markdown and structured data from PDFs, images, and
Office files. Authentication is a single API key sent as the
``x-api-key`` header.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="pulse",
    display_name="Pulse",
    description=(
        "Extract text and structured content from PDFs, images, and Office "
        "files using Pulse OCR. Returns clean markdown, page counts, layout "
        "bounding boxes, chunks, and extracted figures."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:pulse",
    app_url="https://www.runpulse.com",
    categories=["AI & Machine Learning", "document-processing", "ocr"],
    actions=[
        ActionDefinition(
            name="parser",
            description=(
                "Parse a document (PDF, image, or Office file) from a public "
                "URL using Pulse OCR and return clean markdown, page count, "
                "layout bounding boxes, optional HTML, chunks, and figures."
            ),
            parameters={
                "file_url": ParameterDef(
                    type="string",
                    description=(
                        "Public HTTP(S) URL to a document to process "
                        "(PDF, image, or Office file)"
                    ),
                    required=True,
                ),
                "pages": ParameterDef(
                    type="string",
                    description=(
                        'Page range to process, 1-indexed (e.g. "1-2,5"). '
                        "Omit for all pages."
                    ),
                ),
                "chunking": ParameterDef(
                    type="string",
                    description=(
                        "Chunking strategies (comma-separated: semantic, "
                        "header, page, recursive)"
                    ),
                ),
                "chunk_size": ParameterDef(
                    type="integer",
                    description="Maximum characters per chunk when chunking is enabled",
                ),
                "return_html": ParameterDef(
                    type="boolean",
                    description="Whether to include HTML in the response",
                ),
                "extract_figure": ParameterDef(
                    type="boolean",
                    description="Whether to extract figures from the document",
                ),
                "figure_description": ParameterDef(
                    type="boolean",
                    description="Whether to generate descriptions/captions for extracted figures",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Pulse API key",
            setup_instructions=[
                "Go to https://www.runpulse.com and sign up or log in",
                "Open your dashboard and navigate to the API keys section",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="PULSE_API_KEY",
                    display_name="Pulse API Key",
                    description="Your Pulse API key from the runpulse.com dashboard",
                    required=True,
                    sensitive=True,
                    about_url="https://docs.runpulse.com/authentication",
                ),
            ],
        ),
    ],
)

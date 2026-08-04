"""LaTeX integration manifest.

The public LaTeX-on-HTTP service at ``https://latex.ytotech.com`` is open —
it accepts no API key, no OAuth token, and no other credential. Every action
is a plain unauthenticated GET.

The declared ``modulex_key`` schema therefore validates nothing: it exists
so the credential-resolution step the runtime performs before every tool
call has something to resolve. The same approach is used by the other
credential-free integrations in this package. Each ``@tool`` accepts an
``api_key`` argument for signature uniformity and ignores it.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    IntegrationManifest,
    ModulexKeyAuthSchema,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="latex",
    display_name="LaTeX",
    description=(
        "Look up the typesetting resources available on the public "
        "LaTeX-on-HTTP service at latex.ytotech.com. Search the installed "
        "TeX Live package collection by name or description, read a single "
        "package's full metadata (license, category, CTAN topics, related "
        "packages, homepage), and list the system fonts the LaTeX compilers "
        "can address with fontspec — useful for checking, before a document "
        "is written, that the packages and fonts it relies on are actually "
        "available."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:latex",
    app_url="https://www.latex-project.org",
    categories=["Productivity & Collaboration", "documents", "typesetting", "publishing"],
    actions=[
        ActionDefinition(
            name="search_packages",
            description=(
                "Search the TeX Live packages available to the LaTeX compiler by "
                "name or description, e.g. to check which packages can be used in "
                "a document."
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description=(
                        "Search terms matched against package names and "
                        "descriptions, e.g. 'chemistry' or 'tikz'"
                    ),
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of packages to return (default: 25, max: 100)",
                    default=25,
                ),
            },
        ),
        ActionDefinition(
            name="get_package",
            description=(
                "Get details about a specific TeX Live package available to the "
                "LaTeX compiler, including whether it is installed, its "
                "description, license, and related packages."
            ),
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Exact package name, e.g. amsmath, tikz, or biblatex",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_fonts",
            description=(
                "List the system fonts available to the LaTeX compiler, optionally "
                "filtered by name, e.g. to pick a font for xelatex or lualatex "
                "documents using fontspec."
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description=(
                        "Filter matched against font family and full font name, "
                        "e.g. 'Noto Serif'. Omit to list every available font."
                    ),
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of fonts to return (default: 50, max: 200)",
                    default=50,
                ),
            },
        ),
    ],
    auth_schemas=[
        ModulexKeyAuthSchema(
            display_name="ModuleX Managed Key",
            description=(
                "Use ModuleX's managed access (the LaTeX-on-HTTP API is public, "
                "no authentication required)"
            ),
            test_endpoint=TestEndpoint(
                url="https://latex.ytotech.com/",
                method="GET",
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description=(
                    "Reachability check against the public LaTeX-on-HTTP service "
                    "root, which answers with the API and TeX Live versions. "
                    "There is no credential to validate; this only confirms the "
                    "service is reachable."
                ),
            ),
        ),
    ],
)

"""NPM integration manifest."""
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
    name="npm",
    display_name="NPM Registry",
    description=(
        "Access the npm registry to search packages, get package information, "
        "versions, dependencies, and download statistics"
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:npm-icon",
    categories=[
        "Developer Tools & Infrastructure",
        "coding",
        "package_management",
        "developer_tools",
    ],
    actions=[
        ActionDefinition(
            name="get_package_info",
            description=(
                "Get detailed information about an npm package including name, "
                "version, description, author, homepage, repository, and dependencies"
            ),
            parameters={
                "package_name": ParameterDef(
                    type="string",
                    description="The name of the npm package to look up",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search_packages",
            description="Search for npm packages by keyword or name",
            parameters={
                "query": ParameterDef(
                    type="string", description="Search query text", required=True
                ),
                "size": ParameterDef(
                    type="integer",
                    description="Number of results to return (1-250)",
                    default=10,
                ),
            },
        ),
        ActionDefinition(
            name="get_popular_packages",
            description="Get a list of popular npm packages sorted by popularity score",
            parameters={
                "size": ParameterDef(
                    type="integer",
                    description="Number of popular packages to return (1-250)",
                    default=10,
                ),
            },
        ),
        ActionDefinition(
            name="get_package_versions",
            description=(
                "Get all available versions of an npm package with publication "
                "dates and dist-tags"
            ),
            parameters={
                "package_name": ParameterDef(
                    type="string", description="The name of the npm package", required=True
                ),
            },
        ),
        ActionDefinition(
            name="get_package_dependencies",
            description=(
                "Get the dependencies, devDependencies, and peerDependencies "
                "of an npm package"
            ),
            parameters={
                "package_name": ParameterDef(
                    type="string", description="The name of the npm package", required=True
                ),
                "version": ParameterDef(
                    type="string",
                    description="Specific version (defaults to latest)",
                ),
            },
        ),
        ActionDefinition(
            name="get_package_download_stats",
            description=(
                "Get download statistics for an npm package including total "
                "and daily download counts"
            ),
            parameters={
                "package_name": ParameterDef(
                    type="string", description="The name of the npm package", required=True
                ),
                "period": ParameterDef(
                    type="string",
                    description="Time period for download statistics",
                    default="last-week",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description=(
                "Optional authentication for private npm registries. Leave empty "
                "for public npm registry access."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="NPM_API_KEY",
                    display_name="NPM API Key",
                    description=(
                        "Your npm authentication token (optional for public registry)"
                    ),
                    required=False,
                    sensitive=True,
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://registry.npmjs.org/-/v1/search",
                method="GET",
                headers={"Accept": "application/json"},
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description="Validates registry connectivity via a minimal search",
            ),
        ),
    ],
)

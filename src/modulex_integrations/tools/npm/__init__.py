"""NPM Registry integration."""
from modulex_integrations.tools.npm.manifest import manifest
from modulex_integrations.tools.npm.tools import (
    get_package_dependencies,
    get_package_download_stats,
    get_package_info,
    get_package_versions,
    get_popular_packages,
    search_packages,
)

TOOLS = (
    get_package_info,
    search_packages,
    get_popular_packages,
    get_package_versions,
    get_package_dependencies,
    get_package_download_stats,
)

__all__ = [
    "TOOLS",
    "get_package_dependencies",
    "get_package_download_stats",
    "get_package_info",
    "get_package_versions",
    "get_popular_packages",
    "manifest",
    "search_packages",
]

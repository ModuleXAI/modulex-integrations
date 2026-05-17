"""ConvertAPI integration."""
from modulex_integrations.tools.convertapi.manifest import manifest
from modulex_integrations.tools.convertapi.tools import (
    convert_base64_file,
    convert_file,
    convert_web_url,
    get_supported_formats,
)

TOOLS = (convert_file, convert_base64_file, convert_web_url, get_supported_formats)

__all__ = [
    "TOOLS",
    "convert_base64_file",
    "convert_file",
    "convert_web_url",
    "get_supported_formats",
    "manifest",
]

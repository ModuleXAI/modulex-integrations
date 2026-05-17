"""Pinterest integration."""
from modulex_integrations.tools.pinterest.manifest import manifest
from modulex_integrations.tools.pinterest.tools import (
    create_pin,
    get_board_sections,
    list_boards,
    list_pins,
)

TOOLS = (list_boards, get_board_sections, create_pin, list_pins)

__all__ = [
    "TOOLS",
    "create_pin",
    "get_board_sections",
    "list_boards",
    "list_pins",
    "manifest",
]

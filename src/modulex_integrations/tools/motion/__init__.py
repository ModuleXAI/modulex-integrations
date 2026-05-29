"""Motion integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.motion.manifest import manifest
from modulex_integrations.tools.motion.tools import (
    create_task,
    delete_task,
    get_schedules,
    get_task,
    move_workspace,
    update_task,
)

TOOLS = (
    create_task,
    delete_task,
    get_schedules,
    get_task,
    move_workspace,
    update_task,
)

__all__ = [
    "TOOLS",
    "create_task",
    "delete_task",
    "get_schedules",
    "get_task",
    "manifest",
    "move_workspace",
    "update_task",
]

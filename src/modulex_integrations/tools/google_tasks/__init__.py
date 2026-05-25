"""Google Tasks integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_tasks.manifest import manifest
from modulex_integrations.tools.google_tasks.tools import (
    create_task,
    create_task_list,
    delete_task,
    delete_task_list,
    list_task_lists,
    list_tasks,
    update_task,
    update_task_list,
)

TOOLS = (
    create_task,
    create_task_list,
    delete_task,
    delete_task_list,
    list_tasks,
    list_task_lists,
    update_task,
    update_task_list,
)

__all__ = [
    "TOOLS",
    "create_task",
    "create_task_list",
    "delete_task",
    "delete_task_list",
    "list_task_lists",
    "list_tasks",
    "manifest",
    "update_task",
    "update_task_list",
]

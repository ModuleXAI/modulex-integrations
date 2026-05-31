"""Canvas LMS integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.canvas.manifest import manifest
from modulex_integrations.tools.canvas.tools import (
    list_accounts,
    list_assignments,
    list_courses,
    search_course_content,
    update_assignment,
)

TOOLS = (
    list_accounts,
    list_assignments,
    list_courses,
    search_course_content,
    update_assignment,
)

__all__ = [
    "TOOLS",
    "list_accounts",
    "list_assignments",
    "list_courses",
    "manifest",
    "search_course_content",
    "update_assignment",
]

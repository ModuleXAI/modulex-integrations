"""Google My Business integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_my_business.manifest import manifest
from modulex_integrations.tools.google_my_business.tools import (
    create_post,
    create_update_reply_to_review,
    get_reviews_multiple_locations,
    get_specific_review,
    list_all_reviews,
    list_posts,
)

TOOLS = (
    create_post,
    create_update_reply_to_review,
    get_reviews_multiple_locations,
    get_specific_review,
    list_all_reviews,
    list_posts,
)

__all__ = [
    "TOOLS",
    "create_post",
    "create_update_reply_to_review",
    "get_reviews_multiple_locations",
    "get_specific_review",
    "list_all_reviews",
    "list_posts",
    "manifest",
]

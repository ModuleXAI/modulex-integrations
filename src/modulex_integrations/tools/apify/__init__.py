"""Apify integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.apify.manifest import manifest
from modulex_integrations.tools.apify.tools import (
    get_dataset_items,
    get_kvs_record,
    run_actor,
    run_task,
    run_task_synchronously,
    scrape_single_url,
    set_key_value_store_record,
)

TOOLS = (
    run_actor,
    run_task,
    run_task_synchronously,
    get_dataset_items,
    get_kvs_record,
    scrape_single_url,
    set_key_value_store_record,
)

__all__ = [
    "TOOLS",
    "get_dataset_items",
    "get_kvs_record",
    "manifest",
    "run_actor",
    "run_task",
    "run_task_synchronously",
    "scrape_single_url",
    "set_key_value_store_record",
]

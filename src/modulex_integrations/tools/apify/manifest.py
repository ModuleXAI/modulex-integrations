"""Apify integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    BearerTokenAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="apify",
    display_name="Apify",
    description="Web scraping, automation, and data extraction platform via the Apify REST API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:apify-themed",
    app_url="https://apify.com",
    categories=["Web Search & Scraping", "Developer Tools & Infrastructure", "automation"],
    actions=[
        ActionDefinition(
            name="run_actor",
            description="Run an Apify Actor and return the run metadata",
            parameters={
                "actor_id": ParameterDef(
                    type="string",
                    description="The Actor ID or tilde-separated owner/name identifier (e.g. 'apify~web-scraper')",
                    required=True,
                ),
                "run_input": ParameterDef(
                    type="object",
                    description="JSON object with the input for the Actor run",
                ),
                "build_tag": ParameterDef(
                    type="string",
                    description="Specifies the Actor build to run. If not provided, the default build is used.",
                ),
                "run_asynchronously": ParameterDef(
                    type="boolean",
                    description="If true, returns immediately with run metadata. If false, waits for completion.",
                    default=True,
                ),
                "timeout": ParameterDef(
                    type="integer",
                    description="Optional timeout for the run, in seconds",
                ),
                "memory": ParameterDef(
                    type="integer",
                    description="Memory limit for the run, in megabytes (power of 2, min 128)",
                ),
                "max_items": ParameterDef(
                    type="integer",
                    description="The maximum number of items that the Actor run should return",
                ),
            },
        ),
        ActionDefinition(
            name="run_task",
            description="Start an Apify task and return its run metadata",
            parameters={
                "task_id": ParameterDef(
                    type="string",
                    description="The ID of the task to run",
                    required=True,
                ),
                "override_input": ParameterDef(
                    type="string",
                    description="Optional JSON string to override the default input for the task run",
                ),
                "timeout": ParameterDef(
                    type="integer",
                    description="Optional timeout for the run, in seconds",
                ),
                "memory": ParameterDef(
                    type="integer",
                    description="Memory limit for the run, in megabytes (power of 2, min 128)",
                ),
                "build": ParameterDef(
                    type="string",
                    description="Specifies the Actor build to run (build tag or number)",
                ),
            },
        ),
        ActionDefinition(
            name="run_task_synchronously",
            description="Run an Apify task synchronously and return its dataset items",
            parameters={
                "task_id": ParameterDef(
                    type="string",
                    description="The ID of the task to run",
                    required=True,
                ),
                "timeout": ParameterDef(
                    type="integer",
                    description="Optional timeout for the run, in seconds",
                ),
                "memory": ParameterDef(
                    type="integer",
                    description="Memory limit for the run, in megabytes (power of 2, min 128)",
                ),
                "build": ParameterDef(
                    type="string",
                    description="Specifies the Actor build to run (build tag or number)",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="The maximum number of dataset items to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="get_dataset_items",
            description="Retrieve items from an Apify dataset",
            parameters={
                "dataset_id": ParameterDef(
                    type="string",
                    description="The ID of the dataset to retrieve items from",
                    required=True,
                ),
                "offset": ParameterDef(
                    type="integer",
                    description="The number of records to skip before returning results",
                    default=0,
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="The maximum number of items to return",
                    default=100,
                ),
                "clean": ParameterDef(
                    type="boolean",
                    description="Return only non-empty items and skip hidden fields (fields starting with #)",
                ),
                "fields": ParameterDef(
                    type="string",
                    description="Comma-separated list of field names to include in results",
                ),
            },
        ),
        ActionDefinition(
            name="get_kvs_record",
            description="Get a record from an Apify key-value store",
            parameters={
                "key_value_store_id": ParameterDef(
                    type="string",
                    description="The ID of the key-value store",
                    required=True,
                ),
                "key": ParameterDef(
                    type="string",
                    description="The key of the record to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="scrape_single_url",
            description="Scrape a single URL using Apify's Web Content Crawler and return its content",
            parameters={
                "url": ParameterDef(
                    type="string",
                    description="The URL of the web page to scrape",
                    required=True,
                ),
                "crawler_type": ParameterDef(
                    type="string",
                    description="Crawling engine: 'playwright:firefox' (stealthy), 'playwright:chrome', 'cheerio' (fast, static only), 'playwright:adaptive' (auto-switches)",
                    default="playwright:firefox",
                ),
            },
        ),
        ActionDefinition(
            name="set_key_value_store_record",
            description="Create or update a record in an Apify key-value store",
            parameters={
                "key_value_store_id": ParameterDef(
                    type="string",
                    description="The ID of the key-value store",
                    required=True,
                ),
                "key": ParameterDef(
                    type="string",
                    description="The key of the record to create or update",
                    required=True,
                ),
                "value": ParameterDef(
                    type="string",
                    description="The value to store. Valid JSON strings are stored as JSON; otherwise as plain text.",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        BearerTokenAuthSchema(
            display_name="API Token",
            description="Authenticate using your Apify API token",
            setup_instructions=[
                "Go to https://console.apify.com/account/integrations",
                "Copy your Personal API token",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="APIFY_API_TOKEN",
                    display_name="API Token",
                    description="Your Apify API token from the Integrations page",
                    required=True,
                    sensitive=True,
                    sample_format="apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://console.apify.com/account/integrations",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.apify.com/v2/users/me",
                method="GET",
                headers={"Authorization": "Bearer {bearer_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data"],
                ),
                cost_level="free",
                description="Validates the API token by fetching the authenticated user info",
            ),
        ),
    ],
)

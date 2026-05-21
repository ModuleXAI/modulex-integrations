# Apify

Web scraping, automation, and data extraction platform via the Apify REST API (`api.apify.com/v2`).

## Authentication

### API Token

- Sign in at [console.apify.com](https://console.apify.com/account/integrations) and copy your Personal API token from the Integrations page.
- Required env var: `APIFY_API_TOKEN` (format: `apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

## Tools

| name | description | required params |
| --- | --- | --- |
| `run_actor` | Run an Apify Actor and return the run metadata | `actor_id` |
| `run_task` | Start an Apify task and return its run metadata | `task_id` |
| `run_task_synchronously` | Run an Apify task synchronously and return its dataset items | `task_id` |
| `get_dataset_items` | Retrieve items from an Apify dataset | `dataset_id` |
| `get_kvs_record` | Get a record from an Apify key-value store | `key_value_store_id`, `key` |
| `scrape_single_url` | Scrape a single URL using Apify's Web Content Crawler and return its content | `url` |
| `set_key_value_store_record` | Create or update a record in an Apify key-value store | `key_value_store_id`, `key`, `value` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential.

## Limits & Quotas

- Rate limits depend on Apify plan: Free tier has limited concurrent runs; paid plans scale to hundreds.
- Actor runs are billed by compute units (CU) based on memory and duration.
- Synchronous run endpoints have a default server timeout of 300 seconds.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.

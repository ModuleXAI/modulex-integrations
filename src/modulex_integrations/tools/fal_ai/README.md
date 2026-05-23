# fal.ai

Queue-based AI model inference via the fal.ai platform API (`queue.fal.run/fal-ai`). Submit requests to run generative AI models asynchronously, monitor their status, retrieve results, and cancel pending tasks.

## Authentication

### API Key

- Sign in at <https://fal.ai/dashboard/keys> and create or copy your API key.
- Required env var: `FAL_AI_API_KEY` (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).
- The key is sent as `Authorization: Key <api_key>` (non-standard prefix).

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_request_to_queue` | Adds a request to the queue for asynchronous processing, including specifying a webhook URL for receiving updates | `app_id`, `data` |
| `cancel_request` | Cancels a request in the queue to stop a long-running task that is no longer needed | `app_id`, `request_id` |
| `get_request_response` | Gets the response of a completed request in the queue to retrieve results of an asynchronous task | `app_id`, `request_id` |
| `get_request_status` | Gets the status of a request in the queue to monitor the progress of an asynchronous task | `app_id`, `request_id` |

Every tool takes an additional `api_key` parameter that the runtime fills in from the resolved credential.

## Limits & Quotas

- Rate limits depend on your fal.ai plan tier (free tier has limited concurrent requests).
- Requests are queued; queue position is returned in status responses.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.

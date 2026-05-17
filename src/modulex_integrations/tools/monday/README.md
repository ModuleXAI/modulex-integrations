# Monday.com

Work management platform for creating and managing boards, items, columns, groups, and updates via the Monday.com GraphQL API (`api.monday.com/v2`).

## Authentication

### API Key Authentication

- Sign in to Monday.com, click your avatar (bottom left) and select **Developers**.
- Navigate to **My Access Tokens** and copy your personal API token.
- Required env var: `MONDAY_API_KEY` (format: `eyJhbGciOiJIUzI1NiJ9...`)
- Reference: <https://developer.monday.com/api-reference/docs/authentication>

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_board` | Creates a new board | `board_name`, `board_kind` |
| `create_column` | Creates a column in a board | `board_id`, `title`, `column_type` |
| `create_group` | Creates a new group in a specific board | `board_id`, `group_name` |
| `create_item` | Creates an item in a board | `board_id`, `item_name` |
| `create_subitem` | Creates a subitem under a parent item | `board_id`, `parent_item_id`, `item_name` |
| `create_update` | Creates a new update (comment) on an item | `board_id`, `item_id`, `update_body` |
| `get_board_items_page` | Retrieves items from a board with optional filtering | `board_id` |
| `get_column_values` | Returns values of specific columns for a board item | `board_id`, `item_id` |
| `get_items_by_column_value` | Searches a column for items matching a specific value | `board_id`, `column_id`, `value` |
| `list_boards` | Lists boards with optional filters for kind, state, and workspace | _(none)_ |
| `list_workspaces` | Retrieves available workspaces with their IDs and names | _(none)_ |
| `update_column_values` | Updates multiple column values for an item | `board_id`, `item_id`, `column_values` |
| `update_item_name` | Updates an item's name | `board_id`, `item_id`, `item_name` |

Every tool takes an additional `api_key` parameter that the runtime fills in from the resolved credential.

## Limits & Quotas

- **Rate limits**: Monday.com uses a complexity-based rate limit system. Each query has a complexity cost; the default limit is 10,000,000 complexity points per minute.
- **Pagination**: Board items are paginated with a default page size of 500 items per request. The integration handles cursor-based pagination internally for `get_board_items_page` and `get_items_by_column_value`.
- **Error model**: GraphQL errors and non-2xx responses are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.

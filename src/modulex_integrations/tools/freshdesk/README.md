# Freshdesk

Customer support helpdesk platform for managing tickets, contacts, agents, and knowledge base articles via the Freshdesk REST API (`{domain}.freshdesk.com/api/v2`).

## Authentication

### API Key Authentication

- Log in to your Freshdesk account, click your profile picture, and go to **Profile Settings**. Your API key is displayed on the right side.
- Required env vars:
  - `FRESHDESK_DOMAIN` (format: `mycompany` — the subdomain from `mycompany.freshdesk.com`)
  - `FRESHDESK_API_KEY` (format: `xXxXxXxXxXxXxXxXxXxX`)
- The API uses HTTP Basic Auth where the API key is the username and `X` is the password.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_ticket` | Create a new support ticket in Freshdesk | `subject`, `description`, `email` |
| `get_ticket` | Retrieve a specific ticket by its ID | `ticket_id` |
| `update_ticket` | Update an existing ticket's properties | `ticket_id` |
| `list_all_tickets` | List tickets in Freshdesk with optional filtering | |
| `close_ticket` | Close a ticket by setting its status to Closed (5) | `ticket_id` |
| `add_note_to_ticket` | Add a private or public note to a ticket | `ticket_id`, `body` |
| `add_ticket_tags` | Add tags to an existing ticket | `ticket_id`, `tags` |
| `remove_ticket_tags` | Remove tags from an existing ticket | `ticket_id`, `tags` |
| `set_ticket_tags` | Replace all tags on a ticket with the specified set | `ticket_id`, `tags` |
| `set_ticket_priority` | Set the priority of a ticket | `ticket_id`, `priority` |
| `set_ticket_status` | Set the status of a ticket | `ticket_id`, `status` |
| `assign_ticket_to_agent` | Assign a ticket to a specific agent | `ticket_id`, `agent_id` |
| `assign_ticket_to_group` | Assign a ticket to a specific group | `ticket_id`, `group_id` |
| `create_contact` | Create a new contact in Freshdesk | `email`, `name` |
| `get_contact` | Retrieve a contact by their ID | `contact_id` |
| `update_contact` | Update an existing contact's properties | `contact_id` |
| `create_company` | Create a new company in Freshdesk | `name` |
| `create_agent` | Create a new agent in Freshdesk | `email`, `ticket_scope` |
| `update_agent` | Update an existing agent's properties | `agent_id` |
| `get_agent` | Retrieve a single agent by their ID | `agent_id` |
| `list_agents` | List all agents in Freshdesk with optional filtering | |
| `create_reply` | Create a reply to a ticket | `ticket_id`, `body` |
| `forward_ticket` | Forward a ticket to an external email address | `ticket_id`, `body`, `to_emails` |
| `reply_to_forward` | Reply to a previously forwarded ticket email | `ticket_id`, `body`, `to_emails` |
| `create_thread` | Create a collaboration thread on a ticket | `ticket_id`, `type`, `email_config_id` |
| `create_message_for_thread` | Create a message in a collaboration thread | `ticket_id`, `thread_id`, `body` |
| `list_ticket_conversations` | List all conversations (notes, replies) for a ticket | `ticket_id` |
| `list_ticket_fields` | List all ticket fields configured in Freshdesk | |
| `create_ticket_field` | Create a new custom ticket field | `label`, `label_for_customers`, `type` |
| `update_ticket_field` | Update a custom ticket field | `ticket_field_id` |
| `create_solution_article` | Create a knowledge base article in a folder | `folder_id`, `title`, `description`, `status` |
| `get_solution_article` | Retrieve a knowledge base article by its ID | `article_id` |
| `update_solution_article` | Update a knowledge base article | `article_id` |
| `delete_solution_article` | Delete a knowledge base article | `article_id` |
| `search_solution_article` | Search knowledge base articles by keyword | `term` |
| `list_solution_categories` | List all knowledge base solution categories | |
| `list_category_folders` | List all folders within a solution category | `category_id` |
| `list_folder_articles` | List all articles within a solution folder | `folder_id` |
| `list_all_folders` | List all canned response folders | |
| `list_folder_canned_responses` | List all canned responses in a specific folder | `canned_response_folder_id` |
| `get_canned_response` | Retrieve a specific canned response by ID | `canned_response_id` |
| `get_folder_canned_responses` | Get detailed canned responses from a folder | `canned_response_folder_id` |
| `list_companies` | List all companies in Freshdesk | |
| `list_email_configs` | List all email configurations | |
| `list_roles` | List all agent roles | |

Every tool takes additional `domain` and `api_key` parameters that the runtime fills in from the resolved credential.

## Limits & Quotas

- **Rate limits**: Freshdesk applies per-plan rate limits. Free plans: 50 calls/min. Growth and above: 200-400+ calls/min depending on plan.
- **Pagination**: List endpoints return up to 100 results per page by default.
- **Error model**: non-2xx responses are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.

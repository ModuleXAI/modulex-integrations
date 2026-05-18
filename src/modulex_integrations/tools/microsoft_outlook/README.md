# Microsoft Outlook

Send, draft, search, and organize email; manage contacts, folders, and categories in Microsoft Outlook via Microsoft Graph (`graph.microsoft.com/v1.0`). Uses delegated permissions on behalf of an authenticated Microsoft 365 user.

## Authentication

### OAuth2 Authentication

- Register an application at <https://entra.microsoft.com> (Azure AD > App registrations).
- Under "Authentication", add the redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`.
- Under "API permissions", add Microsoft Graph delegated permissions: `Mail.ReadWrite`, `Mail.Send`, `MailboxSettings.Read`, `Contacts.ReadWrite`, `User.Read`, `User.ReadBasic.All`, `offline_access`.
- Under "Certificates & secrets", create a new client secret.
- Required env vars:
  - `MICROSOFT_OUTLOOK_OAUTH2_CLIENT_ID` (format: `00000000-0000-0000-0000-000000000000`)
  - `MICROSOFT_OUTLOOK_OAUTH2_CLIENT_SECRET`
- Scopes requested: `offline_access`, `User.Read`, `User.ReadBasic.All`, `Mail.ReadWrite`, `Mail.Send`, `MailboxSettings.Read`, `Contacts.ReadWrite`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_label_to_email` | Adds a label/category to an email in Microsoft Outlook. | `message_id`, `label` |
| `approve_workflow` | Send an email containing approve/cancel URLs so a recipient can resume or cancel a workflow externally. | `recipients`, `subject`, `resume_url`, `cancel_url` |
| `create_contact` | Add a contact to the root Contacts folder. |  |
| `create_draft_email` | Create a draft email. |  |
| `create_draft_reply` | Create a draft reply to an email. | `message_id` |
| `download_attachment` | Downloads an attachment from a message and returns it as base64-encoded content with metadata. | `message_id`, `attachment_id` |
| `find_contacts` | Finds contacts with the given search string. | `search_string` |
| `find_email` | Search for an email in Microsoft Outlook. `$search` cannot be combined with `$filter` or `$orderby`. |  |
| `find_shared_folder_email` | Search for an email in a shared folder. | `user_id`, `shared_folder_id` |
| `get_current_user` | Returns the authenticated Microsoft user's ID, display name, email, and principal name. |  |
| `get_message` | Retrieve a single email message by its Microsoft Graph message ID. | `message_id` |
| `list_contacts` | Get a contact collection from the default contacts folder. |  |
| `list_folders` | Retrieves a list of mail folders in Microsoft Outlook. |  |
| `list_important_mail` | Get the most important mail from the user's Inbox (filters by high importance or flagged status). |  |
| `list_labels` | Get all the labels/categories that have been defined for a user. |  |
| `move_email_to_folder` | Moves an email to the specified folder. | `message_id`, `folder_id` |
| `remove_label_from_email` | Removes a label/category from an email. | `message_id`, `label` |
| `reply_to_email` | Reply to an email. | `message_id` |
| `send_email` | Send an email to one or multiple recipients. |  |
| `update_contact` | Update an existing contact. | `contact_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- Microsoft Graph throttles per-app and per-mailbox. Mail endpoints allow approximately 10,000 requests per 10 minutes per app per mailbox; consult Microsoft's throttling guidance for exact tiers.
- Search uses Microsoft Graph KQL semantics; combining `search` with `filter` or `order_by` is rejected by Microsoft Graph and short-circuited locally with a `success=False` error.
- Attachments are accepted as URLs only; the integration fetches each URL and base64-encodes the bytes for Microsoft Graph's `fileAttachment` payload. `download_attachment` returns base64-encoded bytes rather than writing files to disk.
- The `approve_workflow` action does not internally suspend a workflow; the caller must supply both `resume_url` and `cancel_url`. The action only sends the approval email.
- Error model: non-2xx responses are caught and returned as `success=False` + `error`; the calling agent can retry or surface the error.

## Maintainer

ModuleX core team.

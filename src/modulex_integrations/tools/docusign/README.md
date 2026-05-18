# DocuSign

Electronic signature and agreement management via the DocuSign eSignature REST API (`account.docusign.com` + per-account base URIs resolved at runtime).

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth app at the [DocuSign Apps and Keys](https://admindemo.docusign.com/apps-and-keys) page in the DocuSign Admin console.
- Required redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Scopes requested: `signature`, `extended`
- Required env vars (only when bringing your own OAuth app):
  - `DOCUSIGN_OAUTH2_CLIENT_ID` (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`) — the Integration Key
  - `DOCUSIGN_OAUTH2_CLIENT_SECRET` — the Secret Key
- The credential test calls `GET /oauth/userinfo` to validate the token and retrieve account info.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_signature_request` | Create and send a signature request from a DocuSign template | `account`, `template`, `email_subject` |
| `create_draft` | Create a draft envelope from a DocuSign template without sending it | `account`, `template`, `email_subject` |
| `create_envelope` | Create a DocuSign envelope from a full envelope definition JSON payload | `account`, `envelope_definition_json` |
| `create_envelope_from_file` | Create and optionally send a single-document envelope from a file URL | `account`, `file_url`, `email_subject`, `signer_name`, `signer_email` |
| `create_recipient_view` | Create an embedded signing URL for a recipient with a clientUserId | `account`, `envelope_id`, `return_url`, `recipient_id` |
| `get_envelope` | Get details for a DocuSign envelope by ID | `account`, `envelope_id` |
| `list_envelopes` | Search for envelopes by date, status, email, text, or folder filters | `account` |
| `list_documents` | List documents in a DocuSign envelope | `account`, `envelope_id` |
| `list_recipients` | List recipients and their status for a DocuSign envelope | `account`, `envelope_id` |
| `send_envelope` | Send an existing draft envelope by updating its status to sent | `account`, `envelope_id` |
| `download_documents` | Download documents from an envelope as base64-encoded content | `account`, `envelope_id`, `download_type`, `filename` |
| `void_envelope` | Void an envelope that is still in process | `account`, `envelope_id`, `voided_reason` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- **Rate limits**: DocuSign enforces per-account rate limits; the eSignature REST API allows approximately 1,000 requests per 15 minutes for production accounts. Demo/sandbox accounts have lower limits.
- **Polling intervals**: For envelope status polling, DocuSign recommends no more than once per 15 minutes.
- **File size**: Maximum document size is 25 MB per document.
- **Error model**: Non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising. Plan for retries on the agent side based on the error string.

## Maintainer

ModuleX core team.

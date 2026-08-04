# AWS SES

Send simple, templated, and bulk emails with Amazon Simple Email Service, and
manage templates, identities, configuration sets, and the account suppression
list through the Amazon SES API v2.

## Authentication

### AWS Access Key

- Sign in to the [AWS Management Console](https://console.aws.amazon.com/).
- Go to **IAM > Users > your user > Security credentials**.
- Create an access key and save both the Access Key ID and Secret Access Key.
- Required env vars:
  - `AWS_ACCESS_KEY_ID` (format: `AKIAIOSFODNN7EXAMPLE`)
  - `AWS_SECRET_ACCESS_KEY` (format: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)
- The IAM user or role needs the SES v2 permissions matching the actions you
  call (`ses:SendEmail`, `ses:SendBulkEmail`, `ses:CreateEmailTemplate`,
  `ses:GetEmailIdentity`, `ses:PutSuppressedDestination`, and so on).
- Requests are signed with AWS Signature Version 4 (`ses` service scope) against
  the regional endpoint `https://email.<region>.amazonaws.com`.
- Sending identities are per-region: verify the sender address or domain in the
  same region you pass as `region`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `send_email` | Send an email through Amazon SES using simple text or HTML content | `from_address`, `to_addresses`, `subject` |
| `send_templated_email` | Send an email rendered from an Amazon SES template with dynamic data | `from_address`, `to_addresses`, `template_name`, `template_data` |
| `send_bulk_email` | Send a templated email to many recipients with per-recipient data | `from_address`, `template_name`, `destinations` |
| `list_identities` | List the email identities (addresses and domains) in the account | (none) |
| `get_account` | Get the Amazon SES account sending quota, rate, and status | (none) |
| `create_template` | Create a reusable Amazon SES email template | `template_name`, `subject_part` |
| `get_template` | Retrieve the subject, HTML, and text content of an email template | `template_name` |
| `list_templates` | List the email templates in the account | (none) |
| `delete_template` | Delete an email template from the account | `template_name` |
| `update_template` | Update the subject, HTML, and text content of an email template | `template_name`, `subject_part` |
| `send_custom_verification_email` | Send a custom verification email to an address to verify it | `email_address`, `template_name` |
| `create_email_identity` | Start verification of an email address or domain identity | `email_identity` |
| `get_email_identity` | Get verification, DKIM, and MAIL FROM details for an identity | `email_identity` |
| `delete_email_identity` | Delete an email address or domain identity from the account | `email_identity` |
| `put_suppressed_destination` | Add an email address to the account-level suppression list | `email_address` |
| `get_suppressed_destination` | Look up a single address on the account-level suppression list | `email_address` |
| `list_suppressed_destinations` | List addresses on the account-level suppression list | (none) |
| `delete_suppressed_destination` | Remove an email address from the account-level suppression list | `email_address` |
| `create_configuration_set` | Create a configuration set that groups sending rules for emails | `configuration_set_name` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the resolved credential. The `region` parameter defaults to
`us-east-1` but can be overridden per call.

## Limits & Quotas

- New accounts start in the SES sandbox: 200 messages per 24 hours, 1 message
  per second, and recipients must be verified identities. `get_account` reports
  `production_access_enabled`, the 24-hour quota, and the send rate.
- Sending quota and rate are per-region and adjustable through AWS Service
  Quotas; other defaults include 10,000 configuration sets per region.
- Template operations are rate limited by SES: `create_template`,
  `update_template`, `delete_template`, `list_templates`, and
  `send_custom_verification_email` allow 1 request per second;
  `get_template` allows 50 per second.
- `send_bulk_email` accepts up to 50 destinations per call and returns a
  per-destination status; check `results` for partial failures even when
  `success` is `true`.
- Suppression list filters (`start_date` / `end_date`) expect ISO 8601
  timestamps; list responses are paginated through `next_token`.
- Error model: non-2xx responses, timeouts, and unexpected exceptions are
  returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.

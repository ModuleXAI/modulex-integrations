"""AWS SES integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


_REGION_PARAM = ParameterDef(
    type="string",
    description="AWS region hosting the SES account (e.g. us-east-1, eu-west-1)",
    default="us-east-1",
)


manifest = IntegrationManifest(
    name="ses",
    display_name="AWS SES",
    description=(
        "Send simple, templated, and bulk emails with Amazon Simple Email Service. "
        "Manage email templates, identities, configuration sets, and the account "
        "suppression list, and read account sending quota and identity verification status."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:ses-themed",
    app_url="https://aws.amazon.com/ses",
    categories=["Communication", "email", "email-marketing", "cloud"],
    actions=[
        ActionDefinition(
            name="send_email",
            description="Send an email through Amazon SES using simple text or HTML content.",
            parameters={
                "region": _REGION_PARAM,
                "from_address": ParameterDef(
                    type="string",
                    description="Verified sender email address",
                    required=True,
                ),
                "to_addresses": ParameterDef(
                    type="array",
                    description="Recipient email addresses",
                    required=True,
                ),
                "subject": ParameterDef(
                    type="string",
                    description="Email subject line",
                    required=True,
                ),
                "body_html": ParameterDef(
                    type="string",
                    description="HTML email body",
                ),
                "body_text": ParameterDef(
                    type="string",
                    description="Plain text email body",
                ),
                "cc_addresses": ParameterDef(
                    type="array",
                    description="CC email addresses",
                ),
                "bcc_addresses": ParameterDef(
                    type="array",
                    description="BCC email addresses",
                ),
                "reply_to_addresses": ParameterDef(
                    type="array",
                    description="Reply-To email addresses",
                ),
                "configuration_set_name": ParameterDef(
                    type="string",
                    description="Configuration set to apply to the send",
                ),
            },
        ),
        ActionDefinition(
            name="send_templated_email",
            description="Send an email rendered from an Amazon SES template with dynamic data.",
            parameters={
                "region": _REGION_PARAM,
                "from_address": ParameterDef(
                    type="string",
                    description="Verified sender email address",
                    required=True,
                ),
                "to_addresses": ParameterDef(
                    type="array",
                    description="Recipient email addresses",
                    required=True,
                ),
                "template_name": ParameterDef(
                    type="string",
                    description="Name of the email template to render",
                    required=True,
                ),
                "template_data": ParameterDef(
                    type="object",
                    description='Template variables, e.g. {"name": "John"}',
                    required=True,
                ),
                "cc_addresses": ParameterDef(
                    type="array",
                    description="CC email addresses",
                ),
                "bcc_addresses": ParameterDef(
                    type="array",
                    description="BCC email addresses",
                ),
                "configuration_set_name": ParameterDef(
                    type="string",
                    description="Configuration set to apply to the send",
                ),
            },
        ),
        ActionDefinition(
            name="send_bulk_email",
            description="Send a templated email to many recipients with per-recipient data.",
            parameters={
                "region": _REGION_PARAM,
                "from_address": ParameterDef(
                    type="string",
                    description="Verified sender email address",
                    required=True,
                ),
                "template_name": ParameterDef(
                    type="string",
                    description="Name of the email template to render",
                    required=True,
                ),
                "destinations": ParameterDef(
                    type="array",
                    description=(
                        'Destination objects, e.g. [{"to_addresses": ["a@example.com"], '
                        '"template_data": {"name": "A"}}]'
                    ),
                    required=True,
                ),
                "default_template_data": ParameterDef(
                    type="object",
                    description="Fallback template variables for destinations without their own",
                ),
                "configuration_set_name": ParameterDef(
                    type="string",
                    description="Configuration set to apply to the send",
                ),
            },
        ),
        ActionDefinition(
            name="list_identities",
            description="List the email identities (addresses and domains) in the account.",
            parameters={
                "region": _REGION_PARAM,
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of identities to return (0-1000)",
                ),
                "next_token": ParameterDef(
                    type="string",
                    description="Pagination token from a previous call",
                ),
            },
        ),
        ActionDefinition(
            name="get_account",
            description="Get the Amazon SES account sending quota, rate, and status.",
            parameters={"region": _REGION_PARAM},
        ),
        ActionDefinition(
            name="create_template",
            description="Create a reusable Amazon SES email template.",
            parameters={
                "region": _REGION_PARAM,
                "template_name": ParameterDef(
                    type="string",
                    description="Unique name for the email template",
                    required=True,
                ),
                "subject_part": ParameterDef(
                    type="string",
                    description="Subject line, supports {{variable}} substitution",
                    required=True,
                ),
                "html_part": ParameterDef(
                    type="string",
                    description="HTML body of the template",
                ),
                "text_part": ParameterDef(
                    type="string",
                    description="Plain text body of the template",
                ),
            },
        ),
        ActionDefinition(
            name="get_template",
            description="Retrieve the subject, HTML, and text content of an email template.",
            parameters={
                "region": _REGION_PARAM,
                "template_name": ParameterDef(
                    type="string",
                    description="Name of the template to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_templates",
            description="List the email templates in the account.",
            parameters={
                "region": _REGION_PARAM,
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of templates to return (1-100)",
                ),
                "next_token": ParameterDef(
                    type="string",
                    description="Pagination token from a previous call",
                ),
            },
        ),
        ActionDefinition(
            name="delete_template",
            description="Delete an email template from the account.",
            parameters={
                "region": _REGION_PARAM,
                "template_name": ParameterDef(
                    type="string",
                    description="Name of the template to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_template",
            description="Update the subject, HTML, and text content of an email template.",
            parameters={
                "region": _REGION_PARAM,
                "template_name": ParameterDef(
                    type="string",
                    description="Name of the template to update",
                    required=True,
                ),
                "subject_part": ParameterDef(
                    type="string",
                    description="Subject line of the template",
                    required=True,
                ),
                "html_part": ParameterDef(
                    type="string",
                    description="HTML body of the template",
                ),
                "text_part": ParameterDef(
                    type="string",
                    description="Plain text body of the template",
                ),
            },
        ),
        ActionDefinition(
            name="send_custom_verification_email",
            description="Send a custom verification email to an address to verify it.",
            parameters={
                "region": _REGION_PARAM,
                "email_address": ParameterDef(
                    type="string",
                    description="Email address to verify",
                    required=True,
                ),
                "template_name": ParameterDef(
                    type="string",
                    description="Custom verification email template name",
                    required=True,
                ),
                "configuration_set_name": ParameterDef(
                    type="string",
                    description="Configuration set to apply to the send",
                ),
            },
        ),
        ActionDefinition(
            name="create_email_identity",
            description="Start verification of an email address or domain identity.",
            parameters={
                "region": _REGION_PARAM,
                "email_identity": ParameterDef(
                    type="string",
                    description="Email address or domain to verify",
                    required=True,
                ),
                "dkim_signing_attributes": ParameterDef(
                    type="object",
                    description=(
                        'BYODKIM settings, e.g. {"domain_signing_selector": "selector1", '
                        '"domain_signing_private_key": "base64-key"}'
                    ),
                ),
                "tags": ParameterDef(
                    type="array",
                    description='Tags, e.g. [{"key": "team", "value": "growth"}]',
                ),
                "configuration_set_name": ParameterDef(
                    type="string",
                    description="Default configuration set for this identity",
                ),
            },
        ),
        ActionDefinition(
            name="get_email_identity",
            description="Get verification, DKIM, and MAIL FROM details for an identity.",
            parameters={
                "region": _REGION_PARAM,
                "email_identity": ParameterDef(
                    type="string",
                    description="Email address or domain identity",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_email_identity",
            description="Delete an email address or domain identity from the account.",
            parameters={
                "region": _REGION_PARAM,
                "email_identity": ParameterDef(
                    type="string",
                    description="Email address or domain identity to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="put_suppressed_destination",
            description="Add an email address to the account-level suppression list.",
            parameters={
                "region": _REGION_PARAM,
                "email_address": ParameterDef(
                    type="string",
                    description="Email address to add to the suppression list",
                    required=True,
                ),
                "reason": ParameterDef(
                    type="string",
                    description="Suppression reason: BOUNCE or COMPLAINT",
                    default="BOUNCE",
                ),
            },
        ),
        ActionDefinition(
            name="get_suppressed_destination",
            description="Look up a single address on the account-level suppression list.",
            parameters={
                "region": _REGION_PARAM,
                "email_address": ParameterDef(
                    type="string",
                    description="Suppressed email address to look up",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_suppressed_destinations",
            description="List addresses on the account-level suppression list.",
            parameters={
                "region": _REGION_PARAM,
                "reasons": ParameterDef(
                    type="array",
                    description="Filter by reason: BOUNCE and/or COMPLAINT",
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="ISO 8601 lower bound timestamp",
                ),
                "end_date": ParameterDef(
                    type="string",
                    description="ISO 8601 upper bound timestamp",
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of addresses to return",
                ),
                "next_token": ParameterDef(
                    type="string",
                    description="Pagination token from a previous call",
                ),
            },
        ),
        ActionDefinition(
            name="delete_suppressed_destination",
            description="Remove an email address from the account-level suppression list.",
            parameters={
                "region": _REGION_PARAM,
                "email_address": ParameterDef(
                    type="string",
                    description="Email address to remove from the suppression list",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_configuration_set",
            description="Create a configuration set that groups sending rules for emails.",
            parameters={
                "region": _REGION_PARAM,
                "configuration_set_name": ParameterDef(
                    type="string",
                    description="Name for the new configuration set",
                    required=True,
                ),
                "custom_redirect_domain": ParameterDef(
                    type="string",
                    description="Custom domain for open/click tracking links",
                ),
                "https_policy": ParameterDef(
                    type="string",
                    description="Tracking link policy: REQUIRE, REQUIRE_OPEN_ONLY, or OPTIONAL",
                ),
                "tls_policy": ParameterDef(
                    type="string",
                    description="Delivery TLS policy: REQUIRE or OPTIONAL",
                ),
                "sending_pool_name": ParameterDef(
                    type="string",
                    description="Dedicated IP pool name",
                ),
                "reputation_metrics_enabled": ParameterDef(
                    type="boolean",
                    description="Whether to collect reputation metrics",
                ),
                "sending_enabled": ParameterDef(
                    type="boolean",
                    description="Whether sending is enabled for this configuration set",
                ),
                "suppressed_reasons": ParameterDef(
                    type="array",
                    description="Auto-suppression reasons: BOUNCE and/or COMPLAINT",
                ),
                "tags": ParameterDef(
                    type="array",
                    description='Tags, e.g. [{"key": "team", "value": "growth"}]',
                ),
            },
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="AWS Access Key",
            description=(
                "Authenticate with an AWS access key ID and secret access key. "
                "Requests are signed with AWS Signature Version 4."
            ),
            setup_instructions=[
                "Sign in to the AWS Management Console.",
                "Go to IAM > Users > your user > Security credentials.",
                "Create an access key and save both the Access Key ID and Secret Access Key.",
                "Attach a policy granting the SES actions you need (e.g. AmazonSESFullAccess).",
                "Verify at least one sending identity in the SES console for the region you use.",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="AWS_ACCESS_KEY_ID",
                    display_name="Access Key ID",
                    description="Your AWS Access Key ID",
                    required=True,
                    sensitive=False,
                    sample_format="AKIAIOSFODNN7EXAMPLE",
                    about_url="https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html",
                ),
                EnvVar(
                    name="AWS_SECRET_ACCESS_KEY",
                    display_name="Secret Access Key",
                    description="Your AWS Secret Access Key",
                    required=True,
                    sensitive=True,
                    sample_format="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://email.us-east-1.amazonaws.com/v2/email/account",
                method="GET",
                # SES requires SigV4-signed requests and the runtime cannot
                # synthesize a signature, so this probe arrives unsigned and
                # SES answers 403 (or 400 if it cannot parse the request).
                # Both confirm the regional SES endpoint is reachable and the
                # request was well-formed; real credential validation happens
                # on the first signed action call.
                success_indicators=SuccessIndicators(status_codes=[200, 400, 403]),
                cost_level="free",
                description=(
                    "Reachability check against the Amazon SES API v2 account endpoint. "
                    "Accepts 200 (signed, unlikely), 400 (malformed unsigned), or 403 "
                    "(missing signature — expected)."
                ),
            ),
        ),
    ],
)

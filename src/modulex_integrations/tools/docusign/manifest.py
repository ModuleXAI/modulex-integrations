"""DocuSign integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="docusign",
    display_name="DocuSign",
    description="Electronic signature and agreement management via the DocuSign eSignature REST API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:docusign-themed",
    app_url="https://www.docusign.com",
    categories=["Productivity & Collaboration", "legal", "e-signature", "document-management"],
    actions=[
        ActionDefinition(
            name="create_signature_request",
            description="Create and send a signature request from a DocuSign template",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="DocuSign Account ID",
                    required=True,
                ),
                "template": ParameterDef(
                    type="string",
                    description="Document Template ID",
                    required=True,
                ),
                "email_subject": ParameterDef(
                    type="string",
                    description="Subject line of the signature request email",
                    required=True,
                ),
                "email_blurb": ParameterDef(
                    type="string",
                    description="Email message body to the recipient. Overrides the template setting",
                ),
                "template_roles_json": ParameterDef(
                    type="string",
                    description="JSON array of template role objects, each with roleName, name, and email. Example: [{\"roleName\":\"Signer 1\",\"name\":\"Jane\",\"email\":\"jane@example.com\"}]",
                ),
            },
        ),
        ActionDefinition(
            name="create_draft",
            description="Create a draft envelope from a DocuSign template without sending it",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="DocuSign Account ID",
                    required=True,
                ),
                "template": ParameterDef(
                    type="string",
                    description="Document Template ID",
                    required=True,
                ),
                "email_subject": ParameterDef(
                    type="string",
                    description="Subject line of the email",
                    required=True,
                ),
                "email_blurb": ParameterDef(
                    type="string",
                    description="Email message body to the recipient. Overrides the template setting",
                ),
                "template_roles_json": ParameterDef(
                    type="string",
                    description="JSON array of template role objects, each with roleName, name, and email",
                ),
            },
        ),
        ActionDefinition(
            name="create_envelope",
            description="Create a DocuSign envelope from a full envelope definition JSON payload for advanced multi-document or multi-recipient scenarios",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="DocuSign Account ID",
                    required=True,
                ),
                "envelope_definition_json": ParameterDef(
                    type="string",
                    description="Full DocuSign envelope definition as a JSON string. Example: {\"emailSubject\":\"Please sign\",\"status\":\"sent\",\"documents\":[...],\"recipients\":{\"signers\":[...]}}",
                    required=True,
                ),
                "status": ParameterDef(
                    type="string",
                    description="Envelope status override. Use 'created' to save as draft or 'sent' to send immediately. Allowed values: sent, created",
                ),
                "merge_roles_on_draft": ParameterDef(
                    type="boolean",
                    description="When creating a draft from multiple templates, merge template roles and remove empty recipients",
                ),
            },
        ),
        ActionDefinition(
            name="create_envelope_from_file",
            description="Create and optionally send a single-document DocuSign envelope from a file URL with anchor-based signature tab placement",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="DocuSign Account ID",
                    required=True,
                ),
                "file_url": ParameterDef(
                    type="string",
                    description="URL of the document to send. The file will be fetched and base64-encoded for upload to DocuSign",
                    required=True,
                ),
                "email_subject": ParameterDef(
                    type="string",
                    description="Subject line of the email",
                    required=True,
                ),
                "signer_name": ParameterDef(
                    type="string",
                    description="Full name of the signer",
                    required=True,
                ),
                "signer_email": ParameterDef(
                    type="string",
                    description="Email address of the signer",
                    required=True,
                ),
                "status": ParameterDef(
                    type="string",
                    description="Use 'sent' to send immediately or 'created' to save as draft. Allowed values: sent, created",
                    default="sent",
                ),
                "document_name": ParameterDef(
                    type="string",
                    description="Document name shown in DocuSign. Defaults to the filename from the URL",
                ),
                "file_extension": ParameterDef(
                    type="string",
                    description="File extension. Defaults to the extension from the URL, or 'pdf' if not detected",
                ),
                "signer_recipient_id": ParameterDef(
                    type="string",
                    description="Recipient ID for the signer",
                    default="1",
                ),
                "routing_order": ParameterDef(
                    type="string",
                    description="Routing order for the signer",
                    default="1",
                ),
                "client_user_id": ParameterDef(
                    type="string",
                    description="Set this for embedded signing recipients. The same value is required when creating a recipient view URL",
                ),
                "sign_here_anchor_string": ParameterDef(
                    type="string",
                    description="Anchor text in the document where DocuSign places the signature tab. Example: /sn1/",
                    default="/sn1/",
                ),
                "anchor_x_offset": ParameterDef(
                    type="string",
                    description="Horizontal offset in pixels for the signature tab relative to the anchor text",
                    default="20",
                ),
                "anchor_y_offset": ParameterDef(
                    type="string",
                    description="Vertical offset in pixels for the signature tab relative to the anchor text",
                    default="10",
                ),
            },
        ),
        ActionDefinition(
            name="create_recipient_view",
            description="Create an embedded signing URL for a selected envelope recipient who was created with a clientUserId",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="DocuSign Account ID",
                    required=True,
                ),
                "envelope_id": ParameterDef(
                    type="string",
                    description="DocuSign envelope ID",
                    required=True,
                ),
                "return_url": ParameterDef(
                    type="string",
                    description="URL where DocuSign redirects the signer after the signing session. Must include https://",
                    required=True,
                ),
                "recipient_id": ParameterDef(
                    type="string",
                    description="Recipient ID on the envelope",
                    required=True,
                ),
                "authentication_method": ParameterDef(
                    type="string",
                    description="Convention string describing how your app authenticated the signer. Example: none",
                    default="none",
                ),
                "ping_url": ParameterDef(
                    type="string",
                    description="URL DocuSign pings while the signing session is active",
                ),
                "ping_frequency": ParameterDef(
                    type="string",
                    description="Ping interval in seconds. DocuSign supports 60 to 1200",
                ),
            },
        ),
        ActionDefinition(
            name="get_envelope",
            description="Get details for a DocuSign envelope by ID",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="DocuSign Account ID",
                    required=True,
                ),
                "envelope_id": ParameterDef(
                    type="string",
                    description="DocuSign envelope ID",
                    required=True,
                ),
                "include": ParameterDef(
                    type="string",
                    description="Comma-separated additional information to include. Allowed values: custom_fields, documents, extensions, folders, recipients, tabs",
                ),
            },
        ),
        ActionDefinition(
            name="list_envelopes",
            description="Search for DocuSign envelopes by date, status, email, text, or folder filters",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="DocuSign Account ID",
                    required=True,
                ),
                "from_date": ParameterDef(
                    type="string",
                    description="Return envelopes changed on or after this ISO 8601 datetime, e.g. 2026-04-01T00:00:00Z. Defaults to 30 days ago",
                ),
                "to_date": ParameterDef(
                    type="string",
                    description="Return envelopes changed on or before this ISO 8601 datetime",
                ),
                "status": ParameterDef(
                    type="string",
                    description="Comma-separated envelope statuses. Allowed values: any, completed, created, declined, deleted, delivered, processing, sent, signed, timedout, voided",
                ),
                "email": ParameterDef(
                    type="string",
                    description="Filter by recipient or sender email address",
                ),
                "search_text": ParameterDef(
                    type="string",
                    description="Search text matched against envelope metadata",
                ),
                "folder_ids": ParameterDef(
                    type="string",
                    description="Comma-separated folder IDs to filter by",
                ),
                "count": ParameterDef(
                    type="integer",
                    description="Number of envelopes per page",
                    default=100,
                ),
                "start_position": ParameterDef(
                    type="integer",
                    description="Zero-based result offset",
                    default=0,
                ),
                "order": ParameterDef(
                    type="string",
                    description="Sort order. Allowed values: asc, desc",
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="Field to sort by. Allowed values: action_required, created, completed, sent, signer_list, status, subject, last_modified",
                ),
                "fetch_all": ParameterDef(
                    type="boolean",
                    description="When true, follow pagination until no pages remain or max_pages is reached",
                    default=False,
                ),
                "max_pages": ParameterDef(
                    type="integer",
                    description="Maximum pages to retrieve when fetch_all is true",
                    default=10,
                ),
            },
        ),
        ActionDefinition(
            name="list_documents",
            description="List documents in a DocuSign envelope",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="DocuSign Account ID",
                    required=True,
                ),
                "envelope_id": ParameterDef(
                    type="string",
                    description="DocuSign envelope ID",
                    required=True,
                ),
                "include_tabs": ParameterDef(
                    type="boolean",
                    description="Whether to include tab information for each document",
                    default=False,
                ),
                "include_metadata": ParameterDef(
                    type="boolean",
                    description="Whether to include document metadata",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="list_recipients",
            description="List recipients and their status for a DocuSign envelope",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="DocuSign Account ID",
                    required=True,
                ),
                "envelope_id": ParameterDef(
                    type="string",
                    description="DocuSign envelope ID",
                    required=True,
                ),
                "include_tabs": ParameterDef(
                    type="boolean",
                    description="Whether to include each recipient's tabs",
                    default=False,
                ),
                "include_extended": ParameterDef(
                    type="boolean",
                    description="Whether to include extended recipient information",
                    default=False,
                ),
                "include_metadata": ParameterDef(
                    type="boolean",
                    description="Whether to include metadata",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="send_envelope",
            description="Send an existing draft DocuSign envelope by updating its status to sent",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="DocuSign Account ID",
                    required=True,
                ),
                "envelope_id": ParameterDef(
                    type="string",
                    description="DocuSign envelope ID",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="download_documents",
            description="Download documents from a DocuSign envelope as base64-encoded content",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="DocuSign Account ID",
                    required=True,
                ),
                "envelope_id": ParameterDef(
                    type="string",
                    description="DocuSign envelope ID",
                    required=True,
                ),
                "download_type": ParameterDef(
                    type="string",
                    description="Download type. Allowed values: combined (All Documents PDF), archive (All Documents Zip), certificate (Certificate PDF), portfolio (Portfolio PDF)",
                    required=True,
                ),
                "filename": ParameterDef(
                    type="string",
                    description="Filename including extension (.pdf or .zip) for the downloaded content",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="void_envelope",
            description="Void a DocuSign envelope that is still in process, cancelling it and preventing recipients from completing it",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="DocuSign Account ID",
                    required=True,
                ),
                "envelope_id": ParameterDef(
                    type="string",
                    description="DocuSign envelope ID",
                    required=True,
                ),
                "voided_reason": ParameterDef(
                    type="string",
                    description="Reason the envelope is being voided. Visible in DocuSign audit history",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using DocuSign OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="DOCUSIGN_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="DocuSign OAuth App Integration Key (Client ID)",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://admindemo.docusign.com/apps-and-keys",
                ),
                EnvVar(
                    name="DOCUSIGN_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="DocuSign OAuth App Secret Key",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="x" * 40,
                    about_url="https://admindemo.docusign.com/apps-and-keys",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://account.docusign.com/oauth/auth",
                token_url="https://account.docusign.com/oauth/token",
                scopes=["signature", "extended"],
            ),
            test_endpoint=TestEndpoint(
                url="https://account.docusign.com/oauth/userinfo",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["accounts"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching user info and account list",
            ),
        ),
    ],
)

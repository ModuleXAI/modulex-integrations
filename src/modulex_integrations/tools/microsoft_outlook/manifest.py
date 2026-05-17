"""Microsoft Outlook integration manifest."""
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
    name="microsoft_outlook",
    display_name="Microsoft Outlook",
    description="Send, draft, search, and organize email; manage contacts, folders, and categories in Microsoft Outlook via Microsoft Graph.",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:microsoft_outlook-themed",
    app_url="https://outlook.live.com",
    categories=["email", "productivity", "communication", "microsoft"],
    actions=[
        ActionDefinition(
            name="add_label_to_email",
            description="Adds a label/category to an email in Microsoft Outlook.",
            parameters={
                "message_id": ParameterDef(
                    type="string",
                    description="The identifier of the message to update.",
                    required=True,
                ),
                "label": ParameterDef(
                    type="string",
                    description="The name of the label/category to add.",
                    required=True,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="The User ID of a shared mailbox. If not provided, defaults to the authenticated user's mailbox.",
                ),
            },
        ),
        ActionDefinition(
            name="approve_workflow",
            description="Send an email containing approve/cancel URLs to a recipient so they can resume or cancel a workflow externally. The caller (workflow engine) is responsible for generating the resume/cancel URLs and passing them in.",
            parameters={
                "recipients": ParameterDef(
                    type="array",
                    description="Array of recipient email addresses.",
                    required=True,
                ),
                "subject": ParameterDef(
                    type="string",
                    description="Subject of the approval email.",
                    required=True,
                ),
                "resume_url": ParameterDef(
                    type="string",
                    description="URL the recipient clicks to approve / resume the workflow.",
                    required=True,
                ),
                "cancel_url": ParameterDef(
                    type="string",
                    description="URL the recipient clicks to cancel the workflow.",
                    required=True,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="The User ID of a shared mailbox. If not provided, defaults to the authenticated user's mailbox.",
                ),
            },
        ),
        ActionDefinition(
            name="create_contact",
            description="Add a contact to the root Contacts folder.",
            parameters={
                "given_name": ParameterDef(
                    type="string",
                    description="Given name of the contact.",
                ),
                "surname": ParameterDef(
                    type="string",
                    description="Surname of the contact.",
                ),
                "email_addresses": ParameterDef(
                    type="array",
                    description="Email addresses for the contact (list of strings).",
                ),
                "business_phones": ParameterDef(
                    type="array",
                    description="Array of phone numbers (list of strings).",
                ),
                "expand": ParameterDef(
                    type="object",
                    description="Additional contact details to merge into the request body. See https://docs.microsoft.com/en-us/graph/api/resources/contact",
                ),
            },
        ),
        ActionDefinition(
            name="create_draft_email",
            description="Create a draft email.",
            parameters={
                "recipients": ParameterDef(
                    type="array",
                    description="Array of TO recipient email addresses (list of strings).",
                ),
                "cc_recipients": ParameterDef(
                    type="array",
                    description="Array of CC recipient email addresses (list of strings).",
                ),
                "bcc_recipients": ParameterDef(
                    type="array",
                    description="Array of BCC recipient email addresses (list of strings).",
                ),
                "subject": ParameterDef(
                    type="string",
                    description="Subject of the email.",
                ),
                "content_type": ParameterDef(
                    type="string",
                    description="Content type of the body. Valid values: text, html.",
                    default="text",
                ),
                "content": ParameterDef(
                    type="string",
                    description="Body content of the email in text or HTML.",
                ),
                "file_urls": ParameterDef(
                    type="array",
                    description="Array of file URLs to fetch and attach to the message (list of strings).",
                ),
                "expand": ParameterDef(
                    type="object",
                    description="Additional Message resource fields merged into the request. See https://docs.microsoft.com/en-us/graph/api/resources/message",
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="The User ID of a shared mailbox. If not provided, defaults to the authenticated user's mailbox.",
                ),
            },
        ),
        ActionDefinition(
            name="create_draft_reply",
            description="Create a draft reply to an email.",
            parameters={
                "message_id": ParameterDef(
                    type="string",
                    description="The identifier of the message to reply to.",
                    required=True,
                ),
                "comment": ParameterDef(
                    type="string",
                    description="Content of the reply in text format.",
                ),
                "recipients": ParameterDef(
                    type="array",
                    description="Array of TO recipient email addresses to override on the draft (list of strings).",
                ),
                "cc_recipients": ParameterDef(
                    type="array",
                    description="Array of CC recipient email addresses (list of strings).",
                ),
                "bcc_recipients": ParameterDef(
                    type="array",
                    description="Array of BCC recipient email addresses (list of strings).",
                ),
                "subject": ParameterDef(
                    type="string",
                    description="Subject override for the reply.",
                ),
                "file_urls": ParameterDef(
                    type="array",
                    description="Array of file URLs to attach to the reply (list of strings).",
                ),
                "expand": ParameterDef(
                    type="object",
                    description="Additional Message resource fields merged into the message body.",
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="The User ID of a shared mailbox.",
                ),
            },
        ),
        ActionDefinition(
            name="download_attachment",
            description="Downloads an attachment from a message and returns it as base64-encoded content with metadata.",
            parameters={
                "message_id": ParameterDef(
                    type="string",
                    description="The identifier of the message containing the attachment.",
                    required=True,
                ),
                "attachment_id": ParameterDef(
                    type="string",
                    description="The identifier of the attachment to download.",
                    required=True,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="The User ID of a shared mailbox.",
                ),
            },
        ),
        ActionDefinition(
            name="find_contacts",
            description="Finds contacts with the given search string.",
            parameters={
                "search_string": ParameterDef(
                    type="string",
                    description="Provide email address, given name, surname, or display name (case sensitive).",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="The maximum number of results to return.",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="find_email",
            description="Search for an email in Microsoft Outlook. $search cannot be combined with $filter or $orderby.",
            parameters={
                "search": ParameterDef(
                    type="string",
                    description='Search query. Can use property syntax like "to:example@example.com" or "subject:example". Not for use with filter or order_by.',
                ),
                "filter": ParameterDef(
                    type="string",
                    description="OData $filter expression, e.g. contains(subject, 'meet for lunch?'). Not for use with search.",
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="OData $orderby expression, e.g. receivedDateTime desc. Not for use with search.",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of messages to return.",
                    default=100,
                ),
                "include_attachments": ParameterDef(
                    type="boolean",
                    description="If true, expands attachments on each returned message.",
                    default=False,
                ),
                "select": ParameterDef(
                    type="string",
                    description="Comma-separated message property names to return (e.g. id,subject,from,receivedDateTime). Shrinks payload size.",
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="The User ID of a shared mailbox.",
                ),
            },
        ),
        ActionDefinition(
            name="find_shared_folder_email",
            description="Search for an email in a shared folder.",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="The user ID owning the shared folder.",
                    required=True,
                ),
                "shared_folder_id": ParameterDef(
                    type="string",
                    description="The ID of the shared folder to search.",
                    required=True,
                ),
                "search": ParameterDef(
                    type="string",
                    description="Search query. Not for use with filter or order_by.",
                ),
                "filter": ParameterDef(
                    type="string",
                    description="OData $filter expression.",
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="OData $orderby expression.",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of messages to return.",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="get_current_user",
            description="Returns the authenticated Microsoft user's ID, display name, email, and principal name via Microsoft Graph. Call this first when the user says 'my emails', 'my inbox', or needs identity context.",
            parameters={},
        ),
        ActionDefinition(
            name="get_message",
            description="Retrieve a single email message by its Microsoft Graph message ID.",
            parameters={
                "message_id": ParameterDef(
                    type="string",
                    description="The Microsoft Graph message ID.",
                    required=True,
                ),
                "include_attachments": ParameterDef(
                    type="boolean",
                    description="If true, expands attachments on the returned message.",
                    default=False,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="The User ID of a shared mailbox.",
                ),
            },
        ),
        ActionDefinition(
            name="list_contacts",
            description="Get a contact collection from the default contacts folder.",
            parameters={
                "filter_address": ParameterDef(
                    type="string",
                    description="If provided, only contacts with the given email address will be retrieved.",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of contacts to return.",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="list_folders",
            description="Retrieves a list of mail folders in Microsoft Outlook.",
            parameters={
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of folders to return.",
                    default=100,
                ),
                "include_subfolders": ParameterDef(
                    type="boolean",
                    description="If true, recursively include subfolders.",
                    default=False,
                ),
                "include_hidden_folders": ParameterDef(
                    type="boolean",
                    description="If true, include hidden folders.",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="list_important_mail",
            description="Get the most important mail from the user's Inbox (filters by high importance or flagged status).",
            parameters={
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of messages to return.",
                    default=100,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="The User ID of a shared mailbox.",
                ),
            },
        ),
        ActionDefinition(
            name="list_labels",
            description="Get all the labels/categories that have been defined for a user.",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="The User ID of a shared mailbox.",
                ),
            },
        ),
        ActionDefinition(
            name="move_email_to_folder",
            description="Moves an email to the specified folder.",
            parameters={
                "message_id": ParameterDef(
                    type="string",
                    description="The identifier of the message to move.",
                    required=True,
                ),
                "folder_id": ParameterDef(
                    type="string",
                    description="The identifier of the destination folder.",
                    required=True,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="The User ID of a shared mailbox.",
                ),
            },
        ),
        ActionDefinition(
            name="remove_label_from_email",
            description="Removes a label/category from an email.",
            parameters={
                "message_id": ParameterDef(
                    type="string",
                    description="The identifier of the message to update.",
                    required=True,
                ),
                "label": ParameterDef(
                    type="string",
                    description="The name of the label/category to remove.",
                    required=True,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="The User ID of a shared mailbox.",
                ),
            },
        ),
        ActionDefinition(
            name="reply_to_email",
            description="Reply to an email.",
            parameters={
                "message_id": ParameterDef(
                    type="string",
                    description="The identifier of the message to reply to.",
                    required=True,
                ),
                "comment": ParameterDef(
                    type="string",
                    description="Content of the reply in text format.",
                ),
                "recipients": ParameterDef(
                    type="array",
                    description="Optional override for TO recipients (list of strings).",
                ),
                "cc_recipients": ParameterDef(
                    type="array",
                    description="CC recipient email addresses (list of strings).",
                ),
                "bcc_recipients": ParameterDef(
                    type="array",
                    description="BCC recipient email addresses (list of strings).",
                ),
                "subject": ParameterDef(
                    type="string",
                    description="Optional subject override.",
                ),
                "file_urls": ParameterDef(
                    type="array",
                    description="Array of file URLs to attach (list of strings).",
                ),
                "expand": ParameterDef(
                    type="object",
                    description="Additional Message resource fields merged into the reply body.",
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="The User ID of a shared mailbox.",
                ),
            },
        ),
        ActionDefinition(
            name="send_email",
            description="Send an email to one or multiple recipients.",
            parameters={
                "recipients": ParameterDef(
                    type="array",
                    description="TO recipient email addresses (list of strings).",
                ),
                "cc_recipients": ParameterDef(
                    type="array",
                    description="CC recipient email addresses (list of strings).",
                ),
                "bcc_recipients": ParameterDef(
                    type="array",
                    description="BCC recipient email addresses (list of strings).",
                ),
                "subject": ParameterDef(
                    type="string",
                    description="Subject of the email.",
                ),
                "content_type": ParameterDef(
                    type="string",
                    description="Content type of the body. Valid values: text, html.",
                    default="text",
                ),
                "content": ParameterDef(
                    type="string",
                    description="Body content of the email.",
                ),
                "file_urls": ParameterDef(
                    type="array",
                    description="Array of file URLs to fetch and attach (list of strings).",
                ),
                "expand": ParameterDef(
                    type="object",
                    description="Additional Message resource fields merged into the request.",
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="The User ID of a shared mailbox.",
                ),
            },
        ),
        ActionDefinition(
            name="update_contact",
            description="Update an existing contact.",
            parameters={
                "contact_id": ParameterDef(
                    type="string",
                    description="The ID of the contact to update.",
                    required=True,
                ),
                "given_name": ParameterDef(
                    type="string",
                    description="Given name of the contact.",
                ),
                "surname": ParameterDef(
                    type="string",
                    description="Surname of the contact.",
                ),
                "email_addresses": ParameterDef(
                    type="array",
                    description="Replacement email addresses for the contact (list of strings).",
                ),
                "business_phones": ParameterDef(
                    type="array",
                    description="Replacement phone numbers (list of strings).",
                ),
                "expand": ParameterDef(
                    type="object",
                    description="Additional contact fields merged into the request body.",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect with your Microsoft account using OAuth 2.0 against the Microsoft identity platform.",
            setup_instructions=[
                "Register an application at https://entra.microsoft.com (Azure AD > App registrations)",
                "Under 'Authentication', add the redirect URI: https://api.modulex.dev/credentials/oauth2/callback",
                "Under 'API permissions', add Microsoft Graph delegated permissions: Mail.ReadWrite, Mail.Send, MailboxSettings.Read, Contacts.ReadWrite, User.Read, User.ReadBasic.All, offline_access",
                "Under 'Certificates & secrets', create a new client secret",
                "Copy the Application (client) ID and the client secret into ModuleX",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="MICROSOFT_OUTLOOK_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Microsoft Entra Application (client) ID for the Microsoft Graph app.",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="00000000-0000-0000-0000-000000000000",
                    about_url="https://entra.microsoft.com",
                ),
                EnvVar(
                    name="MICROSOFT_OUTLOOK_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Microsoft Entra client secret for the Microsoft Graph app.",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://entra.microsoft.com",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
                scopes=[
                    "offline_access",
                    "User.Read",
                    "User.ReadBasic.All",
                    "Mail.ReadWrite",
                    "Mail.Send",
                    "MailboxSettings.Read",
                    "Contacts.ReadWrite",
                ],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://graph.microsoft.com/v1.0/me",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["id"],
                ),
                cost_level="free",
                description="Validates the access token by fetching the authenticated user from Microsoft Graph.",
            ),
        ),
    ],
)

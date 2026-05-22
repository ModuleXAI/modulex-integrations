"""Google Contacts integration manifest."""
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
    name="google_contacts",
    display_name="Google Contacts",
    description=(
        "Manage Google People (Contacts) — create, list, get, update, "
        "and delete contacts plus list Google Workspace directory people."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:google_contacts-themed",
    app_url="https://contacts.google.com",
    categories=["Productivity & Collaboration", "CRM"],
    actions=[
        ActionDefinition(
            name="create_contact",
            description="Create a new contact in the authenticated user's Google Contacts.",
            parameters={
                "person_fields": ParameterDef(
                    type="array",
                    description=(
                        "Contact fields to populate and return — any of: names, "
                        "emailAddresses, phoneNumbers, addresses, biographies, "
                        "birthdays, calendarUrls, genders, urls."
                    ),
                    required=True,
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="Contact's first name (used when person_fields includes 'names').",
                ),
                "middle_name": ParameterDef(
                    type="string",
                    description="Contact's middle name (used when person_fields includes 'names').",
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="Contact's last name (used when person_fields includes 'names').",
                ),
                "email": ParameterDef(
                    type="string",
                    description="Contact's email address (used when person_fields includes 'emailAddresses').",
                ),
                "phone_number": ParameterDef(
                    type="string",
                    description="Contact's phone number (used when person_fields includes 'phoneNumbers').",
                ),
                "street_address": ParameterDef(
                    type="string",
                    description="Street address (used when person_fields includes 'addresses').",
                ),
                "city": ParameterDef(
                    type="string",
                    description="City (used when person_fields includes 'addresses').",
                ),
                "state": ParameterDef(
                    type="string",
                    description="State / region (used when person_fields includes 'addresses').",
                ),
                "zip_code": ParameterDef(
                    type="string",
                    description="Postal / zip code (used when person_fields includes 'addresses').",
                ),
                "country": ParameterDef(
                    type="string",
                    description="Country (used when person_fields includes 'addresses').",
                ),
                "biography": ParameterDef(
                    type="string",
                    description="Biography text (used when person_fields includes 'biographies').",
                ),
                "birthday": ParameterDef(
                    type="string",
                    description="Birthday in YYYY-MM-DD format (used when person_fields includes 'birthdays').",
                ),
                "calendar_url": ParameterDef(
                    type="string",
                    description="Calendar URL (used when person_fields includes 'calendarUrls').",
                ),
                "gender": ParameterDef(
                    type="string",
                    description="Gender: male, female, or unspecified (used when person_fields includes 'genders').",
                ),
                "urls": ParameterDef(
                    type="array",
                    description="List of associated URLs (used when person_fields includes 'urls').",
                ),
                "additional_fields": ParameterDef(
                    type="object",
                    description=(
                        "Optional extra fields merged into the Person request body. "
                        "See https://developers.google.com/people/api/rest/v1/people for the full schema."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="delete_contact",
            description="Delete a contact by its People API resource name (e.g. 'people/c123456').",
            parameters={
                "resource_name": ParameterDef(
                    type="string",
                    description="The People API resource name identifying the contact, e.g. 'people/c123456789'.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_contact",
            description="Fetch a single contact by its People API resource name.",
            parameters={
                "resource_name": ParameterDef(
                    type="string",
                    description="The People API resource name identifying the contact, e.g. 'people/c123456789'.",
                    required=True,
                ),
                "fields": ParameterDef(
                    type="array",
                    description=(
                        "Contact fields to return — any of: addresses, ageRanges, biographies, birthdays, "
                        "calendarUrls, clientData, coverPhotos, emailAddresses, events, externalIds, "
                        "genders, imClients, interests, locales, locations, memberships, metadata, "
                        "miscKeywords, names, nicknames, occupations, organizations, phoneNumbers, "
                        "photos, relations, sipAddresses, skills, urls, userDefined."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_contacts",
            description="List every contact owned by the authenticated user (auto-paginates).",
            parameters={
                "fields": ParameterDef(
                    type="array",
                    description=(
                        "Contact fields to return on every result — same enum as get_contact's `fields`."
                    ),
                    required=True,
                ),
                "max_pages": ParameterDef(
                    type="integer",
                    description="Maximum number of pages to fetch (1-500). Prevents runaway pagination.",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="list_directory_contacts",
            description=(
                "List contacts from the Google Workspace directory (domain contacts / domain profiles). "
                "Requires the directory.readonly OAuth scope."
            ),
            parameters={
                "fields": ParameterDef(
                    type="array",
                    description="Contact fields to return — same enum as get_contact's `fields`.",
                    required=True,
                ),
                "source": ParameterDef(
                    type="string",
                    description=(
                        "Directory source to return: "
                        "'DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT' or 'DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE'."
                    ),
                    required=True,
                ),
                "merge_sources": ParameterDef(
                    type="array",
                    description=(
                        "Optional. Additional sources to merge in via verified join keys. "
                        "Any of: 'DIRECTORY_MERGE_SOURCE_TYPE_UNSPECIFIED', 'DIRECTORY_MERGE_SOURCE_TYPE_CONTACT'."
                    ),
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of people per response page (1-1000). Defaults to 100.",
                    default=100,
                ),
                "page_token": ParameterDef(
                    type="string",
                    description="Page token returned from a previous response's nextPageToken.",
                ),
                "request_sync_token": ParameterDef(
                    type="boolean",
                    description="Whether the response should include a nextSyncToken for incremental sync.",
                    default=False,
                ),
                "sync_token": ParameterDef(
                    type="string",
                    description="Sync token from a previous response — fetch only resources changed since then.",
                ),
            },
        ),
        ActionDefinition(
            name="update_contact",
            description="Update an existing contact. Re-fetches the latest etag first to avoid stale-update errors.",
            parameters={
                "resource_name": ParameterDef(
                    type="string",
                    description="The People API resource name identifying the contact to update.",
                    required=True,
                ),
                "update_person_fields": ParameterDef(
                    type="array",
                    description=(
                        "Contact sections to update — any of: names, emailAddresses, phoneNumbers, "
                        "addresses, biographies, birthdays, calendarUrls, genders, urls."
                    ),
                    required=True,
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="Updated first name (used when update_person_fields includes 'names').",
                ),
                "middle_name": ParameterDef(
                    type="string",
                    description="Updated middle name (used when update_person_fields includes 'names').",
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="Updated last name (used when update_person_fields includes 'names').",
                ),
                "email": ParameterDef(
                    type="string",
                    description="Updated email (used when update_person_fields includes 'emailAddresses').",
                ),
                "phone_number": ParameterDef(
                    type="string",
                    description="Updated phone (used when update_person_fields includes 'phoneNumbers').",
                ),
                "street_address": ParameterDef(
                    type="string",
                    description="Updated street address (used when update_person_fields includes 'addresses').",
                ),
                "city": ParameterDef(
                    type="string",
                    description="Updated city.",
                ),
                "state": ParameterDef(
                    type="string",
                    description="Updated state / region.",
                ),
                "zip_code": ParameterDef(
                    type="string",
                    description="Updated postal / zip code.",
                ),
                "country": ParameterDef(
                    type="string",
                    description="Updated country.",
                ),
                "biography": ParameterDef(
                    type="string",
                    description="Updated biography.",
                ),
                "birthday": ParameterDef(
                    type="string",
                    description="Updated birthday in YYYY-MM-DD format.",
                ),
                "calendar_url": ParameterDef(
                    type="string",
                    description="Updated calendar URL.",
                ),
                "gender": ParameterDef(
                    type="string",
                    description="Updated gender: male, female, or unspecified.",
                ),
                "urls": ParameterDef(
                    type="array",
                    description="Updated list of associated URLs.",
                ),
                "additional_fields": ParameterDef(
                    type="object",
                    description=(
                        "Optional extra fields merged into the Person request body. "
                        "See https://developers.google.com/people/api/rest/v1/people for the full schema."
                    ),
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="Google OAuth2",
            description="Connect using Google OAuth (recommended) — Contacts + Directory scopes.",
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_CONTACTS_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google Cloud OAuth 2.0 Client ID.",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxx-xxxxxxxxxxxxxxxx.apps.googleusercontent.com",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_CONTACTS_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google Cloud OAuth 2.0 Client Secret.",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                scopes=[
                    "https://www.googleapis.com/auth/contacts",
                    "https://www.googleapis.com/auth/directory.readonly",
                ],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://people.googleapis.com/v1/people/me?personFields=names",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["resourceName"],
                ),
                cost_level="free",
                description="Validates the OAuth token by fetching the authenticated user's own People profile.",
            ),
        ),
    ],
)

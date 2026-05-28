"""Typeform integration manifest."""
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
    name="typeform",
    display_name="Typeform",
    description="Online form builder for surveys, quizzes, and interactive forms",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:typeform-themed",
    app_url="https://www.typeform.com",
    categories=["Productivity & Collaboration", "forms", "surveys"],
    actions=[
        ActionDefinition(
            name="list_forms",
            description="Retrieves a list of forms from your Typeform account",
            parameters={
                "search": ParameterDef(
                    type="string",
                    description="Returns items that contain the specified string",
                ),
                "page": ParameterDef(
                    type="integer",
                    description="The page of results to retrieve. Default 1 is the first page of results",
                    default=1,
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of results to retrieve per page. Default is 10. Maximum is 200",
                    default=10,
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="Retrieve typeforms for the specified workspace ID",
                ),
            },
        ),
        ActionDefinition(
            name="create_form",
            description="Creates a new form with the specified title",
            parameters={
                "title": ParameterDef(
                    type="string",
                    description="Title to use for the typeform",
                    required=True,
                ),
                "workspace_href": ParameterDef(
                    type="string",
                    description="URL of the workspace to use for the typeform. If not specified, the form is saved in the default workspace",
                ),
            },
        ),
        ActionDefinition(
            name="duplicate_form",
            description="Duplicates an existing form and adds (copy) to the end of the title",
            parameters={
                "form_id": ParameterDef(
                    type="string",
                    description="Unique ID for the form to duplicate",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_form",
            description="Deletes a form from your Typeform account",
            parameters={
                "form_id": ParameterDef(
                    type="string",
                    description="Unique ID for the form to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_images",
            description="Retrieves a list of all images in your Typeform account",
            parameters={},
        ),
        ActionDefinition(
            name="get_form",
            description="Retrieves the details of a specific form",
            parameters={
                "form_id": ParameterDef(
                    type="string",
                    description="Unique ID for the form to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="lookup_responses",
            description="Search for form responses matching a query string",
            parameters={
                "form_id": ParameterDef(
                    type="string",
                    description="Unique ID for the form",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="Limit request to only responses that include the specified string. Matched against all answers, hidden fields, and variable values",
                    required=True,
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Maximum number of responses. Maximum value is 1000. Default is 25",
                    default=25,
                ),
                "since": ParameterDef(
                    type="string",
                    description="Limit to responses submitted since this date/time (ISO 8601 UTC or timestamp in seconds)",
                ),
                "until": ParameterDef(
                    type="string",
                    description="Limit to responses submitted until this date/time (ISO 8601 UTC or timestamp in seconds)",
                ),
                "after": ParameterDef(
                    type="string",
                    description="Limit to responses submitted after the specified token. Cannot be used with sort",
                ),
                "before": ParameterDef(
                    type="string",
                    description="Limit to responses submitted before the specified token. Cannot be used with sort",
                ),
            },
        ),
        ActionDefinition(
            name="list_responses",
            description="Returns form responses and date and time of form landing and submission",
            parameters={
                "form_id": ParameterDef(
                    type="string",
                    description="Unique ID for the form",
                    required=True,
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Maximum number of responses. Maximum value is 1000. Default is 25",
                    default=25,
                ),
                "since": ParameterDef(
                    type="string",
                    description="Limit to responses submitted since this date/time (ISO 8601 UTC or timestamp in seconds)",
                ),
                "until": ParameterDef(
                    type="string",
                    description="Limit to responses submitted until this date/time (ISO 8601 UTC or timestamp in seconds)",
                ),
                "after": ParameterDef(
                    type="string",
                    description="Limit to responses submitted after the specified token. Cannot be used with sort",
                ),
                "before": ParameterDef(
                    type="string",
                    description="Limit to responses submitted before the specified token. Cannot be used with sort",
                ),
                "included_response_ids": ParameterDef(
                    type="string",
                    description="Comma-separated list of response_ids to include. Cannot be combined with excluded_response_ids",
                ),
                "excluded_response_ids": ParameterDef(
                    type="string",
                    description="Comma-separated list of response_ids to exclude. Cannot be combined with included_response_ids",
                ),
                "completed": ParameterDef(
                    type="boolean",
                    description="Limit responses only to those which were submitted. If true, filters by submitted_at; otherwise by landed_at",
                ),
                "sort": ParameterDef(
                    type="string",
                    description="Responses order in {fieldID},{asc|desc} format. Default is submitted_at,desc",
                    default="submitted_at,desc",
                ),
                "query": ParameterDef(
                    type="string",
                    description="Limit request to only responses that include the specified string",
                ),
                "fields": ParameterDef(
                    type="string",
                    description="Comma-separated list of field IDs to show in answers section",
                ),
                "answered_fields": ParameterDef(
                    type="string",
                    description="Comma-separated list of field IDs that must have answers in the response",
                ),
            },
        ),
        ActionDefinition(
            name="update_form_title",
            description="Updates an existing form's title",
            parameters={
                "form_id": ParameterDef(
                    type="string",
                    description="Unique ID for the form to update",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="New title for the typeform",
                    required=True,
                ),
                "workspace_href": ParameterDef(
                    type="string",
                    description="URL of the workspace to move the form to",
                ),
            },
        ),
        ActionDefinition(
            name="delete_image",
            description="Deletes an image from your Typeform account",
            parameters={
                "image_id": ParameterDef(
                    type="string",
                    description="Unique ID for the image to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_image",
            description="Adds an image to your Typeform account",
            parameters={
                "file_name": ParameterDef(
                    type="string",
                    description="File name for the image",
                    required=True,
                ),
                "image": ParameterDef(
                    type="string",
                    description="Base64 code for the image (without data URI prefix). Either image or url must be provided",
                ),
                "url": ParameterDef(
                    type="string",
                    description="URL of the image to add. Either image or url must be provided",
                ),
            },
        ),
        ActionDefinition(
            name="update_dropdown_multiple_choice_ranking",
            description="Update a dropdown, multiple choice, or ranking field's choices by adding a new choice",
            parameters={
                "form_id": ParameterDef(
                    type="string",
                    description="Unique ID for the form",
                    required=True,
                ),
                "field_id": ParameterDef(
                    type="string",
                    description="Unique ID for the dropdown, multiple choice, or ranking field",
                    required=True,
                ),
                "choice": ParameterDef(
                    type="string",
                    description="The new choice label to add to the end of the existing choices",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Typeform OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="TYPEFORM_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Typeform OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://admin.typeform.com/account#/section/tokens",
                ),
                EnvVar(
                    name="TYPEFORM_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Typeform OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://admin.typeform.com/account#/section/tokens",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://api.typeform.com/oauth/authorize",
                token_url="https://api.typeform.com/oauth/token",
                scopes=[
                    "forms:read",
                    "forms:write",
                    "images:read",
                    "images:write",
                    "responses:read",
                    "accounts:read",
                    "workspaces:read",
                ],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.typeform.com/me",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["user_id"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching authenticated user info",
            ),
        ),
    ],
)

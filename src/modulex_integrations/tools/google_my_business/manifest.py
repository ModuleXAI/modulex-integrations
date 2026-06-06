"""Google My Business integration manifest."""
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
    name="google_my_business",
    display_name="Google My Business",
    description="Manage Google Business Profile posts, reviews, and replies",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:google_my_business",
    app_url="https://business.google.com",
    categories=["Marketing & Advertising", "Marketing", "Local Business", "Reviews"],
    actions=[
        ActionDefinition(
            name="create_post",
            description="Create a new local post associated with a location",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="Account name/ID for the Google Business Profile account",
                    required=True,
                ),
                "location": ParameterDef(
                    type="string",
                    description="Location name/ID whose local posts will be created",
                    required=True,
                ),
                "topic_type": ParameterDef(
                    type="string",
                    description="Topic type of the local post: STANDARD, EVENT, OFFER, or ALERT",
                    required=True,
                ),
                "language_code": ParameterDef(
                    type="string",
                    description="Language of the local post (e.g. en-US)",
                ),
                "summary": ParameterDef(
                    type="string",
                    description="Description/body of the local post",
                ),
                "call_to_action": ParameterDef(
                    type="object",
                    description="Action performed when user clicks through the post. Object with actionType and url fields",
                ),
                "event": ParameterDef(
                    type="object",
                    description="Event information. Required for topic types EVENT and OFFER. Object with title, schedule (startDate, startTime, endDate, endTime)",
                ),
                "media": ParameterDef(
                    type="array",
                    description="Media associated with the post. Array of objects with sourceUrl (publicly accessible URL) fields",
                ),
                "media_format": ParameterDef(
                    type="string",
                    description="Format of the media items: PHOTO or VIDEO",
                ),
                "alert_type": ParameterDef(
                    type="string",
                    description="Type of alert for ALERT topic type: ALERT_TYPE_UNSPECIFIED or COVID_19",
                ),
                "offer": ParameterDef(
                    type="object",
                    description="Additional data for offer posts (only for OFFER topic type). Object with couponCode, redeemOnlineUrl, termsConditions",
                ),
            },
        ),
        ActionDefinition(
            name="create_update_reply_to_review",
            description="Create or update a reply to the specified review",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="Account name/ID for the Google Business Profile account",
                    required=True,
                ),
                "location": ParameterDef(
                    type="string",
                    description="Location name/ID of the review",
                    required=True,
                ),
                "review": ParameterDef(
                    type="string",
                    description="Review name/ID to reply to",
                    required=True,
                ),
                "comment": ParameterDef(
                    type="string",
                    description="Body of the reply as plain text (max 4096 bytes)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_reviews_multiple_locations",
            description="Get reviews from multiple locations at once",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="Account name/ID for the Google Business Profile account",
                    required=True,
                ),
                "location_names": ParameterDef(
                    type="array",
                    description="List of location name/ID strings to get reviews from",
                    required=True,
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of reviews to return per location (max 50)",
                    default=50,
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="How to order reviews: 'createTime desc', 'createTime asc', 'updateTime desc', or 'updateTime asc'",
                ),
                "ignore_rating_only_reviews": ParameterDef(
                    type="boolean",
                    description="If true, only return reviews that have textual content",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_specific_review",
            description="Return a specific review by name",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="Account name/ID for the Google Business Profile account",
                    required=True,
                ),
                "location": ParameterDef(
                    type="string",
                    description="Location name/ID of the review",
                    required=True,
                ),
                "review": ParameterDef(
                    type="string",
                    description="Review name/ID to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_all_reviews",
            description="List all reviews of a location to audit reviews in bulk",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="Account name/ID for the Google Business Profile account",
                    required=True,
                ),
                "location": ParameterDef(
                    type="string",
                    description="Location name/ID whose reviews will be listed",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_posts",
            description="List local posts associated with a location",
            parameters={
                "account": ParameterDef(
                    type="string",
                    description="Account name/ID for the Google Business Profile account",
                    required=True,
                ),
                "location": ParameterDef(
                    type="string",
                    description="Location name/ID whose local posts will be listed",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Max number of posts to retrieve (each request retrieves up to 100, maximum 1000)",
                    default=100,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Google OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_MY_BUSINESS_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="123456789-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_MY_BUSINESS_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google OAuth App Client Secret",
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
                scopes=["https://www.googleapis.com/auth/business.manage"],
            ),
            test_endpoint=TestEndpoint(
                url="https://mybusinessaccountmanagement.googleapis.com/v1/accounts",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["accounts"],
                ),
                cost_level="free",
                description="Validates OAuth token by listing accessible accounts",
            ),
        ),
    ],
)

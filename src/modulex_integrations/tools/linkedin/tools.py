"""LinkedIn LangChain @tool functions."""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.linkedin.outputs import (
    CreateCommentOutput,
    CreateImagePostOrganizationOutput,
    CreateImagePostUserOutput,
    CreateLikeOnShareOutput,
    CreateTextPostOrganizationOutput,
    CreateTextPostUserOutput,
    DeletePostOutput,
    FetchAdAccountOutput,
    GetCurrentMemberProfileOutput,
    GetMemberProfileOutput,
    GetMultipleMemberProfilesOutput,
    GetOrganizationAccessControlOutput,
    GetOrganizationAdministratorsOutput,
    GetOrgMemberAccessOutput,
    GetProfilePictureFieldsOutput,
    RetrieveCommentsOnCommentsOutput,
    RetrieveCommentsSharesOutput,
    SearchOrganizationOutput,
)

__all__ = [
    "create_comment",
    "create_image_post_organization",
    "create_image_post_user",
    "create_like_on_share",
    "create_text_post_organization",
    "create_text_post_user",
    "delete_post",
    "fetch_ad_account",
    "get_current_member_profile",
    "get_member_profile",
    "get_multiple_member_profiles",
    "get_org_member_access",
    "get_organization_access_control",
    "get_organization_administrators",
    "get_profile_picture_fields",
    "retrieve_comments_on_comments",
    "retrieve_comments_shares",
    "search_organization",
]

_BASE_URL = "https://api.linkedin.com/rest"
_LINKEDIN_VERSION = "202509"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {
        "Accept": "application/json",
        "LinkedIn-Version": _LINKEDIN_VERSION,
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _escape_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


# --- Input schemas -----------------------------------------------------------


class CreateCommentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    urn_to_comment: str = Field(description="The share or user generated content post URN where the comment will be made")
    actor: str = Field(description="Entity authoring the comment, must be a person or organization URN")
    message: str = Field(description="Text of the comment")
    content: dict[str, Any] | None = Field(default=None, description="Optional media content entities as a JSON object")
    parent_comment: str | None = Field(default=None, description="URN of the parent comment for nested comments")


class CreateImagePostOrganizationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    organization_id: str = Field(description="ID of the organization that will author the post")
    image_url: str = Field(description="URL of the image to upload and post")
    text: str = Field(description="Text to be posted on the LinkedIn timeline")


class CreateImagePostUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    image_url: str = Field(description="URL of the image to upload and post")
    text: str = Field(description="Text to be posted on the LinkedIn timeline")
    visibility: str = Field(description="Visibility restrictions on content. Valid values: CONNECTIONS, PUBLIC, LOGGED_IN")


class CreateLikeOnShareInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    parent_urn: str = Field(description="The top-level share URN or user generated content URN where the like will be performed")
    actor: str = Field(description="Entity performing the like, must be a person or organization URN")
    object: str = Field(description="URN of the entity to which the like belongs")


class CreateTextPostOrganizationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    organization_id: str = Field(description="ID of the organization that will author the post")
    text: str = Field(description="Text to be posted on the LinkedIn timeline")
    article: str | None = Field(default=None, description="URL of an article to share with the post")


class CreateTextPostUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    visibility: str = Field(description="Visibility restrictions on content. Valid values: CONNECTIONS, PUBLIC, LOGGED_IN")
    text: str = Field(description="Text to be posted on the LinkedIn timeline")
    article: str | None = Field(default=None, description="URL of an article to share with the post")


class DeletePostInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    post_id: str = Field(description="URN of the post to delete")


class FetchAdAccountInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    ad_account_id: str = Field(description="ID of the ad account to fetch")


class GetCurrentMemberProfileInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class GetMemberProfileInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    person_id: str = Field(description="Identifier of the person to retrieve")


class GetMultipleMemberProfilesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    people_ids: list[str] = Field(description="List of person ID strings to retrieve")


class GetOrgMemberAccessInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    role: str | None = Field(default=None, description="Limit results to a specific role. Valid values: ADMINISTRATOR, DIRECT_SPONSORED_CONTENT_POSTER, RECRUITING_POSTER, LEAD_CAPTURE_ADMINISTRATOR, LEAD_GEN_FORMS_MANAGER, ANALYST, CURATOR, CONTENT_ADMINISTRATOR")
    state: str | None = Field(default=None, description="Limit results to a specific role state. Valid values: APPROVED, REJECTED, REQUESTED, REVOKED")


class GetOrganizationAccessControlInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    organization_id: str = Field(description="ID of the organization")
    max: int = Field(default=50, description="Maximum number of results to return")


class GetOrganizationAdministratorsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    organization_id: str = Field(description="ID of the organization")
    max_pages: int = Field(default=50, description="Maximum number of pages to fetch (1-500)", ge=1, le=500)


class GetProfilePictureFieldsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    include_original_image: bool = Field(default=False, description="Whether to include the original image data in the response")


class RetrieveCommentsOnCommentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    comment_urn: str = Field(description="Parent comment URN to retrieve nested comments for")
    max: int = Field(default=50, description="Maximum number of results to return")


class RetrieveCommentsSharesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    entity_urn: str = Field(description="URN of the entity to retrieve comments on")
    max: int = Field(default=50, description="Maximum number of results to return")


class SearchOrganizationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    search_by: str = Field(description="Field to search by. Valid values: vanityName, emailDomain")
    search_term: str = Field(description="Keyword to search for")
    max: int = Field(default=50, description="Maximum number of results to return")


# --- @tool functions ---------------------------------------------------------


@tool(args_schema=CreateCommentInput)
@serialize_pydantic_return
async def create_comment(
    auth_type: str,
    auth_data: dict[str, Any],
    urn_to_comment: str,
    actor: str,
    message: str,
    content: dict[str, Any] | None = None,
    parent_comment: str | None = None,
) -> CreateCommentOutput:
    """Create a comment on a share or user generated content post."""
    if not auth_data.get("access_token"):
        return CreateCommentOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    encoded_urn = quote(urn_to_comment, safe="")
    body: dict[str, Any] = {
        "object": urn_to_comment,
        "actor": actor,
        "message": {"text": message},
    }
    if content is not None:
        body["content"] = [content]
    if parent_comment is not None:
        body["parentComment"] = parent_comment
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/socialActions/{encoded_urn}/comments",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateCommentOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateCommentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateCommentOutput(success=False, error=f"Call failed: {exc}")
    return CreateCommentOutput(success=True, data=data)


@tool(args_schema=CreateImagePostOrganizationInput)
@serialize_pydantic_return
async def create_image_post_organization(
    auth_type: str,
    auth_data: dict[str, Any],
    organization_id: str,
    image_url: str,
    text: str,
) -> CreateImagePostOrganizationOutput:
    """Create an image post on LinkedIn as an organization."""
    if not auth_data.get("access_token"):
        return CreateImagePostOrganizationOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    org_urn = f"urn:li:organization:{organization_id}"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            init_response = await client.post(
                f"{_BASE_URL}/images?action=initializeUpload",
                headers=headers,
                json={
                    "initializeUploadRequest": {
                        "owner": org_urn,
                    },
                },
            )
            if init_response.status_code not in (200, 201):
                return CreateImagePostOrganizationOutput(
                    success=False,
                    error=f"Image upload init failed ({init_response.status_code}): {init_response.text}",
                )
            init_data = init_response.json()
            upload_url = init_data["value"]["uploadUrl"]
            image_urn = init_data["value"]["image"]

            img_response = await client.get(image_url)
            img_response.raise_for_status()
            image_bytes = img_response.content

            upload_response = await client.put(
                upload_url,
                content=image_bytes,
                headers={"Content-Type": "application/octet-stream"},
            )
            if upload_response.status_code not in (200, 201):
                return CreateImagePostOrganizationOutput(
                    success=False,
                    error=f"Image upload failed ({upload_response.status_code}): {upload_response.text}",
                )

            post_body: dict[str, Any] = {
                "author": org_urn,
                "commentary": _escape_text(text),
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "content": {
                    "media": {
                        "id": image_urn,
                    },
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            }
            post_response = await client.post(
                f"{_BASE_URL}/posts",
                headers=headers,
                json=post_body,
            )
        if post_response.status_code not in (200, 201):
            return CreateImagePostOrganizationOutput(
                success=False,
                error=f"Post creation failed ({post_response.status_code}): {post_response.text}",
            )
        post_urn = post_response.headers.get("x-restli-id")
    except httpx.TimeoutException:
        return CreateImagePostOrganizationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateImagePostOrganizationOutput(success=False, error=f"Call failed: {exc}")
    return CreateImagePostOrganizationOutput(success=True, post_urn=post_urn)


@tool(args_schema=CreateImagePostUserInput)
@serialize_pydantic_return
async def create_image_post_user(
    auth_type: str,
    auth_data: dict[str, Any],
    image_url: str,
    text: str,
    visibility: str,
) -> CreateImagePostUserOutput:
    """Create an image post on LinkedIn as the authenticated user."""
    if not auth_data.get("access_token"):
        return CreateImagePostUserOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            me_response = await client.get(
                f"{_BASE_URL}/me",
                headers=headers,
            )
            me_response.raise_for_status()
            person_id = me_response.json().get("id", "")
            person_urn = f"urn:li:person:{person_id}"

            init_response = await client.post(
                f"{_BASE_URL}/images?action=initializeUpload",
                headers=headers,
                json={
                    "initializeUploadRequest": {
                        "owner": person_urn,
                    },
                },
            )
            if init_response.status_code not in (200, 201):
                return CreateImagePostUserOutput(
                    success=False,
                    error=f"Image upload init failed ({init_response.status_code}): {init_response.text}",
                )
            init_data = init_response.json()
            upload_url = init_data["value"]["uploadUrl"]
            image_urn = init_data["value"]["image"]

            img_response = await client.get(image_url)
            img_response.raise_for_status()
            image_bytes = img_response.content

            upload_response = await client.put(
                upload_url,
                content=image_bytes,
                headers={"Content-Type": "application/octet-stream"},
            )
            if upload_response.status_code not in (200, 201):
                return CreateImagePostUserOutput(
                    success=False,
                    error=f"Image upload failed ({upload_response.status_code}): {upload_response.text}",
                )

            post_body: dict[str, Any] = {
                "author": person_urn,
                "commentary": _escape_text(text),
                "visibility": visibility,
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "content": {
                    "media": {
                        "id": image_urn,
                    },
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            }
            post_response = await client.post(
                f"{_BASE_URL}/posts",
                headers=headers,
                json=post_body,
            )
        if post_response.status_code not in (200, 201):
            return CreateImagePostUserOutput(
                success=False,
                error=f"Post creation failed ({post_response.status_code}): {post_response.text}",
            )
        post_urn = post_response.headers.get("x-restli-id")
    except httpx.TimeoutException:
        return CreateImagePostUserOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateImagePostUserOutput(success=False, error=f"Call failed: {exc}")
    return CreateImagePostUserOutput(success=True, post_urn=post_urn)


@tool(args_schema=CreateLikeOnShareInput)
@serialize_pydantic_return
async def create_like_on_share(
    auth_type: str,
    auth_data: dict[str, Any],
    parent_urn: str,
    actor: str,
    object: str,
) -> CreateLikeOnShareOutput:
    """Create a like on a share or user generated content post."""
    if not auth_data.get("access_token"):
        return CreateLikeOnShareOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    encoded_urn = quote(parent_urn, safe="")
    body: dict[str, Any] = {
        "actor": actor,
        "object": object,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/socialActions/{encoded_urn}/likes",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateLikeOnShareOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return CreateLikeOnShareOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateLikeOnShareOutput(success=False, error=f"Call failed: {exc}")
    return CreateLikeOnShareOutput(success=True)


@tool(args_schema=CreateTextPostOrganizationInput)
@serialize_pydantic_return
async def create_text_post_organization(
    auth_type: str,
    auth_data: dict[str, Any],
    organization_id: str,
    text: str,
    article: str | None = None,
) -> CreateTextPostOrganizationOutput:
    """Create a text post on LinkedIn as an organization, optionally with an article URL."""
    if not auth_data.get("access_token"):
        return CreateTextPostOrganizationOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    org_urn = f"urn:li:organization:{organization_id}"
    body: dict[str, Any] = {
        "author": org_urn,
        "commentary": _escape_text(text),
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    if article:
        body["content"] = {
            "article": {
                "source": article,
            },
        }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/posts",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateTextPostOrganizationOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json() if response.text else {}
    except httpx.TimeoutException:
        return CreateTextPostOrganizationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateTextPostOrganizationOutput(success=False, error=f"Call failed: {exc}")
    return CreateTextPostOrganizationOutput(success=True, data=data if data else None)


@tool(args_schema=CreateTextPostUserInput)
@serialize_pydantic_return
async def create_text_post_user(
    auth_type: str,
    auth_data: dict[str, Any],
    visibility: str,
    text: str,
    article: str | None = None,
) -> CreateTextPostUserOutput:
    """Create a text post on LinkedIn as the authenticated user, optionally with an article URL."""
    if not auth_data.get("access_token"):
        return CreateTextPostUserOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            me_response = await client.get(
                f"{_BASE_URL}/me",
                headers=headers,
            )
            me_response.raise_for_status()
            person_id = me_response.json().get("id", "")
            person_urn = f"urn:li:person:{person_id}"

            body: dict[str, Any] = {
                "author": person_urn,
                "commentary": _escape_text(text),
                "visibility": visibility,
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            }
            if article:
                body["content"] = {
                    "article": {
                        "source": article,
                    },
                }
            response = await client.post(
                f"{_BASE_URL}/posts",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateTextPostUserOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json() if response.text else {}
    except httpx.TimeoutException:
        return CreateTextPostUserOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateTextPostUserOutput(success=False, error=f"Call failed: {exc}")
    return CreateTextPostUserOutput(success=True, data=data if data else None)


@tool(args_schema=DeletePostInput)
@serialize_pydantic_return
async def delete_post(
    auth_type: str,
    auth_data: dict[str, Any],
    post_id: str,
) -> DeletePostOutput:
    """Delete a post from LinkedIn."""
    if not auth_data.get("access_token"):
        return DeletePostOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    encoded_id = quote(post_id, safe="")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/posts/{encoded_id}",
                headers=headers,
            )
        if response.status_code not in (200, 204):
            return DeletePostOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeletePostOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeletePostOutput(success=False, error=f"Call failed: {exc}")
    return DeletePostOutput(success=True)


@tool(args_schema=FetchAdAccountInput)
@serialize_pydantic_return
async def fetch_ad_account(
    auth_type: str,
    auth_data: dict[str, Any],
    ad_account_id: str,
) -> FetchAdAccountOutput:
    """Fetch an individual ad account given its ID."""
    if not auth_data.get("access_token"):
        return FetchAdAccountOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    encoded_id = quote(ad_account_id, safe="")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/adAccounts/{encoded_id}",
                headers=headers,
            )
        if response.status_code != 200:
            return FetchAdAccountOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return FetchAdAccountOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FetchAdAccountOutput(success=False, error=f"Call failed: {exc}")
    return FetchAdAccountOutput(success=True, data=data)


@tool(args_schema=GetCurrentMemberProfileInput)
@serialize_pydantic_return
async def get_current_member_profile(
    auth_type: str,
    auth_data: dict[str, Any],
) -> GetCurrentMemberProfileOutput:
    """Get the profile of the current authenticated member."""
    if not auth_data.get("access_token"):
        return GetCurrentMemberProfileOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/me",
                headers=headers,
            )
        if response.status_code != 200:
            return GetCurrentMemberProfileOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetCurrentMemberProfileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCurrentMemberProfileOutput(success=False, error=f"Call failed: {exc}")
    return GetCurrentMemberProfileOutput(success=True, data=data)


@tool(args_schema=GetMemberProfileInput)
@serialize_pydantic_return
async def get_member_profile(
    auth_type: str,
    auth_data: dict[str, Any],
    person_id: str,
) -> GetMemberProfileOutput:
    """Get another member's profile given their person ID."""
    if not auth_data.get("access_token"):
        return GetMemberProfileOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/people/(id:{person_id})",
                headers=headers,
            )
        if response.status_code != 200:
            return GetMemberProfileOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetMemberProfileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetMemberProfileOutput(success=False, error=f"Call failed: {exc}")
    return GetMemberProfileOutput(success=True, data=data)


@tool(args_schema=GetMultipleMemberProfilesInput)
@serialize_pydantic_return
async def get_multiple_member_profiles(
    auth_type: str,
    auth_data: dict[str, Any],
    people_ids: list[str],
) -> GetMultipleMemberProfilesOutput:
    """Get multiple member profiles at once given their person IDs."""
    if not auth_data.get("access_token"):
        return GetMultipleMemberProfilesOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    ids_param = ",".join(f"(id:{pid})" for pid in people_ids)
    params = f"ids=List({ids_param})"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/people?{params}",
                headers=headers,
            )
        if response.status_code != 200:
            return GetMultipleMemberProfilesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetMultipleMemberProfilesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetMultipleMemberProfilesOutput(success=False, error=f"Call failed: {exc}")
    results = data.get("results", data) if isinstance(data, dict) else data
    if isinstance(results, dict):
        results = list(results.values())
    return GetMultipleMemberProfilesOutput(success=True, results=results)


@tool(args_schema=GetOrgMemberAccessInput)
@serialize_pydantic_return
async def get_org_member_access(
    auth_type: str,
    auth_data: dict[str, Any],
    role: str | None = None,
    state: str | None = None,
) -> GetOrgMemberAccessOutput:
    """Get the organization access control information of the current authenticated member."""
    if not auth_data.get("access_token"):
        return GetOrgMemberAccessOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {
        "q": "roleAssignee",
        "count": 1,
    }
    if role:
        params["role"] = role
    if state:
        params["state"] = state
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/organizationAcls",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return GetOrgMemberAccessOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetOrgMemberAccessOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetOrgMemberAccessOutput(success=False, error=f"Call failed: {exc}")
    elements = data.get("elements", [])
    return GetOrgMemberAccessOutput(
        success=True,
        data=elements[0] if elements else None,
    )


@tool(args_schema=GetOrganizationAccessControlInput)
@serialize_pydantic_return
async def get_organization_access_control(
    auth_type: str,
    auth_data: dict[str, Any],
    organization_id: str,
    max: int = 50,
) -> GetOrganizationAccessControlOutput:
    """Get a selected organization's access control information."""
    if not auth_data.get("access_token"):
        return GetOrganizationAccessControlOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    all_elements: list[dict[str, Any]] = []
    start = 0
    count = 50
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while len(all_elements) < max:
                response = await client.get(
                    f"{_BASE_URL}/organizationAcls",
                    headers=headers,
                    params={
                        "q": "organization",
                        "organization": f"urn:li:organization:{organization_id}",
                        "start": start,
                        "count": count,
                    },
                )
                if response.status_code != 200:
                    return GetOrganizationAccessControlOutput(
                        success=False,
                        error=f"API error ({response.status_code}): {response.text}",
                    )
                data = response.json()
                elements = data.get("elements", [])
                if not elements:
                    break
                all_elements.extend(elements)
                start += count
    except httpx.TimeoutException:
        return GetOrganizationAccessControlOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetOrganizationAccessControlOutput(success=False, error=f"Call failed: {exc}")
    return GetOrganizationAccessControlOutput(success=True, elements=all_elements[:max])


@tool(args_schema=GetOrganizationAdministratorsInput)
@serialize_pydantic_return
async def get_organization_administrators(
    auth_type: str,
    auth_data: dict[str, Any],
    organization_id: str,
    max_pages: int = 50,
) -> GetOrganizationAdministratorsOutput:
    """Get the administrator members of a selected organization."""
    if not auth_data.get("access_token"):
        return GetOrganizationAdministratorsOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    all_elements: list[dict[str, Any]] = []
    start = 0
    count = 50
    pages_seen = 0
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while pages_seen < max_pages:
                pages_seen += 1
                response = await client.get(
                    f"{_BASE_URL}/organizationAcls",
                    headers=headers,
                    params={
                        "q": "organization",
                        "organization": f"urn:li:organization:{organization_id}",
                        "role": "ADMINISTRATOR",
                        "state": "APPROVED",
                        "start": start,
                        "count": count,
                    },
                )
                if response.status_code != 200:
                    return GetOrganizationAdministratorsOutput(
                        success=False,
                        error=f"API error ({response.status_code}): {response.text}",
                    )
                data = response.json()
                elements = data.get("elements", [])
                if not elements:
                    break
                all_elements.extend(elements)
                start += count
    except httpx.TimeoutException:
        return GetOrganizationAdministratorsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetOrganizationAdministratorsOutput(success=False, error=f"Call failed: {exc}")
    return GetOrganizationAdministratorsOutput(success=True, elements=all_elements)


@tool(args_schema=GetProfilePictureFieldsInput)
@serialize_pydantic_return
async def get_profile_picture_fields(
    auth_type: str,
    auth_data: dict[str, Any],
    include_original_image: bool = False,
) -> GetProfilePictureFieldsOutput:
    """Get the authenticated user's profile picture data including display image and metadata."""
    if not auth_data.get("access_token"):
        return GetProfilePictureFieldsOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    projection = "(id,profilePicture(displayImage~digitalmediaAsset:playableStreams))"
    if include_original_image:
        projection = "(id,profilePicture(displayImage~digitalmediaAsset:playableStreams,displayImage~:originalImage))"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                "https://api.linkedin.com/v2/me",
                headers=headers,
                params={"projection": projection},
            )
        if response.status_code != 200:
            return GetProfilePictureFieldsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetProfilePictureFieldsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetProfilePictureFieldsOutput(success=False, error=f"Call failed: {exc}")
    return GetProfilePictureFieldsOutput(success=True, data=data)


async def _paginate_comments(
    headers: dict[str, str],
    urn: str,
    max_results: int,
) -> tuple[bool, str | None, list[dict[str, Any]]]:
    encoded_urn = quote(urn, safe="")
    all_elements: list[dict[str, Any]] = []
    start = 0
    count = 50
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while len(all_elements) < max_results:
                response = await client.get(
                    f"{_BASE_URL}/socialActions/{encoded_urn}/comments",
                    headers=headers,
                    params={"start": start, "count": count},
                )
                if response.status_code != 200:
                    return False, f"API error ({response.status_code}): {response.text}", []
                data = response.json()
                elements = data.get("elements", [])
                if not elements:
                    break
                all_elements.extend(elements)
                start += count
    except httpx.TimeoutException:
        return False, "Request timed out.", []
    except Exception as exc:
        return False, f"Call failed: {exc}", []
    return True, None, all_elements[:max_results]


@tool(args_schema=RetrieveCommentsOnCommentsInput)
@serialize_pydantic_return
async def retrieve_comments_on_comments(
    auth_type: str,
    auth_data: dict[str, Any],
    comment_urn: str,
    max: int = 50,
) -> RetrieveCommentsOnCommentsOutput:
    """Retrieve comments on a comment given the parent comment URN."""
    if not auth_data.get("access_token"):
        return RetrieveCommentsOnCommentsOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    ok, error, elements = await _paginate_comments(headers, comment_urn, max)
    if not ok:
        return RetrieveCommentsOnCommentsOutput(success=False, error=error)
    return RetrieveCommentsOnCommentsOutput(success=True, elements=elements)


@tool(args_schema=RetrieveCommentsSharesInput)
@serialize_pydantic_return
async def retrieve_comments_shares(
    auth_type: str,
    auth_data: dict[str, Any],
    entity_urn: str,
    max: int = 50,
) -> RetrieveCommentsSharesOutput:
    """Retrieve comments on a share given the share URN."""
    if not auth_data.get("access_token"):
        return RetrieveCommentsSharesOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    ok, error, elements = await _paginate_comments(headers, entity_urn, max)
    if not ok:
        return RetrieveCommentsSharesOutput(success=False, error=error)
    return RetrieveCommentsSharesOutput(success=True, elements=elements)


@tool(args_schema=SearchOrganizationInput)
@serialize_pydantic_return
async def search_organization(
    auth_type: str,
    auth_data: dict[str, Any],
    search_by: str,
    search_term: str,
    max: int = 50,
) -> SearchOrganizationOutput:
    """Search for an organization by vanity name or email domain."""
    if not auth_data.get("access_token"):
        return SearchOrganizationOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    all_elements: list[dict[str, Any]] = []
    start = 0
    count = 50
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while len(all_elements) < max:
                response = await client.get(
                    f"{_BASE_URL}/organizations",
                    headers=headers,
                    params={
                        "q": search_by,
                        search_by: search_term,
                        "start": start,
                        "count": count,
                    },
                )
                if response.status_code != 200:
                    return SearchOrganizationOutput(
                        success=False,
                        error=f"API error ({response.status_code}): {response.text}",
                    )
                data = response.json()
                elements = data.get("elements", [])
                if not elements:
                    break
                all_elements.extend(elements)
                start += count
    except httpx.TimeoutException:
        return SearchOrganizationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchOrganizationOutput(success=False, error=f"Call failed: {exc}")
    return SearchOrganizationOutput(success=True, elements=all_elements[:max])

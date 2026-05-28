"""Typeform LangChain @tool functions."""
from __future__ import annotations

import json
import re
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.typeform.outputs import (
    CreateFormOutput,
    CreateImageOutput,
    DeleteFormOutput,
    DeleteImageOutput,
    DuplicateFormOutput,
    FormSummary,
    GetFormOutput,
    ImageItem,
    ListFormsOutput,
    ListImagesOutput,
    ListResponsesOutput,
    LookupResponsesOutput,
    ResponseItem,
    UpdateDropdownMultipleChoiceRankingOutput,
    UpdateFormTitleOutput,
)

__all__ = [
    "create_form",
    "create_image",
    "delete_form",
    "delete_image",
    "duplicate_form",
    "get_form",
    "list_forms",
    "list_images",
    "list_responses",
    "lookup_responses",
    "update_dropdown_multiple_choice_ranking",
    "update_form_title",
]

_BASE_URL = "https://api.typeform.com"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Typeform API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class ListFormsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    search: str | None = Field(default=None, description="Returns items that contain the specified string")
    page: int = Field(default=1, description="The page of results to retrieve")
    page_size: int = Field(default=10, description="Number of results to retrieve per page. Maximum is 200")
    workspace_id: str | None = Field(default=None, description="Retrieve typeforms for the specified workspace ID")


class CreateFormInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    title: str = Field(description="Title to use for the typeform")
    workspace_href: str | None = Field(default=None, description="URL of the workspace to use for the typeform")


class DuplicateFormInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    form_id: str = Field(description="Unique ID for the form to duplicate")


class DeleteFormInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    form_id: str = Field(description="Unique ID for the form to delete")


class ListImagesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class GetFormInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    form_id: str = Field(description="Unique ID for the form to retrieve")


class LookupResponsesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    form_id: str = Field(description="Unique ID for the form")
    query: str = Field(description="Limit request to only responses that include the specified string")
    page_size: int = Field(default=25, description="Maximum number of responses. Maximum is 1000")
    since: str | None = Field(default=None, description="Limit to responses submitted since this date/time")
    until: str | None = Field(default=None, description="Limit to responses submitted until this date/time")
    after: str | None = Field(default=None, description="Limit to responses submitted after the specified token")
    before: str | None = Field(default=None, description="Limit to responses submitted before the specified token")


class ListResponsesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    form_id: str = Field(description="Unique ID for the form")
    page_size: int = Field(default=25, description="Maximum number of responses. Maximum is 1000")
    since: str | None = Field(default=None, description="Limit to responses submitted since this date/time")
    until: str | None = Field(default=None, description="Limit to responses submitted until this date/time")
    after: str | None = Field(default=None, description="Limit to responses submitted after the specified token")
    before: str | None = Field(default=None, description="Limit to responses submitted before the specified token")
    included_response_ids: str | None = Field(default=None, description="Comma-separated list of response_ids to include")
    excluded_response_ids: str | None = Field(default=None, description="Comma-separated list of response_ids to exclude")
    completed: bool | None = Field(default=None, description="Limit responses only to those which were submitted")
    sort: str = Field(default="submitted_at,desc", description="Responses order in {fieldID},{asc|desc} format")
    query: str | None = Field(default=None, description="Limit request to only responses that include the specified string")
    fields: str | None = Field(default=None, description="Comma-separated list of field IDs to show in answers section")
    answered_fields: str | None = Field(default=None, description="Comma-separated list of field IDs that must have answers")


class UpdateFormTitleInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    form_id: str = Field(description="Unique ID for the form to update")
    title: str = Field(description="New title for the typeform")
    workspace_href: str | None = Field(default=None, description="URL of the workspace to move the form to")


class DeleteImageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    image_id: str = Field(description="Unique ID for the image to delete")


class CreateImageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    file_name: str = Field(description="File name for the image")
    image: str | None = Field(default=None, description="Base64 code for the image (without data URI prefix)")
    url: str | None = Field(default=None, description="URL of the image to add. Either image or url must be provided")


class UpdateDropdownMultipleChoiceRankingInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    form_id: str = Field(description="Unique ID for the form")
    field_id: str = Field(description="Unique ID for the dropdown, multiple choice, or ranking field")
    choice: str = Field(description="The new choice label to add to the end of the existing choices")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=ListFormsInput)
@serialize_pydantic_return
async def list_forms(
    auth_type: str,
    auth_data: dict[str, Any],
    search: str | None = None,
    page: int = 1,
    page_size: int = 10,
    workspace_id: str | None = None,
) -> ListFormsOutput:
    """Retrieves a list of forms from your Typeform account."""
    if not auth_data.get("access_token"):
        return ListFormsOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if search:
        params["search"] = search
    if workspace_id:
        params["workspace_id"] = workspace_id
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/forms",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListFormsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListFormsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListFormsOutput(success=False, error=f"Call failed: {exc}")
    items = data.get("items", [])
    forms = [
        FormSummary(
            id=f.get("id"),
            title=f.get("title"),
            type=f.get("type"),
            last_updated_at=f.get("last_updated_at"),
            self_url=(f.get("_links") or {}).get("display"),
        )
        for f in items
    ]
    return ListFormsOutput(
        success=True,
        forms=forms,
        total_items=data.get("total_items"),
        page_count=data.get("page_count"),
    )


@tool(args_schema=CreateFormInput)
@serialize_pydantic_return
async def create_form(
    auth_type: str,
    auth_data: dict[str, Any],
    title: str,
    workspace_href: str | None = None,
) -> CreateFormOutput:
    """Creates a new form with the specified title."""
    if not auth_data.get("access_token"):
        return CreateFormOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    payload: dict[str, Any] = {"title": title}
    if workspace_href:
        payload["workspace"] = {"href": workspace_href}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/forms",
                headers=headers,
                json=payload,
            )
        if response.status_code not in (200, 201):
            return CreateFormOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateFormOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateFormOutput(success=False, error=f"Call failed: {exc}")
    return CreateFormOutput(
        success=True,
        id=data.get("id"),
        title=data.get("title"),
        type=data.get("type"),
        self_url=(data.get("_links") or {}).get("display"),
    )


@tool(args_schema=DuplicateFormInput)
@serialize_pydantic_return
async def duplicate_form(
    auth_type: str,
    auth_data: dict[str, Any],
    form_id: str,
) -> DuplicateFormOutput:
    """Duplicates an existing form and adds (copy) to the end of the title."""
    if not auth_data.get("access_token"):
        return DuplicateFormOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            get_response = await client.get(
                f"{_BASE_URL}/forms/{form_id}",
                headers=headers,
            )
        if get_response.status_code != 200:
            return DuplicateFormOutput(
                success=False,
                error=f"API error fetching form ({get_response.status_code}): {get_response.text}",
            )
        form_data = get_response.json()
        form_data.pop("id", None)
        form_data.pop("_links", None)
        form_data["title"] = f"{form_data.get('title', '')} (copy)"
        form_json = json.dumps(form_data)
        form_json = re.sub(r'"id"\s*:\s*"[^"]*"', '"id":""', form_json)
        cleaned_form = json.loads(form_json)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            create_response = await client.post(
                f"{_BASE_URL}/forms",
                headers=headers,
                json=cleaned_form,
            )
        if create_response.status_code not in (200, 201):
            return DuplicateFormOutput(
                success=False,
                error=f"API error creating copy ({create_response.status_code}): {create_response.text}",
            )
        data = create_response.json()
    except httpx.TimeoutException:
        return DuplicateFormOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DuplicateFormOutput(success=False, error=f"Call failed: {exc}")
    return DuplicateFormOutput(
        success=True,
        id=data.get("id"),
        title=data.get("title"),
        type=data.get("type"),
        self_url=(data.get("_links") or {}).get("display"),
    )


@tool(args_schema=DeleteFormInput)
@serialize_pydantic_return
async def delete_form(
    auth_type: str,
    auth_data: dict[str, Any],
    form_id: str,
) -> DeleteFormOutput:
    """Deletes a form from your Typeform account."""
    if not auth_data.get("access_token"):
        return DeleteFormOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/forms/{form_id}",
                headers=headers,
            )
        if response.status_code not in (200, 204):
            return DeleteFormOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteFormOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteFormOutput(success=False, error=f"Call failed: {exc}")
    return DeleteFormOutput(success=True, id=form_id)


@tool(args_schema=ListImagesInput)
@serialize_pydantic_return
async def list_images(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListImagesOutput:
    """Retrieves a list of all images in your Typeform account."""
    if not auth_data.get("access_token"):
        return ListImagesOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/images",
                headers=headers,
            )
        if response.status_code != 200:
            return ListImagesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListImagesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListImagesOutput(success=False, error=f"Call failed: {exc}")
    images = [
        ImageItem(
            id=img.get("id"),
            src=img.get("src"),
            file_name=img.get("file_name"),
            width=img.get("width"),
            height=img.get("height"),
        )
        for img in (data if isinstance(data, list) else [])
    ]
    return ListImagesOutput(success=True, images=images)


@tool(args_schema=GetFormInput)
@serialize_pydantic_return
async def get_form(
    auth_type: str,
    auth_data: dict[str, Any],
    form_id: str,
) -> GetFormOutput:
    """Retrieves the details of a specific form."""
    if not auth_data.get("access_token"):
        return GetFormOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/forms/{form_id}",
                headers=headers,
            )
        if response.status_code != 200:
            return GetFormOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetFormOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetFormOutput(success=False, error=f"Call failed: {exc}")
    return GetFormOutput(
        success=True,
        id=data.get("id"),
        title=data.get("title"),
        type=data.get("type"),
        fields=data.get("fields", []),
        self_url=(data.get("_links") or {}).get("display"),
    )


@tool(args_schema=LookupResponsesInput)
@serialize_pydantic_return
async def lookup_responses(
    auth_type: str,
    auth_data: dict[str, Any],
    form_id: str,
    query: str,
    page_size: int = 25,
    since: str | None = None,
    until: str | None = None,
    after: str | None = None,
    before: str | None = None,
) -> LookupResponsesOutput:
    """Search for form responses matching a query string."""
    if not auth_data.get("access_token"):
        return LookupResponsesOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"query": query, "page_size": page_size}
    if since:
        params["since"] = since
    if until:
        params["until"] = until
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/forms/{form_id}/responses",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return LookupResponsesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return LookupResponsesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return LookupResponsesOutput(success=False, error=f"Call failed: {exc}")
    items = [
        ResponseItem(
            response_id=r.get("response_id"),
            landed_at=r.get("landed_at"),
            submitted_at=r.get("submitted_at"),
            answers=r.get("answers", []),
        )
        for r in data.get("items", [])
    ]
    return LookupResponsesOutput(
        success=True,
        items=items,
        total_items=data.get("total_items"),
        page_count=data.get("page_count"),
    )


@tool(args_schema=ListResponsesInput)
@serialize_pydantic_return
async def list_responses(
    auth_type: str,
    auth_data: dict[str, Any],
    form_id: str,
    page_size: int = 25,
    since: str | None = None,
    until: str | None = None,
    after: str | None = None,
    before: str | None = None,
    included_response_ids: str | None = None,
    excluded_response_ids: str | None = None,
    completed: bool | None = None,
    sort: str = "submitted_at,desc",
    query: str | None = None,
    fields: str | None = None,
    answered_fields: str | None = None,
) -> ListResponsesOutput:
    """Returns form responses and date and time of form landing and submission."""
    if not auth_data.get("access_token"):
        return ListResponsesOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"page_size": page_size, "sort": sort}
    if since:
        params["since"] = since
    if until:
        params["until"] = until
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    if included_response_ids:
        params["included_response_ids"] = included_response_ids
    if excluded_response_ids:
        params["excluded_response_ids"] = excluded_response_ids
    if completed is not None:
        params["completed"] = str(completed).lower()
    if query:
        params["query"] = query
    if fields:
        params["fields"] = fields
    if answered_fields:
        params["answered_fields"] = answered_fields
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/forms/{form_id}/responses",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListResponsesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListResponsesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListResponsesOutput(success=False, error=f"Call failed: {exc}")
    items = [
        ResponseItem(
            response_id=r.get("response_id"),
            landed_at=r.get("landed_at"),
            submitted_at=r.get("submitted_at"),
            answers=r.get("answers", []),
        )
        for r in data.get("items", [])
    ]
    return ListResponsesOutput(
        success=True,
        items=items,
        total_items=data.get("total_items"),
        page_count=data.get("page_count"),
    )


@tool(args_schema=UpdateFormTitleInput)
@serialize_pydantic_return
async def update_form_title(
    auth_type: str,
    auth_data: dict[str, Any],
    form_id: str,
    title: str,
    workspace_href: str | None = None,
) -> UpdateFormTitleOutput:
    """Updates an existing form's title."""
    if not auth_data.get("access_token"):
        return UpdateFormTitleOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    patch_ops: list[dict[str, str]] = [
        {"op": "replace", "path": "/title", "value": title},
    ]
    if workspace_href:
        patch_ops.append({"op": "replace", "path": "/workspace/href", "value": workspace_href})
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/forms/{form_id}",
                headers=headers,
                json=patch_ops,
            )
        if response.status_code not in (200, 204):
            return UpdateFormTitleOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return UpdateFormTitleOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateFormTitleOutput(success=False, error=f"Call failed: {exc}")
    return UpdateFormTitleOutput(success=True, id=form_id, title=title)


@tool(args_schema=DeleteImageInput)
@serialize_pydantic_return
async def delete_image(
    auth_type: str,
    auth_data: dict[str, Any],
    image_id: str,
) -> DeleteImageOutput:
    """Deletes an image from your Typeform account."""
    if not auth_data.get("access_token"):
        return DeleteImageOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/images/{image_id}",
                headers=headers,
            )
        if response.status_code not in (200, 204):
            return DeleteImageOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteImageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteImageOutput(success=False, error=f"Call failed: {exc}")
    return DeleteImageOutput(success=True, id=image_id)


@tool(args_schema=CreateImageInput)
@serialize_pydantic_return
async def create_image(
    auth_type: str,
    auth_data: dict[str, Any],
    file_name: str,
    image: str | None = None,
    url: str | None = None,
) -> CreateImageOutput:
    """Adds an image to your Typeform account."""
    if not auth_data.get("access_token"):
        return CreateImageOutput(success=False, error="Missing OAuth2 access token.")
    if not image and not url:
        return CreateImageOutput(
            success=False,
            error="Either 'image' (base64) or 'url' must be provided.",
        )
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    payload: dict[str, Any] = {"file_name": file_name}
    if image:
        payload["image"] = image
    if url:
        payload["url"] = url
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/images",
                headers=headers,
                json=payload,
            )
        if response.status_code not in (200, 201):
            return CreateImageOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateImageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateImageOutput(success=False, error=f"Call failed: {exc}")
    return CreateImageOutput(
        success=True,
        id=data.get("id"),
        src=data.get("src"),
        file_name=data.get("file_name"),
        width=data.get("width"),
        height=data.get("height"),
    )


@tool(args_schema=UpdateDropdownMultipleChoiceRankingInput)
@serialize_pydantic_return
async def update_dropdown_multiple_choice_ranking(
    auth_type: str,
    auth_data: dict[str, Any],
    form_id: str,
    field_id: str,
    choice: str,
) -> UpdateDropdownMultipleChoiceRankingOutput:
    """Update a dropdown, multiple choice, or ranking field's choices by adding a new choice."""
    if not auth_data.get("access_token"):
        return UpdateDropdownMultipleChoiceRankingOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            get_response = await client.get(
                f"{_BASE_URL}/forms/{form_id}",
                headers=headers,
            )
        if get_response.status_code != 200:
            return UpdateDropdownMultipleChoiceRankingOutput(
                success=False,
                error=f"API error fetching form ({get_response.status_code}): {get_response.text}",
            )
        form_data = get_response.json()
        target_field = None
        for field in form_data.get("fields", []):
            if field.get("id") == field_id:
                target_field = field
                break
        if target_field is None:
            return UpdateDropdownMultipleChoiceRankingOutput(
                success=False,
                error=f"Field '{field_id}' not found in form '{form_id}'",
            )
        valid_types = ("dropdown", "multiple_choice", "ranking")
        if target_field.get("type") not in valid_types:
            return UpdateDropdownMultipleChoiceRankingOutput(
                success=False,
                error=f"Field '{field_id}' is of type '{target_field.get('type')}', expected one of {valid_types}",
            )
        properties = target_field.get("properties", {})
        choices = properties.get("choices", [])
        choices.append({"label": choice})
        properties["choices"] = choices
        target_field["properties"] = properties
        form_data.pop("id", None)
        form_data.pop("_links", None)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            put_response = await client.put(
                f"{_BASE_URL}/forms/{form_id}",
                headers=headers,
                json=form_data,
            )
        if put_response.status_code not in (200, 204):
            return UpdateDropdownMultipleChoiceRankingOutput(
                success=False,
                error=f"API error updating form ({put_response.status_code}): {put_response.text}",
            )
        result_data = put_response.json() if put_response.status_code == 200 else form_data
    except httpx.TimeoutException:
        return UpdateDropdownMultipleChoiceRankingOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateDropdownMultipleChoiceRankingOutput(success=False, error=f"Call failed: {exc}")
    return UpdateDropdownMultipleChoiceRankingOutput(
        success=True,
        id=result_data.get("id", form_id),
        title=result_data.get("title"),
        fields=result_data.get("fields", []),
    )

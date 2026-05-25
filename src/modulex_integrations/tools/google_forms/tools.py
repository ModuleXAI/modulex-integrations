"""Google Forms LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_forms.outputs import (
    CreateFormOutput,
    CreateTextQuestionOutput,
    FormInfo,
    FormResponseSummary,
    FormSummary,
    GetFormOutput,
    GetFormResponseOutput,
    ListFormResponsesOutput,
    UpdateFormTitleOutput,
)

__all__ = [
    "create_form",
    "create_text_question",
    "get_form",
    "get_form_response",
    "list_form_responses",
    "update_form_title",
]

_BASE_URL = "https://forms.googleapis.com/v1"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Google Forms API based on auth_type/auth_data."""
    headers: dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _form_summary_from_dict(data: dict[str, Any]) -> FormSummary:
    """Map a Google Forms API form resource into a FormSummary."""
    raw_info = data.get("info") or {}
    info = FormInfo(
        title=raw_info.get("title"),
        documentTitle=raw_info.get("documentTitle"),
        description=raw_info.get("description"),
    )
    return FormSummary(
        formId=data.get("formId"),
        responderUri=data.get("responderUri"),
        revisionId=data.get("revisionId"),
        info=info,
        settings=data.get("settings"),
        items=list(data.get("items") or []),
    )


def _form_response_from_dict(data: dict[str, Any]) -> FormResponseSummary:
    """Map a Google Forms API form-response resource into a FormResponseSummary."""
    return FormResponseSummary(
        responseId=data.get("responseId"),
        formId=data.get("formId"),
        createTime=data.get("createTime"),
        lastSubmittedTime=data.get("lastSubmittedTime"),
        respondentEmail=data.get("respondentEmail"),
        answers=data.get("answers"),
        totalScore=data.get("totalScore"),
    )


# --- Input schemas --------------------------------------------------------


class CreateFormInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    title: str = Field(description="The title of the form which is visible to responders.")
    document_title: str | None = Field(
        default=None,
        description="The title of the document which is visible in Google Drive. Optional.",
    )


class CreateTextQuestionInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    form_id: str = Field(description="Identifier of the Google Form to update.")
    title: str = Field(description="Title of the question.")
    description: str = Field(description="Description of the question.")
    index: int = Field(description="The 0-based index where the item is inserted in the form.")
    paragraph: bool = Field(
        description="If true, the question is a paragraph (multi-line) question. If false, it is a short text question.",
    )


class GetFormInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    form_id: str = Field(description="Identifier of the Google Form to retrieve.")


class GetFormResponseInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    form_id: str = Field(description="Identifier of the Google Form the response belongs to.")
    response_id: str = Field(description="The response ID within the form to retrieve.")


class ListFormResponsesInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    form_id: str = Field(description="Identifier of the Google Form whose responses are listed.")


class UpdateFormTitleInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    form_id: str = Field(description="Identifier of the Google Form to update.")
    title: str = Field(description="The new title of the form which is visible to responders.")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateFormInput)
@serialize_pydantic_return
async def create_form(
    auth_type: str,
    auth_data: dict[str, Any],
    title: str,
    document_title: str | None = None,
) -> CreateFormOutput:
    """Creates a new Google Form with the specified title and optional document title."""
    headers = _get_auth_headers(auth_type, auth_data)
    info: dict[str, Any] = {"title": title}
    if document_title is not None:
        info["documentTitle"] = document_title
    payload = {"info": info}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/forms",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    return CreateFormOutput(
        success=True,
        form=_form_summary_from_dict(data),
    )


@tool(args_schema=CreateTextQuestionInput)
@serialize_pydantic_return
async def create_text_question(
    auth_type: str,
    auth_data: dict[str, Any],
    form_id: str,
    title: str,
    description: str,
    index: int,
    paragraph: bool,
) -> CreateTextQuestionOutput:
    """Creates a new text question (short or paragraph) in an existing Google Form via batchUpdate."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload = {
        "requests": [
            {
                "createItem": {
                    "item": {
                        "title": title,
                        "description": description,
                        "questionItem": {
                            "question": {
                                "textQuestion": {
                                    "paragraph": paragraph,
                                },
                            },
                        },
                    },
                    "location": {"index": index},
                },
            },
        ],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/forms/{form_id}:batchUpdate",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    raw_form = data.get("form")
    form_summary = _form_summary_from_dict(raw_form) if isinstance(raw_form, dict) else None

    return CreateTextQuestionOutput(
        success=True,
        formId=form_id,
        replies=list(data.get("replies") or []),
        form=form_summary,
        writeControl=data.get("writeControl"),
    )


@tool(args_schema=GetFormInput)
@serialize_pydantic_return
async def get_form(
    auth_type: str,
    auth_data: dict[str, Any],
    form_id: str,
) -> GetFormOutput:
    """Gets information about a Google Form, including its title, settings, and items."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/forms/{form_id}",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

    return GetFormOutput(
        success=True,
        form=_form_summary_from_dict(data),
    )


@tool(args_schema=GetFormResponseInput)
@serialize_pydantic_return
async def get_form_response(
    auth_type: str,
    auth_data: dict[str, Any],
    form_id: str,
    response_id: str,
) -> GetFormResponseOutput:
    """Gets a single response from a Google Form by response ID."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/forms/{form_id}/responses/{response_id}",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

    return GetFormResponseOutput(
        success=True,
        response=_form_response_from_dict(data),
    )


@tool(args_schema=ListFormResponsesInput)
@serialize_pydantic_return
async def list_form_responses(
    auth_type: str,
    auth_data: dict[str, Any],
    form_id: str,
) -> ListFormResponsesOutput:
    """Lists all responses submitted to a Google Form."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/forms/{form_id}/responses",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

    raw_responses = data.get("responses") or []
    responses = [_form_response_from_dict(r) for r in raw_responses if isinstance(r, dict)]

    return ListFormResponsesOutput(
        success=True,
        responses=responses,
        nextPageToken=data.get("nextPageToken"),
    )


@tool(args_schema=UpdateFormTitleInput)
@serialize_pydantic_return
async def update_form_title(
    auth_type: str,
    auth_data: dict[str, Any],
    form_id: str,
    title: str,
) -> UpdateFormTitleOutput:
    """Updates the title of an existing Google Form via batchUpdate."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload = {
        "requests": [
            {
                "updateFormInfo": {
                    "info": {"title": title},
                    "updateMask": "title",
                },
            },
        ],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/forms/{form_id}:batchUpdate",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    raw_form = data.get("form")
    form_summary = _form_summary_from_dict(raw_form) if isinstance(raw_form, dict) else None

    return UpdateFormTitleOutput(
        success=True,
        formId=form_id,
        replies=list(data.get("replies") or []),
        form=form_summary,
        writeControl=data.get("writeControl"),
    )

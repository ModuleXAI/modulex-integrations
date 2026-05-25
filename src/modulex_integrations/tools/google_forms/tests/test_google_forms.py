"""Happy-path tests for every google_forms @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_forms import (
    TOOLS,
    create_form,
    create_text_question,
    get_form,
    get_form_response,
    list_form_responses,
    manifest,
    update_form_title,
)
from modulex_integrations.tools.google_forms.outputs import (
    CreateFormOutput,
    CreateTextQuestionOutput,
    GetFormOutput,
    GetFormResponseOutput,
    ListFormResponsesOutput,
    UpdateFormTitleOutput,
)

API = "https://forms.googleapis.com/v1"

# Auth fixture used by every test.
_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_6_actions(self) -> None:
        assert len(manifest.actions) == 6

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_form(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/forms",
        json={
            # TODO: fill in a representative response from
            # https://developers.google.com/forms/api/reference/rest/v1/forms/create
            "formId": "1FAIpQLSeFakeFormId",
            "info": {
                "title": "Customer Feedback",
                "documentTitle": "Customer Feedback (Internal)",
            },
            "revisionId": "00000001",
            "responderUri": "https://docs.google.com/forms/d/e/fake/viewform",
        },
    )

    result_dict = await create_form.ainvoke(
        _args(title="Customer Feedback", document_title="Customer Feedback (Internal)"),
    )

    assert isinstance(result_dict, dict)
    result = CreateFormOutput.model_validate(result_dict)
    assert result.success is True
    assert result.form is not None
    assert result.form.formId == "1FAIpQLSeFakeFormId"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer fake_access_token"


@pytest.mark.asyncio
async def test_create_text_question(httpx_mock):  # type: ignore[no-untyped-def]
    form_id = "1FAIpQLSeFakeFormId"
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/forms/{form_id}:batchUpdate",
        json={
            # TODO: fill in a representative response from
            # https://developers.google.com/forms/api/reference/rest/v1/forms/batchUpdate
            "replies": [{"createItem": {"itemId": "item123", "questionId": ["q123"]}}],
            "writeControl": {"requiredRevisionId": "00000001"},
        },
    )

    result_dict = await create_text_question.ainvoke(
        _args(
            form_id=form_id,
            title="How did you hear about us?",
            description="A short answer is fine.",
            index=0,
            paragraph=False,
        ),
    )

    assert isinstance(result_dict, dict)
    result = CreateTextQuestionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.formId == form_id


@pytest.mark.asyncio
async def test_get_form(httpx_mock):  # type: ignore[no-untyped-def]
    form_id = "1FAIpQLSeFakeFormId"
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/forms/{form_id}",
        json={
            # TODO: fill in a representative response from
            # https://developers.google.com/forms/api/reference/rest/v1/forms/get
            "formId": form_id,
            "info": {"title": "Customer Feedback", "documentTitle": "Customer Feedback (Internal)"},
            "revisionId": "00000001",
            "responderUri": "https://docs.google.com/forms/d/e/fake/viewform",
            "items": [],
        },
    )

    result_dict = await get_form.ainvoke(_args(form_id=form_id))

    assert isinstance(result_dict, dict)
    result = GetFormOutput.model_validate(result_dict)
    assert result.success is True
    assert result.form is not None
    assert result.form.formId == form_id


@pytest.mark.asyncio
async def test_get_form_response(httpx_mock):  # type: ignore[no-untyped-def]
    form_id = "1FAIpQLSeFakeFormId"
    response_id = "ACYDBNh_fake_response_id"
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/forms/{form_id}/responses/{response_id}",
        json={
            # TODO: fill in a representative response from
            # https://developers.google.com/forms/api/reference/rest/v1/forms.responses/get
            "responseId": response_id,
            "formId": form_id,
            "createTime": "2024-01-01T12:00:00Z",
            "lastSubmittedTime": "2024-01-01T12:05:00Z",
            "answers": {},
        },
    )

    result_dict = await get_form_response.ainvoke(_args(form_id=form_id, response_id=response_id))

    assert isinstance(result_dict, dict)
    result = GetFormResponseOutput.model_validate(result_dict)
    assert result.success is True
    assert result.response is not None
    assert result.response.responseId == response_id


@pytest.mark.asyncio
async def test_list_form_responses(httpx_mock):  # type: ignore[no-untyped-def]
    form_id = "1FAIpQLSeFakeFormId"
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/forms/{form_id}/responses",
        json={
            # TODO: fill in a representative response from
            # https://developers.google.com/forms/api/reference/rest/v1/forms.responses/list
            "responses": [
                {
                    "responseId": "ACYDBNh_fake_1",
                    "formId": form_id,
                    "createTime": "2024-01-01T12:00:00Z",
                    "lastSubmittedTime": "2024-01-01T12:05:00Z",
                    "answers": {},
                },
            ],
        },
    )

    result_dict = await list_form_responses.ainvoke(_args(form_id=form_id))

    assert isinstance(result_dict, dict)
    result = ListFormResponsesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.responses) == 1
    assert result.responses[0].responseId == "ACYDBNh_fake_1"


@pytest.mark.asyncio
async def test_update_form_title(httpx_mock):  # type: ignore[no-untyped-def]
    form_id = "1FAIpQLSeFakeFormId"
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/forms/{form_id}:batchUpdate",
        json={
            # TODO: fill in a representative response from
            # https://developers.google.com/forms/api/reference/rest/v1/forms/batchUpdate
            "replies": [{}],
            "writeControl": {"requiredRevisionId": "00000002"},
        },
    )

    result_dict = await update_form_title.ainvoke(_args(form_id=form_id, title="Customer Feedback v2"))

    assert isinstance(result_dict, dict)
    result = UpdateFormTitleOutput.model_validate(result_dict)
    assert result.success is True
    assert result.formId == form_id

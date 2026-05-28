"""Happy-path tests for every typeform @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.typeform import (
    TOOLS,
    create_form,
    create_image,
    delete_form,
    delete_image,
    duplicate_form,
    get_form,
    list_forms,
    list_images,
    list_responses,
    lookup_responses,
    manifest,
    update_dropdown_multiple_choice_ranking,
    update_form_title,
)
from modulex_integrations.tools.typeform.outputs import (
    CreateFormOutput,
    CreateImageOutput,
    DeleteFormOutput,
    DeleteImageOutput,
    DuplicateFormOutput,
    GetFormOutput,
    ListFormsOutput,
    ListImagesOutput,
    ListResponsesOutput,
    LookupResponsesOutput,
    UpdateDropdownMultipleChoiceRankingOutput,
    UpdateFormTitleOutput,
)

API = "https://api.typeform.com"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_12_actions(self) -> None:
        assert len(manifest.actions) == 12

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_list_forms(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/forms?page=1&page_size=10",
        json={
            "total_items": 1,
            "page_count": 1,
            "items": [
                {
                    "id": "abc123",
                    "title": "My Form",
                    "type": "quiz",
                    "last_updated_at": "2024-01-01T00:00:00Z",
                    "_links": {"display": "https://example.typeform.com/to/abc123"},
                }
            ],
        },
    )

    result_dict = await list_forms.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListFormsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.forms) == 1
    assert result.forms[0].id == "abc123"


@pytest.mark.asyncio
async def test_create_form(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/forms",
        json={
            "id": "new123",
            "title": "New Form",
            "type": "form",
            "_links": {"display": "https://example.typeform.com/to/new123"},
        },
        status_code=201,
    )

    result_dict = await create_form.ainvoke(_args(title="New Form"))

    assert isinstance(result_dict, dict)
    result = CreateFormOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "new123"


@pytest.mark.asyncio
async def test_duplicate_form(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/forms/orig123",
        json={
            "id": "orig123",
            "title": "Original",
            "type": "form",
            "fields": [],
            "_links": {"display": "https://example.typeform.com/to/orig123"},
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/forms",
        json={
            "id": "copy456",
            "title": "Original (copy)",
            "type": "form",
            "_links": {"display": "https://example.typeform.com/to/copy456"},
        },
        status_code=201,
    )

    result_dict = await duplicate_form.ainvoke(_args(form_id="orig123"))

    assert isinstance(result_dict, dict)
    result = DuplicateFormOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "copy456"


@pytest.mark.asyncio
async def test_delete_form(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/forms/del123",
        status_code=204,
    )

    result_dict = await delete_form.ainvoke(_args(form_id="del123"))

    assert isinstance(result_dict, dict)
    result = DeleteFormOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "del123"


@pytest.mark.asyncio
async def test_list_images(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/images",
        json=[
            {
                "id": "img001",
                "src": "https://images.typeform.com/img001",
                "file_name": "logo.png",
                "width": 200,
                "height": 100,
            }
        ],
    )

    result_dict = await list_images.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListImagesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.images) == 1
    assert result.images[0].id == "img001"


@pytest.mark.asyncio
async def test_get_form(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/forms/form789",
        json={
            "id": "form789",
            "title": "Survey",
            "type": "form",
            "fields": [{"id": "f1", "type": "short_text", "title": "Name"}],
            "_links": {"display": "https://example.typeform.com/to/form789"},
        },
    )

    result_dict = await get_form.ainvoke(_args(form_id="form789"))

    assert isinstance(result_dict, dict)
    result = GetFormOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "form789"
    assert len(result.fields) == 1


@pytest.mark.asyncio
async def test_list_forms_missing_token() -> None:
    """Failure path: missing access_token returns structured error."""
    result_dict = await list_forms.ainvoke(
        {"auth_type": "oauth2", "auth_data": {}}
    )
    assert isinstance(result_dict, dict)
    result = ListFormsOutput.model_validate(result_dict)
    assert result.success is False
    assert "access token" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_lookup_responses(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/forms/form789/responses?query=hello&page_size=25",
        json={
            "total_items": 1,
            "page_count": 1,
            "items": [
                {
                    "response_id": "resp001",
                    "landed_at": "2024-01-01T00:00:00Z",
                    "submitted_at": "2024-01-01T00:01:00Z",
                    "answers": [{"field": {"id": "f1"}, "type": "text", "text": "hello"}],
                }
            ],
        },
    )

    result_dict = await lookup_responses.ainvoke(_args(form_id="form789", query="hello"))

    assert isinstance(result_dict, dict)
    result = LookupResponsesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 1
    assert result.items[0].response_id == "resp001"


@pytest.mark.asyncio
async def test_list_responses(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/forms/form789/responses?page_size=25&sort=submitted_at%2Cdesc",
        json={
            "total_items": 1,
            "page_count": 1,
            "items": [
                {
                    "response_id": "resp002",
                    "landed_at": "2024-02-01T00:00:00Z",
                    "submitted_at": "2024-02-01T00:02:00Z",
                    "answers": [],
                }
            ],
        },
    )

    result_dict = await list_responses.ainvoke(_args(form_id="form789"))

    assert isinstance(result_dict, dict)
    result = ListResponsesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_update_form_title(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/forms/form789",
        status_code=204,
    )

    result_dict = await update_form_title.ainvoke(_args(form_id="form789", title="Updated Title"))

    assert isinstance(result_dict, dict)
    result = UpdateFormTitleOutput.model_validate(result_dict)
    assert result.success is True
    assert result.title == "Updated Title"


@pytest.mark.asyncio
async def test_delete_image(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/images/img001",
        status_code=204,
    )

    result_dict = await delete_image.ainvoke(_args(image_id="img001"))

    assert isinstance(result_dict, dict)
    result = DeleteImageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "img001"


@pytest.mark.asyncio
async def test_create_image(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/images",
        json={
            "id": "img002",
            "src": "https://images.typeform.com/img002",
            "file_name": "banner.png",
            "width": 800,
            "height": 400,
        },
        status_code=201,
    )

    result_dict = await create_image.ainvoke(
        _args(file_name="banner.png", url="https://example.com/banner.png")
    )

    assert isinstance(result_dict, dict)
    result = CreateImageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "img002"


@pytest.mark.asyncio
async def test_update_dropdown_multiple_choice_ranking(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/forms/form789",
        json={
            "id": "form789",
            "title": "Survey",
            "type": "form",
            "fields": [
                {
                    "id": "field01",
                    "type": "dropdown",
                    "title": "Favorite Color",
                    "properties": {"choices": [{"label": "Red"}, {"label": "Blue"}]},
                }
            ],
            "_links": {"display": "https://example.typeform.com/to/form789"},
        },
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/forms/form789",
        json={
            "id": "form789",
            "title": "Survey",
            "type": "form",
            "fields": [
                {
                    "id": "field01",
                    "type": "dropdown",
                    "title": "Favorite Color",
                    "properties": {"choices": [{"label": "Red"}, {"label": "Blue"}, {"label": "Green"}]},
                }
            ],
        },
    )

    result_dict = await update_dropdown_multiple_choice_ranking.ainvoke(
        _args(form_id="form789", field_id="field01", choice="Green")
    )

    assert isinstance(result_dict, dict)
    result = UpdateDropdownMultipleChoiceRankingOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "form789"

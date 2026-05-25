"""Tests for the Zendesk integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.zendesk import (
    TOOLS,
    add_ticket_tags,
    create_ticket,
    delete_ticket,
    get_article,
    get_macro,
    get_ticket,
    get_user,
    list_articles,
    list_locales,
    list_macros,
    list_ticket_comments,
    list_tickets,
    manifest,
    remove_ticket_tags,
    search_tickets,
    set_custom_fields,
    set_ticket_tags,
    update_ticket,
)
from modulex_integrations.tools.zendesk.outputs import (
    AddTicketTagsOutput,
    CreateTicketOutput,
    DeleteTicketOutput,
    GetArticleOutput,
    GetMacroOutput,
    GetTicketOutput,
    GetUserOutput,
    ListArticlesOutput,
    ListLocalesOutput,
    ListMacrosOutput,
    ListTicketCommentsOutput,
    ListTicketsOutput,
    RemoveTicketTagsOutput,
    SearchTicketsOutput,
    SetCustomFieldsOutput,
    SetTicketTagsOutput,
    UpdateTicketOutput,
)

API = "https://acme.zendesk.com/api/v2"
_CREDS: dict[str, Any] = {
    "subdomain": "acme",
    "email": "agent@x.io",
    "api_key": "fake_token",
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_CREDS, **extra)


class TestManifest:
    def test_manifest_exposes_17_actions(self) -> None:
        assert len(manifest.actions) == 17

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_and_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == [
            "oauth2",
            "api_key",
        ]


@pytest.mark.asyncio
async def test_create_ticket(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/tickets.json",
        status_code=201,
        json={"ticket": {"id": 42, "subject": "Help", "status": "new"}},
    )
    result = CreateTicketOutput.model_validate(
        await create_ticket.ainvoke(
            _args(subject="Help", comment_body="Need help")
        )
    )
    assert result.success is True
    assert result.id == 42


@pytest.mark.asyncio
async def test_update_ticket_no_changes() -> None:
    result = UpdateTicketOutput.model_validate(
        await update_ticket.ainvoke(_args(ticket_id=42))
    )
    assert result.success is False
    assert result.error is not None and "No update" in result.error


@pytest.mark.asyncio
async def test_update_ticket(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/tickets/42.json",
        json={"ticket": {"id": 42, "status": "solved"}},
    )
    result = UpdateTicketOutput.model_validate(
        await update_ticket.ainvoke(_args(ticket_id=42, status="solved"))
    )
    assert result.success is True
    assert result.status == "solved"


@pytest.mark.asyncio
async def test_delete_ticket(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/tickets/42.json", status_code=204
    )
    result = DeleteTicketOutput.model_validate(
        await delete_ticket.ainvoke(_args(ticket_id=42))
    )
    assert result.success is True
    assert result.deleted is True


@pytest.mark.asyncio
async def test_get_ticket(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tickets/42.json",
        json={"ticket": {"id": 42, "subject": "Hi"}},
    )
    result = GetTicketOutput.model_validate(
        await get_ticket.ainvoke(_args(ticket_id=42))
    )
    assert result.success is True
    assert result.result is not None and result.result["id"] == 42


@pytest.mark.asyncio
async def test_get_ticket_404_envelope(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tickets/999.json",
        status_code=404,
        text="not found",
    )
    result = GetTicketOutput.model_validate(
        await get_ticket.ainvoke(_args(ticket_id=999))
    )
    assert result.success is False
    assert result.error is not None and "404" in result.error


@pytest.mark.asyncio
async def test_list_tickets(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tickets.json?per_page=25&sort_order=desc",
        json={"tickets": [{"id": 1}, {"id": 2}], "next_page": None},
    )
    result = ListTicketsOutput.model_validate(
        await list_tickets.ainvoke(_args())
    )
    assert result.success is True
    assert result.count == 2


@pytest.mark.asyncio
async def test_search_tickets(httpx_mock: Any) -> None:
    import re

    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/search\.json\?.*"),
        json={"results": [{"id": 1}], "count": 1},
    )
    result = SearchTicketsOutput.model_validate(
        await search_tickets.ainvoke(_args(query="type:ticket status:open"))
    )
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_add_ticket_tags(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/tickets/42/tags.json",
        json={"tags": ["urgent", "billing"]},
    )
    result = AddTicketTagsOutput.model_validate(
        await add_ticket_tags.ainvoke(_args(ticket_id=42, tags=["urgent"]))
    )
    assert result.success is True
    assert result.added_count == 1


@pytest.mark.asyncio
async def test_set_ticket_tags(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/tickets/42/tags.json",
        json={"tags": ["new"]},
    )
    result = SetTicketTagsOutput.model_validate(
        await set_ticket_tags.ainvoke(_args(ticket_id=42, tags=["new"]))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_remove_ticket_tags(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/tickets/42/tags.json",
        json={"tags": []},
    )
    result = RemoveTicketTagsOutput.model_validate(
        await remove_ticket_tags.ainvoke(_args(ticket_id=42, tags=["urgent"]))
    )
    assert result.success is True
    assert result.removed_count == 1


@pytest.mark.asyncio
async def test_list_ticket_comments(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tickets/42/comments.json?per_page=25&sort_order=asc",
        json={"comments": [{"id": 1, "body": "hi"}]},
    )
    result = ListTicketCommentsOutput.model_validate(
        await list_ticket_comments.ainvoke(_args(ticket_id=42))
    )
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_set_custom_fields(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/tickets/42.json",
        json={"ticket": {"id": 42, "custom_fields": [{"id": 1, "value": "x"}]}},
    )
    result = SetCustomFieldsOutput.model_validate(
        await set_custom_fields.ainvoke(
            _args(ticket_id=42, custom_fields=[{"id": 1, "value": "x"}])
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_user(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/1.json",
        json={"user": {"id": 1, "email": "x@y.io"}},
    )
    result = GetUserOutput.model_validate(
        await get_user.ainvoke(_args(user_id=1))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_locales(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/locales.json",
        json={"locales": [{"locale": "en-US", "id": 1}]},
    )
    result = ListLocalesOutput.model_validate(
        await list_locales.ainvoke(_args())
    )
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_list_macros(httpx_mock: Any) -> None:
    import re

    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/macros\.json\?.*"),
        json={"macros": [{"id": 1, "title": "Greeting"}]},
    )
    result = ListMacrosOutput.model_validate(
        await list_macros.ainvoke(_args(active=True))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_macro(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/macros/1.json",
        json={"macro": {"id": 1, "title": "Greeting"}},
    )
    result = GetMacroOutput.model_validate(
        await get_macro.ainvoke(_args(macro_id=1))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_list_articles_with_locale(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/help_center/en-us/articles.json?per_page=25",
        json={"articles": [{"id": 1, "title": "FAQ"}]},
    )
    result = ListArticlesOutput.model_validate(
        await list_articles.ainvoke(_args(locale="en-us"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_article(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/help_center/articles/1.json",
        json={"article": {"id": 1, "title": "FAQ"}},
    )
    result = GetArticleOutput.model_validate(
        await get_article.ainvoke(_args(article_id=1))
    )
    assert result.success is True

"""Happy-path tests for every freshdesk @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.freshdesk import (
    TOOLS,
    add_note_to_ticket,
    add_ticket_tags,
    assign_ticket_to_agent,
    assign_ticket_to_group,
    close_ticket,
    create_agent,
    create_company,
    create_contact,
    create_message_for_thread,
    create_reply,
    create_solution_article,
    create_thread,
    create_ticket,
    create_ticket_field,
    delete_solution_article,
    forward_ticket,
    get_agent,
    get_canned_response,
    get_contact,
    get_folder_canned_responses,
    get_solution_article,
    get_ticket,
    list_agents,
    list_all_folders,
    list_all_tickets,
    list_category_folders,
    list_companies,
    list_email_configs,
    list_folder_articles,
    list_folder_canned_responses,
    list_roles,
    list_solution_categories,
    list_ticket_conversations,
    list_ticket_fields,
    manifest,
    remove_ticket_tags,
    reply_to_forward,
    search_solution_article,
    set_ticket_priority,
    set_ticket_status,
    set_ticket_tags,
    update_agent,
    update_contact,
    update_solution_article,
    update_ticket,
    update_ticket_field,
)
from modulex_integrations.tools.freshdesk.outputs import (
    AddNoteToTicketOutput,
    AddTicketTagsOutput,
    AssignTicketToAgentOutput,
    AssignTicketToGroupOutput,
    CloseTicketOutput,
    CreateAgentOutput,
    CreateCompanyOutput,
    CreateContactOutput,
    CreateMessageForThreadOutput,
    CreateReplyOutput,
    CreateSolutionArticleOutput,
    CreateThreadOutput,
    CreateTicketFieldOutput,
    CreateTicketOutput,
    DeleteSolutionArticleOutput,
    ForwardTicketOutput,
    GetAgentOutput,
    GetCannedResponseOutput,
    GetContactOutput,
    GetFolderCannedResponsesOutput,
    GetSolutionArticleOutput,
    GetTicketOutput,
    ListAgentsOutput,
    ListAllFoldersOutput,
    ListAllTicketsOutput,
    ListCategoryFoldersOutput,
    ListCompaniesOutput,
    ListEmailConfigsOutput,
    ListFolderArticlesOutput,
    ListFolderCannedResponsesOutput,
    ListRolesOutput,
    ListSolutionCategoriesOutput,
    ListTicketConversationsOutput,
    ListTicketFieldsOutput,
    RemoveTicketTagsOutput,
    ReplyToForwardOutput,
    SearchSolutionArticleOutput,
    SetTicketPriorityOutput,
    SetTicketStatusOutput,
    SetTicketTagsOutput,
    UpdateAgentOutput,
    UpdateContactOutput,
    UpdateSolutionArticleOutput,
    UpdateTicketFieldOutput,
    UpdateTicketOutput,
)

_DOMAIN = "testcompany"
_API_KEY = "fake-api-key"

API = "https://testcompany.freshdesk.com/api/v2"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(domain=_DOMAIN, api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_45_actions(self) -> None:
        assert len(manifest.actions) == 45

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_ticket(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/tickets",
        json={
            # TODO: fill in a representative response shape from upstream API docs
            "id": 1,
            "subject": "Test",
            "status": 2,
            "priority": 1,
        },
        status_code=201,
    )

    result_dict = await create_ticket.ainvoke(
        _args(subject="Test", description="<p>Body</p>", email="user@example.com")
    )

    assert isinstance(result_dict, dict)
    result = CreateTicketOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_ticket(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tickets/1",
        json={
            # TODO: fill in representative response
            "id": 1,
            "subject": "Test",
            "status": 2,
        },
    )

    result_dict = await get_ticket.ainvoke(_args(ticket_id=1))

    assert isinstance(result_dict, dict)
    result = GetTicketOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_all_tickets(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tickets?per_page=100",
        json=[{"id": 1}, {"id": 2}],
    )

    result_dict = await list_all_tickets.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListAllTicketsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 2


@pytest.mark.asyncio
async def test_close_ticket(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/tickets/1",
        json={"id": 1, "status": 5},
    )

    result_dict = await close_ticket.ainvoke(_args(ticket_id=1))

    assert isinstance(result_dict, dict)
    result = CloseTicketOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts",
        json={"id": 100, "name": "John", "email": "john@example.com"},
        status_code=201,
    )

    result_dict = await create_contact.ainvoke(
        _args(email="john@example.com", name="John")
    )

    assert isinstance(result_dict, dict)
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_agents(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/agents?per_page=100",
        json=[{"id": 1, "contact": {"email": "agent@co.com"}}],
    )

    result_dict = await list_agents.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListAgentsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_create_reply(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/tickets/1/reply",
        json={"id": 50, "body": "<p>Reply</p>"},
        status_code=201,
    )

    result_dict = await create_reply.ainvoke(
        _args(ticket_id=1, body="<p>Reply</p>")
    )

    assert isinstance(result_dict, dict)
    result = CreateReplyOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_solution_categories(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/solutions/categories",
        json=[{"id": 1, "name": "FAQ"}],
    )

    result_dict = await list_solution_categories.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListSolutionCategoriesOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_companies(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/companies",
        json=[{"id": 1, "name": "Acme"}],
    )

    result_dict = await list_companies.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListCompaniesOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_ticket(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="PUT", url=f"{API}/tickets/1", json={"id": 1, "subject": "Updated"})
    result_dict = await update_ticket.ainvoke(_args(ticket_id=1, subject="Updated"))
    assert isinstance(result_dict, dict)
    result = UpdateTicketOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_add_note_to_ticket(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/tickets/1/notes", json={"id": 10, "body": "note"}, status_code=201)
    result_dict = await add_note_to_ticket.ainvoke(_args(ticket_id=1, body="note"))
    assert isinstance(result_dict, dict)
    result = AddNoteToTicketOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_add_ticket_tags(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/tickets/1", json={"id": 1, "tags": ["old"]})
    httpx_mock.add_response(method="PUT", url=f"{API}/tickets/1", json={"id": 1, "tags": ["old", "new"]})
    result_dict = await add_ticket_tags.ainvoke(_args(ticket_id=1, tags=["new"]))
    assert isinstance(result_dict, dict)
    result = AddTicketTagsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_remove_ticket_tags(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/tickets/1", json={"id": 1, "tags": ["a", "b"]})
    httpx_mock.add_response(method="PUT", url=f"{API}/tickets/1", json={"id": 1, "tags": ["a"]})
    result_dict = await remove_ticket_tags.ainvoke(_args(ticket_id=1, tags=["b"]))
    assert isinstance(result_dict, dict)
    result = RemoveTicketTagsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_set_ticket_tags(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="PUT", url=f"{API}/tickets/1", json={"id": 1, "tags": ["x"]})
    result_dict = await set_ticket_tags.ainvoke(_args(ticket_id=1, tags=["x"]))
    assert isinstance(result_dict, dict)
    result = SetTicketTagsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_set_ticket_priority(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="PUT", url=f"{API}/tickets/1", json={"id": 1, "priority": 3})
    result_dict = await set_ticket_priority.ainvoke(_args(ticket_id=1, priority=3))
    assert isinstance(result_dict, dict)
    result = SetTicketPriorityOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_set_ticket_status(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="PUT", url=f"{API}/tickets/1", json={"id": 1, "status": 3})
    result_dict = await set_ticket_status.ainvoke(_args(ticket_id=1, status=3))
    assert isinstance(result_dict, dict)
    result = SetTicketStatusOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_assign_ticket_to_agent(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="PUT", url=f"{API}/tickets/1", json={"id": 1, "responder_id": 5})
    result_dict = await assign_ticket_to_agent.ainvoke(_args(ticket_id=1, agent_id=5))
    assert isinstance(result_dict, dict)
    result = AssignTicketToAgentOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_assign_ticket_to_group(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="PUT", url=f"{API}/tickets/1", json={"id": 1, "group_id": 2})
    result_dict = await assign_ticket_to_group.ainvoke(_args(ticket_id=1, group_id=2))
    assert isinstance(result_dict, dict)
    result = AssignTicketToGroupOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/contacts/1", json={"id": 1, "name": "Jane"})
    result_dict = await get_contact.ainvoke(_args(contact_id=1))
    assert isinstance(result_dict, dict)
    result = GetContactOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="PUT", url=f"{API}/contacts/1", json={"id": 1, "name": "Updated"})
    result_dict = await update_contact.ainvoke(_args(contact_id=1, name="Updated"))
    assert isinstance(result_dict, dict)
    result = UpdateContactOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_company(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/companies", json={"id": 1, "name": "Corp"}, status_code=201)
    result_dict = await create_company.ainvoke(_args(name="Corp"))
    assert isinstance(result_dict, dict)
    result = CreateCompanyOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_agent(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/agents", json={"id": 1}, status_code=201)
    result_dict = await create_agent.ainvoke(_args(email="a@b.com", ticket_scope=1))
    assert isinstance(result_dict, dict)
    result = CreateAgentOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_agent(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="PUT", url=f"{API}/agents/1", json={"id": 1})
    result_dict = await update_agent.ainvoke(_args(agent_id=1, ticket_scope=2))
    assert isinstance(result_dict, dict)
    result = UpdateAgentOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_agent(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/agents/1", json={"id": 1})
    result_dict = await get_agent.ainvoke(_args(agent_id=1))
    assert isinstance(result_dict, dict)
    result = GetAgentOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_forward_ticket(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/tickets/1/forward", json={"id": 1}, status_code=201)
    result_dict = await forward_ticket.ainvoke(_args(ticket_id=1, body="<p>FW</p>", to_emails=["x@y.com"]))
    assert isinstance(result_dict, dict)
    result = ForwardTicketOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_reply_to_forward(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/tickets/1/reply_to_forward", json={"id": 1}, status_code=201)
    result_dict = await reply_to_forward.ainvoke(_args(ticket_id=1, body="<p>Re</p>", to_emails=["x@y.com"]))
    assert isinstance(result_dict, dict)
    result = ReplyToForwardOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_thread(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/collaboration/threads", json={"id": "t1"}, status_code=201)
    result_dict = await create_thread.ainvoke(_args(ticket_id=1, type="discussion", email_config_id=10))
    assert isinstance(result_dict, dict)
    result = CreateThreadOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_message_for_thread(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/collaboration/messages", json={"id": "m1"}, status_code=201)
    result_dict = await create_message_for_thread.ainvoke(_args(ticket_id=1, thread_id="t1", body="<p>msg</p>"))
    assert isinstance(result_dict, dict)
    result = CreateMessageForThreadOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_ticket_conversations(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/tickets/1/conversations?per_page=100", json=[{"id": 1}])
    result_dict = await list_ticket_conversations.ainvoke(_args(ticket_id=1))
    assert isinstance(result_dict, dict)
    result = ListTicketConversationsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_ticket_fields(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/ticket_fields?per_page=100", json=[{"id": 1}])
    result_dict = await list_ticket_fields.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListTicketFieldsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_ticket_field(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/admin/ticket_fields", json={"id": 1}, status_code=201)
    result_dict = await create_ticket_field.ainvoke(_args(label="Custom", label_for_customers="Custom", type="custom_text"))
    assert isinstance(result_dict, dict)
    result = CreateTicketFieldOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_ticket_field(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="PUT", url=f"{API}/admin/ticket_fields/1", json={"id": 1})
    result_dict = await update_ticket_field.ainvoke(_args(ticket_field_id="1", label="Renamed"))
    assert isinstance(result_dict, dict)
    result = UpdateTicketFieldOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_solution_article(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/solutions/folders/1/articles", json={"id": 1}, status_code=201)
    result_dict = await create_solution_article.ainvoke(_args(folder_id=1, title="Art", description="<p>body</p>", status=2))
    assert isinstance(result_dict, dict)
    result = CreateSolutionArticleOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_solution_article(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/solutions/articles/1", json={"id": 1, "title": "Art"})
    result_dict = await get_solution_article.ainvoke(_args(article_id=1))
    assert isinstance(result_dict, dict)
    result = GetSolutionArticleOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_solution_article(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="PUT", url=f"{API}/solutions/articles/1", json={"id": 1})
    result_dict = await update_solution_article.ainvoke(_args(article_id=1, title="Updated"))
    assert isinstance(result_dict, dict)
    result = UpdateSolutionArticleOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_solution_article(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="DELETE", url=f"{API}/solutions/articles/1", status_code=204)
    result_dict = await delete_solution_article.ainvoke(_args(article_id=1))
    assert isinstance(result_dict, dict)
    result = DeleteSolutionArticleOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_search_solution_article(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/search/solutions?term=help", json=[{"id": 1}])
    result_dict = await search_solution_article.ainvoke(_args(term="help"))
    assert isinstance(result_dict, dict)
    result = SearchSolutionArticleOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_category_folders(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/solutions/categories/1/folders", json=[{"id": 1}])
    result_dict = await list_category_folders.ainvoke(_args(category_id=1))
    assert isinstance(result_dict, dict)
    result = ListCategoryFoldersOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_folder_articles(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/solutions/folders/1/articles?per_page=100", json=[{"id": 1}])
    result_dict = await list_folder_articles.ainvoke(_args(folder_id=1))
    assert isinstance(result_dict, dict)
    result = ListFolderArticlesOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_all_folders(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/canned_response_folders?per_page=100", json=[{"id": 1}])
    result_dict = await list_all_folders.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListAllFoldersOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_folder_canned_responses(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/canned_response_folders/1", json={"canned_responses": [{"id": 1}]})
    result_dict = await list_folder_canned_responses.ainvoke(_args(canned_response_folder_id=1))
    assert isinstance(result_dict, dict)
    result = ListFolderCannedResponsesOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_canned_response(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/canned_responses/1", json={"id": 1, "title": "Hello"})
    result_dict = await get_canned_response.ainvoke(_args(canned_response_id=1))
    assert isinstance(result_dict, dict)
    result = GetCannedResponseOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_folder_canned_responses(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/canned_response_folders/1/responses?per_page=100", json=[{"id": 1}])
    result_dict = await get_folder_canned_responses.ainvoke(_args(canned_response_folder_id=1))
    assert isinstance(result_dict, dict)
    result = GetFolderCannedResponsesOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_email_configs(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/email_configs", json=[{"id": 1}])
    result_dict = await list_email_configs.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListEmailConfigsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_roles(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/roles", json=[{"id": 1}])
    result_dict = await list_roles.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListRolesOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_ticket_validates_empty_credentials() -> None:
    result_dict = await create_ticket.ainvoke(
        {"domain": "", "api_key": "", "subject": "x", "description": "x", "email": "x@x.com"}
    )
    result = CreateTicketOutput.model_validate(result_dict)
    assert result.success is False
    assert "domain" in (result.error or "").lower()

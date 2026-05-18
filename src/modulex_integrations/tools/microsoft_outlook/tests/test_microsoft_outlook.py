"""Happy-path tests for every microsoft_outlook @tool, plus a manifest sanity check."""
from __future__ import annotations

import re
from typing import Any

import pytest

from modulex_integrations.tools.microsoft_outlook import (
    TOOLS,
    add_label_to_email,
    approve_workflow,
    create_contact,
    create_draft_email,
    create_draft_reply,
    download_attachment,
    find_contacts,
    find_email,
    find_shared_folder_email,
    get_current_user,
    get_message,
    list_contacts,
    list_folders,
    list_important_mail,
    list_labels,
    manifest,
    move_email_to_folder,
    remove_label_from_email,
    reply_to_email,
    send_email,
    update_contact,
)
from modulex_integrations.tools.microsoft_outlook.outputs import (
    AddLabelToEmailOutput,
    ApproveWorkflowOutput,
    CreateContactOutput,
    CreateDraftEmailOutput,
    CreateDraftReplyOutput,
    DownloadAttachmentOutput,
    FindContactsOutput,
    FindEmailOutput,
    FindSharedFolderEmailOutput,
    GetCurrentUserOutput,
    GetMessageOutput,
    ListContactsOutput,
    ListFoldersOutput,
    ListImportantMailOutput,
    ListLabelsOutput,
    MoveEmailToFolderOutput,
    RemoveLabelFromEmailOutput,
    ReplyToEmailOutput,
    SendEmailOutput,
    UpdateContactOutput,
)

API = "https://graph.microsoft.com/v1.0"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_20_actions(self) -> None:
        assert len(manifest.actions) == 20

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_add_label_to_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/messages/msg-1",
        json={
            # TODO: fill in a representative GET /messages/{id} response
            "id": "msg-1",
            "subject": "Hello",
            "categories": [],
        },
    )
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/me/messages/msg-1",
        json={
            # TODO: fill in a representative PATCH /messages/{id} response
            "id": "msg-1",
            "subject": "Hello",
            "categories": ["Important"],
        },
    )

    result_dict = await add_label_to_email.ainvoke(
        _args(message_id="msg-1", label="Important")
    )

    assert isinstance(result_dict, dict)
    result = AddLabelToEmailOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_approve_workflow(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/me/sendMail",
        status_code=202,
        text="",
    )

    result_dict = await approve_workflow.ainvoke(
        _args(
            recipients=["alice@example.com"],
            subject="Approve please",
            resume_url="https://example.com/resume",
            cancel_url="https://example.com/cancel",
        )
    )

    assert isinstance(result_dict, dict)
    result = ApproveWorkflowOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_create_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/me/contacts",
        json={
            # TODO: fill in a representative POST /me/contacts response
            "id": "contact-1",
            "displayName": "Alice Example",
            "givenName": "Alice",
            "surname": "Example",
            "emailAddresses": [{"address": "alice@example.com"}],
            "businessPhones": [],
        },
    )

    result_dict = await create_contact.ainvoke(
        _args(given_name="Alice", surname="Example")
    )

    assert isinstance(result_dict, dict)
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_create_draft_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/me/messages",
        json={
            # TODO: fill in a representative POST /me/messages response
            "id": "draft-1",
            "subject": "Draft",
            "isDraft": True,
            "webLink": "https://outlook.live.com/...",
        },
    )

    result_dict = await create_draft_email.ainvoke(
        _args(subject="Draft", content="Hello")
    )

    assert isinstance(result_dict, dict)
    result = CreateDraftEmailOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_create_draft_reply(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/me/messages/msg-1/createReply",
        json={
            # TODO: fill in a representative createReply response
            "id": "draft-reply-1",
            "subject": "RE: Hello",
            "isDraft": True,
        },
    )

    result_dict = await create_draft_reply.ainvoke(
        _args(message_id="msg-1", comment="Thanks!")
    )

    assert isinstance(result_dict, dict)
    result = CreateDraftReplyOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_download_attachment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/messages/msg-1/attachments/att-1",
        json={
            # TODO: fill in a representative GET /attachments/{id} response
            "name": "report.pdf",
            "contentType": "application/pdf",
            "size": 1024,
            "contentBytes": "ZmFrZQ==",
        },
    )

    result_dict = await download_attachment.ainvoke(
        _args(message_id="msg-1", attachment_id="att-1")
    )

    assert isinstance(result_dict, dict)
    result = DownloadAttachmentOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_find_contacts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/contacts?%24top=50",
        json={
            # TODO: fill in a representative GET /me/contacts response
            "value": [
                {
                    "id": "contact-1",
                    "displayName": "Alice Example",
                    "emailAddresses": [{"address": "alice@example.com"}],
                }
            ]
        },
    )

    result_dict = await find_contacts.ainvoke(
        _args(search_string="Alice")
    )

    assert isinstance(result_dict, dict)
    result = FindContactsOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_find_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(re.escape(f"{API}/me/messages")),
        json={
            # TODO: fill in a representative GET /me/messages response
            "value": [
                {
                    "id": "msg-1",
                    "subject": "Test",
                    "receivedDateTime": "2024-01-01T00:00:00Z",
                }
            ]
        },
    )

    result_dict = await find_email.ainvoke(
        _args(filter="contains(subject, 'Test')")
    )

    assert isinstance(result_dict, dict)
    result = FindEmailOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_find_shared_folder_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(re.escape(f"{API}/users/user-1/mailFolders/folder-1/messages")),
        json={
            # TODO: fill in a representative shared folder /messages response
            "value": [
                {
                    "id": "msg-1",
                    "subject": "Shared",
                    "receivedDateTime": "2024-01-01T00:00:00Z",
                }
            ]
        },
    )

    result_dict = await find_shared_folder_email.ainvoke(
        _args(user_id="user-1", shared_folder_id="folder-1")
    )

    assert isinstance(result_dict, dict)
    result = FindSharedFolderEmailOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_get_current_user(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(re.escape(f"{API}/me") + r"(\?|$)"),
        json={
            # TODO: fill in a representative GET /me response
            "id": "user-1",
            "displayName": "Alice",
            "mail": "alice@example.com",
            "userPrincipalName": "alice@example.com",
        },
    )

    result_dict = await get_current_user.ainvoke(_AUTH)

    assert isinstance(result_dict, dict)
    result = GetCurrentUserOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_get_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(re.escape(f"{API}/me/messages/msg-1")),
        json={
            # TODO: fill in a representative GET /messages/{id} response
            "id": "msg-1",
            "subject": "Hello",
        },
    )

    result_dict = await get_message.ainvoke(
        _args(message_id="msg-1")
    )

    assert isinstance(result_dict, dict)
    result = GetMessageOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_list_contacts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(re.escape(f"{API}/me/contacts")),
        json={
            # TODO: fill in a representative GET /me/contacts response
            "value": [
                {"id": "contact-1", "displayName": "Alice"}
            ]
        },
    )

    result_dict = await list_contacts.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListContactsOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_list_folders(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(re.escape(f"{API}/me/mailFolders") + r"(\?|$)"),
        json={
            # TODO: fill in a representative GET /me/mailFolders response
            "value": [
                {
                    "id": "folder-1",
                    "displayName": "Inbox",
                    "parentFolderId": "root",
                    "totalItemCount": 10,
                    "unreadItemCount": 2,
                }
            ]
        },
    )

    result_dict = await list_folders.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListFoldersOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_list_important_mail(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(re.escape(f"{API}/me/mailFolders/inbox/messages")),
        json={
            # TODO: fill in a representative inbox /messages response
            "value": [
                {
                    "id": "msg-1",
                    "subject": "Important",
                    "sender": {"emailAddress": {"name": "Boss"}},
                    "receivedDateTime": "2024-01-01T00:00:00Z",
                }
            ]
        },
    )

    result_dict = await list_important_mail.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListImportantMailOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_list_labels(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/outlook/masterCategories",
        json={
            # TODO: fill in a representative GET /outlook/masterCategories response
            "value": [
                {"id": "cat-1", "displayName": "Important", "color": "preset0"}
            ]
        },
    )

    result_dict = await list_labels.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListLabelsOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_move_email_to_folder(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/me/messages/msg-1/move",
        json={
            # TODO: fill in a representative POST /messages/{id}/move response
            "id": "msg-1-moved",
            "parentFolderId": "folder-2",
        },
    )

    result_dict = await move_email_to_folder.ainvoke(
        _args(message_id="msg-1", folder_id="folder-2")
    )

    assert isinstance(result_dict, dict)
    result = MoveEmailToFolderOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_remove_label_from_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/messages/msg-1",
        json={
            # TODO: fill in a representative GET /messages/{id} response
            "id": "msg-1",
            "categories": ["Important", "Other"],
        },
    )
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/me/messages/msg-1",
        json={
            # TODO: fill in a representative PATCH /messages/{id} response
            "id": "msg-1",
            "categories": ["Other"],
        },
    )

    result_dict = await remove_label_from_email.ainvoke(
        _args(message_id="msg-1", label="Important")
    )

    assert isinstance(result_dict, dict)
    result = RemoveLabelFromEmailOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_reply_to_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/me/messages/msg-1/reply",
        status_code=202,
        text="",
    )

    result_dict = await reply_to_email.ainvoke(
        _args(message_id="msg-1", comment="Thanks!")
    )

    assert isinstance(result_dict, dict)
    result = ReplyToEmailOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_send_email(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/me/sendMail",
        status_code=202,
        text="",
    )

    result_dict = await send_email.ainvoke(
        _args(
            recipients=["alice@example.com"],
            subject="Hello",
            content="Body",
        )
    )

    assert isinstance(result_dict, dict)
    result = SendEmailOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


@pytest.mark.asyncio
async def test_update_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/me/contacts/contact-1",
        json={
            # TODO: fill in a representative PATCH /me/contacts/{id} response
            "id": "contact-1",
            "displayName": "Alice Example",
            "givenName": "Alice",
            "surname": "Example",
            "emailAddresses": [{"address": "alice@example.com"}],
            "businessPhones": [],
        },
    )

    result_dict = await update_contact.ainvoke(
        _args(contact_id="contact-1", surname="Example")
    )

    assert isinstance(result_dict, dict)
    result = UpdateContactOutput.model_validate(result_dict)
    assert result.success is True
    # TODO: assert representative output fields


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_get_current_user_empty_token() -> None:
    """Empty access_token should short-circuit with success=False."""
    result_dict = await get_current_user.ainvoke(
        {
            "auth_type": "oauth2",
            "auth_data": {"access_token": ""},
        }
    )

    assert isinstance(result_dict, dict)
    result = GetCurrentUserOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None

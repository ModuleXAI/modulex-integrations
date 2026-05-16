"""Tests for the Telegram Bot integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.telegram import (
    TOOLS,
    ban_chat_member,
    create_chat_invite_link,
    delete_message,
    edit_text_message,
    forward_message,
    get_chat,
    get_chat_administrators,
    get_chat_member_count,
    get_me,
    get_updates,
    manifest,
    pin_message,
    send_audio,
    send_document,
    send_photo,
    send_text_message,
    send_video,
    unban_chat_member,
)
from modulex_integrations.tools.telegram.outputs import (
    BanChatMemberOutput,
    CreateChatInviteLinkOutput,
    DeleteMessageOutput,
    EditTextMessageOutput,
    ForwardMessageOutput,
    GetChatAdministratorsOutput,
    GetChatMemberCountOutput,
    GetChatOutput,
    GetMeOutput,
    GetUpdatesOutput,
    PinMessageOutput,
    SendAudioOutput,
    SendDocumentOutput,
    SendPhotoOutput,
    SendTextMessageOutput,
    SendVideoOutput,
    UnbanChatMemberOutput,
)

_TOKEN = "123456:fake_bot_token"
API = f"https://api.telegram.org/bot{_TOKEN}"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_TOKEN, **extra)


def _ok(result: Any) -> dict[str, Any]:
    return {"ok": True, "result": result}


class TestManifest:
    def test_manifest_exposes_seventeen_actions(self) -> None:
        assert len(manifest.actions) == 17

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]

    def test_test_endpoint_url_carries_token_placeholder(self) -> None:
        auth = manifest.auth_schemas[0]
        assert auth.test_endpoint is not None
        assert "{api_key}" in auth.test_endpoint.url


@pytest.mark.asyncio
async def test_send_text_message(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sendMessage",
        json=_ok({"message_id": 7, "chat": {"id": 42}, "date": 1700, "text": "Hello"}),
    )
    result_dict = await send_text_message.ainvoke(
        _args(chat_id="42", text="Hello", parse_mode="Markdown")
    )
    assert isinstance(result_dict, dict)
    result = SendTextMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.result["message_id"] == 7


@pytest.mark.asyncio
async def test_send_text_message_api_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sendMessage",
        json={"ok": False, "description": "Forbidden: bot was blocked by the user"},
    )
    result = SendTextMessageOutput.model_validate(
        await send_text_message.ainvoke(_args(chat_id="42", text="Hi"))
    )
    assert result.success is False
    assert result.error is not None and "blocked" in result.error


@pytest.mark.asyncio
async def test_send_photo_url(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sendPhoto",
        json=_ok({"message_id": 8, "photo": [{"file_id": "pho1"}]}),
    )
    result = SendPhotoOutput.model_validate(
        await send_photo.ainvoke(
            _args(chat_id="42", photo="https://example.com/cat.jpg", caption="kitty")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_send_document(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sendDocument",
        json=_ok({"message_id": 9, "document": {"file_id": "doc1"}}),
    )
    result = SendDocumentOutput.model_validate(
        await send_document.ainvoke(_args(chat_id="42", document="file_id_abc"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_send_video(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sendVideo",
        json=_ok({"message_id": 10, "video": {"file_id": "vid1"}}),
    )
    result = SendVideoOutput.model_validate(
        await send_video.ainvoke(_args(chat_id="42", video="https://x/v.mp4", duration=30))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_send_audio(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sendAudio",
        json=_ok({"message_id": 11, "audio": {"file_id": "aud1"}}),
    )
    result = SendAudioOutput.model_validate(
        await send_audio.ainvoke(
            _args(chat_id="42", audio="file_id_aud", performer="Bach", title="Toccata")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_forward_message(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST", url=f"{API}/forwardMessage", json=_ok({"message_id": 12})
    )
    result = ForwardMessageOutput.model_validate(
        await forward_message.ainvoke(_args(chat_id="42", from_chat_id="99", message_id=7))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_edit_text_message(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/editMessageText",
        json=_ok({"message_id": 7, "text": "Updated"}),
    )
    result = EditTextMessageOutput.model_validate(
        await edit_text_message.ainvoke(_args(chat_id="42", message_id=7, text="Updated"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_message(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="POST", url=f"{API}/deleteMessage", json=_ok(True))
    result = DeleteMessageOutput.model_validate(
        await delete_message.ainvoke(_args(chat_id="42", message_id=7))
    )
    assert result.success is True
    assert result.result is True


@pytest.mark.asyncio
async def test_pin_message(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="POST", url=f"{API}/pinChatMessage", json=_ok(True))
    result = PinMessageOutput.model_validate(
        await pin_message.ainvoke(_args(chat_id="42", message_id=7))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_chat_member_count(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST", url=f"{API}/getChatMemberCount", json=_ok(123)
    )
    result = GetChatMemberCountOutput.model_validate(
        await get_chat_member_count.ainvoke(_args(chat_id="42"))
    )
    assert result.success is True
    assert result.result == 123


@pytest.mark.asyncio
async def test_get_chat_administrators(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/getChatAdministrators",
        json=_ok([{"status": "creator", "user": {"id": 1}}]),
    )
    result = GetChatAdministratorsOutput.model_validate(
        await get_chat_administrators.ainvoke(_args(chat_id="42"))
    )
    assert result.success is True
    assert len(result.result) == 1


@pytest.mark.asyncio
async def test_get_updates(httpx_mock: Any) -> None:
    # get_updates uses GET with query params (not POST body).
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/getUpdates?limit=100&timeout=0",
        json=_ok([{"update_id": 1, "message": {"text": "hi"}}]),
    )
    result = GetUpdatesOutput.model_validate(await get_updates.ainvoke(_args()))
    assert result.success is True
    assert result.result[0]["update_id"] == 1


@pytest.mark.asyncio
async def test_ban_chat_member(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="POST", url=f"{API}/banChatMember", json=_ok(True))
    result = BanChatMemberOutput.model_validate(
        await ban_chat_member.ainvoke(
            _args(chat_id="42", user_id=999, revoke_messages=True)
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_unban_chat_member(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="POST", url=f"{API}/unbanChatMember", json=_ok(True))
    result = UnbanChatMemberOutput.model_validate(
        await unban_chat_member.ainvoke(_args(chat_id="42", user_id=999))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_chat_invite_link(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/createChatInviteLink",
        json=_ok(
            {
                "invite_link": "https://t.me/+abc",
                "creator": {"id": 1},
                "creates_join_request": False,
                "is_primary": False,
                "is_revoked": False,
                "name": "August batch",
                "member_limit": 100,
            }
        ),
    )
    result = CreateChatInviteLinkOutput.model_validate(
        await create_chat_invite_link.ainvoke(
            _args(chat_id="42", name="August batch", member_limit=100)
        )
    )
    assert result.success is True
    assert result.result["invite_link"] == "https://t.me/+abc"


@pytest.mark.asyncio
async def test_get_chat(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/getChat",
        json=_ok({"id": 42, "type": "group", "title": "Team"}),
    )
    result = GetChatOutput.model_validate(
        await get_chat.ainvoke(_args(chat_id="42"))
    )
    assert result.success is True
    assert result.result["title"] == "Team"


@pytest.mark.asyncio
async def test_get_me(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/getMe",
        json=_ok({"id": 1, "is_bot": True, "first_name": "ModuleX Bot"}),
    )
    result = GetMeOutput.model_validate(await get_me.ainvoke(_args()))
    assert result.success is True
    assert result.result["is_bot"] is True


@pytest.mark.asyncio
async def test_empty_key_short_circuits() -> None:
    result = SendTextMessageOutput.model_validate(
        await send_text_message.ainvoke(
            {"api_key": "", "chat_id": "42", "text": "Hi"}
        )
    )
    assert result.success is False
    assert result.error is not None and "Bot token" in result.error

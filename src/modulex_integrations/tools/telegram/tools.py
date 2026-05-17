"""Telegram Bot LangChain ``@tool`` functions.

The Telegram Bot API uniformly:

- Embeds the credential **in the URL**: ``/bot{token}/{method}``.
- Returns ``{"ok": true, "result": ...}`` on success and
  ``{"ok": false, "description": "..."}`` on failure.

A single ``_call`` helper handles the request + ok/result parsing for
every action.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
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

__all__ = [
    "ban_chat_member",
    "create_chat_invite_link",
    "delete_message",
    "edit_text_message",
    "forward_message",
    "get_chat",
    "get_chat_administrators",
    "get_chat_member_count",
    "get_me",
    "get_updates",
    "pin_message",
    "send_audio",
    "send_document",
    "send_photo",
    "send_text_message",
    "send_video",
    "unban_chat_member",
]

_API_BASE = "https://api.telegram.org/bot"
_TIMEOUT = 30.0


def _url(bot_token: str, method: str) -> str:
    return f"{_API_BASE}{bot_token}/{method}"


def _empty_key_error(name: str) -> str:
    return (
        f"Telegram Bot token is empty for {name}. "
        "Please configure a valid credential."
    )


async def _call(
    api_key: str,
    method: str,
    body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> tuple[bool, str | None, Any]:
    """POST (when body) or GET (when params/neither). Returns (ok, error, result)."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            if body is not None:
                response = await client.post(_url(api_key, method), json=body)
            elif params is not None:
                response = await client.get(_url(api_key, method), params=params)
            else:
                response = await client.get(_url(api_key, method))
        payload = response.json()
    except Exception as exc:
        return False, f"Telegram request failed: {exc}", None

    if not isinstance(payload, dict):
        return False, "Telegram API returned a non-object response", None

    if not payload.get("ok"):
        desc = payload.get("description") or "Unknown error"
        return False, f"Telegram API error: {desc}", None

    return True, None, payload.get("result")


def _filter_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


# --- Input schemas ---------------------------------------------------------


class SendTextMessageInput(BaseModel):
    api_key: str = Field(description="Telegram Bot token (provided by credential system)")
    chat_id: str = Field(description="Target chat ID or @username")
    text: str = Field(description="Message text (1-4096 characters)")
    parse_mode: str | None = Field(default=None, description="Markdown/MarkdownV2/HTML")
    disable_notification: bool = Field(default=False, description="Send silently")
    reply_to_message_id: int | None = Field(default=None, description="Reply target")


class SendPhotoInput(BaseModel):
    api_key: str = Field(description="Telegram Bot token (provided by credential system)")
    chat_id: str = Field(description="Target chat ID or @username")
    photo: str = Field(description="Photo file_id or HTTP URL")
    caption: str | None = Field(default=None, description="Caption (0-1024 chars)")
    parse_mode: str | None = Field(default=None, description="Caption parse mode")
    disable_notification: bool = Field(default=False, description="Send silently")
    reply_to_message_id: int | None = Field(default=None, description="Reply target")


class SendDocumentInput(BaseModel):
    api_key: str = Field(description="Telegram Bot token (provided by credential system)")
    chat_id: str = Field(description="Target chat ID or @username")
    document: str = Field(description="Document file_id or HTTP URL")
    caption: str | None = Field(default=None, description="Caption (0-1024 chars)")
    parse_mode: str | None = Field(default=None, description="Caption parse mode")
    disable_notification: bool = Field(default=False, description="Send silently")
    reply_to_message_id: int | None = Field(default=None, description="Reply target")


class SendVideoInput(BaseModel):
    api_key: str = Field(description="Telegram Bot token (provided by credential system)")
    chat_id: str = Field(description="Target chat ID or @username")
    video: str = Field(description="Video file_id or HTTP URL")
    caption: str | None = Field(default=None, description="Caption (0-1024 chars)")
    parse_mode: str | None = Field(default=None, description="Caption parse mode")
    duration: int | None = Field(default=None, description="Duration in seconds")
    disable_notification: bool = Field(default=False, description="Send silently")
    reply_to_message_id: int | None = Field(default=None, description="Reply target")


class SendAudioInput(BaseModel):
    api_key: str = Field(description="Telegram Bot token (provided by credential system)")
    chat_id: str = Field(description="Target chat ID or @username")
    audio: str = Field(description="Audio file_id or HTTP URL")
    caption: str | None = Field(default=None, description="Caption (0-1024 chars)")
    parse_mode: str | None = Field(default=None, description="Caption parse mode")
    duration: int | None = Field(default=None, description="Duration in seconds")
    performer: str | None = Field(default=None, description="Performer of the audio")
    title: str | None = Field(default=None, description="Track name")
    disable_notification: bool = Field(default=False, description="Send silently")


class ForwardMessageInput(BaseModel):
    api_key: str = Field(description="Telegram Bot token (provided by credential system)")
    chat_id: str = Field(description="Destination chat")
    from_chat_id: str = Field(description="Source chat")
    message_id: int = Field(description="Message identifier")
    disable_notification: bool = Field(default=False, description="Send silently")


class EditTextMessageInput(BaseModel):
    api_key: str = Field(description="Telegram Bot token (provided by credential system)")
    chat_id: str = Field(description="Target chat")
    message_id: int = Field(description="Message to edit")
    text: str = Field(description="New text (1-4096 chars)")
    parse_mode: str | None = Field(default=None, description="Parse mode")


class DeleteMessageInput(BaseModel):
    api_key: str = Field(description="Telegram Bot token (provided by credential system)")
    chat_id: str = Field(description="Target chat")
    message_id: int = Field(description="Message to delete")


class PinMessageInput(BaseModel):
    api_key: str = Field(description="Telegram Bot token (provided by credential system)")
    chat_id: str = Field(description="Target chat")
    message_id: int = Field(description="Message to pin")
    disable_notification: bool = Field(default=False, description="Pin silently")


class ChatOnlyInput(BaseModel):
    api_key: str = Field(description="Telegram Bot token (provided by credential system)")
    chat_id: str = Field(description="Target chat ID or @username")


class GetUpdatesInput(BaseModel):
    api_key: str = Field(description="Telegram Bot token (provided by credential system)")
    offset: int | None = Field(default=None, description="First update ID")
    limit: int = Field(default=100, description="Updates to retrieve (1-100)")
    timeout: int = Field(default=0, description="Long-poll timeout (seconds)")


class BanChatMemberInput(BaseModel):
    api_key: str = Field(description="Telegram Bot token (provided by credential system)")
    chat_id: str = Field(description="Target chat")
    user_id: int = Field(description="User to ban")
    until_date: int | None = Field(default=None, description="Unix time to unban (0 = forever)")
    revoke_messages: bool = Field(default=False, description="Delete user's messages")


class UnbanChatMemberInput(BaseModel):
    api_key: str = Field(description="Telegram Bot token (provided by credential system)")
    chat_id: str = Field(description="Target chat")
    user_id: int = Field(description="User to unban")
    only_if_banned: bool = Field(default=True, description="Skip if not banned")


class CreateChatInviteLinkInput(BaseModel):
    api_key: str = Field(description="Telegram Bot token (provided by credential system)")
    chat_id: str = Field(description="Target chat")
    name: str | None = Field(default=None, description="Link name (0-32 chars)")
    expire_date: int | None = Field(default=None, description="Unix expiry timestamp")
    member_limit: int | None = Field(default=None, description="Max members (1-99999)")
    creates_join_request: bool = Field(default=False, description="Require admin approval")


class GetMeInput(BaseModel):
    api_key: str = Field(description="Telegram Bot token (provided by credential system)")


# --- Tools (all share the same _call wrapper) ------------------------------


@tool(args_schema=SendTextMessageInput)
@serialize_pydantic_return
async def send_text_message(
    api_key: str,
    chat_id: str,
    text: str,
    parse_mode: str | None = None,
    disable_notification: bool = False,
    reply_to_message_id: int | None = None,
) -> SendTextMessageOutput:
    """Send a text message to a Telegram chat."""
    if not api_key or not api_key.strip():
        return SendTextMessageOutput(
            success=False, error=_empty_key_error("send_text_message")
        )
    body = _filter_none(
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
        }
    )
    ok, err, result = await _call(api_key, "sendMessage", body=body)
    return SendTextMessageOutput(success=ok, error=err, result=result)


@tool(args_schema=SendPhotoInput)
@serialize_pydantic_return
async def send_photo(
    api_key: str,
    chat_id: str,
    photo: str,
    caption: str | None = None,
    parse_mode: str | None = None,
    disable_notification: bool = False,
    reply_to_message_id: int | None = None,
) -> SendPhotoOutput:
    """Send a photo to a Telegram chat (URL or file_id)."""
    if not api_key or not api_key.strip():
        return SendPhotoOutput(success=False, error=_empty_key_error("send_photo"))
    body = _filter_none(
        {
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
        }
    )
    ok, err, result = await _call(api_key, "sendPhoto", body=body)
    return SendPhotoOutput(success=ok, error=err, result=result)


@tool(args_schema=SendDocumentInput)
@serialize_pydantic_return
async def send_document(
    api_key: str,
    chat_id: str,
    document: str,
    caption: str | None = None,
    parse_mode: str | None = None,
    disable_notification: bool = False,
    reply_to_message_id: int | None = None,
) -> SendDocumentOutput:
    """Send a document/file to a Telegram chat (URL or file_id)."""
    if not api_key or not api_key.strip():
        return SendDocumentOutput(success=False, error=_empty_key_error("send_document"))
    body = _filter_none(
        {
            "chat_id": chat_id,
            "document": document,
            "caption": caption,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
        }
    )
    ok, err, result = await _call(api_key, "sendDocument", body=body)
    return SendDocumentOutput(success=ok, error=err, result=result)


@tool(args_schema=SendVideoInput)
@serialize_pydantic_return
async def send_video(
    api_key: str,
    chat_id: str,
    video: str,
    caption: str | None = None,
    parse_mode: str | None = None,
    duration: int | None = None,
    disable_notification: bool = False,
    reply_to_message_id: int | None = None,
) -> SendVideoOutput:
    """Send a video to a Telegram chat (URL or file_id)."""
    if not api_key or not api_key.strip():
        return SendVideoOutput(success=False, error=_empty_key_error("send_video"))
    body = _filter_none(
        {
            "chat_id": chat_id,
            "video": video,
            "caption": caption,
            "parse_mode": parse_mode,
            "duration": duration,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
        }
    )
    ok, err, result = await _call(api_key, "sendVideo", body=body)
    return SendVideoOutput(success=ok, error=err, result=result)


@tool(args_schema=SendAudioInput)
@serialize_pydantic_return
async def send_audio(
    api_key: str,
    chat_id: str,
    audio: str,
    caption: str | None = None,
    parse_mode: str | None = None,
    duration: int | None = None,
    performer: str | None = None,
    title: str | None = None,
    disable_notification: bool = False,
) -> SendAudioOutput:
    """Send an audio file to a Telegram chat (URL or file_id)."""
    if not api_key or not api_key.strip():
        return SendAudioOutput(success=False, error=_empty_key_error("send_audio"))
    body = _filter_none(
        {
            "chat_id": chat_id,
            "audio": audio,
            "caption": caption,
            "parse_mode": parse_mode,
            "duration": duration,
            "performer": performer,
            "title": title,
            "disable_notification": disable_notification,
        }
    )
    ok, err, result = await _call(api_key, "sendAudio", body=body)
    return SendAudioOutput(success=ok, error=err, result=result)


@tool(args_schema=ForwardMessageInput)
@serialize_pydantic_return
async def forward_message(
    api_key: str,
    chat_id: str,
    from_chat_id: str,
    message_id: int,
    disable_notification: bool = False,
) -> ForwardMessageOutput:
    """Forward a message from one chat to another."""
    if not api_key or not api_key.strip():
        return ForwardMessageOutput(
            success=False, error=_empty_key_error("forward_message")
        )
    body = {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
        "disable_notification": disable_notification,
    }
    ok, err, result = await _call(api_key, "forwardMessage", body=body)
    return ForwardMessageOutput(success=ok, error=err, result=result)


@tool(args_schema=EditTextMessageInput)
@serialize_pydantic_return
async def edit_text_message(
    api_key: str,
    chat_id: str,
    message_id: int,
    text: str,
    parse_mode: str | None = None,
) -> EditTextMessageOutput:
    """Edit a text message previously sent by the bot."""
    if not api_key or not api_key.strip():
        return EditTextMessageOutput(
            success=False, error=_empty_key_error("edit_text_message")
        )
    body = _filter_none(
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
        }
    )
    ok, err, result = await _call(api_key, "editMessageText", body=body)
    return EditTextMessageOutput(success=ok, error=err, result=result)


@tool(args_schema=DeleteMessageInput)
@serialize_pydantic_return
async def delete_message(
    api_key: str, chat_id: str, message_id: int
) -> DeleteMessageOutput:
    """Delete a message from a chat."""
    if not api_key or not api_key.strip():
        return DeleteMessageOutput(
            success=False, error=_empty_key_error("delete_message")
        )
    ok, err, result = await _call(
        api_key, "deleteMessage", body={"chat_id": chat_id, "message_id": message_id}
    )
    return DeleteMessageOutput(success=ok, error=err, result=result)


@tool(args_schema=PinMessageInput)
@serialize_pydantic_return
async def pin_message(
    api_key: str, chat_id: str, message_id: int, disable_notification: bool = False
) -> PinMessageOutput:
    """Pin a message in a chat."""
    if not api_key or not api_key.strip():
        return PinMessageOutput(success=False, error=_empty_key_error("pin_message"))
    body = {
        "chat_id": chat_id,
        "message_id": message_id,
        "disable_notification": disable_notification,
    }
    ok, err, result = await _call(api_key, "pinChatMessage", body=body)
    return PinMessageOutput(success=ok, error=err, result=result)


@tool(args_schema=ChatOnlyInput)
@serialize_pydantic_return
async def get_chat_member_count(api_key: str, chat_id: str) -> GetChatMemberCountOutput:
    """Get the number of members in a chat."""
    if not api_key or not api_key.strip():
        return GetChatMemberCountOutput(
            success=False, error=_empty_key_error("get_chat_member_count")
        )
    ok, err, result = await _call(
        api_key, "getChatMemberCount", body={"chat_id": chat_id}
    )
    return GetChatMemberCountOutput(success=ok, error=err, result=result)


@tool(args_schema=ChatOnlyInput)
@serialize_pydantic_return
async def get_chat_administrators(
    api_key: str, chat_id: str
) -> GetChatAdministratorsOutput:
    """Get a list of administrators in a chat with their permissions."""
    if not api_key or not api_key.strip():
        return GetChatAdministratorsOutput(
            success=False, error=_empty_key_error("get_chat_administrators")
        )
    ok, err, result = await _call(
        api_key, "getChatAdministrators", body={"chat_id": chat_id}
    )
    return GetChatAdministratorsOutput(success=ok, error=err, result=result)


@tool(args_schema=GetUpdatesInput)
@serialize_pydantic_return
async def get_updates(
    api_key: str,
    offset: int | None = None,
    limit: int = 100,
    timeout: int = 0,
) -> GetUpdatesOutput:
    """Get incoming updates via long polling."""
    if not api_key or not api_key.strip():
        return GetUpdatesOutput(success=False, error=_empty_key_error("get_updates"))
    params = _filter_none({"offset": offset, "limit": limit, "timeout": timeout})
    ok, err, result = await _call(api_key, "getUpdates", params=params)
    return GetUpdatesOutput(success=ok, error=err, result=result)


@tool(args_schema=BanChatMemberInput)
@serialize_pydantic_return
async def ban_chat_member(
    api_key: str,
    chat_id: str,
    user_id: int,
    until_date: int | None = None,
    revoke_messages: bool = False,
) -> BanChatMemberOutput:
    """Ban a user from a chat."""
    if not api_key or not api_key.strip():
        return BanChatMemberOutput(
            success=False, error=_empty_key_error("ban_chat_member")
        )
    body = _filter_none(
        {
            "chat_id": chat_id,
            "user_id": user_id,
            "until_date": until_date,
            "revoke_messages": revoke_messages,
        }
    )
    ok, err, result = await _call(api_key, "banChatMember", body=body)
    return BanChatMemberOutput(success=ok, error=err, result=result)


@tool(args_schema=UnbanChatMemberInput)
@serialize_pydantic_return
async def unban_chat_member(
    api_key: str, chat_id: str, user_id: int, only_if_banned: bool = True
) -> UnbanChatMemberOutput:
    """Unban a previously-banned user."""
    if not api_key or not api_key.strip():
        return UnbanChatMemberOutput(
            success=False, error=_empty_key_error("unban_chat_member")
        )
    body = {
        "chat_id": chat_id,
        "user_id": user_id,
        "only_if_banned": only_if_banned,
    }
    ok, err, result = await _call(api_key, "unbanChatMember", body=body)
    return UnbanChatMemberOutput(success=ok, error=err, result=result)


@tool(args_schema=CreateChatInviteLinkInput)
@serialize_pydantic_return
async def create_chat_invite_link(
    api_key: str,
    chat_id: str,
    name: str | None = None,
    expire_date: int | None = None,
    member_limit: int | None = None,
    creates_join_request: bool = False,
) -> CreateChatInviteLinkOutput:
    """Create an additional invite link for a chat."""
    if not api_key or not api_key.strip():
        return CreateChatInviteLinkOutput(
            success=False, error=_empty_key_error("create_chat_invite_link")
        )
    body = _filter_none(
        {
            "chat_id": chat_id,
            "name": name,
            "expire_date": expire_date,
            "member_limit": member_limit,
            "creates_join_request": creates_join_request,
        }
    )
    ok, err, result = await _call(api_key, "createChatInviteLink", body=body)
    return CreateChatInviteLinkOutput(success=ok, error=err, result=result)


@tool(args_schema=ChatOnlyInput)
@serialize_pydantic_return
async def get_chat(api_key: str, chat_id: str) -> GetChatOutput:
    """Get up-to-date information about a chat."""
    if not api_key or not api_key.strip():
        return GetChatOutput(success=False, error=_empty_key_error("get_chat"))
    ok, err, result = await _call(api_key, "getChat", body={"chat_id": chat_id})
    return GetChatOutput(success=ok, error=err, result=result)


@tool(args_schema=GetMeInput)
@serialize_pydantic_return
async def get_me(api_key: str) -> GetMeOutput:
    """Get basic information about the bot."""
    if not api_key or not api_key.strip():
        return GetMeOutput(success=False, error=_empty_key_error("get_me"))
    ok, err, result = await _call(api_key, "getMe")
    return GetMeOutput(success=ok, error=err, result=result)

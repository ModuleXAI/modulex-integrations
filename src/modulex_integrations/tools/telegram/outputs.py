"""Pydantic response models for the Telegram Bot integration.

The Telegram Bot API uniformly returns ``{"ok": true, "result": ...}``
or ``{"ok": false, "description": "..."}``. We surface the ``result``
verbatim under ``result`` (preserving its variable shape per action)
plus the standard ``success`` + ``error`` envelope.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
    "BanChatMemberOutput",
    "CreateChatInviteLinkOutput",
    "DeleteMessageOutput",
    "EditTextMessageOutput",
    "ForwardMessageOutput",
    "GetChatAdministratorsOutput",
    "GetChatMemberCountOutput",
    "GetChatOutput",
    "GetMeOutput",
    "GetUpdatesOutput",
    "PinMessageOutput",
    "SendAudioOutput",
    "SendDocumentOutput",
    "SendPhotoOutput",
    "SendTextMessageOutput",
    "SendVideoOutput",
    "UnbanChatMemberOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None
    result: Any = None


class SendTextMessageOutput(_Base):
    pass


class SendPhotoOutput(_Base):
    pass


class SendDocumentOutput(_Base):
    pass


class SendVideoOutput(_Base):
    pass


class SendAudioOutput(_Base):
    pass


class ForwardMessageOutput(_Base):
    pass


class EditTextMessageOutput(_Base):
    pass


class DeleteMessageOutput(_Base):
    pass


class PinMessageOutput(_Base):
    pass


class GetChatMemberCountOutput(_Base):
    pass


class GetChatAdministratorsOutput(_Base):
    pass


class GetUpdatesOutput(_Base):
    pass


class BanChatMemberOutput(_Base):
    pass


class UnbanChatMemberOutput(_Base):
    pass


class CreateChatInviteLinkOutput(_Base):
    pass


class GetChatOutput(_Base):
    pass


class GetMeOutput(_Base):
    pass

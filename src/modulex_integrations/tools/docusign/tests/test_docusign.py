"""Happy-path tests for every docusign @tool, plus a manifest sanity check."""
from __future__ import annotations

import re
from typing import Any

import pytest

from modulex_integrations.tools.docusign import (
    TOOLS,
    create_draft,
    create_envelope,
    create_envelope_from_file,
    create_recipient_view,
    create_signature_request,
    download_documents,
    get_envelope,
    list_documents,
    list_envelopes,
    list_recipients,
    manifest,
    send_envelope,
    void_envelope,
)
from modulex_integrations.tools.docusign.outputs import (
    CreateDraftOutput,
    CreateEnvelopeFromFileOutput,
    CreateEnvelopeOutput,
    CreateRecipientViewOutput,
    CreateSignatureRequestOutput,
    DownloadDocumentsOutput,
    GetEnvelopeOutput,
    ListDocumentsOutput,
    ListEnvelopesOutput,
    ListRecipientsOutput,
    SendEnvelopeOutput,
    VoidEnvelopeOutput,
)

USERINFO_URL = "https://account.docusign.com/oauth/userinfo"
BASE = "https://demo.docusign.net/restapi/v2.1/accounts/acct123"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}

_USERINFO_RESPONSE: dict[str, Any] = {
    "accounts": [
        {
            "account_id": "acct123",
            "base_uri": "https://demo.docusign.net",
            "is_default": True,
            "account_name": "Test Account",
        },
    ],
}


def _args(**extra: Any) -> dict[str, Any]:
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
async def test_create_signature_request(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=USERINFO_URL, json=_USERINFO_RESPONSE)
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/envelopes",
        json={
            # TODO: fill in a representative response shape from the DocuSign API docs
            "envelopeId": "env-001",
            "status": "sent",
            "statusDateTime": "2026-05-18T00:00:00Z",
            "uri": "/envelopes/env-001",
        },
    )

    result_dict = await create_signature_request.ainvoke(
        _args(account="acct123", template="tmpl-001", email_subject="Please sign")
    )

    assert isinstance(result_dict, dict)
    result = CreateSignatureRequestOutput.model_validate(result_dict)
    assert result.success is True
    assert result.envelope_id == "env-001"


@pytest.mark.asyncio
async def test_create_draft(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=USERINFO_URL, json=_USERINFO_RESPONSE)
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/envelopes",
        json={
            # TODO: fill in a representative response shape from the DocuSign API docs
            "envelopeId": "env-002",
            "status": "created",
            "statusDateTime": "2026-05-18T00:00:00Z",
            "uri": "/envelopes/env-002",
        },
    )

    result_dict = await create_draft.ainvoke(
        _args(account="acct123", template="tmpl-001", email_subject="Draft envelope")
    )

    assert isinstance(result_dict, dict)
    result = CreateDraftOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "created"


@pytest.mark.asyncio
async def test_create_envelope(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=USERINFO_URL, json=_USERINFO_RESPONSE)
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/envelopes",
        json={
            # TODO: fill in a representative response shape from the DocuSign API docs
            "envelopeId": "env-003",
            "status": "sent",
            "statusDateTime": "2026-05-18T00:00:00Z",
            "uri": "/envelopes/env-003",
        },
    )

    result_dict = await create_envelope.ainvoke(
        _args(
            account="acct123",
            envelope_definition_json='{"emailSubject":"Sign","status":"sent","documents":[],"recipients":{}}',
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateEnvelopeOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_envelope_from_file(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/doc.pdf",
        content=b"%PDF-fake-content",
    )
    httpx_mock.add_response(method="GET", url=USERINFO_URL, json=_USERINFO_RESPONSE)
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/envelopes",
        json={
            # TODO: fill in a representative response shape from the DocuSign API docs
            "envelopeId": "env-004",
            "status": "sent",
            "statusDateTime": "2026-05-18T00:00:00Z",
            "uri": "/envelopes/env-004",
        },
    )

    result_dict = await create_envelope_from_file.ainvoke(
        _args(
            account="acct123",
            file_url="https://example.com/doc.pdf",
            email_subject="Sign this",
            signer_name="Jane Doe",
            signer_email="jane@example.com",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateEnvelopeFromFileOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_recipient_view(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=USERINFO_URL, json=_USERINFO_RESPONSE)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/envelopes/env-001/recipients",
        json={
            "signers": [
                {
                    "recipientId": "1",
                    "name": "Jane Doe",
                    "email": "jane@example.com",
                    "clientUserId": "client-001",
                    "status": "sent",
                },
            ],
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/envelopes/env-001/views/recipient",
        json={
            # TODO: fill in a representative response shape from the DocuSign API docs
            "url": "https://demo.docusign.net/Signing/...",
        },
    )

    result_dict = await create_recipient_view.ainvoke(
        _args(
            account="acct123",
            envelope_id="env-001",
            return_url="https://example.com/done",
            recipient_id="1",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateRecipientViewOutput.model_validate(result_dict)
    assert result.success is True
    assert result.url is not None


@pytest.mark.asyncio
async def test_get_envelope(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=USERINFO_URL, json=_USERINFO_RESPONSE)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/envelopes/env-001",
        json={
            # TODO: fill in a representative response shape from the DocuSign API docs
            "envelopeId": "env-001",
            "status": "sent",
            "emailSubject": "Please sign",
            "statusDateTime": "2026-05-18T00:00:00Z",
        },
    )

    result_dict = await get_envelope.ainvoke(
        _args(account="acct123", envelope_id="env-001")
    )

    assert isinstance(result_dict, dict)
    result = GetEnvelopeOutput.model_validate(result_dict)
    assert result.success is True
    assert result.envelope is not None
    assert result.envelope.envelope_id == "env-001"


@pytest.mark.asyncio
async def test_list_envelopes(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=USERINFO_URL, json=_USERINFO_RESPONSE)
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{re.escape(BASE)}/envelopes\?.*"),
        json={
            # TODO: fill in a representative response shape from the DocuSign API docs
            "envelopes": [
                {
                    "envelopeId": "env-001",
                    "status": "sent",
                    "emailSubject": "Please sign",
                },
            ],
            "resultSetSize": "1",
            "totalSetSize": "1",
        },
    )

    result_dict = await list_envelopes.ainvoke(
        _args(account="acct123")
    )

    assert isinstance(result_dict, dict)
    result = ListEnvelopesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.envelopes) == 1


@pytest.mark.asyncio
async def test_list_documents(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=USERINFO_URL, json=_USERINFO_RESPONSE)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/envelopes/env-001/documents",
        json={
            # TODO: fill in a representative response shape from the DocuSign API docs
            "envelopeDocuments": [
                {
                    "documentId": "1",
                    "name": "Contract.pdf",
                    "type": "content",
                    "uri": "/documents/1",
                    "order": "1",
                    "pages": "3",
                },
            ],
        },
    )

    result_dict = await list_documents.ainvoke(
        _args(account="acct123", envelope_id="env-001")
    )

    assert isinstance(result_dict, dict)
    result = ListDocumentsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.documents) == 1
    assert result.documents[0].name == "Contract.pdf"


@pytest.mark.asyncio
async def test_list_recipients(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=USERINFO_URL, json=_USERINFO_RESPONSE)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/envelopes/env-001/recipients",
        json={
            # TODO: fill in a representative response shape from the DocuSign API docs
            "signers": [
                {
                    "recipientId": "1",
                    "name": "Jane Doe",
                    "email": "jane@example.com",
                    "status": "sent",
                },
            ],
            "carbonCopies": [],
            "agents": [],
        },
    )

    result_dict = await list_recipients.ainvoke(
        _args(account="acct123", envelope_id="env-001")
    )

    assert isinstance(result_dict, dict)
    result = ListRecipientsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.signers) == 1


@pytest.mark.asyncio
async def test_send_envelope(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=USERINFO_URL, json=_USERINFO_RESPONSE)
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE}/envelopes/env-002",
        json={
            # TODO: fill in a representative response shape from the DocuSign API docs
            "envelopeId": "env-002",
        },
    )

    result_dict = await send_envelope.ainvoke(
        _args(account="acct123", envelope_id="env-002")
    )

    assert isinstance(result_dict, dict)
    result = SendEnvelopeOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "sent"


@pytest.mark.asyncio
async def test_download_documents(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=USERINFO_URL, json=_USERINFO_RESPONSE)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/envelopes/env-001",
        json={
            "envelopeId": "env-001",
            "documentsUri": "/envelopes/env-001/documents",
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/envelopes/env-001/documents/combined",
        content=b"%PDF-fake-combined-content",
        headers={"content-type": "application/pdf"},
    )

    result_dict = await download_documents.ainvoke(
        _args(
            account="acct123",
            envelope_id="env-001",
            download_type="combined",
            filename="combined.pdf",
        )
    )

    assert isinstance(result_dict, dict)
    result = DownloadDocumentsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.content_base64 is not None
    assert result.filename == "combined.pdf"


@pytest.mark.asyncio
async def test_void_envelope(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=USERINFO_URL, json=_USERINFO_RESPONSE)
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE}/envelopes/env-003",
        json={
            # TODO: fill in a representative response shape from the DocuSign API docs
            "envelopeId": "env-003",
        },
    )

    result_dict = await void_envelope.ainvoke(
        _args(
            account="acct123",
            envelope_id="env-003",
            voided_reason="Cancelled by requester",
        )
    )

    assert isinstance(result_dict, dict)
    result = VoidEnvelopeOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "voided"


@pytest.mark.asyncio
async def test_create_signature_request_missing_token():  # type: ignore[no-untyped-def]
    """Failure path: missing access token returns error without HTTP call."""
    result_dict = await create_signature_request.ainvoke(
        {
            "auth_type": "oauth2",
            "auth_data": {},
            "account": "acct123",
            "template": "tmpl-001",
            "email_subject": "Please sign",
        }
    )

    assert isinstance(result_dict, dict)
    result = CreateSignatureRequestOutput.model_validate(result_dict)
    assert result.success is False
    assert "token" in (result.error or "").lower()

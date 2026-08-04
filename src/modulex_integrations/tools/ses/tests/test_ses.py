"""Happy-path tests for every ses @tool, plus failure-path,
empty-credential, and SigV4 request-shape checks."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pytest

from modulex_integrations.tools.ses import (
    TOOLS,
    create_configuration_set,
    create_email_identity,
    create_template,
    delete_email_identity,
    delete_suppressed_destination,
    delete_template,
    get_account,
    get_email_identity,
    get_suppressed_destination,
    get_template,
    list_identities,
    list_suppressed_destinations,
    list_templates,
    manifest,
    put_suppressed_destination,
    send_bulk_email,
    send_custom_verification_email,
    send_email,
    send_templated_email,
    update_template,
)
from modulex_integrations.tools.ses.outputs import (
    CreateConfigurationSetOutput,
    CreateEmailIdentityOutput,
    CreateTemplateOutput,
    DeleteEmailIdentityOutput,
    DeleteSuppressedDestinationOutput,
    DeleteTemplateOutput,
    GetAccountOutput,
    GetEmailIdentityOutput,
    GetSuppressedDestinationOutput,
    GetTemplateOutput,
    ListIdentitiesOutput,
    ListSuppressedDestinationsOutput,
    ListTemplatesOutput,
    PutSuppressedDestinationOutput,
    SendBulkEmailOutput,
    SendCustomVerificationEmailOutput,
    SendEmailOutput,
    SendTemplatedEmailOutput,
    UpdateTemplateOutput,
)
from modulex_integrations.tools.ses.tools import _auth_headers

API = "https://email.us-east-1.amazonaws.com"

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "access_key_id": "AKIAIOSFODNN7EXAMPLE",
        "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity ---------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_19_actions(self) -> None:
        assert len(manifest.actions) == 19

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}

    def test_every_action_accepts_a_region(self) -> None:
        for action in manifest.actions:
            assert action.parameters["region"].default == "us-east-1"


# --- Happy-path tests --------------------------------------------------------


@pytest.mark.asyncio
async def test_send_email(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/email/outbound-emails",
        json={"MessageId": "0100018f-1111-2222"},
    )

    result_dict = await send_email.ainvoke(
        _args(
            from_address="sender@example.com",
            to_addresses=["a@example.com", "b@example.com"],
            subject="Hello",
            body_html="<h1>Hi</h1>",
            cc_addresses=["cc@example.com"],
            reply_to_addresses=["reply@example.com"],
            configuration_set_name="tracked",
        )
    )

    assert isinstance(result_dict, dict)
    result = SendEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message_id == "0100018f-1111-2222"

    sent = httpx_mock.get_requests()[0]
    body = json.loads(sent.content)
    assert body["FromEmailAddress"] == "sender@example.com"
    assert body["Destination"]["ToAddresses"] == ["a@example.com", "b@example.com"]
    assert body["Destination"]["CcAddresses"] == ["cc@example.com"]
    assert body["Content"]["Simple"]["Subject"]["Data"] == "Hello"
    assert body["Content"]["Simple"]["Body"]["Html"]["Data"] == "<h1>Hi</h1>"
    assert body["ReplyToAddresses"] == ["reply@example.com"]
    assert body["ConfigurationSetName"] == "tracked"


@pytest.mark.asyncio
async def test_send_templated_email(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/email/outbound-emails",
        json={"MessageId": "0100018f-3333"},
    )

    result_dict = await send_templated_email.ainvoke(
        _args(
            from_address="sender@example.com",
            to_addresses=["a@example.com"],
            template_name="welcome",
            template_data={"name": "Ada"},
        )
    )

    result = SendTemplatedEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message_id == "0100018f-3333"

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["Content"]["Template"]["TemplateName"] == "welcome"
    assert json.loads(body["Content"]["Template"]["TemplateData"]) == {"name": "Ada"}


@pytest.mark.asyncio
async def test_send_bulk_email(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/email/outbound-bulk-emails",
        json={
            "BulkEmailEntryResults": [
                {"Status": "SUCCESS", "MessageId": "id-1"},
                {"Status": "MESSAGE_REJECTED", "Error": "rejected"},
            ]
        },
    )

    result_dict = await send_bulk_email.ainvoke(
        _args(
            from_address="sender@example.com",
            template_name="newsletter",
            destinations=[
                {"to_addresses": ["one@example.com"], "template_data": {"name": "One"}},
                {"toAddresses": "two@example.com"},
            ],
            default_template_data={"company": "Acme"},
        )
    )

    result = SendBulkEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.success_count == 1
    assert result.failure_count == 1
    assert result.results[0].message_id == "id-1"

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["DefaultContent"]["Template"]["TemplateName"] == "newsletter"
    entries = body["BulkEmailEntries"]
    assert entries[0]["Destination"]["ToAddresses"] == ["one@example.com"]
    assert json.loads(
        entries[0]["ReplacementEmailContent"]["ReplacementTemplate"]["ReplacementTemplateData"]
    ) == {"name": "One"}
    assert entries[1]["Destination"]["ToAddresses"] == ["two@example.com"]
    assert json.loads(
        entries[1]["ReplacementEmailContent"]["ReplacementTemplate"]["ReplacementTemplateData"]
    ) == {"company": "Acme"}


@pytest.mark.asyncio
async def test_list_identities(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/email/identities?PageSize=10",
        json={
            "EmailIdentities": [
                {
                    "IdentityName": "example.com",
                    "IdentityType": "DOMAIN",
                    "SendingEnabled": True,
                    "VerificationStatus": "SUCCESS",
                }
            ],
            "NextToken": "next-1",
        },
    )

    result_dict = await list_identities.ainvoke(_args(page_size=10))

    result = ListIdentitiesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.identities[0].identity_name == "example.com"
    assert result.identities[0].verification_status == "SUCCESS"
    assert result.next_token == "next-1"


@pytest.mark.asyncio
async def test_get_account(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/email/account",
        json={
            "SendingEnabled": True,
            "ProductionAccessEnabled": False,
            "EnforcementStatus": "HEALTHY",
            "DedicatedIpAutoWarmupEnabled": True,
            "SendQuota": {
                "Max24HourSend": 50000.0,
                "MaxSendRate": 14.0,
                "SentLast24Hours": 120.0,
            },
            "SuppressionAttributes": {"SuppressedReasons": ["BOUNCE", "COMPLAINT"]},
        },
    )

    result_dict = await get_account.ainvoke(_args())

    result = GetAccountOutput.model_validate(result_dict)
    assert result.success is True
    assert result.sending_enabled is True
    assert result.max_24_hour_send == 50000.0
    assert result.max_send_rate == 14.0
    assert result.sent_last_24_hours == 120.0
    assert result.production_access_enabled is False
    assert result.enforcement_status == "HEALTHY"
    assert result.suppressed_reasons == ["BOUNCE", "COMPLAINT"]


@pytest.mark.asyncio
async def test_create_template(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/v2/email/templates", status_code=200)

    result_dict = await create_template.ainvoke(
        _args(
            template_name="welcome",
            subject_part="Hello, {{name}}!",
            html_part="<h1>Hello, {{name}}!</h1>",
            text_part="Hello, {{name}}!",
        )
    )

    result = CreateTemplateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.template_name == "welcome"

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["TemplateName"] == "welcome"
    assert body["TemplateContent"] == {
        "Subject": "Hello, {{name}}!",
        "Html": "<h1>Hello, {{name}}!</h1>",
        "Text": "Hello, {{name}}!",
    }


@pytest.mark.asyncio
async def test_get_template(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/email/templates/welcome",
        json={
            "TemplateName": "welcome",
            "TemplateContent": {
                "Subject": "Hello, {{name}}!",
                "Html": "<h1>Hi</h1>",
                "Text": "Hi",
            },
        },
    )

    result_dict = await get_template.ainvoke(_args(template_name="welcome"))

    result = GetTemplateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.template_name == "welcome"
    assert result.subject_part == "Hello, {{name}}!"
    assert result.html_part == "<h1>Hi</h1>"
    assert result.text_part == "Hi"


@pytest.mark.asyncio
async def test_list_templates(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/email/templates?PageSize=5",
        json={
            "TemplatesMetadata": [
                {"TemplateName": "welcome", "CreatedTimestamp": 1735689600.0}
            ],
            "NextToken": "next-2",
        },
    )

    result_dict = await list_templates.ainvoke(_args(page_size=5))

    result = ListTemplatesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.templates[0].template_name == "welcome"
    assert result.templates[0].created_timestamp == 1735689600.0
    assert result.next_token == "next-2"


@pytest.mark.asyncio
async def test_delete_template(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/v2/email/templates/welcome", status_code=200
    )

    result_dict = await delete_template.ainvoke(_args(template_name="welcome"))

    result = DeleteTemplateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.template_name == "welcome"
    assert result.message is not None


@pytest.mark.asyncio
async def test_update_template(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT", url=f"{API}/v2/email/templates/welcome", status_code=200
    )

    result_dict = await update_template.ainvoke(
        _args(template_name="welcome", subject_part="Hi again", html_part="<p>Hi</p>")
    )

    result = UpdateTemplateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.template_name == "welcome"

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body == {"TemplateContent": {"Subject": "Hi again", "Html": "<p>Hi</p>"}}


@pytest.mark.asyncio
async def test_send_custom_verification_email(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/email/outbound-custom-verification-emails",
        json={"MessageId": "verify-1"},
    )

    result_dict = await send_custom_verification_email.ainvoke(
        _args(email_address="new@example.com", template_name="verify-template")
    )

    result = SendCustomVerificationEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message_id == "verify-1"

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body == {"EmailAddress": "new@example.com", "TemplateName": "verify-template"}


@pytest.mark.asyncio
async def test_create_email_identity(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/email/identities",
        json={
            "IdentityType": "DOMAIN",
            "VerifiedForSendingStatus": False,
            "DkimAttributes": {
                "SigningEnabled": True,
                "Status": "PENDING",
                "Tokens": ["token1", "token2"],
                "SigningAttributesOrigin": "AWS_SES",
            },
        },
    )

    result_dict = await create_email_identity.ainvoke(
        _args(
            email_identity="example.com",
            dkim_signing_attributes={"domainSigningSelector": "selector1"},
            tags=[{"key": "team", "value": "growth"}],
            configuration_set_name="default-set",
        )
    )

    result = CreateEmailIdentityOutput.model_validate(result_dict)
    assert result.success is True
    assert result.identity_type == "DOMAIN"
    assert result.dkim_attributes is not None
    assert result.dkim_attributes.tokens == ["token1", "token2"]

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["EmailIdentity"] == "example.com"
    assert body["DkimSigningAttributes"] == {"DomainSigningSelector": "selector1"}
    assert body["Tags"] == [{"Key": "team", "Value": "growth"}]
    assert body["ConfigurationSetName"] == "default-set"


@pytest.mark.asyncio
async def test_get_email_identity(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/email/identities/example.com",
        json={
            "IdentityType": "DOMAIN",
            "VerifiedForSendingStatus": True,
            "VerificationStatus": "SUCCESS",
            "FeedbackForwardingStatus": True,
            "ConfigurationSetName": "default-set",
            "DkimAttributes": {"SigningEnabled": True, "Status": "SUCCESS", "Tokens": ["t1"]},
            "MailFromAttributes": {
                "MailFromDomain": "mail.example.com",
                "MailFromDomainStatus": "SUCCESS",
                "BehaviorOnMxFailure": "USE_DEFAULT_VALUE",
            },
            "Policies": {"policy1": "{}"},
            "Tags": [{"Key": "team", "Value": "growth"}],
            "VerificationInfo": {"LastCheckedTimestamp": 1735689600.0},
        },
    )

    result_dict = await get_email_identity.ainvoke(_args(email_identity="example.com"))

    result = GetEmailIdentityOutput.model_validate(result_dict)
    assert result.success is True
    assert result.verification_status == "SUCCESS"
    assert result.mail_from_attributes is not None
    assert result.mail_from_attributes.mail_from_domain == "mail.example.com"
    assert result.policies == {"policy1": "{}"}
    assert result.tags[0].key == "team"
    assert result.verification_info is not None
    assert result.verification_info.last_checked_timestamp == 1735689600.0


@pytest.mark.asyncio
async def test_delete_email_identity(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/v2/email/identities/example.com", status_code=200
    )

    result_dict = await delete_email_identity.ainvoke(_args(email_identity="example.com"))

    result = DeleteEmailIdentityOutput.model_validate(result_dict)
    assert result.success is True
    assert result.email_identity == "example.com"


@pytest.mark.asyncio
async def test_put_suppressed_destination(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT", url=f"{API}/v2/email/suppression/addresses", status_code=200
    )

    result_dict = await put_suppressed_destination.ainvoke(
        _args(email_address="bounced@example.com", reason="complaint")
    )

    result = PutSuppressedDestinationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.reason == "COMPLAINT"

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body == {"EmailAddress": "bounced@example.com", "Reason": "COMPLAINT"}


@pytest.mark.asyncio
async def test_get_suppressed_destination(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/email/suppression/addresses/bounced%40example.com",
        json={
            "SuppressedDestination": {
                "EmailAddress": "bounced@example.com",
                "Reason": "BOUNCE",
                "LastUpdateTime": 1735689600.0,
                "Attributes": {"MessageId": "msg-1", "FeedbackId": "fb-1"},
            }
        },
    )

    result_dict = await get_suppressed_destination.ainvoke(
        _args(email_address="bounced@example.com")
    )

    result = GetSuppressedDestinationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.email_address == "bounced@example.com"
    assert result.reason == "BOUNCE"
    assert result.last_update_time == 1735689600.0
    assert result.message_id == "msg-1"
    assert result.feedback_id == "fb-1"


@pytest.mark.asyncio
async def test_list_suppressed_destinations(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}/v2/email/suppression/addresses"
            "?Reason=BOUNCE&Reason=COMPLAINT&StartDate=2026-01-01T00%3A00%3A00Z&PageSize=25"
        ),
        json={
            "SuppressedDestinationSummaries": [
                {
                    "EmailAddress": "bounced@example.com",
                    "Reason": "BOUNCE",
                    "LastUpdateTime": 1735689600.0,
                }
            ],
            "NextToken": "next-3",
        },
    )

    result_dict = await list_suppressed_destinations.ainvoke(
        _args(
            reasons=["bounce", "complaint"],
            start_date="2026-01-01T00:00:00Z",
            page_size=25,
        )
    )

    result = ListSuppressedDestinationsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.destinations[0].email_address == "bounced@example.com"
    assert result.next_token == "next-3"


@pytest.mark.asyncio
async def test_delete_suppressed_destination(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/v2/email/suppression/addresses/bounced%40example.com",
        status_code=200,
    )

    result_dict = await delete_suppressed_destination.ainvoke(
        _args(email_address="bounced@example.com")
    )

    result = DeleteSuppressedDestinationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.email_address == "bounced@example.com"


@pytest.mark.asyncio
async def test_create_configuration_set(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=f"{API}/v2/email/configuration-sets", status_code=200
    )

    result_dict = await create_configuration_set.ainvoke(
        _args(
            configuration_set_name="marketing",
            custom_redirect_domain="links.example.com",
            https_policy="require",
            tls_policy="require",
            sending_pool_name="pool-1",
            reputation_metrics_enabled=True,
            sending_enabled=True,
            suppressed_reasons=["bounce"],
            tags=[{"key": "team", "value": "growth"}],
        )
    )

    result = CreateConfigurationSetOutput.model_validate(result_dict)
    assert result.success is True
    assert result.configuration_set_name == "marketing"

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["ConfigurationSetName"] == "marketing"
    assert body["TrackingOptions"] == {
        "CustomRedirectDomain": "links.example.com",
        "HttpsPolicy": "REQUIRE",
    }
    assert body["DeliveryOptions"] == {"TlsPolicy": "REQUIRE", "SendingPoolName": "pool-1"}
    assert body["ReputationOptions"] == {"ReputationMetricsEnabled": True}
    assert body["SendingOptions"] == {"SendingEnabled": True}
    assert body["SuppressionOptions"] == {"SuppressedReasons": ["BOUNCE"]}
    assert body["Tags"] == [{"Key": "team", "Value": "growth"}]


# --- Request signing / regional routing --------------------------------------


@pytest.mark.asyncio
async def test_request_is_sigv4_signed_for_region(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://email.eu-west-1.amazonaws.com/v2/email/account",
        json={"SendingEnabled": True},
    )

    result_dict = await get_account.ainvoke(_args(region="eu-west-1"))

    assert GetAccountOutput.model_validate(result_dict).success is True

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["host"] == "email.eu-west-1.amazonaws.com"
    assert "x-amz-date" in sent.headers
    authorization = sent.headers["authorization"]
    assert authorization.startswith("AWS4-HMAC-SHA256 Credential=AKIAIOSFODNN7EXAMPLE/")
    assert "/eu-west-1/ses/aws4_request" in authorization
    assert "SignedHeaders=content-type;host;x-amz-date" in authorization
    assert "Signature=" in authorization


# --- Failure paths -----------------------------------------------------------


@pytest.mark.asyncio
async def test_non_2xx_returns_success_false(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/email/outbound-emails",
        status_code=400,
        json={"message": "Email address is not verified."},
    )

    result_dict = await send_email.ainvoke(
        _args(
            from_address="unverified@example.com",
            to_addresses=["a@example.com"],
            subject="Hello",
            body_text="Hi",
        )
    )

    result = SendEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "400" in result.error
    assert result.message_id is None


@pytest.mark.asyncio
async def test_missing_credentials_short_circuits(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    result_dict = await list_identities.ainvoke({"auth_type": "custom", "auth_data": {}})

    result = ListIdentitiesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "credentials" in result.error.lower()
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_bulk_send_without_destinations(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await send_bulk_email.ainvoke(
        _args(from_address="sender@example.com", template_name="newsletter", destinations=[])
    )

    result = SendBulkEmailOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_invalid_region_short_circuits(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    for bad_region in ("us-east-1.attacker.example/", "us-east-1@attacker.example"):
        result_dict = await get_account.ainvoke(_args(region=bad_region))

        result = GetAccountOutput.model_validate(result_dict)
        assert result.success is False
        assert "region" in (result.error or "").lower()

    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_region_is_lowercased(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url="https://email.eu-west-1.amazonaws.com/v2/email/account",
        json={"SendingEnabled": True},
    )

    result_dict = await get_account.ainvoke(_args(region="EU-West-1"))

    assert GetAccountOutput.model_validate(result_dict).success is True
    sent = httpx_mock.get_requests()[0]
    assert sent.headers["host"] == "email.eu-west-1.amazonaws.com"
    assert "/eu-west-1/ses/aws4_request" in sent.headers["authorization"]


# --- SigV4 differential check against botocore ------------------------------
#
# Mocked transports accept any Authorization header, so nothing above would
# notice a subtly wrong canonical request — every call would simply 403 in
# production. This pins the signer to the reference implementation.

botocore_auth = pytest.importorskip("botocore.auth", reason="botocore is not installed")
from botocore.awsrequest import AWSRequest  # type: ignore[import-untyped]  # noqa: E402
from botocore.credentials import Credentials  # type: ignore[import-untyped]  # noqa: E402

_AK = "AKIAIOSFODNN7EXAMPLE"
_SK = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"


@pytest.mark.parametrize(
    ("method", "path", "canonical_query", "payload"),
    [
        ("GET", "/v2/email/account", "", ""),
        ("GET", "/v2/email/identities", "NextToken=abc%3Ddef&PageSize=10", ""),
        ("POST", "/v2/email/outbound-emails", "", '{"FromEmailAddress":"a@b.co"}'),
        ("POST", "/v2/email/outbound-emails", "", '{"Subject":"héllo — ünicode"}'),
        ("PUT", "/v2/email/templates/my-template", "", "{}"),
        ("DELETE", "/v2/email/suppression/addresses/user%40example.com", "", ""),
        ("GET", "/v2/email/identities/a~b.c/dkim", "", ""),
    ],
)
def test_sigv4_authorization_matches_botocore(
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    path: str,
    canonical_query: str,
    payload: str,
) -> None:
    """Our hand-rolled signer must agree with botocore byte for byte."""
    region = "us-east-1"
    host = f"email.{region}.amazonaws.com"

    ours = _auth_headers(method, host, region, path, canonical_query, payload, _AK, _SK)

    # Freeze botocore to the exact instant our signer stamped, so the only
    # thing that can differ is the signature computation itself.
    stamped = datetime.strptime(ours["X-Amz-Date"], "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    monkeypatch.setattr(botocore_auth, "get_current_datetime", lambda: stamped)

    url = f"https://{host}{path}"
    if canonical_query:
        url = f"{url}?{canonical_query}"
    request = AWSRequest(
        method=method,
        url=url,
        data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    botocore_auth.SigV4Auth(Credentials(_AK, _SK), "ses", region).add_auth(request)

    assert ours["Authorization"] == request.headers["Authorization"]

"""Happy-path tests for every google_ads @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_ads import (
    TOOLS,
    add_contact_to_list_by_email,
    create_ad_group_report,
    create_ad_report,
    create_campaign_report,
    create_customer_list,
    create_customer_report,
    create_report,
    generate_keyword_ideas,
    list_account_id_options,
    manifest,
    send_offline_conversion,
)
from modulex_integrations.tools.google_ads.outputs import (
    AddContactToListByEmailOutput,
    CreateAdGroupReportOutput,
    CreateAdReportOutput,
    CreateCampaignReportOutput,
    CreateCustomerListOutput,
    CreateCustomerReportOutput,
    CreateReportOutput,
    GenerateKeywordIdeasOutput,
    ListAccountIdOptionsOutput,
    SendOfflineConversionOutput,
)

API = "https://googleads.googleapis.com"
V = "v21"
KW_V = "v22"
ACCOUNT = "1234567890"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {
        "access_token": "fake_access_token",
        "developer_token": "fake_developer_token",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_10_actions(self) -> None:
        assert len(manifest.actions) == 10

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}

    def test_tools_is_tuple(self) -> None:
        assert isinstance(TOOLS, tuple)


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_add_contact_to_list_by_email(httpx_mock):  # type: ignore[no-untyped-def]
    job_resource = (
        f"customers/{ACCOUNT}/offlineUserDataJobs/9876543210"
    )
    # Step 1: create job
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{V}/customers/{ACCOUNT}/offlineUserDataJobs:create",
        json={"resourceName": job_resource},
    )
    # Step 2: addOperations
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{V}/{job_resource}:addOperations",
        json={},
    )
    # Step 3: run
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{V}/{job_resource}:run",
        json={"name": f"customers/{ACCOUNT}/operations/123"},
    )

    result_dict = await add_contact_to_list_by_email.ainvoke(
        _args(
            account_id=ACCOUNT,
            user_list_id="55555",
            contact_email="alice@example.com",
        )
    )
    assert isinstance(result_dict, dict)
    result = AddContactToListByEmailOutput.model_validate(result_dict)
    assert result.success is True
    assert result.offline_user_data_job_resource_name == job_resource


@pytest.mark.asyncio
async def test_create_ad_group_report(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{V}/customers/{ACCOUNT}/googleAds:search",
        json={
            "results": [
                # TODO: fill in a representative response shape from the upstream API docs
                {"adGroup": {"id": "111", "name": "Sample AG"}},
            ],
            "fieldMask": "ad_group.id,ad_group.name",
            "requestId": "abc",
        },
    )

    result_dict = await create_ad_group_report.ainvoke(
        _args(account_id=ACCOUNT, fields=["id", "name"])
    )
    assert isinstance(result_dict, dict)
    result = CreateAdGroupReportOutput.model_validate(result_dict)
    assert result.success is True
    assert result.query is not None and "FROM ad_group" in result.query
    assert len(result.results) == 1


@pytest.mark.asyncio
async def test_create_ad_report(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{V}/customers/{ACCOUNT}/googleAds:search",
        json={
            "results": [
                # TODO: fill in a representative response shape from the upstream API docs
                {"adGroupAd": {"ad": {"id": "222"}}}
            ],
        },
    )

    result_dict = await create_ad_report.ainvoke(
        _args(account_id=ACCOUNT, fields=["ad.id"])
    )
    result = CreateAdReportOutput.model_validate(result_dict)
    assert result.success is True
    assert "FROM ad_group_ad" in (result.query or "")


@pytest.mark.asyncio
async def test_create_campaign_report(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{V}/customers/{ACCOUNT}/googleAds:search",
        json={
            "results": [
                # TODO: fill in a representative response shape from the upstream API docs
                {"campaign": {"id": "333", "name": "Holiday Sale"}}
            ],
        },
    )

    result_dict = await create_campaign_report.ainvoke(
        _args(account_id=ACCOUNT, fields=["id", "name"])
    )
    result = CreateCampaignReportOutput.model_validate(result_dict)
    assert result.success is True
    assert "FROM campaign" in (result.query or "")


@pytest.mark.asyncio
async def test_create_customer_list(httpx_mock):  # type: ignore[no-untyped-def]
    resource_name = f"customers/{ACCOUNT}/userLists/444"
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{V}/customers/{ACCOUNT}/userLists:mutate",
        json={
            "results": [
                # TODO: fill in a representative response shape from the upstream API docs
                {"resourceName": resource_name}
            ]
        },
    )

    result_dict = await create_customer_list.ainvoke(
        _args(
            account_id=ACCOUNT,
            name="VIP Customers",
            list_type="crmBasedUserList",
            list_type_data={"uploadKeyType": "CONTACT_INFO"},
        )
    )
    result = CreateCustomerListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "444"
    assert result.resource_name == resource_name


@pytest.mark.asyncio
async def test_create_customer_report(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{V}/customers/{ACCOUNT}/googleAds:search",
        json={
            "results": [
                # TODO: fill in a representative response shape from the upstream API docs
                {"customer": {"id": ACCOUNT, "descriptiveName": "My Acct"}}
            ],
        },
    )

    result_dict = await create_customer_report.ainvoke(
        _args(account_id=ACCOUNT, fields=["id", "descriptive_name"])
    )
    result = CreateCustomerReportOutput.model_validate(result_dict)
    assert result.success is True
    assert "FROM customer" in (result.query or "")


@pytest.mark.asyncio
async def test_create_report(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{V}/customers/{ACCOUNT}/googleAds:search",
        json={
            "results": [
                # TODO: fill in a representative response shape from the upstream API docs
                {"campaign": {"id": "999"}}
            ],
        },
    )

    result_dict = await create_report.ainvoke(
        _args(account_id=ACCOUNT, resource="campaign", fields=["id"])
    )
    result = CreateReportOutput.model_validate(result_dict)
    assert result.success is True
    assert "FROM campaign" in (result.query or "")


@pytest.mark.asyncio
async def test_generate_keyword_ideas(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{KW_V}/customers/{ACCOUNT}:generateKeywordIdeas",
        json={
            "results": [
                # TODO: fill in a representative response shape from the upstream API docs
                {"text": "modulex", "keywordIdeaMetrics": {"avgMonthlySearches": "1000"}}
            ],
            "totalSize": 1,
        },
    )

    result_dict = await generate_keyword_ideas.ainvoke(
        _args(
            account_id=ACCOUNT,
            customer_client_id=ACCOUNT,
            additional_fields={
                "language": "languageConstants/1000",
                "geoTargetConstants": ["geoTargetConstants/2840"],
                "keywordSeed": {"keywords": ["modulex"]},
            },
        )
    )
    result = GenerateKeywordIdeasOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total_size == 1


@pytest.mark.asyncio
async def test_list_account_id_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/{V}/customers:listAccessibleCustomers",
        json={
            "resourceNames": [
                # TODO: fill in a representative response shape from the upstream API docs
                f"customers/{ACCOUNT}",
                "customers/9876543210",
            ]
        },
    )

    result_dict = await list_account_id_options.ainvoke(_args())
    result = ListAccountIdOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.customers) == 2
    assert result.customers[0].customer_id == ACCOUNT


@pytest.mark.asyncio
async def test_send_offline_conversion(httpx_mock):  # type: ignore[no-untyped-def]
    resource_name = f"customers/{ACCOUNT}/conversionActions/777"
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{V}/customers/{ACCOUNT}/conversionActions:mutate",
        json={
            "results": [
                # TODO: fill in a representative response shape from the upstream API docs
                {"resourceName": resource_name}
            ]
        },
    )

    result_dict = await send_offline_conversion.ainvoke(
        _args(account_id=ACCOUNT, name="Form Submit", type="WEBPAGE")
    )
    result = SendOfflineConversionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "777"


# --- Failure-path tests (Pattern B) ----------------------------------------


@pytest.mark.asyncio
async def test_create_report_returns_error_on_missing_developer_token() -> None:
    """Missing developer_token short-circuits before any HTTP call."""
    no_dev_token = {
        "auth_type": "oauth2",
        "auth_data": {"access_token": "x"},
    }
    args = dict(no_dev_token, account_id=ACCOUNT, resource="campaign", fields=["id"])
    result_dict = await create_report.ainvoke(args)
    result = CreateReportOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "developer token" in result.error.lower()


@pytest.mark.asyncio
async def test_create_report_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{V}/customers/{ACCOUNT}/googleAds:search",
        status_code=400,
        text="bad request",
    )

    result_dict = await create_report.ainvoke(
        _args(account_id=ACCOUNT, resource="campaign", fields=["id"])
    )
    result = CreateReportOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "400" in result.error

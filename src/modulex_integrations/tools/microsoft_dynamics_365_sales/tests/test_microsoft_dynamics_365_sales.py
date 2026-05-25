"""Happy-path tests for every microsoft_dynamics_365_sales @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.microsoft_dynamics_365_sales import (
    TOOLS,
    create_appointment,
    create_custom_entity,
    find_contact,
    get_account,
    list_accounts,
    list_appointment_categories,
    list_appointment_category_options,
    list_appointments,
    list_solution_id_options,
    manifest,
    search_accounts,
    update_appointment,
)
from modulex_integrations.tools.microsoft_dynamics_365_sales.outputs import (
    CreateAppointmentOutput,
    CreateCustomEntityOutput,
    FindContactOutput,
    GetAccountOutput,
    ListAccountsOutput,
    ListAppointmentCategoriesOutput,
    ListAppointmentCategoryOptionsOutput,
    ListAppointmentsOutput,
    ListSolutionIdOptionsOutput,
    SearchAccountsOutput,
    UpdateAppointmentOutput,
)

API = "https://org12345.crm.dynamics.com/api/data/v9.2"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token", "api_url": "org12345.crm.dynamics.com"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_11_actions(self) -> None:
        assert len(manifest.actions) == 11

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_appointment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/systemusers?%24filter=internalemailaddress+eq+%27user%40example.com%27&%24select=systemuserid",
        json={"value": [{"systemuserid": "user-guid-123"}]},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/appointments",
        json={
            "activityid": "appt-guid-456",
            "subject": "Meeting",
            # TODO: fill in a representative response shape from the upstream API docs
        },
        status_code=201,
    )

    result_dict = await create_appointment.ainvoke(
        _args(
            subject="Meeting",
            scheduledstart="2026-03-01T10:00:00Z",
            scheduledend="2026-03-01T11:00:00Z",
            regarding_account_id="acct-guid-789",
            required_attendee_email="user@example.com",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateAppointmentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.appointment_id == "appt-guid-456"


@pytest.mark.asyncio
async def test_create_custom_entity(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/solutions(sol-123)?%24select=uniquename%2Cpublisherid",
        json={"uniquename": "MySolution", "publisherid": {"customizationprefix": "new"}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/EntityDefinitions",
        status_code=204,
        headers={"odata-entityid": f"{API}/EntityDefinitions(entity-guid-001)"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/EntityDefinitions(entity-guid-001)",
        json={
            "LogicalName": "bankaccount",
            # TODO: fill in a representative response shape from the upstream API docs
        },
    )

    result_dict = await create_custom_entity.ainvoke(
        _args(
            solution_id="sol-123",
            display_name="Bank Account",
            primary_attribute="Account Name",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateCustomEntityOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_find_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/contacts?%24filter=contains%28fullname%2C%27Smith%27%29",
        json={
            "value": [
                {"contactid": "contact-001", "fullname": "John Smith"},
                # TODO: fill in a representative response shape from the upstream API docs
            ]
        },
    )

    result_dict = await find_contact.ainvoke(_args(name="Smith"))

    assert isinstance(result_dict, dict)
    result = FindContactOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.contacts) >= 1


@pytest.mark.asyncio
async def test_get_account(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/accounts(acct-guid-001)",
        json={
            "accountid": "acct-guid-001",
            "name": "Contoso Ltd",
            # TODO: fill in a representative response shape from the upstream API docs
        },
    )

    result_dict = await get_account.ainvoke(_args(account_id="acct-guid-001"))

    assert isinstance(result_dict, dict)
    result = GetAccountOutput.model_validate(result_dict)
    assert result.success is True
    assert result.account is not None


@pytest.mark.asyncio
async def test_list_accounts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/accounts?%24select=accountid%2Cname%2Ctelephone1%2Cemailaddress1%2C_primarycontactid_value",
        json={
            "value": [
                {"accountid": "acct-001", "name": "Contoso"},
                # TODO: fill in a representative response shape from the upstream API docs
            ]
        },
    )

    result_dict = await list_accounts.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListAccountsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.accounts) >= 1


@pytest.mark.asyncio
async def test_list_appointment_categories(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/EntityDefinitions(LogicalName='appointment')/Attributes(LogicalName='category')/Microsoft.Dynamics.CRM.PicklistAttributeMetadata?%24expand=OptionSet",
        json={
            "OptionSet": {
                "Options": [
                    {"Value": 1, "Label": {"UserLocalizedLabel": {"Label": "Meeting"}}},
                    {"Value": 2, "Label": {"UserLocalizedLabel": {"Label": "Call"}}},
                ]
            }
        },
    )

    result_dict = await list_appointment_categories.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListAppointmentCategoriesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.category_type == "picklist"


@pytest.mark.asyncio
async def test_list_appointment_category_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/EntityDefinitions(LogicalName='appointment')/Attributes(LogicalName='category')/Microsoft.Dynamics.CRM.PicklistAttributeMetadata?%24expand=OptionSet",
        json={
            "OptionSet": {
                "Options": [
                    {"Value": 1, "Label": {"UserLocalizedLabel": {"Label": "Meeting"}}},
                ]
            }
        },
    )

    result_dict = await list_appointment_category_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListAppointmentCategoryOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.options) >= 1


@pytest.mark.asyncio
async def test_list_appointments(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/appointments?%24orderby=scheduledstart+desc",
        json={
            "value": [
                {"activityid": "appt-001", "subject": "Team Standup"},
                # TODO: fill in a representative response shape from the upstream API docs
            ]
        },
    )

    result_dict = await list_appointments.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListAppointmentsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.appointments) >= 1


@pytest.mark.asyncio
async def test_list_solution_id_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/solutions?%24select=solutionid%2Cfriendlyname%2Cuniquename",
        json={
            "value": [
                {"solutionid": "sol-001", "friendlyname": "Default Solution", "uniquename": "Default"},
            ]
        },
    )

    result_dict = await list_solution_id_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListSolutionIdOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.solutions) >= 1


@pytest.mark.asyncio
async def test_search_accounts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/accounts?%24filter=contains%28name%2C%27Contoso%27%29&%24select=accountid%2Cname%2Ctelephone1%2Cemailaddress1",
        json={
            "value": [
                {"accountid": "acct-001", "name": "Contoso Ltd"},
                # TODO: fill in a representative response shape from the upstream API docs
            ]
        },
    )

    result_dict = await search_accounts.ainvoke(_args(search_term="Contoso"))

    assert isinstance(result_dict, dict)
    result = SearchAccountsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.accounts) >= 1


@pytest.mark.asyncio
async def test_update_appointment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/appointments(appt-guid-001)",
        status_code=204,
    )

    result_dict = await update_appointment.ainvoke(
        _args(appointment_id="appt-guid-001", subject="Updated Meeting")
    )

    assert isinstance(result_dict, dict)
    result = UpdateAppointmentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.appointment_id == "appt-guid-001"
    assert "subject" in result.updated_fields


@pytest.mark.asyncio
async def test_get_account_missing_token():  # type: ignore[no-untyped-def]
    """Failure path: missing access_token returns error without hitting network."""
    result_dict = await get_account.ainvoke(
        {"auth_type": "oauth2", "auth_data": {}, "account_id": "acct-guid-001"}
    )

    assert isinstance(result_dict, dict)
    result = GetAccountOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access_token" in result.error

"""Happy-path tests for every QuickBooks Online action, plus the failure paths.

Beyond one success test per action, the suite pins the behaviours that are
easy to regress when every action shares one request helper: a non-2xx folds
into ``success=False`` instead of raising, a ``Fault`` inside an HTTP 200 is
treated as the failure it is, a missing token or company ID is caught before
any HTTP call, the environment can only select a host from a fixed map, and
a 200 whose fields carry the wrong *types* still returns ``success=True``
rather than escaping as a ValidationError.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from modulex_integrations.tools.quickbooks import (
    TOOLS,
    manifest,
)
from modulex_integrations.tools.quickbooks.outputs import (
    CreateAccountOutput,
    CreateBillOutput,
    CreateBillPaymentOutput,
    CreateCreditMemoOutput,
    CreateCustomerOutput,
    CreateEstimateOutput,
    CreateInvoiceOutput,
    CreateItemOutput,
    CreatePaymentOutput,
    CreatePurchaseOutput,
    CreateSalesReceiptOutput,
    CreateVendorOutput,
    DeleteBillOutput,
    DeleteBillPaymentOutput,
    DeleteCreditMemoOutput,
    DeleteCustomerOutput,
    DeleteEstimateOutput,
    DeleteInvoiceOutput,
    DeleteItemOutput,
    DeletePaymentOutput,
    DeletePurchaseOutput,
    DeleteSalesReceiptOutput,
    DeleteVendorOutput,
    GetAccountOutput,
    GetApAgingReportOutput,
    GetBalanceSheetReportOutput,
    GetBillOutput,
    GetBillPaymentOutput,
    GetCashFlowReportOutput,
    GetCompanyInfoOutput,
    GetCreditMemoOutput,
    GetCustomerBalanceReportOutput,
    GetCustomerOutput,
    GetEstimateOutput,
    GetInvoiceOutput,
    GetItemOutput,
    GetPaymentOutput,
    GetProfitAndLossReportOutput,
    GetPurchaseOutput,
    GetSalesReceiptOutput,
    GetTrialBalanceReportOutput,
    GetVendorBalanceReportOutput,
    GetVendorExpensesReportOutput,
    GetVendorOutput,
    RunQueryOutput,
    SearchAccountsOutput,
    SearchBillPaymentsOutput,
    SearchBillsOutput,
    SearchCreditMemosOutput,
    SearchCustomersOutput,
    SearchEstimatesOutput,
    SearchInvoicesOutput,
    SearchItemsOutput,
    SearchPaymentsOutput,
    SearchPurchasesOutput,
    SearchSalesReceiptsOutput,
    SearchVendorsOutput,
    SendEstimateOutput,
    SendInvoiceOutput,
    UpdateAccountOutput,
    UpdateBillOutput,
    UpdateBillPaymentOutput,
    UpdateCompanyInfoOutput,
    UpdateCreditMemoOutput,
    UpdateCustomerOutput,
    UpdateEstimateOutput,
    UpdateInvoiceOutput,
    UpdateItemOutput,
    UpdatePaymentOutput,
    UpdatePurchaseOutput,
    UpdateSalesReceiptOutput,
    UpdateVendorOutput,
    VoidInvoiceOutput,
)
from modulex_integrations.tools.quickbooks.tools import (
    _base_url,
    create_account,
    create_bill,
    create_bill_payment,
    create_credit_memo,
    create_customer,
    create_estimate,
    create_invoice,
    create_item,
    create_payment,
    create_purchase,
    create_sales_receipt,
    create_vendor,
    delete_bill,
    delete_bill_payment,
    delete_credit_memo,
    delete_customer,
    delete_estimate,
    delete_invoice,
    delete_item,
    delete_payment,
    delete_purchase,
    delete_sales_receipt,
    delete_vendor,
    get_account,
    get_ap_aging_report,
    get_balance_sheet_report,
    get_bill,
    get_bill_payment,
    get_cash_flow_report,
    get_company_info,
    get_credit_memo,
    get_customer,
    get_customer_balance_report,
    get_estimate,
    get_invoice,
    get_item,
    get_payment,
    get_profit_and_loss_report,
    get_purchase,
    get_sales_receipt,
    get_trial_balance_report,
    get_vendor,
    get_vendor_balance_report,
    get_vendor_expenses_report,
    run_query,
    search_accounts,
    search_bill_payments,
    search_bills,
    search_credit_memos,
    search_customers,
    search_estimates,
    search_invoices,
    search_items,
    search_payments,
    search_purchases,
    search_sales_receipts,
    search_vendors,
    send_estimate,
    send_invoice,
    update_account,
    update_bill,
    update_bill_payment,
    update_company_info,
    update_credit_memo,
    update_customer,
    update_estimate,
    update_invoice,
    update_item,
    update_payment,
    update_purchase,
    update_sales_receipt,
    update_vendor,
    void_invoice,
)

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {
        "access_token": "test-access-token",
        "realm_id": "9341454816484523",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    """Bypass mypy's TypedDict-spread check on LangChain's .ainvoke()."""
    return dict(_AUTH, **extra)


def _no_realm(**extra: Any) -> dict[str, Any]:
    """Same credential set with the company ID stripped."""
    return dict(
        _AUTH,
        auth_data={"access_token": "test-access-token"},
        **extra,
    )


class TestManifest:
    def test_manifest_exposes_all_actions(self) -> None:
        assert len(manifest.actions) == 73

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}

    def test_no_action_declares_a_credential_parameter(self) -> None:
        reserved = {"auth_type", "auth_data", "access_token", "token", "api_key",
                    "realm_id", "environment"}
        for action in manifest.actions:
            assert not (set(action.parameters) & reserved), action.name


_B1_LINE: dict[str, Any] = {
    "Id": "1",
    "LineNum": 1,
    "Description": "Consulting",
    "Amount": 300.0,
    "DetailType": "SalesItemLineDetail",
    "SalesItemLineDetail": {
        "ItemRef": {"value": "7", "name": "Consulting"},
        "Qty": 3,
        "UnitPrice": 100,
        "TaxCodeRef": {"value": "NON"},
        "ServiceDate": "2026-02-01",
    },
}

_B1_INVOICE: dict[str, Any] = {
    "Id": "42",
    "SyncToken": "1",
    "DocNumber": "1070",
    "TxnDate": "2026-02-01",
    "DueDate": "2026-03-03",
    "CustomerRef": {"value": "58", "name": "Acme Ltd"},
    "CustomerMemo": {"value": "Thanks for your business"},
    "PrivateNote": "Q1 retainer",
    "BillEmail": {"Address": "ap@acme.example"},
    "BillAddr": {"Line1": "1 Market St", "City": "San Francisco"},
    "CurrencyRef": {"value": "USD", "name": "United States Dollar"},
    "TotalAmt": 300.0,
    "Balance": 300.0,
    "EmailStatus": "NotSet",
    "PrintStatus": "NeedToPrint",
    "TxnTaxDetail": {"TotalTax": 0},
    "AllowOnlineCreditCardPayment": True,
    "Line": [_B1_LINE],
    "MetaData": {
        "CreateTime": "2026-02-01T09:00:00-08:00",
        "LastUpdatedTime": "2026-02-01T09:00:00-08:00",
    },
}

_B1_CUSTOMER: dict[str, Any] = {
    "Id": "58",
    "SyncToken": "0",
    "DisplayName": "Acme Ltd",
    "FullyQualifiedName": "Acme Ltd",
    "CompanyName": "Acme Ltd",
    "GivenName": "Ada",
    "FamilyName": "Lovelace",
    "Active": True,
    "Taxable": True,
    "PrimaryEmailAddr": {"Address": "ap@acme.example"},
    "PrimaryPhone": {"FreeFormNumber": "+1 415 555 0100"},
    "WebAddr": {"URI": "https://acme.example"},
    "BillAddr": {"Line1": "1 Market St", "City": "San Francisco"},
    "Balance": 300.0,
    "CurrencyRef": {"value": "USD"},
    "MetaData": {"CreateTime": "2026-01-02T09:00:00-08:00"},
}

_B1_ESTIMATE: dict[str, Any] = {
    "Id": "77",
    "SyncToken": "2",
    "DocNumber": "1021",
    "TxnDate": "2026-02-01",
    "ExpirationDate": "2026-03-01",
    "TxnStatus": "Pending",
    "CustomerRef": {"value": "58", "name": "Acme Ltd"},
    "TotalAmt": 300.0,
    "EmailStatus": "NotSet",
    "Line": [_B1_LINE],
    "MetaData": {"LastUpdatedTime": "2026-02-01T09:00:00-08:00"},
}

_B1_SALES_RECEIPT: dict[str, Any] = {
    "Id": "91",
    "SyncToken": "0",
    "DocNumber": "1005",
    "TxnDate": "2026-02-01",
    "CustomerRef": {"value": "58", "name": "Acme Ltd"},
    "PaymentMethodRef": {"value": "3", "name": "Credit Card"},
    "PaymentRefNum": "ch_123",
    "DepositToAccountRef": {"value": "35", "name": "Checking"},
    "TotalAmt": 300.0,
    "Balance": 0,
    "Line": [_B1_LINE],
    "MetaData": {"CreateTime": "2026-02-01T09:00:00-08:00"},
}

_B1_CREDIT_MEMO: dict[str, Any] = {
    "Id": "64",
    "SyncToken": "0",
    "DocNumber": "1044",
    "TxnDate": "2026-02-02",
    "CustomerRef": {"value": "58", "name": "Acme Ltd"},
    "TotalAmt": 100.0,
    "Balance": 100.0,
    "RemainingCredit": 100.0,
    "Line": [_B1_LINE],
    "MetaData": {"CreateTime": "2026-02-02T09:00:00-08:00"},
}


def _b1_body(httpx_mock: Any) -> dict[str, Any]:
    """JSON body of the most recent request."""
    request = httpx_mock.get_requests()[-1]
    parsed: dict[str, Any] = json.loads(request.content)
    return parsed


def _b1_query(httpx_mock: Any) -> str:
    """``query`` parameter of the most recent request."""
    return str(httpx_mock.get_requests()[-1].url.params["query"])


class TestInvoices:
    @pytest.mark.asyncio
    async def test_create_invoice(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(method="POST", json={"Invoice": _B1_INVOICE})

        result_dict = await create_invoice.ainvoke(
            _args(
                customer_id="58",
                line_items=[{"item_ref": "7", "qty": 3, "unit_price": 100}],
                bill_email="ap@acme.example",
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateInvoiceOutput.model_validate(result_dict)
        assert result.success is True
        assert result.invoice is not None
        assert result.invoice.invoice_id == "42"
        assert result.invoice.customer_name == "Acme Ltd"
        assert result.invoice.lines[0].item_id == "7"

        body = _b1_body(httpx_mock)
        assert body["CustomerRef"] == {"value": "58"}
        assert body["BillEmail"] == {"Address": "ap@acme.example"}
        line = body["Line"][0]
        assert line["DetailType"] == "SalesItemLineDetail"
        assert line["Amount"] == 300
        assert line["SalesItemLineDetail"]["ItemRef"] == {"value": "7"}
        assert line["SalesItemLineDetail"]["UnitPrice"] == 100

    @pytest.mark.asyncio
    async def test_get_invoice(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(method="GET", json={"Invoice": _B1_INVOICE})

        result_dict = await get_invoice.ainvoke(_args(invoice_id="42"))

        assert isinstance(result_dict, dict)
        result = GetInvoiceOutput.model_validate(result_dict)
        assert result.success is True
        assert result.invoice is not None
        assert result.invoice.balance == 300.0
        assert httpx_mock.get_requests()[-1].url.path.endswith("/invoice/42")

    @pytest.mark.asyncio
    async def test_update_invoice(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(method="POST", json={"Invoice": _B1_INVOICE})

        result_dict = await update_invoice.ainvoke(
            _args(invoice_id="42", private_note="Q1 retainer", sync_token="1")
        )

        assert isinstance(result_dict, dict)
        result = UpdateInvoiceOutput.model_validate(result_dict)
        assert result.success is True
        assert result.invoice is not None

        request = httpx_mock.get_requests()[-1]
        assert request.url.params["operation"] == "update"
        body = _b1_body(httpx_mock)
        assert body["Id"] == "42"
        assert body["SyncToken"] == "1"
        assert body["sparse"] is True
        assert body["PrivateNote"] == "Q1 retainer"

    @pytest.mark.asyncio
    async def test_delete_invoice(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            json={"Invoice": {"Id": "42", "status": "Deleted", "domain": "QBO"}},
        )

        result_dict = await delete_invoice.ainvoke(
            _args(invoice_id="42", sync_token="1")
        )

        assert isinstance(result_dict, dict)
        result = DeleteInvoiceOutput.model_validate(result_dict)
        assert result.success is True
        assert result.invoice_id == "42"
        assert result.status == "Deleted"
        assert httpx_mock.get_requests()[-1].url.params["operation"] == "delete"

    @pytest.mark.asyncio
    async def test_search_invoices(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            json={"QueryResponse": {"Invoice": [_B1_INVOICE], "maxResults": 1}},
        )

        result_dict = await search_invoices.ainvoke(
            _args(customer_id="58", unpaid_only=True, max_results=10)
        )

        assert isinstance(result_dict, dict)
        result = SearchInvoicesOutput.model_validate(result_dict)
        assert result.success is True
        assert result.count == 1
        assert result.invoices[0].invoice_id == "42"

        query = _b1_query(httpx_mock)
        assert "SELECT * FROM Invoice WHERE" in query
        assert "CustomerRef = '58'" in query
        assert "Balance > '0'" in query
        assert query.endswith("MAXRESULTS 10")


class TestCustomers:
    @pytest.mark.asyncio
    async def test_create_customer(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(method="POST", json={"Customer": _B1_CUSTOMER})

        result_dict = await create_customer.ainvoke(
            _args(
                display_name="Acme Ltd",
                primary_email="ap@acme.example",
                bill_address={"line1": "1 Market St", "city": "San Francisco"},
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateCustomerOutput.model_validate(result_dict)
        assert result.success is True
        assert result.customer is not None
        assert result.customer.customer_id == "58"
        assert result.customer.primary_email == "ap@acme.example"

        body = _b1_body(httpx_mock)
        assert body["DisplayName"] == "Acme Ltd"
        assert body["PrimaryEmailAddr"] == {"Address": "ap@acme.example"}
        assert body["BillAddr"] == {"Line1": "1 Market St", "City": "San Francisco"}

    @pytest.mark.asyncio
    async def test_get_customer(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(method="GET", json={"Customer": _B1_CUSTOMER})

        result_dict = await get_customer.ainvoke(_args(customer_id="58"))

        assert isinstance(result_dict, dict)
        result = GetCustomerOutput.model_validate(result_dict)
        assert result.success is True
        assert result.customer is not None
        assert result.customer.display_name == "Acme Ltd"
        assert result.customer.website == "https://acme.example"

    @pytest.mark.asyncio
    async def test_update_customer(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(method="POST", json={"Customer": _B1_CUSTOMER})

        result_dict = await update_customer.ainvoke(
            _args(customer_id="58", notes="VIP", sync_token="0")
        )

        assert isinstance(result_dict, dict)
        result = UpdateCustomerOutput.model_validate(result_dict)
        assert result.success is True

        body = _b1_body(httpx_mock)
        assert body["Id"] == "58"
        assert body["sparse"] is True
        assert body["Notes"] == "VIP"

    @pytest.mark.asyncio
    async def test_delete_customer_deactivates(self, httpx_mock: Any) -> None:
        """QuickBooks has no delete for customers.

        The write must be a sparse ``operation=update`` setting
        ``Active: false`` — never ``operation=delete``, which the API does
        not implement for name-list entities.
        """
        httpx_mock.add_response(
            method="POST",
            json={"Customer": dict(_B1_CUSTOMER, Active=False, SyncToken="1")},
        )

        result_dict = await delete_customer.ainvoke(
            _args(customer_id="58", sync_token="0")
        )

        assert isinstance(result_dict, dict)
        result = DeleteCustomerOutput.model_validate(result_dict)
        assert result.success is True
        assert result.deactivated is True
        assert result.customer is not None
        assert result.customer.active is False

        request = httpx_mock.get_requests()[-1]
        assert request.url.path.endswith("/customer")
        assert request.url.params["operation"] == "update"
        assert request.url.params["operation"] != "delete"
        body = _b1_body(httpx_mock)
        assert body["Active"] is False
        assert body["sparse"] is True
        assert body["Id"] == "58"
        assert body["SyncToken"] == "0"

    @pytest.mark.asyncio
    async def test_search_customers(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET", json={"QueryResponse": {"Customer": [_B1_CUSTOMER]}}
        )

        result_dict = await search_customers.ainvoke(
            _args(name_contains="Acme", active=True, start_position=1)
        )

        assert isinstance(result_dict, dict)
        result = SearchCustomersOutput.model_validate(result_dict)
        assert result.success is True
        assert result.count == 1
        assert result.customers[0].display_name == "Acme Ltd"

        query = _b1_query(httpx_mock)
        assert "DisplayName LIKE '%Acme%'" in query
        assert "Active = true" in query
        assert "STARTPOSITION 1" in query

    @pytest.mark.asyncio
    async def test_search_customers_escapes_quotes(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(method="GET", json={"QueryResponse": {}})

        result_dict = await search_customers.ainvoke(_args(display_name="O'Brien"))

        assert isinstance(result_dict, dict)
        result = SearchCustomersOutput.model_validate(result_dict)
        assert result.success is True
        assert "DisplayName = 'O\\'Brien'" in _b1_query(httpx_mock)


class TestEstimates:
    @pytest.mark.asyncio
    async def test_create_estimate(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(method="POST", json={"Estimate": _B1_ESTIMATE})

        result_dict = await create_estimate.ainvoke(
            _args(
                customer_id="58",
                line_items=[{"item_ref": "7", "qty": 3, "unit_price": 100}],
                expiration_date="2026-03-01",
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateEstimateOutput.model_validate(result_dict)
        assert result.success is True
        assert result.estimate is not None
        assert result.estimate.estimate_id == "77"
        assert _b1_body(httpx_mock)["ExpirationDate"] == "2026-03-01"

    @pytest.mark.asyncio
    async def test_get_estimate(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(method="GET", json={"Estimate": _B1_ESTIMATE})

        result_dict = await get_estimate.ainvoke(_args(estimate_id="77"))

        assert isinstance(result_dict, dict)
        result = GetEstimateOutput.model_validate(result_dict)
        assert result.success is True
        assert result.estimate is not None
        assert result.estimate.txn_status == "Pending"

    @pytest.mark.asyncio
    async def test_update_estimate(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST", json={"Estimate": dict(_B1_ESTIMATE, TxnStatus="Accepted")}
        )

        result_dict = await update_estimate.ainvoke(
            _args(estimate_id="77", txn_status="Accepted", sync_token="2")
        )

        assert isinstance(result_dict, dict)
        result = UpdateEstimateOutput.model_validate(result_dict)
        assert result.success is True
        assert result.estimate is not None
        assert result.estimate.txn_status == "Accepted"
        assert _b1_body(httpx_mock)["TxnStatus"] == "Accepted"

    @pytest.mark.asyncio
    async def test_delete_estimate(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST", json={"Estimate": {"Id": "77", "status": "Deleted"}}
        )

        result_dict = await delete_estimate.ainvoke(
            _args(estimate_id="77", sync_token="2")
        )

        assert isinstance(result_dict, dict)
        result = DeleteEstimateOutput.model_validate(result_dict)
        assert result.success is True
        assert result.estimate_id == "77"
        assert result.status == "Deleted"
        assert httpx_mock.get_requests()[-1].url.params["operation"] == "delete"

    @pytest.mark.asyncio
    async def test_search_estimates(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET", json={"QueryResponse": {"Estimate": [_B1_ESTIMATE]}}
        )

        result_dict = await search_estimates.ainvoke(
            _args(customer_id="58", txn_status="Pending")
        )

        assert isinstance(result_dict, dict)
        result = SearchEstimatesOutput.model_validate(result_dict)
        assert result.success is True
        assert result.count == 1

        query = _b1_query(httpx_mock)
        assert "SELECT * FROM Estimate WHERE" in query
        assert "TxnStatus = 'Pending'" in query


class TestSalesReceipts:
    @pytest.mark.asyncio
    async def test_create_sales_receipt(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST", json={"SalesReceipt": _B1_SALES_RECEIPT}
        )

        result_dict = await create_sales_receipt.ainvoke(
            _args(
                line_items=[{"item_ref": "7", "qty": 3, "unit_price": 100}],
                customer_id="58",
                payment_method_id="3",
                deposit_to_account_id="35",
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateSalesReceiptOutput.model_validate(result_dict)
        assert result.success is True
        assert result.sales_receipt is not None
        assert result.sales_receipt.sales_receipt_id == "91"
        assert result.sales_receipt.payment_method_id == "3"

        body = _b1_body(httpx_mock)
        assert body["PaymentMethodRef"] == {"value": "3"}
        assert body["DepositToAccountRef"] == {"value": "35"}

    @pytest.mark.asyncio
    async def test_get_sales_receipt(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(method="GET", json={"SalesReceipt": _B1_SALES_RECEIPT})

        result_dict = await get_sales_receipt.ainvoke(_args(sales_receipt_id="91"))

        assert isinstance(result_dict, dict)
        result = GetSalesReceiptOutput.model_validate(result_dict)
        assert result.success is True
        assert result.sales_receipt is not None
        assert result.sales_receipt.payment_reference_number == "ch_123"
        assert httpx_mock.get_requests()[-1].url.path.endswith("/salesreceipt/91")

    @pytest.mark.asyncio
    async def test_update_sales_receipt(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST", json={"SalesReceipt": _B1_SALES_RECEIPT}
        )

        result_dict = await update_sales_receipt.ainvoke(
            _args(sales_receipt_id="91", private_note="Booth sale", sync_token="0")
        )

        assert isinstance(result_dict, dict)
        result = UpdateSalesReceiptOutput.model_validate(result_dict)
        assert result.success is True

        body = _b1_body(httpx_mock)
        assert body["Id"] == "91"
        assert body["sparse"] is True
        assert body["PrivateNote"] == "Booth sale"

    @pytest.mark.asyncio
    async def test_delete_sales_receipt(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST", json={"SalesReceipt": {"Id": "91", "status": "Deleted"}}
        )

        result_dict = await delete_sales_receipt.ainvoke(
            _args(sales_receipt_id="91", sync_token="0")
        )

        assert isinstance(result_dict, dict)
        result = DeleteSalesReceiptOutput.model_validate(result_dict)
        assert result.success is True
        assert result.sales_receipt_id == "91"
        assert httpx_mock.get_requests()[-1].url.params["operation"] == "delete"

    @pytest.mark.asyncio
    async def test_search_sales_receipts(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            json={"QueryResponse": {"SalesReceipt": [_B1_SALES_RECEIPT]}},
        )

        result_dict = await search_sales_receipts.ainvoke(
            _args(txn_date_from="2026-01-01", txn_date_to="2026-02-28")
        )

        assert isinstance(result_dict, dict)
        result = SearchSalesReceiptsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.count == 1

        query = _b1_query(httpx_mock)
        assert "SELECT * FROM SalesReceipt WHERE" in query
        assert "TxnDate >= '2026-01-01'" in query
        assert "TxnDate <= '2026-02-28'" in query


class TestCreditMemos:
    @pytest.mark.asyncio
    async def test_create_credit_memo(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(method="POST", json={"CreditMemo": _B1_CREDIT_MEMO})

        result_dict = await create_credit_memo.ainvoke(
            _args(
                customer_id="58",
                line_items=[{"item_ref": "7", "qty": 1, "unit_price": 100}],
                customer_memo="Returned one seat",
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateCreditMemoOutput.model_validate(result_dict)
        assert result.success is True
        assert result.credit_memo is not None
        assert result.credit_memo.credit_memo_id == "64"
        assert result.credit_memo.remaining_credit == 100.0
        assert _b1_body(httpx_mock)["CustomerMemo"] == {"value": "Returned one seat"}

    @pytest.mark.asyncio
    async def test_get_credit_memo(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(method="GET", json={"CreditMemo": _B1_CREDIT_MEMO})

        result_dict = await get_credit_memo.ainvoke(_args(credit_memo_id="64"))

        assert isinstance(result_dict, dict)
        result = GetCreditMemoOutput.model_validate(result_dict)
        assert result.success is True
        assert result.credit_memo is not None
        assert result.credit_memo.total_amount == 100.0
        assert httpx_mock.get_requests()[-1].url.path.endswith("/creditmemo/64")

    @pytest.mark.asyncio
    async def test_update_credit_memo(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(method="POST", json={"CreditMemo": _B1_CREDIT_MEMO})

        result_dict = await update_credit_memo.ainvoke(
            _args(credit_memo_id="64", doc_number="1044", sync_token="0")
        )

        assert isinstance(result_dict, dict)
        result = UpdateCreditMemoOutput.model_validate(result_dict)
        assert result.success is True

        body = _b1_body(httpx_mock)
        assert body["Id"] == "64"
        assert body["sparse"] is True
        assert body["DocNumber"] == "1044"

    @pytest.mark.asyncio
    async def test_delete_credit_memo(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST", json={"CreditMemo": {"Id": "64", "status": "Deleted"}}
        )

        result_dict = await delete_credit_memo.ainvoke(
            _args(credit_memo_id="64", sync_token="0")
        )

        assert isinstance(result_dict, dict)
        result = DeleteCreditMemoOutput.model_validate(result_dict)
        assert result.success is True
        assert result.credit_memo_id == "64"
        assert httpx_mock.get_requests()[-1].url.params["operation"] == "delete"

    @pytest.mark.asyncio
    async def test_search_credit_memos(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET", json={"QueryResponse": {"CreditMemo": [_B1_CREDIT_MEMO]}}
        )

        result_dict = await search_credit_memos.ainvoke(_args(customer_id="58"))

        assert isinstance(result_dict, dict)
        result = SearchCreditMemosOutput.model_validate(result_dict)
        assert result.success is True
        assert result.count == 1
        assert "SELECT * FROM CreditMemo WHERE" in _b1_query(httpx_mock)


class TestSalesDelivery:
    @pytest.mark.asyncio
    async def test_send_invoice(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            json={"Invoice": dict(_B1_INVOICE, EmailStatus="EmailSent")},
        )

        result_dict = await send_invoice.ainvoke(
            _args(invoice_id="42", email="ap@acme.example")
        )

        assert isinstance(result_dict, dict)
        result = SendInvoiceOutput.model_validate(result_dict)
        assert result.success is True
        assert result.email_status == "EmailSent"
        assert result.invoice is not None

        request = httpx_mock.get_requests()[-1]
        assert request.url.path.endswith("/invoice/42/send")
        assert request.url.params["sendTo"] == "ap@acme.example"

    @pytest.mark.asyncio
    async def test_send_estimate(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            json={"Estimate": dict(_B1_ESTIMATE, EmailStatus="EmailSent")},
        )

        result_dict = await send_estimate.ainvoke(_args(estimate_id="77"))

        assert isinstance(result_dict, dict)
        result = SendEstimateOutput.model_validate(result_dict)
        assert result.success is True
        assert result.email_status == "EmailSent"

        request = httpx_mock.get_requests()[-1]
        assert request.url.path.endswith("/estimate/77/send")
        assert "sendTo" not in request.url.params

    @pytest.mark.asyncio
    async def test_void_invoice(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            json={
                "Invoice": dict(
                    _B1_INVOICE,
                    TotalAmt=0,
                    Balance=0,
                    PrivateNote="Voided",
                    SyncToken="2",
                )
            },
        )

        result_dict = await void_invoice.ainvoke(
            _args(invoice_id="42", sync_token="1")
        )

        assert isinstance(result_dict, dict)
        result = VoidInvoiceOutput.model_validate(result_dict)
        assert result.success is True
        assert result.invoice is not None
        assert result.invoice.total_amount == 0.0
        assert result.invoice.private_note == "Voided"

        request = httpx_mock.get_requests()[-1]
        assert request.url.params["operation"] == "void"
        body = _b1_body(httpx_mock)
        assert body == {"Id": "42", "SyncToken": "1"}


class TestSalesCycleSyncToken:
    @pytest.mark.asyncio
    async def test_sync_token_is_resolved_when_omitted(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET", json={"Invoice": {"Id": "42", "SyncToken": "7"}}
        )
        httpx_mock.add_response(method="POST", json={"Invoice": _B1_INVOICE})

        result_dict = await update_invoice.ainvoke(
            _args(invoice_id="42", private_note="Amended")
        )

        assert isinstance(result_dict, dict)
        result = UpdateInvoiceOutput.model_validate(result_dict)
        assert result.success is True

        requests = httpx_mock.get_requests()
        assert len(requests) == 2
        assert requests[0].method == "GET"
        assert requests[0].url.path.endswith("/invoice/42")
        assert _b1_body(httpx_mock)["SyncToken"] == "7"

    @pytest.mark.asyncio
    async def test_explicit_sync_token_skips_the_lookup(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST", json={"Invoice": {"Id": "42", "status": "Deleted"}}
        )

        result_dict = await delete_invoice.ainvoke(
            _args(invoice_id="42", sync_token="7")
        )

        assert isinstance(result_dict, dict)
        result = DeleteInvoiceOutput.model_validate(result_dict)
        assert result.success is True

        requests = httpx_mock.get_requests()
        assert len(requests) == 1
        assert requests[0].method == "POST"


class TestSalesCycleErrors:
    @pytest.mark.asyncio
    async def test_non_2xx_folds_into_the_envelope(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            status_code=401,
            json={
                "Fault": {
                    "Error": [
                        {
                            "Message": "message=AuthenticationFailed",
                            "Detail": "Token expired",
                            "code": "3200",
                        }
                    ],
                    "type": "AUTHENTICATION",
                }
            },
        )

        result_dict = await get_invoice.ainvoke(_args(invoice_id="42"))

        assert isinstance(result_dict, dict)
        result = GetInvoiceOutput.model_validate(result_dict)
        assert result.success is False
        assert result.invoice is None
        assert result.error is not None
        assert "3200" in result.error
        assert "401" in result.error

    @pytest.mark.asyncio
    async def test_fault_inside_http_200_is_an_error(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="POST",
            status_code=200,
            json={
                "Fault": {
                    "Error": [
                        {
                            "Message": "Invalid Reference Id",
                            "Detail": "Customer 999 not found",
                            "code": "6240",
                        }
                    ],
                    "type": "ValidationFault",
                }
            },
        )

        result_dict = await create_invoice.ainvoke(
            _args(
                customer_id="999",
                line_items=[{"item_ref": "7", "qty": 1, "unit_price": 10}],
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateInvoiceOutput.model_validate(result_dict)
        assert result.success is False
        assert result.invoice is None
        assert result.error is not None
        assert "6240" in result.error
        assert "ValidationFault" in result.error

    @pytest.mark.asyncio
    async def test_empty_query_response_returns_no_rows(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(method="GET", json={"QueryResponse": {}, "time": "x"})

        result_dict = await search_invoices.ainvoke(_args(customer_id="404"))

        assert isinstance(result_dict, dict)
        result = SearchInvoicesOutput.model_validate(result_dict)
        assert result.success is True
        assert result.invoices == []
        assert result.count == 0

    @pytest.mark.asyncio
    async def test_wrongly_typed_fields_still_succeed(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            method="GET",
            json={
                "Invoice": {
                    "Id": 42,
                    "SyncToken": {"unexpected": "object"},
                    "TotalAmt": "not-a-number",
                    "Balance": "300.50",
                    "CustomerRef": "58",
                    "Line": "not-an-array",
                    "MetaData": [],
                }
            },
        )

        result_dict = await get_invoice.ainvoke(_args(invoice_id="42"))

        assert isinstance(result_dict, dict)
        result = GetInvoiceOutput.model_validate(result_dict)
        assert result.success is True
        assert result.invoice is not None
        assert result.invoice.invoice_id == "42"
        assert result.invoice.sync_token is None
        assert result.invoice.total_amount is None
        assert result.invoice.balance == 300.5
        assert result.invoice.customer_id is None
        assert result.invoice.lines == []


def _b2_body(httpx_mock: Any, index: int = 0) -> str:
    """Outgoing JSON body with whitespace stripped.

    httpx picks its own separators when it serializes, so the tests compare
    against a space-free rendering rather than depending on that choice.
    """
    return str(httpx_mock.get_requests()[index].content.decode()).replace(" ", "")


def _b2_query(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "QueryResponse": {name: rows, "startPosition": 1, "maxResults": len(rows)},
        "time": "2026-01-14T09:00:00-08:00",
    }


def _b2_vendor(**extra: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "Id": "56",
        "SyncToken": "0",
        "DisplayName": "Norton Lumber and Building Materials",
        "CompanyName": "Norton Lumber and Building Materials",
        "PrintOnCheckName": "Norton Lumber and Building Materials",
        "PrimaryEmailAddr": {"Address": "ap@nortonlumber.example"},
        "PrimaryPhone": {"FreeFormNumber": "(650) 555-1234"},
        "WebAddr": {"URI": "https://nortonlumber.example"},
        "BillAddr": {
            "Line1": "29 Fifth Avenue",
            "City": "Half Moon Bay",
            "CountrySubDivisionCode": "CA",
            "PostalCode": "94213",
        },
        "TermRef": {"value": "3", "name": "Net 30"},
        "AcctNum": "35372649",
        "Vendor1099": False,
        "Balance": 0.0,
        "Active": True,
        "MetaData": {
            "CreateTime": "2026-01-10T09:00:00-08:00",
            "LastUpdatedTime": "2026-01-12T09:00:00-08:00",
        },
    }
    record.update(extra)
    return record


def _b2_bill(**extra: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "Id": "890",
        "SyncToken": "0",
        "DocNumber": "INV-4471",
        "TxnDate": "2026-01-12",
        "DueDate": "2026-02-11",
        "VendorRef": {"value": "56", "name": "Norton Lumber"},
        "APAccountRef": {"value": "33", "name": "Accounts Payable (A/P)"},
        "SalesTermRef": {"value": "3"},
        "CurrencyRef": {"value": "USD"},
        "PrivateNote": "Timber for the Miller job",
        "TotalAmt": 1250.0,
        "Balance": 1250.0,
        "Line": [
            {
                "Id": "1",
                "DetailType": "AccountBasedExpenseLineDetail",
                "Amount": 1250.0,
                "Description": "Framing lumber",
                "AccountBasedExpenseLineDetail": {
                    "AccountRef": {"value": "7", "name": "Job Materials"},
                    "BillableStatus": "NotBillable",
                    "TaxCodeRef": {"value": "NON"},
                },
            }
        ],
        "LinkedTxn": [{"TxnId": "915", "TxnType": "BillPaymentCheck"}],
        "MetaData": {
            "CreateTime": "2026-01-12T09:00:00-08:00",
            "LastUpdatedTime": "2026-01-12T09:00:00-08:00",
        },
    }
    record.update(extra)
    return record


def _b2_bill_payment(**extra: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "Id": "915",
        "SyncToken": "0",
        "DocNumber": "1042",
        "TxnDate": "2026-01-20",
        "VendorRef": {"value": "56", "name": "Norton Lumber"},
        "APAccountRef": {"value": "33", "name": "Accounts Payable (A/P)"},
        "PayType": "Check",
        "TotalAmt": 1250.0,
        "CheckPayment": {
            "BankAccountRef": {"value": "35", "name": "Checking"},
            "PrintStatus": "NeedToPrint",
        },
        "Line": [
            {
                "Amount": 1250.0,
                "LinkedTxn": [{"TxnId": "890", "TxnType": "Bill"}],
            }
        ],
        "MetaData": {
            "CreateTime": "2026-01-20T09:00:00-08:00",
            "LastUpdatedTime": "2026-01-20T09:00:00-08:00",
        },
    }
    record.update(extra)
    return record


def _b2_payment(**extra: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "Id": "301",
        "SyncToken": "0",
        "TxnDate": "2026-01-18",
        "CustomerRef": {"value": "20", "name": "Freeman Sporting Goods"},
        "DepositToAccountRef": {"value": "4", "name": "Undeposited Funds"},
        "PaymentMethodRef": {"value": "2", "name": "Check"},
        "PaymentRefNum": "7788",
        "TotalAmt": 450.0,
        "UnappliedAmt": 0.0,
        "Line": [
            {
                "Amount": 450.0,
                "LinkedTxn": [{"TxnId": "129", "TxnType": "Invoice"}],
            }
        ],
        "MetaData": {
            "CreateTime": "2026-01-18T09:00:00-08:00",
            "LastUpdatedTime": "2026-01-18T09:00:00-08:00",
        },
    }
    record.update(extra)
    return record


def _b2_purchase(**extra: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "Id": "252",
        "SyncToken": "0",
        "TxnDate": "2026-01-15",
        "PaymentType": "Cash",
        "TotalAmt": 10.0,
        "AccountRef": {"value": "35", "name": "Checking"},
        "EntityRef": {"value": "56", "name": "Norton Lumber", "type": "Vendor"},
        "Line": [
            {
                "Id": "1",
                "DetailType": "AccountBasedExpenseLineDetail",
                "Amount": 10.0,
                "AccountBasedExpenseLineDetail": {
                    "AccountRef": {"value": "13", "name": "Meals and Entertainment"},
                    "BillableStatus": "NotBillable",
                    "TaxCodeRef": {"value": "NON"},
                },
            }
        ],
        "MetaData": {
            "CreateTime": "2026-01-15T09:00:00-08:00",
            "LastUpdatedTime": "2026-01-15T09:00:00-08:00",
        },
    }
    record.update(extra)
    return record


class TestVendors:
    @pytest.mark.asyncio
    async def test_create_vendor(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Vendor": _b2_vendor()})

        result_dict = await create_vendor.ainvoke(
            _args(
                display_name="Norton Lumber and Building Materials",
                email="ap@nortonlumber.example",
                phone="(650) 555-1234",
                website="https://nortonlumber.example",
                term_id="3",
                bill_address_line1="29 Fifth Avenue",
                bill_address_city="Half Moon Bay",
                bill_address_state="CA",
                bill_address_postal_code="94213",
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateVendorOutput.model_validate(result_dict)
        assert result.success is True
        assert result.vendor is not None
        assert result.vendor.id == "56"
        assert result.vendor.email == "ap@nortonlumber.example"
        assert result.vendor.website == "https://nortonlumber.example"
        assert result.vendor.term_name == "Net 30"
        assert result.vendor.bill_address is not None
        assert result.vendor.bill_address.state == "CA"

        body = _b2_body(httpx_mock)
        assert '"PrimaryEmailAddr":{"Address":"ap@nortonlumber.example"}' in body
        assert '"TermRef":{"value":"3"}' in body
        assert '"CountrySubDivisionCode":"CA"' in body

    @pytest.mark.asyncio
    async def test_create_vendor_needs_a_name(self, httpx_mock: Any) -> None:
        result_dict = await create_vendor.ainvoke(_args(email="nobody@example.com"))

        result = CreateVendorOutput.model_validate(result_dict)
        assert result.success is False
        assert result.error is not None
        assert "display_name" in result.error
        assert httpx_mock.get_requests() == []

    @pytest.mark.asyncio
    async def test_get_vendor(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Vendor": _b2_vendor()})

        result_dict = await get_vendor.ainvoke(_args(vendor_id="56"))

        assert isinstance(result_dict, dict)
        result = GetVendorOutput.model_validate(result_dict)
        assert result.success is True
        assert result.vendor is not None
        assert result.vendor.display_name == "Norton Lumber and Building Materials"
        assert result.vendor.account_number == "35372649"
        assert result.vendor.active is True
        assert httpx_mock.get_requests()[0].url.path.endswith("/vendor/56")

    @pytest.mark.asyncio
    async def test_update_vendor(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            json={"Vendor": _b2_vendor(SyncToken="4", AcctNum="99887766")}
        )

        result_dict = await update_vendor.ainvoke(
            _args(vendor_id="56", account_number="99887766", sync_token="3")
        )

        assert isinstance(result_dict, dict)
        result = UpdateVendorOutput.model_validate(result_dict)
        assert result.success is True
        assert result.vendor is not None
        assert result.vendor.account_number == "99887766"

        request = httpx_mock.get_requests()[0]
        assert request.url.params["operation"] == "update"
        body = _b2_body(httpx_mock)
        assert '"sparse":true' in body
        assert '"SyncToken":"3"' in body
        assert '"AcctNum":"99887766"' in body

    @pytest.mark.asyncio
    async def test_delete_vendor_deactivates_rather_than_deleting(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(
            json={"Vendor": _b2_vendor(SyncToken="4", Active=False)}
        )

        result_dict = await delete_vendor.ainvoke(
            _args(vendor_id="56", sync_token="3")
        )

        assert isinstance(result_dict, dict)
        result = DeleteVendorOutput.model_validate(result_dict)
        assert result.success is True
        assert result.deactivated is True
        assert result.vendor_id == "56"
        assert result.vendor is not None
        assert result.vendor.active is False

        # QuickBooks has no delete for vendors, so this must be a sparse
        # update that clears Active, never operation=delete.
        request = httpx_mock.get_requests()[0]
        assert request.url.params["operation"] == "update"
        assert "operation=delete" not in str(request.url)
        body = _b2_body(httpx_mock)
        assert '"Active":false' in body
        assert '"sparse":true' in body

    @pytest.mark.asyncio
    async def test_search_vendors(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json=_b2_query("Vendor", [_b2_vendor()]))

        result_dict = await search_vendors.ainvoke(
            _args(name_contains="Norton", active=True, max_results=25)
        )

        assert isinstance(result_dict, dict)
        result = SearchVendorsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.count == 1
        assert result.vendors[0].id == "56"
        assert result.start_position == 1

        statement = httpx_mock.get_requests()[0].url.params["query"]
        assert "SELECT * FROM Vendor WHERE" in statement
        assert "DisplayName LIKE '%Norton%'" in statement
        assert "Active = true" in statement
        assert statement.endswith("MAXRESULTS 25")


class TestBills:
    @pytest.mark.asyncio
    async def test_create_bill(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Bill": _b2_bill()})

        result_dict = await create_bill.ainvoke(
            _args(
                vendor_id="56",
                lines=[
                    {
                        "amount": 1250.0,
                        "account_id": "7",
                        "description": "Framing lumber",
                        "tax_code_id": "NON",
                    }
                ],
                due_date="2026-02-11",
                doc_number="INV-4471",
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateBillOutput.model_validate(result_dict)
        assert result.success is True
        assert result.bill is not None
        assert result.bill.id == "890"
        assert result.bill.vendor_id == "56"
        assert result.bill.balance == 1250.0
        assert result.bill.lines[0].account_name == "Job Materials"
        assert result.bill.linked_transactions[0].txn_type == "BillPaymentCheck"

        body = _b2_body(httpx_mock)
        # Expense-side line shape, not the sales-side SalesItemLineDetail.
        assert '"DetailType":"AccountBasedExpenseLineDetail"' in body
        assert '"AccountRef":{"value":"7"}' in body
        assert "SalesItemLineDetail" not in body

    @pytest.mark.asyncio
    async def test_create_bill_needs_a_line(self, httpx_mock: Any) -> None:
        result_dict = await create_bill.ainvoke(_args(vendor_id="56", lines=[]))

        result = CreateBillOutput.model_validate(result_dict)
        assert result.success is False
        assert result.error is not None
        assert httpx_mock.get_requests() == []

    @pytest.mark.asyncio
    async def test_get_bill(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Bill": _b2_bill()})

        result_dict = await get_bill.ainvoke(_args(bill_id="890"))

        assert isinstance(result_dict, dict)
        result = GetBillOutput.model_validate(result_dict)
        assert result.success is True
        assert result.bill is not None
        assert result.bill.doc_number == "INV-4471"
        assert result.bill.due_date == "2026-02-11"
        assert result.bill.lines[0].tax_code_id == "NON"
        assert httpx_mock.get_requests()[0].url.path.endswith("/bill/890")

    @pytest.mark.asyncio
    async def test_update_bill_reads_then_overwrites(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Bill": _b2_bill(SyncToken="1")})
        httpx_mock.add_response(json={"Bill": _b2_bill(SyncToken="2")})

        result_dict = await update_bill.ainvoke(
            _args(bill_id="890", private_note="Miller job", sync_token="1")
        )

        assert isinstance(result_dict, dict)
        result = UpdateBillOutput.model_validate(result_dict)
        assert result.success is True
        assert result.bill is not None
        assert result.bill.sync_token == "2"

        requests = httpx_mock.get_requests()
        # The read happens even when the caller supplied a SyncToken, because
        # the write is a full overwrite and needs the rest of the record.
        assert len(requests) == 2
        assert requests[0].method == "GET"
        assert requests[0].url.path.endswith("/bill/890")
        assert requests[1].url.params["operation"] == "update"

        body = _b2_body(httpx_mock, 1)
        assert '"sparse"' not in body
        assert '"SyncToken":"1"' in body
        assert '"PrivateNote":"Millerjob"' in body
        # Fields the caller never mentioned ride along from the read.
        assert '"DocNumber":"INV-4471"' in body
        assert '"DueDate":"2026-02-11"' in body

    @pytest.mark.asyncio
    async def test_update_bill_without_lines_keeps_the_existing_lines(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json={"Bill": _b2_bill()})
        httpx_mock.add_response(json={"Bill": _b2_bill(SyncToken="1")})

        result_dict = await update_bill.ainvoke(
            _args(bill_id="890", doc_number="INV-4472")
        )

        result = UpdateBillOutput.model_validate(result_dict)
        assert result.success is True

        body = _b2_body(httpx_mock, 1)
        assert '"DocNumber":"INV-4472"' in body
        # Under a full overwrite an omitted Line would wipe every line on the
        # bill, so the array read a moment ago must ride along verbatim.
        assert '"Amount":1250.0' in body
        assert '"AccountRef":{"value":"7","name":"JobMaterials"}' in body
        assert '"TaxCodeRef":{"value":"NON"}' in body

    @pytest.mark.asyncio
    async def test_replacement_line_inherits_class_and_tax_code(
        self, httpx_mock: Any
    ) -> None:
        existing = _b2_bill()
        existing["Line"][0]["AccountBasedExpenseLineDetail"]["ClassRef"] = {
            "value": "5000000000000041",
            "name": "Residential",
        }
        httpx_mock.add_response(json={"Bill": existing})
        httpx_mock.add_response(json={"Bill": _b2_bill(SyncToken="1")})

        result_dict = await update_bill.ainvoke(
            _args(
                bill_id="890",
                lines=[{"line_id": "1", "amount": 1400.0, "account_id": "7"}],
            )
        )

        result = UpdateBillOutput.model_validate(result_dict)
        assert result.success is True

        body = _b2_body(httpx_mock, 1)
        assert '"Amount":1400.0' in body
        # Tracking refs the caller did not mention are carried over from the
        # line being replaced rather than silently dropped.
        assert '"ClassRef":{"value":"5000000000000041","name":"Residential"}' in body
        assert '"TaxCodeRef":{"value":"NON"}' in body

    @pytest.mark.asyncio
    async def test_explicit_class_beats_the_inherited_one(
        self, httpx_mock: Any
    ) -> None:
        existing = _b2_bill()
        existing["Line"][0]["AccountBasedExpenseLineDetail"]["ClassRef"] = {
            "value": "old-class"
        }
        httpx_mock.add_response(json={"Bill": existing})
        httpx_mock.add_response(json={"Bill": _b2_bill(SyncToken="1")})

        result_dict = await update_bill.ainvoke(
            _args(
                bill_id="890",
                lines=[
                    {
                        "line_id": "1",
                        "amount": 1250.0,
                        "account_id": "7",
                        "class_id": "new-class",
                    }
                ],
            )
        )

        result = UpdateBillOutput.model_validate(result_dict)
        assert result.success is True

        body = _b2_body(httpx_mock, 1)
        assert '"ClassRef":{"value":"new-class"}' in body
        assert "old-class" not in body

    @pytest.mark.asyncio
    async def test_replacement_line_without_a_counterpart_passes_through(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json={"Bill": _b2_bill()})
        httpx_mock.add_response(json={"Bill": _b2_bill(SyncToken="1")})

        result_dict = await update_bill.ainvoke(
            _args(
                bill_id="890",
                lines=[{"amount": 300.0, "account_id": "64", "description": "Fuel"}],
            )
        )

        result = UpdateBillOutput.model_validate(result_dict)
        assert result.success is True

        body = _b2_body(httpx_mock, 1)
        # A brand-new line has no line to inherit from, so nothing is invented.
        assert '"AccountRef":{"value":"64"}' in body
        assert '"Amount":300.0' in body
        assert "ClassRef" not in body
        assert "TaxCodeRef" not in body

    @pytest.mark.asyncio
    async def test_delete_bill(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            json={"Bill": {"Id": "890", "domain": "QBO", "status": "Deleted"}}
        )

        result_dict = await delete_bill.ainvoke(_args(bill_id="890", sync_token="1"))

        assert isinstance(result_dict, dict)
        result = DeleteBillOutput.model_validate(result_dict)
        assert result.success is True
        assert result.deleted is True
        assert result.bill_id == "890"
        assert result.status == "Deleted"
        assert httpx_mock.get_requests()[0].url.params["operation"] == "delete"

    @pytest.mark.asyncio
    async def test_search_bills(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json=_b2_query("Bill", [_b2_bill()]))

        result_dict = await search_bills.ainvoke(
            _args(vendor_id="56", unpaid_only=True, txn_date_from="2026-01-01")
        )

        assert isinstance(result_dict, dict)
        result = SearchBillsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.count == 1
        assert result.bills[0].vendor_name == "Norton Lumber"

        statement = httpx_mock.get_requests()[0].url.params["query"]
        assert "SELECT * FROM Bill WHERE" in statement
        assert "VendorRef = '56'" in statement
        assert "TxnDate >= '2026-01-01'" in statement
        assert "Balance > '0'" in statement


class TestBillPayments:
    @pytest.mark.asyncio
    async def test_create_bill_payment(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"BillPayment": _b2_bill_payment()})

        result_dict = await create_bill_payment.ainvoke(
            _args(
                vendor_id="56",
                total_amount=1250.0,
                pay_type="Check",
                bank_account_id="35",
                applied_bills=[{"bill_id": "890", "amount": 1250.0}],
                doc_number="1042",
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateBillPaymentOutput.model_validate(result_dict)
        assert result.success is True
        assert result.bill_payment is not None
        assert result.bill_payment.id == "915"
        assert result.bill_payment.pay_type == "Check"
        assert result.bill_payment.bank_account_name == "Checking"
        assert result.bill_payment.lines[0].linked_transactions[0].txn_id == "890"
        assert result.bill_payment.lines[0].linked_transactions[0].txn_type == "Bill"

        assert httpx_mock.get_requests()[0].url.path.endswith("/billpayment")
        body = _b2_body(httpx_mock)
        assert '"PayType":"Check"' in body
        assert '"CheckPayment":{"BankAccountRef":{"value":"35"}}' in body
        assert '"TxnType":"Bill"' in body

    @pytest.mark.asyncio
    async def test_create_bill_payment_check_needs_a_bank_account(
        self, httpx_mock: Any
    ) -> None:
        result_dict = await create_bill_payment.ainvoke(
            _args(vendor_id="56", total_amount=100.0, pay_type="Check")
        )

        result = CreateBillPaymentOutput.model_validate(result_dict)
        assert result.success is False
        assert result.error is not None
        assert "bank_account_id" in result.error
        assert httpx_mock.get_requests() == []

    @pytest.mark.asyncio
    async def test_get_bill_payment(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"BillPayment": _b2_bill_payment()})

        result_dict = await get_bill_payment.ainvoke(_args(bill_payment_id="915"))

        assert isinstance(result_dict, dict)
        result = GetBillPaymentOutput.model_validate(result_dict)
        assert result.success is True
        assert result.bill_payment is not None
        assert result.bill_payment.total_amount == 1250.0
        assert result.bill_payment.check_print_status == "NeedToPrint"
        assert httpx_mock.get_requests()[0].url.path.endswith("/billpayment/915")

    @pytest.mark.asyncio
    async def test_update_bill_payment(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            json={"BillPayment": _b2_bill_payment(SyncToken="1", DocNumber="1043")}
        )

        result_dict = await update_bill_payment.ainvoke(
            _args(bill_payment_id="915", doc_number="1043", sync_token="0")
        )

        assert isinstance(result_dict, dict)
        result = UpdateBillPaymentOutput.model_validate(result_dict)
        assert result.success is True
        assert result.bill_payment is not None
        assert result.bill_payment.doc_number == "1043"

        request = httpx_mock.get_requests()[0]
        assert request.url.params["operation"] == "update"
        assert '"sparse":true' in _b2_body(httpx_mock)

    @pytest.mark.asyncio
    async def test_delete_bill_payment(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            json={"BillPayment": {"Id": "915", "status": "Deleted"}}
        )

        result_dict = await delete_bill_payment.ainvoke(
            _args(bill_payment_id="915", sync_token="0")
        )

        assert isinstance(result_dict, dict)
        result = DeleteBillPaymentOutput.model_validate(result_dict)
        assert result.success is True
        assert result.deleted is True
        assert result.bill_payment_id == "915"
        assert httpx_mock.get_requests()[0].url.params["operation"] == "delete"

    @pytest.mark.asyncio
    async def test_search_bill_payments(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            json=_b2_query("BillPayment", [_b2_bill_payment()])
        )

        result_dict = await search_bill_payments.ainvoke(
            _args(vendor_id="56", txn_date_to="2026-01-31", start_position=1)
        )

        assert isinstance(result_dict, dict)
        result = SearchBillPaymentsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.count == 1
        assert result.bill_payments[0].vendor_id == "56"

        statement = httpx_mock.get_requests()[0].url.params["query"]
        assert "SELECT * FROM BillPayment WHERE" in statement
        assert "TxnDate <= '2026-01-31'" in statement
        assert "STARTPOSITION 1" in statement


class TestPayments:
    @pytest.mark.asyncio
    async def test_create_payment(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Payment": _b2_payment()})

        result_dict = await create_payment.ainvoke(
            _args(
                customer_id="20",
                total_amount=450.0,
                applied_invoices=[{"invoice_id": "129", "amount": 450.0}],
                payment_ref_num="7788",
            )
        )

        assert isinstance(result_dict, dict)
        result = CreatePaymentOutput.model_validate(result_dict)
        assert result.success is True
        assert result.payment is not None
        assert result.payment.id == "301"
        assert result.payment.customer_name == "Freeman Sporting Goods"
        assert result.payment.lines[0].linked_transactions[0].txn_type == "Invoice"

        assert httpx_mock.get_requests()[0].url.path.endswith("/payment")
        body = _b2_body(httpx_mock)
        assert '"CustomerRef":{"value":"20"}' in body
        assert '"TxnType":"Invoice"' in body
        # A customer receipt must never be built as a vendor payment.
        assert '"TxnType":"Bill"' not in body

    @pytest.mark.asyncio
    async def test_get_payment(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Payment": _b2_payment()})

        result_dict = await get_payment.ainvoke(_args(payment_id="301"))

        assert isinstance(result_dict, dict)
        result = GetPaymentOutput.model_validate(result_dict)
        assert result.success is True
        assert result.payment is not None
        assert result.payment.payment_ref_num == "7788"
        assert result.payment.unapplied_amount == 0.0
        assert result.payment.deposit_to_account_name == "Undeposited Funds"
        assert httpx_mock.get_requests()[0].url.path.endswith("/payment/301")

    @pytest.mark.asyncio
    async def test_update_payment(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            json={"Payment": _b2_payment(SyncToken="1", PrivateNote="Cleared")}
        )

        result_dict = await update_payment.ainvoke(
            _args(payment_id="301", private_note="Cleared", sync_token="0")
        )

        assert isinstance(result_dict, dict)
        result = UpdatePaymentOutput.model_validate(result_dict)
        assert result.success is True
        assert result.payment is not None
        assert result.payment.private_note == "Cleared"

        request = httpx_mock.get_requests()[0]
        assert request.url.params["operation"] == "update"
        assert '"sparse":true' in _b2_body(httpx_mock)

    @pytest.mark.asyncio
    async def test_delete_payment(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Payment": {"Id": "301", "status": "Deleted"}})

        result_dict = await delete_payment.ainvoke(
            _args(payment_id="301", sync_token="0")
        )

        assert isinstance(result_dict, dict)
        result = DeletePaymentOutput.model_validate(result_dict)
        assert result.success is True
        assert result.deleted is True
        assert result.payment_id == "301"
        assert httpx_mock.get_requests()[0].url.params["operation"] == "delete"

    @pytest.mark.asyncio
    async def test_search_payments(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json=_b2_query("Payment", [_b2_payment()]))

        result_dict = await search_payments.ainvoke(
            _args(customer_id="20", payment_ref_num="7788", max_results=10)
        )

        assert isinstance(result_dict, dict)
        result = SearchPaymentsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.count == 1
        assert result.payments[0].customer_id == "20"

        statement = httpx_mock.get_requests()[0].url.params["query"]
        assert "SELECT * FROM Payment WHERE" in statement
        assert "CustomerRef = '20'" in statement
        assert "PaymentRefNum = '7788'" in statement


class TestPurchases:
    @pytest.mark.asyncio
    async def test_create_purchase(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Purchase": _b2_purchase()})

        result_dict = await create_purchase.ainvoke(
            _args(
                account_id="35",
                payment_type="cash",
                lines=[{"amount": 10.0, "account_id": "13"}],
                entity_id="56",
                entity_type="Vendor",
            )
        )

        assert isinstance(result_dict, dict)
        result = CreatePurchaseOutput.model_validate(result_dict)
        assert result.success is True
        assert result.purchase is not None
        assert result.purchase.id == "252"
        assert result.purchase.payment_type == "Cash"
        assert result.purchase.account_name == "Checking"
        assert result.purchase.entity_type == "Vendor"
        assert result.purchase.lines[0].account_id == "13"

        body = _b2_body(httpx_mock)
        # PaymentType is normalized to the casing QuickBooks requires.
        assert '"PaymentType":"Cash"' in body
        assert '"AccountRef":{"value":"35"}' in body
        assert '"EntityRef":{"value":"56","type":"Vendor"}' in body

    @pytest.mark.asyncio
    async def test_create_purchase_rejects_an_unknown_payment_type(
        self, httpx_mock: Any
    ) -> None:
        result_dict = await create_purchase.ainvoke(
            _args(
                account_id="35",
                payment_type="Wire",
                lines=[{"amount": 10.0, "account_id": "13"}],
            )
        )

        result = CreatePurchaseOutput.model_validate(result_dict)
        assert result.success is False
        assert result.error is not None
        assert "Cash" in result.error
        assert httpx_mock.get_requests() == []

    @pytest.mark.asyncio
    async def test_get_purchase(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Purchase": _b2_purchase()})

        result_dict = await get_purchase.ainvoke(_args(purchase_id="252"))

        assert isinstance(result_dict, dict)
        result = GetPurchaseOutput.model_validate(result_dict)
        assert result.success is True
        assert result.purchase is not None
        assert result.purchase.total_amount == 10.0
        assert result.purchase.lines[0].account_name == "Meals and Entertainment"
        assert httpx_mock.get_requests()[0].url.path.endswith("/purchase/252")

    @pytest.mark.asyncio
    async def test_update_purchase(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            json={"Purchase": _b2_purchase(SyncToken="1", PrivateNote="Team lunch")}
        )

        result_dict = await update_purchase.ainvoke(
            _args(purchase_id="252", private_note="Team lunch", sync_token="0")
        )

        assert isinstance(result_dict, dict)
        result = UpdatePurchaseOutput.model_validate(result_dict)
        assert result.success is True
        assert result.purchase is not None
        assert result.purchase.private_note == "Team lunch"

        request = httpx_mock.get_requests()[0]
        assert request.url.params["operation"] == "update"
        assert '"sparse":true' in _b2_body(httpx_mock)

    @pytest.mark.asyncio
    async def test_delete_purchase(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Purchase": {"Id": "252", "status": "Deleted"}})

        result_dict = await delete_purchase.ainvoke(
            _args(purchase_id="252", sync_token="0")
        )

        assert isinstance(result_dict, dict)
        result = DeletePurchaseOutput.model_validate(result_dict)
        assert result.success is True
        assert result.deleted is True
        assert result.purchase_id == "252"
        assert httpx_mock.get_requests()[0].url.params["operation"] == "delete"

    @pytest.mark.asyncio
    async def test_search_purchases(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json=_b2_query("Purchase", [_b2_purchase()]))

        result_dict = await search_purchases.ainvoke(
            _args(txn_date_from="2026-01-01", max_total_amount=100.0, max_results=5)
        )

        assert isinstance(result_dict, dict)
        result = SearchPurchasesOutput.model_validate(result_dict)
        assert result.success is True
        assert result.count == 1
        assert result.purchases[0].payment_type == "Cash"

        statement = httpx_mock.get_requests()[0].url.params["query"]
        assert "SELECT * FROM Purchase WHERE" in statement
        assert "TxnDate >= '2026-01-01'" in statement
        assert "TotalAmt <= '100.0'" in statement
        assert statement.endswith("MAXRESULTS 5")


class TestPurchaseCycleSyncToken:
    @pytest.mark.asyncio
    async def test_omitted_sync_token_is_read_first(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Purchase": _b2_purchase(SyncToken="7")})
        httpx_mock.add_response(json={"Purchase": _b2_purchase(SyncToken="8")})

        result_dict = await update_purchase.ainvoke(
            _args(purchase_id="252", doc_number="CHK-77")
        )

        result = UpdatePurchaseOutput.model_validate(result_dict)
        assert result.success is True

        requests = httpx_mock.get_requests()
        assert len(requests) == 2
        assert requests[0].method == "GET"
        assert requests[0].url.path.endswith("/purchase/252")
        assert requests[1].method == "POST"
        assert requests[1].url.params["operation"] == "update"
        assert '"SyncToken":"7"' in _b2_body(httpx_mock, 1)

    @pytest.mark.asyncio
    async def test_explicit_sync_token_skips_the_read(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Purchase": {"Id": "252", "status": "Deleted"}})

        result_dict = await delete_purchase.ainvoke(
            _args(purchase_id="252", sync_token="12")
        )

        result = DeletePurchaseOutput.model_validate(result_dict)
        assert result.success is True

        requests = httpx_mock.get_requests()
        assert len(requests) == 1
        assert requests[0].method == "POST"
        assert '"SyncToken":"12"' in _b2_body(httpx_mock)


class TestPurchaseCycleEdgeCases:
    @pytest.mark.asyncio
    async def test_non_2xx_becomes_an_error_envelope(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            status_code=401,
            json={
                "Fault": {
                    "Error": [
                        {
                            "Message": "message=AuthenticationFailed",
                            "Detail": "Token expired",
                            "code": "3200",
                        }
                    ],
                    "type": "AUTHENTICATION",
                }
            },
        )

        result_dict = await get_vendor.ainvoke(_args(vendor_id="56"))

        result = GetVendorOutput.model_validate(result_dict)
        assert result.success is False
        assert result.vendor is None
        assert result.error is not None
        assert "3200" in result.error
        assert "401" in result.error

    @pytest.mark.asyncio
    async def test_fault_inside_http_200_is_an_error(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            status_code=200,
            json={
                "Fault": {
                    "Error": [
                        {
                            "Message": "Invalid Reference Id",
                            "Detail": "Vendor id 999 not found",
                            "code": "6240",
                        }
                    ],
                    "type": "ValidationFault"
                },
                "time": "2026-01-14T09:00:00-08:00",
            },
        )

        result_dict = await create_bill.ainvoke(
            _args(vendor_id="999", lines=[{"amount": 5.0, "account_id": "7"}])
        )

        result = CreateBillOutput.model_validate(result_dict)
        assert result.success is False
        assert result.bill is None
        assert result.error is not None
        assert "6240" in result.error
        assert "Vendor id 999 not found" in result.error

    @pytest.mark.asyncio
    async def test_empty_query_response_returns_no_rows(
        self, httpx_mock: Any
    ) -> None:
        # A search that matches nothing omits the entity key entirely.
        httpx_mock.add_response(
            json={"QueryResponse": {}, "time": "2026-01-14T09:00:00-08:00"}
        )

        result_dict = await search_bill_payments.ainvoke(_args(vendor_id="404"))

        result = SearchBillPaymentsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.bill_payments == []
        assert result.count == 0
        assert result.start_position is None

    @pytest.mark.asyncio
    async def test_unexpected_field_types_still_succeed(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(
            json={
                "Purchase": {
                    "Id": 252,
                    "SyncToken": 3,
                    "TotalAmt": "not-a-number",
                    "PaymentType": ["Cash"],
                    "AccountRef": "35",
                    "Credit": "yes",
                    "Line": "oops",
                    "MetaData": [],
                }
            }
        )

        result_dict = await get_purchase.ainvoke(_args(purchase_id="252"))

        result = GetPurchaseOutput.model_validate(result_dict)
        assert result.success is True
        assert result.error is None
        assert result.purchase is not None
        # Numbers arriving as text and refs arriving as bare strings degrade
        # to None instead of raising after the request already succeeded.
        assert result.purchase.id == "252"
        assert result.purchase.sync_token == "3"
        assert result.purchase.total_amount is None
        assert result.purchase.payment_type is None
        assert result.purchase.account_id is None
        assert result.purchase.credit is None
        assert result.purchase.lines == []
        assert result.purchase.created_at is None


_B3_ITEM: dict[str, Any] = {
    "Id": "19",
    "SyncToken": "3",
    "Name": "Rock Fountain",
    "FullyQualifiedName": "Rock Fountain",
    "Sku": "RF-001",
    "Description": "Rock fountain for the garden",
    "PurchaseDesc": "Rock fountain",
    "Type": "Inventory",
    "Active": True,
    "Taxable": True,
    "UnitPrice": 275.0,
    "PurchaseCost": 125.0,
    "TrackQtyOnHand": True,
    "QtyOnHand": 2.0,
    "ReorderPoint": 1.0,
    "InvStartDate": "2026-01-01",
    "SubItem": False,
    "Level": 0,
    "IncomeAccountRef": {"value": "79", "name": "Sales of Product Income"},
    "ExpenseAccountRef": {"value": "80", "name": "Cost of Goods Sold"},
    "AssetAccountRef": {"value": "81", "name": "Inventory Asset"},
    "MetaData": {
        "CreateTime": "2026-01-02T09:00:00-08:00",
        "LastUpdatedTime": "2026-02-03T10:11:12-08:00",
    },
}

_B3_ACCOUNT: dict[str, Any] = {
    "Id": "94",
    "SyncToken": "0",
    "Name": "Savings",
    "FullyQualifiedName": "Savings",
    "Description": "Business savings",
    "AccountType": "Bank",
    "AccountSubType": "Savings",
    "Classification": "Asset",
    "AcctNum": "1200",
    "Active": True,
    "SubAccount": False,
    "CurrentBalance": 4500.25,
    "CurrentBalanceWithSubAccounts": 4500.25,
    "CurrencyRef": {"value": "USD", "name": "United States Dollar"},
    "sparse": False,
    "MetaData": {
        "CreateTime": "2026-01-02T09:00:00-08:00",
        "LastUpdatedTime": "2026-02-03T10:11:12-08:00",
    },
}

_B3_COMPANY: dict[str, Any] = {
    "Id": "9341454816484523",
    "SyncToken": "4",
    "CompanyName": "Larry's Landscaping",
    "LegalName": "Larry's Landscaping LLC",
    "Country": "US",
    "CompanyStartDate": "2024-01-01",
    "FiscalYearStartMonth": "January",
    "SupportedLanguages": "en",
    "DefaultTimeZone": "America/Los_Angeles",
    "CompanyAddr": {
        "Id": "1",
        "Line1": "123 Sierra Way",
        "City": "San Pablo",
        "CountrySubDivisionCode": "CA",
        "PostalCode": "87999",
    },
    "Email": {"Address": "books@example.com"},
    "WebAddr": {"URI": "https://example.com"},
    "PrimaryPhone": {"FreeFormNumber": "(555) 555-5555"},
    "NameValue": [{"Name": "IndustryType", "Value": "Landscaping Services"}],
    "MetaData": {
        "CreateTime": "2024-01-02T09:00:00-08:00",
        "LastUpdatedTime": "2026-02-03T10:11:12-08:00",
    },
}

_B3_REPORT: dict[str, Any] = {
    "Header": {
        "Time": "2026-03-01T09:00:00-08:00",
        "ReportName": "BalanceSheet",
        "StartPeriod": "2026-01-01",
        "EndPeriod": "2026-03-01",
        "Currency": "USD",
        "Option": [{"Name": "AccountingStandard", "Value": "GAAP"}],
    },
    "Columns": {
        "Column": [
            {"ColTitle": "", "ColType": "Account"},
            {"ColTitle": "Total", "ColType": "Money"},
        ]
    },
    "Rows": {
        "Row": [
            {
                "type": "Section",
                "group": "TotalAssets",
                "Rows": {
                    "Row": [
                        {
                            "type": "Data",
                            "ColData": [
                                {"value": "Checking", "id": "35"},
                                {"value": "1201.00"},
                            ],
                        }
                    ]
                },
            }
        ]
    },
}


def _b3_report(name: str) -> dict[str, Any]:
    """A report payload whose header names the report under test."""
    payload = dict(_B3_REPORT)
    payload["Header"] = dict(_B3_REPORT["Header"], ReportName=name)
    return payload


def _b3_body(request: Any) -> dict[str, Any]:
    """Decode the JSON body a recorded request carried."""
    import json

    decoded: dict[str, Any] = json.loads(request.content)
    return decoded


class TestItems:
    @pytest.mark.asyncio
    async def test_create_item_builds_the_reference_stanzas(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Item": _B3_ITEM})

        result_dict = await create_item.ainvoke(
            _args(
                name="Rock Fountain",
                item_type="Inventory",
                income_account_id="79",
                expense_account_id="80",
                asset_account_id="81",
                track_qty_on_hand=True,
                qty_on_hand=2,
                inv_start_date="2026-01-01",
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateItemOutput.model_validate(result_dict)
        assert result.success is True
        assert result.item is not None
        assert result.item.id == "19"
        assert result.item.item_type == "Inventory"
        assert result.item.income_account_id == "79"
        assert result.item.income_account_name == "Sales of Product Income"
        assert result.item.created_at == "2026-01-02T09:00:00-08:00"
        request = httpx_mock.get_requests()[0]
        assert request.method == "POST"
        assert str(request.url).split("?")[0].endswith("/item")
        body = _b3_body(request)
        assert body["Type"] == "Inventory"
        assert body["IncomeAccountRef"] == {"value": "79"}
        assert body["AssetAccountRef"] == {"value": "81"}
        # Unset fields never reach the wire, so a create cannot blank a default.
        assert "Description" not in body

    @pytest.mark.asyncio
    async def test_get_item_returns_the_record(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Item": _B3_ITEM})

        result_dict = await get_item.ainvoke(_args(item_id="19"))

        assert isinstance(result_dict, dict)
        result = GetItemOutput.model_validate(result_dict)
        assert result.success is True
        assert result.item is not None
        assert result.item.name == "Rock Fountain"
        assert result.item.unit_price == 275.0
        assert result.item.qty_on_hand == 2.0
        assert str(httpx_mock.get_requests()[0].url).split("?")[0].endswith("/item/19")

    @pytest.mark.asyncio
    async def test_update_item_resolves_the_sync_token_and_sends_a_sparse_body(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json={"Item": _B3_ITEM})
        httpx_mock.add_response(json={"Item": dict(_B3_ITEM, SyncToken="4", UnitPrice=299.0)})

        result_dict = await update_item.ainvoke(
            _args(item_id="19", name="Rock Fountain", unit_price=299.0)
        )

        assert isinstance(result_dict, dict)
        result = UpdateItemOutput.model_validate(result_dict)
        assert result.success is True
        assert result.item is not None
        assert result.item.unit_price == 299.0
        requests = httpx_mock.get_requests()
        # One read to lift the SyncToken, then the write.
        assert len(requests) == 2
        assert requests[0].method == "GET"
        assert "operation=update" in str(requests[1].url)
        body = _b3_body(requests[1])
        assert body["Id"] == "19"
        assert body["SyncToken"] == "3"
        assert body["sparse"] is True
        assert body["UnitPrice"] == 299.0

    @pytest.mark.asyncio
    async def test_update_item_with_an_explicit_sync_token_skips_the_read(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json={"Item": dict(_B3_ITEM, SyncToken="8")})

        result_dict = await update_item.ainvoke(
            _args(item_id="19", name="Rock Fountain", sync_token="7")
        )

        assert result_dict["success"] is True
        requests = httpx_mock.get_requests()
        assert len(requests) == 1
        assert _b3_body(requests[0])["SyncToken"] == "7"

    @pytest.mark.asyncio
    async def test_delete_item_deactivates_rather_than_deleting(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json={"Item": dict(_B3_ITEM, Active=False, SyncToken="4")})

        result_dict = await delete_item.ainvoke(_args(item_id="19", sync_token="3"))

        assert isinstance(result_dict, dict)
        result = DeleteItemOutput.model_validate(result_dict)
        assert result.success is True
        assert result.item is not None
        assert result.item.active is False
        requests = httpx_mock.get_requests()
        assert len(requests) == 1
        # QuickBooks has no hard delete for items: this is a sparse update
        # that flips Active, not an operation=delete call.
        assert "operation=update" in str(requests[0].url)
        body = _b3_body(requests[0])
        assert body["Active"] is False
        assert body["sparse"] is True
        assert body["SyncToken"] == "3"

    @pytest.mark.asyncio
    async def test_search_items_builds_the_filtered_statement(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(
            json={
                "QueryResponse": {
                    "Item": [_B3_ITEM],
                    "startPosition": 1,
                    "maxResults": 1,
                }
            }
        )

        result_dict = await search_items.ainvoke(
            _args(name="Rock Fountain", item_type="Inventory", active=True, max_results=10)
        )

        assert isinstance(result_dict, dict)
        result = SearchItemsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.count == 1
        assert result.items[0].sku == "RF-001"
        assert result.start_position == 1
        assert result.max_results == 1
        query = dict(httpx_mock.get_requests()[0].url.params)["query"]
        assert query == (
            "SELECT * FROM Item WHERE Name = 'Rock Fountain' AND Type = 'Inventory' "
            "AND Active = true MAXRESULTS 10"
        )


class TestAccounts:
    @pytest.mark.asyncio
    async def test_create_account_nests_under_a_parent(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Account": _B3_ACCOUNT})

        result_dict = await create_account.ainvoke(
            _args(
                name="Savings",
                account_type="Bank",
                account_sub_type="Savings",
                parent_account_id="35",
            )
        )

        assert isinstance(result_dict, dict)
        result = CreateAccountOutput.model_validate(result_dict)
        assert result.success is True
        assert result.account is not None
        assert result.account.id == "94"
        assert result.account.classification == "Asset"
        assert result.account.current_balance == 4500.25
        assert result.account.currency_code == "USD"
        body = _b3_body(httpx_mock.get_requests()[0])
        assert body["AccountType"] == "Bank"
        assert body["SubAccount"] is True
        assert body["ParentRef"] == {"value": "35"}

    @pytest.mark.asyncio
    async def test_get_account_returns_the_record(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Account": _B3_ACCOUNT})

        result_dict = await get_account.ainvoke(_args(account_id="94"))

        assert isinstance(result_dict, dict)
        result = GetAccountOutput.model_validate(result_dict)
        assert result.success is True
        assert result.account is not None
        assert result.account.name == "Savings"
        assert result.account.account_sub_type == "Savings"
        assert str(httpx_mock.get_requests()[0].url).split("?")[0].endswith("/account/94")

    @pytest.mark.asyncio
    async def test_update_account_sends_a_full_body_carrying_the_existing_fields(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json={"Account": _B3_ACCOUNT})
        httpx_mock.add_response(json={"Account": dict(_B3_ACCOUNT, Active=False, SyncToken="1")})

        result_dict = await update_account.ainvoke(_args(account_id="94", active=False))

        assert isinstance(result_dict, dict)
        result = UpdateAccountOutput.model_validate(result_dict)
        assert result.success is True
        assert result.account is not None
        assert result.account.active is False
        requests = httpx_mock.get_requests()
        assert len(requests) == 2
        body = _b3_body(requests[1])
        # Account rejects a sparse write, so the read-back fields ride along
        # and the sparse marker from the read response is stripped.
        assert "sparse" not in body
        assert body["Name"] == "Savings"
        assert body["AccountType"] == "Bank"
        assert body["SyncToken"] == "0"
        assert body["Active"] is False

    @pytest.mark.asyncio
    async def test_search_accounts_escapes_caller_supplied_literals(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json={"QueryResponse": {"Account": [_B3_ACCOUNT]}})

        result_dict = await search_accounts.ainvoke(
            _args(name="Bob's Burgers", account_type="Bank", start_position=11)
        )

        assert isinstance(result_dict, dict)
        result = SearchAccountsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.count == 1
        assert result.accounts[0].fully_qualified_name == "Savings"
        query = dict(httpx_mock.get_requests()[0].url.params)["query"]
        # The apostrophe is escaped, so it cannot terminate the literal early.
        assert query == (
            "SELECT * FROM Account WHERE Name = 'Bob\\'s Burgers' "
            "AND AccountType = 'Bank' STARTPOSITION 11"
        )


class TestCompanyProfile:
    @pytest.mark.asyncio
    async def test_get_company_info_addresses_the_realm_twice(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json={"CompanyInfo": _B3_COMPANY})

        result_dict = await get_company_info.ainvoke(_args())

        assert isinstance(result_dict, dict)
        result = GetCompanyInfoOutput.model_validate(result_dict)
        assert result.success is True
        assert result.company_info is not None
        assert result.company_info.company_name == "Larry's Landscaping"
        assert result.company_info.email == "books@example.com"
        assert result.company_info.web_addr == "https://example.com"
        assert result.company_info.primary_phone == "(555) 555-5555"
        assert result.company_info.company_addr is not None
        assert result.company_info.company_addr.city == "San Pablo"
        assert result.company_info.name_values[0]["Name"] == "IndustryType"
        # The realm is both the company path segment and the record id.
        assert str(httpx_mock.get_requests()[0].url).split("?")[0].endswith(
            "/company/9341454816484523/companyinfo/9341454816484523"
        )

    @pytest.mark.asyncio
    async def test_update_company_info_sends_a_sparse_body_with_the_realm_as_id(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json={"CompanyInfo": _B3_COMPANY})
        httpx_mock.add_response(
            json={"CompanyInfo": dict(_B3_COMPANY, CompanyName="Acme Books", SyncToken="5")}
        )

        result_dict = await update_company_info.ainvoke(
            _args(company_name="Acme Books", address_city="Oakland")
        )

        assert isinstance(result_dict, dict)
        result = UpdateCompanyInfoOutput.model_validate(result_dict)
        assert result.success is True
        assert result.company_info is not None
        assert result.company_info.company_name == "Acme Books"
        requests = httpx_mock.get_requests()
        assert len(requests) == 2
        assert "operation=update" in str(requests[1].url)
        body = _b3_body(requests[1])
        assert body["Id"] == "9341454816484523"
        assert body["SyncToken"] == "4"
        assert body["sparse"] is True
        assert body["CompanyAddr"] == {"City": "Oakland"}


class TestRawQuery:
    @pytest.mark.asyncio
    async def test_run_query_passes_the_statement_through_untouched(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(
            json={
                "QueryResponse": {
                    "Invoice": [{"Id": "130", "TotalAmt": 150.0}],
                    "startPosition": 1,
                    "maxResults": 1,
                },
                "time": "2026-03-01T09:00:00-08:00",
            }
        )

        statement = "SELECT * FROM Invoice WHERE TotalAmt > '100' MAXRESULTS 5"
        result_dict = await run_query.ainvoke(_args(query=statement))

        assert isinstance(result_dict, dict)
        result = RunQueryOutput.model_validate(result_dict)
        assert result.success is True
        assert result.entity_name == "Invoice"
        assert result.count == 1
        assert result.rows[0]["Id"] == "130"
        assert result.start_position == 1
        # The caller wrote the statement deliberately; it is not re-escaped.
        assert dict(httpx_mock.get_requests()[0].url.params)["query"] == statement

    @pytest.mark.asyncio
    async def test_run_query_reports_a_count_statement(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"QueryResponse": {"totalCount": 42}})

        result_dict = await run_query.ainvoke(_args(query="SELECT COUNT(*) FROM Invoice"))

        result = RunQueryOutput.model_validate(result_dict)
        assert result.success is True
        assert result.total_count == 42
        assert result.entity_name is None
        assert result.rows == []


class TestReports:
    @pytest.mark.asyncio
    async def test_get_balance_sheet_report_returns_the_row_tree(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json=_b3_report("BalanceSheet"))

        result_dict = await get_balance_sheet_report.ainvoke(
            _args(
                end_date="2026-03-01",
                accounting_method="Accrual",
                customer_ids=["1", "2"],
                class_ids=["7"],
            )
        )

        assert isinstance(result_dict, dict)
        result = GetBalanceSheetReportOutput.model_validate(result_dict)
        assert result.success is True
        assert result.report is not None
        assert result.report.report_name == "BalanceSheet"
        assert result.report.currency == "USD"
        assert result.report.start_period == "2026-01-01"
        assert len(result.report.columns) == 2
        # Rows nest: the section keeps its own Rows rather than being flattened.
        assert result.report.rows[0]["group"] == "TotalAssets"
        assert result.report.rows[0]["Rows"]["Row"][0]["type"] == "Data"
        request = httpx_mock.get_requests()[0]
        assert "/reports/BalanceSheet" in str(request.url)
        params = dict(request.url.params)
        assert params["customer"] == "1,2"
        assert params["class"] == "7"
        assert params["accounting_method"] == "Accrual"

    @pytest.mark.asyncio
    async def test_get_profit_and_loss_report_returns_the_report(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json=_b3_report("ProfitAndLoss"))

        result_dict = await get_profit_and_loss_report.ainvoke(
            _args(
                start_date="2026-01-01",
                end_date="2026-03-01",
                summarize_column_by="Month",
                account_ids=["79", "80"],
                payment_method="Visa",
            )
        )

        assert isinstance(result_dict, dict)
        result = GetProfitAndLossReportOutput.model_validate(result_dict)
        assert result.success is True
        assert result.report is not None
        assert result.report.report_name == "ProfitAndLoss"
        params = dict(httpx_mock.get_requests()[0].url.params)
        assert "/reports/ProfitAndLoss" in str(httpx_mock.get_requests()[0].url)
        assert params["account"] == "79,80"
        assert params["summarize_column_by"] == "Month"
        assert params["payment_method"] == "Visa"

    @pytest.mark.asyncio
    async def test_get_trial_balance_report_returns_the_report(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json=_b3_report("TrialBalance"))

        result_dict = await get_trial_balance_report.ainvoke(
            _args(start_date="2026-01-01", end_date="2026-03-01", accounting_method="Cash")
        )

        assert isinstance(result_dict, dict)
        result = GetTrialBalanceReportOutput.model_validate(result_dict)
        assert result.success is True
        assert result.report is not None
        assert result.report.report_name == "TrialBalance"
        request = httpx_mock.get_requests()[0]
        assert "/reports/TrialBalance" in str(request.url)
        assert dict(request.url.params)["accounting_method"] == "Cash"

    @pytest.mark.asyncio
    async def test_get_cash_flow_report_returns_the_report(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json=_b3_report("CashFlow"))

        result_dict = await get_cash_flow_report.ainvoke(
            _args(date_macro="Last Fiscal Year", summarize_column_by="Quarter")
        )

        assert isinstance(result_dict, dict)
        result = GetCashFlowReportOutput.model_validate(result_dict)
        assert result.success is True
        assert result.report is not None
        assert result.report.report_name == "CashFlow"
        request = httpx_mock.get_requests()[0]
        assert "/reports/CashFlow" in str(request.url)
        assert dict(request.url.params)["date_macro"] == "Last Fiscal Year"

    @pytest.mark.asyncio
    async def test_get_customer_balance_report_returns_the_report(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json=_b3_report("CustomerBalance"))

        result_dict = await get_customer_balance_report.ainvoke(
            _args(report_date="2026-03-01", customer_ids=["1"])
        )

        assert isinstance(result_dict, dict)
        result = GetCustomerBalanceReportOutput.model_validate(result_dict)
        assert result.success is True
        assert result.report is not None
        assert result.report.report_name == "CustomerBalance"
        request = httpx_mock.get_requests()[0]
        assert "/reports/CustomerBalance" in str(request.url)
        assert dict(request.url.params)["customer"] == "1"

    @pytest.mark.asyncio
    async def test_get_vendor_balance_report_returns_the_report(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json=_b3_report("VendorBalance"))

        result_dict = await get_vendor_balance_report.ainvoke(
            _args(report_date="2026-03-01", vendor_ids=["30", "31"])
        )

        assert isinstance(result_dict, dict)
        result = GetVendorBalanceReportOutput.model_validate(result_dict)
        assert result.success is True
        assert result.report is not None
        assert result.report.report_name == "VendorBalance"
        request = httpx_mock.get_requests()[0]
        assert "/reports/VendorBalance" in str(request.url)
        assert dict(request.url.params)["vendor"] == "30,31"

    @pytest.mark.asyncio
    async def test_get_vendor_expenses_report_returns_the_report(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json=_b3_report("VendorExpenses"))

        result_dict = await get_vendor_expenses_report.ainvoke(
            _args(
                start_date="2026-01-01",
                end_date="2026-03-01",
                accounting_method="Accrual",
                summarize_column_by="Total",
            )
        )

        assert isinstance(result_dict, dict)
        result = GetVendorExpensesReportOutput.model_validate(result_dict)
        assert result.success is True
        assert result.report is not None
        assert result.report.report_name == "VendorExpenses"
        request = httpx_mock.get_requests()[0]
        assert "/reports/VendorExpenses" in str(request.url)
        assert dict(request.url.params)["summarize_column_by"] == "Total"

    @pytest.mark.asyncio
    async def test_get_ap_aging_report_returns_the_report(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json=_b3_report("AgedPayables"))

        result_dict = await get_ap_aging_report.ainvoke(
            _args(report_date="2026-03-01", num_periods=4, aging_period=30, past_due=1)
        )

        assert isinstance(result_dict, dict)
        result = GetApAgingReportOutput.model_validate(result_dict)
        assert result.success is True
        assert result.report is not None
        assert result.report.report_name == "AgedPayables"
        request = httpx_mock.get_requests()[0]
        assert "/reports/AgedPayables" in str(request.url)
        params = dict(request.url.params)
        assert params["num_periods"] == "4"
        assert params["aging_period"] == "30"
        assert params["past_due"] == "1"

    @pytest.mark.asyncio
    async def test_a_report_with_no_rows_is_still_a_success(
        self, httpx_mock: Any
    ) -> None:
        # A period with no activity answers 200 with an empty Rows wrapper.
        httpx_mock.add_response(
            json={"Header": {"ReportName": "TrialBalance"}, "Columns": {}, "Rows": {}}
        )

        result_dict = await get_trial_balance_report.ainvoke(_args())

        result = GetTrialBalanceReportOutput.model_validate(result_dict)
        assert result.success is True
        assert result.report is not None
        assert result.report.rows == []
        assert result.report.columns == []


class TestLedgerFailures:
    @pytest.mark.asyncio
    async def test_a_non_2xx_folds_into_the_error_envelope(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            status_code=404,
            json={
                "Fault": {
                    "type": "ValidationFault",
                    "Error": [
                        {
                            "Message": "Object Not Found",
                            "Detail": "Object Not Found : Something went wrong",
                            "code": "610",
                        }
                    ],
                }
            },
        )

        result_dict = await get_item.ainvoke(_args(item_id="99999"))

        assert isinstance(result_dict, dict)
        result = GetItemOutput.model_validate(result_dict)
        assert result.success is False
        assert result.item is None
        assert result.error is not None
        assert "Object Not Found" in result.error
        assert "610" in result.error
        assert "404" in result.error

    @pytest.mark.asyncio
    async def test_a_fault_inside_http_200_fails_a_write(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(
            status_code=200,
            json={
                "Fault": {
                    "type": "ValidationFault",
                    "Error": [
                        {
                            "Message": "Duplicate Name Exists Error",
                            "Detail": "The name supplied already exists",
                            "code": "6240",
                        }
                    ],
                }
            },
        )

        result_dict = await create_item.ainvoke(
            _args(name="Rock Fountain", item_type="Service", income_account_id="79")
        )

        result = CreateItemOutput.model_validate(result_dict)
        assert result.success is False
        assert result.item is None
        assert result.error is not None
        assert "Duplicate Name Exists Error" in result.error
        assert "6240" in result.error

    @pytest.mark.asyncio
    async def test_an_empty_query_response_is_a_successful_empty_page(
        self, httpx_mock: Any
    ) -> None:
        # No match omits the entity key entirely rather than sending [].
        httpx_mock.add_response(
            json={"QueryResponse": {}, "time": "2026-03-01T09:00:00-08:00"}
        )

        result_dict = await search_items.ainvoke(_args(sku="does-not-exist"))

        result = SearchItemsOutput.model_validate(result_dict)
        assert result.success is True
        assert result.items == []
        assert result.count == 0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_wrongly_typed_fields_degrade_instead_of_raising(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(
            json={
                "Item": {
                    "Id": 19,
                    "SyncToken": 3,
                    "Name": ["not", "a", "string"],
                    "UnitPrice": "275.00",
                    "Active": "yes",
                    "QtyOnHand": None,
                    "Level": 1.5,
                    "MetaData": "nope",
                    "IncomeAccountRef": "79",
                }
            }
        )

        result_dict = await get_item.ainvoke(_args(item_id="19"))

        result = GetItemOutput.model_validate(result_dict)
        assert result.success is True
        assert result.item is not None
        assert result.item.id == "19"
        assert result.item.sync_token == "3"
        assert result.item.name is None
        assert result.item.unit_price == 275.0
        assert result.item.active is None
        assert result.item.qty_on_hand is None
        assert result.item.level is None
        assert result.item.created_at is None
        assert result.item.income_account_id is None

    @pytest.mark.asyncio
    async def test_a_failed_sync_token_read_stops_before_the_write(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(status_code=401, text="unauthorized")

        result_dict = await delete_item.ainvoke(_args(item_id="19"))

        result = DeleteItemOutput.model_validate(result_dict)
        assert result.success is False
        assert result.error is not None
        assert "401" in result.error
        assert len(httpx_mock.get_requests()) == 1

class TestSharedTransport:
    """The request contract every one of the actions shares."""

    def test_environment_selects_the_host_from_a_closed_map(self) -> None:
        # A value that reaches the netloc is an SSRF vector, so it is looked
        # up rather than interpolated; anything unknown falls back to prod.
        prod = {"realm_id": "123"}
        assert _base_url(prod).startswith("https://quickbooks.api.intuit.com")
        assert _base_url(dict(prod, environment="sandbox")).startswith(
            "https://sandbox-quickbooks.api.intuit.com"
        )
        assert _base_url(dict(prod, environment="  SANDBOX ")).startswith(
            "https://sandbox-quickbooks.api.intuit.com"
        )
        assert _base_url(dict(prod, environment="evil.example.com")).startswith(
            "https://quickbooks.api.intuit.com"
        )

    def test_realm_id_is_encoded_into_the_path(self) -> None:
        assert _base_url({"realm_id": "../../evil"}).endswith("/company/..%2F..%2Fevil")

    @pytest.mark.asyncio
    async def test_every_request_pins_minorversion_and_format(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json={"CompanyInfo": {"Id": "1"}})

        await get_company_info.ainvoke(_args())

        params = dict(httpx_mock.get_requests()[0].url.params)
        assert params["minorversion"] == "75"
        assert params["format"] == "json"

    @pytest.mark.asyncio
    async def test_a_fault_inside_http_200_is_an_error(
        self, httpx_mock: Any
    ) -> None:
        # QuickBooks reports validation problems with a 200 and a Fault body.
        httpx_mock.add_response(
            status_code=200,
            json={
                "Fault": {
                    "type": "ValidationFault",
                    "Error": [
                        {
                            "Message": "Duplicate Document Number Error",
                            "Detail": "You must specify a different number",
                            "code": "6140",
                        }
                    ],
                }
            },
        )

        result_dict = await get_company_info.ainvoke(_args())

        assert isinstance(result_dict, dict)
        assert result_dict["success"] is False
        error = str(result_dict["error"])
        assert "Duplicate Document Number Error" in error
        assert "6140" in error

    @pytest.mark.asyncio
    async def test_missing_token_short_circuits_before_any_request(self) -> None:
        result_dict = await get_company_info.ainvoke(
            {"auth_type": "oauth2", "auth_data": {"realm_id": "123"}}
        )

        assert result_dict["success"] is False
        assert "token" in str(result_dict["error"]).lower()

    @pytest.mark.asyncio
    async def test_missing_realm_short_circuits_before_any_request(self) -> None:
        result_dict = await get_company_info.ainvoke(
            {"auth_type": "oauth2", "auth_data": {"access_token": "t"}}
        )

        assert result_dict["success"] is False
        assert "company id" in str(result_dict["error"]).lower()



class TestFaultDetection:
    """A fault must be a failure however its detail happens to serialize."""

    @pytest.mark.asyncio
    async def test_a_single_unwrapped_error_object_is_still_a_failure(
        self, httpx_mock: Any
    ) -> None:
        # This API is XML-derived, so a single repeated element can serialize
        # as a bare object instead of a one-element array. Keying on the
        # presence of Fault rather than on parsing its contents is what stops
        # a rejected write from being reported as a success.
        httpx_mock.add_response(
            status_code=200,
            json={
                "Fault": {
                    "type": "ValidationFault",
                    "Error": {"Message": "Invalid Reference Id", "code": "6240"},
                }
            },
        )

        result_dict = await get_company_info.ainvoke(_args())

        assert result_dict["success"] is False
        assert "6240" in str(result_dict["error"])
        assert "Invalid Reference Id" in str(result_dict["error"])

    @pytest.mark.asyncio
    async def test_an_unreadable_fault_is_still_a_failure(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(status_code=200, json={"Fault": {"Error": []}})

        result_dict = await get_company_info.ainvoke(_args())

        assert result_dict["success"] is False
        assert result_dict["error"] is not None

    @pytest.mark.asyncio
    async def test_a_non_object_fault_is_still_a_failure(
        self, httpx_mock: Any
    ) -> None:
        # The failure signal is the Fault *key*, not a parseable Fault value.
        httpx_mock.add_response(status_code=200, json={"Fault": "boom"})

        result_dict = await get_company_info.ainvoke(_args())

        assert result_dict["success"] is False
        assert result_dict["error"] is not None

    @pytest.mark.asyncio
    async def test_a_null_fault_is_still_a_failure(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(status_code=200, json={"Fault": None})

        result_dict = await get_company_info.ainvoke(_args())

        assert result_dict["success"] is False

    @pytest.mark.asyncio
    async def test_a_clean_response_is_not_mistaken_for_a_fault(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json={"CompanyInfo": {"Id": "1", "CompanyName": "Acme"}})

        result_dict = await get_company_info.ainvoke(_args())

        assert result_dict["success"] is True


class TestPathSegmentSafety:
    """An id must never be able to address something the caller did not name."""

    @pytest.mark.asyncio
    async def test_a_dot_id_cannot_reach_the_parent_collection(
        self, httpx_mock: Any
    ) -> None:
        # `.` and `..` are in quote()'s always-safe set, so encoding alone
        # leaves them as dot segments that httpx resolves away.
        httpx_mock.add_response(json={"Invoice": {"Id": "1"}})

        await get_invoice.ainvoke(_args(invoice_id="."))

        path = httpx_mock.get_requests()[0].url.path
        assert not path.endswith("/invoice")
        assert path.endswith("/invoice/invalid-id")

    @pytest.mark.asyncio
    async def test_a_double_dot_id_cannot_drop_the_entity_segment(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json={"Invoice": {"Id": "1"}})

        await get_invoice.ainvoke(_args(invoice_id=".."))

        assert "/invoice/invalid-id" in httpx_mock.get_requests()[0].url.path

    @pytest.mark.asyncio
    async def test_an_empty_id_cannot_collapse_onto_the_collection(
        self, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json={"Invoice": {"Id": "1"}})

        await get_invoice.ainvoke(_args(invoice_id=""))

        assert httpx_mock.get_requests()[0].url.path.endswith("/invoice/invalid-id")

    @pytest.mark.asyncio
    async def test_a_traversal_id_stays_one_segment(self, httpx_mock: Any) -> None:
        httpx_mock.add_response(json={"Invoice": {"Id": "1"}})

        await get_invoice.ainvoke(_args(invoice_id="../../oauth/token"))

        url = str(httpx_mock.get_requests()[0].url)
        assert "/oauth/token" not in url
        assert "..%2F..%2Foauth%2Ftoken" in url


class TestCredentialHygiene:
    @pytest.mark.asyncio
    async def test_a_whitespace_only_token_never_reaches_the_wire(self) -> None:
        result_dict = await get_company_info.ainvoke(
            {
                "auth_type": "oauth2",
                "auth_data": {"access_token": "   ", "realm_id": "123"},
            }
        )

        assert result_dict["success"] is False
        assert "token" in str(result_dict["error"]).lower()

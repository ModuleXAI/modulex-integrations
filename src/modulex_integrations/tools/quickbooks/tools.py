"""QuickBooks Online LangChain ``@tool`` functions.

Pure HTTP integration against the QuickBooks Online Accounting API v3.
Credentials arrive as ``auth_type, auth_data`` (first args); ``auth_data``
carries the OAuth 2.0 ``access_token`` plus the ``realm_id`` of the company
the token was issued for.

Every endpoint is scoped to one company, so the realm ID is a
credential-level fact rather than a per-call decision and is read from
``auth_data`` instead of being exposed as an action parameter.

Three things about this API shape the whole module:

* **A 200 can be a failure.** QuickBooks answers validation problems with
  HTTP 200 and a ``Fault.Error[]`` array in the body. ``_request`` treats a
  non-empty fault as an error so no caller has to remember to check.
* **Writes need a SyncToken.** Updates and deletes use optimistic
  concurrency: the body must carry ``Id`` and the record's *current*
  ``SyncToken``. ``_resolve_sync_token`` fetches it when the caller does not
  supply one.
* **Updates are sparse.** ``sparse: true`` means only the supplied fields
  change; without it QuickBooks blanks every omitted field.

Error model: nothing raises past the ``@tool`` boundary. Transport failures,
non-2xx responses, faults inside a 200, and malformed bodies all fold into
one ``success=False`` + ``error`` envelope. Response values are routed
through the ``_as_*`` coercers before reaching a pydantic model, so a field
that arrives with an unexpected *type* degrades to ``None`` instead of
raising ``ValidationError`` after the request already succeeded.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.quickbooks.outputs import (
    AccountRecord,
    BillPaymentRecord,
    BillRecord,
    CompanyInfoAddress,
    CompanyInfoRecord,
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
    CreditMemoRecord,
    CustomerRecord,
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
    EstimateRecord,
    ExpenseLineItem,
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
    InvoiceRecord,
    ItemRecord,
    LinkedTxnLine,
    LinkedTxnRef,
    PaymentRecord,
    PurchaseRecord,
    ReportResult,
    RunQueryOutput,
    SalesLineItem,
    SalesReceiptRecord,
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
    VendorAddress,
    VendorRecord,
    VoidInvoiceOutput,
)

__all__ = [
    "create_account",
    "create_bill",
    "create_bill_payment",
    "create_credit_memo",
    "create_customer",
    "create_estimate",
    "create_invoice",
    "create_item",
    "create_payment",
    "create_purchase",
    "create_sales_receipt",
    "create_vendor",
    "delete_bill",
    "delete_bill_payment",
    "delete_credit_memo",
    "delete_customer",
    "delete_estimate",
    "delete_invoice",
    "delete_item",
    "delete_payment",
    "delete_purchase",
    "delete_sales_receipt",
    "delete_vendor",
    "get_account",
    "get_ap_aging_report",
    "get_balance_sheet_report",
    "get_bill",
    "get_bill_payment",
    "get_cash_flow_report",
    "get_company_info",
    "get_credit_memo",
    "get_customer",
    "get_customer_balance_report",
    "get_estimate",
    "get_invoice",
    "get_item",
    "get_payment",
    "get_profit_and_loss_report",
    "get_purchase",
    "get_sales_receipt",
    "get_trial_balance_report",
    "get_vendor",
    "get_vendor_balance_report",
    "get_vendor_expenses_report",
    "run_query",
    "search_accounts",
    "search_bill_payments",
    "search_bills",
    "search_credit_memos",
    "search_customers",
    "search_estimates",
    "search_invoices",
    "search_items",
    "search_payments",
    "search_purchases",
    "search_sales_receipts",
    "search_vendors",
    "send_estimate",
    "send_invoice",
    "update_account",
    "update_bill",
    "update_bill_payment",
    "update_company_info",
    "update_credit_memo",
    "update_customer",
    "update_estimate",
    "update_invoice",
    "update_item",
    "update_payment",
    "update_purchase",
    "update_sales_receipt",
    "update_vendor",
    "void_invoice",
]

# The environment selects between two different hosts, so it is resolved
# through a closed map — a value interpolated into the netloc would be an
# SSRF vector, and anything unrecognised falls back to production.
_HOSTS: dict[str, str] = {
    "production": "https://quickbooks.api.intuit.com",
    "sandbox": "https://sandbox-quickbooks.api.intuit.com",
}
_DEFAULT_ENVIRONMENT = "production"

# Pinned deliberately. The API is versioned through this query parameter and
# raising it can change response shapes, so it is a considered upgrade rather
# than a default that drifts.
_MINOR_VERSION = "75"
_TIMEOUT = 30.0

_MISSING_TOKEN = "QuickBooks access token is missing. Reconnect the integration."
_MISSING_REALM = (
    "QuickBooks company ID is missing. Set QUICKBOOKS_REALM_ID on the credential."
)


# --- Credentials ------------------------------------------------------------


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build the standard header set. Empty dict when the token is absent."""
    token = (_as_str(auth_data.get("access_token")) or "").strip()
    if not token:
        return {}
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _realm_id(auth_data: dict[str, Any]) -> str:
    """Resolve the company (realm) ID.

    ``inject_into_auth_data`` normalizes ``QUICKBOOKS_REALM_ID`` to the
    ``realm_id`` key. The ``realmId`` fallback covers the raw field name
    QuickBooks returns on the OAuth callback, in case the runtime ever
    persists it verbatim.
    """
    raw = auth_data.get("realm_id") or auth_data.get("realmId")
    return (_as_str(raw) or "").strip()


def _base_url(auth_data: dict[str, Any]) -> str:
    """Company-scoped API root for the credential's environment."""
    raw = _as_str(auth_data.get("environment")) or ""
    host = _HOSTS.get(raw.strip().lower(), _HOSTS[_DEFAULT_ENVIRONMENT])
    return f"{host}/v3/company/{quote(_realm_id(auth_data), safe='')}"


# A path segment that cannot name a QuickBooks record — record Ids are numeric.
_INERT_SEGMENT = "invalid-id"


def _seg(value: str) -> str:
    """Percent-encode one path segment.

    ``quote`` treats ``.`` as always-safe, so a bare ``.`` or ``..`` survives
    as a dot segment and httpx resolves it while building the URL — pointing
    the request at a resource the caller never named (``.`` collapses
    ``/invoice/{id}`` onto the ``/invoice`` collection, ``..`` drops the
    entity segment entirely). An empty value collapses the same way. All
    three become a segment that cannot match a record, so the call fails
    cleanly through the normal error envelope instead of addressing
    something else.
    """
    encoded = quote(value, safe="")
    return _INERT_SEGMENT if encoded in {"", ".", ".."} else encoded


# --- Response coercion ------------------------------------------------------
#
# The envelope invariant: no code path between ``response.json()`` and the
# ``return`` may raise. ``_request`` guards the parse; these guard the types.


def _as_dict(payload: Any) -> dict[str, Any]:
    """A non-object value degrades to empty rather than raising."""
    return payload if isinstance(payload, dict) else {}


def _as_list(payload: Any) -> list[Any]:
    """A non-array value degrades to empty rather than raising."""
    return payload if isinstance(payload, list) else []


def _as_str(value: Any) -> str | None:
    if value is None or isinstance(value, (dict, list, bool)):
        return None
    return value if isinstance(value, str) else str(value)


def _as_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _as_int(value: Any) -> int | None:
    """Coerce a JSON number to ``int``.

    QuickBooks declares counters and positions as plain JSON numbers, so a
    value can arrive as ``7.0`` just as easily as ``7``. An integral float is
    accepted; a genuinely fractional value degrades to ``None`` rather than
    being silently truncated.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _as_float(value: Any) -> float | None:
    """Monetary amounts arrive as JSON numbers; strings are tolerated too."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _as_str_list(value: Any) -> list[str]:
    return [item for item in _as_list(value) if isinstance(item, str)]


def _as_dict_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in _as_list(value) if isinstance(item, dict)]


def _ref(value: Any) -> str | None:
    """Read the ``value`` out of a QuickBooks ``*Ref`` stanza.

    References are ``{"value": "42", "name": "Acme"}``; callers almost always
    want the ID.
    """
    return _as_str(_as_dict(value).get("value"))


def _ref_name(value: Any) -> str | None:
    """Read the display ``name`` out of a QuickBooks ``*Ref`` stanza."""
    return _as_str(_as_dict(value).get("name"))


# --- Request ----------------------------------------------------------------


def _clean_params(params: dict[str, Any] | None) -> dict[str, Any]:
    """Drop unset query params."""
    if not params:
        return {}
    return {k: v for k, v in params.items() if v is not None and v != ""}


def _clean_body(body: dict[str, Any] | None) -> dict[str, Any]:
    """Drop unset body fields so a sparse update never blanks a value."""
    if not body:
        return {}
    return {k: v for k, v in body.items() if v is not None}


def _fault_text(payload: Any) -> str | None:
    """Turn a ``Fault`` stanza into one readable sentence, or None.

    QuickBooks reports validation problems inside an HTTP 200, so this is
    checked on success responses too. ``code`` is surfaced because that is
    what Intuit support asks for.

    The *presence* of the ``Fault`` key is the failure signal; reading the
    detail out of it is best effort. ``Error`` is documented as an array,
    but this API is XML-derived and a single repeated element can serialize
    as a bare object — so a fault must never degrade into a successful empty
    result just because its detail was unreadable. A successful response
    never carries a ``Fault`` key at all.
    """
    body = _as_dict(payload)
    if "Fault" not in body:
        return None
    fault = _as_dict(body.get("Fault"))
    raw = fault.get("Error")
    errors = _as_dict_list(raw)
    if not errors and isinstance(raw, dict):
        errors = [raw]
    kind = _as_str(fault.get("type")) or "Fault"
    if not errors:
        return f"QuickBooks {kind}: the response carried a fault with no readable detail."
    parts: list[str] = []
    for item in errors:
        message = _as_str(item.get("Message")) or ""
        detail = _as_str(item.get("Detail")) or ""
        code = _as_str(item.get("code")) or ""
        text = " — ".join(p for p in (message, detail) if p) or "unspecified error"
        parts.append(f"{text} (code {code})" if code else text)
    return f"QuickBooks {kind}: " + "; ".join(parts)


def _error_text(response: httpx.Response) -> str:
    """Turn a non-2xx into one readable sentence."""
    try:
        payload = response.json()
    except (ValueError, httpx.DecodingError):
        payload = None
    detail = _fault_text(payload)
    if detail:
        return f"{detail} (HTTP {response.status_code})"
    body = (response.text or "").strip()[:300]
    return (
        f"QuickBooks API error {response.status_code}: {body}"
        if body
        else f"QuickBooks API error {response.status_code}"
    )


async def _request(
    auth_type: str,
    auth_data: dict[str, Any],
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    send_body: bool = False,
) -> tuple[Any, str | None]:
    """Perform one Accounting API call.

    Returns ``(payload, None)`` on success or ``(None, error)`` on any
    failure — transport, non-2xx, a fault inside a 200, or an unparseable
    body. Never raises, so every caller can build its success model
    unconditionally after the ``error is not None`` early return.

    ``send_body`` forces a JSON body even when it cleans down to ``{}``.
    """
    headers = _get_auth_headers(auth_type, auth_data)
    if not headers:
        return None, _MISSING_TOKEN
    if not _realm_id(auth_data):
        return None, _MISSING_REALM

    query = _clean_params(params)
    query.setdefault("minorversion", _MINOR_VERSION)
    query.setdefault("format", "json")

    body = _clean_body(json_body)
    kwargs: dict[str, Any] = {"headers": headers, "params": query}
    if send_body or body:
        kwargs["json"] = body

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.request(
                method, f"{_base_url(auth_data)}{path}", **kwargs
            )
    except httpx.HTTPError as exc:
        return None, f"QuickBooks request failed: {exc}"

    if response.status_code >= 400:
        return None, _error_text(response)

    if not response.content:
        return {}, None
    try:
        payload = response.json()
    except (ValueError, httpx.DecodingError):
        return None, "QuickBooks returned a non-JSON response body."

    # A 200 carrying a fault is still a failure.
    fault = _fault_text(payload)
    if fault:
        return None, fault
    return payload, None


def _entity(payload: Any, name: str) -> dict[str, Any]:
    """Unwrap ``{"<EntityName>": {...}}`` into the entity object."""
    return _as_dict(_as_dict(payload).get(name))


def _query_rows(payload: Any, name: str) -> list[dict[str, Any]]:
    """Unwrap ``{"QueryResponse": {"<EntityName>": [...]}}``.

    A search that matches nothing returns ``{"QueryResponse": {}}`` with the
    entity key absent entirely rather than an empty array, so this must go
    through the coercers rather than indexing.
    """
    return _as_dict_list(_as_dict(_as_dict(payload).get("QueryResponse")).get(name))


def _escape_sql(value: str) -> str:
    """Escape a literal for a QuickBooks query string.

    Query filters are assembled into a SQL-like statement, so a raw quote in
    a caller-supplied value would change the statement's meaning.
    """
    return value.replace("\\", "\\\\").replace("'", "\\'")


async def _resolve_sync_token(
    auth_type: str,
    auth_data: dict[str, Any],
    entity_path: str,
    entity_name: str,
    record_id: str,
    sync_token: str | None,
) -> tuple[str | None, str | None]:
    """Return the SyncToken to write with, fetching it when not supplied.

    QuickBooks rejects an update or delete whose ``SyncToken`` is stale, so
    the caller may pass the current one to save a round trip. When they do
    not, read the record and lift it. Returns ``(token, error)``.
    """
    if sync_token:
        return sync_token, None
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/{entity_path}/{_seg(record_id)}"
    )
    if error is not None:
        return None, error
    current = _as_str(_entity(payload, entity_name).get("SyncToken"))
    if current is None:
        return None, (
            f"QuickBooks did not return a SyncToken for {entity_name} {record_id}; "
            "pass sync_token explicitly."
        )
    return current, None


def _parse_sales_line(raw: Any) -> SalesLineItem:
    """Map one ``Line`` entry of a sales transaction onto a flat model."""
    row = _as_dict(raw)
    detail = _as_dict(row.get("SalesItemLineDetail"))
    return SalesLineItem(
        line_id=_as_str(row.get("Id")),
        line_number=_as_int(row.get("LineNum")),
        description=_as_str(row.get("Description")),
        amount=_as_float(row.get("Amount")),
        detail_type=_as_str(row.get("DetailType")),
        item_id=_ref(detail.get("ItemRef")),
        item_name=_ref_name(detail.get("ItemRef")),
        quantity=_as_float(detail.get("Qty")),
        unit_price=_as_float(detail.get("UnitPrice")),
        tax_code_id=_ref(detail.get("TaxCodeRef")),
        service_date=_as_str(detail.get("ServiceDate")),
    )


def _build_sales_lines(line_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build the QuickBooks ``Line`` array from curated line-item dicts.

    Callers describe *what was sold* (item, quantity, unit price); the
    ``DetailType`` / ``SalesItemLineDetail`` nesting QuickBooks wants is
    assembled here so no caller has to hand-write the vendor's JSON. The
    line amount defaults to ``qty * unit_price`` — the same arithmetic the
    QuickBooks UI performs — and an explicit ``amount`` overrides it.
    """
    lines: list[dict[str, Any]] = []
    for index, item in enumerate(_as_dict_list(line_items), start=1):
        quantity = _as_float(item.get("qty"))
        unit_price = _as_float(item.get("unit_price"))
        amount = _as_float(item.get("amount"))
        if amount is None and quantity is not None and unit_price is not None:
            amount = quantity * unit_price
        detail: dict[str, Any] = {"Qty": quantity, "UnitPrice": unit_price}
        item_id = _as_str(item.get("item_ref")) or _as_str(item.get("item_id"))
        if item_id:
            detail["ItemRef"] = {"value": item_id}
        tax_code_id = _as_str(item.get("tax_code_ref")) or _as_str(item.get("tax_code_id"))
        if tax_code_id:
            detail["TaxCodeRef"] = {"value": tax_code_id}
        service_date = _as_str(item.get("service_date"))
        if service_date:
            detail["ServiceDate"] = service_date
        line: dict[str, Any] = {
            "LineNum": index,
            "Description": _as_str(item.get("description")),
            "Amount": amount,
            "DetailType": "SalesItemLineDetail",
            "SalesItemLineDetail": _clean_body(detail),
        }
        lines.append(_clean_body(line))
    return lines


def _build_sales_address(address: dict[str, Any] | None) -> dict[str, Any] | None:
    """Turn a flat address dict into a QuickBooks ``PhysicalAddress``.

    Both the friendly names (``line1``, ``city``, ``state``,
    ``postal_code``, ``country``) and QuickBooks' own field names are
    accepted, so echoing back an address that came out of a read works.
    """
    row = _as_dict(address)
    if not row:
        return None

    def pick(*names: str) -> str | None:
        for name in names:
            value = _as_str(row.get(name))
            if value:
                return value
        return None

    mapped: dict[str, Any] = {
        "Line1": pick("line1", "Line1", "street", "address1"),
        "Line2": pick("line2", "Line2", "address2"),
        "City": pick("city", "City"),
        "CountrySubDivisionCode": pick("state", "region", "CountrySubDivisionCode"),
        "PostalCode": pick("postal_code", "zip", "PostalCode"),
        "Country": pick("country", "Country"),
    }
    return _clean_body(mapped) or None


def _sales_query_suffix(max_results: int | None, start_position: int | None) -> str:
    """Render the pagination tail of a query statement.

    QuickBooks expects ``STARTPOSITION`` before ``MAXRESULTS``; both are
    keywords rather than bindable values, so only integers reach them.
    """
    suffix = ""
    if start_position is not None and start_position > 0:
        suffix += f" STARTPOSITION {start_position}"
    if max_results is not None and max_results > 0:
        suffix += f" MAXRESULTS {max_results}"
    return suffix


def _parse_invoice(raw: Any) -> InvoiceRecord:
    """Map one QuickBooks ``Invoice`` object onto :class:`InvoiceRecord`."""
    row = _as_dict(raw)
    meta = _as_dict(row.get("MetaData"))
    return InvoiceRecord(
        invoice_id=_as_str(row.get("Id")),
        sync_token=_as_str(row.get("SyncToken")),
        doc_number=_as_str(row.get("DocNumber")),
        txn_date=_as_str(row.get("TxnDate")),
        due_date=_as_str(row.get("DueDate")),
        ship_date=_as_str(row.get("ShipDate")),
        customer_id=_ref(row.get("CustomerRef")),
        customer_name=_ref_name(row.get("CustomerRef")),
        customer_memo=_as_str(_as_dict(row.get("CustomerMemo")).get("value")),
        private_note=_as_str(row.get("PrivateNote")),
        bill_email=_as_str(_as_dict(row.get("BillEmail")).get("Address")),
        bill_address=_as_dict(row.get("BillAddr")) or None,
        ship_address=_as_dict(row.get("ShipAddr")) or None,
        currency=_ref(row.get("CurrencyRef")),
        exchange_rate=_as_float(row.get("ExchangeRate")),
        total_amount=_as_float(row.get("TotalAmt")),
        balance=_as_float(row.get("Balance")),
        home_balance=_as_float(row.get("HomeBalance")),
        deposit=_as_float(row.get("Deposit")),
        total_tax=_as_float(_as_dict(row.get("TxnTaxDetail")).get("TotalTax")),
        txn_status=_as_str(row.get("TxnStatus")),
        email_status=_as_str(row.get("EmailStatus")),
        print_status=_as_str(row.get("PrintStatus")),
        global_tax_calculation=_as_str(row.get("GlobalTaxCalculation")),
        apply_tax_after_discount=_as_bool(row.get("ApplyTaxAfterDiscount")),
        allow_online_credit_card_payment=_as_bool(row.get("AllowOnlineCreditCardPayment")),
        allow_online_ach_payment=_as_bool(row.get("AllowOnlineACHPayment")),
        invoice_link=_as_str(row.get("InvoiceLink")),
        tracking_number=_as_str(row.get("TrackingNum")),
        sales_term_id=_ref(row.get("SalesTermRef")),
        lines=[_parse_sales_line(line) for line in _as_dict_list(row.get("Line"))],
        linked_transactions=_as_dict_list(row.get("LinkedTxn")),
        created_time=_as_str(meta.get("CreateTime")),
        last_updated_time=_as_str(meta.get("LastUpdatedTime")),
    )


def _parse_customer(raw: Any) -> CustomerRecord:
    """Map one QuickBooks ``Customer`` object onto :class:`CustomerRecord`."""
    row = _as_dict(raw)
    meta = _as_dict(row.get("MetaData"))
    return CustomerRecord(
        customer_id=_as_str(row.get("Id")),
        sync_token=_as_str(row.get("SyncToken")),
        display_name=_as_str(row.get("DisplayName")),
        fully_qualified_name=_as_str(row.get("FullyQualifiedName")),
        company_name=_as_str(row.get("CompanyName")),
        print_on_check_name=_as_str(row.get("PrintOnCheckName")),
        title=_as_str(row.get("Title")),
        given_name=_as_str(row.get("GivenName")),
        middle_name=_as_str(row.get("MiddleName")),
        family_name=_as_str(row.get("FamilyName")),
        suffix=_as_str(row.get("Suffix")),
        active=_as_bool(row.get("Active")),
        taxable=_as_bool(row.get("Taxable")),
        job=_as_bool(row.get("Job")),
        bill_with_parent=_as_bool(row.get("BillWithParent")),
        parent_id=_ref(row.get("ParentRef")),
        level=_as_int(row.get("Level")),
        primary_email=_as_str(_as_dict(row.get("PrimaryEmailAddr")).get("Address")),
        primary_phone=_as_str(_as_dict(row.get("PrimaryPhone")).get("FreeFormNumber")),
        alternate_phone=_as_str(_as_dict(row.get("AlternatePhone")).get("FreeFormNumber")),
        mobile=_as_str(_as_dict(row.get("Mobile")).get("FreeFormNumber")),
        fax=_as_str(_as_dict(row.get("Fax")).get("FreeFormNumber")),
        website=_as_str(_as_dict(row.get("WebAddr")).get("URI")),
        bill_address=_as_dict(row.get("BillAddr")) or None,
        ship_address=_as_dict(row.get("ShipAddr")) or None,
        notes=_as_str(row.get("Notes")),
        balance=_as_float(row.get("Balance")),
        balance_with_jobs=_as_float(row.get("BalanceWithJobs")),
        open_balance_date=_as_str(row.get("OpenBalanceDate")),
        currency=_ref(row.get("CurrencyRef")),
        preferred_delivery_method=_as_str(row.get("PreferredDeliveryMethod")),
        resale_number=_as_str(row.get("ResaleNum")),
        account_number=_as_str(row.get("AcctNum")),
        default_tax_code_id=_ref(row.get("DefaultTaxCodeRef")),
        sales_term_id=_ref(row.get("SalesTermRef")),
        payment_method_id=_ref(row.get("PaymentMethodRef")),
        customer_type_id=_ref(row.get("CustomerTypeRef")),
        created_time=_as_str(meta.get("CreateTime")),
        last_updated_time=_as_str(meta.get("LastUpdatedTime")),
    )


def _parse_estimate(raw: Any) -> EstimateRecord:
    """Map one QuickBooks ``Estimate`` object onto :class:`EstimateRecord`."""
    row = _as_dict(raw)
    meta = _as_dict(row.get("MetaData"))
    return EstimateRecord(
        estimate_id=_as_str(row.get("Id")),
        sync_token=_as_str(row.get("SyncToken")),
        doc_number=_as_str(row.get("DocNumber")),
        txn_date=_as_str(row.get("TxnDate")),
        expiration_date=_as_str(row.get("ExpirationDate")),
        accepted_by=_as_str(row.get("AcceptedBy")),
        accepted_date=_as_str(row.get("AcceptedDate")),
        txn_status=_as_str(row.get("TxnStatus")),
        customer_id=_ref(row.get("CustomerRef")),
        customer_name=_ref_name(row.get("CustomerRef")),
        customer_memo=_as_str(_as_dict(row.get("CustomerMemo")).get("value")),
        private_note=_as_str(row.get("PrivateNote")),
        bill_email=_as_str(_as_dict(row.get("BillEmail")).get("Address")),
        bill_address=_as_dict(row.get("BillAddr")) or None,
        ship_address=_as_dict(row.get("ShipAddr")) or None,
        currency=_ref(row.get("CurrencyRef")),
        exchange_rate=_as_float(row.get("ExchangeRate")),
        total_amount=_as_float(row.get("TotalAmt")),
        total_tax=_as_float(_as_dict(row.get("TxnTaxDetail")).get("TotalTax")),
        email_status=_as_str(row.get("EmailStatus")),
        print_status=_as_str(row.get("PrintStatus")),
        global_tax_calculation=_as_str(row.get("GlobalTaxCalculation")),
        apply_tax_after_discount=_as_bool(row.get("ApplyTaxAfterDiscount")),
        lines=[_parse_sales_line(line) for line in _as_dict_list(row.get("Line"))],
        linked_transactions=_as_dict_list(row.get("LinkedTxn")),
        created_time=_as_str(meta.get("CreateTime")),
        last_updated_time=_as_str(meta.get("LastUpdatedTime")),
    )


def _parse_sales_receipt(raw: Any) -> SalesReceiptRecord:
    """Map one ``SalesReceipt`` object onto :class:`SalesReceiptRecord`."""
    row = _as_dict(raw)
    meta = _as_dict(row.get("MetaData"))
    return SalesReceiptRecord(
        sales_receipt_id=_as_str(row.get("Id")),
        sync_token=_as_str(row.get("SyncToken")),
        doc_number=_as_str(row.get("DocNumber")),
        txn_date=_as_str(row.get("TxnDate")),
        customer_id=_ref(row.get("CustomerRef")),
        customer_name=_ref_name(row.get("CustomerRef")),
        customer_memo=_as_str(_as_dict(row.get("CustomerMemo")).get("value")),
        private_note=_as_str(row.get("PrivateNote")),
        bill_email=_as_str(_as_dict(row.get("BillEmail")).get("Address")),
        bill_address=_as_dict(row.get("BillAddr")) or None,
        ship_address=_as_dict(row.get("ShipAddr")) or None,
        currency=_ref(row.get("CurrencyRef")),
        exchange_rate=_as_float(row.get("ExchangeRate")),
        total_amount=_as_float(row.get("TotalAmt")),
        balance=_as_float(row.get("Balance")),
        total_tax=_as_float(_as_dict(row.get("TxnTaxDetail")).get("TotalTax")),
        payment_method_id=_ref(row.get("PaymentMethodRef")),
        payment_reference_number=_as_str(row.get("PaymentRefNum")),
        deposit_to_account_id=_ref(row.get("DepositToAccountRef")),
        email_status=_as_str(row.get("EmailStatus")),
        print_status=_as_str(row.get("PrintStatus")),
        global_tax_calculation=_as_str(row.get("GlobalTaxCalculation")),
        apply_tax_after_discount=_as_bool(row.get("ApplyTaxAfterDiscount")),
        lines=[_parse_sales_line(line) for line in _as_dict_list(row.get("Line"))],
        created_time=_as_str(meta.get("CreateTime")),
        last_updated_time=_as_str(meta.get("LastUpdatedTime")),
    )


def _parse_credit_memo(raw: Any) -> CreditMemoRecord:
    """Map one ``CreditMemo`` object onto :class:`CreditMemoRecord`."""
    row = _as_dict(raw)
    meta = _as_dict(row.get("MetaData"))
    return CreditMemoRecord(
        credit_memo_id=_as_str(row.get("Id")),
        sync_token=_as_str(row.get("SyncToken")),
        doc_number=_as_str(row.get("DocNumber")),
        txn_date=_as_str(row.get("TxnDate")),
        customer_id=_ref(row.get("CustomerRef")),
        customer_name=_ref_name(row.get("CustomerRef")),
        customer_memo=_as_str(_as_dict(row.get("CustomerMemo")).get("value")),
        private_note=_as_str(row.get("PrivateNote")),
        bill_email=_as_str(_as_dict(row.get("BillEmail")).get("Address")),
        bill_address=_as_dict(row.get("BillAddr")) or None,
        ship_address=_as_dict(row.get("ShipAddr")) or None,
        currency=_ref(row.get("CurrencyRef")),
        exchange_rate=_as_float(row.get("ExchangeRate")),
        total_amount=_as_float(row.get("TotalAmt")),
        balance=_as_float(row.get("Balance")),
        remaining_credit=_as_float(row.get("RemainingCredit")),
        total_tax=_as_float(_as_dict(row.get("TxnTaxDetail")).get("TotalTax")),
        email_status=_as_str(row.get("EmailStatus")),
        print_status=_as_str(row.get("PrintStatus")),
        global_tax_calculation=_as_str(row.get("GlobalTaxCalculation")),
        apply_tax_after_discount=_as_bool(row.get("ApplyTaxAfterDiscount")),
        lines=[_parse_sales_line(line) for line in _as_dict_list(row.get("Line"))],
        created_time=_as_str(meta.get("CreateTime")),
        last_updated_time=_as_str(meta.get("LastUpdatedTime")),
    )


# --- Invoices ---------------------------------------------------------------


class CreateInvoiceInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    customer_id: str = Field(description="ID of the customer being billed")
    line_items: list[dict[str, Any]] = Field(
        description=(
            "What is being billed. Each object accepts item_ref (the QuickBooks "
            "Item ID), qty, unit_price, description, tax_code_ref (a TaxCode ID, "
            "or TAX/NON in the US) and service_date (YYYY-MM-DD). The line total "
            "defaults to qty * unit_price; pass amount to override it"
        )
    )
    txn_date: str | None = Field(
        default=None, description="Invoice date as YYYY-MM-DD. Defaults to today"
    )
    due_date: str | None = Field(
        default=None,
        description="Date the payment is due as YYYY-MM-DD. Defaults to the sales term",
    )
    doc_number: str | None = Field(
        default=None,
        description="Reference number for the transaction. Auto-assigned when omitted",
    )
    bill_email: str | None = Field(
        default=None,
        description="Email address the invoice is addressed to. Defaults to the customer's",
    )
    customer_memo: str | None = Field(
        default=None, description="Message shown to the customer on the invoice"
    )
    private_note: str | None = Field(
        default=None, description="Internal note. Never shown to the customer"
    )
    currency_code: str | None = Field(
        default=None,
        description="ISO 4217 code such as USD or EUR. Required if multicurrency is enabled",
    )
    sales_term_id: str | None = Field(
        default=None,
        description="ID of the SalesTerm (payment terms). Falls back to the customer's default",
    )
    bill_address: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Billing address. Keys: line1, line2, city, state, postal_code, country"
        ),
    )
    ship_address: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Shipping address. Keys: line1, line2, city, state, postal_code, country"
        ),
    )
    global_tax_calculation: str | None = Field(
        default=None,
        description=(
            "How tax applies to the lines: TaxExcluded, TaxInclusive or "
            "NotApplicable. Non-US companies only"
        ),
    )


@tool(args_schema=CreateInvoiceInput)
@serialize_pydantic_return
async def create_invoice(
    auth_type: str,
    auth_data: dict[str, Any],
    customer_id: str,
    line_items: list[dict[str, Any]],
    txn_date: str | None = None,
    due_date: str | None = None,
    doc_number: str | None = None,
    bill_email: str | None = None,
    customer_memo: str | None = None,
    private_note: str | None = None,
    currency_code: str | None = None,
    sales_term_id: str | None = None,
    bill_address: dict[str, Any] | None = None,
    ship_address: dict[str, Any] | None = None,
    global_tax_calculation: str | None = None,
) -> CreateInvoiceOutput:
    """Create an invoice billing a customer for one or more items.

    Records money the customer now owes. Use ``create_sales_receipt``
    instead when the sale was already paid for.
    """
    body: dict[str, Any] = {
        "CustomerRef": {"value": customer_id},
        "Line": _build_sales_lines(line_items),
        "TxnDate": txn_date,
        "DueDate": due_date,
        "DocNumber": doc_number,
        "PrivateNote": private_note,
        "GlobalTaxCalculation": global_tax_calculation,
        "BillAddr": _build_sales_address(bill_address),
        "ShipAddr": _build_sales_address(ship_address),
    }
    if bill_email:
        body["BillEmail"] = {"Address": bill_email}
    if customer_memo:
        body["CustomerMemo"] = {"value": customer_memo}
    if currency_code:
        body["CurrencyRef"] = {"value": currency_code}
    if sales_term_id:
        body["SalesTermRef"] = {"value": sales_term_id}

    payload, error = await _request(auth_type, auth_data, "POST", "/invoice", json_body=body)
    if error is not None:
        return CreateInvoiceOutput(success=False, error=error)
    entity = _entity(payload, "Invoice")
    return CreateInvoiceOutput(
        success=True, invoice=_parse_invoice(entity) if entity else None
    )


class GetInvoiceInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    invoice_id: str = Field(description="ID of the invoice to read")


@tool(args_schema=GetInvoiceInput)
@serialize_pydantic_return
async def get_invoice(
    auth_type: str,
    auth_data: dict[str, Any],
    invoice_id: str,
) -> GetInvoiceOutput:
    """Read one invoice by its ID, including its line items and balance."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/invoice/{_seg(invoice_id)}"
    )
    if error is not None:
        return GetInvoiceOutput(success=False, error=error)
    entity = _entity(payload, "Invoice")
    return GetInvoiceOutput(success=True, invoice=_parse_invoice(entity) if entity else None)


class UpdateInvoiceInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    invoice_id: str = Field(description="ID of the invoice to update")
    customer_id: str | None = Field(
        default=None, description="ID of the customer the invoice is billed to"
    )
    line_items: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Replacement line items. Supplying this REPLACES every existing "
            "line, so include the lines you want to keep. Each object accepts "
            "item_ref, qty, unit_price, description, tax_code_ref and "
            "service_date"
        ),
    )
    txn_date: str | None = Field(default=None, description="Invoice date as YYYY-MM-DD")
    due_date: str | None = Field(default=None, description="Payment due date as YYYY-MM-DD")
    doc_number: str | None = Field(
        default=None, description="Reference number for the transaction"
    )
    bill_email: str | None = Field(
        default=None, description="Email address the invoice is addressed to"
    )
    customer_memo: str | None = Field(
        default=None, description="Message shown to the customer on the invoice"
    )
    private_note: str | None = Field(default=None, description="Internal note")
    currency_code: str | None = Field(
        default=None, description="ISO 4217 code such as USD or EUR"
    )
    sales_term_id: str | None = Field(
        default=None, description="ID of the SalesTerm (payment terms)"
    )
    bill_address: dict[str, Any] | None = Field(
        default=None,
        description="Billing address. Keys: line1, line2, city, state, postal_code, country",
    )
    ship_address: dict[str, Any] | None = Field(
        default=None,
        description="Shipping address. Keys: line1, line2, city, state, postal_code, country",
    )
    global_tax_calculation: str | None = Field(
        default=None,
        description="TaxExcluded, TaxInclusive or NotApplicable. Non-US companies only",
    )
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request"
        ),
    )


@tool(args_schema=UpdateInvoiceInput)
@serialize_pydantic_return
async def update_invoice(
    auth_type: str,
    auth_data: dict[str, Any],
    invoice_id: str,
    customer_id: str | None = None,
    line_items: list[dict[str, Any]] | None = None,
    txn_date: str | None = None,
    due_date: str | None = None,
    doc_number: str | None = None,
    bill_email: str | None = None,
    customer_memo: str | None = None,
    private_note: str | None = None,
    currency_code: str | None = None,
    sales_term_id: str | None = None,
    bill_address: dict[str, Any] | None = None,
    ship_address: dict[str, Any] | None = None,
    global_tax_calculation: str | None = None,
    sync_token: str | None = None,
) -> UpdateInvoiceOutput:
    """Change fields on an existing invoice, leaving the rest untouched.

    This is a sparse update: only the values supplied here change. To email
    the invoice use ``send_invoice``; to cancel it use ``void_invoice``.
    """
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "invoice", "Invoice", invoice_id, sync_token
    )
    if error is not None:
        return UpdateInvoiceOutput(success=False, error=error)

    body: dict[str, Any] = {
        "Id": invoice_id,
        "SyncToken": token,
        "sparse": True,
        "TxnDate": txn_date,
        "DueDate": due_date,
        "DocNumber": doc_number,
        "PrivateNote": private_note,
        "GlobalTaxCalculation": global_tax_calculation,
        "BillAddr": _build_sales_address(bill_address),
        "ShipAddr": _build_sales_address(ship_address),
    }
    if customer_id:
        body["CustomerRef"] = {"value": customer_id}
    if line_items is not None:
        body["Line"] = _build_sales_lines(line_items)
    if bill_email:
        body["BillEmail"] = {"Address": bill_email}
    if customer_memo:
        body["CustomerMemo"] = {"value": customer_memo}
    if currency_code:
        body["CurrencyRef"] = {"value": currency_code}
    if sales_term_id:
        body["SalesTermRef"] = {"value": sales_term_id}

    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/invoice",
        params={"operation": "update"},
        json_body=body,
    )
    if error is not None:
        return UpdateInvoiceOutput(success=False, error=error)
    entity = _entity(payload, "Invoice")
    return UpdateInvoiceOutput(
        success=True, invoice=_parse_invoice(entity) if entity else None
    )


class DeleteInvoiceInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    invoice_id: str = Field(description="ID of the invoice to delete")
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request"
        ),
    )


@tool(args_schema=DeleteInvoiceInput)
@serialize_pydantic_return
async def delete_invoice(
    auth_type: str,
    auth_data: dict[str, Any],
    invoice_id: str,
    sync_token: str | None = None,
) -> DeleteInvoiceOutput:
    """Delete an invoice permanently.

    The transaction disappears from the books entirely. When the invoice
    must stay on record for the audit trail — the usual accounting choice —
    use ``void_invoice`` instead, which keeps it at a zero amount.
    """
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "invoice", "Invoice", invoice_id, sync_token
    )
    if error is not None:
        return DeleteInvoiceOutput(success=False, error=error)

    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/invoice",
        params={"operation": "delete"},
        json_body={"Id": invoice_id, "SyncToken": token},
    )
    if error is not None:
        return DeleteInvoiceOutput(success=False, error=error)
    entity = _entity(payload, "Invoice")
    return DeleteInvoiceOutput(
        success=True,
        invoice_id=_as_str(entity.get("Id")) or invoice_id,
        status=_as_str(entity.get("status")),
    )


class SearchInvoicesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    customer_id: str | None = Field(
        default=None, description="Only invoices billed to this customer ID"
    )
    doc_number: str | None = Field(
        default=None, description="Only the invoice carrying this reference number"
    )
    txn_date_from: str | None = Field(
        default=None, description="Only invoices dated on or after this date (YYYY-MM-DD)"
    )
    txn_date_to: str | None = Field(
        default=None, description="Only invoices dated on or before this date (YYYY-MM-DD)"
    )
    due_date_from: str | None = Field(
        default=None, description="Only invoices due on or after this date (YYYY-MM-DD)"
    )
    due_date_to: str | None = Field(
        default=None, description="Only invoices due on or before this date (YYYY-MM-DD)"
    )
    unpaid_only: bool = Field(
        default=False,
        description="When true, return only invoices with an outstanding balance",
    )
    max_results: int | None = Field(
        default=None, description="Maximum number of invoices to return"
    )
    start_position: int | None = Field(
        default=None, description="1-based index of the first result, for paging"
    )


@tool(args_schema=SearchInvoicesInput)
@serialize_pydantic_return
async def search_invoices(
    auth_type: str,
    auth_data: dict[str, Any],
    customer_id: str | None = None,
    doc_number: str | None = None,
    txn_date_from: str | None = None,
    txn_date_to: str | None = None,
    due_date_from: str | None = None,
    due_date_to: str | None = None,
    unpaid_only: bool = False,
    max_results: int | None = None,
    start_position: int | None = None,
) -> SearchInvoicesOutput:
    """Find invoices by customer, number, date range or unpaid status.

    All supplied filters are combined with AND. With no filters at all this
    lists the company's invoices.
    """
    clauses: list[str] = []
    if customer_id:
        clauses.append(f"CustomerRef = '{_escape_sql(customer_id)}'")
    if doc_number:
        clauses.append(f"DocNumber = '{_escape_sql(doc_number)}'")
    if txn_date_from:
        clauses.append(f"TxnDate >= '{_escape_sql(txn_date_from)}'")
    if txn_date_to:
        clauses.append(f"TxnDate <= '{_escape_sql(txn_date_to)}'")
    if due_date_from:
        clauses.append(f"DueDate >= '{_escape_sql(due_date_from)}'")
    if due_date_to:
        clauses.append(f"DueDate <= '{_escape_sql(due_date_to)}'")
    if unpaid_only:
        clauses.append("Balance > '0'")

    statement = "SELECT * FROM Invoice"
    if clauses:
        statement += " WHERE " + " AND ".join(clauses)
    statement += _sales_query_suffix(max_results, start_position)

    payload, error = await _request(
        auth_type, auth_data, "GET", "/query", params={"query": statement}
    )
    if error is not None:
        return SearchInvoicesOutput(success=False, error=error, query=statement)
    rows = _query_rows(payload, "Invoice")
    return SearchInvoicesOutput(
        success=True,
        invoices=[_parse_invoice(row) for row in rows],
        count=len(rows),
        query=statement,
    )


# --- Customers --------------------------------------------------------------


class CreateCustomerInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    display_name: str | None = Field(
        default=None,
        description=(
            "Name as displayed. Must be unique across all customers, vendors "
            "and employees. Either this or one of the name parts is required"
        ),
    )
    title: str | None = Field(default=None, description="Title of the person, such as Ms")
    given_name: str | None = Field(default=None, description="First name of the person")
    middle_name: str | None = Field(default=None, description="Middle name of the person")
    family_name: str | None = Field(default=None, description="Last name of the person")
    suffix: str | None = Field(default=None, description="Suffix of the name, such as Jr")
    company_name: str | None = Field(
        default=None, description="Name of the company the customer belongs to"
    )
    print_on_check_name: str | None = Field(
        default=None, description="Name as printed on a check. Defaults to the display name"
    )
    primary_email: str | None = Field(default=None, description="Primary email address")
    primary_phone: str | None = Field(default=None, description="Primary phone number")
    mobile: str | None = Field(default=None, description="Mobile phone number")
    website: str | None = Field(default=None, description="Website URL")
    bill_address: dict[str, Any] | None = Field(
        default=None,
        description="Billing address. Keys: line1, line2, city, state, postal_code, country",
    )
    ship_address: dict[str, Any] | None = Field(
        default=None,
        description="Shipping address. Keys: line1, line2, city, state, postal_code, country",
    )
    notes: str | None = Field(default=None, description="Free-form note about the customer")
    taxable: bool | None = Field(
        default=None, description="Whether sales to this customer are taxable"
    )
    currency_code: str | None = Field(
        default=None, description="ISO 4217 code such as USD. Multicurrency companies only"
    )
    sales_term_id: str | None = Field(
        default=None, description="ID of the SalesTerm used as this customer's default terms"
    )
    payment_method_id: str | None = Field(
        default=None, description="ID of the PaymentMethod usually used by this customer"
    )
    account_number: str | None = Field(
        default=None, description="Your account number for this customer"
    )
    resale_number: str | None = Field(
        default=None, description="Resale number, for tax-exempt resellers"
    )
    preferred_delivery_method: str | None = Field(
        default=None, description="How documents reach the customer: Print, Email or None"
    )


@tool(args_schema=CreateCustomerInput)
@serialize_pydantic_return
async def create_customer(
    auth_type: str,
    auth_data: dict[str, Any],
    display_name: str | None = None,
    title: str | None = None,
    given_name: str | None = None,
    middle_name: str | None = None,
    family_name: str | None = None,
    suffix: str | None = None,
    company_name: str | None = None,
    print_on_check_name: str | None = None,
    primary_email: str | None = None,
    primary_phone: str | None = None,
    mobile: str | None = None,
    website: str | None = None,
    bill_address: dict[str, Any] | None = None,
    ship_address: dict[str, Any] | None = None,
    notes: str | None = None,
    taxable: bool | None = None,
    currency_code: str | None = None,
    sales_term_id: str | None = None,
    payment_method_id: str | None = None,
    account_number: str | None = None,
    resale_number: str | None = None,
    preferred_delivery_method: str | None = None,
) -> CreateCustomerOutput:
    """Add a customer to the company.

    Supply either a display name or at least one name part — QuickBooks
    builds the display name from the parts when it is omitted, and rejects
    a display name that is already taken by a customer, vendor or employee.
    """
    body: dict[str, Any] = {
        "DisplayName": display_name,
        "Title": title,
        "GivenName": given_name,
        "MiddleName": middle_name,
        "FamilyName": family_name,
        "Suffix": suffix,
        "CompanyName": company_name,
        "PrintOnCheckName": print_on_check_name,
        "Notes": notes,
        "Taxable": taxable,
        "AcctNum": account_number,
        "ResaleNum": resale_number,
        "PreferredDeliveryMethod": preferred_delivery_method,
        "BillAddr": _build_sales_address(bill_address),
        "ShipAddr": _build_sales_address(ship_address),
    }
    if primary_email:
        body["PrimaryEmailAddr"] = {"Address": primary_email}
    if primary_phone:
        body["PrimaryPhone"] = {"FreeFormNumber": primary_phone}
    if mobile:
        body["Mobile"] = {"FreeFormNumber": mobile}
    if website:
        body["WebAddr"] = {"URI": website}
    if currency_code:
        body["CurrencyRef"] = {"value": currency_code}
    if sales_term_id:
        body["SalesTermRef"] = {"value": sales_term_id}
    if payment_method_id:
        body["PaymentMethodRef"] = {"value": payment_method_id}

    payload, error = await _request(auth_type, auth_data, "POST", "/customer", json_body=body)
    if error is not None:
        return CreateCustomerOutput(success=False, error=error)
    entity = _entity(payload, "Customer")
    return CreateCustomerOutput(
        success=True, customer=_parse_customer(entity) if entity else None
    )


class GetCustomerInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    customer_id: str = Field(description="ID of the customer to read")


@tool(args_schema=GetCustomerInput)
@serialize_pydantic_return
async def get_customer(
    auth_type: str,
    auth_data: dict[str, Any],
    customer_id: str,
) -> GetCustomerOutput:
    """Read one customer by ID, including contact details and balance."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/customer/{_seg(customer_id)}"
    )
    if error is not None:
        return GetCustomerOutput(success=False, error=error)
    entity = _entity(payload, "Customer")
    return GetCustomerOutput(
        success=True, customer=_parse_customer(entity) if entity else None
    )


class UpdateCustomerInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    customer_id: str = Field(description="ID of the customer to update")
    display_name: str | None = Field(
        default=None, description="Name as displayed. Must stay unique across the company"
    )
    title: str | None = Field(default=None, description="Title of the person, such as Ms")
    given_name: str | None = Field(default=None, description="First name of the person")
    middle_name: str | None = Field(default=None, description="Middle name of the person")
    family_name: str | None = Field(default=None, description="Last name of the person")
    suffix: str | None = Field(default=None, description="Suffix of the name, such as Jr")
    company_name: str | None = Field(default=None, description="Name of the company")
    print_on_check_name: str | None = Field(
        default=None, description="Name as printed on a check"
    )
    primary_email: str | None = Field(default=None, description="Primary email address")
    primary_phone: str | None = Field(default=None, description="Primary phone number")
    mobile: str | None = Field(default=None, description="Mobile phone number")
    website: str | None = Field(default=None, description="Website URL")
    bill_address: dict[str, Any] | None = Field(
        default=None,
        description="Billing address. Keys: line1, line2, city, state, postal_code, country",
    )
    ship_address: dict[str, Any] | None = Field(
        default=None,
        description="Shipping address. Keys: line1, line2, city, state, postal_code, country",
    )
    notes: str | None = Field(default=None, description="Free-form note about the customer")
    active: bool | None = Field(
        default=None,
        description="Set false to deactivate the customer, true to reactivate one",
    )
    taxable: bool | None = Field(
        default=None, description="Whether sales to this customer are taxable"
    )
    currency_code: str | None = Field(default=None, description="ISO 4217 code such as USD")
    sales_term_id: str | None = Field(
        default=None, description="ID of the SalesTerm used as this customer's default terms"
    )
    payment_method_id: str | None = Field(
        default=None, description="ID of the PaymentMethod usually used by this customer"
    )
    account_number: str | None = Field(
        default=None, description="Your account number for this customer"
    )
    resale_number: str | None = Field(default=None, description="Resale number")
    preferred_delivery_method: str | None = Field(
        default=None, description="How documents reach the customer: Print, Email or None"
    )
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request"
        ),
    )


@tool(args_schema=UpdateCustomerInput)
@serialize_pydantic_return
async def update_customer(
    auth_type: str,
    auth_data: dict[str, Any],
    customer_id: str,
    display_name: str | None = None,
    title: str | None = None,
    given_name: str | None = None,
    middle_name: str | None = None,
    family_name: str | None = None,
    suffix: str | None = None,
    company_name: str | None = None,
    print_on_check_name: str | None = None,
    primary_email: str | None = None,
    primary_phone: str | None = None,
    mobile: str | None = None,
    website: str | None = None,
    bill_address: dict[str, Any] | None = None,
    ship_address: dict[str, Any] | None = None,
    notes: str | None = None,
    active: bool | None = None,
    taxable: bool | None = None,
    currency_code: str | None = None,
    sales_term_id: str | None = None,
    payment_method_id: str | None = None,
    account_number: str | None = None,
    resale_number: str | None = None,
    preferred_delivery_method: str | None = None,
    sync_token: str | None = None,
) -> UpdateCustomerOutput:
    """Change fields on an existing customer, leaving the rest untouched.

    This is a sparse update: only the values supplied here change.
    """
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "customer", "Customer", customer_id, sync_token
    )
    if error is not None:
        return UpdateCustomerOutput(success=False, error=error)

    body: dict[str, Any] = {
        "Id": customer_id,
        "SyncToken": token,
        "sparse": True,
        "DisplayName": display_name,
        "Title": title,
        "GivenName": given_name,
        "MiddleName": middle_name,
        "FamilyName": family_name,
        "Suffix": suffix,
        "CompanyName": company_name,
        "PrintOnCheckName": print_on_check_name,
        "Notes": notes,
        "Active": active,
        "Taxable": taxable,
        "AcctNum": account_number,
        "ResaleNum": resale_number,
        "PreferredDeliveryMethod": preferred_delivery_method,
        "BillAddr": _build_sales_address(bill_address),
        "ShipAddr": _build_sales_address(ship_address),
    }
    if primary_email:
        body["PrimaryEmailAddr"] = {"Address": primary_email}
    if primary_phone:
        body["PrimaryPhone"] = {"FreeFormNumber": primary_phone}
    if mobile:
        body["Mobile"] = {"FreeFormNumber": mobile}
    if website:
        body["WebAddr"] = {"URI": website}
    if currency_code:
        body["CurrencyRef"] = {"value": currency_code}
    if sales_term_id:
        body["SalesTermRef"] = {"value": sales_term_id}
    if payment_method_id:
        body["PaymentMethodRef"] = {"value": payment_method_id}

    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/customer",
        params={"operation": "update"},
        json_body=body,
    )
    if error is not None:
        return UpdateCustomerOutput(success=False, error=error)
    entity = _entity(payload, "Customer")
    return UpdateCustomerOutput(
        success=True, customer=_parse_customer(entity) if entity else None
    )


class DeleteCustomerInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    customer_id: str = Field(description="ID of the customer to deactivate")
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request"
        ),
    )


@tool(args_schema=DeleteCustomerInput)
@serialize_pydantic_return
async def delete_customer(
    auth_type: str,
    auth_data: dict[str, Any],
    customer_id: str,
    sync_token: str | None = None,
) -> DeleteCustomerOutput:
    """Deactivate a customer.

    QuickBooks does not permit deleting customers, so this marks the record
    inactive; its history is preserved and ``update_customer`` with
    ``active=true`` reverses it. This is also what "delete customer" does in
    the QuickBooks UI.
    """
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "customer", "Customer", customer_id, sync_token
    )
    if error is not None:
        return DeleteCustomerOutput(success=False, error=error)

    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/customer",
        params={"operation": "update"},
        json_body={
            "Id": customer_id,
            "SyncToken": token,
            "sparse": True,
            "Active": False,
        },
    )
    if error is not None:
        return DeleteCustomerOutput(success=False, error=error)
    entity = _entity(payload, "Customer")
    return DeleteCustomerOutput(
        success=True,
        customer=_parse_customer(entity) if entity else None,
        deactivated=True,
    )


class SearchCustomersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    display_name: str | None = Field(
        default=None, description="Only the customer whose display name matches exactly"
    )
    name_contains: str | None = Field(
        default=None, description="Only customers whose display name contains this text"
    )
    company_name: str | None = Field(
        default=None, description="Only customers with this exact company name"
    )
    given_name: str | None = Field(
        default=None, description="Only customers with this exact first name"
    )
    family_name: str | None = Field(
        default=None, description="Only customers with this exact last name"
    )
    active: bool | None = Field(
        default=None,
        description="True for active customers only, false for deactivated ones",
    )
    max_results: int | None = Field(
        default=None, description="Maximum number of customers to return"
    )
    start_position: int | None = Field(
        default=None, description="1-based index of the first result, for paging"
    )


@tool(args_schema=SearchCustomersInput)
@serialize_pydantic_return
async def search_customers(
    auth_type: str,
    auth_data: dict[str, Any],
    display_name: str | None = None,
    name_contains: str | None = None,
    company_name: str | None = None,
    given_name: str | None = None,
    family_name: str | None = None,
    active: bool | None = None,
    max_results: int | None = None,
    start_position: int | None = None,
) -> SearchCustomersOutput:
    """Find customers by name, company or active state.

    All supplied filters are combined with AND. With no filters at all this
    lists the company's customers — a good way to resolve a name to the ID
    the invoice actions need.
    """
    clauses: list[str] = []
    if display_name:
        clauses.append(f"DisplayName = '{_escape_sql(display_name)}'")
    if name_contains:
        clauses.append(f"DisplayName LIKE '%{_escape_sql(name_contains)}%'")
    if company_name:
        clauses.append(f"CompanyName = '{_escape_sql(company_name)}'")
    if given_name:
        clauses.append(f"GivenName = '{_escape_sql(given_name)}'")
    if family_name:
        clauses.append(f"FamilyName = '{_escape_sql(family_name)}'")
    if active is not None:
        clauses.append("Active = true" if active else "Active = false")

    statement = "SELECT * FROM Customer"
    if clauses:
        statement += " WHERE " + " AND ".join(clauses)
    statement += _sales_query_suffix(max_results, start_position)

    payload, error = await _request(
        auth_type, auth_data, "GET", "/query", params={"query": statement}
    )
    if error is not None:
        return SearchCustomersOutput(success=False, error=error, query=statement)
    rows = _query_rows(payload, "Customer")
    return SearchCustomersOutput(
        success=True,
        customers=[_parse_customer(row) for row in rows],
        count=len(rows),
        query=statement,
    )


# --- Estimates --------------------------------------------------------------


class CreateEstimateInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    customer_id: str = Field(description="ID of the customer being quoted")
    line_items: list[dict[str, Any]] = Field(
        description=(
            "What is being quoted. Each object accepts item_ref (the QuickBooks "
            "Item ID), qty, unit_price, description, tax_code_ref and "
            "service_date (YYYY-MM-DD). The line total defaults to "
            "qty * unit_price; pass amount to override it"
        )
    )
    txn_date: str | None = Field(default=None, description="Estimate date as YYYY-MM-DD")
    expiration_date: str | None = Field(
        default=None, description="Date the estimate stops being valid (YYYY-MM-DD)"
    )
    doc_number: str | None = Field(
        default=None, description="Reference number for the transaction"
    )
    bill_email: str | None = Field(
        default=None, description="Email address the estimate is addressed to"
    )
    customer_memo: str | None = Field(
        default=None, description="Message shown to the customer on the estimate"
    )
    private_note: str | None = Field(default=None, description="Internal note")
    accepted_by: str | None = Field(
        default=None, description="Name of the person who accepted the estimate"
    )
    accepted_date: str | None = Field(
        default=None, description="Date the estimate was accepted (YYYY-MM-DD)"
    )
    txn_status: str | None = Field(
        default=None, description="Estimate status: Pending, Accepted, Closed or Rejected"
    )
    currency_code: str | None = Field(default=None, description="ISO 4217 code such as USD")
    bill_address: dict[str, Any] | None = Field(
        default=None,
        description="Billing address. Keys: line1, line2, city, state, postal_code, country",
    )
    ship_address: dict[str, Any] | None = Field(
        default=None,
        description="Shipping address. Keys: line1, line2, city, state, postal_code, country",
    )
    global_tax_calculation: str | None = Field(
        default=None,
        description="TaxExcluded, TaxInclusive or NotApplicable. Non-US companies only",
    )


@tool(args_schema=CreateEstimateInput)
@serialize_pydantic_return
async def create_estimate(
    auth_type: str,
    auth_data: dict[str, Any],
    customer_id: str,
    line_items: list[dict[str, Any]],
    txn_date: str | None = None,
    expiration_date: str | None = None,
    doc_number: str | None = None,
    bill_email: str | None = None,
    customer_memo: str | None = None,
    private_note: str | None = None,
    accepted_by: str | None = None,
    accepted_date: str | None = None,
    txn_status: str | None = None,
    currency_code: str | None = None,
    bill_address: dict[str, Any] | None = None,
    ship_address: dict[str, Any] | None = None,
    global_tax_calculation: str | None = None,
) -> CreateEstimateOutput:
    """Create an estimate — a quote or proposal for a customer.

    An estimate is non-posting: it does not affect the books until it is
    converted into an invoice.
    """
    body: dict[str, Any] = {
        "CustomerRef": {"value": customer_id},
        "Line": _build_sales_lines(line_items),
        "TxnDate": txn_date,
        "ExpirationDate": expiration_date,
        "DocNumber": doc_number,
        "PrivateNote": private_note,
        "AcceptedBy": accepted_by,
        "AcceptedDate": accepted_date,
        "TxnStatus": txn_status,
        "GlobalTaxCalculation": global_tax_calculation,
        "BillAddr": _build_sales_address(bill_address),
        "ShipAddr": _build_sales_address(ship_address),
    }
    if bill_email:
        body["BillEmail"] = {"Address": bill_email}
    if customer_memo:
        body["CustomerMemo"] = {"value": customer_memo}
    if currency_code:
        body["CurrencyRef"] = {"value": currency_code}

    payload, error = await _request(auth_type, auth_data, "POST", "/estimate", json_body=body)
    if error is not None:
        return CreateEstimateOutput(success=False, error=error)
    entity = _entity(payload, "Estimate")
    return CreateEstimateOutput(
        success=True, estimate=_parse_estimate(entity) if entity else None
    )


class GetEstimateInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    estimate_id: str = Field(description="ID of the estimate to read")


@tool(args_schema=GetEstimateInput)
@serialize_pydantic_return
async def get_estimate(
    auth_type: str,
    auth_data: dict[str, Any],
    estimate_id: str,
) -> GetEstimateOutput:
    """Read one estimate by its ID, including its line items and status."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/estimate/{_seg(estimate_id)}"
    )
    if error is not None:
        return GetEstimateOutput(success=False, error=error)
    entity = _entity(payload, "Estimate")
    return GetEstimateOutput(
        success=True, estimate=_parse_estimate(entity) if entity else None
    )


class UpdateEstimateInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    estimate_id: str = Field(description="ID of the estimate to update")
    customer_id: str | None = Field(
        default=None, description="ID of the customer the estimate is addressed to"
    )
    line_items: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Replacement line items. Supplying this REPLACES every existing "
            "line, so include the lines you want to keep. Each object accepts "
            "item_ref, qty, unit_price, description, tax_code_ref and "
            "service_date"
        ),
    )
    txn_date: str | None = Field(default=None, description="Estimate date as YYYY-MM-DD")
    expiration_date: str | None = Field(
        default=None, description="Date the estimate stops being valid (YYYY-MM-DD)"
    )
    doc_number: str | None = Field(
        default=None, description="Reference number for the transaction"
    )
    bill_email: str | None = Field(
        default=None, description="Email address the estimate is addressed to"
    )
    customer_memo: str | None = Field(
        default=None, description="Message shown to the customer on the estimate"
    )
    private_note: str | None = Field(default=None, description="Internal note")
    accepted_by: str | None = Field(
        default=None, description="Name of the person who accepted the estimate"
    )
    accepted_date: str | None = Field(
        default=None, description="Date the estimate was accepted (YYYY-MM-DD)"
    )
    txn_status: str | None = Field(
        default=None, description="Estimate status: Pending, Accepted, Closed or Rejected"
    )
    currency_code: str | None = Field(default=None, description="ISO 4217 code such as USD")
    bill_address: dict[str, Any] | None = Field(
        default=None,
        description="Billing address. Keys: line1, line2, city, state, postal_code, country",
    )
    ship_address: dict[str, Any] | None = Field(
        default=None,
        description="Shipping address. Keys: line1, line2, city, state, postal_code, country",
    )
    global_tax_calculation: str | None = Field(
        default=None,
        description="TaxExcluded, TaxInclusive or NotApplicable. Non-US companies only",
    )
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request"
        ),
    )


@tool(args_schema=UpdateEstimateInput)
@serialize_pydantic_return
async def update_estimate(
    auth_type: str,
    auth_data: dict[str, Any],
    estimate_id: str,
    customer_id: str | None = None,
    line_items: list[dict[str, Any]] | None = None,
    txn_date: str | None = None,
    expiration_date: str | None = None,
    doc_number: str | None = None,
    bill_email: str | None = None,
    customer_memo: str | None = None,
    private_note: str | None = None,
    accepted_by: str | None = None,
    accepted_date: str | None = None,
    txn_status: str | None = None,
    currency_code: str | None = None,
    bill_address: dict[str, Any] | None = None,
    ship_address: dict[str, Any] | None = None,
    global_tax_calculation: str | None = None,
    sync_token: str | None = None,
) -> UpdateEstimateOutput:
    """Change fields on an existing estimate, leaving the rest untouched.

    This is a sparse update: only the values supplied here change. Marking
    a quote as won is ``txn_status="Accepted"``.
    """
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "estimate", "Estimate", estimate_id, sync_token
    )
    if error is not None:
        return UpdateEstimateOutput(success=False, error=error)

    body: dict[str, Any] = {
        "Id": estimate_id,
        "SyncToken": token,
        "sparse": True,
        "TxnDate": txn_date,
        "ExpirationDate": expiration_date,
        "DocNumber": doc_number,
        "PrivateNote": private_note,
        "AcceptedBy": accepted_by,
        "AcceptedDate": accepted_date,
        "TxnStatus": txn_status,
        "GlobalTaxCalculation": global_tax_calculation,
        "BillAddr": _build_sales_address(bill_address),
        "ShipAddr": _build_sales_address(ship_address),
    }
    if customer_id:
        body["CustomerRef"] = {"value": customer_id}
    if line_items is not None:
        body["Line"] = _build_sales_lines(line_items)
    if bill_email:
        body["BillEmail"] = {"Address": bill_email}
    if customer_memo:
        body["CustomerMemo"] = {"value": customer_memo}
    if currency_code:
        body["CurrencyRef"] = {"value": currency_code}

    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/estimate",
        params={"operation": "update"},
        json_body=body,
    )
    if error is not None:
        return UpdateEstimateOutput(success=False, error=error)
    entity = _entity(payload, "Estimate")
    return UpdateEstimateOutput(
        success=True, estimate=_parse_estimate(entity) if entity else None
    )


class DeleteEstimateInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    estimate_id: str = Field(description="ID of the estimate to delete")
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request"
        ),
    )


@tool(args_schema=DeleteEstimateInput)
@serialize_pydantic_return
async def delete_estimate(
    auth_type: str,
    auth_data: dict[str, Any],
    estimate_id: str,
    sync_token: str | None = None,
) -> DeleteEstimateOutput:
    """Delete an estimate permanently.

    To keep the quote on record but take it out of play, set its status to
    ``Closed`` or ``Rejected`` with ``update_estimate`` instead.
    """
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "estimate", "Estimate", estimate_id, sync_token
    )
    if error is not None:
        return DeleteEstimateOutput(success=False, error=error)

    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/estimate",
        params={"operation": "delete"},
        json_body={"Id": estimate_id, "SyncToken": token},
    )
    if error is not None:
        return DeleteEstimateOutput(success=False, error=error)
    entity = _entity(payload, "Estimate")
    return DeleteEstimateOutput(
        success=True,
        estimate_id=_as_str(entity.get("Id")) or estimate_id,
        status=_as_str(entity.get("status")),
    )


class SearchEstimatesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    customer_id: str | None = Field(
        default=None, description="Only estimates addressed to this customer ID"
    )
    doc_number: str | None = Field(
        default=None, description="Only the estimate carrying this reference number"
    )
    txn_status: str | None = Field(
        default=None,
        description="Only estimates in this status: Pending, Accepted, Closed or Rejected",
    )
    txn_date_from: str | None = Field(
        default=None, description="Only estimates dated on or after this date (YYYY-MM-DD)"
    )
    txn_date_to: str | None = Field(
        default=None, description="Only estimates dated on or before this date (YYYY-MM-DD)"
    )
    max_results: int | None = Field(
        default=None, description="Maximum number of estimates to return"
    )
    start_position: int | None = Field(
        default=None, description="1-based index of the first result, for paging"
    )


@tool(args_schema=SearchEstimatesInput)
@serialize_pydantic_return
async def search_estimates(
    auth_type: str,
    auth_data: dict[str, Any],
    customer_id: str | None = None,
    doc_number: str | None = None,
    txn_status: str | None = None,
    txn_date_from: str | None = None,
    txn_date_to: str | None = None,
    max_results: int | None = None,
    start_position: int | None = None,
) -> SearchEstimatesOutput:
    """Find estimates by customer, number, status or date range.

    All supplied filters are combined with AND. With no filters at all this
    lists the company's estimates.
    """
    clauses: list[str] = []
    if customer_id:
        clauses.append(f"CustomerRef = '{_escape_sql(customer_id)}'")
    if doc_number:
        clauses.append(f"DocNumber = '{_escape_sql(doc_number)}'")
    if txn_status:
        # TODO (unverified): TxnStatus is documented as an Estimate attribute
        # with values Pending/Accepted/Closed/Rejected, but the entity
        # reference page could not be read to confirm it is *filterable* in a
        # query. QuickBooks answers with a fault if it is not.
        clauses.append(f"TxnStatus = '{_escape_sql(txn_status)}'")
    if txn_date_from:
        clauses.append(f"TxnDate >= '{_escape_sql(txn_date_from)}'")
    if txn_date_to:
        clauses.append(f"TxnDate <= '{_escape_sql(txn_date_to)}'")

    statement = "SELECT * FROM Estimate"
    if clauses:
        statement += " WHERE " + " AND ".join(clauses)
    statement += _sales_query_suffix(max_results, start_position)

    payload, error = await _request(
        auth_type, auth_data, "GET", "/query", params={"query": statement}
    )
    if error is not None:
        return SearchEstimatesOutput(success=False, error=error, query=statement)
    rows = _query_rows(payload, "Estimate")
    return SearchEstimatesOutput(
        success=True,
        estimates=[_parse_estimate(row) for row in rows],
        count=len(rows),
        query=statement,
    )


# --- Sales receipts ---------------------------------------------------------


class CreateSalesReceiptInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    line_items: list[dict[str, Any]] = Field(
        description=(
            "What was sold. Each object accepts item_ref (the QuickBooks Item "
            "ID), qty, unit_price, description, tax_code_ref and service_date "
            "(YYYY-MM-DD). The line total defaults to qty * unit_price; pass "
            "amount to override it"
        )
    )
    customer_id: str | None = Field(
        default=None, description="ID of the customer. Omit for an anonymous cash sale"
    )
    txn_date: str | None = Field(default=None, description="Sale date as YYYY-MM-DD")
    doc_number: str | None = Field(
        default=None, description="Reference number for the transaction"
    )
    payment_method_id: str | None = Field(
        default=None, description="ID of the PaymentMethod the customer paid with"
    )
    payment_reference_number: str | None = Field(
        default=None, description="Check or transaction number for the payment"
    )
    deposit_to_account_id: str | None = Field(
        default=None,
        description="ID of the account the money lands in. Defaults to Undeposited Funds",
    )
    bill_email: str | None = Field(
        default=None, description="Email address the receipt is addressed to"
    )
    customer_memo: str | None = Field(
        default=None, description="Message shown to the customer on the receipt"
    )
    private_note: str | None = Field(default=None, description="Internal note")
    currency_code: str | None = Field(default=None, description="ISO 4217 code such as USD")
    bill_address: dict[str, Any] | None = Field(
        default=None,
        description="Billing address. Keys: line1, line2, city, state, postal_code, country",
    )
    ship_address: dict[str, Any] | None = Field(
        default=None,
        description="Shipping address. Keys: line1, line2, city, state, postal_code, country",
    )
    global_tax_calculation: str | None = Field(
        default=None,
        description="TaxExcluded, TaxInclusive or NotApplicable. Non-US companies only",
    )


@tool(args_schema=CreateSalesReceiptInput)
@serialize_pydantic_return
async def create_sales_receipt(
    auth_type: str,
    auth_data: dict[str, Any],
    line_items: list[dict[str, Any]],
    customer_id: str | None = None,
    txn_date: str | None = None,
    doc_number: str | None = None,
    payment_method_id: str | None = None,
    payment_reference_number: str | None = None,
    deposit_to_account_id: str | None = None,
    bill_email: str | None = None,
    customer_memo: str | None = None,
    private_note: str | None = None,
    currency_code: str | None = None,
    bill_address: dict[str, Any] | None = None,
    ship_address: dict[str, Any] | None = None,
    global_tax_calculation: str | None = None,
) -> CreateSalesReceiptOutput:
    """Record a sale that was paid for at the same time.

    Use this for point-of-sale style transactions. When the customer will
    pay later, create an invoice instead.
    """
    body: dict[str, Any] = {
        "Line": _build_sales_lines(line_items),
        "TxnDate": txn_date,
        "DocNumber": doc_number,
        "PaymentRefNum": payment_reference_number,
        "PrivateNote": private_note,
        "GlobalTaxCalculation": global_tax_calculation,
        "BillAddr": _build_sales_address(bill_address),
        "ShipAddr": _build_sales_address(ship_address),
    }
    if customer_id:
        body["CustomerRef"] = {"value": customer_id}
    if payment_method_id:
        body["PaymentMethodRef"] = {"value": payment_method_id}
    if deposit_to_account_id:
        body["DepositToAccountRef"] = {"value": deposit_to_account_id}
    if bill_email:
        body["BillEmail"] = {"Address": bill_email}
    if customer_memo:
        body["CustomerMemo"] = {"value": customer_memo}
    if currency_code:
        body["CurrencyRef"] = {"value": currency_code}

    payload, error = await _request(
        auth_type, auth_data, "POST", "/salesreceipt", json_body=body
    )
    if error is not None:
        return CreateSalesReceiptOutput(success=False, error=error)
    entity = _entity(payload, "SalesReceipt")
    return CreateSalesReceiptOutput(
        success=True, sales_receipt=_parse_sales_receipt(entity) if entity else None
    )


class GetSalesReceiptInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    sales_receipt_id: str = Field(description="ID of the sales receipt to read")


@tool(args_schema=GetSalesReceiptInput)
@serialize_pydantic_return
async def get_sales_receipt(
    auth_type: str,
    auth_data: dict[str, Any],
    sales_receipt_id: str,
) -> GetSalesReceiptOutput:
    """Read one sales receipt by its ID, including its line items."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/salesreceipt/{_seg(sales_receipt_id)}"
    )
    if error is not None:
        return GetSalesReceiptOutput(success=False, error=error)
    entity = _entity(payload, "SalesReceipt")
    return GetSalesReceiptOutput(
        success=True, sales_receipt=_parse_sales_receipt(entity) if entity else None
    )


class UpdateSalesReceiptInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    sales_receipt_id: str = Field(description="ID of the sales receipt to update")
    customer_id: str | None = Field(default=None, description="ID of the customer")
    line_items: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Replacement line items. Supplying this REPLACES every existing "
            "line, so include the lines you want to keep. Each object accepts "
            "item_ref, qty, unit_price, description, tax_code_ref and "
            "service_date"
        ),
    )
    txn_date: str | None = Field(default=None, description="Sale date as YYYY-MM-DD")
    doc_number: str | None = Field(
        default=None, description="Reference number for the transaction"
    )
    payment_method_id: str | None = Field(
        default=None, description="ID of the PaymentMethod the customer paid with"
    )
    payment_reference_number: str | None = Field(
        default=None, description="Check or transaction number for the payment"
    )
    deposit_to_account_id: str | None = Field(
        default=None, description="ID of the account the money lands in"
    )
    bill_email: str | None = Field(
        default=None, description="Email address the receipt is addressed to"
    )
    customer_memo: str | None = Field(
        default=None, description="Message shown to the customer on the receipt"
    )
    private_note: str | None = Field(default=None, description="Internal note")
    currency_code: str | None = Field(default=None, description="ISO 4217 code such as USD")
    bill_address: dict[str, Any] | None = Field(
        default=None,
        description="Billing address. Keys: line1, line2, city, state, postal_code, country",
    )
    ship_address: dict[str, Any] | None = Field(
        default=None,
        description="Shipping address. Keys: line1, line2, city, state, postal_code, country",
    )
    global_tax_calculation: str | None = Field(
        default=None,
        description="TaxExcluded, TaxInclusive or NotApplicable. Non-US companies only",
    )
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request"
        ),
    )


@tool(args_schema=UpdateSalesReceiptInput)
@serialize_pydantic_return
async def update_sales_receipt(
    auth_type: str,
    auth_data: dict[str, Any],
    sales_receipt_id: str,
    customer_id: str | None = None,
    line_items: list[dict[str, Any]] | None = None,
    txn_date: str | None = None,
    doc_number: str | None = None,
    payment_method_id: str | None = None,
    payment_reference_number: str | None = None,
    deposit_to_account_id: str | None = None,
    bill_email: str | None = None,
    customer_memo: str | None = None,
    private_note: str | None = None,
    currency_code: str | None = None,
    bill_address: dict[str, Any] | None = None,
    ship_address: dict[str, Any] | None = None,
    global_tax_calculation: str | None = None,
    sync_token: str | None = None,
) -> UpdateSalesReceiptOutput:
    """Change fields on an existing sales receipt, leaving the rest alone.

    This is a sparse update: only the values supplied here change.
    """
    token, error = await _resolve_sync_token(
        auth_type,
        auth_data,
        "salesreceipt",
        "SalesReceipt",
        sales_receipt_id,
        sync_token,
    )
    if error is not None:
        return UpdateSalesReceiptOutput(success=False, error=error)

    body: dict[str, Any] = {
        "Id": sales_receipt_id,
        "SyncToken": token,
        "sparse": True,
        "TxnDate": txn_date,
        "DocNumber": doc_number,
        "PaymentRefNum": payment_reference_number,
        "PrivateNote": private_note,
        "GlobalTaxCalculation": global_tax_calculation,
        "BillAddr": _build_sales_address(bill_address),
        "ShipAddr": _build_sales_address(ship_address),
    }
    if customer_id:
        body["CustomerRef"] = {"value": customer_id}
    if line_items is not None:
        body["Line"] = _build_sales_lines(line_items)
    if payment_method_id:
        body["PaymentMethodRef"] = {"value": payment_method_id}
    if deposit_to_account_id:
        body["DepositToAccountRef"] = {"value": deposit_to_account_id}
    if bill_email:
        body["BillEmail"] = {"Address": bill_email}
    if customer_memo:
        body["CustomerMemo"] = {"value": customer_memo}
    if currency_code:
        body["CurrencyRef"] = {"value": currency_code}

    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/salesreceipt",
        params={"operation": "update"},
        json_body=body,
    )
    if error is not None:
        return UpdateSalesReceiptOutput(success=False, error=error)
    entity = _entity(payload, "SalesReceipt")
    return UpdateSalesReceiptOutput(
        success=True, sales_receipt=_parse_sales_receipt(entity) if entity else None
    )


class DeleteSalesReceiptInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    sales_receipt_id: str = Field(description="ID of the sales receipt to delete")
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request"
        ),
    )


@tool(args_schema=DeleteSalesReceiptInput)
@serialize_pydantic_return
async def delete_sales_receipt(
    auth_type: str,
    auth_data: dict[str, Any],
    sales_receipt_id: str,
    sync_token: str | None = None,
) -> DeleteSalesReceiptOutput:
    """Delete a sales receipt permanently.

    Both the sale and the payment it recorded come off the books.
    """
    token, error = await _resolve_sync_token(
        auth_type,
        auth_data,
        "salesreceipt",
        "SalesReceipt",
        sales_receipt_id,
        sync_token,
    )
    if error is not None:
        return DeleteSalesReceiptOutput(success=False, error=error)

    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/salesreceipt",
        params={"operation": "delete"},
        json_body={"Id": sales_receipt_id, "SyncToken": token},
    )
    if error is not None:
        return DeleteSalesReceiptOutput(success=False, error=error)
    entity = _entity(payload, "SalesReceipt")
    return DeleteSalesReceiptOutput(
        success=True,
        sales_receipt_id=_as_str(entity.get("Id")) or sales_receipt_id,
        status=_as_str(entity.get("status")),
    )


class SearchSalesReceiptsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    customer_id: str | None = Field(
        default=None, description="Only receipts for this customer ID"
    )
    doc_number: str | None = Field(
        default=None, description="Only the receipt carrying this reference number"
    )
    txn_date_from: str | None = Field(
        default=None, description="Only receipts dated on or after this date (YYYY-MM-DD)"
    )
    txn_date_to: str | None = Field(
        default=None, description="Only receipts dated on or before this date (YYYY-MM-DD)"
    )
    max_results: int | None = Field(
        default=None, description="Maximum number of receipts to return"
    )
    start_position: int | None = Field(
        default=None, description="1-based index of the first result, for paging"
    )


@tool(args_schema=SearchSalesReceiptsInput)
@serialize_pydantic_return
async def search_sales_receipts(
    auth_type: str,
    auth_data: dict[str, Any],
    customer_id: str | None = None,
    doc_number: str | None = None,
    txn_date_from: str | None = None,
    txn_date_to: str | None = None,
    max_results: int | None = None,
    start_position: int | None = None,
) -> SearchSalesReceiptsOutput:
    """Find sales receipts by customer, number or date range.

    All supplied filters are combined with AND. With no filters at all this
    lists the company's sales receipts.
    """
    clauses: list[str] = []
    if customer_id:
        clauses.append(f"CustomerRef = '{_escape_sql(customer_id)}'")
    if doc_number:
        clauses.append(f"DocNumber = '{_escape_sql(doc_number)}'")
    if txn_date_from:
        clauses.append(f"TxnDate >= '{_escape_sql(txn_date_from)}'")
    if txn_date_to:
        clauses.append(f"TxnDate <= '{_escape_sql(txn_date_to)}'")

    statement = "SELECT * FROM SalesReceipt"
    if clauses:
        statement += " WHERE " + " AND ".join(clauses)
    statement += _sales_query_suffix(max_results, start_position)

    payload, error = await _request(
        auth_type, auth_data, "GET", "/query", params={"query": statement}
    )
    if error is not None:
        return SearchSalesReceiptsOutput(success=False, error=error, query=statement)
    rows = _query_rows(payload, "SalesReceipt")
    return SearchSalesReceiptsOutput(
        success=True,
        sales_receipts=[_parse_sales_receipt(row) for row in rows],
        count=len(rows),
        query=statement,
    )


# --- Credit memos -----------------------------------------------------------


class CreateCreditMemoInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    customer_id: str = Field(description="ID of the customer receiving the credit")
    line_items: list[dict[str, Any]] = Field(
        description=(
            "What is being credited back. Each object accepts item_ref (the "
            "QuickBooks Item ID), qty, unit_price, description, tax_code_ref "
            "and service_date (YYYY-MM-DD). The line total defaults to "
            "qty * unit_price; pass amount to override it"
        )
    )
    txn_date: str | None = Field(default=None, description="Credit memo date as YYYY-MM-DD")
    doc_number: str | None = Field(
        default=None, description="Reference number for the transaction"
    )
    bill_email: str | None = Field(
        default=None, description="Email address the credit memo is addressed to"
    )
    customer_memo: str | None = Field(
        default=None, description="Message shown to the customer on the credit memo"
    )
    private_note: str | None = Field(default=None, description="Internal note")
    currency_code: str | None = Field(default=None, description="ISO 4217 code such as USD")
    bill_address: dict[str, Any] | None = Field(
        default=None,
        description="Billing address. Keys: line1, line2, city, state, postal_code, country",
    )
    global_tax_calculation: str | None = Field(
        default=None,
        description="TaxExcluded, TaxInclusive or NotApplicable. Non-US companies only",
    )


@tool(args_schema=CreateCreditMemoInput)
@serialize_pydantic_return
async def create_credit_memo(
    auth_type: str,
    auth_data: dict[str, Any],
    customer_id: str,
    line_items: list[dict[str, Any]],
    txn_date: str | None = None,
    doc_number: str | None = None,
    bill_email: str | None = None,
    customer_memo: str | None = None,
    private_note: str | None = None,
    currency_code: str | None = None,
    bill_address: dict[str, Any] | None = None,
    global_tax_calculation: str | None = None,
) -> CreateCreditMemoOutput:
    """Issue a credit memo to a customer.

    Records credit the customer can apply against an open invoice — the
    usual answer to a return, an overcharge or a goodwill discount.
    """
    body: dict[str, Any] = {
        "CustomerRef": {"value": customer_id},
        "Line": _build_sales_lines(line_items),
        "TxnDate": txn_date,
        "DocNumber": doc_number,
        "PrivateNote": private_note,
        "GlobalTaxCalculation": global_tax_calculation,
        "BillAddr": _build_sales_address(bill_address),
    }
    if bill_email:
        body["BillEmail"] = {"Address": bill_email}
    if customer_memo:
        body["CustomerMemo"] = {"value": customer_memo}
    if currency_code:
        body["CurrencyRef"] = {"value": currency_code}

    payload, error = await _request(
        auth_type, auth_data, "POST", "/creditmemo", json_body=body
    )
    if error is not None:
        return CreateCreditMemoOutput(success=False, error=error)
    entity = _entity(payload, "CreditMemo")
    return CreateCreditMemoOutput(
        success=True, credit_memo=_parse_credit_memo(entity) if entity else None
    )


class GetCreditMemoInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    credit_memo_id: str = Field(description="ID of the credit memo to read")


@tool(args_schema=GetCreditMemoInput)
@serialize_pydantic_return
async def get_credit_memo(
    auth_type: str,
    auth_data: dict[str, Any],
    credit_memo_id: str,
) -> GetCreditMemoOutput:
    """Read one credit memo by ID, including how much credit is left."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/creditmemo/{_seg(credit_memo_id)}"
    )
    if error is not None:
        return GetCreditMemoOutput(success=False, error=error)
    entity = _entity(payload, "CreditMemo")
    return GetCreditMemoOutput(
        success=True, credit_memo=_parse_credit_memo(entity) if entity else None
    )


class UpdateCreditMemoInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    credit_memo_id: str = Field(description="ID of the credit memo to update")
    customer_id: str | None = Field(
        default=None, description="ID of the customer receiving the credit"
    )
    line_items: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Replacement line items. Supplying this REPLACES every existing "
            "line, so include the lines you want to keep. Each object accepts "
            "item_ref, qty, unit_price, description, tax_code_ref and "
            "service_date"
        ),
    )
    txn_date: str | None = Field(default=None, description="Credit memo date as YYYY-MM-DD")
    doc_number: str | None = Field(
        default=None, description="Reference number for the transaction"
    )
    bill_email: str | None = Field(
        default=None, description="Email address the credit memo is addressed to"
    )
    customer_memo: str | None = Field(
        default=None, description="Message shown to the customer on the credit memo"
    )
    private_note: str | None = Field(default=None, description="Internal note")
    currency_code: str | None = Field(default=None, description="ISO 4217 code such as USD")
    bill_address: dict[str, Any] | None = Field(
        default=None,
        description="Billing address. Keys: line1, line2, city, state, postal_code, country",
    )
    global_tax_calculation: str | None = Field(
        default=None,
        description="TaxExcluded, TaxInclusive or NotApplicable. Non-US companies only",
    )
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request"
        ),
    )


@tool(args_schema=UpdateCreditMemoInput)
@serialize_pydantic_return
async def update_credit_memo(
    auth_type: str,
    auth_data: dict[str, Any],
    credit_memo_id: str,
    customer_id: str | None = None,
    line_items: list[dict[str, Any]] | None = None,
    txn_date: str | None = None,
    doc_number: str | None = None,
    bill_email: str | None = None,
    customer_memo: str | None = None,
    private_note: str | None = None,
    currency_code: str | None = None,
    bill_address: dict[str, Any] | None = None,
    global_tax_calculation: str | None = None,
    sync_token: str | None = None,
) -> UpdateCreditMemoOutput:
    """Change fields on an existing credit memo, leaving the rest alone.

    This is a sparse update: only the values supplied here change.
    """
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "creditmemo", "CreditMemo", credit_memo_id, sync_token
    )
    if error is not None:
        return UpdateCreditMemoOutput(success=False, error=error)

    body: dict[str, Any] = {
        "Id": credit_memo_id,
        "SyncToken": token,
        "sparse": True,
        "TxnDate": txn_date,
        "DocNumber": doc_number,
        "PrivateNote": private_note,
        "GlobalTaxCalculation": global_tax_calculation,
        "BillAddr": _build_sales_address(bill_address),
    }
    if customer_id:
        body["CustomerRef"] = {"value": customer_id}
    if line_items is not None:
        body["Line"] = _build_sales_lines(line_items)
    if bill_email:
        body["BillEmail"] = {"Address": bill_email}
    if customer_memo:
        body["CustomerMemo"] = {"value": customer_memo}
    if currency_code:
        body["CurrencyRef"] = {"value": currency_code}

    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/creditmemo",
        params={"operation": "update"},
        json_body=body,
    )
    if error is not None:
        return UpdateCreditMemoOutput(success=False, error=error)
    entity = _entity(payload, "CreditMemo")
    return UpdateCreditMemoOutput(
        success=True, credit_memo=_parse_credit_memo(entity) if entity else None
    )


class DeleteCreditMemoInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    credit_memo_id: str = Field(description="ID of the credit memo to delete")
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request"
        ),
    )


@tool(args_schema=DeleteCreditMemoInput)
@serialize_pydantic_return
async def delete_credit_memo(
    auth_type: str,
    auth_data: dict[str, Any],
    credit_memo_id: str,
    sync_token: str | None = None,
) -> DeleteCreditMemoOutput:
    """Delete a credit memo permanently.

    Any credit it had already applied to an invoice is released, so the
    invoice balance goes back up.
    """
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "creditmemo", "CreditMemo", credit_memo_id, sync_token
    )
    if error is not None:
        return DeleteCreditMemoOutput(success=False, error=error)

    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/creditmemo",
        params={"operation": "delete"},
        json_body={"Id": credit_memo_id, "SyncToken": token},
    )
    if error is not None:
        return DeleteCreditMemoOutput(success=False, error=error)
    entity = _entity(payload, "CreditMemo")
    return DeleteCreditMemoOutput(
        success=True,
        credit_memo_id=_as_str(entity.get("Id")) or credit_memo_id,
        status=_as_str(entity.get("status")),
    )


class SearchCreditMemosInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    customer_id: str | None = Field(
        default=None, description="Only credit memos for this customer ID"
    )
    doc_number: str | None = Field(
        default=None, description="Only the credit memo carrying this reference number"
    )
    txn_date_from: str | None = Field(
        default=None,
        description="Only credit memos dated on or after this date (YYYY-MM-DD)",
    )
    txn_date_to: str | None = Field(
        default=None,
        description="Only credit memos dated on or before this date (YYYY-MM-DD)",
    )
    max_results: int | None = Field(
        default=None, description="Maximum number of credit memos to return"
    )
    start_position: int | None = Field(
        default=None, description="1-based index of the first result, for paging"
    )


@tool(args_schema=SearchCreditMemosInput)
@serialize_pydantic_return
async def search_credit_memos(
    auth_type: str,
    auth_data: dict[str, Any],
    customer_id: str | None = None,
    doc_number: str | None = None,
    txn_date_from: str | None = None,
    txn_date_to: str | None = None,
    max_results: int | None = None,
    start_position: int | None = None,
) -> SearchCreditMemosOutput:
    """Find credit memos by customer, number or date range.

    All supplied filters are combined with AND. With no filters at all this
    lists the company's credit memos.
    """
    clauses: list[str] = []
    if customer_id:
        clauses.append(f"CustomerRef = '{_escape_sql(customer_id)}'")
    if doc_number:
        clauses.append(f"DocNumber = '{_escape_sql(doc_number)}'")
    if txn_date_from:
        clauses.append(f"TxnDate >= '{_escape_sql(txn_date_from)}'")
    if txn_date_to:
        clauses.append(f"TxnDate <= '{_escape_sql(txn_date_to)}'")

    statement = "SELECT * FROM CreditMemo"
    if clauses:
        statement += " WHERE " + " AND ".join(clauses)
    statement += _sales_query_suffix(max_results, start_position)

    payload, error = await _request(
        auth_type, auth_data, "GET", "/query", params={"query": statement}
    )
    if error is not None:
        return SearchCreditMemosOutput(success=False, error=error, query=statement)
    rows = _query_rows(payload, "CreditMemo")
    return SearchCreditMemosOutput(
        success=True,
        credit_memos=[_parse_credit_memo(row) for row in rows],
        count=len(rows),
        query=statement,
    )


# --- Delivery ---------------------------------------------------------------


class SendInvoiceInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    invoice_id: str = Field(description="ID of the invoice to email")
    email: str | None = Field(
        default=None,
        description=(
            "Address to send to. Defaults to the invoice's own billing email; "
            "supplying one also updates that billing email"
        ),
    )


@tool(args_schema=SendInvoiceInput)
@serialize_pydantic_return
async def send_invoice(
    auth_type: str,
    auth_data: dict[str, Any],
    invoice_id: str,
    email: str | None = None,
) -> SendInvoiceOutput:
    """Email an invoice to the customer.

    QuickBooks sends the mail itself and marks the invoice ``EmailSent``.
    """
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        f"/invoice/{_seg(invoice_id)}/send",
        params={"sendTo": email},
    )
    if error is not None:
        return SendInvoiceOutput(success=False, error=error)
    entity = _entity(payload, "Invoice")
    return SendInvoiceOutput(
        success=True,
        invoice=_parse_invoice(entity) if entity else None,
        email_status=_as_str(entity.get("EmailStatus")),
    )


class SendEstimateInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    estimate_id: str = Field(description="ID of the estimate to email")
    email: str | None = Field(
        default=None,
        description=(
            "Address to send to. Defaults to the estimate's own billing "
            "email; supplying one also updates that billing email"
        ),
    )


@tool(args_schema=SendEstimateInput)
@serialize_pydantic_return
async def send_estimate(
    auth_type: str,
    auth_data: dict[str, Any],
    estimate_id: str,
    email: str | None = None,
) -> SendEstimateOutput:
    """Email an estimate to the customer.

    QuickBooks sends the mail itself and marks the estimate ``EmailSent``.
    """
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        f"/estimate/{_seg(estimate_id)}/send",
        params={"sendTo": email},
    )
    if error is not None:
        return SendEstimateOutput(success=False, error=error)
    entity = _entity(payload, "Estimate")
    return SendEstimateOutput(
        success=True,
        estimate=_parse_estimate(entity) if entity else None,
        email_status=_as_str(entity.get("EmailStatus")),
    )


class VoidInvoiceInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    invoice_id: str = Field(description="ID of the invoice to void")
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request"
        ),
    )


@tool(args_schema=VoidInvoiceInput)
@serialize_pydantic_return
async def void_invoice(
    auth_type: str,
    auth_data: dict[str, Any],
    invoice_id: str,
    sync_token: str | None = None,
) -> VoidInvoiceOutput:
    """Void an invoice, keeping the record on the books.

    The invoice stays in QuickBooks with its number and date intact, but
    its amount drops to zero and it is marked as voided — so the audit
    trail survives. This is the safe way to cancel a billing mistake;
    ``delete_invoice`` erases the transaction instead.
    """
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "invoice", "Invoice", invoice_id, sync_token
    )
    if error is not None:
        return VoidInvoiceOutput(success=False, error=error)

    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/invoice",
        params={"operation": "void"},
        json_body={"Id": invoice_id, "SyncToken": token},
    )
    if error is not None:
        return VoidInvoiceOutput(success=False, error=error)
    entity = _entity(payload, "Invoice")
    return VoidInvoiceOutput(
        success=True, invoice=_parse_invoice(entity) if entity else None
    )


def _make_ref(value: str | None) -> dict[str, str] | None:
    """Wrap an ID in a QuickBooks ``*Ref`` stanza, or None when unset.

    Returning None lets ``_clean_body`` drop the whole reference instead of
    sending ``{"value": null}``, which QuickBooks rejects.
    """
    return {"value": value} if value else None


def _b2_build_query(
    entity: str,
    clauses: list[str],
    max_results: int | None,
    start_position: int | None,
) -> str:
    """Assemble a QuickBooks query statement.

    Clause order is fixed by the API: WHERE, then STARTPOSITION, then
    MAXRESULTS. Caller-supplied literals are already escaped by the time
    they reach ``clauses``; the two paging values are integers, so they
    cannot carry a quote.
    """
    statement = f"SELECT * FROM {entity}"
    if clauses:
        statement += " WHERE " + " AND ".join(clauses)
    if start_position is not None:
        statement += f" STARTPOSITION {start_position}"
    if max_results is not None:
        statement += f" MAXRESULTS {max_results}"
    return statement


def _b2_query_paging(payload: Any) -> tuple[int | None, int | None]:
    """Read ``startPosition`` and ``maxResults`` off a query response."""
    response = _as_dict(_as_dict(payload).get("QueryResponse"))
    return _as_int(response.get("startPosition")), _as_int(response.get("maxResults"))


# --- Request builders -------------------------------------------------------


def _build_vendor_address(
    line1: str | None,
    city: str | None,
    state: str | None,
    postal_code: str | None,
    country: str | None,
) -> dict[str, Any] | None:
    """Build a ``BillAddr`` stanza, or None when no component was supplied."""
    address = _clean_body(
        {
            "Line1": line1,
            "City": city,
            "CountrySubDivisionCode": state,
            "PostalCode": postal_code,
            "Country": country,
        }
    )
    return address or None


def _build_vendor_body(
    *,
    display_name: str | None = None,
    company_name: str | None = None,
    given_name: str | None = None,
    family_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    website: str | None = None,
    print_on_check_name: str | None = None,
    account_number: str | None = None,
    tax_identifier: str | None = None,
    term_id: str | None = None,
    vendor_1099: bool | None = None,
    active: bool | None = None,
    address: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map friendly vendor fields onto the QuickBooks Vendor shape.

    Contact details are nested one level deep in QuickBooks
    (``PrimaryEmailAddr.Address``, ``PrimaryPhone.FreeFormNumber``,
    ``WebAddr.URI``), so each is built only when its value is present —
    an empty wrapper would blank the field on a sparse update.
    """
    body: dict[str, Any] = {
        "DisplayName": display_name,
        "CompanyName": company_name,
        "GivenName": given_name,
        "FamilyName": family_name,
        "PrintOnCheckName": print_on_check_name,
        "AcctNum": account_number,
        "TaxIdentifier": tax_identifier,
        "TermRef": _make_ref(term_id),
        "Vendor1099": vendor_1099,
        "Active": active,
        "PrimaryEmailAddr": {"Address": email} if email else None,
        "PrimaryPhone": {"FreeFormNumber": phone} if phone else None,
        "WebAddr": {"URI": website} if website else None,
        "BillAddr": address,
    }
    return _clean_body(body)


def _build_expense_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Turn friendly line dicts into QuickBooks expense lines.

    Bills and purchases use the expense-side line shape: an amount plus an
    ``AccountBasedExpenseLineDetail`` naming the expense account. A line
    that names ``item_id`` instead becomes an
    ``ItemBasedExpenseLineDetail``, which is what QuickBooks expects when
    the expense is a product bought from the vendor.

    Accepted keys per line: ``amount``, ``account_id``, ``description``,
    ``item_id``, ``quantity``, ``unit_price``, ``billable_status``,
    ``customer_id``, ``class_id``, ``tax_code_id``, ``line_id``.
    """
    built: list[dict[str, Any]] = []
    for raw in lines:
        line = _as_dict(raw)
        item_id = _as_str(line.get("item_id"))
        if item_id:
            detail_type = "ItemBasedExpenseLineDetail"
            detail: dict[str, Any] = {
                "ItemRef": _make_ref(item_id),
                "Qty": _as_float(line.get("quantity")),
                "UnitPrice": _as_float(line.get("unit_price")),
            }
        else:
            detail_type = "AccountBasedExpenseLineDetail"
            detail = {"AccountRef": _make_ref(_as_str(line.get("account_id")))}
        detail["BillableStatus"] = _as_str(line.get("billable_status"))
        detail["CustomerRef"] = _make_ref(_as_str(line.get("customer_id")))
        detail["ClassRef"] = _make_ref(_as_str(line.get("class_id")))
        detail["TaxCodeRef"] = _make_ref(_as_str(line.get("tax_code_id")))
        built.append(
            _clean_body(
                {
                    "Id": _as_str(line.get("line_id")),
                    "DetailType": detail_type,
                    "Amount": _as_float(line.get("amount")),
                    "Description": _as_str(line.get("description")),
                    detail_type: _clean_body(detail),
                }
            )
        )
    return built


def _merge_expense_line_refs(
    built: list[dict[str, Any]],
    existing: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Carry tracking references forward onto replacement expense lines.

    A bill is written as a full overwrite, so a replacement line that arrives
    without its tracking references loses them server-side — silently
    breaking class-based reporting, or un-billing a line that was marked
    billable to a customer, on a bill the caller only meant to retitle.
    Each is copied from the existing line with the same ``Id`` unless the
    caller set it. A line with no counterpart is left exactly as given.
    """
    by_id: dict[str, dict[str, Any]] = {}
    for line in existing:
        line_id = _as_str(line.get("Id"))
        if line_id is not None:
            by_id[line_id] = line

    merged: list[dict[str, Any]] = []
    for line in built:
        line_id = _as_str(line.get("Id"))
        previous = by_id.get(line_id) if line_id is not None else None
        if previous is None:
            merged.append(line)
            continue
        updated = dict(line)
        for detail_key in (
            "AccountBasedExpenseLineDetail",
            "ItemBasedExpenseLineDetail",
        ):
            detail = _as_dict(updated.get(detail_key))
            if not detail:
                continue
            previous_detail = _as_dict(previous.get(detail_key))
            carried = dict(detail)
            for ref in ("ClassRef", "TaxCodeRef", "CustomerRef", "BillableStatus"):
                if ref not in carried and ref in previous_detail:
                    carried[ref] = previous_detail[ref]
            updated[detail_key] = carried
        merged.append(updated)
    return merged


def _build_linked_txns(
    entries: list[dict[str, Any]],
    txn_type: str,
    id_key: str,
) -> list[dict[str, Any]]:
    """Turn ``[{"<id_key>": "12", "amount": 50.0}]`` into payment lines.

    QuickBooks applies a payment to a document through a line whose
    ``LinkedTxn`` names that document, so callers hand over a flat list of
    IDs and amounts and the nested structure is assembled here.
    """
    built: list[dict[str, Any]] = []
    for raw in entries:
        entry = _as_dict(raw)
        txn_id = _as_str(entry.get(id_key)) or _as_str(entry.get("txn_id"))
        built.append(
            _clean_body(
                {
                    "Amount": _as_float(entry.get("amount")),
                    "LinkedTxn": [
                        _clean_body({"TxnId": txn_id, "TxnType": txn_type})
                    ],
                }
            )
        )
    return built


# --- Response parsers -------------------------------------------------------


def _parse_linked_txn(payload: Any) -> LinkedTxnRef:
    txn = _as_dict(payload)
    return LinkedTxnRef(
        txn_id=_as_str(txn.get("TxnId")),
        txn_type=_as_str(txn.get("TxnType")),
        txn_line_id=_as_str(txn.get("TxnLineId")),
    )


def _parse_linked_txn_line(payload: Any) -> LinkedTxnLine:
    line = _as_dict(payload)
    return LinkedTxnLine(
        id=_as_str(line.get("Id")),
        amount=_as_float(line.get("Amount")),
        linked_transactions=[
            _parse_linked_txn(item) for item in _as_dict_list(line.get("LinkedTxn"))
        ],
    )


def _parse_expense_line(payload: Any) -> ExpenseLineItem:
    line = _as_dict(payload)
    account_detail = _as_dict(line.get("AccountBasedExpenseLineDetail"))
    item_detail = _as_dict(line.get("ItemBasedExpenseLineDetail"))
    detail = account_detail or item_detail
    return ExpenseLineItem(
        id=_as_str(line.get("Id")),
        description=_as_str(line.get("Description")),
        amount=_as_float(line.get("Amount")),
        detail_type=_as_str(line.get("DetailType")),
        account_id=_ref(detail.get("AccountRef")),
        account_name=_ref_name(detail.get("AccountRef")),
        item_id=_ref(item_detail.get("ItemRef")),
        item_name=_ref_name(item_detail.get("ItemRef")),
        quantity=_as_float(item_detail.get("Qty")),
        unit_price=_as_float(item_detail.get("UnitPrice")),
        billable_status=_as_str(detail.get("BillableStatus")),
        customer_id=_ref(detail.get("CustomerRef")),
        customer_name=_ref_name(detail.get("CustomerRef")),
        class_id=_ref(detail.get("ClassRef")),
        tax_code_id=_ref(detail.get("TaxCodeRef")),
    )


def _parse_vendor_address(payload: Any) -> VendorAddress | None:
    address = _as_dict(payload)
    if not address:
        return None
    return VendorAddress(
        line1=_as_str(address.get("Line1")),
        line2=_as_str(address.get("Line2")),
        city=_as_str(address.get("City")),
        state=_as_str(address.get("CountrySubDivisionCode")),
        postal_code=_as_str(address.get("PostalCode")),
        country=_as_str(address.get("Country")),
    )


def _parse_vendor(payload: Any) -> VendorRecord:
    vendor = _as_dict(payload)
    meta = _as_dict(vendor.get("MetaData"))
    return VendorRecord(
        id=_as_str(vendor.get("Id")),
        sync_token=_as_str(vendor.get("SyncToken")),
        display_name=_as_str(vendor.get("DisplayName")),
        company_name=_as_str(vendor.get("CompanyName")),
        title=_as_str(vendor.get("Title")),
        given_name=_as_str(vendor.get("GivenName")),
        middle_name=_as_str(vendor.get("MiddleName")),
        family_name=_as_str(vendor.get("FamilyName")),
        suffix=_as_str(vendor.get("Suffix")),
        print_on_check_name=_as_str(vendor.get("PrintOnCheckName")),
        email=_as_str(_as_dict(vendor.get("PrimaryEmailAddr")).get("Address")),
        phone=_as_str(_as_dict(vendor.get("PrimaryPhone")).get("FreeFormNumber")),
        mobile=_as_str(_as_dict(vendor.get("Mobile")).get("FreeFormNumber")),
        fax=_as_str(_as_dict(vendor.get("Fax")).get("FreeFormNumber")),
        website=_as_str(_as_dict(vendor.get("WebAddr")).get("URI")),
        account_number=_as_str(vendor.get("AcctNum")),
        tax_identifier=_as_str(vendor.get("TaxIdentifier")),
        term_id=_ref(vendor.get("TermRef")),
        term_name=_ref_name(vendor.get("TermRef")),
        vendor_1099=_as_bool(vendor.get("Vendor1099")),
        bill_rate=_as_float(vendor.get("BillRate")),
        cost_rate=_as_float(vendor.get("CostRate")),
        balance=_as_float(vendor.get("Balance")),
        currency=_ref(vendor.get("CurrencyRef")),
        active=_as_bool(vendor.get("Active")),
        bill_address=_parse_vendor_address(vendor.get("BillAddr")),
        created_at=_as_str(meta.get("CreateTime")),
        updated_at=_as_str(meta.get("LastUpdatedTime")),
    )


def _parse_bill(payload: Any) -> BillRecord:
    bill = _as_dict(payload)
    meta = _as_dict(bill.get("MetaData"))
    return BillRecord(
        id=_as_str(bill.get("Id")),
        sync_token=_as_str(bill.get("SyncToken")),
        doc_number=_as_str(bill.get("DocNumber")),
        txn_date=_as_str(bill.get("TxnDate")),
        due_date=_as_str(bill.get("DueDate")),
        vendor_id=_ref(bill.get("VendorRef")),
        vendor_name=_ref_name(bill.get("VendorRef")),
        ap_account_id=_ref(bill.get("APAccountRef")),
        ap_account_name=_ref_name(bill.get("APAccountRef")),
        sales_term_id=_ref(bill.get("SalesTermRef")),
        department_id=_ref(bill.get("DepartmentRef")),
        currency=_ref(bill.get("CurrencyRef")),
        exchange_rate=_as_float(bill.get("ExchangeRate")),
        private_note=_as_str(bill.get("PrivateNote")),
        global_tax_calculation=_as_str(bill.get("GlobalTaxCalculation")),
        total_amount=_as_float(bill.get("TotalAmt")),
        balance=_as_float(bill.get("Balance")),
        home_balance=_as_float(bill.get("HomeBalance")),
        lines=[_parse_expense_line(item) for item in _as_dict_list(bill.get("Line"))],
        linked_transactions=[
            _parse_linked_txn(item) for item in _as_dict_list(bill.get("LinkedTxn"))
        ],
        created_at=_as_str(meta.get("CreateTime")),
        updated_at=_as_str(meta.get("LastUpdatedTime")),
    )


def _parse_bill_payment(payload: Any) -> BillPaymentRecord:
    bill_payment = _as_dict(payload)
    meta = _as_dict(bill_payment.get("MetaData"))
    check = _as_dict(bill_payment.get("CheckPayment"))
    card = _as_dict(bill_payment.get("CreditCardPayment"))
    return BillPaymentRecord(
        id=_as_str(bill_payment.get("Id")),
        sync_token=_as_str(bill_payment.get("SyncToken")),
        doc_number=_as_str(bill_payment.get("DocNumber")),
        txn_date=_as_str(bill_payment.get("TxnDate")),
        vendor_id=_ref(bill_payment.get("VendorRef")),
        vendor_name=_ref_name(bill_payment.get("VendorRef")),
        ap_account_id=_ref(bill_payment.get("APAccountRef")),
        ap_account_name=_ref_name(bill_payment.get("APAccountRef")),
        pay_type=_as_str(bill_payment.get("PayType")),
        total_amount=_as_float(bill_payment.get("TotalAmt")),
        private_note=_as_str(bill_payment.get("PrivateNote")),
        currency=_ref(bill_payment.get("CurrencyRef")),
        exchange_rate=_as_float(bill_payment.get("ExchangeRate")),
        department_id=_ref(bill_payment.get("DepartmentRef")),
        bank_account_id=_ref(check.get("BankAccountRef")),
        bank_account_name=_ref_name(check.get("BankAccountRef")),
        check_print_status=_as_str(check.get("PrintStatus")),
        credit_card_account_id=_ref(card.get("CCAccountRef")),
        credit_card_account_name=_ref_name(card.get("CCAccountRef")),
        process_bill_payment=_as_bool(bill_payment.get("ProcessBillPayment")),
        lines=[
            _parse_linked_txn_line(item)
            for item in _as_dict_list(bill_payment.get("Line"))
        ],
        created_at=_as_str(meta.get("CreateTime")),
        updated_at=_as_str(meta.get("LastUpdatedTime")),
    )


def _parse_payment(payload: Any) -> PaymentRecord:
    payment = _as_dict(payload)
    meta = _as_dict(payment.get("MetaData"))
    return PaymentRecord(
        id=_as_str(payment.get("Id")),
        sync_token=_as_str(payment.get("SyncToken")),
        txn_date=_as_str(payment.get("TxnDate")),
        customer_id=_ref(payment.get("CustomerRef")),
        customer_name=_ref_name(payment.get("CustomerRef")),
        total_amount=_as_float(payment.get("TotalAmt")),
        unapplied_amount=_as_float(payment.get("UnappliedAmt")),
        payment_method_id=_ref(payment.get("PaymentMethodRef")),
        payment_method_name=_ref_name(payment.get("PaymentMethodRef")),
        deposit_to_account_id=_ref(payment.get("DepositToAccountRef")),
        deposit_to_account_name=_ref_name(payment.get("DepositToAccountRef")),
        payment_ref_num=_as_str(payment.get("PaymentRefNum")),
        private_note=_as_str(payment.get("PrivateNote")),
        currency=_ref(payment.get("CurrencyRef")),
        exchange_rate=_as_float(payment.get("ExchangeRate")),
        project_id=_ref(payment.get("ProjectRef")),
        lines=[
            _parse_linked_txn_line(item) for item in _as_dict_list(payment.get("Line"))
        ],
        created_at=_as_str(meta.get("CreateTime")),
        updated_at=_as_str(meta.get("LastUpdatedTime")),
    )


def _parse_purchase(payload: Any) -> PurchaseRecord:
    purchase = _as_dict(payload)
    meta = _as_dict(purchase.get("MetaData"))
    entity = _as_dict(purchase.get("EntityRef"))
    return PurchaseRecord(
        id=_as_str(purchase.get("Id")),
        sync_token=_as_str(purchase.get("SyncToken")),
        doc_number=_as_str(purchase.get("DocNumber")),
        txn_date=_as_str(purchase.get("TxnDate")),
        payment_type=_as_str(purchase.get("PaymentType")),
        account_id=_ref(purchase.get("AccountRef")),
        account_name=_ref_name(purchase.get("AccountRef")),
        entity_id=_ref(purchase.get("EntityRef")),
        entity_name=_ref_name(purchase.get("EntityRef")),
        entity_type=_as_str(entity.get("type")),
        payment_method_id=_ref(purchase.get("PaymentMethodRef")),
        payment_method_name=_ref_name(purchase.get("PaymentMethodRef")),
        department_id=_ref(purchase.get("DepartmentRef")),
        currency=_ref(purchase.get("CurrencyRef")),
        exchange_rate=_as_float(purchase.get("ExchangeRate")),
        private_note=_as_str(purchase.get("PrivateNote")),
        print_status=_as_str(purchase.get("PrintStatus")),
        global_tax_calculation=_as_str(purchase.get("GlobalTaxCalculation")),
        credit=_as_bool(purchase.get("Credit")),
        total_amount=_as_float(purchase.get("TotalAmt")),
        lines=[
            _parse_expense_line(item) for item in _as_dict_list(purchase.get("Line"))
        ],
        linked_transactions=[
            _parse_linked_txn(item) for item in _as_dict_list(purchase.get("LinkedTxn"))
        ],
        created_at=_as_str(meta.get("CreateTime")),
        updated_at=_as_str(meta.get("LastUpdatedTime")),
    )


# --- Vendors ----------------------------------------------------------------


class CreateVendorInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    display_name: str | None = Field(
        default=None,
        description=(
            "Name to show for the vendor. Must be unique across all vendors, "
            "customers and employees. Required unless a given/family name is "
            "supplied for QuickBooks to build one from."
        ),
    )
    company_name: str | None = Field(default=None, description="Vendor's company name")
    given_name: str | None = Field(default=None, description="Contact's first name")
    family_name: str | None = Field(default=None, description="Contact's last name")
    email: str | None = Field(default=None, description="Primary email address")
    phone: str | None = Field(default=None, description="Primary phone number")
    website: str | None = Field(default=None, description="Website URL")
    print_on_check_name: str | None = Field(
        default=None, description="Name to print on cheques paid to this vendor"
    )
    account_number: str | None = Field(
        default=None, description="Your account number with this vendor"
    )
    tax_identifier: str | None = Field(
        default=None, description="Vendor's tax ID (EIN or SSN)"
    )
    term_id: str | None = Field(
        default=None, description="ID of the default payment term for this vendor"
    )
    vendor_1099: bool | None = Field(
        default=None, description="True if this vendor is a 1099 contractor"
    )
    bill_address_line1: str | None = Field(
        default=None, description="Billing address street line"
    )
    bill_address_city: str | None = Field(default=None, description="Billing city")
    bill_address_state: str | None = Field(
        default=None, description="Billing state, province or region"
    )
    bill_address_postal_code: str | None = Field(
        default=None, description="Billing postal or ZIP code"
    )
    bill_address_country: str | None = Field(default=None, description="Billing country")


@tool(args_schema=CreateVendorInput)
@serialize_pydantic_return
async def create_vendor(
    auth_type: str,
    auth_data: dict[str, Any],
    display_name: str | None = None,
    company_name: str | None = None,
    given_name: str | None = None,
    family_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    website: str | None = None,
    print_on_check_name: str | None = None,
    account_number: str | None = None,
    tax_identifier: str | None = None,
    term_id: str | None = None,
    vendor_1099: bool | None = None,
    bill_address_line1: str | None = None,
    bill_address_city: str | None = None,
    bill_address_state: str | None = None,
    bill_address_postal_code: str | None = None,
    bill_address_country: str | None = None,
) -> CreateVendorOutput:
    """Create a vendor: a supplier the company buys from and pays bills to."""
    if not (display_name or given_name or family_name):
        return CreateVendorOutput(
            success=False,
            error=(
                "A vendor needs a display_name, or a given_name/family_name for "
                "QuickBooks to build one from."
            ),
        )
    body = _build_vendor_body(
        display_name=display_name,
        company_name=company_name,
        given_name=given_name,
        family_name=family_name,
        email=email,
        phone=phone,
        website=website,
        print_on_check_name=print_on_check_name,
        account_number=account_number,
        tax_identifier=tax_identifier,
        term_id=term_id,
        vendor_1099=vendor_1099,
        address=_build_vendor_address(
            bill_address_line1,
            bill_address_city,
            bill_address_state,
            bill_address_postal_code,
            bill_address_country,
        ),
    )
    payload, error = await _request(
        auth_type, auth_data, "POST", "/vendor", json_body=body
    )
    if error is not None:
        return CreateVendorOutput(success=False, error=error)
    return CreateVendorOutput(
        success=True, vendor=_parse_vendor(_entity(payload, "Vendor"))
    )


class GetVendorInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    vendor_id: str = Field(description="ID of the vendor to read")


@tool(args_schema=GetVendorInput)
@serialize_pydantic_return
async def get_vendor(
    auth_type: str,
    auth_data: dict[str, Any],
    vendor_id: str,
) -> GetVendorOutput:
    """Read one vendor by ID, including its open balance and contact details."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/vendor/{_seg(vendor_id)}"
    )
    if error is not None:
        return GetVendorOutput(success=False, error=error)
    return GetVendorOutput(
        success=True, vendor=_parse_vendor(_entity(payload, "Vendor"))
    )


class UpdateVendorInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    vendor_id: str = Field(description="ID of the vendor to update")
    display_name: str | None = Field(default=None, description="New display name")
    company_name: str | None = Field(default=None, description="New company name")
    given_name: str | None = Field(default=None, description="New first name")
    family_name: str | None = Field(default=None, description="New last name")
    email: str | None = Field(default=None, description="New primary email address")
    phone: str | None = Field(default=None, description="New primary phone number")
    website: str | None = Field(default=None, description="New website URL")
    print_on_check_name: str | None = Field(
        default=None, description="New name to print on cheques"
    )
    account_number: str | None = Field(
        default=None, description="New account number with this vendor"
    )
    tax_identifier: str | None = Field(default=None, description="New tax ID")
    term_id: str | None = Field(default=None, description="New default payment term ID")
    vendor_1099: bool | None = Field(
        default=None, description="Whether this vendor is a 1099 contractor"
    )
    active: bool | None = Field(
        default=None, description="Set false to retire the vendor, true to restore it"
    )
    bill_address_line1: str | None = Field(
        default=None, description="New billing address street line"
    )
    bill_address_city: str | None = Field(default=None, description="New billing city")
    bill_address_state: str | None = Field(
        default=None, description="New billing state, province or region"
    )
    bill_address_postal_code: str | None = Field(
        default=None, description="New billing postal or ZIP code"
    )
    bill_address_country: str | None = Field(
        default=None, description="New billing country"
    )
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request."
        ),
    )


@tool(args_schema=UpdateVendorInput)
@serialize_pydantic_return
async def update_vendor(
    auth_type: str,
    auth_data: dict[str, Any],
    vendor_id: str,
    display_name: str | None = None,
    company_name: str | None = None,
    given_name: str | None = None,
    family_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    website: str | None = None,
    print_on_check_name: str | None = None,
    account_number: str | None = None,
    tax_identifier: str | None = None,
    term_id: str | None = None,
    vendor_1099: bool | None = None,
    active: bool | None = None,
    bill_address_line1: str | None = None,
    bill_address_city: str | None = None,
    bill_address_state: str | None = None,
    bill_address_postal_code: str | None = None,
    bill_address_country: str | None = None,
    sync_token: str | None = None,
) -> UpdateVendorOutput:
    """Change a vendor's details. Only the fields you supply are altered."""
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "vendor", "Vendor", vendor_id, sync_token
    )
    if error is not None:
        return UpdateVendorOutput(success=False, error=error)
    body: dict[str, Any] = {"Id": vendor_id, "SyncToken": token, "sparse": True}
    body.update(
        _build_vendor_body(
            display_name=display_name,
            company_name=company_name,
            given_name=given_name,
            family_name=family_name,
            email=email,
            phone=phone,
            website=website,
            print_on_check_name=print_on_check_name,
            account_number=account_number,
            tax_identifier=tax_identifier,
            term_id=term_id,
            vendor_1099=vendor_1099,
            active=active,
            address=_build_vendor_address(
                bill_address_line1,
                bill_address_city,
                bill_address_state,
                bill_address_postal_code,
                bill_address_country,
            ),
        )
    )
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/vendor",
        params={"operation": "update"},
        json_body=body,
    )
    if error is not None:
        return UpdateVendorOutput(success=False, error=error)
    return UpdateVendorOutput(
        success=True, vendor=_parse_vendor(_entity(payload, "Vendor"))
    )


class DeleteVendorInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    vendor_id: str = Field(description="ID of the vendor to retire")
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request."
        ),
    )


@tool(args_schema=DeleteVendorInput)
@serialize_pydantic_return
async def delete_vendor(
    auth_type: str,
    auth_data: dict[str, Any],
    vendor_id: str,
    sync_token: str | None = None,
) -> DeleteVendorOutput:
    """Deactivate a vendor.

    QuickBooks does not permit deleting vendors, so this marks the record
    inactive: it disappears from pick lists while its bills and payments stay
    intact. Calling update_vendor with active=true reverses it.
    """
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "vendor", "Vendor", vendor_id, sync_token
    )
    if error is not None:
        return DeleteVendorOutput(success=False, error=error, vendor_id=vendor_id)
    body: dict[str, Any] = {
        "Id": vendor_id,
        "SyncToken": token,
        "sparse": True,
        "Active": False,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/vendor",
        params={"operation": "update"},
        json_body=body,
    )
    if error is not None:
        return DeleteVendorOutput(success=False, error=error, vendor_id=vendor_id)
    vendor = _parse_vendor(_entity(payload, "Vendor"))
    return DeleteVendorOutput(
        success=True,
        vendor_id=vendor.id or vendor_id,
        deactivated=True,
        vendor=vendor,
    )


class SearchVendorsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    display_name: str | None = Field(
        default=None, description="Exact display name to match"
    )
    company_name: str | None = Field(
        default=None, description="Exact company name to match"
    )
    name_contains: str | None = Field(
        default=None, description="Substring to look for anywhere in the display name"
    )
    active: bool | None = Field(
        default=None, description="True for active vendors only, false for retired ones"
    )
    max_results: int | None = Field(
        default=None, description="Maximum number of vendors to return (QuickBooks caps at 1000)"
    )
    start_position: int | None = Field(
        default=None, description="1-based index of the first result, for paging"
    )


@tool(args_schema=SearchVendorsInput)
@serialize_pydantic_return
async def search_vendors(
    auth_type: str,
    auth_data: dict[str, Any],
    display_name: str | None = None,
    company_name: str | None = None,
    name_contains: str | None = None,
    active: bool | None = None,
    max_results: int | None = None,
    start_position: int | None = None,
) -> SearchVendorsOutput:
    """Find vendors by name or active state. Omit every filter to list them all."""
    clauses: list[str] = []
    if display_name:
        clauses.append(f"DisplayName = '{_escape_sql(display_name)}'")
    if company_name:
        clauses.append(f"CompanyName = '{_escape_sql(company_name)}'")
    if name_contains:
        clauses.append(f"DisplayName LIKE '%{_escape_sql(name_contains)}%'")
    if active is not None:
        clauses.append(f"Active = {'true' if active else 'false'}")
    statement = _b2_build_query("Vendor", clauses, max_results, start_position)
    payload, error = await _request(
        auth_type, auth_data, "GET", "/query", params={"query": statement}
    )
    if error is not None:
        return SearchVendorsOutput(success=False, error=error)
    rows = _query_rows(payload, "Vendor")
    position, returned = _b2_query_paging(payload)
    return SearchVendorsOutput(
        success=True,
        vendors=[_parse_vendor(row) for row in rows],
        count=len(rows),
        start_position=position,
        max_results=returned,
    )


# --- Bills ------------------------------------------------------------------


_B2_LINES_DESCRIPTION = (
    "Expense lines. Each entry is an object: {'amount': 100.0, 'account_id': "
    "'7', 'description': 'Office rent'}. Use 'item_id' with 'quantity' and "
    "'unit_price' instead of 'account_id' when buying a product. Optional "
    "per-line keys: 'customer_id', 'billable_status' (Billable, NotBillable, "
    "HasBeenBilled), 'class_id', 'tax_code_id'."
)


class CreateBillInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    vendor_id: str = Field(description="ID of the vendor who sent the bill")
    lines: list[dict[str, Any]] = Field(description=_B2_LINES_DESCRIPTION)
    txn_date: str | None = Field(
        default=None, description="Bill date as YYYY-MM-DD; defaults to today"
    )
    due_date: str | None = Field(
        default=None,
        description="Payment due date as YYYY-MM-DD; derived from the term when omitted",
    )
    doc_number: str | None = Field(
        default=None, description="The vendor's invoice or reference number"
    )
    private_note: str | None = Field(
        default=None, description="Internal memo, not visible to the vendor"
    )
    ap_account_id: str | None = Field(
        default=None,
        description="Accounts Payable account to credit; implied when the company has one",
    )
    sales_term_id: str | None = Field(
        default=None, description="ID of the payment term governing the due date"
    )
    department_id: str | None = Field(
        default=None, description="ID of the location or department for this bill"
    )
    currency_code: str | None = Field(
        default=None,
        description="Three-letter currency code, required if multicurrency is on",
    )


@tool(args_schema=CreateBillInput)
@serialize_pydantic_return
async def create_bill(
    auth_type: str,
    auth_data: dict[str, Any],
    vendor_id: str,
    lines: list[dict[str, Any]],
    txn_date: str | None = None,
    due_date: str | None = None,
    doc_number: str | None = None,
    private_note: str | None = None,
    ap_account_id: str | None = None,
    sales_term_id: str | None = None,
    department_id: str | None = None,
    currency_code: str | None = None,
) -> CreateBillOutput:
    """Record a bill: money a vendor has invoiced but the company has not yet paid.

    Use this for an unpaid obligation. If the expense was paid on the spot,
    use create_purchase instead.
    """
    built_lines = _build_expense_lines(lines)
    if not built_lines:
        return CreateBillOutput(
            success=False, error="A bill needs at least one expense line."
        )
    body: dict[str, Any] = {
        "VendorRef": _make_ref(vendor_id),
        "Line": built_lines,
        "TxnDate": txn_date,
        "DueDate": due_date,
        "DocNumber": doc_number,
        "PrivateNote": private_note,
        "APAccountRef": _make_ref(ap_account_id),
        "SalesTermRef": _make_ref(sales_term_id),
        "DepartmentRef": _make_ref(department_id),
        "CurrencyRef": _make_ref(currency_code),
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/bill", json_body=body
    )
    if error is not None:
        return CreateBillOutput(success=False, error=error)
    return CreateBillOutput(success=True, bill=_parse_bill(_entity(payload, "Bill")))


class GetBillInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    bill_id: str = Field(description="ID of the bill to read")


@tool(args_schema=GetBillInput)
@serialize_pydantic_return
async def get_bill(
    auth_type: str,
    auth_data: dict[str, Any],
    bill_id: str,
) -> GetBillOutput:
    """Read one bill by ID, including its expense lines and unpaid balance."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/bill/{_seg(bill_id)}"
    )
    if error is not None:
        return GetBillOutput(success=False, error=error)
    return GetBillOutput(success=True, bill=_parse_bill(_entity(payload, "Bill")))


class UpdateBillInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    bill_id: str = Field(description="ID of the bill to update")
    vendor_id: str | None = Field(default=None, description="New vendor ID")
    lines: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Replacement expense lines. Omit to leave the bill's existing "
            "lines untouched; supplying this replaces the whole set. "
            + _B2_LINES_DESCRIPTION
        ),
    )
    txn_date: str | None = Field(default=None, description="New bill date as YYYY-MM-DD")
    due_date: str | None = Field(default=None, description="New due date as YYYY-MM-DD")
    doc_number: str | None = Field(
        default=None, description="New vendor invoice or reference number"
    )
    private_note: str | None = Field(default=None, description="New internal memo")
    ap_account_id: str | None = Field(
        default=None, description="New Accounts Payable account ID"
    )
    sales_term_id: str | None = Field(default=None, description="New payment term ID")
    department_id: str | None = Field(
        default=None, description="New location or department ID"
    )
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional, and it saves no round "
            "trip here because this action reads the bill either way, but it "
            "is honoured when supplied."
        ),
    )


@tool(args_schema=UpdateBillInput)
@serialize_pydantic_return
async def update_bill(
    auth_type: str,
    auth_data: dict[str, Any],
    bill_id: str,
    vendor_id: str | None = None,
    lines: list[dict[str, Any]] | None = None,
    txn_date: str | None = None,
    due_date: str | None = None,
    doc_number: str | None = None,
    private_note: str | None = None,
    ap_account_id: str | None = None,
    sales_term_id: str | None = None,
    department_id: str | None = None,
    sync_token: str | None = None,
) -> UpdateBillOutput:
    """Change a bill. Anything you do not mention keeps its current value.

    The bill is read first and your changes are laid over it, because
    QuickBooks rewrites a bill wholesale rather than patching it. Omitting
    lines leaves the existing ones exactly as they are; supplying lines
    replaces the set, and each replacement inherits the class and tax code of
    the line it replaces unless you set them yourself.
    """
    # A bill is written as a full overwrite: anything absent from the body is
    # cleared server-side, which silently strips line-level ClassRef and
    # TaxCodeRef and breaks class-based reporting. So the current record is
    # read and the caller's changes are overlaid onto it. That read also
    # yields the SyncToken.
    current, error = await _request(
        auth_type, auth_data, "GET", f"/bill/{_seg(bill_id)}"
    )
    if error is not None:
        return UpdateBillOutput(success=False, error=error)
    record = dict(_entity(current, "Bill"))
    record.pop("sparse", None)
    token = sync_token or _as_str(record.get("SyncToken"))
    if token is None:
        return UpdateBillOutput(
            success=False,
            error=(
                f"QuickBooks did not return a SyncToken for Bill {bill_id}; "
                "pass sync_token explicitly."
            ),
        )
    changes: dict[str, Any] = {
        "VendorRef": _make_ref(vendor_id),
        "TxnDate": txn_date,
        "DueDate": due_date,
        "DocNumber": doc_number,
        "PrivateNote": private_note,
        "APAccountRef": _make_ref(ap_account_id),
        "SalesTermRef": _make_ref(sales_term_id),
        "DepartmentRef": _make_ref(department_id),
    }
    if lines:
        # Line is only touched when the caller sent one. Left alone, the array
        # read a moment ago rides along verbatim — an omitted Line under a
        # full overwrite would wipe every line on the bill.
        changes["Line"] = _merge_expense_line_refs(
            _build_expense_lines(lines), _as_dict_list(record.get("Line"))
        )
    record.update(_clean_body(changes))
    record["Id"] = bill_id
    record["SyncToken"] = token
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/bill",
        params={"operation": "update"},
        json_body=record,
    )
    if error is not None:
        return UpdateBillOutput(success=False, error=error)
    return UpdateBillOutput(success=True, bill=_parse_bill(_entity(payload, "Bill")))


class DeleteBillInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    bill_id: str = Field(description="ID of the bill to delete")
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request."
        ),
    )


@tool(args_schema=DeleteBillInput)
@serialize_pydantic_return
async def delete_bill(
    auth_type: str,
    auth_data: dict[str, Any],
    bill_id: str,
    sync_token: str | None = None,
) -> DeleteBillOutput:
    """Delete a bill.

    Any bill payment already applied to it must be unlinked first, or
    QuickBooks refuses the delete.
    """
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "bill", "Bill", bill_id, sync_token
    )
    if error is not None:
        return DeleteBillOutput(success=False, error=error, bill_id=bill_id)
    body: dict[str, Any] = {"Id": bill_id, "SyncToken": token}
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/bill",
        params={"operation": "delete"},
        json_body=body,
    )
    if error is not None:
        return DeleteBillOutput(success=False, error=error, bill_id=bill_id)
    deleted = _entity(payload, "Bill")
    return DeleteBillOutput(
        success=True,
        bill_id=_as_str(deleted.get("Id")) or bill_id,
        status=_as_str(deleted.get("status")),
        deleted=True,
    )


class SearchBillsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    vendor_id: str | None = Field(default=None, description="Only bills from this vendor")
    doc_number: str | None = Field(
        default=None, description="Exact vendor invoice or reference number"
    )
    ap_account_id: str | None = Field(
        default=None, description="Only bills against this Accounts Payable account"
    )
    txn_date_from: str | None = Field(
        default=None, description="Earliest bill date, YYYY-MM-DD"
    )
    txn_date_to: str | None = Field(
        default=None, description="Latest bill date, YYYY-MM-DD"
    )
    due_date_from: str | None = Field(
        default=None, description="Earliest due date, YYYY-MM-DD"
    )
    due_date_to: str | None = Field(
        default=None, description="Latest due date, YYYY-MM-DD"
    )
    unpaid_only: bool | None = Field(
        default=None, description="True to return only bills with an outstanding balance"
    )
    max_results: int | None = Field(
        default=None, description="Maximum number of bills to return (QuickBooks caps at 1000)"
    )
    start_position: int | None = Field(
        default=None, description="1-based index of the first result, for paging"
    )


@tool(args_schema=SearchBillsInput)
@serialize_pydantic_return
async def search_bills(
    auth_type: str,
    auth_data: dict[str, Any],
    vendor_id: str | None = None,
    doc_number: str | None = None,
    ap_account_id: str | None = None,
    txn_date_from: str | None = None,
    txn_date_to: str | None = None,
    due_date_from: str | None = None,
    due_date_to: str | None = None,
    unpaid_only: bool | None = None,
    max_results: int | None = None,
    start_position: int | None = None,
) -> SearchBillsOutput:
    """Find bills by vendor, date, due date or unpaid state.

    Use unpaid_only to answer "what do we owe?" — it keeps bills whose
    remaining balance is above zero.
    """
    clauses: list[str] = []
    if vendor_id:
        clauses.append(f"VendorRef = '{_escape_sql(vendor_id)}'")
    if doc_number:
        clauses.append(f"DocNumber = '{_escape_sql(doc_number)}'")
    if ap_account_id:
        clauses.append(f"APAccountRef = '{_escape_sql(ap_account_id)}'")
    if txn_date_from:
        clauses.append(f"TxnDate >= '{_escape_sql(txn_date_from)}'")
    if txn_date_to:
        clauses.append(f"TxnDate <= '{_escape_sql(txn_date_to)}'")
    if due_date_from:
        clauses.append(f"DueDate >= '{_escape_sql(due_date_from)}'")
    if due_date_to:
        clauses.append(f"DueDate <= '{_escape_sql(due_date_to)}'")
    if unpaid_only:
        clauses.append("Balance > '0'")
    statement = _b2_build_query("Bill", clauses, max_results, start_position)
    payload, error = await _request(
        auth_type, auth_data, "GET", "/query", params={"query": statement}
    )
    if error is not None:
        return SearchBillsOutput(success=False, error=error)
    rows = _query_rows(payload, "Bill")
    position, returned = _b2_query_paging(payload)
    return SearchBillsOutput(
        success=True,
        bills=[_parse_bill(row) for row in rows],
        count=len(rows),
        start_position=position,
        max_results=returned,
    )


# --- Bill payments (money out, to a vendor) ---------------------------------


_B2_APPLIED_BILLS_DESCRIPTION = (
    "Bills this payment settles. Each entry is an object: {'bill_id': '12', "
    "'amount': 200.0}. Leave empty to record the payment as an unapplied "
    "credit with the vendor."
)


class CreateBillPaymentInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    vendor_id: str = Field(description="ID of the vendor being paid")
    total_amount: float = Field(description="Total amount paid to the vendor")
    pay_type: str = Field(description="How the vendor was paid: Check or CreditCard")
    bank_account_id: str | None = Field(
        default=None,
        description="Bank account the money leaves. Required when pay_type is Check.",
    )
    credit_card_account_id: str | None = Field(
        default=None,
        description=(
            "Credit card account charged. Required when pay_type is CreditCard."
        ),
    )
    applied_bills: list[dict[str, Any]] | None = Field(
        default=None, description=_B2_APPLIED_BILLS_DESCRIPTION
    )
    txn_date: str | None = Field(
        default=None, description="Payment date as YYYY-MM-DD; defaults to today"
    )
    doc_number: str | None = Field(
        default=None, description="Cheque number or payment reference"
    )
    private_note: str | None = Field(default=None, description="Internal memo")
    ap_account_id: str | None = Field(
        default=None, description="Accounts Payable account to debit"
    )
    currency_code: str | None = Field(
        default=None,
        description="Three-letter currency code, required if multicurrency is on",
    )


@tool(args_schema=CreateBillPaymentInput)
@serialize_pydantic_return
async def create_bill_payment(
    auth_type: str,
    auth_data: dict[str, Any],
    vendor_id: str,
    total_amount: float,
    pay_type: str,
    bank_account_id: str | None = None,
    credit_card_account_id: str | None = None,
    applied_bills: list[dict[str, Any]] | None = None,
    txn_date: str | None = None,
    doc_number: str | None = None,
    private_note: str | None = None,
    ap_account_id: str | None = None,
    currency_code: str | None = None,
) -> CreateBillPaymentOutput:
    """Pay a vendor: record money going OUT to settle one or more bills.

    This is the accounts-payable side. To record money coming IN from a
    customer against an invoice, use create_payment instead.
    """
    normalized = pay_type.strip().lower()
    if normalized == "check":
        if not bank_account_id:
            return CreateBillPaymentOutput(
                success=False,
                error="pay_type 'Check' requires bank_account_id.",
            )
        settled_pay_type = "Check"
        payment_detail: dict[str, Any] = {
            "CheckPayment": {"BankAccountRef": _make_ref(bank_account_id)}
        }
    elif normalized == "creditcard":
        if not credit_card_account_id:
            return CreateBillPaymentOutput(
                success=False,
                error="pay_type 'CreditCard' requires credit_card_account_id.",
            )
        settled_pay_type = "CreditCard"
        payment_detail = {
            "CreditCardPayment": {"CCAccountRef": _make_ref(credit_card_account_id)}
        }
    else:
        return CreateBillPaymentOutput(
            success=False,
            error=f"pay_type must be 'Check' or 'CreditCard', got {pay_type!r}.",
        )
    body: dict[str, Any] = {
        "VendorRef": _make_ref(vendor_id),
        "TotalAmt": total_amount,
        "PayType": settled_pay_type,
        "Line": _build_linked_txns(applied_bills or [], "Bill", "bill_id") or None,
        "TxnDate": txn_date,
        "DocNumber": doc_number,
        "PrivateNote": private_note,
        "APAccountRef": _make_ref(ap_account_id),
        "CurrencyRef": _make_ref(currency_code),
    }
    body.update(payment_detail)
    payload, error = await _request(
        auth_type, auth_data, "POST", "/billpayment", json_body=body
    )
    if error is not None:
        return CreateBillPaymentOutput(success=False, error=error)
    return CreateBillPaymentOutput(
        success=True,
        bill_payment=_parse_bill_payment(_entity(payload, "BillPayment")),
    )


class GetBillPaymentInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    bill_payment_id: str = Field(description="ID of the bill payment to read")


@tool(args_schema=GetBillPaymentInput)
@serialize_pydantic_return
async def get_bill_payment(
    auth_type: str,
    auth_data: dict[str, Any],
    bill_payment_id: str,
) -> GetBillPaymentOutput:
    """Read one payment made to a vendor, including which bills it settled."""
    payload, error = await _request(
        auth_type,
        auth_data,
        "GET",
        f"/billpayment/{_seg(bill_payment_id)}",
    )
    if error is not None:
        return GetBillPaymentOutput(success=False, error=error)
    return GetBillPaymentOutput(
        success=True,
        bill_payment=_parse_bill_payment(_entity(payload, "BillPayment")),
    )


class UpdateBillPaymentInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    bill_payment_id: str = Field(description="ID of the bill payment to update")
    vendor_id: str | None = Field(default=None, description="New vendor ID")
    total_amount: float | None = Field(default=None, description="New total amount paid")
    pay_type: str | None = Field(
        default=None, description="New payment method: Check or CreditCard"
    )
    bank_account_id: str | None = Field(
        default=None, description="New bank account ID, for a Check payment"
    )
    credit_card_account_id: str | None = Field(
        default=None, description="New credit card account ID, for a CreditCard payment"
    )
    applied_bills: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Replacement set of settled bills; supplying this replaces every "
            "existing line. " + _B2_APPLIED_BILLS_DESCRIPTION
        ),
    )
    txn_date: str | None = Field(
        default=None, description="New payment date as YYYY-MM-DD"
    )
    doc_number: str | None = Field(
        default=None, description="New cheque number or payment reference"
    )
    private_note: str | None = Field(default=None, description="New internal memo")
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request."
        ),
    )


@tool(args_schema=UpdateBillPaymentInput)
@serialize_pydantic_return
async def update_bill_payment(
    auth_type: str,
    auth_data: dict[str, Any],
    bill_payment_id: str,
    vendor_id: str | None = None,
    total_amount: float | None = None,
    pay_type: str | None = None,
    bank_account_id: str | None = None,
    credit_card_account_id: str | None = None,
    applied_bills: list[dict[str, Any]] | None = None,
    txn_date: str | None = None,
    doc_number: str | None = None,
    private_note: str | None = None,
    sync_token: str | None = None,
) -> UpdateBillPaymentOutput:
    """Change a payment made to a vendor. Only the fields you supply are altered."""
    token, error = await _resolve_sync_token(
        auth_type,
        auth_data,
        "billpayment",
        "BillPayment",
        bill_payment_id,
        sync_token,
    )
    if error is not None:
        return UpdateBillPaymentOutput(success=False, error=error)
    settled_pay_type: str | None = None
    if pay_type:
        normalized = pay_type.strip().lower()
        if normalized == "check":
            settled_pay_type = "Check"
        elif normalized == "creditcard":
            settled_pay_type = "CreditCard"
        else:
            return UpdateBillPaymentOutput(
                success=False,
                error=f"pay_type must be 'Check' or 'CreditCard', got {pay_type!r}.",
            )
    body: dict[str, Any] = {
        "Id": bill_payment_id,
        "SyncToken": token,
        "sparse": True,
        "VendorRef": _make_ref(vendor_id),
        "TotalAmt": total_amount,
        "PayType": settled_pay_type,
        "TxnDate": txn_date,
        "DocNumber": doc_number,
        "PrivateNote": private_note,
        "Line": _build_linked_txns(applied_bills, "Bill", "bill_id")
        if applied_bills
        else None,
        "CheckPayment": {"BankAccountRef": _make_ref(bank_account_id)}
        if bank_account_id
        else None,
        "CreditCardPayment": {"CCAccountRef": _make_ref(credit_card_account_id)}
        if credit_card_account_id
        else None,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/billpayment",
        params={"operation": "update"},
        json_body=body,
    )
    if error is not None:
        return UpdateBillPaymentOutput(success=False, error=error)
    return UpdateBillPaymentOutput(
        success=True,
        bill_payment=_parse_bill_payment(_entity(payload, "BillPayment")),
    )


class DeleteBillPaymentInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    bill_payment_id: str = Field(description="ID of the bill payment to delete")
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request."
        ),
    )


@tool(args_schema=DeleteBillPaymentInput)
@serialize_pydantic_return
async def delete_bill_payment(
    auth_type: str,
    auth_data: dict[str, Any],
    bill_payment_id: str,
    sync_token: str | None = None,
) -> DeleteBillPaymentOutput:
    """Delete a payment made to a vendor, restoring the balance on its bills."""
    token, error = await _resolve_sync_token(
        auth_type,
        auth_data,
        "billpayment",
        "BillPayment",
        bill_payment_id,
        sync_token,
    )
    if error is not None:
        return DeleteBillPaymentOutput(
            success=False, error=error, bill_payment_id=bill_payment_id
        )
    body: dict[str, Any] = {"Id": bill_payment_id, "SyncToken": token}
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/billpayment",
        params={"operation": "delete"},
        json_body=body,
    )
    if error is not None:
        return DeleteBillPaymentOutput(
            success=False, error=error, bill_payment_id=bill_payment_id
        )
    deleted = _entity(payload, "BillPayment")
    return DeleteBillPaymentOutput(
        success=True,
        bill_payment_id=_as_str(deleted.get("Id")) or bill_payment_id,
        status=_as_str(deleted.get("status")),
        deleted=True,
    )


class SearchBillPaymentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    vendor_id: str | None = Field(
        default=None, description="Only payments made to this vendor"
    )
    doc_number: str | None = Field(
        default=None, description="Exact cheque number or payment reference"
    )
    ap_account_id: str | None = Field(
        default=None, description="Only payments against this Accounts Payable account"
    )
    txn_date_from: str | None = Field(
        default=None, description="Earliest payment date, YYYY-MM-DD"
    )
    txn_date_to: str | None = Field(
        default=None, description="Latest payment date, YYYY-MM-DD"
    )
    max_results: int | None = Field(
        default=None,
        description="Maximum number of bill payments to return (QuickBooks caps at 1000)",
    )
    start_position: int | None = Field(
        default=None, description="1-based index of the first result, for paging"
    )


@tool(args_schema=SearchBillPaymentsInput)
@serialize_pydantic_return
async def search_bill_payments(
    auth_type: str,
    auth_data: dict[str, Any],
    vendor_id: str | None = None,
    doc_number: str | None = None,
    ap_account_id: str | None = None,
    txn_date_from: str | None = None,
    txn_date_to: str | None = None,
    max_results: int | None = None,
    start_position: int | None = None,
) -> SearchBillPaymentsOutput:
    """Find payments the company made to vendors, by vendor or date.

    This searches money OUT. For money received from customers, use
    search_payments.
    """
    clauses: list[str] = []
    if vendor_id:
        clauses.append(f"VendorRef = '{_escape_sql(vendor_id)}'")
    if doc_number:
        clauses.append(f"DocNumber = '{_escape_sql(doc_number)}'")
    if ap_account_id:
        clauses.append(f"APAccountRef = '{_escape_sql(ap_account_id)}'")
    if txn_date_from:
        clauses.append(f"TxnDate >= '{_escape_sql(txn_date_from)}'")
    if txn_date_to:
        clauses.append(f"TxnDate <= '{_escape_sql(txn_date_to)}'")
    statement = _b2_build_query("BillPayment", clauses, max_results, start_position)
    payload, error = await _request(
        auth_type, auth_data, "GET", "/query", params={"query": statement}
    )
    if error is not None:
        return SearchBillPaymentsOutput(success=False, error=error)
    rows = _query_rows(payload, "BillPayment")
    position, returned = _b2_query_paging(payload)
    return SearchBillPaymentsOutput(
        success=True,
        bill_payments=[_parse_bill_payment(row) for row in rows],
        count=len(rows),
        start_position=position,
        max_results=returned,
    )


# --- Payments (money in, from a customer) -----------------------------------


_B2_APPLIED_INVOICES_DESCRIPTION = (
    "Invoices this payment settles. Each entry is an object: {'invoice_id': "
    "'42', 'amount': 150.0}. Leave empty to record the receipt as an "
    "unapplied credit on the customer's account."
)


class CreatePaymentInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    customer_id: str = Field(description="ID of the customer the money came from")
    total_amount: float = Field(description="Total amount received")
    applied_invoices: list[dict[str, Any]] | None = Field(
        default=None, description=_B2_APPLIED_INVOICES_DESCRIPTION
    )
    payment_method_id: str | None = Field(
        default=None, description="ID of the payment method (cash, cheque, card)"
    )
    deposit_to_account_id: str | None = Field(
        default=None,
        description="Account to deposit into; Undeposited Funds when omitted",
    )
    txn_date: str | None = Field(
        default=None, description="Receipt date as YYYY-MM-DD; defaults to today"
    )
    payment_ref_num: str | None = Field(
        default=None, description="Cheque number or other reference for the receipt"
    )
    private_note: str | None = Field(default=None, description="Internal memo")
    currency_code: str | None = Field(
        default=None,
        description="Three-letter currency code, required if multicurrency is on",
    )
    exchange_rate: float | None = Field(
        default=None, description="Home-currency units per unit of currency_code"
    )


@tool(args_schema=CreatePaymentInput)
@serialize_pydantic_return
async def create_payment(
    auth_type: str,
    auth_data: dict[str, Any],
    customer_id: str,
    total_amount: float,
    applied_invoices: list[dict[str, Any]] | None = None,
    payment_method_id: str | None = None,
    deposit_to_account_id: str | None = None,
    txn_date: str | None = None,
    payment_ref_num: str | None = None,
    private_note: str | None = None,
    currency_code: str | None = None,
    exchange_rate: float | None = None,
) -> CreatePaymentOutput:
    """Receive a customer payment: record money coming IN against invoices.

    This is the accounts-receivable side. To record money going OUT to a
    vendor against a bill, use create_bill_payment instead.
    """
    body: dict[str, Any] = {
        "CustomerRef": _make_ref(customer_id),
        "TotalAmt": total_amount,
        "Line": _build_linked_txns(applied_invoices or [], "Invoice", "invoice_id")
        or None,
        "PaymentMethodRef": _make_ref(payment_method_id),
        "DepositToAccountRef": _make_ref(deposit_to_account_id),
        "TxnDate": txn_date,
        "PaymentRefNum": payment_ref_num,
        "PrivateNote": private_note,
        "CurrencyRef": _make_ref(currency_code),
        "ExchangeRate": exchange_rate,
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/payment", json_body=body
    )
    if error is not None:
        return CreatePaymentOutput(success=False, error=error)
    return CreatePaymentOutput(
        success=True, payment=_parse_payment(_entity(payload, "Payment"))
    )


class GetPaymentInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    payment_id: str = Field(description="ID of the customer payment to read")


@tool(args_schema=GetPaymentInput)
@serialize_pydantic_return
async def get_payment(
    auth_type: str,
    auth_data: dict[str, Any],
    payment_id: str,
) -> GetPaymentOutput:
    """Read one customer payment, including which invoices it was applied to."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/payment/{_seg(payment_id)}"
    )
    if error is not None:
        return GetPaymentOutput(success=False, error=error)
    return GetPaymentOutput(
        success=True, payment=_parse_payment(_entity(payload, "Payment"))
    )


class UpdatePaymentInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    payment_id: str = Field(description="ID of the customer payment to update")
    customer_id: str | None = Field(default=None, description="New customer ID")
    total_amount: float | None = Field(
        default=None, description="New total amount received"
    )
    applied_invoices: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Replacement set of settled invoices. QuickBooks updates payment "
            "lines all-or-nothing, so send every line the payment should keep. "
            + _B2_APPLIED_INVOICES_DESCRIPTION
        ),
    )
    payment_method_id: str | None = Field(
        default=None, description="New payment method ID"
    )
    deposit_to_account_id: str | None = Field(
        default=None, description="New deposit account ID"
    )
    txn_date: str | None = Field(
        default=None, description="New receipt date as YYYY-MM-DD"
    )
    payment_ref_num: str | None = Field(
        default=None, description="New cheque number or reference"
    )
    private_note: str | None = Field(default=None, description="New internal memo")
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request."
        ),
    )


@tool(args_schema=UpdatePaymentInput)
@serialize_pydantic_return
async def update_payment(
    auth_type: str,
    auth_data: dict[str, Any],
    payment_id: str,
    customer_id: str | None = None,
    total_amount: float | None = None,
    applied_invoices: list[dict[str, Any]] | None = None,
    payment_method_id: str | None = None,
    deposit_to_account_id: str | None = None,
    txn_date: str | None = None,
    payment_ref_num: str | None = None,
    private_note: str | None = None,
    sync_token: str | None = None,
) -> UpdatePaymentOutput:
    """Change a customer payment. Only the fields you supply are altered.

    Applied invoices are the exception: QuickBooks rewrites payment lines
    all-or-nothing, so send the complete set whenever you send any.
    """
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "payment", "Payment", payment_id, sync_token
    )
    if error is not None:
        return UpdatePaymentOutput(success=False, error=error)
    body: dict[str, Any] = {
        "Id": payment_id,
        "SyncToken": token,
        "sparse": True,
        "CustomerRef": _make_ref(customer_id),
        "TotalAmt": total_amount,
        "Line": _build_linked_txns(applied_invoices, "Invoice", "invoice_id")
        if applied_invoices
        else None,
        "PaymentMethodRef": _make_ref(payment_method_id),
        "DepositToAccountRef": _make_ref(deposit_to_account_id),
        "TxnDate": txn_date,
        "PaymentRefNum": payment_ref_num,
        "PrivateNote": private_note,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/payment",
        params={"operation": "update"},
        json_body=body,
    )
    if error is not None:
        return UpdatePaymentOutput(success=False, error=error)
    return UpdatePaymentOutput(
        success=True, payment=_parse_payment(_entity(payload, "Payment"))
    )


class DeletePaymentInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    payment_id: str = Field(description="ID of the customer payment to delete")
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request."
        ),
    )


@tool(args_schema=DeletePaymentInput)
@serialize_pydantic_return
async def delete_payment(
    auth_type: str,
    auth_data: dict[str, Any],
    payment_id: str,
    sync_token: str | None = None,
) -> DeletePaymentOutput:
    """Delete a customer payment, reopening the balance on any invoices it paid."""
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "payment", "Payment", payment_id, sync_token
    )
    if error is not None:
        return DeletePaymentOutput(success=False, error=error, payment_id=payment_id)
    body: dict[str, Any] = {"Id": payment_id, "SyncToken": token}
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/payment",
        params={"operation": "delete"},
        json_body=body,
    )
    if error is not None:
        return DeletePaymentOutput(success=False, error=error, payment_id=payment_id)
    deleted = _entity(payload, "Payment")
    return DeletePaymentOutput(
        success=True,
        payment_id=_as_str(deleted.get("Id")) or payment_id,
        status=_as_str(deleted.get("status")),
        deleted=True,
    )


class SearchPaymentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    customer_id: str | None = Field(
        default=None, description="Only payments received from this customer"
    )
    payment_ref_num: str | None = Field(
        default=None, description="Exact cheque number or payment reference"
    )
    txn_date_from: str | None = Field(
        default=None, description="Earliest receipt date, YYYY-MM-DD"
    )
    txn_date_to: str | None = Field(
        default=None, description="Latest receipt date, YYYY-MM-DD"
    )
    max_results: int | None = Field(
        default=None,
        description="Maximum number of payments to return (QuickBooks caps at 1000)",
    )
    start_position: int | None = Field(
        default=None, description="1-based index of the first result, for paging"
    )


@tool(args_schema=SearchPaymentsInput)
@serialize_pydantic_return
async def search_payments(
    auth_type: str,
    auth_data: dict[str, Any],
    customer_id: str | None = None,
    payment_ref_num: str | None = None,
    txn_date_from: str | None = None,
    txn_date_to: str | None = None,
    max_results: int | None = None,
    start_position: int | None = None,
) -> SearchPaymentsOutput:
    """Find payments received from customers, by customer, reference or date.

    This searches money IN. For payments the company made to vendors, use
    search_bill_payments.
    """
    clauses: list[str] = []
    if customer_id:
        clauses.append(f"CustomerRef = '{_escape_sql(customer_id)}'")
    if payment_ref_num:
        clauses.append(f"PaymentRefNum = '{_escape_sql(payment_ref_num)}'")
    if txn_date_from:
        clauses.append(f"TxnDate >= '{_escape_sql(txn_date_from)}'")
    if txn_date_to:
        clauses.append(f"TxnDate <= '{_escape_sql(txn_date_to)}'")
    statement = _b2_build_query("Payment", clauses, max_results, start_position)
    payload, error = await _request(
        auth_type, auth_data, "GET", "/query", params={"query": statement}
    )
    if error is not None:
        return SearchPaymentsOutput(success=False, error=error)
    rows = _query_rows(payload, "Payment")
    position, returned = _b2_query_paging(payload)
    return SearchPaymentsOutput(
        success=True,
        payments=[_parse_payment(row) for row in rows],
        count=len(rows),
        start_position=position,
        max_results=returned,
    )


# --- Purchases (expenses paid at the time they are incurred) ----------------


class CreatePurchaseInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    account_id: str = Field(
        description=(
            "Account the money came out of. A Check purchase must name a bank "
            "account, a CreditCard purchase a credit card account."
        )
    )
    payment_type: str = Field(
        description="How it was paid: Cash, Check or CreditCard"
    )
    lines: list[dict[str, Any]] = Field(description=_B2_LINES_DESCRIPTION)
    entity_id: str | None = Field(
        default=None, description="ID of who was paid (vendor, customer or employee)"
    )
    entity_type: str | None = Field(
        default=None,
        description="Type of the entity_id record: Vendor, Customer or Employee",
    )
    payment_method_id: str | None = Field(
        default=None, description="ID of the payment method"
    )
    txn_date: str | None = Field(
        default=None, description="Expense date as YYYY-MM-DD; defaults to today"
    )
    doc_number: str | None = Field(
        default=None, description="Cheque number or reference for the expense"
    )
    private_note: str | None = Field(default=None, description="Internal memo")
    department_id: str | None = Field(
        default=None, description="ID of the location or department"
    )
    credit: bool | None = Field(
        default=None,
        description="True to record a credit card refund instead of a charge",
    )
    currency_code: str | None = Field(
        default=None,
        description="Three-letter currency code, required if multicurrency is on",
    )


@tool(args_schema=CreatePurchaseInput)
@serialize_pydantic_return
async def create_purchase(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    payment_type: str,
    lines: list[dict[str, Any]],
    entity_id: str | None = None,
    entity_type: str | None = None,
    payment_method_id: str | None = None,
    txn_date: str | None = None,
    doc_number: str | None = None,
    private_note: str | None = None,
    department_id: str | None = None,
    credit: bool | None = None,
    currency_code: str | None = None,
) -> CreatePurchaseOutput:
    """Record an expense that was already paid, by cash, cheque or credit card.

    Use this when money has already left the account. For an invoice from a
    vendor that is still owed, use create_bill.
    """
    allowed = {"cash": "Cash", "check": "Check", "creditcard": "CreditCard"}
    settled_type = allowed.get(payment_type.strip().lower())
    if settled_type is None:
        return CreatePurchaseOutput(
            success=False,
            error=(
                "payment_type must be 'Cash', 'Check' or 'CreditCard', got "
                f"{payment_type!r}."
            ),
        )
    built_lines = _build_expense_lines(lines)
    if not built_lines:
        return CreatePurchaseOutput(
            success=False, error="A purchase needs at least one expense line."
        )
    entity_ref = _make_ref(entity_id)
    if entity_ref is not None and entity_type:
        entity_ref = {**entity_ref, "type": entity_type}
    body: dict[str, Any] = {
        "AccountRef": _make_ref(account_id),
        "PaymentType": settled_type,
        "Line": built_lines,
        "EntityRef": entity_ref,
        "PaymentMethodRef": _make_ref(payment_method_id),
        "TxnDate": txn_date,
        "DocNumber": doc_number,
        "PrivateNote": private_note,
        "DepartmentRef": _make_ref(department_id),
        "Credit": credit,
        "CurrencyRef": _make_ref(currency_code),
    }
    payload, error = await _request(
        auth_type, auth_data, "POST", "/purchase", json_body=body
    )
    if error is not None:
        return CreatePurchaseOutput(success=False, error=error)
    return CreatePurchaseOutput(
        success=True, purchase=_parse_purchase(_entity(payload, "Purchase"))
    )


class GetPurchaseInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    purchase_id: str = Field(description="ID of the purchase to read")


@tool(args_schema=GetPurchaseInput)
@serialize_pydantic_return
async def get_purchase(
    auth_type: str,
    auth_data: dict[str, Any],
    purchase_id: str,
) -> GetPurchaseOutput:
    """Read one purchase (expense) by ID, including its expense lines."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/purchase/{_seg(purchase_id)}"
    )
    if error is not None:
        return GetPurchaseOutput(success=False, error=error)
    return GetPurchaseOutput(
        success=True, purchase=_parse_purchase(_entity(payload, "Purchase"))
    )


class UpdatePurchaseInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    purchase_id: str = Field(description="ID of the purchase to update")
    account_id: str | None = Field(
        default=None, description="New account the money came out of"
    )
    payment_type: str | None = Field(
        default=None, description="New payment type: Cash, Check or CreditCard"
    )
    lines: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Replacement expense lines. Supplying this replaces every existing "
            "line, so send the full set. " + _B2_LINES_DESCRIPTION
        ),
    )
    entity_id: str | None = Field(default=None, description="New payee ID")
    entity_type: str | None = Field(
        default=None, description="Type of the payee: Vendor, Customer or Employee"
    )
    payment_method_id: str | None = Field(
        default=None, description="New payment method ID"
    )
    txn_date: str | None = Field(
        default=None, description="New expense date as YYYY-MM-DD"
    )
    doc_number: str | None = Field(
        default=None, description="New cheque number or reference"
    )
    private_note: str | None = Field(default=None, description="New internal memo")
    credit: bool | None = Field(
        default=None, description="Whether this is a credit card refund"
    )
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request."
        ),
    )


@tool(args_schema=UpdatePurchaseInput)
@serialize_pydantic_return
async def update_purchase(
    auth_type: str,
    auth_data: dict[str, Any],
    purchase_id: str,
    account_id: str | None = None,
    payment_type: str | None = None,
    lines: list[dict[str, Any]] | None = None,
    entity_id: str | None = None,
    entity_type: str | None = None,
    payment_method_id: str | None = None,
    txn_date: str | None = None,
    doc_number: str | None = None,
    private_note: str | None = None,
    credit: bool | None = None,
    sync_token: str | None = None,
) -> UpdatePurchaseOutput:
    """Change a purchase (expense). Only the fields you supply are altered.

    Lines are the exception: sending any line replaces the whole set, so
    include every line the purchase should end up with.
    """
    settled_type: str | None = None
    if payment_type:
        allowed = {"cash": "Cash", "check": "Check", "creditcard": "CreditCard"}
        settled_type = allowed.get(payment_type.strip().lower())
        if settled_type is None:
            return UpdatePurchaseOutput(
                success=False,
                error=(
                    "payment_type must be 'Cash', 'Check' or 'CreditCard', got "
                    f"{payment_type!r}."
                ),
            )
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "purchase", "Purchase", purchase_id, sync_token
    )
    if error is not None:
        return UpdatePurchaseOutput(success=False, error=error)
    entity_ref = _make_ref(entity_id)
    if entity_ref is not None and entity_type:
        entity_ref = {**entity_ref, "type": entity_type}
    body: dict[str, Any] = {
        "Id": purchase_id,
        "SyncToken": token,
        "sparse": True,
        "AccountRef": _make_ref(account_id),
        "PaymentType": settled_type,
        "Line": _build_expense_lines(lines) if lines else None,
        "EntityRef": entity_ref,
        "PaymentMethodRef": _make_ref(payment_method_id),
        "TxnDate": txn_date,
        "DocNumber": doc_number,
        "PrivateNote": private_note,
        "Credit": credit,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/purchase",
        params={"operation": "update"},
        json_body=body,
    )
    if error is not None:
        return UpdatePurchaseOutput(success=False, error=error)
    return UpdatePurchaseOutput(
        success=True, purchase=_parse_purchase(_entity(payload, "Purchase"))
    )


class DeletePurchaseInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    purchase_id: str = Field(description="ID of the purchase to delete")
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched "
            "automatically when omitted, at the cost of one extra request."
        ),
    )


@tool(args_schema=DeletePurchaseInput)
@serialize_pydantic_return
async def delete_purchase(
    auth_type: str,
    auth_data: dict[str, Any],
    purchase_id: str,
    sync_token: str | None = None,
) -> DeletePurchaseOutput:
    """Delete a purchase (expense), reversing its effect on the account."""
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "purchase", "Purchase", purchase_id, sync_token
    )
    if error is not None:
        return DeletePurchaseOutput(success=False, error=error, purchase_id=purchase_id)
    body: dict[str, Any] = {"Id": purchase_id, "SyncToken": token}
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/purchase",
        params={"operation": "delete"},
        json_body=body,
    )
    if error is not None:
        return DeletePurchaseOutput(success=False, error=error, purchase_id=purchase_id)
    deleted = _entity(payload, "Purchase")
    return DeletePurchaseOutput(
        success=True,
        purchase_id=_as_str(deleted.get("Id")) or purchase_id,
        status=_as_str(deleted.get("status")),
        deleted=True,
    )


class SearchPurchasesInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data carrying the access token and company ID"
    )
    doc_number: str | None = Field(
        default=None, description="Exact cheque number or reference"
    )
    txn_date_from: str | None = Field(
        default=None, description="Earliest expense date, YYYY-MM-DD"
    )
    txn_date_to: str | None = Field(
        default=None, description="Latest expense date, YYYY-MM-DD"
    )
    min_total_amount: float | None = Field(
        default=None, description="Only purchases at or above this total"
    )
    max_total_amount: float | None = Field(
        default=None, description="Only purchases at or below this total"
    )
    max_results: int | None = Field(
        default=None,
        description="Maximum number of purchases to return (QuickBooks caps at 1000)",
    )
    start_position: int | None = Field(
        default=None, description="1-based index of the first result, for paging"
    )


@tool(args_schema=SearchPurchasesInput)
@serialize_pydantic_return
async def search_purchases(
    auth_type: str,
    auth_data: dict[str, Any],
    doc_number: str | None = None,
    txn_date_from: str | None = None,
    txn_date_to: str | None = None,
    min_total_amount: float | None = None,
    max_total_amount: float | None = None,
    max_results: int | None = None,
    start_position: int | None = None,
) -> SearchPurchasesOutput:
    """Find purchases (already-paid expenses) by date, reference or amount."""
    clauses: list[str] = []
    if doc_number:
        clauses.append(f"DocNumber = '{_escape_sql(doc_number)}'")
    if txn_date_from:
        clauses.append(f"TxnDate >= '{_escape_sql(txn_date_from)}'")
    if txn_date_to:
        clauses.append(f"TxnDate <= '{_escape_sql(txn_date_to)}'")
    # The entity reference's attribute table does not tag TotalAmt filterable,
    # but the same page's own sample query filters on it
    # ("select * from Purchase where TotalAmt < '100.00'"), which is where this
    # quoted-literal form comes from.
    # TODO (unverified): TotalAmt filtering is documented only by that sample,
    # not by the attribute table — confirm against a live company.
    if min_total_amount is not None:
        clauses.append(f"TotalAmt >= '{min_total_amount}'")
    if max_total_amount is not None:
        clauses.append(f"TotalAmt <= '{max_total_amount}'")
    statement = _b2_build_query("Purchase", clauses, max_results, start_position)
    payload, error = await _request(
        auth_type, auth_data, "GET", "/query", params={"query": statement}
    )
    if error is not None:
        return SearchPurchasesOutput(success=False, error=error)
    rows = _query_rows(payload, "Purchase")
    position, returned = _b2_query_paging(payload)
    return SearchPurchasesOutput(
        success=True,
        purchases=[_parse_purchase(row) for row in rows],
        count=len(rows),
        start_position=position,
        max_results=returned,
    )


def _parse_item(record: dict[str, Any]) -> ItemRecord:
    """Map one QuickBooks ``Item`` object onto :class:`ItemRecord`."""
    meta = _as_dict(record.get("MetaData"))
    return ItemRecord(
        id=_as_str(record.get("Id")),
        sync_token=_as_str(record.get("SyncToken")),
        name=_as_str(record.get("Name")),
        fully_qualified_name=_as_str(record.get("FullyQualifiedName")),
        sku=_as_str(record.get("Sku")),
        description=_as_str(record.get("Description")),
        purchase_description=_as_str(record.get("PurchaseDesc")),
        item_type=_as_str(record.get("Type")),
        active=_as_bool(record.get("Active")),
        taxable=_as_bool(record.get("Taxable")),
        sales_tax_included=_as_bool(record.get("SalesTaxIncluded")),
        purchase_tax_included=_as_bool(record.get("PurchaseTaxIncluded")),
        unit_price=_as_float(record.get("UnitPrice")),
        purchase_cost=_as_float(record.get("PurchaseCost")),
        track_qty_on_hand=_as_bool(record.get("TrackQtyOnHand")),
        qty_on_hand=_as_float(record.get("QtyOnHand")),
        reorder_point=_as_float(record.get("ReorderPoint")),
        inv_start_date=_as_str(record.get("InvStartDate")),
        sub_item=_as_bool(record.get("SubItem")),
        level=_as_int(record.get("Level")),
        parent_item_id=_ref(record.get("ParentRef")),
        parent_item_name=_ref_name(record.get("ParentRef")),
        income_account_id=_ref(record.get("IncomeAccountRef")),
        income_account_name=_ref_name(record.get("IncomeAccountRef")),
        expense_account_id=_ref(record.get("ExpenseAccountRef")),
        expense_account_name=_ref_name(record.get("ExpenseAccountRef")),
        asset_account_id=_ref(record.get("AssetAccountRef")),
        asset_account_name=_ref_name(record.get("AssetAccountRef")),
        pref_vendor_id=_ref(record.get("PrefVendorRef")),
        pref_vendor_name=_ref_name(record.get("PrefVendorRef")),
        sales_tax_code_id=_ref(record.get("SalesTaxCodeRef")),
        purchase_tax_code_id=_ref(record.get("PurchaseTaxCodeRef")),
        class_id=_ref(record.get("ClassRef")),
        created_at=_as_str(meta.get("CreateTime")),
        updated_at=_as_str(meta.get("LastUpdatedTime")),
    )


def _parse_account(record: dict[str, Any]) -> AccountRecord:
    """Map one QuickBooks ``Account`` object onto :class:`AccountRecord`."""
    meta = _as_dict(record.get("MetaData"))
    return AccountRecord(
        id=_as_str(record.get("Id")),
        sync_token=_as_str(record.get("SyncToken")),
        name=_as_str(record.get("Name")),
        fully_qualified_name=_as_str(record.get("FullyQualifiedName")),
        description=_as_str(record.get("Description")),
        account_type=_as_str(record.get("AccountType")),
        account_sub_type=_as_str(record.get("AccountSubType")),
        classification=_as_str(record.get("Classification")),
        acct_num=_as_str(record.get("AcctNum")),
        active=_as_bool(record.get("Active")),
        sub_account=_as_bool(record.get("SubAccount")),
        parent_account_id=_ref(record.get("ParentRef")),
        parent_account_name=_ref_name(record.get("ParentRef")),
        current_balance=_as_float(record.get("CurrentBalance")),
        current_balance_with_sub_accounts=_as_float(
            record.get("CurrentBalanceWithSubAccounts")
        ),
        currency_code=_ref(record.get("CurrencyRef")),
        currency_name=_ref_name(record.get("CurrencyRef")),
        created_at=_as_str(meta.get("CreateTime")),
        updated_at=_as_str(meta.get("LastUpdatedTime")),
    )


def _parse_company_address(value: Any) -> CompanyInfoAddress | None:
    """Map a QuickBooks ``PhysicalAddress`` stanza, or ``None`` when absent."""
    stanza = _as_dict(value)
    if not stanza:
        return None
    return CompanyInfoAddress(
        line1=_as_str(stanza.get("Line1")),
        line2=_as_str(stanza.get("Line2")),
        city=_as_str(stanza.get("City")),
        country_sub_division_code=_as_str(stanza.get("CountrySubDivisionCode")),
        postal_code=_as_str(stanza.get("PostalCode")),
        country=_as_str(stanza.get("Country")),
    )


def _parse_company_info(record: dict[str, Any]) -> CompanyInfoRecord:
    """Map the QuickBooks ``CompanyInfo`` object onto :class:`CompanyInfoRecord`."""
    meta = _as_dict(record.get("MetaData"))
    return CompanyInfoRecord(
        id=_as_str(record.get("Id")),
        sync_token=_as_str(record.get("SyncToken")),
        company_name=_as_str(record.get("CompanyName")),
        legal_name=_as_str(record.get("LegalName")),
        country=_as_str(record.get("Country")),
        company_start_date=_as_str(record.get("CompanyStartDate")),
        fiscal_year_start_month=_as_str(record.get("FiscalYearStartMonth")),
        employer_id=_as_str(record.get("EmployerId")),
        supported_languages=_as_str(record.get("SupportedLanguages")),
        default_time_zone=_as_str(record.get("DefaultTimeZone")),
        email=_as_str(_as_dict(record.get("Email")).get("Address")),
        web_addr=_as_str(_as_dict(record.get("WebAddr")).get("URI")),
        primary_phone=_as_str(
            _as_dict(record.get("PrimaryPhone")).get("FreeFormNumber")
        ),
        company_addr=_parse_company_address(record.get("CompanyAddr")),
        legal_addr=_parse_company_address(record.get("LegalAddr")),
        customer_communication_addr=_parse_company_address(
            record.get("CustomerCommunicationAddr")
        ),
        name_values=_as_dict_list(record.get("NameValue")),
        created_at=_as_str(meta.get("CreateTime")),
        updated_at=_as_str(meta.get("LastUpdatedTime")),
    )


def _parse_report(payload: Any) -> ReportResult:
    """Map a QuickBooks report payload onto :class:`ReportResult`.

    ``Columns`` and ``Rows`` are wrappers around a single ``Column`` /
    ``Row`` array; both degrade to an empty list when the report came back
    without any (an empty period is a legitimate, successful answer).
    """
    body = _as_dict(payload)
    header = _as_dict(body.get("Header"))
    return ReportResult(
        report_name=_as_str(header.get("ReportName")),
        start_period=_as_str(header.get("StartPeriod")),
        end_period=_as_str(header.get("EndPeriod")),
        currency=_as_str(header.get("Currency")),
        report_time=_as_str(header.get("Time")),
        header=header or None,
        columns=_as_dict_list(_as_dict(body.get("Columns")).get("Column")),
        rows=_as_dict_list(_as_dict(body.get("Rows")).get("Row")),
    )


def _report_id_csv(values: list[str] | None) -> str | None:
    """Render a list of entity IDs as the comma-separated form reports take."""
    if not values:
        return None
    return ",".join(value for value in values if value)


class CreateItemInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="Name of the product or service. Must be unique.")
    item_type: str = Field(
        description=(
            "Classification of the item: `Inventory`, `NonInventory` or `Service`. "
            "`Inventory` additionally requires income_account_id, expense_account_id, "
            "asset_account_id, inv_start_date and qty_on_hand."
        )
    )
    description: str | None = Field(
        default=None, description="Sales description shown on customer-facing documents"
    )
    sku: str | None = Field(
        default=None, description="Stock keeping unit used to track the item in inventory"
    )
    unit_price: float | None = Field(
        default=None,
        description=(
            "Price or rate for the item. For a discount or tax rate express the "
            "percentage as a fraction, e.g. 0.4 for 40%."
        ),
    )
    purchase_cost: float | None = Field(
        default=None, description="Amount paid when buying the item, in the home currency"
    )
    purchase_description: str | None = Field(
        default=None, description="Purchase description shown on bills and purchase orders"
    )
    income_account_id: str | None = Field(
        default=None,
        description=(
            "Id of the account that records the proceeds from selling this item. "
            "Required for `Inventory` and `Service` items."
        ),
    )
    expense_account_id: str | None = Field(
        default=None,
        description=(
            "Id of the expense account used to pay the vendor for this item; must be "
            "a Cost of Goods Sold account. Required for `Inventory` items."
        ),
    )
    asset_account_id: str | None = Field(
        default=None,
        description=(
            "Id of the Other Current Asset account tracking the value of the "
            "inventory. Required for `Inventory` items."
        ),
    )
    track_qty_on_hand: bool | None = Field(
        default=None,
        description=(
            "Track quantity on hand. Applies to `Inventory` items only and cannot be "
            "turned back off once true."
        ),
    )
    qty_on_hand: float | None = Field(
        default=None,
        description="Opening quantity available for sale. Required for `Inventory` items.",
    )
    inv_start_date: str | None = Field(
        default=None,
        description=(
            "Date of the opening inventory balance as YYYY-MM-DD. Required for "
            "`Inventory` items."
        ),
    )
    taxable: bool | None = Field(
        default=None, description="Whether transactions for this item are taxable (US only)"
    )
    sub_item: bool | None = Field(
        default=None, description="Whether this item is nested under another item"
    )
    parent_item_id: str | None = Field(
        default=None,
        description="Id of the parent item. Required when sub_item is true.",
    )
    pref_vendor_id: str | None = Field(
        default=None, description="Id of the preferred vendor to buy this item from"
    )
    reorder_point: float | None = Field(
        default=None,
        description="Quantity at which the inventory item should be restocked",
    )


@tool(args_schema=CreateItemInput)
@serialize_pydantic_return
async def create_item(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    item_type: str,
    description: str | None = None,
    sku: str | None = None,
    unit_price: float | None = None,
    purchase_cost: float | None = None,
    purchase_description: str | None = None,
    income_account_id: str | None = None,
    expense_account_id: str | None = None,
    asset_account_id: str | None = None,
    track_qty_on_hand: bool | None = None,
    qty_on_hand: float | None = None,
    inv_start_date: str | None = None,
    taxable: bool | None = None,
    sub_item: bool | None = None,
    parent_item_id: str | None = None,
    pref_vendor_id: str | None = None,
    reorder_point: float | None = None,
) -> CreateItemOutput:
    """Create a product or service in QuickBooks.

    The required fields depend on the item type. Every item needs a unique
    name and a type; a `Service` or `NonInventory` item needs an income
    account, and an `Inventory` item additionally needs an expense account,
    an asset account, an opening quantity and an inventory start date.
    """
    body: dict[str, Any] = {
        "Name": name,
        "Type": item_type,
        "Description": description,
        "Sku": sku,
        "UnitPrice": unit_price,
        "PurchaseCost": purchase_cost,
        "PurchaseDesc": purchase_description,
        "IncomeAccountRef": {"value": income_account_id} if income_account_id else None,
        "ExpenseAccountRef": {"value": expense_account_id} if expense_account_id else None,
        "AssetAccountRef": {"value": asset_account_id} if asset_account_id else None,
        "TrackQtyOnHand": track_qty_on_hand,
        "QtyOnHand": qty_on_hand,
        "InvStartDate": inv_start_date,
        "Taxable": taxable,
        "SubItem": sub_item,
        "ParentRef": {"value": parent_item_id} if parent_item_id else None,
        "PrefVendorRef": {"value": pref_vendor_id} if pref_vendor_id else None,
        "ReorderPoint": reorder_point,
    }
    payload, error = await _request(auth_type, auth_data, "POST", "/item", json_body=body)
    if error is not None:
        return CreateItemOutput(success=False, error=error)
    return CreateItemOutput(success=True, item=_parse_item(_entity(payload, "Item")))


class GetItemInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    item_id: str = Field(description="Id of the product or service to read")


@tool(args_schema=GetItemInput)
@serialize_pydantic_return
async def get_item(
    auth_type: str,
    auth_data: dict[str, Any],
    item_id: str,
) -> GetItemOutput:
    """Read one product or service by its QuickBooks Id."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/item/{_seg(item_id)}"
    )
    if error is not None:
        return GetItemOutput(success=False, error=error)
    return GetItemOutput(success=True, item=_parse_item(_entity(payload, "Item")))


class UpdateItemInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    item_id: str = Field(description="Id of the product or service to update")
    name: str | None = Field(
        default=None,
        description=(
            "Name of the item. QuickBooks rejects an item update that leaves the name "
            "unset, so supply the item's current name when changing other fields."
        ),
    )
    item_type: str | None = Field(
        default=None,
        description="Classification of the item: `Inventory`, `NonInventory` or `Service`",
    )
    description: str | None = Field(default=None, description="Sales description")
    sku: str | None = Field(default=None, description="Stock keeping unit")
    unit_price: float | None = Field(default=None, description="Price or rate for the item")
    purchase_cost: float | None = Field(
        default=None, description="Amount paid when buying the item"
    )
    purchase_description: str | None = Field(
        default=None, description="Purchase description shown on bills"
    )
    income_account_id: str | None = Field(
        default=None, description="Id of the account recording sales of this item"
    )
    expense_account_id: str | None = Field(
        default=None, description="Id of the Cost of Goods Sold account for this item"
    )
    asset_account_id: str | None = Field(
        default=None, description="Id of the Other Current Asset inventory account"
    )
    track_qty_on_hand: bool | None = Field(
        default=None, description="Track quantity on hand; cannot be turned back off"
    )
    qty_on_hand: float | None = Field(
        default=None, description="Current quantity available for sale"
    )
    inv_start_date: str | None = Field(
        default=None, description="Date of the opening inventory balance as YYYY-MM-DD"
    )
    taxable: bool | None = Field(
        default=None, description="Whether transactions for this item are taxable"
    )
    active: bool | None = Field(
        default=None,
        description="Whether the item is enabled for use; set false to deactivate it",
    )
    sub_item: bool | None = Field(
        default=None, description="Whether this item is nested under another item"
    )
    parent_item_id: str | None = Field(
        default=None, description="Id of the parent item when sub_item is true"
    )
    pref_vendor_id: str | None = Field(
        default=None, description="Id of the preferred vendor for this item"
    )
    reorder_point: float | None = Field(
        default=None, description="Quantity at which the item should be restocked"
    )
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched automatically "
            "when omitted, at the cost of one extra request."
        ),
    )


@tool(args_schema=UpdateItemInput)
@serialize_pydantic_return
async def update_item(
    auth_type: str,
    auth_data: dict[str, Any],
    item_id: str,
    name: str | None = None,
    item_type: str | None = None,
    description: str | None = None,
    sku: str | None = None,
    unit_price: float | None = None,
    purchase_cost: float | None = None,
    purchase_description: str | None = None,
    income_account_id: str | None = None,
    expense_account_id: str | None = None,
    asset_account_id: str | None = None,
    track_qty_on_hand: bool | None = None,
    qty_on_hand: float | None = None,
    inv_start_date: str | None = None,
    taxable: bool | None = None,
    active: bool | None = None,
    sub_item: bool | None = None,
    parent_item_id: str | None = None,
    pref_vendor_id: str | None = None,
    reorder_point: float | None = None,
    sync_token: str | None = None,
) -> UpdateItemOutput:
    """Update a product or service, changing only the fields supplied.

    The update is sparse: omitted fields keep their current values. Pass
    the item's current name alongside the change — QuickBooks treats the
    name as mandatory on an item write.
    """
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "item", "Item", item_id, sync_token
    )
    if error is not None:
        return UpdateItemOutput(success=False, error=error)
    body: dict[str, Any] = {
        "Id": item_id,
        "SyncToken": token,
        "sparse": True,
        "Name": name,
        "Type": item_type,
        "Description": description,
        "Sku": sku,
        "UnitPrice": unit_price,
        "PurchaseCost": purchase_cost,
        "PurchaseDesc": purchase_description,
        "IncomeAccountRef": {"value": income_account_id} if income_account_id else None,
        "ExpenseAccountRef": {"value": expense_account_id} if expense_account_id else None,
        "AssetAccountRef": {"value": asset_account_id} if asset_account_id else None,
        "TrackQtyOnHand": track_qty_on_hand,
        "QtyOnHand": qty_on_hand,
        "InvStartDate": inv_start_date,
        "Taxable": taxable,
        "Active": active,
        "SubItem": sub_item,
        "ParentRef": {"value": parent_item_id} if parent_item_id else None,
        "PrefVendorRef": {"value": pref_vendor_id} if pref_vendor_id else None,
        "ReorderPoint": reorder_point,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/item",
        params={"operation": "update"},
        json_body=body,
    )
    if error is not None:
        return UpdateItemOutput(success=False, error=error)
    return UpdateItemOutput(success=True, item=_parse_item(_entity(payload, "Item")))


class DeleteItemInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    item_id: str = Field(description="Id of the product or service to deactivate")
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched automatically "
            "when omitted, at the cost of one extra request."
        ),
    )


@tool(args_schema=DeleteItemInput)
@serialize_pydantic_return
async def delete_item(
    auth_type: str,
    auth_data: dict[str, Any],
    item_id: str,
    sync_token: str | None = None,
) -> DeleteItemOutput:
    """Remove a product or service from use by deactivating it.

    QuickBooks does not permit deleting an item, because historical
    transactions reference it. The item is marked inactive instead, which
    hides it from lists and pickers while leaving past invoices, bills and
    reports untouched. Reactivate it with `update_item` and `active=true`.
    """
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "item", "Item", item_id, sync_token
    )
    if error is not None:
        return DeleteItemOutput(success=False, error=error)
    body: dict[str, Any] = {
        "Id": item_id,
        "SyncToken": token,
        "sparse": True,
        "Active": False,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/item",
        params={"operation": "update"},
        json_body=body,
    )
    if error is not None:
        return DeleteItemOutput(success=False, error=error)
    return DeleteItemOutput(success=True, item=_parse_item(_entity(payload, "Item")))


class SearchItemsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str | None = Field(default=None, description="Exact item name to match")
    sku: str | None = Field(default=None, description="Exact stock keeping unit to match")
    item_type: str | None = Field(
        default=None,
        description="Item classification to match: `Inventory`, `NonInventory` or `Service`",
    )
    active: bool | None = Field(
        default=None,
        description="Restrict to active (true) or inactive (false) items",
    )
    max_results: int | None = Field(
        default=None, description="Maximum number of items to return (QuickBooks caps at 1000)"
    )
    start_position: int | None = Field(
        default=None, description="1-based index of the first row to return, for paging"
    )


@tool(args_schema=SearchItemsInput)
@serialize_pydantic_return
async def search_items(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str | None = None,
    sku: str | None = None,
    item_type: str | None = None,
    active: bool | None = None,
    max_results: int | None = None,
    start_position: int | None = None,
) -> SearchItemsOutput:
    """Search products and services by name, SKU, type or active state.

    Filters are combined with AND. With no filters this returns the whole
    products-and-services list, one page at a time.
    """
    clauses: list[str] = []
    if name:
        clauses.append(f"Name = '{_escape_sql(name)}'")
    if sku:
        clauses.append(f"Sku = '{_escape_sql(sku)}'")
    if item_type:
        clauses.append(f"Type = '{_escape_sql(item_type)}'")
    if active is not None:
        clauses.append(f"Active = {'true' if active else 'false'}")
    statement = "SELECT * FROM Item"
    if clauses:
        statement += " WHERE " + " AND ".join(clauses)
    if start_position is not None:
        statement += f" STARTPOSITION {start_position}"
    if max_results is not None:
        statement += f" MAXRESULTS {max_results}"
    payload, error = await _request(
        auth_type, auth_data, "GET", "/query", params={"query": statement}
    )
    if error is not None:
        return SearchItemsOutput(success=False, error=error)
    response = _as_dict(_as_dict(payload).get("QueryResponse"))
    items = [_parse_item(row) for row in _query_rows(payload, "Item")]
    return SearchItemsOutput(
        success=True,
        items=items,
        count=len(items),
        start_position=_as_int(response.get("startPosition")),
        max_results=_as_int(response.get("maxResults")),
    )


class CreateAccountInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(
        description=(
            "Name of the account. Must be unique and may not contain a colon or a "
            "double quote."
        )
    )
    account_type: str | None = Field(
        default=None,
        description=(
            "Type of account, e.g. `Bank`, `Expense`, `Income`, `AccountsPayable`, "
            "`AccountsReceivable`, `CreditCard`, `Equity`, `FixedAsset`, "
            "`CostOfGoodsSold`, `OtherCurrentAsset`, `OtherCurrentLiability`, "
            "`LongTermLiability`, `OtherAsset`, `OtherExpense`, `OtherIncome`, "
            "`NonPosting`. QuickBooks derives it from account_sub_type when omitted."
        ),
    )
    account_sub_type: str | None = Field(
        default=None,
        description=(
            "Detailed sub-type, e.g. `Savings`, `CashOnHand`, `SalesOfProductIncome`. "
            "It must be one of the sub-types QuickBooks defines for the chosen "
            "account_type."
        ),
    )
    description: str | None = Field(default=None, description="Description of the account")
    acct_num: str | None = Field(
        default=None,
        description="Account number in the chart of accounts, when numbering is enabled",
    )
    parent_account_id: str | None = Field(
        default=None,
        description=(
            "Id of the parent account to nest this account under. The parent's "
            "account_type must match this account's."
        ),
    )


@tool(args_schema=CreateAccountInput)
@serialize_pydantic_return
async def create_account(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    account_type: str | None = None,
    account_sub_type: str | None = None,
    description: str | None = None,
    acct_num: str | None = None,
    parent_account_id: str | None = None,
) -> CreateAccountOutput:
    """Add an account to the QuickBooks chart of accounts.

    Only the name is strictly required; supplying account_type and
    account_sub_type is strongly recommended, because otherwise QuickBooks
    picks the classification for you.
    """
    body: dict[str, Any] = {
        "Name": name,
        "AccountType": account_type,
        "AccountSubType": account_sub_type,
        "Description": description,
        "AcctNum": acct_num,
    }
    if parent_account_id:
        body["SubAccount"] = True
        body["ParentRef"] = {"value": parent_account_id}
    payload, error = await _request(auth_type, auth_data, "POST", "/account", json_body=body)
    if error is not None:
        return CreateAccountOutput(success=False, error=error)
    return CreateAccountOutput(
        success=True, account=_parse_account(_entity(payload, "Account"))
    )


class GetAccountInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account_id: str = Field(description="Id of the account to read")


@tool(args_schema=GetAccountInput)
@serialize_pydantic_return
async def get_account(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
) -> GetAccountOutput:
    """Read one chart-of-accounts entry by its QuickBooks Id."""
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/account/{_seg(account_id)}"
    )
    if error is not None:
        return GetAccountOutput(success=False, error=error)
    return GetAccountOutput(success=True, account=_parse_account(_entity(payload, "Account")))


class UpdateAccountInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account_id: str = Field(description="Id of the account to update")
    name: str | None = Field(default=None, description="New name for the account")
    account_type: str | None = Field(default=None, description="New account type")
    account_sub_type: str | None = Field(default=None, description="New account sub-type")
    description: str | None = Field(default=None, description="New description")
    acct_num: str | None = Field(default=None, description="New account number")
    active: bool | None = Field(
        default=None,
        description="Set false to deactivate the account, true to reactivate it",
    )
    parent_account_id: str | None = Field(
        default=None, description="Id of the account to nest this account under"
    )
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — the account is read before "
            "every write anyway, so this only overrides the fetched value."
        ),
    )


@tool(args_schema=UpdateAccountInput)
@serialize_pydantic_return
async def update_account(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    name: str | None = None,
    account_type: str | None = None,
    account_sub_type: str | None = None,
    description: str | None = None,
    acct_num: str | None = None,
    active: bool | None = None,
    parent_account_id: str | None = None,
    sync_token: str | None = None,
) -> UpdateAccountOutput:
    """Update a chart-of-accounts entry, or deactivate it with active=false.

    This is also how an account is removed: QuickBooks does not permit
    deleting an account, because the ledger history points at it. Setting
    active=false hides it from the chart of accounts while leaving posted
    transactions intact.
    """
    # Account is the one entity that rejects a sparse write (it answers
    # error 2020, "Required parameter Name is missing"), so the current
    # record is read and the caller's changes are overlaid onto it for a
    # full update. That read also yields the SyncToken.
    current, error = await _request(
        auth_type, auth_data, "GET", f"/account/{_seg(account_id)}"
    )
    if error is not None:
        return UpdateAccountOutput(success=False, error=error)
    record = dict(_entity(current, "Account"))
    record.pop("sparse", None)
    token = sync_token or _as_str(record.get("SyncToken"))
    if token is None:
        return UpdateAccountOutput(
            success=False,
            error=(
                f"QuickBooks did not return a SyncToken for Account {account_id}; "
                "pass sync_token explicitly."
            ),
        )
    changes: dict[str, Any] = {
        "Name": name,
        "AccountType": account_type,
        "AccountSubType": account_sub_type,
        "Description": description,
        "AcctNum": acct_num,
        "Active": active,
    }
    if parent_account_id:
        changes["SubAccount"] = True
        changes["ParentRef"] = {"value": parent_account_id}
    record.update(_clean_body(changes))
    record["Id"] = account_id
    record["SyncToken"] = token
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/account",
        params={"operation": "update"},
        json_body=record,
    )
    if error is not None:
        return UpdateAccountOutput(success=False, error=error)
    return UpdateAccountOutput(
        success=True, account=_parse_account(_entity(payload, "Account"))
    )


class SearchAccountsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str | None = Field(default=None, description="Exact account name to match")
    account_type: str | None = Field(
        default=None, description="Account type to match, e.g. `Bank` or `Expense`"
    )
    account_sub_type: str | None = Field(
        default=None, description="Account sub-type to match, e.g. `Savings`"
    )
    classification: str | None = Field(
        default=None,
        description=(
            "Ledger classification to match: `Asset`, `Equity`, `Expense`, "
            "`Liability` or `Revenue`"
        ),
    )
    active: bool | None = Field(
        default=None, description="Restrict to active (true) or inactive (false) accounts"
    )
    max_results: int | None = Field(
        default=None,
        description="Maximum number of accounts to return (QuickBooks caps at 1000)",
    )
    start_position: int | None = Field(
        default=None, description="1-based index of the first row to return, for paging"
    )


@tool(args_schema=SearchAccountsInput)
@serialize_pydantic_return
async def search_accounts(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str | None = None,
    account_type: str | None = None,
    account_sub_type: str | None = None,
    classification: str | None = None,
    active: bool | None = None,
    max_results: int | None = None,
    start_position: int | None = None,
) -> SearchAccountsOutput:
    """Search the chart of accounts by name, type, classification or state.

    Filters are combined with AND. With no filters this returns the whole
    chart of accounts, one page at a time — the usual way to find the
    account Id another action needs.
    """
    clauses: list[str] = []
    if name:
        clauses.append(f"Name = '{_escape_sql(name)}'")
    if account_type:
        clauses.append(f"AccountType = '{_escape_sql(account_type)}'")
    if account_sub_type:
        clauses.append(f"AccountSubType = '{_escape_sql(account_sub_type)}'")
    if classification:
        clauses.append(f"Classification = '{_escape_sql(classification)}'")
    if active is not None:
        clauses.append(f"Active = {'true' if active else 'false'}")
    statement = "SELECT * FROM Account"
    if clauses:
        statement += " WHERE " + " AND ".join(clauses)
    if start_position is not None:
        statement += f" STARTPOSITION {start_position}"
    if max_results is not None:
        statement += f" MAXRESULTS {max_results}"
    payload, error = await _request(
        auth_type, auth_data, "GET", "/query", params={"query": statement}
    )
    if error is not None:
        return SearchAccountsOutput(success=False, error=error)
    response = _as_dict(_as_dict(payload).get("QueryResponse"))
    accounts = [_parse_account(row) for row in _query_rows(payload, "Account")]
    return SearchAccountsOutput(
        success=True,
        accounts=accounts,
        count=len(accounts),
        start_position=_as_int(response.get("startPosition")),
        max_results=_as_int(response.get("maxResults")),
    )


class GetCompanyInfoInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


@tool(args_schema=GetCompanyInfoInput)
@serialize_pydantic_return
async def get_company_info(
    auth_type: str,
    auth_data: dict[str, Any],
) -> GetCompanyInfoOutput:
    """Read the profile of the connected QuickBooks company.

    Returns the company name, addresses, contact details, country, fiscal
    year start and the company preferences QuickBooks exposes as name/value
    pairs. Which company is read is fixed by the credential.
    """
    # The realm identifies both the company path segment and the
    # CompanyInfo record itself, so it legitimately appears twice in the
    # resolved URL.
    realm = _realm_id(auth_data)
    payload, error = await _request(
        auth_type, auth_data, "GET", f"/companyinfo/{_seg(realm)}"
    )
    if error is not None:
        return GetCompanyInfoOutput(success=False, error=error)
    return GetCompanyInfoOutput(
        success=True, company_info=_parse_company_info(_entity(payload, "CompanyInfo"))
    )


class UpdateCompanyInfoInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    company_name: str | None = Field(
        default=None, description="Trading name of the company"
    )
    legal_name: str | None = Field(
        default=None, description="Registered legal name of the company"
    )
    address_line1: str | None = Field(
        default=None, description="First line of the company address"
    )
    address_city: str | None = Field(default=None, description="City of the company address")
    address_state: str | None = Field(
        default=None,
        description="State, province or region of the company address",
    )
    address_postal_code: str | None = Field(
        default=None, description="Postal or ZIP code of the company address"
    )
    address_country: str | None = Field(
        default=None, description="Country of the company address"
    )
    primary_phone: str | None = Field(
        default=None, description="Main telephone number of the company"
    )
    email: str | None = Field(default=None, description="Contact email address")
    web_addr: str | None = Field(default=None, description="Company website URL")
    sync_token: str | None = Field(
        default=None,
        description=(
            "Current SyncToken of the record. Optional — it is fetched automatically "
            "when omitted, at the cost of one extra request."
        ),
    )


@tool(args_schema=UpdateCompanyInfoInput)
@serialize_pydantic_return
async def update_company_info(
    auth_type: str,
    auth_data: dict[str, Any],
    company_name: str | None = None,
    legal_name: str | None = None,
    address_line1: str | None = None,
    address_city: str | None = None,
    address_state: str | None = None,
    address_postal_code: str | None = None,
    address_country: str | None = None,
    primary_phone: str | None = None,
    email: str | None = None,
    web_addr: str | None = None,
    sync_token: str | None = None,
) -> UpdateCompanyInfoOutput:
    """Update the profile of the connected QuickBooks company.

    The update is sparse: omitted fields keep their current values. Address
    parts are sent together, so supply every part of the company address
    you want to keep whenever you change any of them.
    """
    realm = _realm_id(auth_data)
    token, error = await _resolve_sync_token(
        auth_type, auth_data, "companyinfo", "CompanyInfo", realm, sync_token
    )
    if error is not None:
        return UpdateCompanyInfoOutput(success=False, error=error)
    address = _clean_body(
        {
            "Line1": address_line1,
            "City": address_city,
            "CountrySubDivisionCode": address_state,
            "PostalCode": address_postal_code,
            "Country": address_country,
        }
    )
    body: dict[str, Any] = {
        "Id": realm,
        "SyncToken": token,
        "sparse": True,
        "CompanyName": company_name,
        "LegalName": legal_name,
        "CompanyAddr": address or None,
        "PrimaryPhone": {"FreeFormNumber": primary_phone} if primary_phone else None,
        "Email": {"Address": email} if email else None,
        "WebAddr": {"URI": web_addr} if web_addr else None,
    }
    payload, error = await _request(
        auth_type,
        auth_data,
        "POST",
        "/companyinfo",
        params={"operation": "update"},
        json_body=body,
    )
    if error is not None:
        return UpdateCompanyInfoOutput(success=False, error=error)
    return UpdateCompanyInfoOutput(
        success=True, company_info=_parse_company_info(_entity(payload, "CompanyInfo"))
    )


class RunQueryInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    query: str = Field(
        description=(
            "A QuickBooks query statement, e.g. "
            "`SELECT * FROM Invoice WHERE TotalAmt > '100'`. This is QuickBooks' own "
            "SQL-like language, not SQL: one entity per statement, no JOINs, no "
            "sub-selects, and the only SELECT lists allowed are `*`, `COUNT(*)` and "
            "explicit field names. Filter with WHERE (clauses are AND-ed; OR is not "
            "supported), sort with ORDERBY, and page with STARTPOSITION and "
            "MAXRESULTS, which go after the WHERE clause."
        )
    )


@tool(args_schema=RunQueryInput)
@serialize_pydantic_return
async def run_query(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
) -> RunQueryOutput:
    """Run a raw QuickBooks query statement and return the matching rows.

    The escape hatch for anything the typed search actions do not cover —
    entities they do not expose, fields they do not filter on, or a
    `SELECT COUNT(*)` to size a result set before fetching it. Rows come
    back as raw QuickBooks objects because the entity is only known from
    the statement.
    """
    payload, error = await _request(
        auth_type, auth_data, "GET", "/query", params={"query": query}
    )
    if error is not None:
        return RunQueryOutput(success=False, error=error)
    response = _as_dict(_as_dict(payload).get("QueryResponse"))
    entity_name: str | None = None
    rows: list[dict[str, Any]] = []
    for key, value in response.items():
        # The entity key is the only array in the envelope; the siblings are
        # the paging counters. An empty result omits it altogether.
        if isinstance(value, list):
            entity_name = key
            rows = _as_dict_list(value)
            break
    return RunQueryOutput(
        success=True,
        entity_name=entity_name,
        rows=rows,
        count=len(rows),
        total_count=_as_int(response.get("totalCount")),
        start_position=_as_int(response.get("startPosition")),
        max_results=_as_int(response.get("maxResults")),
    )


class GetBalanceSheetReportInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    start_date: str | None = Field(
        default=None, description="Start of the reporting period as YYYY-MM-DD"
    )
    end_date: str | None = Field(
        default=None,
        description=(
            "End of the reporting period as YYYY-MM-DD; the balance sheet is drawn "
            "as of this date"
        ),
    )
    date_macro: str | None = Field(
        default=None,
        description=(
            "Named date range instead of explicit dates, e.g. `This Month-to-date`, "
            "`Last Fiscal Year`, `This Fiscal Quarter`"
        ),
    )
    accounting_method: str | None = Field(
        default=None, description="`Cash` or `Accrual`; defaults to the company setting"
    )
    summarize_column_by: str | None = Field(
        default=None,
        description=(
            "How to group the columns: `Total`, `Month`, `Week`, `Days`, `Quarter`, "
            "`Year`, `Customers`, `Vendors`, `Classes`, `Departments`, `Employees` "
            "or `ProductsAndServices`"
        ),
    )
    customer_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these customer Ids"
    )
    vendor_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these vendor Ids"
    )
    department_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these department (location) Ids"
    )
    class_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these class Ids"
    )
    item_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these item Ids"
    )
    sort_order: str | None = Field(
        default=None, description="Sort direction for report rows: `ascend` or `descend`"
    )


@tool(args_schema=GetBalanceSheetReportInput)
@serialize_pydantic_return
async def get_balance_sheet_report(
    auth_type: str,
    auth_data: dict[str, Any],
    start_date: str | None = None,
    end_date: str | None = None,
    date_macro: str | None = None,
    accounting_method: str | None = None,
    summarize_column_by: str | None = None,
    customer_ids: list[str] | None = None,
    vendor_ids: list[str] | None = None,
    department_ids: list[str] | None = None,
    class_ids: list[str] | None = None,
    item_ids: list[str] | None = None,
    sort_order: str | None = None,
) -> GetBalanceSheetReportOutput:
    """Run the Balance Sheet report — assets, liabilities and equity.

    Reports come back as a header plus a column definition and a tree of
    rows, where a row may nest further rows for its section. Read the
    figures out of `report.rows`; `report.columns` names what each cell in
    a row's `ColData` array means.
    """
    params: dict[str, Any] = {
        "start_date": start_date,
        "end_date": end_date,
        "date_macro": date_macro,
        "accounting_method": accounting_method,
        "summarize_column_by": summarize_column_by,
        "customer": _report_id_csv(customer_ids),
        "vendor": _report_id_csv(vendor_ids),
        "department": _report_id_csv(department_ids),
        "class": _report_id_csv(class_ids),
        "item": _report_id_csv(item_ids),
        "sort_order": sort_order,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/reports/BalanceSheet", params=params
    )
    if error is not None:
        return GetBalanceSheetReportOutput(success=False, error=error)
    return GetBalanceSheetReportOutput(success=True, report=_parse_report(payload))


class GetProfitAndLossReportInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    start_date: str | None = Field(
        default=None, description="Start of the reporting period as YYYY-MM-DD"
    )
    end_date: str | None = Field(
        default=None, description="End of the reporting period as YYYY-MM-DD"
    )
    date_macro: str | None = Field(
        default=None,
        description=(
            "Named date range instead of explicit dates, e.g. `This Month-to-date` "
            "or `Last Fiscal Year`"
        ),
    )
    accounting_method: str | None = Field(
        default=None, description="`Cash` or `Accrual`; defaults to the company setting"
    )
    summarize_column_by: str | None = Field(
        default=None,
        description=(
            "How to group the columns: `Total`, `Month`, `Week`, `Days`, `Quarter`, "
            "`Year`, `Customers`, `Vendors`, `Classes`, `Departments`, `Employees` "
            "or `ProductsAndServices`"
        ),
    )
    customer_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these customer Ids"
    )
    vendor_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these vendor Ids"
    )
    item_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these item Ids"
    )
    department_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these department (location) Ids"
    )
    class_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these class Ids"
    )
    account_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these account Ids"
    )
    employee_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these employee Ids"
    )
    payment_method: str | None = Field(
        default=None,
        description=(
            "Restrict the report to one payment method, e.g. `Cash`, `Check`, `Visa`, "
            "`MasterCard`, `American Express`, `Discover`"
        ),
    )


@tool(args_schema=GetProfitAndLossReportInput)
@serialize_pydantic_return
async def get_profit_and_loss_report(
    auth_type: str,
    auth_data: dict[str, Any],
    start_date: str | None = None,
    end_date: str | None = None,
    date_macro: str | None = None,
    accounting_method: str | None = None,
    summarize_column_by: str | None = None,
    customer_ids: list[str] | None = None,
    vendor_ids: list[str] | None = None,
    item_ids: list[str] | None = None,
    department_ids: list[str] | None = None,
    class_ids: list[str] | None = None,
    account_ids: list[str] | None = None,
    employee_ids: list[str] | None = None,
    payment_method: str | None = None,
) -> GetProfitAndLossReportOutput:
    """Run the Profit and Loss report — income, expenses and net income.

    The rows form a tree of sections (Income, Cost of Goods Sold, Expenses,
    Net Income); each leaf row's `ColData` lines up with `report.columns`.
    """
    params: dict[str, Any] = {
        "start_date": start_date,
        "end_date": end_date,
        "date_macro": date_macro,
        "accounting_method": accounting_method,
        "summarize_column_by": summarize_column_by,
        "customer": _report_id_csv(customer_ids),
        "vendor": _report_id_csv(vendor_ids),
        "item": _report_id_csv(item_ids),
        "department": _report_id_csv(department_ids),
        "class": _report_id_csv(class_ids),
        "account": _report_id_csv(account_ids),
        "employee": _report_id_csv(employee_ids),
        "payment_method": payment_method,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/reports/ProfitAndLoss", params=params
    )
    if error is not None:
        return GetProfitAndLossReportOutput(success=False, error=error)
    return GetProfitAndLossReportOutput(success=True, report=_parse_report(payload))


class GetTrialBalanceReportInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    start_date: str | None = Field(
        default=None, description="Start of the reporting period as YYYY-MM-DD"
    )
    end_date: str | None = Field(
        default=None, description="End of the reporting period as YYYY-MM-DD"
    )
    accounting_method: str | None = Field(
        default=None, description="`Cash` or `Accrual`; defaults to the company setting"
    )


@tool(args_schema=GetTrialBalanceReportInput)
@serialize_pydantic_return
async def get_trial_balance_report(
    auth_type: str,
    auth_data: dict[str, Any],
    start_date: str | None = None,
    end_date: str | None = None,
    accounting_method: str | None = None,
) -> GetTrialBalanceReportOutput:
    """Run the Trial Balance report — debit and credit totals per account.

    Use it to confirm the ledger balances before closing a period: the
    debit and credit columns of the total row must agree.
    """
    params: dict[str, Any] = {
        "start_date": start_date,
        "end_date": end_date,
        "accounting_method": accounting_method,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/reports/TrialBalance", params=params
    )
    if error is not None:
        return GetTrialBalanceReportOutput(success=False, error=error)
    return GetTrialBalanceReportOutput(success=True, report=_parse_report(payload))


class GetCashFlowReportInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    start_date: str | None = Field(
        default=None, description="Start of the reporting period as YYYY-MM-DD"
    )
    end_date: str | None = Field(
        default=None, description="End of the reporting period as YYYY-MM-DD"
    )
    date_macro: str | None = Field(
        default=None,
        description=(
            "Named date range instead of explicit dates, e.g. `This Month-to-date` "
            "or `Last Fiscal Year`"
        ),
    )
    summarize_column_by: str | None = Field(
        default=None,
        description=(
            "How to group the columns: `Total`, `Month`, `Week`, `Days`, `Quarter`, "
            "`Year`, `Customers`, `Vendors`, `Classes`, `Departments`, `Employees` "
            "or `ProductsAndServices`"
        ),
    )
    customer_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these customer Ids"
    )
    vendor_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these vendor Ids"
    )
    department_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these department (location) Ids"
    )
    class_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these class Ids"
    )
    item_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these item Ids"
    )
    sort_order: str | None = Field(
        default=None, description="Sort direction for report rows: `ascend` or `descend`"
    )


@tool(args_schema=GetCashFlowReportInput)
@serialize_pydantic_return
async def get_cash_flow_report(
    auth_type: str,
    auth_data: dict[str, Any],
    start_date: str | None = None,
    end_date: str | None = None,
    date_macro: str | None = None,
    summarize_column_by: str | None = None,
    customer_ids: list[str] | None = None,
    vendor_ids: list[str] | None = None,
    department_ids: list[str] | None = None,
    class_ids: list[str] | None = None,
    item_ids: list[str] | None = None,
    sort_order: str | None = None,
) -> GetCashFlowReportOutput:
    """Run the Statement of Cash Flows report.

    Shows cash movement split into operating, investing and financing
    activities over the requested period.
    """
    params: dict[str, Any] = {
        "start_date": start_date,
        "end_date": end_date,
        "date_macro": date_macro,
        "summarize_column_by": summarize_column_by,
        "customer": _report_id_csv(customer_ids),
        "vendor": _report_id_csv(vendor_ids),
        "department": _report_id_csv(department_ids),
        "class": _report_id_csv(class_ids),
        "item": _report_id_csv(item_ids),
        "sort_order": sort_order,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/reports/CashFlow", params=params
    )
    if error is not None:
        return GetCashFlowReportOutput(success=False, error=error)
    return GetCashFlowReportOutput(success=True, report=_parse_report(payload))


class GetCustomerBalanceReportInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    report_date: str | None = Field(
        default=None,
        description="Date the balances are drawn as of, as YYYY-MM-DD; defaults to today",
    )
    customer_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these customer Ids"
    )
    summarize_column_by: str | None = Field(
        default=None,
        description="How to group the columns: `Total`, `Month`, `Week` or `Days`",
    )


@tool(args_schema=GetCustomerBalanceReportInput)
@serialize_pydantic_return
async def get_customer_balance_report(
    auth_type: str,
    auth_data: dict[str, Any],
    report_date: str | None = None,
    customer_ids: list[str] | None = None,
    summarize_column_by: str | None = None,
) -> GetCustomerBalanceReportOutput:
    """Run the Customer Balance report — how much each customer still owes.

    The accounts-receivable view: one row per customer with their
    outstanding balance as of the report date.
    """
    params: dict[str, Any] = {
        "report_date": report_date,
        "customer": _report_id_csv(customer_ids),
        "summarize_column_by": summarize_column_by,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/reports/CustomerBalance", params=params
    )
    if error is not None:
        return GetCustomerBalanceReportOutput(success=False, error=error)
    return GetCustomerBalanceReportOutput(success=True, report=_parse_report(payload))


class GetVendorBalanceReportInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    report_date: str | None = Field(
        default=None,
        description="Date the balances are drawn as of, as YYYY-MM-DD; defaults to today",
    )
    vendor_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these vendor Ids"
    )
    summarize_column_by: str | None = Field(
        default=None,
        description="How to group the columns: `Total`, `Month`, `Week` or `Days`",
    )


@tool(args_schema=GetVendorBalanceReportInput)
@serialize_pydantic_return
async def get_vendor_balance_report(
    auth_type: str,
    auth_data: dict[str, Any],
    report_date: str | None = None,
    vendor_ids: list[str] | None = None,
    summarize_column_by: str | None = None,
) -> GetVendorBalanceReportOutput:
    """Run the Vendor Balance report — how much is still owed to each vendor.

    The accounts-payable counterpart of the customer balance report: one
    row per vendor with the outstanding balance as of the report date.
    """
    params: dict[str, Any] = {
        "report_date": report_date,
        "vendor": _report_id_csv(vendor_ids),
        "summarize_column_by": summarize_column_by,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/reports/VendorBalance", params=params
    )
    if error is not None:
        return GetVendorBalanceReportOutput(success=False, error=error)
    return GetVendorBalanceReportOutput(success=True, report=_parse_report(payload))


class GetVendorExpensesReportInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    start_date: str | None = Field(
        default=None, description="Start of the reporting period as YYYY-MM-DD"
    )
    end_date: str | None = Field(
        default=None, description="End of the reporting period as YYYY-MM-DD"
    )
    accounting_method: str | None = Field(
        default=None, description="`Cash` or `Accrual`; defaults to the company setting"
    )
    vendor_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these vendor Ids"
    )
    summarize_column_by: str | None = Field(
        default=None,
        description="How to group the columns: `Total`, `Month`, `Week` or `Days`",
    )


@tool(args_schema=GetVendorExpensesReportInput)
@serialize_pydantic_return
async def get_vendor_expenses_report(
    auth_type: str,
    auth_data: dict[str, Any],
    start_date: str | None = None,
    end_date: str | None = None,
    accounting_method: str | None = None,
    vendor_ids: list[str] | None = None,
    summarize_column_by: str | None = None,
) -> GetVendorExpensesReportOutput:
    """Run the Expenses by Vendor report — total spend per vendor.

    Answers "who did we spend the most with over this period", which the
    vendor balance report cannot: this totals what was spent, not what is
    still outstanding.
    """
    params: dict[str, Any] = {
        "start_date": start_date,
        "end_date": end_date,
        "accounting_method": accounting_method,
        "vendor": _report_id_csv(vendor_ids),
        "summarize_column_by": summarize_column_by,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/reports/VendorExpenses", params=params
    )
    if error is not None:
        return GetVendorExpensesReportOutput(success=False, error=error)
    return GetVendorExpensesReportOutput(success=True, report=_parse_report(payload))


class GetApAgingReportInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    report_date: str | None = Field(
        default=None,
        description="Date the ageing is calculated from, as YYYY-MM-DD; defaults to today",
    )
    accounting_method: str | None = Field(
        default=None, description="`Cash` or `Accrual`; defaults to the company setting"
    )
    vendor_ids: list[str] | None = Field(
        default=None, description="Restrict the report to these vendor Ids"
    )
    num_periods: int | None = Field(
        default=None, description="Number of ageing buckets to show"
    )
    aging_period: int | None = Field(
        default=None, description="Length of each ageing bucket in days"
    )
    past_due: int | None = Field(
        default=None, description="Only include bills at least this many days past due"
    )


@tool(args_schema=GetApAgingReportInput)
@serialize_pydantic_return
async def get_ap_aging_report(
    auth_type: str,
    auth_data: dict[str, Any],
    report_date: str | None = None,
    accounting_method: str | None = None,
    vendor_ids: list[str] | None = None,
    num_periods: int | None = None,
    aging_period: int | None = None,
    past_due: int | None = None,
) -> GetApAgingReportOutput:
    """Run the A/P Ageing Summary report — unpaid bills bucketed by age.

    One row per vendor, with the outstanding amount split across ageing
    buckets (current, 1-30 days, 31-60 days, …) so overdue payables stand
    out.
    """
    # TODO (unverified): the ageing criteria below are confirmed against the
    # AgedPayableDetail report; the summary AgedPayables report is
    # documented alongside it but its exact parameter list was not
    # independently confirmed. Parameters that are detail-report specific
    # (columns, shipvia, term) are deliberately omitted rather than guessed.
    params: dict[str, Any] = {
        "report_date": report_date,
        "accounting_method": accounting_method,
        "vendor": _report_id_csv(vendor_ids),
        "num_periods": num_periods,
        "aging_period": aging_period,
        "past_due": past_due,
    }
    payload, error = await _request(
        auth_type, auth_data, "GET", "/reports/AgedPayables", params=params
    )
    if error is not None:
        return GetApAgingReportOutput(success=False, error=error)
    return GetApAgingReportOutput(success=True, report=_parse_report(payload))

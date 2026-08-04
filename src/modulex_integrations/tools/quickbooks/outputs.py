"""Pydantic response models for the QuickBooks Online integration.

One ``<Action>Output`` per action, each carrying ``success`` and ``error``
alongside its payload. Payload fields are deliberately permissive
(``<type> | None``) — the Accounting API omits fields freely and its
numeric types are not pinned, so the tool functions coerce every value
before it lands here.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SalesLineItem(BaseModel):
    """One line of a sales transaction.

    QuickBooks nests the interesting values two levels deep, inside
    ``Line[].SalesItemLineDetail``. They are lifted to the top here so a
    caller never has to walk the nesting to learn what was sold.
    """

    model_config = ConfigDict(extra="forbid")

    line_id: str | None = None
    line_number: int | None = None
    description: str | None = None
    amount: float | None = None
    detail_type: str | None = None
    item_id: str | None = None
    item_name: str | None = None
    quantity: float | None = None
    unit_price: float | None = None
    tax_code_id: str | None = None
    service_date: str | None = None


class InvoiceRecord(BaseModel):
    """A QuickBooks ``Invoice``.

    ``sync_token`` is the optimistic-concurrency version of the record: pass
    it back to ``update_invoice`` / ``delete_invoice`` / ``void_invoice`` to
    save those actions a lookup round trip.
    """

    model_config = ConfigDict(extra="forbid")

    invoice_id: str | None = None
    sync_token: str | None = None
    doc_number: str | None = None
    txn_date: str | None = None
    due_date: str | None = None
    ship_date: str | None = None
    customer_id: str | None = None
    customer_name: str | None = None
    customer_memo: str | None = None
    private_note: str | None = None
    bill_email: str | None = None
    bill_address: dict[str, Any] | None = None
    ship_address: dict[str, Any] | None = None
    currency: str | None = None
    exchange_rate: float | None = None
    total_amount: float | None = None
    balance: float | None = None
    home_balance: float | None = None
    deposit: float | None = None
    total_tax: float | None = None
    txn_status: str | None = None
    email_status: str | None = None
    print_status: str | None = None
    global_tax_calculation: str | None = None
    apply_tax_after_discount: bool | None = None
    allow_online_credit_card_payment: bool | None = None
    allow_online_ach_payment: bool | None = None
    invoice_link: str | None = None
    tracking_number: str | None = None
    sales_term_id: str | None = None
    lines: list[SalesLineItem] = Field(default_factory=list)
    linked_transactions: list[dict[str, Any]] = Field(default_factory=list)
    created_time: str | None = None
    last_updated_time: str | None = None


class CustomerRecord(BaseModel):
    """A QuickBooks ``Customer`` (a customer, a job, or a sub-customer)."""

    model_config = ConfigDict(extra="forbid")

    customer_id: str | None = None
    sync_token: str | None = None
    display_name: str | None = None
    fully_qualified_name: str | None = None
    company_name: str | None = None
    print_on_check_name: str | None = None
    title: str | None = None
    given_name: str | None = None
    middle_name: str | None = None
    family_name: str | None = None
    suffix: str | None = None
    active: bool | None = None
    taxable: bool | None = None
    job: bool | None = None
    bill_with_parent: bool | None = None
    parent_id: str | None = None
    level: int | None = None
    primary_email: str | None = None
    primary_phone: str | None = None
    alternate_phone: str | None = None
    mobile: str | None = None
    fax: str | None = None
    website: str | None = None
    bill_address: dict[str, Any] | None = None
    ship_address: dict[str, Any] | None = None
    notes: str | None = None
    balance: float | None = None
    balance_with_jobs: float | None = None
    open_balance_date: str | None = None
    currency: str | None = None
    preferred_delivery_method: str | None = None
    resale_number: str | None = None
    account_number: str | None = None
    default_tax_code_id: str | None = None
    sales_term_id: str | None = None
    payment_method_id: str | None = None
    customer_type_id: str | None = None
    created_time: str | None = None
    last_updated_time: str | None = None


class EstimateRecord(BaseModel):
    """A QuickBooks ``Estimate`` — a quote that may become an invoice."""

    model_config = ConfigDict(extra="forbid")

    estimate_id: str | None = None
    sync_token: str | None = None
    doc_number: str | None = None
    txn_date: str | None = None
    expiration_date: str | None = None
    accepted_by: str | None = None
    accepted_date: str | None = None
    txn_status: str | None = None
    customer_id: str | None = None
    customer_name: str | None = None
    customer_memo: str | None = None
    private_note: str | None = None
    bill_email: str | None = None
    bill_address: dict[str, Any] | None = None
    ship_address: dict[str, Any] | None = None
    currency: str | None = None
    exchange_rate: float | None = None
    total_amount: float | None = None
    total_tax: float | None = None
    email_status: str | None = None
    print_status: str | None = None
    global_tax_calculation: str | None = None
    apply_tax_after_discount: bool | None = None
    lines: list[SalesLineItem] = Field(default_factory=list)
    linked_transactions: list[dict[str, Any]] = Field(default_factory=list)
    created_time: str | None = None
    last_updated_time: str | None = None


class SalesReceiptRecord(BaseModel):
    """A QuickBooks ``SalesReceipt`` — a sale that was paid immediately."""

    model_config = ConfigDict(extra="forbid")

    sales_receipt_id: str | None = None
    sync_token: str | None = None
    doc_number: str | None = None
    txn_date: str | None = None
    customer_id: str | None = None
    customer_name: str | None = None
    customer_memo: str | None = None
    private_note: str | None = None
    bill_email: str | None = None
    bill_address: dict[str, Any] | None = None
    ship_address: dict[str, Any] | None = None
    currency: str | None = None
    exchange_rate: float | None = None
    total_amount: float | None = None
    balance: float | None = None
    total_tax: float | None = None
    payment_method_id: str | None = None
    payment_reference_number: str | None = None
    deposit_to_account_id: str | None = None
    email_status: str | None = None
    print_status: str | None = None
    global_tax_calculation: str | None = None
    apply_tax_after_discount: bool | None = None
    lines: list[SalesLineItem] = Field(default_factory=list)
    created_time: str | None = None
    last_updated_time: str | None = None


class CreditMemoRecord(BaseModel):
    """A QuickBooks ``CreditMemo`` — credit issued back to a customer."""

    model_config = ConfigDict(extra="forbid")

    credit_memo_id: str | None = None
    sync_token: str | None = None
    doc_number: str | None = None
    txn_date: str | None = None
    customer_id: str | None = None
    customer_name: str | None = None
    customer_memo: str | None = None
    private_note: str | None = None
    bill_email: str | None = None
    bill_address: dict[str, Any] | None = None
    ship_address: dict[str, Any] | None = None
    currency: str | None = None
    exchange_rate: float | None = None
    total_amount: float | None = None
    balance: float | None = None
    remaining_credit: float | None = None
    total_tax: float | None = None
    email_status: str | None = None
    print_status: str | None = None
    global_tax_calculation: str | None = None
    apply_tax_after_discount: bool | None = None
    lines: list[SalesLineItem] = Field(default_factory=list)
    created_time: str | None = None
    last_updated_time: str | None = None


# --- Invoices ---------------------------------------------------------------


class CreateInvoiceOutput(BaseModel):
    """Result of ``create_invoice``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    invoice: InvoiceRecord | None = None


class GetInvoiceOutput(BaseModel):
    """Result of ``get_invoice``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    invoice: InvoiceRecord | None = None


class UpdateInvoiceOutput(BaseModel):
    """Result of ``update_invoice``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    invoice: InvoiceRecord | None = None


class DeleteInvoiceOutput(BaseModel):
    """Result of ``delete_invoice``.

    A delete answers with a stub carrying the ID and ``status: "Deleted"``
    rather than the full record, so only those two values are surfaced.
    """

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    invoice_id: str | None = None
    status: str | None = None


class SearchInvoicesOutput(BaseModel):
    """Result of ``search_invoices``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    invoices: list[InvoiceRecord] = Field(default_factory=list)
    count: int = 0
    query: str | None = None


# --- Customers --------------------------------------------------------------


class CreateCustomerOutput(BaseModel):
    """Result of ``create_customer``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    customer: CustomerRecord | None = None


class GetCustomerOutput(BaseModel):
    """Result of ``get_customer``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    customer: CustomerRecord | None = None


class UpdateCustomerOutput(BaseModel):
    """Result of ``update_customer``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    customer: CustomerRecord | None = None


class DeleteCustomerOutput(BaseModel):
    """Result of ``delete_customer``.

    QuickBooks has no delete for customers, so the action deactivates the
    record and the (still existing, now inactive) customer comes back.
    ``deactivated`` is true whenever the write succeeded.
    """

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    customer: CustomerRecord | None = None
    deactivated: bool = False


class SearchCustomersOutput(BaseModel):
    """Result of ``search_customers``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    customers: list[CustomerRecord] = Field(default_factory=list)
    count: int = 0
    query: str | None = None


# --- Estimates --------------------------------------------------------------


class CreateEstimateOutput(BaseModel):
    """Result of ``create_estimate``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    estimate: EstimateRecord | None = None


class GetEstimateOutput(BaseModel):
    """Result of ``get_estimate``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    estimate: EstimateRecord | None = None


class UpdateEstimateOutput(BaseModel):
    """Result of ``update_estimate``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    estimate: EstimateRecord | None = None


class DeleteEstimateOutput(BaseModel):
    """Result of ``delete_estimate``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    estimate_id: str | None = None
    status: str | None = None


class SearchEstimatesOutput(BaseModel):
    """Result of ``search_estimates``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    estimates: list[EstimateRecord] = Field(default_factory=list)
    count: int = 0
    query: str | None = None


# --- Sales receipts ---------------------------------------------------------


class CreateSalesReceiptOutput(BaseModel):
    """Result of ``create_sales_receipt``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    sales_receipt: SalesReceiptRecord | None = None


class GetSalesReceiptOutput(BaseModel):
    """Result of ``get_sales_receipt``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    sales_receipt: SalesReceiptRecord | None = None


class UpdateSalesReceiptOutput(BaseModel):
    """Result of ``update_sales_receipt``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    sales_receipt: SalesReceiptRecord | None = None


class DeleteSalesReceiptOutput(BaseModel):
    """Result of ``delete_sales_receipt``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    sales_receipt_id: str | None = None
    status: str | None = None


class SearchSalesReceiptsOutput(BaseModel):
    """Result of ``search_sales_receipts``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    sales_receipts: list[SalesReceiptRecord] = Field(default_factory=list)
    count: int = 0
    query: str | None = None


# --- Credit memos -----------------------------------------------------------


class CreateCreditMemoOutput(BaseModel):
    """Result of ``create_credit_memo``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    credit_memo: CreditMemoRecord | None = None


class GetCreditMemoOutput(BaseModel):
    """Result of ``get_credit_memo``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    credit_memo: CreditMemoRecord | None = None


class UpdateCreditMemoOutput(BaseModel):
    """Result of ``update_credit_memo``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    credit_memo: CreditMemoRecord | None = None


class DeleteCreditMemoOutput(BaseModel):
    """Result of ``delete_credit_memo``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    credit_memo_id: str | None = None
    status: str | None = None


class SearchCreditMemosOutput(BaseModel):
    """Result of ``search_credit_memos``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    credit_memos: list[CreditMemoRecord] = Field(default_factory=list)
    count: int = 0
    query: str | None = None


# --- Delivery ---------------------------------------------------------------


class SendInvoiceOutput(BaseModel):
    """Result of ``send_invoice``.

    ``email_status`` reads ``EmailSent`` once QuickBooks has handed the mail
    off; it is also present on the returned invoice.
    """

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    invoice: InvoiceRecord | None = None
    email_status: str | None = None


class SendEstimateOutput(BaseModel):
    """Result of ``send_estimate``."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    estimate: EstimateRecord | None = None
    email_status: str | None = None


class VoidInvoiceOutput(BaseModel):
    """Result of ``void_invoice``.

    The invoice survives the call: the returned record keeps its number and
    date but carries a zero total and a ``Voided`` private note.
    """

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    invoice: InvoiceRecord | None = None


class LinkedTxnRef(BaseModel):
    """A pointer from one transaction to another.

    QuickBooks records "this payment pays that bill" as a link rather than a
    foreign key, so the linked document is identified by ID *and* type.
    """

    model_config = ConfigDict(extra="forbid")

    txn_id: str | None = None
    txn_type: str | None = Field(
        default=None,
        description="Type of the linked document, e.g. Bill, Invoice, PurchaseOrder.",
    )
    txn_line_id: str | None = None


class LinkedTxnLine(BaseModel):
    """One line of a payment: an amount applied to linked documents.

    Both ``Payment`` (money in) and ``BillPayment`` (money out) use this
    shape; the ``txn_type`` inside distinguishes what is being paid.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    amount: float | None = None
    linked_transactions: list[LinkedTxnRef] = Field(default_factory=list)


class ExpenseLineItem(BaseModel):
    """One expense-side line of a bill or a purchase.

    Expense lines carry an *account* (a category such as "Advertising") in
    ``AccountBasedExpenseLineDetail``, or an *item* when the expense is a
    purchased product. This is a different shape from the sales-side line
    used by invoices and estimates.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    description: str | None = None
    amount: float | None = None
    detail_type: str | None = None
    account_id: str | None = None
    account_name: str | None = None
    item_id: str | None = None
    item_name: str | None = None
    quantity: float | None = None
    unit_price: float | None = None
    billable_status: str | None = None
    customer_id: str | None = None
    customer_name: str | None = None
    class_id: str | None = None
    tax_code_id: str | None = None


class VendorAddress(BaseModel):
    """A postal address on a vendor record."""

    model_config = ConfigDict(extra="forbid")

    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = Field(
        default=None,
        description="State, province or region (CountrySubDivisionCode).",
    )
    postal_code: str | None = None
    country: str | None = None


class VendorRecord(BaseModel):
    """A supplier the company buys from and owes money to."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    sync_token: str | None = None
    display_name: str | None = None
    company_name: str | None = None
    title: str | None = None
    given_name: str | None = None
    middle_name: str | None = None
    family_name: str | None = None
    suffix: str | None = None
    print_on_check_name: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    fax: str | None = None
    website: str | None = None
    account_number: str | None = None
    tax_identifier: str | None = Field(
        default=None,
        description="Tax ID, masked by QuickBooks to the last four characters.",
    )
    term_id: str | None = None
    term_name: str | None = None
    vendor_1099: bool | None = None
    bill_rate: float | None = None
    cost_rate: float | None = None
    balance: float | None = Field(
        default=None, description="Open (unpaid) balance owed to this vendor."
    )
    currency: str | None = None
    active: bool | None = None
    bill_address: VendorAddress | None = None
    created_at: str | None = None
    updated_at: str | None = None


class BillRecord(BaseModel):
    """A bill: a vendor's request for payment, owed but not yet paid."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    sync_token: str | None = None
    doc_number: str | None = None
    txn_date: str | None = None
    due_date: str | None = None
    vendor_id: str | None = None
    vendor_name: str | None = None
    ap_account_id: str | None = None
    ap_account_name: str | None = None
    sales_term_id: str | None = None
    department_id: str | None = None
    currency: str | None = None
    exchange_rate: float | None = None
    private_note: str | None = None
    global_tax_calculation: str | None = None
    total_amount: float | None = None
    balance: float | None = Field(
        default=None,
        description="Amount still unpaid on this bill; 0 means fully paid.",
    )
    home_balance: float | None = None
    lines: list[ExpenseLineItem] = Field(default_factory=list)
    linked_transactions: list[LinkedTxnRef] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class BillPaymentRecord(BaseModel):
    """A payment the company made to a vendor against one or more bills."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    sync_token: str | None = None
    doc_number: str | None = None
    txn_date: str | None = None
    vendor_id: str | None = None
    vendor_name: str | None = None
    ap_account_id: str | None = None
    ap_account_name: str | None = None
    pay_type: str | None = Field(
        default=None, description="Check or CreditCard."
    )
    total_amount: float | None = None
    private_note: str | None = None
    currency: str | None = None
    exchange_rate: float | None = None
    department_id: str | None = None
    bank_account_id: str | None = Field(
        default=None, description="Bank account drawn on when pay_type is Check."
    )
    bank_account_name: str | None = None
    check_print_status: str | None = None
    credit_card_account_id: str | None = Field(
        default=None,
        description="Credit card account charged when pay_type is CreditCard.",
    )
    credit_card_account_name: str | None = None
    process_bill_payment: bool | None = None
    lines: list[LinkedTxnLine] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class PaymentRecord(BaseModel):
    """A payment the company received from a customer."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    sync_token: str | None = None
    txn_date: str | None = None
    customer_id: str | None = None
    customer_name: str | None = None
    total_amount: float | None = None
    unapplied_amount: float | None = Field(
        default=None,
        description="Part of the payment not yet applied to any invoice.",
    )
    payment_method_id: str | None = None
    payment_method_name: str | None = None
    deposit_to_account_id: str | None = None
    deposit_to_account_name: str | None = None
    payment_ref_num: str | None = Field(
        default=None, description="Cheque number or other reference for the receipt."
    )
    private_note: str | None = None
    currency: str | None = None
    exchange_rate: float | None = None
    project_id: str | None = None
    lines: list[LinkedTxnLine] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class PurchaseRecord(BaseModel):
    """An expense paid at the time it was incurred (cash, cheque or card)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    sync_token: str | None = None
    doc_number: str | None = None
    txn_date: str | None = None
    payment_type: str | None = Field(
        default=None, description="Cash, Check or CreditCard."
    )
    account_id: str | None = Field(
        default=None, description="Account the money came out of."
    )
    account_name: str | None = None
    entity_id: str | None = Field(
        default=None, description="Who the expense was paid to, when recorded."
    )
    entity_name: str | None = None
    entity_type: str | None = Field(
        default=None, description="Vendor, Customer or Employee."
    )
    payment_method_id: str | None = None
    payment_method_name: str | None = None
    department_id: str | None = None
    currency: str | None = None
    exchange_rate: float | None = None
    private_note: str | None = None
    print_status: str | None = None
    global_tax_calculation: str | None = None
    credit: bool | None = Field(
        default=None,
        description="True when this is a credit card refund rather than a charge.",
    )
    total_amount: float | None = None
    lines: list[ExpenseLineItem] = Field(default_factory=list)
    linked_transactions: list[LinkedTxnRef] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


# --- Vendors ----------------------------------------------------------------


class CreateVendorOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    vendor: VendorRecord | None = None


class GetVendorOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    vendor: VendorRecord | None = None


class UpdateVendorOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    vendor: VendorRecord | None = None


class DeleteVendorOutput(BaseModel):
    """Result of retiring a vendor.

    QuickBooks has no delete for vendors, so ``deactivated`` rather than
    ``deleted`` reports what actually happened to the record.
    """

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    vendor_id: str | None = None
    deactivated: bool = False
    vendor: VendorRecord | None = None


class SearchVendorsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    vendors: list[VendorRecord] = Field(default_factory=list)
    count: int = 0
    start_position: int | None = None
    max_results: int | None = None


# --- Bills ------------------------------------------------------------------


class CreateBillOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    bill: BillRecord | None = None


class GetBillOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    bill: BillRecord | None = None


class UpdateBillOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    bill: BillRecord | None = None


class DeleteBillOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    bill_id: str | None = None
    status: str | None = None
    deleted: bool = False


class SearchBillsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    bills: list[BillRecord] = Field(default_factory=list)
    count: int = 0
    start_position: int | None = None
    max_results: int | None = None


# --- Bill payments (money out, to a vendor) ---------------------------------


class CreateBillPaymentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    bill_payment: BillPaymentRecord | None = None


class GetBillPaymentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    bill_payment: BillPaymentRecord | None = None


class UpdateBillPaymentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    bill_payment: BillPaymentRecord | None = None


class DeleteBillPaymentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    bill_payment_id: str | None = None
    status: str | None = None
    deleted: bool = False


class SearchBillPaymentsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    bill_payments: list[BillPaymentRecord] = Field(default_factory=list)
    count: int = 0
    start_position: int | None = None
    max_results: int | None = None


# --- Payments (money in, from a customer) -----------------------------------


class CreatePaymentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    payment: PaymentRecord | None = None


class GetPaymentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    payment: PaymentRecord | None = None


class UpdatePaymentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    payment: PaymentRecord | None = None


class DeletePaymentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    payment_id: str | None = None
    status: str | None = None
    deleted: bool = False


class SearchPaymentsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    payments: list[PaymentRecord] = Field(default_factory=list)
    count: int = 0
    start_position: int | None = None
    max_results: int | None = None


# --- Purchases (expenses) ---------------------------------------------------


class CreatePurchaseOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    purchase: PurchaseRecord | None = None


class GetPurchaseOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    purchase: PurchaseRecord | None = None


class UpdatePurchaseOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    purchase: PurchaseRecord | None = None


class DeletePurchaseOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    purchase_id: str | None = None
    status: str | None = None
    deleted: bool = False


class SearchPurchasesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    purchases: list[PurchaseRecord] = Field(default_factory=list)
    count: int = 0
    start_position: int | None = None
    max_results: int | None = None


class ItemRecord(BaseModel):
    """One product or service from the QuickBooks ``Item`` name list.

    Field names are snake_case renderings of the upstream PascalCase keys;
    the mapping happens in ``_parse_item`` in ``tools.py``. ``*Ref`` stanzas
    are flattened into an ``_id`` / ``_name`` pair because callers almost
    always want the ID and the LLM almost always wants the label.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    sync_token: str | None = None
    name: str | None = None
    fully_qualified_name: str | None = None
    sku: str | None = None
    description: str | None = None
    purchase_description: str | None = None
    item_type: str | None = None
    active: bool | None = None
    taxable: bool | None = None
    sales_tax_included: bool | None = None
    purchase_tax_included: bool | None = None
    unit_price: float | None = None
    purchase_cost: float | None = None
    track_qty_on_hand: bool | None = None
    qty_on_hand: float | None = None
    reorder_point: float | None = None
    inv_start_date: str | None = None
    sub_item: bool | None = None
    level: int | None = None
    parent_item_id: str | None = None
    parent_item_name: str | None = None
    income_account_id: str | None = None
    income_account_name: str | None = None
    expense_account_id: str | None = None
    expense_account_name: str | None = None
    asset_account_id: str | None = None
    asset_account_name: str | None = None
    pref_vendor_id: str | None = None
    pref_vendor_name: str | None = None
    sales_tax_code_id: str | None = None
    purchase_tax_code_id: str | None = None
    class_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CreateItemOutput(BaseModel):
    """Result of creating a product or service."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    item: ItemRecord | None = None


class GetItemOutput(BaseModel):
    """Result of reading one product or service by ID."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    item: ItemRecord | None = None


class UpdateItemOutput(BaseModel):
    """Result of updating a product or service."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    item: ItemRecord | None = None


class DeleteItemOutput(BaseModel):
    """Result of deactivating a product or service.

    QuickBooks has no hard delete for items, so ``item`` carries the
    record as it stands after being marked inactive.
    """

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    item: ItemRecord | None = None


class SearchItemsOutput(BaseModel):
    """A page of products and services matching the supplied filters."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    items: list[ItemRecord] = Field(default_factory=list)
    count: int = 0
    start_position: int | None = None
    max_results: int | None = None


class AccountRecord(BaseModel):
    """One ledger account from the QuickBooks chart of accounts."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    sync_token: str | None = None
    name: str | None = None
    fully_qualified_name: str | None = None
    description: str | None = None
    account_type: str | None = None
    account_sub_type: str | None = None
    classification: str | None = None
    acct_num: str | None = None
    active: bool | None = None
    sub_account: bool | None = None
    parent_account_id: str | None = None
    parent_account_name: str | None = None
    current_balance: float | None = None
    current_balance_with_sub_accounts: float | None = None
    currency_code: str | None = None
    currency_name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CreateAccountOutput(BaseModel):
    """Result of creating a ledger account."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    account: AccountRecord | None = None


class GetAccountOutput(BaseModel):
    """Result of reading one ledger account by ID."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    account: AccountRecord | None = None


class UpdateAccountOutput(BaseModel):
    """Result of updating (or deactivating) a ledger account."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    account: AccountRecord | None = None


class SearchAccountsOutput(BaseModel):
    """A page of ledger accounts matching the supplied filters."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    accounts: list[AccountRecord] = Field(default_factory=list)
    count: int = 0
    start_position: int | None = None
    max_results: int | None = None


class CompanyInfoAddress(BaseModel):
    """A QuickBooks ``PhysicalAddress`` stanza on the company profile."""

    model_config = ConfigDict(extra="forbid")

    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    country_sub_division_code: str | None = None
    postal_code: str | None = None
    country: str | None = None


class CompanyInfoRecord(BaseModel):
    """The company profile of the connected QuickBooks realm.

    ``name_values`` is left as raw objects: QuickBooks uses it as an
    open-ended bag of company preferences (``IndustryType``,
    ``SubscriptionStatus``, ``NeoEnabled``, …) whose keys are not a fixed
    set, so typing it would only lose information.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    sync_token: str | None = None
    company_name: str | None = None
    legal_name: str | None = None
    country: str | None = None
    company_start_date: str | None = None
    fiscal_year_start_month: str | None = None
    employer_id: str | None = None
    supported_languages: str | None = None
    default_time_zone: str | None = None
    email: str | None = None
    web_addr: str | None = None
    primary_phone: str | None = None
    company_addr: CompanyInfoAddress | None = None
    legal_addr: CompanyInfoAddress | None = None
    customer_communication_addr: CompanyInfoAddress | None = None
    name_values: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class GetCompanyInfoOutput(BaseModel):
    """Result of reading the connected company's profile."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    company_info: CompanyInfoRecord | None = None


class UpdateCompanyInfoOutput(BaseModel):
    """Result of updating the connected company's profile."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    company_info: CompanyInfoRecord | None = None


class RunQueryOutput(BaseModel):
    """Rows returned by a raw QuickBooks query statement.

    The entity is not known ahead of time, so rows stay as raw objects and
    ``entity_name`` reports which QuickBooks entity they came from.
    ``total_count`` is populated only by ``SELECT COUNT(*)`` statements.
    """

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    entity_name: str | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    total_count: int | None = None
    start_position: int | None = None
    max_results: int | None = None


class ReportResult(BaseModel):
    """A QuickBooks financial report.

    Reports are not entity lists: the payload is a ``Header`` / ``Columns``
    / ``Rows`` tree where a row may itself contain nested ``Rows``, and the
    nesting differs per report and per requested grouping. Rows and columns
    are therefore kept as raw objects — a typed row model would silently
    drop the sections that carry the actual subtotals. The header values
    that every report shares are lifted out for convenience.
    """

    model_config = ConfigDict(extra="forbid")

    report_name: str | None = None
    start_period: str | None = None
    end_period: str | None = None
    currency: str | None = None
    report_time: str | None = None
    header: dict[str, Any] | None = None
    columns: list[dict[str, Any]] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)


class GetBalanceSheetReportOutput(BaseModel):
    """Result of running the Balance Sheet report."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    report: ReportResult | None = None


class GetProfitAndLossReportOutput(BaseModel):
    """Result of running the Profit and Loss report."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    report: ReportResult | None = None


class GetTrialBalanceReportOutput(BaseModel):
    """Result of running the Trial Balance report."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    report: ReportResult | None = None


class GetCashFlowReportOutput(BaseModel):
    """Result of running the Statement of Cash Flows report."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    report: ReportResult | None = None


class GetCustomerBalanceReportOutput(BaseModel):
    """Result of running the Customer Balance report."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    report: ReportResult | None = None


class GetVendorBalanceReportOutput(BaseModel):
    """Result of running the Vendor Balance report."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    report: ReportResult | None = None


class GetVendorExpensesReportOutput(BaseModel):
    """Result of running the Expenses by Vendor Summary report."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    report: ReportResult | None = None


class GetApAgingReportOutput(BaseModel):
    """Result of running the A/P Ageing Summary report."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    error: str | None = None
    report: ReportResult | None = None

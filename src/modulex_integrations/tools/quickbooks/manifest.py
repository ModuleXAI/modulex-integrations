"""QuickBooks Online integration manifest.

Declares the accounting actions this integration exposes against the
QuickBooks Online Accounting API v3, plus the OAuth 2.0 credential schema
the modulex runtime uses to drive the connect flow, credential validation,
and tool discovery.

Two credential facts shape this manifest. QuickBooks issues a token per
**company** and every endpoint is scoped to that company, so the realm
(company) ID is declared as an ``inject_into_auth_data`` environment
variable and read from ``auth_data`` rather than asked for on every action.
And the sandbox and production APIs live on different hosts, so the
environment is a credential-level setting resolved through a closed map —
never a value an action can influence.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="quickbooks",
    display_name="QuickBooks Online",
    description=(
        "Run a QuickBooks Online company from an agent: raise and send "
        "invoices and estimates, record sales receipts and credit memos, "
        "manage customers, vendors, items and the chart of accounts, enter "
        "bills, purchases and payments on both sides of the ledger, run the "
        "balance sheet, P&L, trial balance, cash flow and ageing reports, "
        "and query any entity directly."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:quickbooks",
    app_url="https://quickbooks.intuit.com",
    categories=["Finance & Payments", "Accounting", "Bookkeeping"],
    actions=[
    ActionDefinition(
        name="create_invoice",
        description=(
            "Create an invoice billing a customer for one or more items. Records "
            "money the customer now owes; use create_sales_receipt instead when "
            "the sale was already paid for."
        ),
        parameters={
            "customer_id": ParameterDef(
                type="string",
                description="ID of the customer being billed",
                required=True,
            ),
            "line_items": ParameterDef(
                type="array",
                description=(
                    "What is being billed. Each object accepts item_ref (the "
                    "QuickBooks Item ID), qty, unit_price, description, "
                    "tax_code_ref (a TaxCode ID, or TAX/NON in the US) and "
                    "service_date (YYYY-MM-DD). The line total defaults to "
                    "qty * unit_price; pass amount to override it"
                ),
                required=True,
            ),
            "txn_date": ParameterDef(
                type="string",
                description="Invoice date as YYYY-MM-DD. Defaults to today",
            ),
            "due_date": ParameterDef(
                type="string",
                description=(
                    "Date the payment is due as YYYY-MM-DD. Defaults to the sales term"
                ),
            ),
            "doc_number": ParameterDef(
                type="string",
                description=(
                    "Reference number for the transaction. Auto-assigned when omitted"
                ),
            ),
            "bill_email": ParameterDef(
                type="string",
                description=(
                    "Email address the invoice is addressed to. Defaults to the "
                    "customer's"
                ),
            ),
            "customer_memo": ParameterDef(
                type="string",
                description="Message shown to the customer on the invoice",
            ),
            "private_note": ParameterDef(
                type="string",
                description="Internal note. Never shown to the customer",
            ),
            "currency_code": ParameterDef(
                type="string",
                description=(
                    "ISO 4217 code such as USD or EUR. Required if multicurrency "
                    "is enabled"
                ),
            ),
            "sales_term_id": ParameterDef(
                type="string",
                description=(
                    "ID of the SalesTerm (payment terms). Falls back to the "
                    "customer's default"
                ),
            ),
            "bill_address": ParameterDef(
                type="object",
                description=(
                    "Billing address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "ship_address": ParameterDef(
                type="object",
                description=(
                    "Shipping address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "global_tax_calculation": ParameterDef(
                type="string",
                description=(
                    "How tax applies to the lines: TaxExcluded, TaxInclusive or "
                    "NotApplicable. Non-US companies only"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="get_invoice",
        description=(
            "Read one invoice by its ID, including its line items and balance."
        ),
        parameters={
            "invoice_id": ParameterDef(
                type="string",
                description="ID of the invoice to read",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_invoice",
        description=(
            "Change fields on an existing invoice, leaving the rest untouched. "
            "This is a sparse update: only the values supplied here change. To "
            "email the invoice use send_invoice; to cancel it use void_invoice."
        ),
        parameters={
            "invoice_id": ParameterDef(
                type="string",
                description="ID of the invoice to update",
                required=True,
            ),
            "customer_id": ParameterDef(
                type="string",
                description="ID of the customer the invoice is billed to",
            ),
            "line_items": ParameterDef(
                type="array",
                description=(
                    "Replacement line items. Supplying this REPLACES every "
                    "existing line, so include the lines you want to keep. Each "
                    "object accepts item_ref, qty, unit_price, description, "
                    "tax_code_ref and service_date"
                ),
            ),
            "txn_date": ParameterDef(
                type="string", description="Invoice date as YYYY-MM-DD"
            ),
            "due_date": ParameterDef(
                type="string", description="Payment due date as YYYY-MM-DD"
            ),
            "doc_number": ParameterDef(
                type="string", description="Reference number for the transaction"
            ),
            "bill_email": ParameterDef(
                type="string", description="Email address the invoice is addressed to"
            ),
            "customer_memo": ParameterDef(
                type="string",
                description="Message shown to the customer on the invoice",
            ),
            "private_note": ParameterDef(type="string", description="Internal note"),
            "currency_code": ParameterDef(
                type="string", description="ISO 4217 code such as USD or EUR"
            ),
            "sales_term_id": ParameterDef(
                type="string", description="ID of the SalesTerm (payment terms)"
            ),
            "bill_address": ParameterDef(
                type="object",
                description=(
                    "Billing address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "ship_address": ParameterDef(
                type="object",
                description=(
                    "Shipping address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "global_tax_calculation": ParameterDef(
                type="string",
                description=(
                    "TaxExcluded, TaxInclusive or NotApplicable. Non-US companies only"
                ),
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional — it is fetched "
                    "automatically when omitted, at the cost of one extra request"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="delete_invoice",
        description=(
            "Delete an invoice permanently. The transaction disappears from the "
            "books entirely; when the invoice must stay on record for the audit "
            "trail — the usual accounting choice — use void_invoice instead."
        ),
        parameters={
            "invoice_id": ParameterDef(
                type="string",
                description="ID of the invoice to delete",
                required=True,
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional — it is fetched "
                    "automatically when omitted, at the cost of one extra request"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="search_invoices",
        description=(
            "Find invoices by customer, number, date range or unpaid status. All "
            "supplied filters are combined with AND; with none at all this lists "
            "the company's invoices."
        ),
        parameters={
            "customer_id": ParameterDef(
                type="string", description="Only invoices billed to this customer ID"
            ),
            "doc_number": ParameterDef(
                type="string",
                description="Only the invoice carrying this reference number",
            ),
            "txn_date_from": ParameterDef(
                type="string",
                description="Only invoices dated on or after this date (YYYY-MM-DD)",
            ),
            "txn_date_to": ParameterDef(
                type="string",
                description="Only invoices dated on or before this date (YYYY-MM-DD)",
            ),
            "due_date_from": ParameterDef(
                type="string",
                description="Only invoices due on or after this date (YYYY-MM-DD)",
            ),
            "due_date_to": ParameterDef(
                type="string",
                description="Only invoices due on or before this date (YYYY-MM-DD)",
            ),
            "unpaid_only": ParameterDef(
                type="boolean",
                description=(
                    "When true, return only invoices with an outstanding balance"
                ),
                default=False,
            ),
            "max_results": ParameterDef(
                type="integer", description="Maximum number of invoices to return"
            ),
            "start_position": ParameterDef(
                type="integer",
                description="1-based index of the first result, for paging",
            ),
        },
    ),
    ActionDefinition(
        name="create_customer",
        description=(
            "Add a customer to the company. Supply either a display name or at "
            "least one name part — QuickBooks builds the display name from the "
            "parts when it is omitted, and rejects a display name already taken "
            "by a customer, vendor or employee."
        ),
        parameters={
            "display_name": ParameterDef(
                type="string",
                description=(
                    "Name as displayed. Must be unique across all customers, "
                    "vendors and employees. Either this or one of the name parts "
                    "is required"
                ),
            ),
            "title": ParameterDef(
                type="string", description="Title of the person, such as Ms"
            ),
            "given_name": ParameterDef(
                type="string", description="First name of the person"
            ),
            "middle_name": ParameterDef(
                type="string", description="Middle name of the person"
            ),
            "family_name": ParameterDef(
                type="string", description="Last name of the person"
            ),
            "suffix": ParameterDef(
                type="string", description="Suffix of the name, such as Jr"
            ),
            "company_name": ParameterDef(
                type="string",
                description="Name of the company the customer belongs to",
            ),
            "print_on_check_name": ParameterDef(
                type="string",
                description=(
                    "Name as printed on a check. Defaults to the display name"
                ),
            ),
            "primary_email": ParameterDef(
                type="string", description="Primary email address"
            ),
            "primary_phone": ParameterDef(
                type="string", description="Primary phone number"
            ),
            "mobile": ParameterDef(type="string", description="Mobile phone number"),
            "website": ParameterDef(type="string", description="Website URL"),
            "bill_address": ParameterDef(
                type="object",
                description=(
                    "Billing address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "ship_address": ParameterDef(
                type="object",
                description=(
                    "Shipping address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "notes": ParameterDef(
                type="string", description="Free-form note about the customer"
            ),
            "taxable": ParameterDef(
                type="boolean",
                description="Whether sales to this customer are taxable",
            ),
            "currency_code": ParameterDef(
                type="string",
                description=(
                    "ISO 4217 code such as USD. Multicurrency companies only"
                ),
            ),
            "sales_term_id": ParameterDef(
                type="string",
                description=(
                    "ID of the SalesTerm used as this customer's default terms"
                ),
            ),
            "payment_method_id": ParameterDef(
                type="string",
                description=(
                    "ID of the PaymentMethod usually used by this customer"
                ),
            ),
            "account_number": ParameterDef(
                type="string", description="Your account number for this customer"
            ),
            "resale_number": ParameterDef(
                type="string",
                description="Resale number, for tax-exempt resellers",
            ),
            "preferred_delivery_method": ParameterDef(
                type="string",
                description=(
                    "How documents reach the customer: Print, Email or None"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="get_customer",
        description=(
            "Read one customer by ID, including contact details and balance."
        ),
        parameters={
            "customer_id": ParameterDef(
                type="string",
                description="ID of the customer to read",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_customer",
        description=(
            "Change fields on an existing customer, leaving the rest untouched. "
            "This is a sparse update: only the values supplied here change."
        ),
        parameters={
            "customer_id": ParameterDef(
                type="string",
                description="ID of the customer to update",
                required=True,
            ),
            "display_name": ParameterDef(
                type="string",
                description=(
                    "Name as displayed. Must stay unique across the company"
                ),
            ),
            "title": ParameterDef(
                type="string", description="Title of the person, such as Ms"
            ),
            "given_name": ParameterDef(
                type="string", description="First name of the person"
            ),
            "middle_name": ParameterDef(
                type="string", description="Middle name of the person"
            ),
            "family_name": ParameterDef(
                type="string", description="Last name of the person"
            ),
            "suffix": ParameterDef(
                type="string", description="Suffix of the name, such as Jr"
            ),
            "company_name": ParameterDef(
                type="string", description="Name of the company"
            ),
            "print_on_check_name": ParameterDef(
                type="string", description="Name as printed on a check"
            ),
            "primary_email": ParameterDef(
                type="string", description="Primary email address"
            ),
            "primary_phone": ParameterDef(
                type="string", description="Primary phone number"
            ),
            "mobile": ParameterDef(type="string", description="Mobile phone number"),
            "website": ParameterDef(type="string", description="Website URL"),
            "bill_address": ParameterDef(
                type="object",
                description=(
                    "Billing address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "ship_address": ParameterDef(
                type="object",
                description=(
                    "Shipping address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "notes": ParameterDef(
                type="string", description="Free-form note about the customer"
            ),
            "active": ParameterDef(
                type="boolean",
                description=(
                    "Set false to deactivate the customer, true to reactivate one"
                ),
            ),
            "taxable": ParameterDef(
                type="boolean",
                description="Whether sales to this customer are taxable",
            ),
            "currency_code": ParameterDef(
                type="string", description="ISO 4217 code such as USD"
            ),
            "sales_term_id": ParameterDef(
                type="string",
                description=(
                    "ID of the SalesTerm used as this customer's default terms"
                ),
            ),
            "payment_method_id": ParameterDef(
                type="string",
                description=(
                    "ID of the PaymentMethod usually used by this customer"
                ),
            ),
            "account_number": ParameterDef(
                type="string", description="Your account number for this customer"
            ),
            "resale_number": ParameterDef(type="string", description="Resale number"),
            "preferred_delivery_method": ParameterDef(
                type="string",
                description=(
                    "How documents reach the customer: Print, Email or None"
                ),
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional — it is fetched "
                    "automatically when omitted, at the cost of one extra request"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="delete_customer",
        description=(
            "Deactivate a customer. QuickBooks does not permit deleting "
            "customers, so this marks the record inactive; its history is "
            "preserved and update_customer with active=true reverses it. This "
            "is also what deleting a customer does in the QuickBooks UI."
        ),
        parameters={
            "customer_id": ParameterDef(
                type="string",
                description="ID of the customer to deactivate",
                required=True,
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional — it is fetched "
                    "automatically when omitted, at the cost of one extra request"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="search_customers",
        description=(
            "Find customers by name, company or active state. All supplied "
            "filters are combined with AND; with none at all this lists the "
            "company's customers — a good way to resolve a name to the ID the "
            "invoice actions need."
        ),
        parameters={
            "display_name": ParameterDef(
                type="string",
                description="Only the customer whose display name matches exactly",
            ),
            "name_contains": ParameterDef(
                type="string",
                description="Only customers whose display name contains this text",
            ),
            "company_name": ParameterDef(
                type="string",
                description="Only customers with this exact company name",
            ),
            "given_name": ParameterDef(
                type="string", description="Only customers with this exact first name"
            ),
            "family_name": ParameterDef(
                type="string", description="Only customers with this exact last name"
            ),
            "active": ParameterDef(
                type="boolean",
                description=(
                    "True for active customers only, false for deactivated ones"
                ),
            ),
            "max_results": ParameterDef(
                type="integer", description="Maximum number of customers to return"
            ),
            "start_position": ParameterDef(
                type="integer",
                description="1-based index of the first result, for paging",
            ),
        },
    ),
    ActionDefinition(
        name="create_estimate",
        description=(
            "Create an estimate — a quote or proposal for a customer. An "
            "estimate is non-posting: it does not affect the books until it is "
            "converted into an invoice."
        ),
        parameters={
            "customer_id": ParameterDef(
                type="string",
                description="ID of the customer being quoted",
                required=True,
            ),
            "line_items": ParameterDef(
                type="array",
                description=(
                    "What is being quoted. Each object accepts item_ref (the "
                    "QuickBooks Item ID), qty, unit_price, description, "
                    "tax_code_ref and service_date (YYYY-MM-DD). The line total "
                    "defaults to qty * unit_price; pass amount to override it"
                ),
                required=True,
            ),
            "txn_date": ParameterDef(
                type="string", description="Estimate date as YYYY-MM-DD"
            ),
            "expiration_date": ParameterDef(
                type="string",
                description="Date the estimate stops being valid (YYYY-MM-DD)",
            ),
            "doc_number": ParameterDef(
                type="string", description="Reference number for the transaction"
            ),
            "bill_email": ParameterDef(
                type="string",
                description="Email address the estimate is addressed to",
            ),
            "customer_memo": ParameterDef(
                type="string",
                description="Message shown to the customer on the estimate",
            ),
            "private_note": ParameterDef(type="string", description="Internal note"),
            "accepted_by": ParameterDef(
                type="string",
                description="Name of the person who accepted the estimate",
            ),
            "accepted_date": ParameterDef(
                type="string",
                description="Date the estimate was accepted (YYYY-MM-DD)",
            ),
            "txn_status": ParameterDef(
                type="string",
                description=(
                    "Estimate status: Pending, Accepted, Closed or Rejected"
                ),
            ),
            "currency_code": ParameterDef(
                type="string", description="ISO 4217 code such as USD"
            ),
            "bill_address": ParameterDef(
                type="object",
                description=(
                    "Billing address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "ship_address": ParameterDef(
                type="object",
                description=(
                    "Shipping address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "global_tax_calculation": ParameterDef(
                type="string",
                description=(
                    "TaxExcluded, TaxInclusive or NotApplicable. Non-US companies only"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="get_estimate",
        description=(
            "Read one estimate by its ID, including its line items and status."
        ),
        parameters={
            "estimate_id": ParameterDef(
                type="string",
                description="ID of the estimate to read",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_estimate",
        description=(
            "Change fields on an existing estimate, leaving the rest untouched. "
            "This is a sparse update: only the values supplied here change. "
            "Marking a quote as won is txn_status=Accepted."
        ),
        parameters={
            "estimate_id": ParameterDef(
                type="string",
                description="ID of the estimate to update",
                required=True,
            ),
            "customer_id": ParameterDef(
                type="string",
                description="ID of the customer the estimate is addressed to",
            ),
            "line_items": ParameterDef(
                type="array",
                description=(
                    "Replacement line items. Supplying this REPLACES every "
                    "existing line, so include the lines you want to keep. Each "
                    "object accepts item_ref, qty, unit_price, description, "
                    "tax_code_ref and service_date"
                ),
            ),
            "txn_date": ParameterDef(
                type="string", description="Estimate date as YYYY-MM-DD"
            ),
            "expiration_date": ParameterDef(
                type="string",
                description="Date the estimate stops being valid (YYYY-MM-DD)",
            ),
            "doc_number": ParameterDef(
                type="string", description="Reference number for the transaction"
            ),
            "bill_email": ParameterDef(
                type="string",
                description="Email address the estimate is addressed to",
            ),
            "customer_memo": ParameterDef(
                type="string",
                description="Message shown to the customer on the estimate",
            ),
            "private_note": ParameterDef(type="string", description="Internal note"),
            "accepted_by": ParameterDef(
                type="string",
                description="Name of the person who accepted the estimate",
            ),
            "accepted_date": ParameterDef(
                type="string",
                description="Date the estimate was accepted (YYYY-MM-DD)",
            ),
            "txn_status": ParameterDef(
                type="string",
                description=(
                    "Estimate status: Pending, Accepted, Closed or Rejected"
                ),
            ),
            "currency_code": ParameterDef(
                type="string", description="ISO 4217 code such as USD"
            ),
            "bill_address": ParameterDef(
                type="object",
                description=(
                    "Billing address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "ship_address": ParameterDef(
                type="object",
                description=(
                    "Shipping address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "global_tax_calculation": ParameterDef(
                type="string",
                description=(
                    "TaxExcluded, TaxInclusive or NotApplicable. Non-US companies only"
                ),
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional — it is fetched "
                    "automatically when omitted, at the cost of one extra request"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="delete_estimate",
        description=(
            "Delete an estimate permanently. To keep the quote on record but "
            "take it out of play, set its status to Closed or Rejected with "
            "update_estimate instead."
        ),
        parameters={
            "estimate_id": ParameterDef(
                type="string",
                description="ID of the estimate to delete",
                required=True,
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional — it is fetched "
                    "automatically when omitted, at the cost of one extra request"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="search_estimates",
        description=(
            "Find estimates by customer, number, status or date range. All "
            "supplied filters are combined with AND; with none at all this lists "
            "the company's estimates."
        ),
        parameters={
            "customer_id": ParameterDef(
                type="string",
                description="Only estimates addressed to this customer ID",
            ),
            "doc_number": ParameterDef(
                type="string",
                description="Only the estimate carrying this reference number",
            ),
            "txn_status": ParameterDef(
                type="string",
                description=(
                    "Only estimates in this status: Pending, Accepted, Closed or "
                    "Rejected"
                ),
            ),
            "txn_date_from": ParameterDef(
                type="string",
                description="Only estimates dated on or after this date (YYYY-MM-DD)",
            ),
            "txn_date_to": ParameterDef(
                type="string",
                description="Only estimates dated on or before this date (YYYY-MM-DD)",
            ),
            "max_results": ParameterDef(
                type="integer", description="Maximum number of estimates to return"
            ),
            "start_position": ParameterDef(
                type="integer",
                description="1-based index of the first result, for paging",
            ),
        },
    ),
    ActionDefinition(
        name="create_sales_receipt",
        description=(
            "Record a sale that was paid for at the same time. Use this for "
            "point-of-sale style transactions; when the customer will pay later, "
            "create an invoice instead."
        ),
        parameters={
            "line_items": ParameterDef(
                type="array",
                description=(
                    "What was sold. Each object accepts item_ref (the QuickBooks "
                    "Item ID), qty, unit_price, description, tax_code_ref and "
                    "service_date (YYYY-MM-DD). The line total defaults to "
                    "qty * unit_price; pass amount to override it"
                ),
                required=True,
            ),
            "customer_id": ParameterDef(
                type="string",
                description=(
                    "ID of the customer. Omit for an anonymous cash sale"
                ),
            ),
            "txn_date": ParameterDef(
                type="string", description="Sale date as YYYY-MM-DD"
            ),
            "doc_number": ParameterDef(
                type="string", description="Reference number for the transaction"
            ),
            "payment_method_id": ParameterDef(
                type="string",
                description="ID of the PaymentMethod the customer paid with",
            ),
            "payment_reference_number": ParameterDef(
                type="string",
                description="Check or transaction number for the payment",
            ),
            "deposit_to_account_id": ParameterDef(
                type="string",
                description=(
                    "ID of the account the money lands in. Defaults to "
                    "Undeposited Funds"
                ),
            ),
            "bill_email": ParameterDef(
                type="string",
                description="Email address the receipt is addressed to",
            ),
            "customer_memo": ParameterDef(
                type="string",
                description="Message shown to the customer on the receipt",
            ),
            "private_note": ParameterDef(type="string", description="Internal note"),
            "currency_code": ParameterDef(
                type="string", description="ISO 4217 code such as USD"
            ),
            "bill_address": ParameterDef(
                type="object",
                description=(
                    "Billing address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "ship_address": ParameterDef(
                type="object",
                description=(
                    "Shipping address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "global_tax_calculation": ParameterDef(
                type="string",
                description=(
                    "TaxExcluded, TaxInclusive or NotApplicable. Non-US companies only"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="get_sales_receipt",
        description="Read one sales receipt by its ID, including its line items.",
        parameters={
            "sales_receipt_id": ParameterDef(
                type="string",
                description="ID of the sales receipt to read",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_sales_receipt",
        description=(
            "Change fields on an existing sales receipt, leaving the rest alone. "
            "This is a sparse update: only the values supplied here change."
        ),
        parameters={
            "sales_receipt_id": ParameterDef(
                type="string",
                description="ID of the sales receipt to update",
                required=True,
            ),
            "customer_id": ParameterDef(
                type="string", description="ID of the customer"
            ),
            "line_items": ParameterDef(
                type="array",
                description=(
                    "Replacement line items. Supplying this REPLACES every "
                    "existing line, so include the lines you want to keep. Each "
                    "object accepts item_ref, qty, unit_price, description, "
                    "tax_code_ref and service_date"
                ),
            ),
            "txn_date": ParameterDef(
                type="string", description="Sale date as YYYY-MM-DD"
            ),
            "doc_number": ParameterDef(
                type="string", description="Reference number for the transaction"
            ),
            "payment_method_id": ParameterDef(
                type="string",
                description="ID of the PaymentMethod the customer paid with",
            ),
            "payment_reference_number": ParameterDef(
                type="string",
                description="Check or transaction number for the payment",
            ),
            "deposit_to_account_id": ParameterDef(
                type="string", description="ID of the account the money lands in"
            ),
            "bill_email": ParameterDef(
                type="string",
                description="Email address the receipt is addressed to",
            ),
            "customer_memo": ParameterDef(
                type="string",
                description="Message shown to the customer on the receipt",
            ),
            "private_note": ParameterDef(type="string", description="Internal note"),
            "currency_code": ParameterDef(
                type="string", description="ISO 4217 code such as USD"
            ),
            "bill_address": ParameterDef(
                type="object",
                description=(
                    "Billing address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "ship_address": ParameterDef(
                type="object",
                description=(
                    "Shipping address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "global_tax_calculation": ParameterDef(
                type="string",
                description=(
                    "TaxExcluded, TaxInclusive or NotApplicable. Non-US companies only"
                ),
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional — it is fetched "
                    "automatically when omitted, at the cost of one extra request"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="delete_sales_receipt",
        description=(
            "Delete a sales receipt permanently. Both the sale and the payment "
            "it recorded come off the books."
        ),
        parameters={
            "sales_receipt_id": ParameterDef(
                type="string",
                description="ID of the sales receipt to delete",
                required=True,
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional — it is fetched "
                    "automatically when omitted, at the cost of one extra request"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="search_sales_receipts",
        description=(
            "Find sales receipts by customer, number or date range. All supplied "
            "filters are combined with AND; with none at all this lists the "
            "company's sales receipts."
        ),
        parameters={
            "customer_id": ParameterDef(
                type="string", description="Only receipts for this customer ID"
            ),
            "doc_number": ParameterDef(
                type="string",
                description="Only the receipt carrying this reference number",
            ),
            "txn_date_from": ParameterDef(
                type="string",
                description="Only receipts dated on or after this date (YYYY-MM-DD)",
            ),
            "txn_date_to": ParameterDef(
                type="string",
                description="Only receipts dated on or before this date (YYYY-MM-DD)",
            ),
            "max_results": ParameterDef(
                type="integer", description="Maximum number of receipts to return"
            ),
            "start_position": ParameterDef(
                type="integer",
                description="1-based index of the first result, for paging",
            ),
        },
    ),
    ActionDefinition(
        name="create_credit_memo",
        description=(
            "Issue a credit memo to a customer. Records credit the customer can "
            "apply against an open invoice — the usual answer to a return, an "
            "overcharge or a goodwill discount."
        ),
        parameters={
            "customer_id": ParameterDef(
                type="string",
                description="ID of the customer receiving the credit",
                required=True,
            ),
            "line_items": ParameterDef(
                type="array",
                description=(
                    "What is being credited back. Each object accepts item_ref "
                    "(the QuickBooks Item ID), qty, unit_price, description, "
                    "tax_code_ref and service_date (YYYY-MM-DD). The line total "
                    "defaults to qty * unit_price; pass amount to override it"
                ),
                required=True,
            ),
            "txn_date": ParameterDef(
                type="string", description="Credit memo date as YYYY-MM-DD"
            ),
            "doc_number": ParameterDef(
                type="string", description="Reference number for the transaction"
            ),
            "bill_email": ParameterDef(
                type="string",
                description="Email address the credit memo is addressed to",
            ),
            "customer_memo": ParameterDef(
                type="string",
                description="Message shown to the customer on the credit memo",
            ),
            "private_note": ParameterDef(type="string", description="Internal note"),
            "currency_code": ParameterDef(
                type="string", description="ISO 4217 code such as USD"
            ),
            "bill_address": ParameterDef(
                type="object",
                description=(
                    "Billing address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "global_tax_calculation": ParameterDef(
                type="string",
                description=(
                    "TaxExcluded, TaxInclusive or NotApplicable. Non-US companies only"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="get_credit_memo",
        description="Read one credit memo by ID, including how much credit is left.",
        parameters={
            "credit_memo_id": ParameterDef(
                type="string",
                description="ID of the credit memo to read",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_credit_memo",
        description=(
            "Change fields on an existing credit memo, leaving the rest alone. "
            "This is a sparse update: only the values supplied here change."
        ),
        parameters={
            "credit_memo_id": ParameterDef(
                type="string",
                description="ID of the credit memo to update",
                required=True,
            ),
            "customer_id": ParameterDef(
                type="string",
                description="ID of the customer receiving the credit",
            ),
            "line_items": ParameterDef(
                type="array",
                description=(
                    "Replacement line items. Supplying this REPLACES every "
                    "existing line, so include the lines you want to keep. Each "
                    "object accepts item_ref, qty, unit_price, description, "
                    "tax_code_ref and service_date"
                ),
            ),
            "txn_date": ParameterDef(
                type="string", description="Credit memo date as YYYY-MM-DD"
            ),
            "doc_number": ParameterDef(
                type="string", description="Reference number for the transaction"
            ),
            "bill_email": ParameterDef(
                type="string",
                description="Email address the credit memo is addressed to",
            ),
            "customer_memo": ParameterDef(
                type="string",
                description="Message shown to the customer on the credit memo",
            ),
            "private_note": ParameterDef(type="string", description="Internal note"),
            "currency_code": ParameterDef(
                type="string", description="ISO 4217 code such as USD"
            ),
            "bill_address": ParameterDef(
                type="object",
                description=(
                    "Billing address. Keys: line1, line2, city, state, postal_code, "
                    "country"
                ),
            ),
            "global_tax_calculation": ParameterDef(
                type="string",
                description=(
                    "TaxExcluded, TaxInclusive or NotApplicable. Non-US companies only"
                ),
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional — it is fetched "
                    "automatically when omitted, at the cost of one extra request"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="delete_credit_memo",
        description=(
            "Delete a credit memo permanently. Any credit it had already applied "
            "to an invoice is released, so the invoice balance goes back up."
        ),
        parameters={
            "credit_memo_id": ParameterDef(
                type="string",
                description="ID of the credit memo to delete",
                required=True,
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional — it is fetched "
                    "automatically when omitted, at the cost of one extra request"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="search_credit_memos",
        description=(
            "Find credit memos by customer, number or date range. All supplied "
            "filters are combined with AND; with none at all this lists the "
            "company's credit memos."
        ),
        parameters={
            "customer_id": ParameterDef(
                type="string", description="Only credit memos for this customer ID"
            ),
            "doc_number": ParameterDef(
                type="string",
                description="Only the credit memo carrying this reference number",
            ),
            "txn_date_from": ParameterDef(
                type="string",
                description=(
                    "Only credit memos dated on or after this date (YYYY-MM-DD)"
                ),
            ),
            "txn_date_to": ParameterDef(
                type="string",
                description=(
                    "Only credit memos dated on or before this date (YYYY-MM-DD)"
                ),
            ),
            "max_results": ParameterDef(
                type="integer", description="Maximum number of credit memos to return"
            ),
            "start_position": ParameterDef(
                type="integer",
                description="1-based index of the first result, for paging",
            ),
        },
    ),
    ActionDefinition(
        name="send_invoice",
        description=(
            "Email an invoice to the customer. QuickBooks sends the mail itself "
            "and marks the invoice EmailSent."
        ),
        parameters={
            "invoice_id": ParameterDef(
                type="string",
                description="ID of the invoice to email",
                required=True,
            ),
            "email": ParameterDef(
                type="string",
                description=(
                    "Address to send to. Defaults to the invoice's own billing "
                    "email; supplying one also updates that billing email"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="send_estimate",
        description=(
            "Email an estimate to the customer. QuickBooks sends the mail itself "
            "and marks the estimate EmailSent."
        ),
        parameters={
            "estimate_id": ParameterDef(
                type="string",
                description="ID of the estimate to email",
                required=True,
            ),
            "email": ParameterDef(
                type="string",
                description=(
                    "Address to send to. Defaults to the estimate's own billing "
                    "email; supplying one also updates that billing email"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="void_invoice",
        description=(
            "Void an invoice, keeping the record on the books. The invoice stays "
            "in QuickBooks with its number and date intact, but its amount drops "
            "to zero and it is marked as voided — so the audit trail survives. "
            "This is the safe way to cancel a billing mistake; delete_invoice "
            "erases the transaction instead."
        ),
        parameters={
            "invoice_id": ParameterDef(
                type="string",
                description="ID of the invoice to void",
                required=True,
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional — it is fetched "
                    "automatically when omitted, at the cost of one extra request"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="create_vendor",
        description=(
            "Create a vendor: a supplier the company buys from and pays bills "
            "to. Needs a display name, or a first/last name for QuickBooks to "
            "build one from."
        ),
        parameters={
            "display_name": ParameterDef(
                type="string",
                description=(
                    "Name to show for the vendor. Must be unique across all "
                    "vendors, customers and employees."
                ),
            ),
            "company_name": ParameterDef(
                type="string", description="Vendor's company name"
            ),
            "given_name": ParameterDef(
                type="string", description="Contact's first name"
            ),
            "family_name": ParameterDef(
                type="string", description="Contact's last name"
            ),
            "email": ParameterDef(type="string", description="Primary email address"),
            "phone": ParameterDef(type="string", description="Primary phone number"),
            "website": ParameterDef(type="string", description="Website URL"),
            "print_on_check_name": ParameterDef(
                type="string",
                description="Name to print on cheques paid to this vendor",
            ),
            "account_number": ParameterDef(
                type="string", description="Your account number with this vendor"
            ),
            "tax_identifier": ParameterDef(
                type="string", description="Vendor's tax ID (EIN or SSN)"
            ),
            "term_id": ParameterDef(
                type="string",
                description="ID of the default payment term for this vendor",
            ),
            "vendor_1099": ParameterDef(
                type="boolean",
                description="True if this vendor is a 1099 contractor",
            ),
            "bill_address_line1": ParameterDef(
                type="string", description="Billing address street line"
            ),
            "bill_address_city": ParameterDef(
                type="string", description="Billing city"
            ),
            "bill_address_state": ParameterDef(
                type="string", description="Billing state, province or region"
            ),
            "bill_address_postal_code": ParameterDef(
                type="string", description="Billing postal or ZIP code"
            ),
            "bill_address_country": ParameterDef(
                type="string", description="Billing country"
            ),
        },
    ),
    ActionDefinition(
        name="get_vendor",
        description=(
            "Read one vendor by ID, including its open balance, contact "
            "details and billing address."
        ),
        parameters={
            "vendor_id": ParameterDef(
                type="string",
                description="ID of the vendor to read",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_vendor",
        description=(
            "Change a vendor's details. Only the fields supplied are altered; "
            "everything else is left as it is. Set active=false to retire the "
            "vendor or true to restore it."
        ),
        parameters={
            "vendor_id": ParameterDef(
                type="string",
                description="ID of the vendor to update",
                required=True,
            ),
            "display_name": ParameterDef(
                type="string", description="New display name"
            ),
            "company_name": ParameterDef(
                type="string", description="New company name"
            ),
            "given_name": ParameterDef(type="string", description="New first name"),
            "family_name": ParameterDef(type="string", description="New last name"),
            "email": ParameterDef(
                type="string", description="New primary email address"
            ),
            "phone": ParameterDef(
                type="string", description="New primary phone number"
            ),
            "website": ParameterDef(type="string", description="New website URL"),
            "print_on_check_name": ParameterDef(
                type="string", description="New name to print on cheques"
            ),
            "account_number": ParameterDef(
                type="string", description="New account number with this vendor"
            ),
            "tax_identifier": ParameterDef(type="string", description="New tax ID"),
            "term_id": ParameterDef(
                type="string", description="New default payment term ID"
            ),
            "vendor_1099": ParameterDef(
                type="boolean",
                description="Whether this vendor is a 1099 contractor",
            ),
            "active": ParameterDef(
                type="boolean",
                description="False retires the vendor, true restores it",
            ),
            "bill_address_line1": ParameterDef(
                type="string", description="New billing address street line"
            ),
            "bill_address_city": ParameterDef(
                type="string", description="New billing city"
            ),
            "bill_address_state": ParameterDef(
                type="string", description="New billing state, province or region"
            ),
            "bill_address_postal_code": ParameterDef(
                type="string", description="New billing postal or ZIP code"
            ),
            "bill_address_country": ParameterDef(
                type="string", description="New billing country"
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional - it is fetched "
                    "automatically when omitted, at the cost of one extra "
                    "request."
                ),
            ),
        },
    ),
    ActionDefinition(
        name="delete_vendor",
        description=(
            "Deactivate a vendor. QuickBooks does not permit deleting "
            "vendors, so this marks the record inactive; its history is "
            "preserved and update_vendor with active=true reverses it."
        ),
        parameters={
            "vendor_id": ParameterDef(
                type="string",
                description="ID of the vendor to deactivate",
                required=True,
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional - it is fetched "
                    "automatically when omitted, at the cost of one extra "
                    "request."
                ),
            ),
        },
    ),
    ActionDefinition(
        name="search_vendors",
        description=(
            "Find vendors by name or active state. Omit every filter to list "
            "all vendors."
        ),
        parameters={
            "display_name": ParameterDef(
                type="string", description="Exact display name to match"
            ),
            "company_name": ParameterDef(
                type="string", description="Exact company name to match"
            ),
            "name_contains": ParameterDef(
                type="string",
                description="Substring to look for anywhere in the display name",
            ),
            "active": ParameterDef(
                type="boolean",
                description="True for active vendors only, false for retired",
            ),
            "max_results": ParameterDef(
                type="integer",
                description="Maximum number of vendors to return",
            ),
            "start_position": ParameterDef(
                type="integer",
                description="1-based index of the first result, for paging",
            ),
        },
    ),
    ActionDefinition(
        name="create_bill",
        description=(
            "Record a bill: money a vendor has invoiced that the company owes "
            "but has not yet paid. If the expense was paid on the spot, use "
            "create_purchase instead."
        ),
        parameters={
            "vendor_id": ParameterDef(
                type="string",
                description="ID of the vendor who sent the bill",
                required=True,
            ),
            "lines": ParameterDef(
                type="array",
                description=(
                    "Expense lines, e.g. [{'amount': 100.0, 'account_id': '7', "
                    "'description': 'Office rent'}]. Use 'item_id' with "
                    "'quantity' and 'unit_price' instead of 'account_id' when "
                    "buying a product. Optional per-line keys: 'customer_id', "
                    "'billable_status', 'class_id', 'tax_code_id'."
                ),
                required=True,
            ),
            "txn_date": ParameterDef(
                type="string",
                description="Bill date as YYYY-MM-DD; defaults to today",
            ),
            "due_date": ParameterDef(
                type="string",
                description=(
                    "Payment due date as YYYY-MM-DD; derived from the term "
                    "when omitted"
                ),
            ),
            "doc_number": ParameterDef(
                type="string",
                description="The vendor's invoice or reference number",
            ),
            "private_note": ParameterDef(
                type="string",
                description="Internal memo, not visible to the vendor",
            ),
            "ap_account_id": ParameterDef(
                type="string",
                description="Accounts Payable account to credit",
            ),
            "sales_term_id": ParameterDef(
                type="string",
                description="ID of the payment term governing the due date",
            ),
            "department_id": ParameterDef(
                type="string",
                description="ID of the location or department for this bill",
            ),
            "currency_code": ParameterDef(
                type="string",
                description=(
                    "Three-letter currency code, required if multicurrency is on"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="get_bill",
        description=(
            "Read one bill by ID, including its expense lines and the balance "
            "still unpaid."
        ),
        parameters={
            "bill_id": ParameterDef(
                type="string", description="ID of the bill to read", required=True
            ),
        },
    ),
    ActionDefinition(
        name="update_bill",
        description=(
            "Change a bill. Anything not mentioned keeps its current value: "
            "QuickBooks rewrites a bill wholesale rather than patching it, so "
            "this action reads the bill first and lays the supplied changes "
            "over it. Omitting lines leaves the existing ones untouched."
        ),
        parameters={
            "bill_id": ParameterDef(
                type="string",
                description="ID of the bill to update",
                required=True,
            ),
            "vendor_id": ParameterDef(type="string", description="New vendor ID"),
            "lines": ParameterDef(
                type="array",
                description=(
                    "Replacement expense lines; omit to leave the bill's "
                    "existing lines untouched. Supplying this replaces the "
                    "whole set, and each replacement line inherits the class "
                    "and tax code of the line it replaces unless set here. "
                    "Same shape as create_bill."
                ),
            ),
            "txn_date": ParameterDef(
                type="string", description="New bill date as YYYY-MM-DD"
            ),
            "due_date": ParameterDef(
                type="string", description="New due date as YYYY-MM-DD"
            ),
            "doc_number": ParameterDef(
                type="string",
                description="New vendor invoice or reference number",
            ),
            "private_note": ParameterDef(
                type="string", description="New internal memo"
            ),
            "ap_account_id": ParameterDef(
                type="string", description="New Accounts Payable account ID"
            ),
            "sales_term_id": ParameterDef(
                type="string", description="New payment term ID"
            ),
            "department_id": ParameterDef(
                type="string", description="New location or department ID"
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional, and it saves "
                    "no round trip here because this action reads the bill "
                    "either way, but it is honoured when supplied."
                ),
            ),
        },
    ),
    ActionDefinition(
        name="delete_bill",
        description=(
            "Delete a bill. Any bill payment already applied to it must be "
            "unlinked first, or QuickBooks refuses the delete."
        ),
        parameters={
            "bill_id": ParameterDef(
                type="string",
                description="ID of the bill to delete",
                required=True,
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional - it is fetched "
                    "automatically when omitted, at the cost of one extra "
                    "request."
                ),
            ),
        },
    ),
    ActionDefinition(
        name="search_bills",
        description=(
            "Find bills by vendor, date, due date or unpaid state. Use "
            "unpaid_only to answer 'what do we owe?'."
        ),
        parameters={
            "vendor_id": ParameterDef(
                type="string", description="Only bills from this vendor"
            ),
            "doc_number": ParameterDef(
                type="string",
                description="Exact vendor invoice or reference number",
            ),
            "ap_account_id": ParameterDef(
                type="string",
                description="Only bills against this Accounts Payable account",
            ),
            "txn_date_from": ParameterDef(
                type="string", description="Earliest bill date, YYYY-MM-DD"
            ),
            "txn_date_to": ParameterDef(
                type="string", description="Latest bill date, YYYY-MM-DD"
            ),
            "due_date_from": ParameterDef(
                type="string", description="Earliest due date, YYYY-MM-DD"
            ),
            "due_date_to": ParameterDef(
                type="string", description="Latest due date, YYYY-MM-DD"
            ),
            "unpaid_only": ParameterDef(
                type="boolean",
                description="True to return only bills with a balance owing",
            ),
            "max_results": ParameterDef(
                type="integer", description="Maximum number of bills to return"
            ),
            "start_position": ParameterDef(
                type="integer",
                description="1-based index of the first result, for paging",
            ),
        },
    ),
    ActionDefinition(
        name="create_bill_payment",
        description=(
            "Pay a vendor: record money going OUT of the company to settle one "
            "or more bills. This is the accounts-payable side. To record money "
            "coming IN from a customer against an invoice, use create_payment."
        ),
        parameters={
            "vendor_id": ParameterDef(
                type="string",
                description="ID of the vendor being paid",
                required=True,
            ),
            "total_amount": ParameterDef(
                type="number",
                description="Total amount paid to the vendor",
                required=True,
            ),
            "pay_type": ParameterDef(
                type="string",
                description="How the vendor was paid: Check or CreditCard",
                required=True,
            ),
            "bank_account_id": ParameterDef(
                type="string",
                description=(
                    "Bank account the money leaves. Required when pay_type is "
                    "Check."
                ),
            ),
            "credit_card_account_id": ParameterDef(
                type="string",
                description=(
                    "Credit card account charged. Required when pay_type is "
                    "CreditCard."
                ),
            ),
            "applied_bills": ParameterDef(
                type="array",
                description=(
                    "Bills this payment settles, e.g. [{'bill_id': '12', "
                    "'amount': 200.0}]. Leave empty to record an unapplied "
                    "credit with the vendor."
                ),
            ),
            "txn_date": ParameterDef(
                type="string",
                description="Payment date as YYYY-MM-DD; defaults to today",
            ),
            "doc_number": ParameterDef(
                type="string", description="Cheque number or payment reference"
            ),
            "private_note": ParameterDef(
                type="string", description="Internal memo"
            ),
            "ap_account_id": ParameterDef(
                type="string", description="Accounts Payable account to debit"
            ),
            "currency_code": ParameterDef(
                type="string",
                description=(
                    "Three-letter currency code, required if multicurrency is on"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="get_bill_payment",
        description=(
            "Read one payment the company made to a vendor, including which "
            "bills it settled and the account it was paid from."
        ),
        parameters={
            "bill_payment_id": ParameterDef(
                type="string",
                description="ID of the bill payment to read",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_bill_payment",
        description=(
            "Change a payment made to a vendor. Only the fields supplied are "
            "altered; supplying applied_bills replaces the whole set of "
            "settled bills."
        ),
        parameters={
            "bill_payment_id": ParameterDef(
                type="string",
                description="ID of the bill payment to update",
                required=True,
            ),
            "vendor_id": ParameterDef(type="string", description="New vendor ID"),
            "total_amount": ParameterDef(
                type="number", description="New total amount paid"
            ),
            "pay_type": ParameterDef(
                type="string",
                description="New payment method: Check or CreditCard",
            ),
            "bank_account_id": ParameterDef(
                type="string",
                description="New bank account ID, for a Check payment",
            ),
            "credit_card_account_id": ParameterDef(
                type="string",
                description="New credit card account ID, for a CreditCard payment",
            ),
            "applied_bills": ParameterDef(
                type="array",
                description=(
                    "Replacement set of settled bills, e.g. [{'bill_id': '12', "
                    "'amount': 200.0}]; this replaces every existing line."
                ),
            ),
            "txn_date": ParameterDef(
                type="string", description="New payment date as YYYY-MM-DD"
            ),
            "doc_number": ParameterDef(
                type="string",
                description="New cheque number or payment reference",
            ),
            "private_note": ParameterDef(
                type="string", description="New internal memo"
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional - it is fetched "
                    "automatically when omitted, at the cost of one extra "
                    "request."
                ),
            ),
        },
    ),
    ActionDefinition(
        name="delete_bill_payment",
        description=(
            "Delete a payment made to a vendor, restoring the outstanding "
            "balance on the bills it had settled."
        ),
        parameters={
            "bill_payment_id": ParameterDef(
                type="string",
                description="ID of the bill payment to delete",
                required=True,
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional - it is fetched "
                    "automatically when omitted, at the cost of one extra "
                    "request."
                ),
            ),
        },
    ),
    ActionDefinition(
        name="search_bill_payments",
        description=(
            "Find payments the company made to vendors, by vendor, reference "
            "or date. This searches money OUT; for payments received from "
            "customers use search_payments."
        ),
        parameters={
            "vendor_id": ParameterDef(
                type="string", description="Only payments made to this vendor"
            ),
            "doc_number": ParameterDef(
                type="string",
                description="Exact cheque number or payment reference",
            ),
            "ap_account_id": ParameterDef(
                type="string",
                description="Only payments against this Accounts Payable account",
            ),
            "txn_date_from": ParameterDef(
                type="string", description="Earliest payment date, YYYY-MM-DD"
            ),
            "txn_date_to": ParameterDef(
                type="string", description="Latest payment date, YYYY-MM-DD"
            ),
            "max_results": ParameterDef(
                type="integer",
                description="Maximum number of bill payments to return",
            ),
            "start_position": ParameterDef(
                type="integer",
                description="1-based index of the first result, for paging",
            ),
        },
    ),
    ActionDefinition(
        name="create_payment",
        description=(
            "Receive a customer payment: record money coming IN and apply it "
            "to the customer's invoices. This is the accounts-receivable side. "
            "To record money going OUT to a vendor against a bill, use "
            "create_bill_payment."
        ),
        parameters={
            "customer_id": ParameterDef(
                type="string",
                description="ID of the customer the money came from",
                required=True,
            ),
            "total_amount": ParameterDef(
                type="number",
                description="Total amount received",
                required=True,
            ),
            "applied_invoices": ParameterDef(
                type="array",
                description=(
                    "Invoices this payment settles, e.g. [{'invoice_id': '42', "
                    "'amount': 150.0}]. Leave empty to record an unapplied "
                    "credit on the customer's account."
                ),
            ),
            "payment_method_id": ParameterDef(
                type="string",
                description="ID of the payment method (cash, cheque, card)",
            ),
            "deposit_to_account_id": ParameterDef(
                type="string",
                description=(
                    "Account to deposit into; Undeposited Funds when omitted"
                ),
            ),
            "txn_date": ParameterDef(
                type="string",
                description="Receipt date as YYYY-MM-DD; defaults to today",
            ),
            "payment_ref_num": ParameterDef(
                type="string",
                description="Cheque number or other reference for the receipt",
            ),
            "private_note": ParameterDef(
                type="string", description="Internal memo"
            ),
            "currency_code": ParameterDef(
                type="string",
                description=(
                    "Three-letter currency code, required if multicurrency is on"
                ),
            ),
            "exchange_rate": ParameterDef(
                type="number",
                description="Home-currency units per unit of currency_code",
            ),
        },
    ),
    ActionDefinition(
        name="get_payment",
        description=(
            "Read one payment received from a customer, including which "
            "invoices it was applied to and how much is still unapplied."
        ),
        parameters={
            "payment_id": ParameterDef(
                type="string",
                description="ID of the customer payment to read",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_payment",
        description=(
            "Change a payment received from a customer. Only the fields "
            "supplied are altered; QuickBooks rewrites payment lines "
            "all-or-nothing, so send every applied invoice whenever you send "
            "any."
        ),
        parameters={
            "payment_id": ParameterDef(
                type="string",
                description="ID of the customer payment to update",
                required=True,
            ),
            "customer_id": ParameterDef(
                type="string", description="New customer ID"
            ),
            "total_amount": ParameterDef(
                type="number", description="New total amount received"
            ),
            "applied_invoices": ParameterDef(
                type="array",
                description=(
                    "Replacement set of settled invoices, e.g. "
                    "[{'invoice_id': '42', 'amount': 150.0}]; this replaces "
                    "every existing line."
                ),
            ),
            "payment_method_id": ParameterDef(
                type="string", description="New payment method ID"
            ),
            "deposit_to_account_id": ParameterDef(
                type="string", description="New deposit account ID"
            ),
            "txn_date": ParameterDef(
                type="string", description="New receipt date as YYYY-MM-DD"
            ),
            "payment_ref_num": ParameterDef(
                type="string", description="New cheque number or reference"
            ),
            "private_note": ParameterDef(
                type="string", description="New internal memo"
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional - it is fetched "
                    "automatically when omitted, at the cost of one extra "
                    "request."
                ),
            ),
        },
    ),
    ActionDefinition(
        name="delete_payment",
        description=(
            "Delete a payment received from a customer, reopening the balance "
            "on any invoices it had paid."
        ),
        parameters={
            "payment_id": ParameterDef(
                type="string",
                description="ID of the customer payment to delete",
                required=True,
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional - it is fetched "
                    "automatically when omitted, at the cost of one extra "
                    "request."
                ),
            ),
        },
    ),
    ActionDefinition(
        name="search_payments",
        description=(
            "Find payments received from customers, by customer, reference or "
            "date. This searches money IN; for payments the company made to "
            "vendors use search_bill_payments."
        ),
        parameters={
            "customer_id": ParameterDef(
                type="string",
                description="Only payments received from this customer",
            ),
            "payment_ref_num": ParameterDef(
                type="string",
                description="Exact cheque number or payment reference",
            ),
            "txn_date_from": ParameterDef(
                type="string", description="Earliest receipt date, YYYY-MM-DD"
            ),
            "txn_date_to": ParameterDef(
                type="string", description="Latest receipt date, YYYY-MM-DD"
            ),
            "max_results": ParameterDef(
                type="integer", description="Maximum number of payments to return"
            ),
            "start_position": ParameterDef(
                type="integer",
                description="1-based index of the first result, for paging",
            ),
        },
    ),
    ActionDefinition(
        name="create_purchase",
        description=(
            "Record an expense that was already paid, by cash, cheque or "
            "credit card. Use this when the money has already left the "
            "account; for a vendor invoice that is still owed, use create_bill."
        ),
        parameters={
            "account_id": ParameterDef(
                type="string",
                description=(
                    "Account the money came out of. A Check purchase must name "
                    "a bank account, a CreditCard purchase a credit card "
                    "account."
                ),
                required=True,
            ),
            "payment_type": ParameterDef(
                type="string",
                description="How it was paid: Cash, Check or CreditCard",
                required=True,
            ),
            "lines": ParameterDef(
                type="array",
                description=(
                    "Expense lines, e.g. [{'amount': 25.0, 'account_id': '13', "
                    "'description': 'Client lunch'}]. Use 'item_id' with "
                    "'quantity' and 'unit_price' instead of 'account_id' when "
                    "buying a product. Optional per-line keys: 'customer_id', "
                    "'billable_status', 'class_id', 'tax_code_id'."
                ),
                required=True,
            ),
            "entity_id": ParameterDef(
                type="string",
                description="ID of who was paid (vendor, customer or employee)",
            ),
            "entity_type": ParameterDef(
                type="string",
                description=(
                    "Type of the entity_id record: Vendor, Customer or Employee"
                ),
            ),
            "payment_method_id": ParameterDef(
                type="string", description="ID of the payment method"
            ),
            "txn_date": ParameterDef(
                type="string",
                description="Expense date as YYYY-MM-DD; defaults to today",
            ),
            "doc_number": ParameterDef(
                type="string",
                description="Cheque number or reference for the expense",
            ),
            "private_note": ParameterDef(
                type="string", description="Internal memo"
            ),
            "department_id": ParameterDef(
                type="string", description="ID of the location or department"
            ),
            "credit": ParameterDef(
                type="boolean",
                description=(
                    "True to record a credit card refund instead of a charge"
                ),
            ),
            "currency_code": ParameterDef(
                type="string",
                description=(
                    "Three-letter currency code, required if multicurrency is on"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="get_purchase",
        description=(
            "Read one purchase (an already-paid expense) by ID, including its "
            "expense lines and the account it was paid from."
        ),
        parameters={
            "purchase_id": ParameterDef(
                type="string",
                description="ID of the purchase to read",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_purchase",
        description=(
            "Change a purchase (expense). Only the fields supplied are "
            "altered, except lines: sending any line replaces the whole set."
        ),
        parameters={
            "purchase_id": ParameterDef(
                type="string",
                description="ID of the purchase to update",
                required=True,
            ),
            "account_id": ParameterDef(
                type="string", description="New account the money came out of"
            ),
            "payment_type": ParameterDef(
                type="string",
                description="New payment type: Cash, Check or CreditCard",
            ),
            "lines": ParameterDef(
                type="array",
                description=(
                    "Replacement expense lines; supplying this replaces every "
                    "existing line. Same shape as create_purchase."
                ),
            ),
            "entity_id": ParameterDef(type="string", description="New payee ID"),
            "entity_type": ParameterDef(
                type="string",
                description="Type of the payee: Vendor, Customer or Employee",
            ),
            "payment_method_id": ParameterDef(
                type="string", description="New payment method ID"
            ),
            "txn_date": ParameterDef(
                type="string", description="New expense date as YYYY-MM-DD"
            ),
            "doc_number": ParameterDef(
                type="string", description="New cheque number or reference"
            ),
            "private_note": ParameterDef(
                type="string", description="New internal memo"
            ),
            "credit": ParameterDef(
                type="boolean",
                description="Whether this is a credit card refund",
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional - it is fetched "
                    "automatically when omitted, at the cost of one extra "
                    "request."
                ),
            ),
        },
    ),
    ActionDefinition(
        name="delete_purchase",
        description=(
            "Delete a purchase (expense), reversing its effect on the account "
            "it was paid from."
        ),
        parameters={
            "purchase_id": ParameterDef(
                type="string",
                description="ID of the purchase to delete",
                required=True,
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional - it is fetched "
                    "automatically when omitted, at the cost of one extra "
                    "request."
                ),
            ),
        },
    ),
    ActionDefinition(
        name="search_purchases",
        description=(
            "Find purchases (already-paid expenses) by date, reference or "
            "amount."
        ),
        parameters={
            "doc_number": ParameterDef(
                type="string", description="Exact cheque number or reference"
            ),
            "txn_date_from": ParameterDef(
                type="string", description="Earliest expense date, YYYY-MM-DD"
            ),
            "txn_date_to": ParameterDef(
                type="string", description="Latest expense date, YYYY-MM-DD"
            ),
            "min_total_amount": ParameterDef(
                type="number",
                description="Only purchases at or above this total",
            ),
            "max_total_amount": ParameterDef(
                type="number",
                description="Only purchases at or below this total",
            ),
            "max_results": ParameterDef(
                type="integer",
                description="Maximum number of purchases to return",
            ),
            "start_position": ParameterDef(
                type="integer",
                description="1-based index of the first result, for paging",
            ),
        },
    ),
    ActionDefinition(
        name="create_item",
        description=(
            "Create a product or service in QuickBooks. Every item needs a unique name "
            "and a type; a Service or NonInventory item needs an income account, and an "
            "Inventory item additionally needs an expense account, an asset account, an "
            "opening quantity and an inventory start date."
        ),
        parameters={
            "name": ParameterDef(
                type="string",
                description="Name of the product or service. Must be unique.",
                required=True,
            ),
            "item_type": ParameterDef(
                type="string",
                description=(
                    "Classification of the item: Inventory, NonInventory or Service"
                ),
                required=True,
            ),
            "description": ParameterDef(
                type="string",
                description="Sales description shown on customer-facing documents",
            ),
            "sku": ParameterDef(
                type="string",
                description="Stock keeping unit used to track the item in inventory",
            ),
            "unit_price": ParameterDef(
                type="number",
                description=(
                    "Price or rate for the item; express a discount or tax rate as a "
                    "fraction, e.g. 0.4 for 40%"
                ),
            ),
            "purchase_cost": ParameterDef(
                type="number",
                description="Amount paid when buying the item, in the home currency",
            ),
            "purchase_description": ParameterDef(
                type="string",
                description="Purchase description shown on bills and purchase orders",
            ),
            "income_account_id": ParameterDef(
                type="string",
                description=(
                    "Id of the account recording sales of this item; required for "
                    "Inventory and Service items"
                ),
            ),
            "expense_account_id": ParameterDef(
                type="string",
                description=(
                    "Id of the Cost of Goods Sold account; required for Inventory items"
                ),
            ),
            "asset_account_id": ParameterDef(
                type="string",
                description=(
                    "Id of the Other Current Asset inventory account; required for "
                    "Inventory items"
                ),
            ),
            "track_qty_on_hand": ParameterDef(
                type="boolean",
                description=(
                    "Track quantity on hand; Inventory items only and cannot be turned "
                    "back off once true"
                ),
            ),
            "qty_on_hand": ParameterDef(
                type="number",
                description=(
                    "Opening quantity available for sale; required for Inventory items"
                ),
            ),
            "inv_start_date": ParameterDef(
                type="string",
                description=(
                    "Date of the opening inventory balance as YYYY-MM-DD; required for "
                    "Inventory items"
                ),
            ),
            "taxable": ParameterDef(
                type="boolean",
                description="Whether transactions for this item are taxable (US only)",
            ),
            "sub_item": ParameterDef(
                type="boolean",
                description="Whether this item is nested under another item",
            ),
            "parent_item_id": ParameterDef(
                type="string",
                description="Id of the parent item; required when sub_item is true",
            ),
            "pref_vendor_id": ParameterDef(
                type="string",
                description="Id of the preferred vendor to buy this item from",
            ),
            "reorder_point": ParameterDef(
                type="number",
                description="Quantity at which the inventory item should be restocked",
            ),
        },
    ),
    ActionDefinition(
        name="get_item",
        description="Read one product or service by its QuickBooks Id.",
        parameters={
            "item_id": ParameterDef(
                type="string",
                description="Id of the product or service to read",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_item",
        description=(
            "Update a product or service, changing only the fields supplied. Omitted "
            "fields keep their current values, but QuickBooks treats the name as "
            "mandatory on an item write, so pass the item's current name alongside the "
            "change."
        ),
        parameters={
            "item_id": ParameterDef(
                type="string",
                description="Id of the product or service to update",
                required=True,
            ),
            "name": ParameterDef(
                type="string",
                description=(
                    "Name of the item; supply the current name when changing other "
                    "fields"
                ),
            ),
            "item_type": ParameterDef(
                type="string",
                description=(
                    "Classification of the item: Inventory, NonInventory or Service"
                ),
            ),
            "description": ParameterDef(
                type="string", description="Sales description"
            ),
            "sku": ParameterDef(type="string", description="Stock keeping unit"),
            "unit_price": ParameterDef(
                type="number", description="Price or rate for the item"
            ),
            "purchase_cost": ParameterDef(
                type="number", description="Amount paid when buying the item"
            ),
            "purchase_description": ParameterDef(
                type="string", description="Purchase description shown on bills"
            ),
            "income_account_id": ParameterDef(
                type="string",
                description="Id of the account recording sales of this item",
            ),
            "expense_account_id": ParameterDef(
                type="string",
                description="Id of the Cost of Goods Sold account for this item",
            ),
            "asset_account_id": ParameterDef(
                type="string",
                description="Id of the Other Current Asset inventory account",
            ),
            "track_qty_on_hand": ParameterDef(
                type="boolean",
                description="Track quantity on hand; cannot be turned back off",
            ),
            "qty_on_hand": ParameterDef(
                type="number", description="Current quantity available for sale"
            ),
            "inv_start_date": ParameterDef(
                type="string",
                description="Date of the opening inventory balance as YYYY-MM-DD",
            ),
            "taxable": ParameterDef(
                type="boolean",
                description="Whether transactions for this item are taxable",
            ),
            "active": ParameterDef(
                type="boolean",
                description=(
                    "Whether the item is enabled for use; set false to deactivate it"
                ),
            ),
            "sub_item": ParameterDef(
                type="boolean",
                description="Whether this item is nested under another item",
            ),
            "parent_item_id": ParameterDef(
                type="string",
                description="Id of the parent item when sub_item is true",
            ),
            "pref_vendor_id": ParameterDef(
                type="string", description="Id of the preferred vendor for this item"
            ),
            "reorder_point": ParameterDef(
                type="number",
                description="Quantity at which the item should be restocked",
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional — it is fetched "
                    "automatically when omitted, at the cost of one extra request."
                ),
            ),
        },
    ),
    ActionDefinition(
        name="delete_item",
        description=(
            "Remove a product or service from use by deactivating it. QuickBooks does "
            "not permit deleting an item because historical transactions reference it, "
            "so the item is marked inactive: it disappears from lists and pickers while "
            "past invoices, bills and reports stay intact. Reactivate it with "
            "update_item and active=true."
        ),
        parameters={
            "item_id": ParameterDef(
                type="string",
                description="Id of the product or service to deactivate",
                required=True,
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional — it is fetched "
                    "automatically when omitted, at the cost of one extra request."
                ),
            ),
        },
    ),
    ActionDefinition(
        name="search_items",
        description=(
            "Search products and services by name, SKU, type or active state. Filters "
            "are combined with AND; with no filters this returns the whole "
            "products-and-services list, one page at a time."
        ),
        parameters={
            "name": ParameterDef(
                type="string", description="Exact item name to match"
            ),
            "sku": ParameterDef(
                type="string", description="Exact stock keeping unit to match"
            ),
            "item_type": ParameterDef(
                type="string",
                description=(
                    "Item classification to match: Inventory, NonInventory or Service"
                ),
            ),
            "active": ParameterDef(
                type="boolean",
                description="Restrict to active (true) or inactive (false) items",
            ),
            "max_results": ParameterDef(
                type="integer",
                description=(
                    "Maximum number of items to return; QuickBooks caps this at 1000"
                ),
            ),
            "start_position": ParameterDef(
                type="integer",
                description="1-based index of the first row to return, for paging",
            ),
        },
    ),
    ActionDefinition(
        name="create_account",
        description=(
            "Add an account to the QuickBooks chart of accounts. Only the name is "
            "strictly required, but supplying account_type and account_sub_type is "
            "strongly recommended — otherwise QuickBooks picks the classification."
        ),
        parameters={
            "name": ParameterDef(
                type="string",
                description=(
                    "Name of the account; must be unique and may not contain a colon "
                    "or a double quote"
                ),
                required=True,
            ),
            "account_type": ParameterDef(
                type="string",
                description=(
                    "Type of account, e.g. Bank, Expense, Income, AccountsPayable, "
                    "AccountsReceivable, CreditCard, Equity, FixedAsset, "
                    "CostOfGoodsSold, OtherCurrentAsset, OtherCurrentLiability, "
                    "LongTermLiability, OtherAsset, OtherExpense, OtherIncome, "
                    "NonPosting"
                ),
            ),
            "account_sub_type": ParameterDef(
                type="string",
                description=(
                    "Detailed sub-type such as Savings or SalesOfProductIncome; must be "
                    "valid for the chosen account_type"
                ),
            ),
            "description": ParameterDef(
                type="string", description="Description of the account"
            ),
            "acct_num": ParameterDef(
                type="string",
                description=(
                    "Account number in the chart of accounts, when numbering is enabled"
                ),
            ),
            "parent_account_id": ParameterDef(
                type="string",
                description=(
                    "Id of the parent account to nest this account under; the parent's "
                    "account_type must match"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="get_account",
        description="Read one chart-of-accounts entry by its QuickBooks Id.",
        parameters={
            "account_id": ParameterDef(
                type="string",
                description="Id of the account to read",
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="update_account",
        description=(
            "Update a chart-of-accounts entry, or deactivate it with active=false. This "
            "is also how an account is removed: QuickBooks does not permit deleting an "
            "account because the ledger history points at it, so setting active=false "
            "hides it from the chart of accounts while posted transactions stay intact."
        ),
        parameters={
            "account_id": ParameterDef(
                type="string",
                description="Id of the account to update",
                required=True,
            ),
            "name": ParameterDef(
                type="string", description="New name for the account"
            ),
            "account_type": ParameterDef(
                type="string", description="New account type"
            ),
            "account_sub_type": ParameterDef(
                type="string", description="New account sub-type"
            ),
            "description": ParameterDef(
                type="string", description="New description"
            ),
            "acct_num": ParameterDef(type="string", description="New account number"),
            "active": ParameterDef(
                type="boolean",
                description=(
                    "Set false to deactivate the account, true to reactivate it"
                ),
            ),
            "parent_account_id": ParameterDef(
                type="string",
                description="Id of the account to nest this account under",
            ),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional — the account is read "
                    "before every write anyway, so this only overrides the fetched "
                    "value."
                ),
            ),
        },
    ),
    ActionDefinition(
        name="search_accounts",
        description=(
            "Search the chart of accounts by name, type, classification or active "
            "state. Filters are combined with AND; with no filters this returns the "
            "whole chart of accounts, which is the usual way to find the account Id "
            "another action needs."
        ),
        parameters={
            "name": ParameterDef(
                type="string", description="Exact account name to match"
            ),
            "account_type": ParameterDef(
                type="string",
                description="Account type to match, e.g. Bank or Expense",
            ),
            "account_sub_type": ParameterDef(
                type="string", description="Account sub-type to match, e.g. Savings"
            ),
            "classification": ParameterDef(
                type="string",
                description=(
                    "Ledger classification to match: Asset, Equity, Expense, Liability "
                    "or Revenue"
                ),
            ),
            "active": ParameterDef(
                type="boolean",
                description="Restrict to active (true) or inactive (false) accounts",
            ),
            "max_results": ParameterDef(
                type="integer",
                description=(
                    "Maximum number of accounts to return; QuickBooks caps this at 1000"
                ),
            ),
            "start_position": ParameterDef(
                type="integer",
                description="1-based index of the first row to return, for paging",
            ),
        },
    ),
    ActionDefinition(
        name="get_company_info",
        description=(
            "Read the profile of the connected QuickBooks company — name, addresses, "
            "contact details, country, fiscal year start, and the company preferences "
            "QuickBooks exposes as name/value pairs. Which company is read is fixed by "
            "the credential."
        ),
        parameters={},
    ),
    ActionDefinition(
        name="update_company_info",
        description=(
            "Update the profile of the connected QuickBooks company. Only the fields "
            "supplied change; address parts are sent together, so supply every part of "
            "the company address you want to keep whenever you change any of them."
        ),
        parameters={
            "company_name": ParameterDef(
                type="string", description="Trading name of the company"
            ),
            "legal_name": ParameterDef(
                type="string", description="Registered legal name of the company"
            ),
            "address_line1": ParameterDef(
                type="string", description="First line of the company address"
            ),
            "address_city": ParameterDef(
                type="string", description="City of the company address"
            ),
            "address_state": ParameterDef(
                type="string",
                description="State, province or region of the company address",
            ),
            "address_postal_code": ParameterDef(
                type="string", description="Postal or ZIP code of the company address"
            ),
            "address_country": ParameterDef(
                type="string", description="Country of the company address"
            ),
            "primary_phone": ParameterDef(
                type="string", description="Main telephone number of the company"
            ),
            "email": ParameterDef(
                type="string", description="Contact email address"
            ),
            "web_addr": ParameterDef(type="string", description="Company website URL"),
            "sync_token": ParameterDef(
                type="string",
                description=(
                    "Current SyncToken of the record. Optional — it is fetched "
                    "automatically when omitted, at the cost of one extra request."
                ),
            ),
        },
    ),
    ActionDefinition(
        name="run_query",
        description=(
            "Run a raw QuickBooks query statement and return the matching rows — the "
            "escape hatch for entities and filters the typed search actions do not "
            "cover, and for SELECT COUNT(*) to size a result set. Rows come back as raw "
            "QuickBooks objects because the entity is only known from the statement."
        ),
        parameters={
            "query": ParameterDef(
                type="string",
                description=(
                    "A QuickBooks query statement, e.g. SELECT * FROM Invoice WHERE "
                    "TotalAmt > '100'. This is QuickBooks' own SQL-like language, not "
                    "SQL: one entity per statement, no JOINs, no sub-selects, and the "
                    "only SELECT lists allowed are *, COUNT(*) and explicit field "
                    "names. Filter with WHERE (clauses are AND-ed; OR is unsupported), "
                    "sort with ORDERBY, and page with STARTPOSITION and MAXRESULTS "
                    "after the WHERE clause."
                ),
                required=True,
            ),
        },
    ),
    ActionDefinition(
        name="get_balance_sheet_report",
        description=(
            "Run the Balance Sheet report — assets, liabilities and equity as of a "
            "date. Returns a header, a column definition and a tree of rows where a row "
            "may nest further rows for its section."
        ),
        parameters={
            "start_date": ParameterDef(
                type="string",
                description="Start of the reporting period as YYYY-MM-DD",
            ),
            "end_date": ParameterDef(
                type="string",
                description=(
                    "End of the reporting period as YYYY-MM-DD; the balance sheet is "
                    "drawn as of this date"
                ),
            ),
            "date_macro": ParameterDef(
                type="string",
                description=(
                    "Named date range instead of explicit dates, e.g. This "
                    "Month-to-date, Last Fiscal Year, This Fiscal Quarter"
                ),
            ),
            "accounting_method": ParameterDef(
                type="string",
                description="Cash or Accrual; defaults to the company setting",
            ),
            "summarize_column_by": ParameterDef(
                type="string",
                description=(
                    "How to group the columns: Total, Month, Week, Days, Quarter, Year, "
                    "Customers, Vendors, Classes, Departments, Employees or "
                    "ProductsAndServices"
                ),
            ),
            "customer_ids": ParameterDef(
                type="array", description="Restrict the report to these customer Ids"
            ),
            "vendor_ids": ParameterDef(
                type="array", description="Restrict the report to these vendor Ids"
            ),
            "department_ids": ParameterDef(
                type="array",
                description="Restrict the report to these department (location) Ids",
            ),
            "class_ids": ParameterDef(
                type="array", description="Restrict the report to these class Ids"
            ),
            "item_ids": ParameterDef(
                type="array", description="Restrict the report to these item Ids"
            ),
            "sort_order": ParameterDef(
                type="string",
                description="Sort direction for report rows: ascend or descend",
            ),
        },
    ),
    ActionDefinition(
        name="get_profit_and_loss_report",
        description=(
            "Run the Profit and Loss report — income, expenses and net income over a "
            "period. The rows form a tree of sections (Income, Cost of Goods Sold, "
            "Expenses, Net Income) and each leaf row's ColData lines up with the "
            "returned columns."
        ),
        parameters={
            "start_date": ParameterDef(
                type="string",
                description="Start of the reporting period as YYYY-MM-DD",
            ),
            "end_date": ParameterDef(
                type="string", description="End of the reporting period as YYYY-MM-DD"
            ),
            "date_macro": ParameterDef(
                type="string",
                description=(
                    "Named date range instead of explicit dates, e.g. This "
                    "Month-to-date or Last Fiscal Year"
                ),
            ),
            "accounting_method": ParameterDef(
                type="string",
                description="Cash or Accrual; defaults to the company setting",
            ),
            "summarize_column_by": ParameterDef(
                type="string",
                description=(
                    "How to group the columns: Total, Month, Week, Days, Quarter, Year, "
                    "Customers, Vendors, Classes, Departments, Employees or "
                    "ProductsAndServices"
                ),
            ),
            "customer_ids": ParameterDef(
                type="array", description="Restrict the report to these customer Ids"
            ),
            "vendor_ids": ParameterDef(
                type="array", description="Restrict the report to these vendor Ids"
            ),
            "item_ids": ParameterDef(
                type="array", description="Restrict the report to these item Ids"
            ),
            "department_ids": ParameterDef(
                type="array",
                description="Restrict the report to these department (location) Ids",
            ),
            "class_ids": ParameterDef(
                type="array", description="Restrict the report to these class Ids"
            ),
            "account_ids": ParameterDef(
                type="array", description="Restrict the report to these account Ids"
            ),
            "employee_ids": ParameterDef(
                type="array", description="Restrict the report to these employee Ids"
            ),
            "payment_method": ParameterDef(
                type="string",
                description=(
                    "Restrict the report to one payment method, e.g. Cash, Check, Visa, "
                    "MasterCard, American Express, Discover"
                ),
            ),
        },
    ),
    ActionDefinition(
        name="get_trial_balance_report",
        description=(
            "Run the Trial Balance report — debit and credit totals per account. Use it "
            "to confirm the ledger balances before closing a period: the debit and "
            "credit columns of the total row must agree."
        ),
        parameters={
            "start_date": ParameterDef(
                type="string",
                description="Start of the reporting period as YYYY-MM-DD",
            ),
            "end_date": ParameterDef(
                type="string", description="End of the reporting period as YYYY-MM-DD"
            ),
            "accounting_method": ParameterDef(
                type="string",
                description="Cash or Accrual; defaults to the company setting",
            ),
        },
    ),
    ActionDefinition(
        name="get_cash_flow_report",
        description=(
            "Run the Statement of Cash Flows report — cash movement split into "
            "operating, investing and financing activities over the requested period."
        ),
        parameters={
            "start_date": ParameterDef(
                type="string",
                description="Start of the reporting period as YYYY-MM-DD",
            ),
            "end_date": ParameterDef(
                type="string", description="End of the reporting period as YYYY-MM-DD"
            ),
            "date_macro": ParameterDef(
                type="string",
                description=(
                    "Named date range instead of explicit dates, e.g. This "
                    "Month-to-date or Last Fiscal Year"
                ),
            ),
            "summarize_column_by": ParameterDef(
                type="string",
                description=(
                    "How to group the columns: Total, Month, Week, Days, Quarter, Year, "
                    "Customers, Vendors, Classes, Departments, Employees or "
                    "ProductsAndServices"
                ),
            ),
            "customer_ids": ParameterDef(
                type="array", description="Restrict the report to these customer Ids"
            ),
            "vendor_ids": ParameterDef(
                type="array", description="Restrict the report to these vendor Ids"
            ),
            "department_ids": ParameterDef(
                type="array",
                description="Restrict the report to these department (location) Ids",
            ),
            "class_ids": ParameterDef(
                type="array", description="Restrict the report to these class Ids"
            ),
            "item_ids": ParameterDef(
                type="array", description="Restrict the report to these item Ids"
            ),
            "sort_order": ParameterDef(
                type="string",
                description="Sort direction for report rows: ascend or descend",
            ),
        },
    ),
    ActionDefinition(
        name="get_customer_balance_report",
        description=(
            "Run the Customer Balance report — the accounts-receivable view, with one "
            "row per customer showing how much they still owe as of the report date."
        ),
        parameters={
            "report_date": ParameterDef(
                type="string",
                description=(
                    "Date the balances are drawn as of, as YYYY-MM-DD; defaults to today"
                ),
            ),
            "customer_ids": ParameterDef(
                type="array", description="Restrict the report to these customer Ids"
            ),
            "summarize_column_by": ParameterDef(
                type="string",
                description="How to group the columns: Total, Month, Week or Days",
            ),
        },
    ),
    ActionDefinition(
        name="get_vendor_balance_report",
        description=(
            "Run the Vendor Balance report — the accounts-payable counterpart of the "
            "customer balance report, with one row per vendor showing how much is still "
            "owed to them as of the report date."
        ),
        parameters={
            "report_date": ParameterDef(
                type="string",
                description=(
                    "Date the balances are drawn as of, as YYYY-MM-DD; defaults to today"
                ),
            ),
            "vendor_ids": ParameterDef(
                type="array", description="Restrict the report to these vendor Ids"
            ),
            "summarize_column_by": ParameterDef(
                type="string",
                description="How to group the columns: Total, Month, Week or Days",
            ),
        },
    ),
    ActionDefinition(
        name="get_vendor_expenses_report",
        description=(
            "Run the Expenses by Vendor report — total spend per vendor over a period. "
            "Answers who the company spent the most with, which the vendor balance "
            "report cannot: this totals what was spent, not what is still outstanding."
        ),
        parameters={
            "start_date": ParameterDef(
                type="string",
                description="Start of the reporting period as YYYY-MM-DD",
            ),
            "end_date": ParameterDef(
                type="string", description="End of the reporting period as YYYY-MM-DD"
            ),
            "accounting_method": ParameterDef(
                type="string",
                description="Cash or Accrual; defaults to the company setting",
            ),
            "vendor_ids": ParameterDef(
                type="array", description="Restrict the report to these vendor Ids"
            ),
            "summarize_column_by": ParameterDef(
                type="string",
                description="How to group the columns: Total, Month, Week or Days",
            ),
        },
    ),
    ActionDefinition(
        name="get_ap_aging_report",
        description=(
            "Run the A/P Ageing Summary report — unpaid bills bucketed by age, one row "
            "per vendor with the outstanding amount split across ageing buckets "
            "(current, 1-30 days, 31-60 days, ...) so overdue payables stand out."
        ),
        parameters={
            "report_date": ParameterDef(
                type="string",
                description=(
                    "Date the ageing is calculated from, as YYYY-MM-DD; defaults to "
                    "today"
                ),
            ),
            "accounting_method": ParameterDef(
                type="string",
                description="Cash or Accrual; defaults to the company setting",
            ),
            "vendor_ids": ParameterDef(
                type="array", description="Restrict the report to these vendor Ids"
            ),
            "num_periods": ParameterDef(
                type="integer", description="Number of ageing buckets to show"
            ),
            "aging_period": ParameterDef(
                type="integer", description="Length of each ageing bucket in days"
            ),
            "past_due": ParameterDef(
                type="integer",
                description="Only include bills at least this many days past due",
            ),
        },
    ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect a QuickBooks Online company",
            setup_instructions=[
                "Sign in at https://developer.intuit.com and open My Apps",
                "Create an app (or open an existing one) and enable the "
                "Accounting scope",
                "Under Keys & credentials, add your ModuleX OAuth callback to "
                "the Redirect URIs",
                "Copy the Client ID and Client Secret into the fields below",
                "Connect below, then pick the company you want to automate — "
                "its Company ID appears in QuickBooks under Settings -> "
                "Account and settings -> Billing & subscription",
                "Paste that Company ID below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="QUICKBOOKS_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Client ID of your QuickBooks app",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://developer.intuit.com/app/developer/myapps",
                ),
                EnvVar(
                    name="QUICKBOOKS_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Client Secret of your QuickBooks app",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://developer.intuit.com/app/developer/myapps",
                ),
                EnvVar(
                    name="QUICKBOOKS_REALM_ID",
                    display_name="Company ID",
                    description=(
                        "ID of the QuickBooks company (realm) to work in. Found "
                        "under Settings -> Account and settings -> Billing & "
                        "subscription, and returned as realmId on the OAuth "
                        "callback."
                    ),
                    required=True,
                    sensitive=False,
                    # Per-credential user input: every company has its own ID,
                    # so it cannot be a server global. The runtime persists the
                    # user-entered value into auth_data at credential creation;
                    # tools.py reads it as auth_data["realm_id"].
                    only_for_custom=False,
                    inject_into_auth_data=True,
                    sample_format="9341454816484523",
                    about_url="https://developer.intuit.com/app/developer/qbo/docs/develop",
                ),
                EnvVar(
                    name="QUICKBOOKS_ENVIRONMENT",
                    display_name="Environment",
                    description=(
                        "Which QuickBooks API to call: 'production' for a real "
                        "company, or 'sandbox' for a developer test company. "
                        "Defaults to production."
                    ),
                    required=False,
                    sensitive=False,
                    only_for_custom=False,
                    inject_into_auth_data=True,
                    sample_format="production",
                ),
            ],
            oauth_config=OAuthConfig(
                # Both URLs come from the vendor's OIDC discovery document at
                # https://developer.api.intuit.com/.well-known/openid_configuration/
                auth_url="https://appcenter.intuit.com/connect/oauth2",
                token_url="https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
                scopes=["com.intuit.quickbooks.accounting"],
                token_auth_method="basic",
            ),
            test_endpoint=TestEndpoint(
                url=(
                    "https://quickbooks.api.intuit.com/v3/company/{realm_id}"
                    "/companyinfo/{realm_id}?minorversion=75"
                ),
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                    "Accept": "application/json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["CompanyInfo.CompanyName"],
                ),
                cost_level="free",
                description=(
                    "Reads the company profile to prove the token and company "
                    "ID work together"
                ),
            ),
        ),
    ],
)

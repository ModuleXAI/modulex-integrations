# QuickBooks Online

Run a QuickBooks Online company from an agent — raise and send invoices and
estimates, record sales receipts and credit memos, manage customers, vendors,
items and the chart of accounts, enter bills, purchases and payments on both
sides of the ledger, run the standard financial reports, and query any entity
directly via the QuickBooks Online Accounting API v3
(`quickbooks.api.intuit.com/v3`).

## Authentication

### OAuth 2.0

- QuickBooks Online supports **no** static credential — no API key, no basic
  token, and no `client_credentials` grant for the accounting API. OAuth 2.0
  with user authorization is the only way in
  ([docs](https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization)).
- Create an app at <https://developer.intuit.com>, enable the **Accounting**
  scope, and add your ModuleX callback under **Keys & credentials → Redirect
  URIs**.
- Env vars: `QUICKBOOKS_OAUTH2_CLIENT_ID`, `QUICKBOOKS_OAUTH2_CLIENT_SECRET`
  (both app-level), plus `QUICKBOOKS_REALM_ID` and the optional
  `QUICKBOOKS_ENVIRONMENT` (per credential).
- Authorize at `https://appcenter.intuit.com/connect/oauth2`; exchange at
  `https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer` with the client
  credentials in an **HTTP Basic** header. Scope:
  `com.intuit.quickbooks.accounting`.
- Access tokens last about an hour. Refresh tokens last about 100 days and
  **rotate on every use** — the newest one must be stored each time, or the
  connection dies.
- **`QUICKBOOKS_REALM_ID` is not optional.** Every endpoint is scoped to one
  company, so the company ID is stored on the credential and injected into
  `auth_data`; no action takes it as a parameter. It also arrives as the
  `realmId` query parameter on the OAuth callback.
- `QUICKBOOKS_ENVIRONMENT` selects between the production and sandbox hosts
  and defaults to `production`. It is resolved through a fixed map, so an
  unrecognised value falls back to production rather than being used to build
  a URL.
- The credential is validated by reading the company profile, which proves
  the token and the company ID work together.

## Tools

### Invoices

| name | description | required params |
| --- | --- | --- |
| `create_invoice` | Create an invoice billing a customer for one or more items. Records money the customer now owes; use create_sales_receipt instead when the sale was already paid for. | `customer_id`, `line_items` |
| `get_invoice` | Read one invoice by its ID, including its line items and balance. | `invoice_id` |
| `update_invoice` | Change fields on an existing invoice, leaving the rest untouched. This is a sparse update: only the values supplied here change. To email the invoice use send_invoice; to cancel it use void_invoice. | `invoice_id` |
| `delete_invoice` | Delete an invoice permanently. The transaction disappears from the books entirely; when the invoice must stay on record for the audit trail — the usual accounting choice — use void_invoice instead. | `invoice_id` |
| `search_invoices` | Find invoices by customer, number, date range or unpaid status. All supplied filters are combined with AND; with none at all this lists the company's invoices. | — |

### Customers

| name | description | required params |
| --- | --- | --- |
| `create_customer` | Add a customer to the company. Supply either a display name or at least one name part — QuickBooks builds the display name from the parts when it is omitted, and rejects a display name already taken by a customer, vendor or employee. | — |
| `get_customer` | Read one customer by ID, including contact details and balance. | `customer_id` |
| `update_customer` | Change fields on an existing customer, leaving the rest untouched. This is a sparse update: only the values supplied here change. | `customer_id` |
| `delete_customer` | Deactivate a customer. QuickBooks does not permit deleting customers, so this marks the record inactive; its history is preserved and update_customer with active=true reverses it. This is also what deleting a customer does in the QuickBooks UI. | `customer_id` |
| `search_customers` | Find customers by name, company or active state. All supplied filters are combined with AND; with none at all this lists the company's customers — a good way to resolve a name to the ID the invoice actions need. | — |

### Vendors

| name | description | required params |
| --- | --- | --- |
| `create_vendor` | Create a vendor: a supplier the company buys from and pays bills to. Needs a display name, or a first/last name for QuickBooks to build one from. | — |
| `get_vendor` | Read one vendor by ID, including its open balance, contact details and billing address. | `vendor_id` |
| `update_vendor` | Change a vendor's details. Only the fields supplied are altered; everything else is left as it is. Set active=false to retire the vendor or true to restore it. | `vendor_id` |
| `delete_vendor` | Deactivate a vendor. QuickBooks does not permit deleting vendors, so this marks the record inactive; its history is preserved and update_vendor with active=true reverses it. | `vendor_id` |
| `search_vendors` | Find vendors by name or active state. Omit every filter to list all vendors. | — |

### Items (products & services)

| name | description | required params |
| --- | --- | --- |
| `create_item` | Create a product or service in QuickBooks. Every item needs a unique name and a type; a Service or NonInventory item needs an income account, and an Inventory item additionally needs an expense account, an asset account, an opening quantity and an inventory start date. | `name`, `item_type` |
| `get_item` | Read one product or service by its QuickBooks Id. | `item_id` |
| `update_item` | Update a product or service, changing only the fields supplied. Omitted fields keep their current values, but QuickBooks treats the name as mandatory on an item write, so pass the item's current name alongside the change. | `item_id` |
| `delete_item` | Remove a product or service from use by deactivating it. QuickBooks does not permit deleting an item because historical transactions reference it, so the item is marked inactive: it disappears from lists and pickers while past invoices, bills and reports stay intact. Reactivate it with update_item and active=true. | `item_id` |
| `search_items` | Search products and services by name, SKU, type or active state. Filters are combined with AND; with no filters this returns the whole products-and-services list, one page at a time. | — |

### Chart of accounts

| name | description | required params |
| --- | --- | --- |
| `create_account` | Add an account to the QuickBooks chart of accounts. Only the name is strictly required, but supplying account_type and account_sub_type is strongly recommended — otherwise QuickBooks picks the classification. | `name` |
| `get_account` | Read one chart-of-accounts entry by its QuickBooks Id. | `account_id` |
| `update_account` | Update a chart-of-accounts entry, or deactivate it with active=false. This is also how an account is removed: QuickBooks does not permit deleting an account because the ledger history points at it, so setting active=false hides it from the chart of accounts while posted transactions stay intact. | `account_id` |
| `search_accounts` | Search the chart of accounts by name, type, classification or active state. Filters are combined with AND; with no filters this returns the whole chart of accounts, which is the usual way to find the account Id another action needs. | — |

### Estimates

| name | description | required params |
| --- | --- | --- |
| `create_estimate` | Create an estimate — a quote or proposal for a customer. An estimate is non-posting: it does not affect the books until it is converted into an invoice. | `customer_id`, `line_items` |
| `get_estimate` | Read one estimate by its ID, including its line items and status. | `estimate_id` |
| `update_estimate` | Change fields on an existing estimate, leaving the rest untouched. This is a sparse update: only the values supplied here change. Marking a quote as won is txn_status=Accepted. | `estimate_id` |
| `delete_estimate` | Delete an estimate permanently. To keep the quote on record but take it out of play, set its status to Closed or Rejected with update_estimate instead. | `estimate_id` |
| `search_estimates` | Find estimates by customer, number, status or date range. All supplied filters are combined with AND; with none at all this lists the company's estimates. | — |

### Sales receipts

| name | description | required params |
| --- | --- | --- |
| `create_sales_receipt` | Record a sale that was paid for at the same time. Use this for point-of-sale style transactions; when the customer will pay later, create an invoice instead. | `line_items` |
| `get_sales_receipt` | Read one sales receipt by its ID, including its line items. | `sales_receipt_id` |
| `update_sales_receipt` | Change fields on an existing sales receipt, leaving the rest alone. This is a sparse update: only the values supplied here change. | `sales_receipt_id` |
| `delete_sales_receipt` | Delete a sales receipt permanently. Both the sale and the payment it recorded come off the books. | `sales_receipt_id` |
| `search_sales_receipts` | Find sales receipts by customer, number or date range. All supplied filters are combined with AND; with none at all this lists the company's sales receipts. | — |

### Credit memos

| name | description | required params |
| --- | --- | --- |
| `create_credit_memo` | Issue a credit memo to a customer. Records credit the customer can apply against an open invoice — the usual answer to a return, an overcharge or a goodwill discount. | `customer_id`, `line_items` |
| `get_credit_memo` | Read one credit memo by ID, including how much credit is left. | `credit_memo_id` |
| `update_credit_memo` | Change fields on an existing credit memo, leaving the rest alone. This is a sparse update: only the values supplied here change. | `credit_memo_id` |
| `delete_credit_memo` | Delete a credit memo permanently. Any credit it had already applied to an invoice is released, so the invoice balance goes back up. | `credit_memo_id` |
| `search_credit_memos` | Find credit memos by customer, number or date range. All supplied filters are combined with AND; with none at all this lists the company's credit memos. | — |

### Bills

| name | description | required params |
| --- | --- | --- |
| `create_bill` | Record a bill: money a vendor has invoiced that the company owes but has not yet paid. If the expense was paid on the spot, use create_purchase instead. | `vendor_id`, `lines` |
| `get_bill` | Read one bill by ID, including its expense lines and the balance still unpaid. | `bill_id` |
| `update_bill` | Change a bill. Anything not mentioned keeps its current value: QuickBooks rewrites a bill wholesale rather than patching it, so this action reads the bill first and lays the supplied changes over it. Omitting lines leaves the existing ones untouched. | `bill_id` |
| `delete_bill` | Delete a bill. Any bill payment already applied to it must be unlinked first, or QuickBooks refuses the delete. | `bill_id` |
| `search_bills` | Find bills by vendor, date, due date or unpaid state. Use unpaid_only to answer 'what do we owe?'. | — |

### Bill payments

| name | description | required params |
| --- | --- | --- |
| `create_bill_payment` | Pay a vendor: record money going OUT of the company to settle one or more bills. This is the accounts-payable side. To record money coming IN from a customer against an invoice, use create_payment. | `vendor_id`, `total_amount`, `pay_type` |
| `get_bill_payment` | Read one payment the company made to a vendor, including which bills it settled and the account it was paid from. | `bill_payment_id` |
| `update_bill_payment` | Change a payment made to a vendor. Only the fields supplied are altered; supplying applied_bills replaces the whole set of settled bills. | `bill_payment_id` |
| `delete_bill_payment` | Delete a payment made to a vendor, restoring the outstanding balance on the bills it had settled. | `bill_payment_id` |
| `search_bill_payments` | Find payments the company made to vendors, by vendor, reference or date. This searches money OUT; for payments received from customers use search_payments. | — |

### Customer payments

| name | description | required params |
| --- | --- | --- |
| `create_payment` | Receive a customer payment: record money coming IN and apply it to the customer's invoices. This is the accounts-receivable side. To record money going OUT to a vendor against a bill, use create_bill_payment. | `customer_id`, `total_amount` |
| `get_payment` | Read one payment received from a customer, including which invoices it was applied to and how much is still unapplied. | `payment_id` |
| `update_payment` | Change a payment received from a customer. Only the fields supplied are altered; QuickBooks rewrites payment lines all-or-nothing, so send every applied invoice whenever you send any. | `payment_id` |
| `delete_payment` | Delete a payment received from a customer, reopening the balance on any invoices it had paid. | `payment_id` |
| `search_payments` | Find payments received from customers, by customer, reference or date. This searches money IN; for payments the company made to vendors use search_bill_payments. | — |

### Purchases / expenses

| name | description | required params |
| --- | --- | --- |
| `create_purchase` | Record an expense that was already paid, by cash, cheque or credit card. Use this when the money has already left the account; for a vendor invoice that is still owed, use create_bill. | `account_id`, `payment_type`, `lines` |
| `get_purchase` | Read one purchase (an already-paid expense) by ID, including its expense lines and the account it was paid from. | `purchase_id` |
| `update_purchase` | Change a purchase (expense). Only the fields supplied are altered, except lines: sending any line replaces the whole set. | `purchase_id` |
| `delete_purchase` | Delete a purchase (expense), reversing its effect on the account it was paid from. | `purchase_id` |
| `search_purchases` | Find purchases (already-paid expenses) by date, reference or amount. | — |

### Company

| name | description | required params |
| --- | --- | --- |
| `get_company_info` | Read the profile of the connected QuickBooks company — name, addresses, contact details, country, fiscal year start, and the company preferences QuickBooks exposes as name/value pairs. Which company is read is fixed by the credential. | — |
| `update_company_info` | Update the profile of the connected QuickBooks company. Only the fields supplied change; address parts are sent together, so supply every part of the company address you want to keep whenever you change any of them. | — |

### Delivery

| name | description | required params |
| --- | --- | --- |
| `send_invoice` | Email an invoice to the customer. QuickBooks sends the mail itself and marks the invoice EmailSent. | `invoice_id` |
| `send_estimate` | Email an estimate to the customer. QuickBooks sends the mail itself and marks the estimate EmailSent. | `estimate_id` |
| `void_invoice` | Void an invoice, keeping the record on the books. The invoice stays in QuickBooks with its number and date intact, but its amount drops to zero and it is marked as voided — so the audit trail survives. This is the safe way to cancel a billing mistake; delete_invoice erases the transaction instead. | `invoice_id` |

### Query

| name | description | required params |
| --- | --- | --- |
| `run_query` | Run a raw QuickBooks query statement and return the matching rows — the escape hatch for entities and filters the typed search actions do not cover, and for SELECT COUNT(*) to size a result set. Rows come back as raw QuickBooks objects because the entity is only known from the statement. | `query` |

### Reports

| name | description | required params |
| --- | --- | --- |
| `get_balance_sheet_report` | Run the Balance Sheet report — assets, liabilities and equity as of a date. Returns a header, a column definition and a tree of rows where a row may nest further rows for its section. | — |
| `get_profit_and_loss_report` | Run the Profit and Loss report — income, expenses and net income over a period. The rows form a tree of sections (Income, Cost of Goods Sold, Expenses, Net Income) and each leaf row's ColData lines up with the returned columns. | — |
| `get_trial_balance_report` | Run the Trial Balance report — debit and credit totals per account. Use it to confirm the ledger balances before closing a period: the debit and credit columns of the total row must agree. | — |
| `get_cash_flow_report` | Run the Statement of Cash Flows report — cash movement split into operating, investing and financing activities over the requested period. | — |
| `get_customer_balance_report` | Run the Customer Balance report — the accounts-receivable view, with one row per customer showing how much they still owe as of the report date. | — |
| `get_vendor_balance_report` | Run the Vendor Balance report — the accounts-payable counterpart of the customer balance report, with one row per vendor showing how much is still owed to them as of the report date. | — |
| `get_vendor_expenses_report` | Run the Expenses by Vendor report — total spend per vendor over a period. Answers who the company spent the most with, which the vendor balance report cannot: this totals what was spent, not what is still outstanding. | — |
| `get_ap_aging_report` | Run the A/P Ageing Summary report — unpaid bills bucketed by age, one row per vendor with the outstanding amount split across ageing buckets (current, 1-30 days, 31-60 days, ...) so overdue payables stand out. | — |

Every tool additionally takes `auth_type` and `auth_data`, which the runtime
fills in from the resolved credential.

Start from `search_customers` or `search_items` to find the IDs an invoice
needs, then `create_invoice`. For bookkeeping questions, the report actions
answer most of them directly; `run_query` is the escape hatch for anything
the typed actions do not cover.

## Limits & Quotas

- **A 200 response can still be a failure.** QuickBooks reports validation
  problems with HTTP 200 and a `Fault.Error[]` array in the body. These tools
  treat a non-empty fault as an error and surface Intuit's `Message`,
  `Detail` and `code` — quote that code when contacting support.
- **Writes use optimistic concurrency.** Every update and delete must carry
  the record's current `SyncToken`. Each such action takes an optional
  `sync_token`; when omitted, the record is read first to fetch it, costing
  one extra request. Supplying it explicitly is faster and closes the small
  race window between the read and the write.
- **Updates are sparse.** Only the fields you supply change. This is
  deliberate — a non-sparse update blanks every field you leave out.
- **Accounts cannot be deleted.** QuickBooks only allows deactivating them:
  call `update_account` with `active=false`. There is no `delete_account`.
- **Searches are a SQL-like dialect, not SQL.** No JOINs, no arbitrary
  projections; paging is `MAXRESULTS` / `STARTPOSITION`, and a search that
  matches nothing returns an empty result set rather than an error. Literals
  supplied to the typed `search_*` actions are escaped automatically.
- **Rate limits** (per app, per company): roughly 500 requests per minute,
  with a concurrency ceiling of 10 in flight. Sandbox limits are lower.
- **`minorversion` is pinned to 75.** The API is versioned through this query
  parameter; raising it can change response shapes, so it is a deliberate
  upgrade rather than a default that drifts.
- **Binary payloads are out of scope.** Fetching an invoice as a PDF returns
  `application/pdf`, and attaching a file is a `multipart/form-data` upload —
  neither can be represented as a JSON tool result.
- **Error model**: transport failures, non-2xx responses, faults inside a
  200, and unparseable bodies all fold into `success=False` + `error` rather
  than raising.

## Maintainer

ModuleX core team.

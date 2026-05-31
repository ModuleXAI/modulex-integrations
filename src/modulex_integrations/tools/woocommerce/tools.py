"""WooCommerce LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.woocommerce.outputs import (
    AddOrderNoteOutput,
    CreateCustomerOutput,
    CreateOrderOutput,
    CreateProductOutput,
    CreateRefundOutput,
    CustomerSummary,
    DeleteOrderOutput,
    GetCustomerOutput,
    GetOrderNoteOutput,
    GetOrderOutput,
    GetProductOutput,
    ListOrderNotesOutput,
    ListOrdersOutput,
    ListPaymentMethodOptionsOutput,
    ListProductsOutput,
    OrderNoteSummary,
    OrderSummary,
    PaymentMethodSummary,
    ProductSummary,
    RefundSummary,
    SearchCustomersOutput,
    UpdateOrderStatusOutput,
    UpdateProductOutput,
)

__all__ = [
    "add_order_note",
    "create_customer",
    "create_order",
    "create_product",
    "create_refund",
    "delete_order",
    "get_customer",
    "get_order",
    "get_order_note",
    "get_product",
    "list_order_notes",
    "list_orders",
    "list_payment_method_options",
    "list_products",
    "search_customers",
    "update_order_status",
    "update_product",
]

_TIMEOUT = 30.0


def _build_base_url(auth_data: dict[str, Any]) -> str:
    store_url = auth_data.get("store_url", "").rstrip("/")
    return f"{store_url}/wp-json/wc/v3"


def _get_auth(auth_data: dict[str, Any]) -> tuple[str, str]:
    return (
        auth_data.get("consumer_key", ""),
        auth_data.get("consumer_secret", ""),
    )


def _validate_credentials(auth_data: dict[str, Any]) -> str | None:
    store_url = auth_data.get("store_url", "")
    consumer_key = auth_data.get("consumer_key", "")
    consumer_secret = auth_data.get("consumer_secret", "")
    if not store_url or not store_url.strip():
        return "Store URL is empty. Please configure a valid WooCommerce store URL."
    if not consumer_key or not consumer_key.strip():
        return "Consumer key is empty. Please configure valid WooCommerce REST API credentials."
    if not consumer_secret or not consumer_secret.strip():
        return "Consumer secret is empty. Please configure valid WooCommerce REST API credentials."
    return None


def _parse_order(data: dict[str, Any]) -> OrderSummary:
    return OrderSummary(
        id=data.get("id"),
        number=str(data.get("number", "")),
        status=data.get("status"),
        total=data.get("total"),
        currency=data.get("currency"),
        customer_id=data.get("customer_id"),
        payment_method=data.get("payment_method"),
        date_created=data.get("date_created"),
        date_modified=data.get("date_modified"),
        line_items=data.get("line_items") or [],
        billing=data.get("billing"),
        shipping=data.get("shipping"),
    )


def _parse_product(data: dict[str, Any]) -> ProductSummary:
    return ProductSummary(
        id=data.get("id"),
        name=data.get("name"),
        slug=data.get("slug"),
        type=data.get("type"),
        status=data.get("status"),
        regular_price=data.get("regular_price"),
        sale_price=data.get("sale_price"),
        price=data.get("price"),
        description=data.get("description"),
        categories=data.get("categories") or [],
        images=data.get("images") or [],
        date_created=data.get("date_created"),
    )


def _parse_customer(data: dict[str, Any]) -> CustomerSummary:
    return CustomerSummary(
        id=data.get("id"),
        email=data.get("email"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        username=data.get("username"),
        role=data.get("role"),
        date_created=data.get("date_created"),
        billing=data.get("billing"),
        shipping=data.get("shipping"),
        is_paying_customer=data.get("is_paying_customer"),
    )


def _parse_order_note(data: dict[str, Any]) -> OrderNoteSummary:
    return OrderNoteSummary(
        id=data.get("id"),
        author=data.get("author"),
        date_created=data.get("date_created"),
        note=data.get("note"),
        customer_note=data.get("customer_note"),
    )


# --- Input schemas --------------------------------------------------------


class CreateOrderInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    status: str | None = Field(default="pending", description="Order status. Options: pending, processing, on-hold, completed, cancelled, refunded, failed, trash")
    customer_id: int | None = Field(default=None, description="User ID who owns the order. 0 for guests")
    payment_method: str | None = Field(default=None, description="Payment method ID (e.g. bacs, cheque, cod, paypal)")
    line_items: list[dict[str, Any]] | None = Field(default=None, description="Array of line item objects, each with product_id (integer) and quantity (integer)")


class GetOrderInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    order_id: int = Field(description="ID of the order to retrieve")


class ListOrdersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    search: str | None = Field(default=None, description="Limit results to those matching a string")
    status: str | None = Field(default="pending", description="Order status filter. Options: pending, processing, on-hold, completed, cancelled, refunded, failed, trash")
    customer: int | None = Field(default=None, description="Filter by customer user ID. 0 for guests")
    after: str | None = Field(default=None, description="Limit to orders created after this ISO8601 date")
    before: str | None = Field(default=None, description="Limit to orders created before this ISO8601 date")
    max_results: int = Field(default=20, description="Maximum number of results to return")


class DeleteOrderInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    order_id: int = Field(description="ID of the order to delete")
    force: bool | None = Field(default=None, description="Whether to bypass trash and permanently delete the order")


class UpdateOrderStatusInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    order_id: int = Field(description="ID of the order to update")
    status: str = Field(description="New order status. Options: pending, processing, on-hold, completed, cancelled, refunded, failed, trash")


class CreateProductInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="Name of the product")
    type: str | None = Field(default="simple", description="Product type. Options: simple, grouped, external, variable")
    status: str | None = Field(default="publish", description="Product status. Options: draft, pending, private, publish")
    regular_price: str | None = Field(default=None, description="Product regular price")
    sale_price: str | None = Field(default=None, description="Product sale price")
    description: str | None = Field(default=None, description="Product description (HTML allowed)")
    categories: list[int] | None = Field(default=None, description="Array of category IDs to assign the product to")
    image_url: str | None = Field(default=None, description="URL of an image to add to the product")


class UpdateProductInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    product_id: int = Field(description="ID of the product to update")
    name: str | None = Field(default=None, description="New name for the product")
    type: str | None = Field(default=None, description="Product type. Options: simple, grouped, external, variable")
    status: str | None = Field(default=None, description="Product status. Options: draft, pending, private, publish")
    regular_price: str | None = Field(default=None, description="Product regular price")
    sale_price: str | None = Field(default=None, description="Product sale price")
    description: str | None = Field(default=None, description="Product description (HTML allowed)")
    categories: list[int] | None = Field(default=None, description="Array of category IDs to assign the product to")
    image_url: str | None = Field(default=None, description="URL of an image to add to the product")


class GetProductInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    product_id: int = Field(description="ID of the product to retrieve")


class ListProductsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    search: str | None = Field(default=None, description="Limit results to those matching a string")
    status: str | None = Field(default="publish", description="Product status filter. Options: draft, pending, private, publish")
    type: str | None = Field(default="simple", description="Product type filter. Options: simple, grouped, external, variable")
    after: str | None = Field(default=None, description="Limit to products created after this ISO8601 date")
    before: str | None = Field(default=None, description="Limit to products created before this ISO8601 date")
    max_results: int = Field(default=20, description="Maximum number of results to return")


class SearchCustomersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    search: str | None = Field(default=None, description="Limit results to those matching a string")
    email: str | None = Field(default=None, description="Filter by exact customer email address")
    role: str | None = Field(default="customer", description="Filter by role. Options: all, administrator, editor, author, contributor, subscriber, customer")
    max_results: int = Field(default=20, description="Maximum number of results to return")


class GetCustomerInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    customer_id: int = Field(description="ID of the customer to retrieve")


class CreateCustomerInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    email: str = Field(description="Customer email address")
    first_name: str | None = Field(default=None, description="Customer first name")
    last_name: str | None = Field(default=None, description="Customer last name")
    username: str | None = Field(default=None, description="Customer login username")
    password: str | None = Field(default=None, description="Customer password")
    is_paying_customer: bool | None = Field(default=None, description="Whether the customer is a paying customer")


class AddOrderNoteInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    order_id: int = Field(description="ID of the order to add a note to")
    note: str = Field(description="Content of the order note")


class GetOrderNoteInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    order_id: int = Field(description="ID of the order")
    note_id: int = Field(description="ID of the order note")


class ListOrderNotesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    order_id: int = Field(description="ID of the order")
    type: str | None = Field(default="any", description="Filter by note type. Options: any, customer, internal")


class CreateRefundInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    order_id: int = Field(description="ID of the order to refund")
    amount: str | None = Field(default=None, description="Refund amount. If not specified, calculated from line items")
    reason: str | None = Field(default=None, description="Reason for the refund")
    api_refund: bool | None = Field(default=None, description="When true, the payment gateway API generates the refund")
    line_items: list[dict[str, Any]] | None = Field(default=None, description="Array of line item refund objects with id, refund_total, and optionally refund_tax")


class ListPaymentMethodOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateOrderInput)
@serialize_pydantic_return
async def create_order(
    auth_type: str,
    auth_data: dict[str, Any],
    status: str | None = "pending",
    customer_id: int | None = None,
    payment_method: str | None = None,
    line_items: list[dict[str, Any]] | None = None,
) -> CreateOrderOutput:
    """Create a new order in the WooCommerce store."""
    err = _validate_credentials(auth_data)
    if err:
        return CreateOrderOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    body: dict[str, Any] = {}
    if status:
        body["status"] = status
    if customer_id is not None:
        body["customer_id"] = customer_id
    if payment_method:
        body["payment_method"] = payment_method
    if line_items:
        body["line_items"] = line_items
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{base_url}/orders",
                auth=auth,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateOrderOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateOrderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateOrderOutput(success=False, error=f"Call failed: {exc}")
    return CreateOrderOutput(success=True, order=_parse_order(data))


@tool(args_schema=GetOrderInput)
@serialize_pydantic_return
async def get_order(
    auth_type: str,
    auth_data: dict[str, Any],
    order_id: int,
) -> GetOrderOutput:
    """Retrieve a specific order by ID."""
    err = _validate_credentials(auth_data)
    if err:
        return GetOrderOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/orders/{order_id}",
                auth=auth,
            )
        if response.status_code != 200:
            return GetOrderOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetOrderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetOrderOutput(success=False, error=f"Call failed: {exc}")
    return GetOrderOutput(success=True, order=_parse_order(data))


@tool(args_schema=ListOrdersInput)
@serialize_pydantic_return
async def list_orders(
    auth_type: str,
    auth_data: dict[str, Any],
    search: str | None = None,
    status: str | None = "pending",
    customer: int | None = None,
    after: str | None = None,
    before: str | None = None,
    max_results: int = 20,
) -> ListOrdersOutput:
    """Retrieve a list of orders with optional filters."""
    err = _validate_credentials(auth_data)
    if err:
        return ListOrdersOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    params: dict[str, Any] = {"per_page": min(max_results, 100)}
    if search:
        params["search"] = search
    if status:
        params["status"] = status
    if customer is not None:
        params["customer"] = customer
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/orders",
                auth=auth,
                params=params,
            )
        if response.status_code != 200:
            return ListOrdersOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListOrdersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListOrdersOutput(success=False, error=f"Call failed: {exc}")
    orders = [_parse_order(o) for o in data]
    return ListOrdersOutput(success=True, orders=orders, total=len(orders))


@tool(args_schema=DeleteOrderInput)
@serialize_pydantic_return
async def delete_order(
    auth_type: str,
    auth_data: dict[str, Any],
    order_id: int,
    force: bool | None = None,
) -> DeleteOrderOutput:
    """Delete an existing order."""
    err = _validate_credentials(auth_data)
    if err:
        return DeleteOrderOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    params: dict[str, Any] = {}
    if force is not None:
        params["force"] = str(force).lower()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{base_url}/orders/{order_id}",
                auth=auth,
                params=params,
            )
        if response.status_code != 200:
            return DeleteOrderOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return DeleteOrderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteOrderOutput(success=False, error=f"Call failed: {exc}")
    return DeleteOrderOutput(success=True, order=_parse_order(data))


@tool(args_schema=UpdateOrderStatusInput)
@serialize_pydantic_return
async def update_order_status(
    auth_type: str,
    auth_data: dict[str, Any],
    order_id: int,
    status: str,
) -> UpdateOrderStatusOutput:
    """Update the status of a specific order."""
    err = _validate_credentials(auth_data)
    if err:
        return UpdateOrderStatusOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{base_url}/orders/{order_id}",
                auth=auth,
                json={"status": status},
            )
        if response.status_code != 200:
            return UpdateOrderStatusOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return UpdateOrderStatusOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateOrderStatusOutput(success=False, error=f"Call failed: {exc}")
    return UpdateOrderStatusOutput(success=True, order=_parse_order(data))


@tool(args_schema=CreateProductInput)
@serialize_pydantic_return
async def create_product(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    type: str | None = "simple",
    status: str | None = "publish",
    regular_price: str | None = None,
    sale_price: str | None = None,
    description: str | None = None,
    categories: list[int] | None = None,
    image_url: str | None = None,
) -> CreateProductOutput:
    """Create a new product in the WooCommerce store."""
    err = _validate_credentials(auth_data)
    if err:
        return CreateProductOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    body: dict[str, Any] = {"name": name}
    if type:
        body["type"] = type
    if status:
        body["status"] = status
    if regular_price:
        body["regular_price"] = regular_price
    if sale_price:
        body["sale_price"] = sale_price
    if description:
        body["description"] = description
    if categories:
        body["categories"] = [{"id": c} for c in categories]
    if image_url:
        body["images"] = [{"src": image_url}]
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{base_url}/products",
                auth=auth,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateProductOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateProductOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateProductOutput(success=False, error=f"Call failed: {exc}")
    return CreateProductOutput(success=True, product=_parse_product(data))


@tool(args_schema=UpdateProductInput)
@serialize_pydantic_return
async def update_product(
    auth_type: str,
    auth_data: dict[str, Any],
    product_id: int,
    name: str | None = None,
    type: str | None = None,
    status: str | None = None,
    regular_price: str | None = None,
    sale_price: str | None = None,
    description: str | None = None,
    categories: list[int] | None = None,
    image_url: str | None = None,
) -> UpdateProductOutput:
    """Update an existing product."""
    err = _validate_credentials(auth_data)
    if err:
        return UpdateProductOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    body: dict[str, Any] = {}
    if name:
        body["name"] = name
    if type:
        body["type"] = type
    if status:
        body["status"] = status
    if regular_price:
        body["regular_price"] = regular_price
    if sale_price:
        body["sale_price"] = sale_price
    if description:
        body["description"] = description
    if categories:
        body["categories"] = [{"id": c} for c in categories]
    if image_url:
        body["images"] = [{"src": image_url}]
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{base_url}/products/{product_id}",
                auth=auth,
                json=body,
            )
        if response.status_code != 200:
            return UpdateProductOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return UpdateProductOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateProductOutput(success=False, error=f"Call failed: {exc}")
    return UpdateProductOutput(success=True, product=_parse_product(data))


@tool(args_schema=GetProductInput)
@serialize_pydantic_return
async def get_product(
    auth_type: str,
    auth_data: dict[str, Any],
    product_id: int,
) -> GetProductOutput:
    """Retrieve a specific product by ID."""
    err = _validate_credentials(auth_data)
    if err:
        return GetProductOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/products/{product_id}",
                auth=auth,
            )
        if response.status_code != 200:
            return GetProductOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetProductOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetProductOutput(success=False, error=f"Call failed: {exc}")
    return GetProductOutput(success=True, product=_parse_product(data))


@tool(args_schema=ListProductsInput)
@serialize_pydantic_return
async def list_products(
    auth_type: str,
    auth_data: dict[str, Any],
    search: str | None = None,
    status: str | None = "publish",
    type: str | None = "simple",
    after: str | None = None,
    before: str | None = None,
    max_results: int = 20,
) -> ListProductsOutput:
    """Retrieve a list of products with optional filters."""
    err = _validate_credentials(auth_data)
    if err:
        return ListProductsOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    params: dict[str, Any] = {"per_page": min(max_results, 100)}
    if search:
        params["search"] = search
    if status:
        params["status"] = status
    if type:
        params["type"] = type
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/products",
                auth=auth,
                params=params,
            )
        if response.status_code != 200:
            return ListProductsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListProductsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListProductsOutput(success=False, error=f"Call failed: {exc}")
    products = [_parse_product(p) for p in data]
    return ListProductsOutput(success=True, products=products, total=len(products))


@tool(args_schema=SearchCustomersInput)
@serialize_pydantic_return
async def search_customers(
    auth_type: str,
    auth_data: dict[str, Any],
    search: str | None = None,
    email: str | None = None,
    role: str | None = "customer",
    max_results: int = 20,
) -> SearchCustomersOutput:
    """Search for customers by email, name, or other criteria."""
    err = _validate_credentials(auth_data)
    if err:
        return SearchCustomersOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    params: dict[str, Any] = {"per_page": min(max_results, 100)}
    if search:
        params["search"] = search
    if email:
        params["email"] = email
    if role:
        params["role"] = role
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/customers",
                auth=auth,
                params=params,
            )
        if response.status_code != 200:
            return SearchCustomersOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return SearchCustomersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchCustomersOutput(success=False, error=f"Call failed: {exc}")
    customers = [_parse_customer(c) for c in data]
    return SearchCustomersOutput(success=True, customers=customers, total=len(customers))


@tool(args_schema=GetCustomerInput)
@serialize_pydantic_return
async def get_customer(
    auth_type: str,
    auth_data: dict[str, Any],
    customer_id: int,
) -> GetCustomerOutput:
    """Retrieve a specific customer by ID."""
    err = _validate_credentials(auth_data)
    if err:
        return GetCustomerOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/customers/{customer_id}",
                auth=auth,
            )
        if response.status_code != 200:
            return GetCustomerOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetCustomerOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCustomerOutput(success=False, error=f"Call failed: {exc}")
    return GetCustomerOutput(success=True, customer=_parse_customer(data))


@tool(args_schema=CreateCustomerInput)
@serialize_pydantic_return
async def create_customer(
    auth_type: str,
    auth_data: dict[str, Any],
    email: str,
    first_name: str | None = None,
    last_name: str | None = None,
    username: str | None = None,
    password: str | None = None,
    is_paying_customer: bool | None = None,
) -> CreateCustomerOutput:
    """Create a new customer."""
    err = _validate_credentials(auth_data)
    if err:
        return CreateCustomerOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    body: dict[str, Any] = {"email": email}
    if first_name:
        body["first_name"] = first_name
    if last_name:
        body["last_name"] = last_name
    if username:
        body["username"] = username
    if password:
        body["password"] = password
    if is_paying_customer is not None:
        body["is_paying_customer"] = is_paying_customer
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{base_url}/customers",
                auth=auth,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateCustomerOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateCustomerOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateCustomerOutput(success=False, error=f"Call failed: {exc}")
    return CreateCustomerOutput(success=True, customer=_parse_customer(data))


@tool(args_schema=AddOrderNoteInput)
@serialize_pydantic_return
async def add_order_note(
    auth_type: str,
    auth_data: dict[str, Any],
    order_id: int,
    note: str,
) -> AddOrderNoteOutput:
    """Create a new note for an order."""
    err = _validate_credentials(auth_data)
    if err:
        return AddOrderNoteOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{base_url}/orders/{order_id}/notes",
                auth=auth,
                json={"note": note},
            )
        if response.status_code not in (200, 201):
            return AddOrderNoteOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return AddOrderNoteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddOrderNoteOutput(success=False, error=f"Call failed: {exc}")
    return AddOrderNoteOutput(success=True, note=_parse_order_note(data))


@tool(args_schema=GetOrderNoteInput)
@serialize_pydantic_return
async def get_order_note(
    auth_type: str,
    auth_data: dict[str, Any],
    order_id: int,
    note_id: int,
) -> GetOrderNoteOutput:
    """Retrieve a specific order note."""
    err = _validate_credentials(auth_data)
    if err:
        return GetOrderNoteOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/orders/{order_id}/notes/{note_id}",
                auth=auth,
            )
        if response.status_code != 200:
            return GetOrderNoteOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetOrderNoteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetOrderNoteOutput(success=False, error=f"Call failed: {exc}")
    return GetOrderNoteOutput(success=True, note=_parse_order_note(data))


@tool(args_schema=ListOrderNotesInput)
@serialize_pydantic_return
async def list_order_notes(
    auth_type: str,
    auth_data: dict[str, Any],
    order_id: int,
    type: str | None = "any",
) -> ListOrderNotesOutput:
    """Retrieve all notes for a specific order."""
    err = _validate_credentials(auth_data)
    if err:
        return ListOrderNotesOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    params: dict[str, Any] = {}
    if type and type != "any":
        params["type"] = type
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/orders/{order_id}/notes",
                auth=auth,
                params=params,
            )
        if response.status_code != 200:
            return ListOrderNotesOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListOrderNotesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListOrderNotesOutput(success=False, error=f"Call failed: {exc}")
    notes = [_parse_order_note(n) for n in data]
    return ListOrderNotesOutput(success=True, notes=notes)


@tool(args_schema=CreateRefundInput)
@serialize_pydantic_return
async def create_refund(
    auth_type: str,
    auth_data: dict[str, Any],
    order_id: int,
    amount: str | None = None,
    reason: str | None = None,
    api_refund: bool | None = None,
    line_items: list[dict[str, Any]] | None = None,
) -> CreateRefundOutput:
    """Create a new refund for an order."""
    err = _validate_credentials(auth_data)
    if err:
        return CreateRefundOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    body: dict[str, Any] = {}
    if amount:
        body["amount"] = amount
    if reason:
        body["reason"] = reason
    if api_refund is not None:
        body["api_refund"] = api_refund
    if line_items:
        body["line_items"] = line_items
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{base_url}/orders/{order_id}/refunds",
                auth=auth,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateRefundOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateRefundOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateRefundOutput(success=False, error=f"Call failed: {exc}")
    return CreateRefundOutput(
        success=True,
        refund=RefundSummary(
            id=data.get("id"),
            amount=data.get("amount"),
            reason=data.get("reason"),
            refunded_by=data.get("refunded_by"),
            date_created=data.get("date_created"),
            line_items=data.get("line_items") or [],
        ),
    )


@tool(args_schema=ListPaymentMethodOptionsInput)
@serialize_pydantic_return
async def list_payment_method_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListPaymentMethodOptionsOutput:
    """Retrieve available payment gateway options."""
    err = _validate_credentials(auth_data)
    if err:
        return ListPaymentMethodOptionsOutput(success=False, error=err)
    base_url = _build_base_url(auth_data)
    auth = _get_auth(auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/payment_gateways",
                auth=auth,
            )
        if response.status_code != 200:
            return ListPaymentMethodOptionsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListPaymentMethodOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListPaymentMethodOptionsOutput(success=False, error=f"Call failed: {exc}")
    methods = [
        PaymentMethodSummary(
            id=m.get("id"),
            title=m.get("title"),
            description=m.get("description"),
            enabled=m.get("enabled"),
        )
        for m in data
    ]
    return ListPaymentMethodOptionsOutput(success=True, payment_methods=methods)

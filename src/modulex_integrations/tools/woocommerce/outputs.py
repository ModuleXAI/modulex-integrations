"""Pydantic response models for the woocommerce integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddOrderNoteOutput",
    "CreateCustomerOutput",
    "CreateOrderOutput",
    "CreateProductOutput",
    "CreateRefundOutput",
    "CustomerSummary",
    "DeleteOrderOutput",
    "GetCustomerOutput",
    "GetOrderNoteOutput",
    "GetOrderOutput",
    "GetProductOutput",
    "ListOrderNotesOutput",
    "ListOrdersOutput",
    "ListPaymentMethodOptionsOutput",
    "ListProductsOutput",
    "OrderNoteSummary",
    "OrderSummary",
    "PaymentMethodSummary",
    "ProductSummary",
    "RefundSummary",
    "SearchCustomersOutput",
    "UpdateOrderStatusOutput",
    "UpdateProductOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class OrderSummary(_Base):
    id: int | None = None
    number: str | None = None
    status: str | None = None
    total: str | None = None
    currency: str | None = None
    customer_id: int | None = None
    payment_method: str | None = None
    date_created: str | None = None
    date_modified: str | None = None
    line_items: list[dict[str, Any]] = Field(default_factory=list)
    billing: dict[str, Any] | None = None
    shipping: dict[str, Any] | None = None


class ProductSummary(_Base):
    id: int | None = None
    name: str | None = None
    slug: str | None = None
    type: str | None = None
    status: str | None = None
    regular_price: str | None = None
    sale_price: str | None = None
    price: str | None = None
    description: str | None = None
    categories: list[dict[str, Any]] = Field(default_factory=list)
    images: list[dict[str, Any]] = Field(default_factory=list)
    date_created: str | None = None


class CustomerSummary(_Base):
    id: int | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    role: str | None = None
    date_created: str | None = None
    billing: dict[str, Any] | None = None
    shipping: dict[str, Any] | None = None
    is_paying_customer: bool | None = None


class OrderNoteSummary(_Base):
    id: int | None = None
    author: str | None = None
    date_created: str | None = None
    note: str | None = None
    customer_note: bool | None = None


class RefundSummary(_Base):
    id: int | None = None
    amount: str | None = None
    reason: str | None = None
    refunded_by: int | None = None
    date_created: str | None = None
    line_items: list[dict[str, Any]] = Field(default_factory=list)


class PaymentMethodSummary(_Base):
    id: str | None = None
    title: str | None = None
    description: str | None = None
    enabled: bool | None = None


# --- Per-action output models ---------------------------------------------


class CreateOrderOutput(_Base):
    success: bool
    error: str | None = None
    order: OrderSummary | None = None


class GetOrderOutput(_Base):
    success: bool
    error: str | None = None
    order: OrderSummary | None = None


class ListOrdersOutput(_Base):
    success: bool
    error: str | None = None
    orders: list[OrderSummary] = Field(default_factory=list)
    total: int = 0


class DeleteOrderOutput(_Base):
    success: bool
    error: str | None = None
    order: OrderSummary | None = None


class UpdateOrderStatusOutput(_Base):
    success: bool
    error: str | None = None
    order: OrderSummary | None = None


class CreateProductOutput(_Base):
    success: bool
    error: str | None = None
    product: ProductSummary | None = None


class UpdateProductOutput(_Base):
    success: bool
    error: str | None = None
    product: ProductSummary | None = None


class GetProductOutput(_Base):
    success: bool
    error: str | None = None
    product: ProductSummary | None = None


class ListProductsOutput(_Base):
    success: bool
    error: str | None = None
    products: list[ProductSummary] = Field(default_factory=list)
    total: int = 0


class SearchCustomersOutput(_Base):
    success: bool
    error: str | None = None
    customers: list[CustomerSummary] = Field(default_factory=list)
    total: int = 0


class GetCustomerOutput(_Base):
    success: bool
    error: str | None = None
    customer: CustomerSummary | None = None


class CreateCustomerOutput(_Base):
    success: bool
    error: str | None = None
    customer: CustomerSummary | None = None


class AddOrderNoteOutput(_Base):
    success: bool
    error: str | None = None
    note: OrderNoteSummary | None = None


class GetOrderNoteOutput(_Base):
    success: bool
    error: str | None = None
    note: OrderNoteSummary | None = None


class ListOrderNotesOutput(_Base):
    success: bool
    error: str | None = None
    notes: list[OrderNoteSummary] = Field(default_factory=list)


class CreateRefundOutput(_Base):
    success: bool
    error: str | None = None
    refund: RefundSummary | None = None


class ListPaymentMethodOptionsOutput(_Base):
    success: bool
    error: str | None = None
    payment_methods: list[PaymentMethodSummary] = Field(default_factory=list)

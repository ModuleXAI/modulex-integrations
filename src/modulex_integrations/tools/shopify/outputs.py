"""Pydantic response models for the shopify integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddProductToCustomCollectionOutput",
    "AddTagsOutput",
    "CreateArticleOutput",
    "CreateBlogOutput",
    "CreateCustomCollectionOutput",
    "CreateMetafieldOutput",
    "CreateMetaobjectOutput",
    "CreatePageOutput",
    "CreateProductOutput",
    "CreateProductVariantOutput",
    "CreateSmartCollectionOutput",
    "DeleteArticleOutput",
    "DeleteBlogOutput",
    "DeleteMetafieldOutput",
    "DeletePageOutput",
    "GetArticlesOutput",
    "GetAssignedFulfillmentOrdersOutput",
    "GetCustomerOutput",
    "GetCustomersOutput",
    "GetDraftOrderOutput",
    "GetDraftOrdersOutput",
    "GetFulfillmentOrderOutput",
    "GetFulfillmentOrdersOutput",
    "GetFulfillmentOutput",
    "GetMetafieldsOutput",
    "GetMetaobjectsOutput",
    "GetPagesOutput",
    "SearchCustomCollectionByNameOutput",
    "SearchOrdersOutput",
    "SearchProductVariantOutput",
    "SearchProductsOutput",
    "ShopifyUserError",
    "UpdateArticleOutput",
    "UpdateInventoryLevelOutput",
    "UpdateMetafieldOutput",
    "UpdateMetaobjectOutput",
    "UpdateOrderOutput",
    "UpdatePageOutput",
    "UpdateProductOutput",
    "UpdateProductVariantOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class ShopifyUserError(_Base):
    """Error returned by a Shopify GraphQL mutation."""

    field: list[str] | None = None
    message: str | None = None


# --- Per-action output models (alphabetized) --------------------------------


class AddProductToCustomCollectionOutput(_Base):
    success: bool
    error: str | None = None
    job_id: str | None = None
    job_done: bool | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class AddTagsOutput(_Base):
    success: bool
    error: str | None = None
    node_id: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class CreateArticleOutput(_Base):
    success: bool
    error: str | None = None
    article_id: str | None = None
    title: str | None = None
    handle: str | None = None
    body: str | None = None
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class CreateBlogOutput(_Base):
    success: bool
    error: str | None = None
    blog_id: str | None = None
    title: str | None = None
    handle: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class CreateCustomCollectionOutput(_Base):
    success: bool
    error: str | None = None
    collection_id: str | None = None
    title: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class CreateMetafieldOutput(_Base):
    success: bool
    error: str | None = None
    definition_id: str | None = None
    name: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class CreateMetaobjectOutput(_Base):
    success: bool
    error: str | None = None
    metaobject_id: str | None = None
    handle: str | None = None
    type_name: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class CreatePageOutput(_Base):
    success: bool
    error: str | None = None
    page_id: str | None = None
    title: str | None = None
    handle: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class CreateProductOutput(_Base):
    success: bool
    error: str | None = None
    product_id: str | None = None
    title: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class CreateProductVariantOutput(_Base):
    success: bool
    error: str | None = None
    variant_id: str | None = None
    title: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class CreateSmartCollectionOutput(_Base):
    success: bool
    error: str | None = None
    collection_id: str | None = None
    title: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class DeleteArticleOutput(_Base):
    success: bool
    error: str | None = None
    deleted_article_id: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class DeleteBlogOutput(_Base):
    success: bool
    error: str | None = None
    deleted_blog_id: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class DeleteMetafieldOutput(_Base):
    success: bool
    error: str | None = None
    deleted_metafields: list[dict[str, Any]] = Field(default_factory=list)
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class DeletePageOutput(_Base):
    success: bool
    error: str | None = None
    deleted_page_id: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class GetArticlesOutput(_Base):
    success: bool
    error: str | None = None
    articles: list[dict[str, Any]] = Field(default_factory=list)


class GetAssignedFulfillmentOrdersOutput(_Base):
    success: bool
    error: str | None = None
    fulfillment_orders: list[dict[str, Any]] = Field(default_factory=list)


class GetCustomerOutput(_Base):
    success: bool
    error: str | None = None
    customer_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    state: str | None = None
    tags: list[str] = Field(default_factory=list)
    note: str | None = None


class GetCustomersOutput(_Base):
    success: bool
    error: str | None = None
    customers: list[dict[str, Any]] = Field(default_factory=list)


class GetDraftOrderOutput(_Base):
    success: bool
    error: str | None = None
    draft_order_id: str | None = None
    name: str | None = None
    status: str | None = None
    email: str | None = None
    invoice_url: str | None = None
    total_price: str | None = None
    currency_code: str | None = None


class GetDraftOrdersOutput(_Base):
    success: bool
    error: str | None = None
    draft_orders: list[dict[str, Any]] = Field(default_factory=list)


class GetFulfillmentOutput(_Base):
    success: bool
    error: str | None = None
    fulfillment_id: str | None = None
    name: str | None = None
    status: str | None = None
    display_status: str | None = None
    total_quantity: int | None = None
    created_at: str | None = None
    tracking_info: list[dict[str, Any]] = Field(default_factory=list)


class GetFulfillmentOrderOutput(_Base):
    success: bool
    error: str | None = None
    fulfillment_order_id: str | None = None
    status: str | None = None
    request_status: str | None = None
    created_at: str | None = None


class GetFulfillmentOrdersOutput(_Base):
    success: bool
    error: str | None = None
    fulfillment_orders: list[dict[str, Any]] = Field(default_factory=list)


class GetMetafieldsOutput(_Base):
    success: bool
    error: str | None = None
    metafields: list[dict[str, Any]] = Field(default_factory=list)


class GetMetaobjectsOutput(_Base):
    success: bool
    error: str | None = None
    metaobjects: list[dict[str, Any]] = Field(default_factory=list)


class GetPagesOutput(_Base):
    success: bool
    error: str | None = None
    pages: list[dict[str, Any]] = Field(default_factory=list)


class SearchCustomCollectionByNameOutput(_Base):
    success: bool
    error: str | None = None
    collections: list[dict[str, Any]] = Field(default_factory=list)


class SearchOrdersOutput(_Base):
    success: bool
    error: str | None = None
    orders: list[dict[str, Any]] = Field(default_factory=list)


class SearchProductVariantOutput(_Base):
    success: bool
    error: str | None = None
    variant_id: str | None = None
    title: str | None = None
    created: bool = False
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class SearchProductsOutput(_Base):
    success: bool
    error: str | None = None
    products: list[dict[str, Any]] = Field(default_factory=list)


class UpdateArticleOutput(_Base):
    success: bool
    error: str | None = None
    article_id: str | None = None
    title: str | None = None
    handle: str | None = None
    body: str | None = None
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class UpdateInventoryLevelOutput(_Base):
    success: bool
    error: str | None = None
    created_at: str | None = None
    reason: str | None = None
    changes: list[dict[str, Any]] = Field(default_factory=list)
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class UpdateMetafieldOutput(_Base):
    success: bool
    error: str | None = None
    metafields: list[dict[str, Any]] = Field(default_factory=list)
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class UpdateMetaobjectOutput(_Base):
    success: bool
    error: str | None = None
    metaobject_id: str | None = None
    type_name: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class UpdateOrderOutput(_Base):
    success: bool
    error: str | None = None
    order_id: str | None = None
    name: str | None = None
    email: str | None = None
    tags: list[str] = Field(default_factory=list)
    note: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class UpdatePageOutput(_Base):
    success: bool
    error: str | None = None
    page_id: str | None = None
    title: str | None = None
    handle: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class UpdateProductOutput(_Base):
    success: bool
    error: str | None = None
    product_id: str | None = None
    title: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)


class UpdateProductVariantOutput(_Base):
    success: bool
    error: str | None = None
    variant_id: str | None = None
    title: str | None = None
    user_errors: list[ShopifyUserError] = Field(default_factory=list)

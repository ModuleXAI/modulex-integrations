"""Shopify LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.shopify.outputs import (
    AddProductToCustomCollectionOutput,
    AddTagsOutput,
    CreateArticleOutput,
    CreateBlogOutput,
    CreateCustomCollectionOutput,
    CreateMetafieldOutput,
    CreateMetaobjectOutput,
    CreatePageOutput,
    CreateProductOutput,
    CreateProductVariantOutput,
    CreateSmartCollectionOutput,
    DeleteArticleOutput,
    DeleteBlogOutput,
    DeleteMetafieldOutput,
    DeletePageOutput,
    GetArticlesOutput,
    GetAssignedFulfillmentOrdersOutput,
    GetCustomerOutput,
    GetCustomersOutput,
    GetDraftOrderOutput,
    GetDraftOrdersOutput,
    GetFulfillmentOrderOutput,
    GetFulfillmentOrdersOutput,
    GetFulfillmentOutput,
    GetMetafieldsOutput,
    GetMetaobjectsOutput,
    GetPagesOutput,
    SearchCustomCollectionByNameOutput,
    SearchOrdersOutput,
    SearchProductsOutput,
    SearchProductVariantOutput,
    ShopifyUserError,
    UpdateArticleOutput,
    UpdateInventoryLevelOutput,
    UpdateMetafieldOutput,
    UpdateMetaobjectOutput,
    UpdateOrderOutput,
    UpdatePageOutput,
    UpdateProductOutput,
    UpdateProductVariantOutput,
)

__all__ = [
    "add_product_to_custom_collection",
    "add_tags",
    "create_article",
    "create_blog",
    "create_custom_collection",
    "create_metafield",
    "create_metaobject",
    "create_page",
    "create_product",
    "create_product_variant",
    "create_smart_collection",
    "delete_article",
    "delete_blog",
    "delete_metafield",
    "delete_page",
    "get_articles",
    "get_assigned_fulfillment_orders",
    "get_customer",
    "get_customers",
    "get_draft_order",
    "get_draft_orders",
    "get_fulfillment",
    "get_fulfillment_order",
    "get_fulfillment_orders",
    "get_metafields",
    "get_metaobjects",
    "get_pages",
    "search_custom_collection_by_name",
    "search_orders",
    "search_product_variant",
    "search_products",
    "update_article",
    "update_inventory_level",
    "update_metafield",
    "update_metaobject",
    "update_order",
    "update_page",
    "update_product",
    "update_product_variant",
]

_API_VERSION = "2025-01"
_TIMEOUT = 30.0


def _check_credentials(auth_data: dict[str, Any]) -> str | None:
    """Return an error message if credentials are missing, else None."""
    token = auth_data.get("access_token") or auth_data.get("token") or ""
    if not token or not token.strip():
        return "Missing or empty access token in auth_data"
    return None


def _graphql_url(shop_id: str) -> str:
    return f"https://{shop_id}.myshopify.com/admin/api/{_API_VERSION}/graphql.json"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    token = auth_data.get("access_token") or auth_data.get("token") or ""
    return {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": token,
    }


def _parse_user_errors(errors: list[dict[str, Any]] | None) -> list[ShopifyUserError]:
    if not errors:
        return []
    return [ShopifyUserError(field=e.get("field"), message=e.get("message")) for e in errors]


async def _graphql(
    shop_id: str,
    headers: dict[str, str],
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.post(
            _graphql_url(shop_id),
            headers=headers,
            json={"query": query, "variables": variables or {}},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data


# --- Input schemas --------------------------------------------------------


class AddProductToCustomCollectionInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    collection_id: str = Field(description="The GID of the custom collection")
    product_ids: list[str] = Field(description="Array of product GID strings to add")


class AddTagsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    resource_type: str = Field(description="Resource type: Product, Customer, Order, DraftOrder, Article")
    gid: str = Field(description="The Shopify Admin Resource GID")
    tags: list[str] = Field(description="Array of tag strings to add")


class CreateArticleInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    blog_id: str = Field(description="The GID of the blog")
    title: str = Field(description="The title of the article")
    author: str = Field(description="The author name")
    body: str | None = Field(default=None, description="Article body with HTML markup")
    summary: str | None = Field(default=None, description="Article summary")
    image_url: str | None = Field(default=None, description="URL of the article image")
    tags: list[str] | None = Field(default=None, description="Array of tag strings")


class CreateBlogInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    title: str = Field(description="The title of the blog")


class CreateCustomCollectionInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    title: str = Field(description="The name of the custom collection")
    products: list[str] | None = Field(default=None, description="Array of product GID strings")
    metafields: list[dict[str, Any]] | None = Field(default=None, description="Array of metafield objects")
    image_url: str | None = Field(default=None, description="The source URL of the collection image")


class CreateMetafieldInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    owner_resource: str = Field(description="The resource type")
    name: str = Field(description="Human-readable name for the definition")
    namespace: str = Field(description="Namespace for the metafield group")
    key: str = Field(description="The metafield key")
    type: str = Field(description="The metafield data type")
    pin: bool = Field(default=False, description="Whether to pin the definition")


class CreateMetaobjectInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    type: str = Field(description="The metaobject type")
    fields: list[dict[str, str]] | None = Field(default=None, description="Array of field objects with key and value")


class CreatePageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    title: str = Field(description="The title of the page")
    body: str = Field(description="The text content with HTML markup")


class CreateProductInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    title: str = Field(description="Title of the new product")
    product_description: str | None = Field(default=None, description="Product description (HTML)")
    vendor: str | None = Field(default=None, description="Vendor name")
    product_type: str | None = Field(default=None, description="Product type categorization")
    status: str | None = Field(default=None, description="Status: ACTIVE, ARCHIVED, DRAFT")
    images: list[str] | None = Field(default=None, description="Array of image URL strings")
    options: list[dict[str, Any]] | None = Field(default=None, description="Array of option objects")
    tags: list[str] | None = Field(default=None, description="Array of tag strings")


class CreateProductVariantInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    product_id: str = Field(description="The GID of the product")
    option_ids: list[str] = Field(description="Array of option value GID strings")
    price: str | None = Field(default=None, description="The price")
    image_url: str | None = Field(default=None, description="URL of the variant image")
    sku: str | None = Field(default=None, description="SKU identifier")
    barcode: str | None = Field(default=None, description="Barcode/UPC/ISBN")
    weight: str | None = Field(default=None, description="Weight value")
    weight_unit: str | None = Field(default=None, description="Weight unit")
    metafields: list[dict[str, Any]] | None = Field(default=None, description="Array of metafield objects")


class CreateSmartCollectionInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    title: str = Field(description="Title of the smart collection")
    rules: list[dict[str, Any]] = Field(description="Array of rule objects with column, relation, condition")
    disjunctive: bool = Field(default=False, description="If true, match any rule; if false, match all")


class DeleteArticleInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    article_id: str = Field(description="The GID of the article to delete")


class DeleteBlogInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    blog_id: str = Field(description="The GID of the blog to delete")


class DeleteMetafieldInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    metafield_id: str = Field(description="The GID of the metafield to delete")


class DeletePageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    page_id: str = Field(description="The GID of the page to delete")


class GetArticlesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    blog_id: str = Field(description="The GID of the blog")
    max_results: int = Field(default=100, description="Maximum number of results")


class GetAssignedFulfillmentOrdersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    max_results: int = Field(default=100, description="Maximum number of results")


class GetCustomerInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    customer_id: str = Field(description="The GID of the customer")


class GetCustomersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    query: str | None = Field(default=None, description="Filter query string")
    sort_key: str | None = Field(default=None, description="Sort key")
    max_results: int = Field(default=100, description="Maximum number of results")


class GetDraftOrderInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    draft_order_id: str = Field(description="The GID of the draft order")


class GetDraftOrdersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    query: str | None = Field(default=None, description="Filter query")
    sort_key: str | None = Field(default=None, description="Sort key")
    max_results: int = Field(default=100, description="Maximum number of results")


class GetFulfillmentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    fulfillment_id: str = Field(description="The GID of the fulfillment")


class GetFulfillmentOrderInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    fulfillment_order_id: str = Field(description="The GID of the fulfillment order")


class GetFulfillmentOrdersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    query: str | None = Field(default=None, description="Filter query")
    include_closed: bool = Field(default=False, description="Include closed fulfillment orders")
    max_results: int = Field(default=100, description="Maximum number of results")


class GetMetafieldsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    owner_resource: str = Field(description="The resource type")
    owner_id: str = Field(description="The GID of the resource owner")
    namespace: list[str] | None = Field(default=None, description="Filter by namespace")
    key: list[str] | None = Field(default=None, description="Filter by key")


class GetMetaobjectsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    type: str = Field(description="The metaobject type name")


class GetPagesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    max_results: int = Field(default=100, description="Maximum number of results")


class SearchCustomCollectionByNameInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    title: str | None = Field(default=None, description="Collection name to search")
    exact_match: bool = Field(default=False, description="Require exact title match")
    max_results: int = Field(default=100, description="Maximum number of results")
    sort_key: str | None = Field(default=None, description="Sort key")


class SearchOrdersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    query: str | None = Field(default=None, description="Search query")
    sort_key: str | None = Field(default=None, description="Sort key")
    max_results: int | None = Field(default=None, description="Maximum number of results")


class SearchProductVariantInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    product_id: str = Field(description="The GID of the product")
    product_variant_id: str | None = Field(default=None, description="Variant GID (takes precedence)")
    title: str | None = Field(default=None, description="Variant title to search")
    create_if_not_found: bool = Field(default=False, description="Create if not found")
    option_ids: list[str] | None = Field(default=None, description="Option value GIDs for creation")
    price: str | None = Field(default=None, description="Price for creation")


class SearchProductsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    title: str | None = Field(default=None, description="Product title to search")
    exact_match: bool = Field(default=False, description="Exact title match")
    product_ids: list[str] | None = Field(default=None, description="Filter by product GIDs")
    collection_id: str | None = Field(default=None, description="Filter by collection GID")
    product_type: str | None = Field(default=None, description="Filter by product type")
    vendor: str | None = Field(default=None, description="Filter by vendor")
    max_results: int = Field(default=100, description="Maximum number of results")
    sort_key: str | None = Field(default=None, description="Sort key")


class UpdateArticleInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    article_id: str = Field(description="The GID of the article")
    title: str | None = Field(default=None, description="New title")
    body_html: str | None = Field(default=None, description="New body with HTML")
    author: str | None = Field(default=None, description="New author name")
    summary: str | None = Field(default=None, description="New summary")
    image_url: str | None = Field(default=None, description="New image URL")
    tags: list[str] | None = Field(default=None, description="New tags")


class UpdateInventoryLevelInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    location_id: str = Field(description="The GID of the location")
    inventory_item_id: str = Field(description="The GID of the inventory item")
    available: int = Field(description="The available quantity to set")
    reason: str = Field(description="The reason for the change")
    reference_document_uri: str | None = Field(default=None, description="Reference URI")


class UpdateMetafieldInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    owner_id: str = Field(description="The GID of the resource owner")
    metafield_id: str = Field(description="The GID of the metafield")
    value: str = Field(description="The new value")


class UpdateMetaobjectInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    metaobject_id: str = Field(description="The GID of the metaobject")
    fields: list[dict[str, str]] | None = Field(default=None, description="Array of field objects")


class UpdateOrderInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    order_id: str = Field(description="The GID of the order")
    email: str | None = Field(default=None, description="Email address")
    note: str | None = Field(default=None, description="Order note")
    tags: list[str] | None = Field(default=None, description="Tags")
    metafields: list[dict[str, Any]] | None = Field(default=None, description="Metafield objects")


class UpdatePageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    page_id: str = Field(description="The GID of the page")
    title: str | None = Field(default=None, description="New title")
    body: str | None = Field(default=None, description="New body with HTML")


class UpdateProductInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    product_id: str = Field(description="The GID of the product")
    title: str | None = Field(default=None, description="New title")
    product_description: str | None = Field(default=None, description="New description (HTML)")
    vendor: str | None = Field(default=None, description="New vendor name")
    product_type: str | None = Field(default=None, description="New product type")
    status: str | None = Field(default=None, description="New status: ACTIVE, ARCHIVED, DRAFT")
    images: list[str] | None = Field(default=None, description="New image URLs")
    tags: list[str] | None = Field(default=None, description="New tags")
    metafields: list[dict[str, Any]] | None = Field(default=None, description="Metafield objects")
    handle: str | None = Field(default=None, description="URL handle")
    seo_title: str | None = Field(default=None, description="SEO title")
    seo_description: str | None = Field(default=None, description="SEO description")


class UpdateProductVariantInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shop_id: str = Field(description="The Shopify store subdomain")
    product_id: str = Field(description="The GID of the product")
    product_variant_id: str = Field(description="The GID of the variant")
    option_ids: list[str] | None = Field(default=None, description="Option value GIDs")
    price: str | None = Field(default=None, description="New price")
    sku: str | None = Field(default=None, description="New SKU")
    barcode: str | None = Field(default=None, description="New barcode")
    weight: str | None = Field(default=None, description="New weight")
    weight_unit: str | None = Field(default=None, description="Weight unit")
    metafields: list[dict[str, Any]] | None = Field(default=None, description="Metafield objects")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=AddProductToCustomCollectionInput)
@serialize_pydantic_return
async def add_product_to_custom_collection(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    collection_id: str,
    product_ids: list[str],
) -> AddProductToCustomCollectionOutput:
    """Add one or more products to a custom collection."""
    if _cred_err := _check_credentials(auth_data):
        return AddProductToCustomCollectionOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation collectionAddProductsV2($id: ID!, $productIds: [ID!]!) {
      collectionAddProductsV2(id: $id, productIds: $productIds) {
        job { done id }
        userErrors { field message }
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"id": collection_id, "productIds": product_ids})
        data = result.get("data", {}).get("collectionAddProductsV2", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return AddProductToCustomCollectionOutput(success=False, error=ue[0].message, user_errors=ue)
        job = data.get("job") or {}
        return AddProductToCustomCollectionOutput(success=True, job_id=job.get("id"), job_done=job.get("done"), user_errors=ue)
    except Exception as exc:
        return AddProductToCustomCollectionOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=AddTagsInput)
@serialize_pydantic_return
async def add_tags(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    resource_type: str,
    gid: str,
    tags: list[str],
) -> AddTagsOutput:
    """Add tags to a Shopify resource (Product, Customer, Order, DraftOrder, or Article)."""
    if _cred_err := _check_credentials(auth_data):
        return AddTagsOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation tagsAdd($id: ID!, $tags: [String!]!) {
      tagsAdd(id: $id, tags: $tags) {
        node { id }
        userErrors { field message }
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"id": gid, "tags": tags})
        data = result.get("data", {}).get("tagsAdd", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return AddTagsOutput(success=False, error=ue[0].message, user_errors=ue)
        node = data.get("node") or {}
        return AddTagsOutput(success=True, node_id=node.get("id"), user_errors=ue)
    except Exception as exc:
        return AddTagsOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=CreateArticleInput)
@serialize_pydantic_return
async def create_article(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    blog_id: str,
    title: str,
    author: str,
    body: str | None = None,
    summary: str | None = None,
    image_url: str | None = None,
    tags: list[str] | None = None,
) -> CreateArticleOutput:
    """Create a new blog article."""
    if _cred_err := _check_credentials(auth_data):
        return CreateArticleOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation articleCreate($article: ArticleCreateInput!) {
      articleCreate(article: $article) {
        article { id title handle body summary tags }
        userErrors { field message }
      }
    }
    """
    article_input: dict[str, Any] = {"blog": blog_id, "title": title, "author": {"name": author}}
    if body is not None:
        article_input["body"] = body
    if summary is not None:
        article_input["summary"] = summary
    if image_url is not None:
        article_input["image"] = {"url": image_url}
    if tags:
        article_input["tags"] = tags
    try:
        result = await _graphql(shop_id, headers, query, {"article": article_input})
        data = result.get("data", {}).get("articleCreate", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return CreateArticleOutput(success=False, error=ue[0].message, user_errors=ue)
        article = data.get("article") or {}
        return CreateArticleOutput(
            success=True, article_id=article.get("id"), title=article.get("title"),
            handle=article.get("handle"), body=article.get("body"), summary=article.get("summary"),
            tags=article.get("tags") or [], user_errors=ue,
        )
    except Exception as exc:
        return CreateArticleOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=CreateBlogInput)
@serialize_pydantic_return
async def create_blog(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    title: str,
) -> CreateBlogOutput:
    """Create a new blog."""
    if _cred_err := _check_credentials(auth_data):
        return CreateBlogOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation blogCreate($blog: BlogCreateInput!) {
      blogCreate(blog: $blog) {
        blog { id title handle }
        userErrors { field message }
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"blog": {"title": title}})
        data = result.get("data", {}).get("blogCreate", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return CreateBlogOutput(success=False, error=ue[0].message, user_errors=ue)
        blog = data.get("blog") or {}
        return CreateBlogOutput(success=True, blog_id=blog.get("id"), title=blog.get("title"), handle=blog.get("handle"), user_errors=ue)
    except Exception as exc:
        return CreateBlogOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=CreateCustomCollectionInput)
@serialize_pydantic_return
async def create_custom_collection(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    title: str,
    products: list[str] | None = None,
    metafields: list[dict[str, Any]] | None = None,
    image_url: str | None = None,
) -> CreateCustomCollectionOutput:
    """Create a new custom collection."""
    if _cred_err := _check_credentials(auth_data):
        return CreateCustomCollectionOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation collectionCreate($input: CollectionInput!) {
      collectionCreate(input: $input) {
        collection { id title }
        userErrors { field message }
      }
    }
    """
    collection_input: dict[str, Any] = {"title": title}
    if products:
        collection_input["products"] = products
    if metafields:
        collection_input["metafields"] = metafields
    if image_url:
        collection_input["image"] = {"src": image_url}
    try:
        result = await _graphql(shop_id, headers, query, {"input": collection_input})
        data = result.get("data", {}).get("collectionCreate", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return CreateCustomCollectionOutput(success=False, error=ue[0].message, user_errors=ue)
        coll = data.get("collection") or {}
        return CreateCustomCollectionOutput(success=True, collection_id=coll.get("id"), title=coll.get("title"), user_errors=ue)
    except Exception as exc:
        return CreateCustomCollectionOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=CreateMetafieldInput)
@serialize_pydantic_return
async def create_metafield(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    owner_resource: str,
    name: str,
    namespace: str,
    key: str,
    type: str,
    pin: bool = False,
) -> CreateMetafieldOutput:
    """Create a metafield definition belonging to a resource."""
    if _cred_err := _check_credentials(auth_data):
        return CreateMetafieldOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation metafieldDefinitionCreate($definition: MetafieldDefinitionInput!) {
      metafieldDefinitionCreate(definition: $definition) {
        createdDefinition { id name }
        userErrors { field message }
      }
    }
    """
    definition: dict[str, Any] = {
        "ownerType": owner_resource,
        "name": name,
        "namespace": namespace,
        "key": key,
        "type": type,
        "pin": pin,
    }
    try:
        result = await _graphql(shop_id, headers, query, {"definition": definition})
        data = result.get("data", {}).get("metafieldDefinitionCreate", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return CreateMetafieldOutput(success=False, error=ue[0].message, user_errors=ue)
        defn = data.get("createdDefinition") or {}
        return CreateMetafieldOutput(success=True, definition_id=defn.get("id"), name=defn.get("name"), user_errors=ue)
    except Exception as exc:
        return CreateMetafieldOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=CreateMetaobjectInput)
@serialize_pydantic_return
async def create_metaobject(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    type: str,
    fields: list[dict[str, str]] | None = None,
) -> CreateMetaobjectOutput:
    """Create a metaobject."""
    if _cred_err := _check_credentials(auth_data):
        return CreateMetaobjectOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation metaobjectCreate($metaobject: MetaobjectCreateInput!) {
      metaobjectCreate(metaobject: $metaobject) {
        metaobject { id handle type }
        userErrors { field message }
      }
    }
    """
    metaobject_input: dict[str, Any] = {"type": type}
    if fields:
        metaobject_input["fields"] = fields
    try:
        result = await _graphql(shop_id, headers, query, {"metaobject": metaobject_input})
        data = result.get("data", {}).get("metaobjectCreate", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return CreateMetaobjectOutput(success=False, error=ue[0].message, user_errors=ue)
        mo = data.get("metaobject") or {}
        return CreateMetaobjectOutput(success=True, metaobject_id=mo.get("id"), handle=mo.get("handle"), type_name=mo.get("type"), user_errors=ue)
    except Exception as exc:
        return CreateMetaobjectOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=CreatePageInput)
@serialize_pydantic_return
async def create_page(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    title: str,
    body: str,
) -> CreatePageOutput:
    """Create a new page."""
    if _cred_err := _check_credentials(auth_data):
        return CreatePageOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation pageCreate($page: PageCreateInput!) {
      pageCreate(page: $page) {
        page { id title handle }
        userErrors { field message }
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"page": {"title": title, "body": body}})
        data = result.get("data", {}).get("pageCreate", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return CreatePageOutput(success=False, error=ue[0].message, user_errors=ue)
        page = data.get("page") or {}
        return CreatePageOutput(success=True, page_id=page.get("id"), title=page.get("title"), handle=page.get("handle"), user_errors=ue)
    except Exception as exc:
        return CreatePageOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=CreateProductInput)
@serialize_pydantic_return
async def create_product(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    title: str,
    product_description: str | None = None,
    vendor: str | None = None,
    product_type: str | None = None,
    status: str | None = None,
    images: list[str] | None = None,
    options: list[dict[str, Any]] | None = None,
    tags: list[str] | None = None,
) -> CreateProductOutput:
    """Create a new product."""
    if _cred_err := _check_credentials(auth_data):
        return CreateProductOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation productCreate($product: ProductCreateInput!, $media: [CreateMediaInput!]) {
      productCreate(product: $product, media: $media) {
        product { id title }
        userErrors { field message }
      }
    }
    """
    product_input: dict[str, Any] = {"title": title}
    if product_description is not None:
        product_input["descriptionHtml"] = product_description
    if vendor is not None:
        product_input["vendor"] = vendor
    if product_type is not None:
        product_input["productType"] = product_type
    if status is not None:
        product_input["status"] = status
    if options:
        product_input["productOptions"] = options
    if tags:
        product_input["tags"] = tags
    media: list[dict[str, Any]] = []
    if images:
        media = [{"originalSource": url, "mediaContentType": "IMAGE"} for url in images]
    try:
        result = await _graphql(shop_id, headers, query, {"product": product_input, "media": media or None})
        data = result.get("data", {}).get("productCreate", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return CreateProductOutput(success=False, error=ue[0].message, user_errors=ue)
        product = data.get("product") or {}
        return CreateProductOutput(success=True, product_id=product.get("id"), title=product.get("title"), user_errors=ue)
    except Exception as exc:
        return CreateProductOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=CreateProductVariantInput)
@serialize_pydantic_return
async def create_product_variant(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    product_id: str,
    option_ids: list[str],
    price: str | None = None,
    image_url: str | None = None,
    sku: str | None = None,
    barcode: str | None = None,
    weight: str | None = None,
    weight_unit: str | None = None,
    metafields: list[dict[str, Any]] | None = None,
) -> CreateProductVariantOutput:
    """Create a new product variant."""
    if _cred_err := _check_credentials(auth_data):
        return CreateProductVariantOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation productVariantsBulkCreate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
      productVariantsBulkCreate(productId: $productId, variants: $variants) {
        productVariants { id title }
        userErrors { field message }
      }
    }
    """
    variant: dict[str, Any] = {"optionValues": [{"optionName": "", "id": oid} for oid in option_ids]}
    if price is not None:
        variant["price"] = price
    if image_url is not None:
        variant["mediaSrc"] = [image_url]
    if sku is not None:
        variant["inventoryItem"] = {"sku": sku}
    if barcode is not None:
        variant.setdefault("inventoryItem", {})["measurement"] = {"weight": {}}
        variant["barcode"] = barcode
    if weight is not None and weight_unit is not None:
        variant.setdefault("inventoryItem", {})["measurement"] = {"weight": {"value": float(weight), "unit": weight_unit}}
    if metafields:
        variant["metafields"] = metafields
    try:
        result = await _graphql(shop_id, headers, query, {"productId": product_id, "variants": [variant]})
        data = result.get("data", {}).get("productVariantsBulkCreate", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return CreateProductVariantOutput(success=False, error=ue[0].message, user_errors=ue)
        variants = data.get("productVariants") or []
        v = variants[0] if variants else {}
        return CreateProductVariantOutput(success=True, variant_id=v.get("id"), title=v.get("title"), user_errors=ue)
    except Exception as exc:
        return CreateProductVariantOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=CreateSmartCollectionInput)
@serialize_pydantic_return
async def create_smart_collection(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    title: str,
    rules: list[dict[str, Any]],
    disjunctive: bool = False,
) -> CreateSmartCollectionOutput:
    """Create a smart collection with automated rules."""
    if _cred_err := _check_credentials(auth_data):
        return CreateSmartCollectionOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation collectionCreate($input: CollectionInput!) {
      collectionCreate(input: $input) {
        collection { id title }
        userErrors { field message }
      }
    }
    """
    collection_input: dict[str, Any] = {
        "title": title,
        "ruleSet": {
            "appliedDisjunctively": disjunctive,
            "rules": rules,
        },
    }
    try:
        result = await _graphql(shop_id, headers, query, {"input": collection_input})
        data = result.get("data", {}).get("collectionCreate", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return CreateSmartCollectionOutput(success=False, error=ue[0].message, user_errors=ue)
        coll = data.get("collection") or {}
        return CreateSmartCollectionOutput(success=True, collection_id=coll.get("id"), title=coll.get("title"), user_errors=ue)
    except Exception as exc:
        return CreateSmartCollectionOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=DeleteArticleInput)
@serialize_pydantic_return
async def delete_article(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    article_id: str,
) -> DeleteArticleOutput:
    """Delete an existing blog article."""
    if _cred_err := _check_credentials(auth_data):
        return DeleteArticleOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation articleDelete($id: ID!) {
      articleDelete(id: $id) {
        deletedArticleId
        userErrors { field message }
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"id": article_id})
        data = result.get("data", {}).get("articleDelete", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return DeleteArticleOutput(success=False, error=ue[0].message, user_errors=ue)
        return DeleteArticleOutput(success=True, deleted_article_id=data.get("deletedArticleId"), user_errors=ue)
    except Exception as exc:
        return DeleteArticleOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=DeleteBlogInput)
@serialize_pydantic_return
async def delete_blog(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    blog_id: str,
) -> DeleteBlogOutput:
    """Delete an existing blog."""
    if _cred_err := _check_credentials(auth_data):
        return DeleteBlogOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation blogDelete($id: ID!) {
      blogDelete(id: $id) {
        deletedBlogId
        userErrors { field message }
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"id": blog_id})
        data = result.get("data", {}).get("blogDelete", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return DeleteBlogOutput(success=False, error=ue[0].message, user_errors=ue)
        return DeleteBlogOutput(success=True, deleted_blog_id=data.get("deletedBlogId"), user_errors=ue)
    except Exception as exc:
        return DeleteBlogOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=DeleteMetafieldInput)
@serialize_pydantic_return
async def delete_metafield(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    metafield_id: str,
) -> DeleteMetafieldOutput:
    """Delete a metafield belonging to a resource."""
    if _cred_err := _check_credentials(auth_data):
        return DeleteMetafieldOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation metafieldsDelete($metafields: [MetafieldIdentifierInput!]!) {
      metafieldsDelete(metafields: $metafields) {
        deletedMetafields { key namespace ownerId }
        userErrors { field message }
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"metafields": [{"id": metafield_id}]})
        data = result.get("data", {}).get("metafieldsDelete", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return DeleteMetafieldOutput(success=False, error=ue[0].message, user_errors=ue)
        deleted = data.get("deletedMetafields") or []
        return DeleteMetafieldOutput(success=True, deleted_metafields=deleted, user_errors=ue)
    except Exception as exc:
        return DeleteMetafieldOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=DeletePageInput)
@serialize_pydantic_return
async def delete_page(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    page_id: str,
) -> DeletePageOutput:
    """Delete an existing page."""
    if _cred_err := _check_credentials(auth_data):
        return DeletePageOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation pageDelete($id: ID!) {
      pageDelete(id: $id) {
        deletedPageId
        userErrors { field message }
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"id": page_id})
        data = result.get("data", {}).get("pageDelete", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return DeletePageOutput(success=False, error=ue[0].message, user_errors=ue)
        return DeletePageOutput(success=True, deleted_page_id=data.get("deletedPageId"), user_errors=ue)
    except Exception as exc:
        return DeletePageOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=GetArticlesInput)
@serialize_pydantic_return
async def get_articles(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    blog_id: str,
    max_results: int = 100,
) -> GetArticlesOutput:
    """Retrieve a list of articles from a blog."""
    if _cred_err := _check_credentials(auth_data):
        return GetArticlesOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    first = min(max_results, 250)
    query = """
    query articles($blogId: ID!, $first: Int!) {
      blog(id: $blogId) {
        articles(first: $first) {
          nodes { id title handle body summary tags createdAt updatedAt }
        }
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"blogId": blog_id, "first": first})
        blog = result.get("data", {}).get("blog") or {}
        articles_data = blog.get("articles", {}).get("nodes") or []
        return GetArticlesOutput(success=True, articles=articles_data)
    except Exception as exc:
        return GetArticlesOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=GetAssignedFulfillmentOrdersInput)
@serialize_pydantic_return
async def get_assigned_fulfillment_orders(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    max_results: int = 100,
) -> GetAssignedFulfillmentOrdersOutput:
    """Retrieve fulfillment orders assigned to a merchant location."""
    if _cred_err := _check_credentials(auth_data):
        return GetAssignedFulfillmentOrdersOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    first = min(max_results, 250)
    query = """
    query assignedFulfillmentOrders($first: Int!) {
      assignedFulfillmentOrders(first: $first) {
        nodes { id status createdAt updatedAt requestStatus }
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"first": first})
        nodes = result.get("data", {}).get("assignedFulfillmentOrders", {}).get("nodes") or []
        return GetAssignedFulfillmentOrdersOutput(success=True, fulfillment_orders=nodes)
    except Exception as exc:
        return GetAssignedFulfillmentOrdersOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=GetCustomerInput)
@serialize_pydantic_return
async def get_customer(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    customer_id: str,
) -> GetCustomerOutput:
    """Retrieve a single customer by ID."""
    if _cred_err := _check_credentials(auth_data):
        return GetCustomerOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    query customer($id: ID!) {
      customer(id: $id) {
        id firstName lastName email state tags note
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"id": customer_id})
        c = result.get("data", {}).get("customer") or {}
        return GetCustomerOutput(
            success=True, customer_id=c.get("id"), first_name=c.get("firstName"),
            last_name=c.get("lastName"), email=c.get("email"), state=c.get("state"),
            tags=c.get("tags") or [], note=c.get("note"),
        )
    except Exception as exc:
        return GetCustomerOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=GetCustomersInput)
@serialize_pydantic_return
async def get_customers(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    query: str | None = None,
    sort_key: str | None = None,
    max_results: int = 100,
) -> GetCustomersOutput:
    """Retrieve a list of customers."""
    if _cred_err := _check_credentials(auth_data):
        return GetCustomersOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    first = min(max_results, 250)
    gql = """
    query customers($first: Int!, $query: String, $sortKey: CustomerSortKeys) {
      customers(first: $first, query: $query, sortKey: $sortKey) {
        nodes { id email firstName lastName phone state tags }
      }
    }
    """
    variables: dict[str, Any] = {"first": first}
    if query:
        variables["query"] = query
    if sort_key:
        variables["sortKey"] = sort_key
    try:
        result = await _graphql(shop_id, headers, gql, variables)
        nodes = result.get("data", {}).get("customers", {}).get("nodes") or []
        return GetCustomersOutput(success=True, customers=nodes)
    except Exception as exc:
        return GetCustomersOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=GetDraftOrderInput)
@serialize_pydantic_return
async def get_draft_order(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    draft_order_id: str,
) -> GetDraftOrderOutput:
    """Retrieve a single draft order by ID."""
    if _cred_err := _check_credentials(auth_data):
        return GetDraftOrderOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    query draftOrder($id: ID!) {
      draftOrder(id: $id) {
        id name status email invoiceUrl currencyCode
        totalPriceSet { shopMoney { amount } }
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"id": draft_order_id})
        d = result.get("data", {}).get("draftOrder") or {}
        total = (d.get("totalPriceSet") or {}).get("shopMoney", {}).get("amount")
        return GetDraftOrderOutput(
            success=True, draft_order_id=d.get("id"), name=d.get("name"), status=d.get("status"),
            email=d.get("email"), invoice_url=d.get("invoiceUrl"), total_price=total,
            currency_code=d.get("currencyCode"),
        )
    except Exception as exc:
        return GetDraftOrderOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=GetDraftOrdersInput)
@serialize_pydantic_return
async def get_draft_orders(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    query: str | None = None,
    sort_key: str | None = None,
    max_results: int = 100,
) -> GetDraftOrdersOutput:
    """Retrieve a list of draft orders."""
    if _cred_err := _check_credentials(auth_data):
        return GetDraftOrdersOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    first = min(max_results, 250)
    gql = """
    query draftOrders($first: Int!, $query: String, $sortKey: DraftOrderSortKeys) {
      draftOrders(first: $first, query: $query, sortKey: $sortKey) {
        nodes { id name status email createdAt updatedAt }
      }
    }
    """
    variables: dict[str, Any] = {"first": first}
    if query:
        variables["query"] = query
    if sort_key:
        variables["sortKey"] = sort_key
    try:
        result = await _graphql(shop_id, headers, gql, variables)
        nodes = result.get("data", {}).get("draftOrders", {}).get("nodes") or []
        return GetDraftOrdersOutput(success=True, draft_orders=nodes)
    except Exception as exc:
        return GetDraftOrdersOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=GetFulfillmentInput)
@serialize_pydantic_return
async def get_fulfillment(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    fulfillment_id: str,
) -> GetFulfillmentOutput:
    """Retrieve a fulfillment by ID including tracking info and status."""
    if _cred_err := _check_credentials(auth_data):
        return GetFulfillmentOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    query fulfillment($id: ID!) {
      fulfillment(id: $id) {
        id name status displayStatus totalQuantity createdAt
        trackingInfo { number url company }
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"id": fulfillment_id})
        f = result.get("data", {}).get("fulfillment") or {}
        return GetFulfillmentOutput(
            success=True, fulfillment_id=f.get("id"), name=f.get("name"), status=f.get("status"),
            display_status=f.get("displayStatus"), total_quantity=f.get("totalQuantity"),
            created_at=f.get("createdAt"), tracking_info=f.get("trackingInfo") or [],
        )
    except Exception as exc:
        return GetFulfillmentOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=GetFulfillmentOrderInput)
@serialize_pydantic_return
async def get_fulfillment_order(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    fulfillment_order_id: str,
) -> GetFulfillmentOrderOutput:
    """Retrieve a single fulfillment order by ID."""
    if _cred_err := _check_credentials(auth_data):
        return GetFulfillmentOrderOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    query fulfillmentOrder($id: ID!) {
      fulfillmentOrder(id: $id) {
        id status requestStatus createdAt
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"id": fulfillment_order_id})
        fo = result.get("data", {}).get("fulfillmentOrder") or {}
        return GetFulfillmentOrderOutput(
            success=True, fulfillment_order_id=fo.get("id"), status=fo.get("status"),
            request_status=fo.get("requestStatus"), created_at=fo.get("createdAt"),
        )
    except Exception as exc:
        return GetFulfillmentOrderOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=GetFulfillmentOrdersInput)
@serialize_pydantic_return
async def get_fulfillment_orders(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    query: str | None = None,
    include_closed: bool = False,
    max_results: int = 100,
) -> GetFulfillmentOrdersOutput:
    """Retrieve a list of fulfillment orders."""
    if _cred_err := _check_credentials(auth_data):
        return GetFulfillmentOrdersOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    first = min(max_results, 250)
    gql = """
    query fulfillmentOrders($first: Int!, $query: String, $includeClosed: Boolean) {
      fulfillmentOrders(first: $first, query: $query, includeClosed: $includeClosed) {
        nodes { id status createdAt requestStatus }
      }
    }
    """
    variables: dict[str, Any] = {"first": first, "includeClosed": include_closed}
    if query:
        variables["query"] = query
    try:
        result = await _graphql(shop_id, headers, gql, variables)
        nodes = result.get("data", {}).get("fulfillmentOrders", {}).get("nodes") or []
        return GetFulfillmentOrdersOutput(success=True, fulfillment_orders=nodes)
    except Exception as exc:
        return GetFulfillmentOrdersOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=GetMetafieldsInput)
@serialize_pydantic_return
async def get_metafields(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    owner_resource: str,
    owner_id: str,
    namespace: list[str] | None = None,
    key: list[str] | None = None,
) -> GetMetafieldsOutput:
    """Retrieve metafields belonging to a resource."""
    if _cred_err := _check_credentials(auth_data):
        return GetMetafieldsOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    gql = """
    query metafields($ownerId: ID!, $namespace: String, $first: Int!) {
      node(id: $ownerId) {
        ... on HasMetafields {
          metafields(first: $first, namespace: $namespace) {
            nodes { id key namespace value type }
          }
        }
      }
    }
    """
    variables: dict[str, Any] = {"ownerId": owner_id, "first": 250}
    if namespace and len(namespace) == 1:
        variables["namespace"] = namespace[0]
    try:
        result = await _graphql(shop_id, headers, gql, variables)
        node = result.get("data", {}).get("node") or {}
        metafields = node.get("metafields", {}).get("nodes") or []
        if key:
            metafields = [m for m in metafields if m.get("key") in key]
        return GetMetafieldsOutput(success=True, metafields=metafields)
    except Exception as exc:
        return GetMetafieldsOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=GetMetaobjectsInput)
@serialize_pydantic_return
async def get_metaobjects(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    type: str,
) -> GetMetaobjectsOutput:
    """Retrieve a list of metaobjects by type."""
    if _cred_err := _check_credentials(auth_data):
        return GetMetaobjectsOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    query metaobjects($type: String!, $first: Int!) {
      metaobjects(type: $type, first: $first) {
        nodes { id handle type displayName updatedAt fields { key type value } }
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"type": type, "first": 250})
        nodes = result.get("data", {}).get("metaobjects", {}).get("nodes") or []
        return GetMetaobjectsOutput(success=True, metaobjects=nodes)
    except Exception as exc:
        return GetMetaobjectsOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=GetPagesInput)
@serialize_pydantic_return
async def get_pages(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    max_results: int = 100,
) -> GetPagesOutput:
    """Retrieve a list of all pages."""
    if _cred_err := _check_credentials(auth_data):
        return GetPagesOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    first = min(max_results, 250)
    query = """
    query pages($first: Int!) {
      pages(first: $first) {
        nodes { id title handle body bodySummary createdAt updatedAt }
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"first": first})
        nodes = result.get("data", {}).get("pages", {}).get("nodes") or []
        return GetPagesOutput(success=True, pages=nodes)
    except Exception as exc:
        return GetPagesOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=SearchCustomCollectionByNameInput)
@serialize_pydantic_return
async def search_custom_collection_by_name(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    title: str | None = None,
    exact_match: bool = False,
    max_results: int = 100,
    sort_key: str | None = None,
) -> SearchCustomCollectionByNameOutput:
    """Search for a custom collection by name or title."""
    if _cred_err := _check_credentials(auth_data):
        return SearchCustomCollectionByNameOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    first = min(max_results, 250)
    gql = """
    query collections($first: Int!, $query: String, $sortKey: CollectionSortKeys) {
      collections(first: $first, query: $query, sortKey: $sortKey) {
        nodes { id title handle description }
      }
    }
    """
    variables: dict[str, Any] = {"first": first}
    if title:
        variables["query"] = f"title:{title}"
    if sort_key:
        variables["sortKey"] = sort_key
    try:
        result = await _graphql(shop_id, headers, gql, variables)
        nodes = result.get("data", {}).get("collections", {}).get("nodes") or []
        if exact_match and title:
            nodes = [n for n in nodes if n.get("title") == title]
        return SearchCustomCollectionByNameOutput(success=True, collections=nodes)
    except Exception as exc:
        return SearchCustomCollectionByNameOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=SearchOrdersInput)
@serialize_pydantic_return
async def search_orders(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    query: str | None = None,
    sort_key: str | None = None,
    max_results: int | None = None,
) -> SearchOrdersOutput:
    """Search for orders."""
    if _cred_err := _check_credentials(auth_data):
        return SearchOrdersOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    first = min(max_results or 250, 250)
    gql = """
    query orders($first: Int!, $query: String, $sortKey: OrderSortKeys) {
      orders(first: $first, query: $query, sortKey: $sortKey) {
        nodes { id name createdAt displayFinancialStatus displayFulfillmentStatus tags }
      }
    }
    """
    variables: dict[str, Any] = {"first": first}
    if query:
        variables["query"] = query
    if sort_key:
        variables["sortKey"] = sort_key
    try:
        result = await _graphql(shop_id, headers, gql, variables)
        nodes = result.get("data", {}).get("orders", {}).get("nodes") or []
        return SearchOrdersOutput(success=True, orders=nodes)
    except Exception as exc:
        return SearchOrdersOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=SearchProductVariantInput)
@serialize_pydantic_return
async def search_product_variant(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    product_id: str,
    product_variant_id: str | None = None,
    title: str | None = None,
    create_if_not_found: bool = False,
    option_ids: list[str] | None = None,
    price: str | None = None,
) -> SearchProductVariantOutput:
    """Search for a product variant by ID or title, optionally creating if not found."""
    if _cred_err := _check_credentials(auth_data):
        return SearchProductVariantOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    if product_variant_id:
        query = """
        query productVariant($id: ID!) {
          productVariant(id: $id) { id title }
        }
        """
        try:
            result = await _graphql(shop_id, headers, query, {"id": product_variant_id})
            v = result.get("data", {}).get("productVariant") or {}
            if v.get("id"):
                return SearchProductVariantOutput(success=True, variant_id=v.get("id"), title=v.get("title"))
        except Exception as exc:
            return SearchProductVariantOutput(success=False, error=f"Request failed: {exc}")
    if title:
        query = """
        query productVariants($productId: ID!, $first: Int!) {
          product(id: $productId) {
            variants(first: $first) { nodes { id title } }
          }
        }
        """
        try:
            result = await _graphql(shop_id, headers, query, {"productId": product_id, "first": 250})
            variants = result.get("data", {}).get("product", {}).get("variants", {}).get("nodes") or []
            for v in variants:
                if v.get("title") == title:
                    return SearchProductVariantOutput(success=True, variant_id=v.get("id"), title=v.get("title"))
        except Exception as exc:
            return SearchProductVariantOutput(success=False, error=f"Request failed: {exc}")
    if create_if_not_found and option_ids:
        create_query = """
        mutation productVariantsBulkCreate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
          productVariantsBulkCreate(productId: $productId, variants: $variants) {
            productVariants { id title }
            userErrors { field message }
          }
        }
        """
        variant_input: dict[str, Any] = {"optionValues": [{"id": oid} for oid in option_ids]}
        if price:
            variant_input["price"] = price
        try:
            result = await _graphql(shop_id, headers, create_query, {"productId": product_id, "variants": [variant_input]})
            data = result.get("data", {}).get("productVariantsBulkCreate", {})
            ue = _parse_user_errors(data.get("userErrors"))
            if ue:
                return SearchProductVariantOutput(success=False, error=ue[0].message, user_errors=ue)
            created_variants = data.get("productVariants") or []
            v = created_variants[0] if created_variants else {}
            return SearchProductVariantOutput(success=True, variant_id=v.get("id"), title=v.get("title"), created=True, user_errors=ue)
        except Exception as exc:
            return SearchProductVariantOutput(success=False, error=f"Request failed: {exc}")
    return SearchProductVariantOutput(success=False, error="Variant not found and create_if_not_found is False or no option_ids provided")


@tool(args_schema=SearchProductsInput)
@serialize_pydantic_return
async def search_products(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    title: str | None = None,
    exact_match: bool = False,
    product_ids: list[str] | None = None,
    collection_id: str | None = None,
    product_type: str | None = None,
    vendor: str | None = None,
    max_results: int = 100,
    sort_key: str | None = None,
) -> SearchProductsOutput:
    """Search for products."""
    if _cred_err := _check_credentials(auth_data):
        return SearchProductsOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    first = min(max_results, 250)
    gql = """
    query products($first: Int!, $query: String, $sortKey: ProductSortKeys) {
      products(first: $first, query: $query, sortKey: $sortKey) {
        nodes { id title handle status vendor productType tags }
      }
    }
    """
    query_parts: list[str] = []
    if title:
        query_parts.append(f"title:*{title}*")
    if product_type:
        query_parts.append(f"product_type:{product_type}")
    if vendor:
        query_parts.append(f"vendor:{vendor}")
    if collection_id:
        query_parts.append(f"collection_id:{collection_id}")
    if product_ids:
        for pid in product_ids:
            query_parts.append(f"id:{pid}")
    variables: dict[str, Any] = {"first": first}
    if query_parts:
        variables["query"] = " ".join(query_parts)
    if sort_key:
        variables["sortKey"] = sort_key
    try:
        result = await _graphql(shop_id, headers, gql, variables)
        nodes = result.get("data", {}).get("products", {}).get("nodes") or []
        if exact_match and title:
            nodes = [n for n in nodes if n.get("title") == title]
        return SearchProductsOutput(success=True, products=nodes)
    except Exception as exc:
        return SearchProductsOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=UpdateArticleInput)
@serialize_pydantic_return
async def update_article(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    article_id: str,
    title: str | None = None,
    body_html: str | None = None,
    author: str | None = None,
    summary: str | None = None,
    image_url: str | None = None,
    tags: list[str] | None = None,
) -> UpdateArticleOutput:
    """Update a blog article."""
    if _cred_err := _check_credentials(auth_data):
        return UpdateArticleOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation articleUpdate($id: ID!, $article: ArticleUpdateInput!) {
      articleUpdate(id: $id, article: $article) {
        article { id title handle body summary tags }
        userErrors { field message }
      }
    }
    """
    article_input: dict[str, Any] = {}
    if title is not None:
        article_input["title"] = title
    if body_html is not None:
        article_input["body"] = body_html
    if author is not None:
        article_input["author"] = {"name": author}
    if summary is not None:
        article_input["summary"] = summary
    if image_url is not None:
        article_input["image"] = {"url": image_url}
    if tags is not None:
        article_input["tags"] = tags
    try:
        result = await _graphql(shop_id, headers, query, {"id": article_id, "article": article_input})
        data = result.get("data", {}).get("articleUpdate", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return UpdateArticleOutput(success=False, error=ue[0].message, user_errors=ue)
        a = data.get("article") or {}
        return UpdateArticleOutput(
            success=True, article_id=a.get("id"), title=a.get("title"), handle=a.get("handle"),
            body=a.get("body"), summary=a.get("summary"), tags=a.get("tags") or [], user_errors=ue,
        )
    except Exception as exc:
        return UpdateArticleOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=UpdateInventoryLevelInput)
@serialize_pydantic_return
async def update_inventory_level(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    location_id: str,
    inventory_item_id: str,
    available: int,
    reason: str,
    reference_document_uri: str | None = None,
) -> UpdateInventoryLevelOutput:
    """Set the inventory level for an inventory item at a location."""
    if _cred_err := _check_credentials(auth_data):
        return UpdateInventoryLevelOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation inventorySetOnHandQuantities($input: InventorySetOnHandQuantitiesInput!) {
      inventorySetOnHandQuantities(input: $input) {
        inventoryAdjustmentGroup { createdAt reason referenceDocumentUri changes { name delta } }
        userErrors { field message }
      }
    }
    """
    inv_input: dict[str, Any] = {
        "reason": reason,
        "setQuantities": [{"inventoryItemId": inventory_item_id, "locationId": location_id, "quantity": available}],
    }
    if reference_document_uri:
        inv_input["referenceDocumentUri"] = reference_document_uri
    try:
        result = await _graphql(shop_id, headers, query, {"input": inv_input})
        data = result.get("data", {}).get("inventorySetOnHandQuantities", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return UpdateInventoryLevelOutput(success=False, error=ue[0].message, user_errors=ue)
        group = data.get("inventoryAdjustmentGroup") or {}
        return UpdateInventoryLevelOutput(
            success=True, created_at=group.get("createdAt"), reason=group.get("reason"),
            changes=group.get("changes") or [], user_errors=ue,
        )
    except Exception as exc:
        return UpdateInventoryLevelOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=UpdateMetafieldInput)
@serialize_pydantic_return
async def update_metafield(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    owner_id: str,
    metafield_id: str,
    value: str,
) -> UpdateMetafieldOutput:
    """Update a metafield belonging to a resource."""
    if _cred_err := _check_credentials(auth_data):
        return UpdateMetafieldOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation metafieldsSet($metafields: [MetafieldsSetInput!]!) {
      metafieldsSet(metafields: $metafields) {
        metafields { key namespace value createdAt updatedAt }
        userErrors { field message }
      }
    }
    """
    try:
        result = await _graphql(shop_id, headers, query, {"metafields": [{"id": metafield_id, "ownerId": owner_id, "value": value}]})
        data = result.get("data", {}).get("metafieldsSet", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return UpdateMetafieldOutput(success=False, error=ue[0].message, user_errors=ue)
        return UpdateMetafieldOutput(success=True, metafields=data.get("metafields") or [], user_errors=ue)
    except Exception as exc:
        return UpdateMetafieldOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=UpdateMetaobjectInput)
@serialize_pydantic_return
async def update_metaobject(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    metaobject_id: str,
    fields: list[dict[str, str]] | None = None,
) -> UpdateMetaobjectOutput:
    """Update a metaobject."""
    if _cred_err := _check_credentials(auth_data):
        return UpdateMetaobjectOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation metaobjectUpdate($id: ID!, $metaobject: MetaobjectUpdateInput!) {
      metaobjectUpdate(id: $id, metaobject: $metaobject) {
        metaobject { id type }
        userErrors { field message }
      }
    }
    """
    metaobject_input: dict[str, Any] = {}
    if fields:
        metaobject_input["fields"] = fields
    try:
        result = await _graphql(shop_id, headers, query, {"id": metaobject_id, "metaobject": metaobject_input})
        data = result.get("data", {}).get("metaobjectUpdate", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return UpdateMetaobjectOutput(success=False, error=ue[0].message, user_errors=ue)
        mo = data.get("metaobject") or {}
        return UpdateMetaobjectOutput(success=True, metaobject_id=mo.get("id"), type_name=mo.get("type"), user_errors=ue)
    except Exception as exc:
        return UpdateMetaobjectOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=UpdateOrderInput)
@serialize_pydantic_return
async def update_order(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    order_id: str,
    email: str | None = None,
    note: str | None = None,
    tags: list[str] | None = None,
    metafields: list[dict[str, Any]] | None = None,
) -> UpdateOrderOutput:
    """Update an existing order."""
    if _cred_err := _check_credentials(auth_data):
        return UpdateOrderOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation orderUpdate($input: OrderInput!) {
      orderUpdate(input: $input) {
        order { id name email tags note }
        userErrors { field message }
      }
    }
    """
    order_input: dict[str, Any] = {"id": order_id}
    if email is not None:
        order_input["email"] = email
    if note is not None:
        order_input["note"] = note
    if tags is not None:
        order_input["tags"] = tags
    if metafields:
        order_input["metafields"] = metafields
    try:
        result = await _graphql(shop_id, headers, query, {"input": order_input})
        data = result.get("data", {}).get("orderUpdate", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return UpdateOrderOutput(success=False, error=ue[0].message, user_errors=ue)
        o = data.get("order") or {}
        return UpdateOrderOutput(
            success=True, order_id=o.get("id"), name=o.get("name"), email=o.get("email"),
            tags=o.get("tags") or [], note=o.get("note"), user_errors=ue,
        )
    except Exception as exc:
        return UpdateOrderOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=UpdatePageInput)
@serialize_pydantic_return
async def update_page(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    page_id: str,
    title: str | None = None,
    body: str | None = None,
) -> UpdatePageOutput:
    """Update an existing page."""
    if _cred_err := _check_credentials(auth_data):
        return UpdatePageOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation pageUpdate($id: ID!, $page: PageUpdateInput!) {
      pageUpdate(id: $id, page: $page) {
        page { id title handle }
        userErrors { field message }
      }
    }
    """
    page_input: dict[str, Any] = {}
    if title is not None:
        page_input["title"] = title
    if body is not None:
        page_input["body"] = body
    try:
        result = await _graphql(shop_id, headers, query, {"id": page_id, "page": page_input})
        data = result.get("data", {}).get("pageUpdate", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return UpdatePageOutput(success=False, error=ue[0].message, user_errors=ue)
        p = data.get("page") or {}
        return UpdatePageOutput(success=True, page_id=p.get("id"), title=p.get("title"), handle=p.get("handle"), user_errors=ue)
    except Exception as exc:
        return UpdatePageOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=UpdateProductInput)
@serialize_pydantic_return
async def update_product(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    product_id: str,
    title: str | None = None,
    product_description: str | None = None,
    vendor: str | None = None,
    product_type: str | None = None,
    status: str | None = None,
    images: list[str] | None = None,
    tags: list[str] | None = None,
    metafields: list[dict[str, Any]] | None = None,
    handle: str | None = None,
    seo_title: str | None = None,
    seo_description: str | None = None,
) -> UpdateProductOutput:
    """Update an existing product."""
    if _cred_err := _check_credentials(auth_data):
        return UpdateProductOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation productUpdate($input: ProductInput!, $media: [CreateMediaInput!]) {
      productUpdate(input: $input, media: $media) {
        product { id title }
        userErrors { field message }
      }
    }
    """
    product_input: dict[str, Any] = {"id": product_id}
    if title is not None:
        product_input["title"] = title
    if product_description is not None:
        product_input["descriptionHtml"] = product_description
    if vendor is not None:
        product_input["vendor"] = vendor
    if product_type is not None:
        product_input["productType"] = product_type
    if status is not None:
        product_input["status"] = status
    if tags is not None:
        product_input["tags"] = tags
    if metafields:
        product_input["metafields"] = metafields
    if handle is not None:
        product_input["handle"] = handle
    seo: dict[str, str] = {}
    if seo_title is not None:
        seo["title"] = seo_title
    if seo_description is not None:
        seo["description"] = seo_description
    if seo:
        product_input["seo"] = seo
    media: list[dict[str, Any]] | None = None
    if images:
        media = [{"originalSource": url, "mediaContentType": "IMAGE"} for url in images]
    try:
        result = await _graphql(shop_id, headers, query, {"input": product_input, "media": media})
        data = result.get("data", {}).get("productUpdate", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return UpdateProductOutput(success=False, error=ue[0].message, user_errors=ue)
        p = data.get("product") or {}
        return UpdateProductOutput(success=True, product_id=p.get("id"), title=p.get("title"), user_errors=ue)
    except Exception as exc:
        return UpdateProductOutput(success=False, error=f"Request failed: {exc}")


@tool(args_schema=UpdateProductVariantInput)
@serialize_pydantic_return
async def update_product_variant(
    auth_type: str,
    auth_data: dict[str, Any],
    shop_id: str,
    product_id: str,
    product_variant_id: str,
    option_ids: list[str] | None = None,
    price: str | None = None,
    sku: str | None = None,
    barcode: str | None = None,
    weight: str | None = None,
    weight_unit: str | None = None,
    metafields: list[dict[str, Any]] | None = None,
) -> UpdateProductVariantOutput:
    """Update an existing product variant."""
    if _cred_err := _check_credentials(auth_data):
        return UpdateProductVariantOutput(success=False, error=_cred_err)
    headers = _get_auth_headers(auth_type, auth_data)
    query = """
    mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
      productVariantsBulkUpdate(productId: $productId, variants: $variants) {
        productVariants { id title }
        userErrors { field message }
      }
    }
    """
    variant: dict[str, Any] = {"id": product_variant_id}
    if option_ids:
        variant["optionValues"] = [{"id": oid} for oid in option_ids]
    if price is not None:
        variant["price"] = price
    if sku is not None:
        variant.setdefault("inventoryItem", {})["sku"] = sku
    if barcode is not None:
        variant["barcode"] = barcode
    if weight is not None and weight_unit is not None:
        variant.setdefault("inventoryItem", {})["measurement"] = {"weight": {"value": float(weight), "unit": weight_unit}}
    if metafields:
        variant["metafields"] = metafields
    try:
        result = await _graphql(shop_id, headers, query, {"productId": product_id, "variants": [variant]})
        data = result.get("data", {}).get("productVariantsBulkUpdate", {})
        ue = _parse_user_errors(data.get("userErrors"))
        if ue:
            return UpdateProductVariantOutput(success=False, error=ue[0].message, user_errors=ue)
        variants = data.get("productVariants") or []
        v = variants[0] if variants else {}
        return UpdateProductVariantOutput(success=True, variant_id=v.get("id"), title=v.get("title"), user_errors=ue)
    except Exception as exc:
        return UpdateProductVariantOutput(success=False, error=f"Request failed: {exc}")

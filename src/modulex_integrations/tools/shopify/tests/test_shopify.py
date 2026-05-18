"""Happy-path tests for every shopify @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.shopify import (
    TOOLS,
    add_product_to_custom_collection,
    add_tags,
    create_article,
    create_blog,
    create_custom_collection,
    create_metafield,
    create_metaobject,
    create_page,
    create_product,
    create_product_variant,
    create_smart_collection,
    delete_article,
    delete_blog,
    delete_metafield,
    delete_page,
    get_articles,
    get_assigned_fulfillment_orders,
    get_customer,
    get_customers,
    get_draft_order,
    get_draft_orders,
    get_fulfillment,
    get_fulfillment_order,
    get_fulfillment_orders,
    get_metafields,
    get_metaobjects,
    get_pages,
    manifest,
    search_custom_collection_by_name,
    search_orders,
    search_product_variant,
    search_products,
    update_article,
    update_inventory_level,
    update_metafield,
    update_metaobject,
    update_order,
    update_page,
    update_product,
    update_product_variant,
)
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
    UpdateArticleOutput,
    UpdateInventoryLevelOutput,
    UpdateMetafieldOutput,
    UpdateMetaobjectOutput,
    UpdateOrderOutput,
    UpdatePageOutput,
    UpdateProductOutput,
    UpdateProductVariantOutput,
)

API = "https://test-shop.myshopify.com/admin/api/2025-01/graphql.json"

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {"access_token": "shpat_fake_token", "shop_id": "test-shop"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, shop_id="test-shop", **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_39_actions(self) -> None:
        assert len(manifest.actions) == 39

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_add_product_to_custom_collection(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "collectionAddProductsV2": {
                    "job": {"done": True, "id": "gid://shopify/Job/1"},
                    "userErrors": [],
                }
            }
        },
    )
    result_dict = await add_product_to_custom_collection.ainvoke(
        _args(collection_id="gid://shopify/Collection/1", product_ids=["gid://shopify/Product/1"])
    )
    assert isinstance(result_dict, dict)
    result = AddProductToCustomCollectionOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_add_tags(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "tagsAdd": {
                    "node": {"id": "gid://shopify/Product/1"},
                    "userErrors": [],
                }
            }
        },
    )
    result_dict = await add_tags.ainvoke(
        _args(resource_type="Product", gid="gid://shopify/Product/1", tags=["sale"])
    )
    assert isinstance(result_dict, dict)
    result = AddTagsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_article(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "articleCreate": {
                    "article": {"id": "gid://shopify/Article/1", "title": "Test", "handle": "test", "body": "<p>hi</p>", "summary": None, "tags": []},
                    "userErrors": [],
                }
            }
        },
    )
    result_dict = await create_article.ainvoke(
        _args(blog_id="gid://shopify/Blog/1", title="Test", author="Author")
    )
    assert isinstance(result_dict, dict)
    result = CreateArticleOutput.model_validate(result_dict)
    assert result.success is True
    assert result.title == "Test"


@pytest.mark.asyncio
async def test_create_blog(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "blogCreate": {
                    "blog": {"id": "gid://shopify/Blog/1", "title": "My Blog", "handle": "my-blog"},
                    "userErrors": [],
                }
            }
        },
    )
    result_dict = await create_blog.ainvoke(_args(title="My Blog"))
    assert isinstance(result_dict, dict)
    result = CreateBlogOutput.model_validate(result_dict)
    assert result.success is True
    assert result.title == "My Blog"


@pytest.mark.asyncio
async def test_create_page(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "pageCreate": {
                    "page": {"id": "gid://shopify/Page/1", "title": "About", "handle": "about"},
                    "userErrors": [],
                }
            }
        },
    )
    result_dict = await create_page.ainvoke(_args(title="About", body="<p>About us</p>"))
    assert isinstance(result_dict, dict)
    result = CreatePageOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_product(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "productCreate": {
                    "product": {"id": "gid://shopify/Product/1", "title": "Widget"},
                    "userErrors": [],
                }
            }
        },
    )
    result_dict = await create_product.ainvoke(_args(title="Widget"))
    assert isinstance(result_dict, dict)
    result = CreateProductOutput.model_validate(result_dict)
    assert result.success is True
    assert result.title == "Widget"


@pytest.mark.asyncio
async def test_delete_blog(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "blogDelete": {
                    "deletedBlogId": "gid://shopify/Blog/1",
                    "userErrors": [],
                }
            }
        },
    )
    result_dict = await delete_blog.ainvoke(_args(blog_id="gid://shopify/Blog/1"))
    assert isinstance(result_dict, dict)
    result = DeleteBlogOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted_blog_id == "gid://shopify/Blog/1"


@pytest.mark.asyncio
async def test_get_customer(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "customer": {
                    "id": "gid://shopify/Customer/1",
                    "firstName": "Jane",
                    "lastName": "Doe",
                    "email": "jane@example.com",
                    "state": "ENABLED",
                    "tags": ["vip"],
                    "note": None,
                }
            }
        },
    )
    result_dict = await get_customer.ainvoke(_args(customer_id="gid://shopify/Customer/1"))
    assert isinstance(result_dict, dict)
    result = GetCustomerOutput.model_validate(result_dict)
    assert result.success is True
    assert result.first_name == "Jane"


@pytest.mark.asyncio
async def test_get_pages(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "pages": {
                    "nodes": [
                        {"id": "gid://shopify/Page/1", "title": "About", "handle": "about", "body": "<p>hi</p>", "bodySummary": "hi", "createdAt": "2025-01-01", "updatedAt": "2025-01-01"},
                    ]
                }
            }
        },
    )
    result_dict = await get_pages.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = GetPagesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.pages) == 1


@pytest.mark.asyncio
async def test_search_products(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "products": {
                    "nodes": [
                        {"id": "gid://shopify/Product/1", "title": "Widget", "handle": "widget", "status": "ACTIVE", "vendor": "Acme", "productType": "Gadget", "tags": []},
                    ]
                }
            }
        },
    )
    result_dict = await search_products.ainvoke(_args(title="Widget"))
    assert isinstance(result_dict, dict)
    result = SearchProductsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.products) == 1


@pytest.mark.asyncio
async def test_update_order(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "orderUpdate": {
                    "order": {"id": "gid://shopify/Order/1", "name": "#1001", "email": "new@example.com", "tags": ["updated"], "note": "test note"},
                    "userErrors": [],
                }
            }
        },
    )
    result_dict = await update_order.ainvoke(
        _args(order_id="gid://shopify/Order/1", email="new@example.com", note="test note")
    )
    assert isinstance(result_dict, dict)
    result = UpdateOrderOutput.model_validate(result_dict)
    assert result.success is True
    assert result.email == "new@example.com"


@pytest.mark.asyncio
async def test_create_custom_collection(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"collectionCreate": {"collection": {"id": "gid://shopify/Collection/1", "title": "Summer"}, "userErrors": []}}},
    )
    result_dict = await create_custom_collection.ainvoke(_args(title="Summer"))
    assert isinstance(result_dict, dict)
    result = CreateCustomCollectionOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_metafield(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"metafieldDefinitionCreate": {"createdDefinition": {"id": "gid://shopify/MetafieldDefinition/1", "name": "Color"}, "userErrors": []}}},
    )
    result_dict = await create_metafield.ainvoke(
        _args(owner_resource="PRODUCT", name="Color", namespace="custom", key="color", type="single_line_text_field")
    )
    assert isinstance(result_dict, dict)
    result = CreateMetafieldOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_metaobject(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"metaobjectCreate": {"metaobject": {"id": "gid://shopify/Metaobject/1", "handle": "test", "type": "lookbook"}, "userErrors": []}}},
    )
    result_dict = await create_metaobject.ainvoke(_args(type="lookbook"))
    assert isinstance(result_dict, dict)
    result = CreateMetaobjectOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_product_variant(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"productVariantsBulkCreate": {"productVariants": [{"id": "gid://shopify/ProductVariant/1", "title": "Small"}], "userErrors": []}}},
    )
    result_dict = await create_product_variant.ainvoke(
        _args(product_id="gid://shopify/Product/1", option_ids=["gid://shopify/ProductOptionValue/1"])
    )
    assert isinstance(result_dict, dict)
    result = CreateProductVariantOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_smart_collection(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"collectionCreate": {"collection": {"id": "gid://shopify/Collection/2", "title": "Sale"}, "userErrors": []}}},
    )
    result_dict = await create_smart_collection.ainvoke(
        _args(title="Sale", rules=[{"column": "TAG", "relation": "EQUALS", "condition": "sale"}])
    )
    assert isinstance(result_dict, dict)
    result = CreateSmartCollectionOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_article(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"articleDelete": {"deletedArticleId": "gid://shopify/Article/1", "userErrors": []}}},
    )
    result_dict = await delete_article.ainvoke(_args(article_id="gid://shopify/Article/1"))
    assert isinstance(result_dict, dict)
    result = DeleteArticleOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_metafield(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"metafieldsDelete": {"deletedMetafields": [{"key": "color", "namespace": "custom", "ownerId": "gid://shopify/Product/1"}], "userErrors": []}}},
    )
    result_dict = await delete_metafield.ainvoke(_args(metafield_id="gid://shopify/Metafield/1"))
    assert isinstance(result_dict, dict)
    result = DeleteMetafieldOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_page(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"pageDelete": {"deletedPageId": "gid://shopify/Page/1", "userErrors": []}}},
    )
    result_dict = await delete_page.ainvoke(_args(page_id="gid://shopify/Page/1"))
    assert isinstance(result_dict, dict)
    result = DeletePageOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_articles(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"blog": {"articles": {"nodes": [{"id": "gid://shopify/Article/1", "title": "Post", "handle": "post", "body": "", "summary": None, "tags": [], "createdAt": "2025-01-01", "updatedAt": "2025-01-01"}]}}}},
    )
    result_dict = await get_articles.ainvoke(_args(blog_id="gid://shopify/Blog/1"))
    assert isinstance(result_dict, dict)
    result = GetArticlesOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_assigned_fulfillment_orders(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"assignedFulfillmentOrders": {"nodes": [{"id": "gid://shopify/FulfillmentOrder/1", "status": "OPEN", "createdAt": "2025-01-01", "updatedAt": "2025-01-01", "requestStatus": "UNSUBMITTED"}]}}},
    )
    result_dict = await get_assigned_fulfillment_orders.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = GetAssignedFulfillmentOrdersOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_customers(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"customers": {"nodes": [{"id": "gid://shopify/Customer/1", "email": "j@e.com", "firstName": "J", "lastName": "D", "phone": None, "state": "ENABLED", "tags": []}]}}},
    )
    result_dict = await get_customers.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = GetCustomersOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_draft_order(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"draftOrder": {"id": "gid://shopify/DraftOrder/1", "name": "#D1", "status": "OPEN", "email": "j@e.com", "invoiceUrl": None, "currencyCode": "USD", "totalPriceSet": {"shopMoney": {"amount": "10.00"}}}}},
    )
    result_dict = await get_draft_order.ainvoke(_args(draft_order_id="gid://shopify/DraftOrder/1"))
    assert isinstance(result_dict, dict)
    result = GetDraftOrderOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_draft_orders(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"draftOrders": {"nodes": [{"id": "gid://shopify/DraftOrder/1", "name": "#D1", "status": "OPEN", "email": "j@e.com", "createdAt": "2025-01-01", "updatedAt": "2025-01-01"}]}}},
    )
    result_dict = await get_draft_orders.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = GetDraftOrdersOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_fulfillment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"fulfillment": {"id": "gid://shopify/Fulfillment/1", "name": "#1.1", "status": "SUCCESS", "displayStatus": "FULFILLED", "totalQuantity": 2, "createdAt": "2025-01-01", "trackingInfo": []}}},
    )
    result_dict = await get_fulfillment.ainvoke(_args(fulfillment_id="gid://shopify/Fulfillment/1"))
    assert isinstance(result_dict, dict)
    result = GetFulfillmentOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_fulfillment_order(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"fulfillmentOrder": {"id": "gid://shopify/FulfillmentOrder/1", "status": "OPEN", "requestStatus": "UNSUBMITTED", "createdAt": "2025-01-01"}}},
    )
    result_dict = await get_fulfillment_order.ainvoke(_args(fulfillment_order_id="gid://shopify/FulfillmentOrder/1"))
    assert isinstance(result_dict, dict)
    result = GetFulfillmentOrderOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_fulfillment_orders(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"fulfillmentOrders": {"nodes": [{"id": "gid://shopify/FulfillmentOrder/1", "status": "OPEN", "createdAt": "2025-01-01", "requestStatus": "UNSUBMITTED"}]}}},
    )
    result_dict = await get_fulfillment_orders.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = GetFulfillmentOrdersOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_metafields(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"node": {"metafields": {"nodes": [{"id": "gid://shopify/Metafield/1", "key": "color", "namespace": "custom", "value": "red", "type": "single_line_text_field"}]}}}},
    )
    result_dict = await get_metafields.ainvoke(_args(owner_resource="product", owner_id="gid://shopify/Product/1"))
    assert isinstance(result_dict, dict)
    result = GetMetafieldsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_metaobjects(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"metaobjects": {"nodes": [{"id": "gid://shopify/Metaobject/1", "handle": "test", "type": "lookbook", "displayName": "Test", "updatedAt": "2025-01-01", "fields": []}]}}},
    )
    result_dict = await get_metaobjects.ainvoke(_args(type="lookbook"))
    assert isinstance(result_dict, dict)
    result = GetMetaobjectsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_search_custom_collection_by_name(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"collections": {"nodes": [{"id": "gid://shopify/Collection/1", "title": "Summer", "handle": "summer", "description": ""}]}}},
    )
    result_dict = await search_custom_collection_by_name.ainvoke(_args(title="Summer"))
    assert isinstance(result_dict, dict)
    result = SearchCustomCollectionByNameOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_search_orders(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"orders": {"nodes": [{"id": "gid://shopify/Order/1", "name": "#1001", "createdAt": "2025-01-01", "displayFinancialStatus": "PAID", "displayFulfillmentStatus": "FULFILLED", "tags": []}]}}},
    )
    result_dict = await search_orders.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = SearchOrdersOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_search_product_variant(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"productVariant": {"id": "gid://shopify/ProductVariant/1", "title": "Small"}}},
    )
    result_dict = await search_product_variant.ainvoke(
        _args(product_id="gid://shopify/Product/1", product_variant_id="gid://shopify/ProductVariant/1")
    )
    assert isinstance(result_dict, dict)
    result = SearchProductVariantOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_article(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"articleUpdate": {"article": {"id": "gid://shopify/Article/1", "title": "Updated", "handle": "updated", "body": "<p>new</p>", "summary": None, "tags": []}, "userErrors": []}}},
    )
    result_dict = await update_article.ainvoke(_args(article_id="gid://shopify/Article/1", title="Updated"))
    assert isinstance(result_dict, dict)
    result = UpdateArticleOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_inventory_level(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"inventorySetOnHandQuantities": {"inventoryAdjustmentGroup": {"createdAt": "2025-01-01", "reason": "correction", "referenceDocumentUri": None, "changes": [{"name": "available", "delta": 10}]}, "userErrors": []}}},
    )
    result_dict = await update_inventory_level.ainvoke(
        _args(location_id="gid://shopify/Location/1", inventory_item_id="gid://shopify/InventoryItem/1", available=10, reason="correction")
    )
    assert isinstance(result_dict, dict)
    result = UpdateInventoryLevelOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_metafield(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"metafieldsSet": {"metafields": [{"key": "color", "namespace": "custom", "value": "blue", "createdAt": "2025-01-01", "updatedAt": "2025-01-02"}], "userErrors": []}}},
    )
    result_dict = await update_metafield.ainvoke(
        _args(owner_id="gid://shopify/Product/1", metafield_id="gid://shopify/Metafield/1", value="blue")
    )
    assert isinstance(result_dict, dict)
    result = UpdateMetafieldOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_metaobject(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"metaobjectUpdate": {"metaobject": {"id": "gid://shopify/Metaobject/1", "type": "lookbook"}, "userErrors": []}}},
    )
    result_dict = await update_metaobject.ainvoke(_args(metaobject_id="gid://shopify/Metaobject/1"))
    assert isinstance(result_dict, dict)
    result = UpdateMetaobjectOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_page(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"pageUpdate": {"page": {"id": "gid://shopify/Page/1", "title": "Updated", "handle": "updated"}, "userErrors": []}}},
    )
    result_dict = await update_page.ainvoke(_args(page_id="gid://shopify/Page/1", title="Updated"))
    assert isinstance(result_dict, dict)
    result = UpdatePageOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_product(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"productUpdate": {"product": {"id": "gid://shopify/Product/1", "title": "Updated Widget"}, "userErrors": []}}},
    )
    result_dict = await update_product.ainvoke(_args(product_id="gid://shopify/Product/1", title="Updated Widget"))
    assert isinstance(result_dict, dict)
    result = UpdateProductOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_product_variant(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"productVariantsBulkUpdate": {"productVariants": [{"id": "gid://shopify/ProductVariant/1", "title": "Large"}], "userErrors": []}}},
    )
    result_dict = await update_product_variant.ainvoke(
        _args(product_id="gid://shopify/Product/1", product_variant_id="gid://shopify/ProductVariant/1", price="19.99")
    )
    assert isinstance(result_dict, dict)
    result = UpdateProductVariantOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_product_empty_credentials():  # type: ignore[no-untyped-def]
    """Failure-path: empty credentials should return success=False without hitting the wire."""
    result_dict = await create_product.ainvoke(
        _args(auth_data={}, title="Widget")
    )
    assert isinstance(result_dict, dict)
    result = CreateProductOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "token" in result.error.lower() or "credential" in result.error.lower()

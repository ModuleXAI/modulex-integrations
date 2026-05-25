"""Shopify integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="shopify",
    display_name="Shopify",
    description="E-commerce platform for managing products, orders, customers, and content via the Shopify Admin GraphQL API",
    version="1.0.0",
    author="ModuleX",
    logo="logos:shopify",
    app_url="https://www.shopify.com",
    categories=["E-Commerce", "Retail", "Inventory Management"],
    actions=[
        ActionDefinition(
            name="add_product_to_custom_collection",
            description="Add one or more products to a custom collection",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain (e.g. 'my-store' from my-store.myshopify.com)",
                    required=True,
                ),
                "collection_id": ParameterDef(
                    type="string",
                    description="The Shopify GID of the custom collection",
                    required=True,
                ),
                "product_ids": ParameterDef(
                    type="array",
                    description="Array of product GID strings to add to the collection",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="add_tags",
            description="Add tags to a Shopify resource (Product, Customer, Order, DraftOrder, or Article)",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "resource_type": ParameterDef(
                    type="string",
                    description="The resource type. Allowed values: Product, Customer, Order, DraftOrder, Article",
                    required=True,
                ),
                "gid": ParameterDef(
                    type="string",
                    description="The Shopify Admin Resource GID",
                    required=True,
                ),
                "tags": ParameterDef(
                    type="array",
                    description="Array of tag strings to add",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_article",
            description="Create a new blog article",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "blog_id": ParameterDef(
                    type="string",
                    description="The GID of the blog to create the article in",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The title of the article",
                    required=True,
                ),
                "author": ParameterDef(
                    type="string",
                    description="The name of the author of the article",
                    required=True,
                ),
                "body": ParameterDef(
                    type="string",
                    description="The text content of the article, with HTML markup",
                ),
                "summary": ParameterDef(
                    type="string",
                    description="A summary of the article, with HTML markup",
                ),
                "image_url": ParameterDef(
                    type="string",
                    description="The URL of the image associated with the article",
                ),
                "tags": ParameterDef(
                    type="array",
                    description="Array of tag strings",
                ),
            },
        ),
        ActionDefinition(
            name="create_blog",
            description="Create a new blog",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The title of the blog",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_custom_collection",
            description="Create a new custom collection",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The name of the custom collection",
                    required=True,
                ),
                "products": ParameterDef(
                    type="array",
                    description="Array of product GID strings to include in the collection",
                ),
                "metafields": ParameterDef(
                    type="array",
                    description="Array of metafield objects, each with key, value, type, and namespace",
                ),
                "image_url": ParameterDef(
                    type="string",
                    description="The source URL of the collection image",
                ),
            },
        ),
        ActionDefinition(
            name="create_metafield",
            description="Create a metafield definition belonging to a resource",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "owner_resource": ParameterDef(
                    type="string",
                    description="The resource type. Allowed values: BLOG, COLLECTION, PAGE, PRODUCT, VARIANTS, ARTICLE",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="The human-readable name for the metafield definition",
                    required=True,
                ),
                "namespace": ParameterDef(
                    type="string",
                    description="A container for a group of metafields (3-255 characters)",
                    required=True,
                ),
                "key": ParameterDef(
                    type="string",
                    description="The key of the metafield (up to 64 characters)",
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description="The metafield data type (e.g. single_line_text_field, number_integer, json, boolean, url, color)",
                    required=True,
                ),
                "pin": ParameterDef(
                    type="boolean",
                    description="Whether to pin the metafield definition",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="create_metaobject",
            description="Create a metaobject",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description="The metaobject type (Shopify GID or type name)",
                    required=True,
                ),
                "fields": ParameterDef(
                    type="array",
                    description="Array of field objects, each with 'key' and 'value' strings",
                ),
            },
        ),
        ActionDefinition(
            name="create_page",
            description="Create a new page",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The title of the page",
                    required=True,
                ),
                "body": ParameterDef(
                    type="string",
                    description="The text content of the page, with HTML markup",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_product",
            description="Create a new product",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="Title of the new product",
                    required=True,
                ),
                "product_description": ParameterDef(
                    type="string",
                    description="A description of the product (supports HTML)",
                ),
                "vendor": ParameterDef(
                    type="string",
                    description="The name of the product's vendor",
                ),
                "product_type": ParameterDef(
                    type="string",
                    description="A categorization for the product",
                ),
                "status": ParameterDef(
                    type="string",
                    description="The product status. Allowed values: ACTIVE, ARCHIVED, DRAFT",
                ),
                "images": ParameterDef(
                    type="array",
                    description="Array of image URL strings",
                ),
                "options": ParameterDef(
                    type="array",
                    description="Array of option objects, each with 'name' (string) and 'values' (array of objects with 'name')",
                ),
                "tags": ParameterDef(
                    type="array",
                    description="Array of tag strings",
                ),
            },
        ),
        ActionDefinition(
            name="create_product_variant",
            description="Create a new product variant",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "product_id": ParameterDef(
                    type="string",
                    description="The GID of the product",
                    required=True,
                ),
                "option_ids": ParameterDef(
                    type="array",
                    description="Array of product option value GID strings",
                    required=True,
                ),
                "price": ParameterDef(
                    type="string",
                    description="The price of the product variant",
                ),
                "image_url": ParameterDef(
                    type="string",
                    description="The URL of an image for the variant",
                ),
                "sku": ParameterDef(
                    type="string",
                    description="A unique SKU for the product variant",
                ),
                "barcode": ParameterDef(
                    type="string",
                    description="The barcode, UPC, or ISBN number",
                ),
                "weight": ParameterDef(
                    type="string",
                    description="The weight of the variant (requires weight_unit)",
                ),
                "weight_unit": ParameterDef(
                    type="string",
                    description="Weight unit. Allowed values: KILOGRAMS, GRAMS, POUNDS, OUNCES",
                ),
                "metafields": ParameterDef(
                    type="array",
                    description="Array of metafield objects with key, value, type, namespace",
                ),
            },
        ),
        ActionDefinition(
            name="create_smart_collection",
            description="Create a smart collection with automated rules",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="Title of the smart collection",
                    required=True,
                ),
                "rules": ParameterDef(
                    type="array",
                    description="Array of rule objects with 'column' (TAG, TITLE, VENDOR, etc.), 'relation' (CONTAINS, EQUALS, etc.), and 'condition'",
                    required=True,
                ),
                "disjunctive": ParameterDef(
                    type="boolean",
                    description="If true, product matches any rule. If false, product must match all rules.",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="delete_article",
            description="Delete an existing blog article",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "article_id": ParameterDef(
                    type="string",
                    description="The GID of the article to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_blog",
            description="Delete an existing blog",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "blog_id": ParameterDef(
                    type="string",
                    description="The GID of the blog to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_metafield",
            description="Delete a metafield belonging to a resource",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "metafield_id": ParameterDef(
                    type="string",
                    description="The GID of the metafield to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_page",
            description="Delete an existing page",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "page_id": ParameterDef(
                    type="string",
                    description="The GID of the page to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_articles",
            description="Retrieve a list of articles from a blog",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "blog_id": ParameterDef(
                    type="string",
                    description="The GID of the blog",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="get_assigned_fulfillment_orders",
            description="Retrieve fulfillment orders assigned to a merchant location",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="get_customer",
            description="Retrieve a single customer by ID",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "customer_id": ParameterDef(
                    type="string",
                    description="The GID of the customer",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_customers",
            description="Retrieve a list of customers",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="Filter query string (e.g. email:customer@example.com or state:ENABLED)",
                ),
                "sort_key": ParameterDef(
                    type="string",
                    description="Sort key. Options: CREATED_AT, ID, NAME, ORDERS_COUNT, STATE, TOTAL_SPENT, UPDATED_AT",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="get_draft_order",
            description="Retrieve a single draft order by ID",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "draft_order_id": ParameterDef(
                    type="string",
                    description="The GID of the draft order",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_draft_orders",
            description="Retrieve a list of draft orders",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="Filter query (e.g. status:OPEN, tag:fraud)",
                ),
                "sort_key": ParameterDef(
                    type="string",
                    description="Sort key. Options: CREATED_AT, ID, NUMBER, STATUS, TOTAL_PRICE, UPDATED_AT, CUSTOMER_NAME",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="get_fulfillment",
            description="Retrieve a fulfillment by ID including tracking info and status",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "fulfillment_id": ParameterDef(
                    type="string",
                    description="The globally-unique GID of a fulfillment (e.g. gid://shopify/Fulfillment/1234567890)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_fulfillment_order",
            description="Retrieve a single fulfillment order by ID",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "fulfillment_order_id": ParameterDef(
                    type="string",
                    description="The GID of the fulfillment order",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_fulfillment_orders",
            description="Retrieve a list of fulfillment orders",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="Filter query (e.g. status:open)",
                ),
                "include_closed": ParameterDef(
                    type="boolean",
                    description="Whether to include closed fulfillment orders",
                    default=False,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="get_metafields",
            description="Retrieve metafields belonging to a resource",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "owner_resource": ParameterDef(
                    type="string",
                    description="The resource type. Allowed values: blog, collection, page, product, variants, article",
                    required=True,
                ),
                "owner_id": ParameterDef(
                    type="string",
                    description="The GID of the resource that owns the metafields",
                    required=True,
                ),
                "namespace": ParameterDef(
                    type="array",
                    description="Filter by namespace strings",
                ),
                "key": ParameterDef(
                    type="array",
                    description="Filter by key strings",
                ),
            },
        ),
        ActionDefinition(
            name="get_metaobjects",
            description="Retrieve a list of metaobjects by type",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description="The metaobject type name",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_pages",
            description="Retrieve a list of all pages",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="search_custom_collection_by_name",
            description="Search for a custom collection by name or title",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The name of the custom collection to search for",
                ),
                "exact_match": ParameterDef(
                    type="boolean",
                    description="Whether to require an exact title match",
                    default=False,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
                "sort_key": ParameterDef(
                    type="string",
                    description="Sort key. Options: ID, RELEVANCE, TITLE, UPDATED_AT",
                ),
            },
        ),
        ActionDefinition(
            name="search_orders",
            description="Search for orders",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="Search query using Shopify search syntax",
                ),
                "sort_key": ParameterDef(
                    type="string",
                    description="Sort key. Options: CREATED_AT, CUSTOMER_NAME, FINANCIAL_STATUS, FULFILLMENT_STATUS, ID, ORDER_NUMBER, PROCESSED_AT, TOTAL_PRICE, UPDATED_AT",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                ),
            },
        ),
        ActionDefinition(
            name="search_product_variant",
            description="Search for a product variant by ID or title, optionally creating if not found",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "product_id": ParameterDef(
                    type="string",
                    description="The GID of the product",
                    required=True,
                ),
                "product_variant_id": ParameterDef(
                    type="string",
                    description="The GID of the product variant (takes precedence over title)",
                ),
                "title": ParameterDef(
                    type="string",
                    description="The name of the product variant to search for",
                ),
                "create_if_not_found": ParameterDef(
                    type="boolean",
                    description="Create the variant if not found",
                    default=False,
                ),
                "option_ids": ParameterDef(
                    type="array",
                    description="Option value GID strings for creation",
                ),
                "price": ParameterDef(
                    type="string",
                    description="Price of the variant (used only when creating)",
                ),
            },
        ),
        ActionDefinition(
            name="search_products",
            description="Search for products",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The product title to search for",
                ),
                "exact_match": ParameterDef(
                    type="boolean",
                    description="Whether the title search should be an exact match",
                    default=False,
                ),
                "product_ids": ParameterDef(
                    type="array",
                    description="Array of product GID strings to filter by",
                ),
                "collection_id": ParameterDef(
                    type="string",
                    description="Filter by collection GID",
                ),
                "product_type": ParameterDef(
                    type="string",
                    description="Filter by product type",
                ),
                "vendor": ParameterDef(
                    type="string",
                    description="Filter by vendor name",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
                "sort_key": ParameterDef(
                    type="string",
                    description="Sort key. Options: CREATED_AT, ID, INVENTORY_TOTAL, PRODUCT_TYPE, PUBLISHED_AT, RELEVANCE, TITLE, UPDATED_AT, VENDOR",
                ),
            },
        ),
        ActionDefinition(
            name="update_article",
            description="Update a blog article",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "article_id": ParameterDef(
                    type="string",
                    description="The GID of the article to update",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The new title of the article",
                ),
                "body_html": ParameterDef(
                    type="string",
                    description="The text content with HTML markup",
                ),
                "author": ParameterDef(
                    type="string",
                    description="The name of the author",
                ),
                "summary": ParameterDef(
                    type="string",
                    description="A summary of the article",
                ),
                "image_url": ParameterDef(
                    type="string",
                    description="The URL of the article image",
                ),
                "tags": ParameterDef(
                    type="array",
                    description="Array of tag strings",
                ),
            },
        ),
        ActionDefinition(
            name="update_inventory_level",
            description="Set the inventory level for an inventory item at a location",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "location_id": ParameterDef(
                    type="string",
                    description="The GID of the location",
                    required=True,
                ),
                "inventory_item_id": ParameterDef(
                    type="string",
                    description="The GID of the inventory item",
                    required=True,
                ),
                "available": ParameterDef(
                    type="integer",
                    description="The available inventory quantity to set",
                    required=True,
                ),
                "reason": ParameterDef(
                    type="string",
                    description="The reason for the change. Values: correction, cycle_count_available, damaged, other, promotion, quality_control, received, restock, safety_stock, shrinkage",
                    required=True,
                ),
                "reference_document_uri": ParameterDef(
                    type="string",
                    description="A freeform URI representing why the change happened",
                ),
            },
        ),
        ActionDefinition(
            name="update_metafield",
            description="Update a metafield belonging to a resource",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "owner_id": ParameterDef(
                    type="string",
                    description="The GID of the resource that owns the metafield",
                    required=True,
                ),
                "metafield_id": ParameterDef(
                    type="string",
                    description="The GID of the metafield to update",
                    required=True,
                ),
                "value": ParameterDef(
                    type="string",
                    description="The new value for the metafield",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_metaobject",
            description="Update a metaobject",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "metaobject_id": ParameterDef(
                    type="string",
                    description="The GID of the metaobject to update",
                    required=True,
                ),
                "fields": ParameterDef(
                    type="array",
                    description="Array of field objects, each with 'key' and 'value' strings",
                ),
            },
        ),
        ActionDefinition(
            name="update_order",
            description="Update an existing order",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "order_id": ParameterDef(
                    type="string",
                    description="The GID of the order to update",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="The email address associated with the order",
                ),
                "note": ParameterDef(
                    type="string",
                    description="An optional note to attach to the order",
                ),
                "tags": ParameterDef(
                    type="array",
                    description="Array of tag strings",
                ),
                "metafields": ParameterDef(
                    type="array",
                    description="Array of metafield objects with key, value, type, namespace",
                ),
            },
        ),
        ActionDefinition(
            name="update_page",
            description="Update an existing page",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "page_id": ParameterDef(
                    type="string",
                    description="The GID of the page to update",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The new title of the page",
                ),
                "body": ParameterDef(
                    type="string",
                    description="The text content with HTML markup",
                ),
            },
        ),
        ActionDefinition(
            name="update_product",
            description="Update an existing product",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "product_id": ParameterDef(
                    type="string",
                    description="The GID of the product to update",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The new title of the product",
                ),
                "product_description": ParameterDef(
                    type="string",
                    description="A description of the product (supports HTML)",
                ),
                "vendor": ParameterDef(
                    type="string",
                    description="The name of the product's vendor",
                ),
                "product_type": ParameterDef(
                    type="string",
                    description="A categorization for the product",
                ),
                "status": ParameterDef(
                    type="string",
                    description="Product status. Allowed values: ACTIVE, ARCHIVED, DRAFT",
                ),
                "images": ParameterDef(
                    type="array",
                    description="Array of image URL strings",
                ),
                "tags": ParameterDef(
                    type="array",
                    description="Array of tag strings",
                ),
                "metafields": ParameterDef(
                    type="array",
                    description="Array of metafield objects with key, value, type, namespace",
                ),
                "handle": ParameterDef(
                    type="string",
                    description="A unique human-friendly URL handle",
                ),
                "seo_title": ParameterDef(
                    type="string",
                    description="The product title for SEO",
                ),
                "seo_description": ParameterDef(
                    type="string",
                    description="The product description for SEO",
                ),
            },
        ),
        ActionDefinition(
            name="update_product_variant",
            description="Update an existing product variant",
            parameters={
                "shop_id": ParameterDef(
                    type="string",
                    description="The Shopify store subdomain",
                    required=True,
                ),
                "product_id": ParameterDef(
                    type="string",
                    description="The GID of the product",
                    required=True,
                ),
                "product_variant_id": ParameterDef(
                    type="string",
                    description="The GID of the product variant to update",
                    required=True,
                ),
                "option_ids": ParameterDef(
                    type="array",
                    description="Array of product option value GID strings",
                ),
                "price": ParameterDef(
                    type="string",
                    description="The price of the variant",
                ),
                "sku": ParameterDef(
                    type="string",
                    description="A unique SKU for the variant",
                ),
                "barcode": ParameterDef(
                    type="string",
                    description="The barcode, UPC, or ISBN number",
                ),
                "weight": ParameterDef(
                    type="string",
                    description="The weight of the variant (requires weight_unit)",
                ),
                "weight_unit": ParameterDef(
                    type="string",
                    description="Weight unit. Allowed values: KILOGRAMS, GRAMS, POUNDS, OUNCES",
                ),
                "metafields": ParameterDef(
                    type="array",
                    description="Array of metafield objects with key, value, type, namespace",
                ),
            },
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="Shopify OAuth Access Token",
            description="Authenticate using a Shopify OAuth access token and shop ID. Shopify uses shop-specific OAuth URLs which require custom auth handling.",
            setup_environment_variables=[
                EnvVar(
                    name="SHOPIFY_SHOP_ID",
                    display_name="Shop ID",
                    description="Your Shopify store subdomain (e.g. 'my-store' from my-store.myshopify.com)",
                    required=True,
                    sensitive=False,
                    sample_format="my-store",
                    about_url="https://admin.shopify.com",
                ),
                EnvVar(
                    name="SHOPIFY_ACCESS_TOKEN",
                    display_name="Access Token",
                    description="Shopify Admin API access token (from a custom app or OAuth flow)",
                    required=True,
                    sensitive=True,
                    sample_format="shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://shopify.dev/docs/apps/build/authentication",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://{shop_id}.myshopify.com/admin/api/2024-01/shop.json",
                method="GET",
                headers={
                    "X-Shopify-Access-Token": "{access_token}",
                    "Accept": "application/json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["shop"]
                ),
                cost_level="free",
                description=(
                    "Validates the access token and shop ID by fetching shop "
                    "metadata via the Admin REST API"
                ),
            ),
        ),
    ],
)

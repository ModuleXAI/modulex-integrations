"""WooCommerce integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="woocommerce",
    display_name="WooCommerce",
    description="WooCommerce REST API integration for managing orders, products, customers, and refunds on self-hosted WooCommerce stores.",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:woocommerce-themed",
    app_url="https://woocommerce.com",
    categories=["E-Commerce", "Retail", "Payments"],
    actions=[
        ActionDefinition(
            name="create_order",
            description="Create a new order in the WooCommerce store.",
            parameters={
                "status": ParameterDef(
                    type="string",
                    description="Order status. Options: pending, processing, on-hold, completed, cancelled, refunded, failed, trash",
                    default="pending",
                ),
                "customer_id": ParameterDef(
                    type="integer",
                    description="User ID who owns the order. 0 for guests",
                ),
                "payment_method": ParameterDef(
                    type="string",
                    description="Payment method ID (e.g. bacs, cheque, cod, paypal)",
                ),
                "line_items": ParameterDef(
                    type="array",
                    description="Array of line item objects, each with product_id (integer) and quantity (integer)",
                ),
            },
        ),
        ActionDefinition(
            name="get_order",
            description="Retrieve a specific order by ID.",
            parameters={
                "order_id": ParameterDef(
                    type="integer",
                    description="ID of the order to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_orders",
            description="Retrieve a list of orders with optional filters.",
            parameters={
                "search": ParameterDef(
                    type="string",
                    description="Limit results to those matching a string",
                ),
                "status": ParameterDef(
                    type="string",
                    description="Order status filter. Options: pending, processing, on-hold, completed, cancelled, refunded, failed, trash",
                    default="pending",
                ),
                "customer": ParameterDef(
                    type="integer",
                    description="Filter by customer user ID. 0 for guests",
                ),
                "after": ParameterDef(
                    type="string",
                    description="Limit to orders created after this ISO8601 date (e.g. 2023-01-01T00:00:00)",
                ),
                "before": ParameterDef(
                    type="string",
                    description="Limit to orders created before this ISO8601 date (e.g. 2023-12-31T23:59:59)",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=20,
                ),
            },
        ),
        ActionDefinition(
            name="delete_order",
            description="Delete an existing order.",
            parameters={
                "order_id": ParameterDef(
                    type="integer",
                    description="ID of the order to delete",
                    required=True,
                ),
                "force": ParameterDef(
                    type="boolean",
                    description="Whether to bypass trash and permanently delete the order",
                ),
            },
        ),
        ActionDefinition(
            name="update_order_status",
            description="Update the status of a specific order.",
            parameters={
                "order_id": ParameterDef(
                    type="integer",
                    description="ID of the order to update",
                    required=True,
                ),
                "status": ParameterDef(
                    type="string",
                    description="New order status. Options: pending, processing, on-hold, completed, cancelled, refunded, failed, trash",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_product",
            description="Create a new product in the WooCommerce store.",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Name of the product",
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description="Product type. Options: simple, grouped, external, variable",
                    default="simple",
                ),
                "status": ParameterDef(
                    type="string",
                    description="Product status. Options: draft, pending, private, publish",
                    default="publish",
                ),
                "regular_price": ParameterDef(
                    type="string",
                    description="Product regular price",
                ),
                "sale_price": ParameterDef(
                    type="string",
                    description="Product sale price",
                ),
                "description": ParameterDef(
                    type="string",
                    description="Product description (HTML allowed)",
                ),
                "categories": ParameterDef(
                    type="array",
                    description="Array of category IDs (integers) to assign the product to",
                ),
                "image_url": ParameterDef(
                    type="string",
                    description="URL of an image to add to the product",
                ),
            },
        ),
        ActionDefinition(
            name="update_product",
            description="Update an existing product.",
            parameters={
                "product_id": ParameterDef(
                    type="integer",
                    description="ID of the product to update",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="New name for the product",
                ),
                "type": ParameterDef(
                    type="string",
                    description="Product type. Options: simple, grouped, external, variable",
                ),
                "status": ParameterDef(
                    type="string",
                    description="Product status. Options: draft, pending, private, publish",
                ),
                "regular_price": ParameterDef(
                    type="string",
                    description="Product regular price",
                ),
                "sale_price": ParameterDef(
                    type="string",
                    description="Product sale price",
                ),
                "description": ParameterDef(
                    type="string",
                    description="Product description (HTML allowed)",
                ),
                "categories": ParameterDef(
                    type="array",
                    description="Array of category IDs (integers) to assign the product to",
                ),
                "image_url": ParameterDef(
                    type="string",
                    description="URL of an image to add to the product",
                ),
            },
        ),
        ActionDefinition(
            name="get_product",
            description="Retrieve a specific product by ID.",
            parameters={
                "product_id": ParameterDef(
                    type="integer",
                    description="ID of the product to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_products",
            description="Retrieve a list of products with optional filters.",
            parameters={
                "search": ParameterDef(
                    type="string",
                    description="Limit results to those matching a string",
                ),
                "status": ParameterDef(
                    type="string",
                    description="Product status filter. Options: draft, pending, private, publish",
                    default="publish",
                ),
                "type": ParameterDef(
                    type="string",
                    description="Product type filter. Options: simple, grouped, external, variable",
                    default="simple",
                ),
                "after": ParameterDef(
                    type="string",
                    description="Limit to products created after this ISO8601 date",
                ),
                "before": ParameterDef(
                    type="string",
                    description="Limit to products created before this ISO8601 date",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=20,
                ),
            },
        ),
        ActionDefinition(
            name="search_customers",
            description="Search for customers by email, name, or other criteria.",
            parameters={
                "search": ParameterDef(
                    type="string",
                    description="Limit results to those matching a string",
                ),
                "email": ParameterDef(
                    type="string",
                    description="Filter by exact customer email address",
                ),
                "role": ParameterDef(
                    type="string",
                    description="Filter by role. Options: all, administrator, editor, author, contributor, subscriber, customer",
                    default="customer",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=20,
                ),
            },
        ),
        ActionDefinition(
            name="get_customer",
            description="Retrieve a specific customer by ID.",
            parameters={
                "customer_id": ParameterDef(
                    type="integer",
                    description="ID of the customer to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_customer",
            description="Create a new customer.",
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="Customer email address",
                    required=True,
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="Customer first name",
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="Customer last name",
                ),
                "username": ParameterDef(
                    type="string",
                    description="Customer login username",
                ),
                "password": ParameterDef(
                    type="string",
                    description="Customer password",
                ),
                "is_paying_customer": ParameterDef(
                    type="boolean",
                    description="Whether the customer is a paying customer",
                ),
            },
        ),
        ActionDefinition(
            name="add_order_note",
            description="Create a new note for an order.",
            parameters={
                "order_id": ParameterDef(
                    type="integer",
                    description="ID of the order to add a note to",
                    required=True,
                ),
                "note": ParameterDef(
                    type="string",
                    description="Content of the order note",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_order_note",
            description="Retrieve a specific order note.",
            parameters={
                "order_id": ParameterDef(
                    type="integer",
                    description="ID of the order",
                    required=True,
                ),
                "note_id": ParameterDef(
                    type="integer",
                    description="ID of the order note",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_order_notes",
            description="Retrieve all notes for a specific order.",
            parameters={
                "order_id": ParameterDef(
                    type="integer",
                    description="ID of the order",
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description="Filter by note type. Options: any, customer, internal",
                    default="any",
                ),
            },
        ),
        ActionDefinition(
            name="create_refund",
            description="Create a new refund for an order.",
            parameters={
                "order_id": ParameterDef(
                    type="integer",
                    description="ID of the order to refund",
                    required=True,
                ),
                "amount": ParameterDef(
                    type="string",
                    description="Refund amount. If not specified, calculated from line items",
                ),
                "reason": ParameterDef(
                    type="string",
                    description="Reason for the refund",
                ),
                "api_refund": ParameterDef(
                    type="boolean",
                    description="When true, the payment gateway API generates the refund. When false, the refund is manual",
                ),
                "line_items": ParameterDef(
                    type="array",
                    description="Array of line item refund objects. Each with id (integer), refund_total (string), and optionally refund_tax (array)",
                ),
            },
        ),
        ActionDefinition(
            name="list_payment_method_options",
            description="Retrieve available payment gateway options.",
            parameters={},
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="WooCommerce REST API Credentials",
            description="Authenticate using your WooCommerce store URL, consumer key, and consumer secret via HTTP Basic Auth (HTTPS required).",
            setup_environment_variables=[
                EnvVar(
                    name="WOOCOMMERCE_STORE_URL",
                    display_name="Store URL",
                    description="Your WooCommerce store URL (e.g. https://mystore.com)",
                    required=True,
                    sensitive=False,
                    sample_format="https://mystore.example.com",
                    about_url="https://woocommerce.github.io/woocommerce-rest-api-docs/#authentication",
                ),
                EnvVar(
                    name="WOOCOMMERCE_CONSUMER_KEY",
                    display_name="Consumer Key",
                    description="WooCommerce REST API consumer key from WooCommerce > Settings > Advanced > REST API",
                    required=True,
                    sensitive=True,
                    sample_format="ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://woocommerce.github.io/woocommerce-rest-api-docs/#authentication",
                ),
                EnvVar(
                    name="WOOCOMMERCE_CONSUMER_SECRET",
                    display_name="Consumer Secret",
                    description="WooCommerce REST API consumer secret from WooCommerce > Settings > Advanced > REST API",
                    required=True,
                    sensitive=True,
                    sample_format="cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://woocommerce.github.io/woocommerce-rest-api-docs/#authentication",
                ),
            ],
        ),
    ],
)

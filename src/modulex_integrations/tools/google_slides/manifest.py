"""Google Slides integration manifest."""
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
    name="google_slides",
    display_name="Google Slides",
    description=(
        "Create and edit Google Slides presentations — manage slides, shapes, "
        "images, tables, and text via the Google Slides REST API."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:google_slides",
    app_url="https://slides.google.com",
    categories=[
        "Productivity & Collaboration",
        "Document Management",
    ],
    actions=[
        ActionDefinition(
            name="create_image",
            description=(
                "Insert an image (by URL) onto a slide in a presentation via "
                "the Slides batchUpdate CreateImageRequest."
            ),
            parameters={
                "presentation_id": ParameterDef(
                    type="string",
                    description="ID of the target Google Slides presentation.",
                    required=True,
                ),
                "slide_id": ParameterDef(
                    type="string",
                    description=(
                        "Object ID of the slide (page) on which to place the "
                        "image."
                    ),
                    required=True,
                ),
                "url": ParameterDef(
                    type="string",
                    description=(
                        "Publicly accessible URL of the image to insert; must "
                        "be reachable by Google's servers."
                    ),
                    required=True,
                ),
                "height": ParameterDef(
                    type="integer",
                    description=(
                        "Height of the image in points (1 pt = 1/72 inch)."
                    ),
                    required=True,
                ),
                "width": ParameterDef(
                    type="integer",
                    description=(
                        "Width of the image in points (1 pt = 1/72 inch)."
                    ),
                    required=True,
                ),
                "scale_x": ParameterDef(
                    type="integer",
                    description="Horizontal scale factor for the image.",
                    required=False,
                    default=1,
                ),
                "scale_y": ParameterDef(
                    type="integer",
                    description="Vertical scale factor for the image.",
                    required=False,
                    default=1,
                ),
                "translate_x": ParameterDef(
                    type="integer",
                    description=(
                        "Horizontal translation (offset) of the image in "
                        "points."
                    ),
                    required=False,
                    default=0,
                ),
                "translate_y": ParameterDef(
                    type="integer",
                    description=(
                        "Vertical translation (offset) of the image in points."
                    ),
                    required=False,
                    default=0,
                ),
            },
        ),
        ActionDefinition(
            name="create_page_element",
            description=(
                "Insert a new shape page element (text box, rectangle, "
                "ellipse, arrow, etc.) onto a slide via the Slides "
                "batchUpdate CreateShapeRequest."
            ),
            parameters={
                "presentation_id": ParameterDef(
                    type="string",
                    description="ID of the target Google Slides presentation.",
                    required=True,
                ),
                "slide_id": ParameterDef(
                    type="string",
                    description=(
                        "Object ID of the slide on which to place the shape."
                    ),
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description=(
                        "Shape type. Common values: 'TEXT_BOX', 'RECTANGLE', "
                        "'ELLIPSE', 'ROUND_RECTANGLE', 'ARROW_EAST', "
                        "'RIGHT_ARROW', 'STAR_5', 'CLOUD'. See Google Slides "
                        "API Type enum for the full list."
                    ),
                    required=True,
                ),
                "height": ParameterDef(
                    type="integer",
                    description=(
                        "Height of the shape in points (1 pt = 1/72 inch)."
                    ),
                    required=True,
                ),
                "width": ParameterDef(
                    type="integer",
                    description=(
                        "Width of the shape in points (1 pt = 1/72 inch)."
                    ),
                    required=True,
                ),
                "scale_x": ParameterDef(
                    type="integer",
                    description="Horizontal scale factor for the shape.",
                    required=False,
                    default=1,
                ),
                "scale_y": ParameterDef(
                    type="integer",
                    description="Vertical scale factor for the shape.",
                    required=False,
                    default=1,
                ),
                "translate_x": ParameterDef(
                    type="integer",
                    description=(
                        "Horizontal translation (offset) of the shape in "
                        "points."
                    ),
                    required=False,
                    default=0,
                ),
                "translate_y": ParameterDef(
                    type="integer",
                    description=(
                        "Vertical translation (offset) of the shape in points."
                    ),
                    required=False,
                    default=0,
                ),
            },
        ),
        ActionDefinition(
            name="create_presentation",
            description=(
                "Create a blank Google Slides presentation via the Slides API."
            ),
            parameters={
                "title": ParameterDef(
                    type="string",
                    description="Title of the new presentation.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_slide",
            description=(
                "Create a new slide in a presentation, optionally based on a "
                "specific layout, via the Slides batchUpdate "
                "CreateSlideRequest."
            ),
            parameters={
                "presentation_id": ParameterDef(
                    type="string",
                    description="ID of the target Google Slides presentation.",
                    required=True,
                ),
                "layout_id": ParameterDef(
                    type="string",
                    description=(
                        "Object ID of the slide layout to apply (from "
                        "presentation.layouts[*].objectId)."
                    ),
                    required=True,
                ),
                "insertion_index": ParameterDef(
                    type="integer",
                    description=(
                        "Optional 0-based index where the slide is inserted. "
                        "Omit to append at the end."
                    ),
                    required=False,
                    default=None,
                ),
            },
        ),
        ActionDefinition(
            name="create_table",
            description=(
                "Create a new table on a slide with the given rows and "
                "columns via the Slides batchUpdate CreateTableRequest."
            ),
            parameters={
                "presentation_id": ParameterDef(
                    type="string",
                    description="ID of the target Google Slides presentation.",
                    required=True,
                ),
                "slide_id": ParameterDef(
                    type="string",
                    description=(
                        "Object ID of the slide on which to place the table."
                    ),
                    required=True,
                ),
                "rows": ParameterDef(
                    type="integer",
                    description="Number of rows in the table.",
                    required=True,
                ),
                "columns": ParameterDef(
                    type="integer",
                    description="Number of columns in the table.",
                    required=True,
                ),
                "height": ParameterDef(
                    type="integer",
                    description=(
                        "Height of the table in points (1 pt = 1/72 inch)."
                    ),
                    required=True,
                ),
                "width": ParameterDef(
                    type="integer",
                    description=(
                        "Width of the table in points (1 pt = 1/72 inch)."
                    ),
                    required=True,
                ),
                "translate_x": ParameterDef(
                    type="integer",
                    description=(
                        "Optional horizontal translation (offset) of the "
                        "table in points."
                    ),
                    required=False,
                    default=None,
                ),
                "translate_y": ParameterDef(
                    type="integer",
                    description=(
                        "Optional vertical translation (offset) of the table "
                        "in points."
                    ),
                    required=False,
                    default=None,
                ),
            },
        ),
        ActionDefinition(
            name="delete_page_element",
            description=(
                "Delete a page element (shape, image, table, etc.) from a "
                "slide via the Slides batchUpdate DeleteObjectRequest."
            ),
            parameters={
                "presentation_id": ParameterDef(
                    type="string",
                    description="ID of the target Google Slides presentation.",
                    required=True,
                ),
                "page_element_id": ParameterDef(
                    type="string",
                    description=(
                        "Object ID of the page element to delete."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_slide",
            description=(
                "Delete a slide from a presentation via the Slides "
                "batchUpdate DeleteObjectRequest."
            ),
            parameters={
                "presentation_id": ParameterDef(
                    type="string",
                    description="ID of the target Google Slides presentation.",
                    required=True,
                ),
                "slide_id": ParameterDef(
                    type="string",
                    description="Object ID of the slide to delete.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_table_column",
            description=(
                "Delete a single column from an existing table on a slide "
                "via the Slides batchUpdate DeleteTableColumnRequest."
            ),
            parameters={
                "presentation_id": ParameterDef(
                    type="string",
                    description="ID of the target Google Slides presentation.",
                    required=True,
                ),
                "table_id": ParameterDef(
                    type="string",
                    description="Object ID of the table to modify.",
                    required=True,
                ),
                "column_index": ParameterDef(
                    type="integer",
                    description=(
                        "0-based index of the column inside the table to "
                        "delete."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_table_row",
            description=(
                "Delete a single row from an existing table on a slide via "
                "the Slides batchUpdate DeleteTableRowRequest."
            ),
            parameters={
                "presentation_id": ParameterDef(
                    type="string",
                    description="ID of the target Google Slides presentation.",
                    required=True,
                ),
                "table_id": ParameterDef(
                    type="string",
                    description="Object ID of the table to modify.",
                    required=True,
                ),
                "row_index": ParameterDef(
                    type="integer",
                    description=(
                        "0-based index of the row inside the table to delete."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="find_presentation",
            description=(
                "Fetch full metadata about a Google Slides presentation "
                "(slides, layouts, masters) via Slides presentations.get."
            ),
            parameters={
                "presentation_id": ParameterDef(
                    type="string",
                    description=(
                        "ID of the Google Slides presentation to retrieve."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="insert_table_columns",
            description=(
                "Insert new columns into an existing table on a slide via "
                "the Slides batchUpdate InsertTableColumnsRequest. Maximum "
                "20 columns per request."
            ),
            parameters={
                "presentation_id": ParameterDef(
                    type="string",
                    description="ID of the target Google Slides presentation.",
                    required=True,
                ),
                "table_id": ParameterDef(
                    type="string",
                    description="Object ID of the table to modify.",
                    required=True,
                ),
                "column_index": ParameterDef(
                    type="integer",
                    description=(
                        "Optional 0-based column index of the reference cell."
                    ),
                    required=False,
                    default=None,
                ),
                "insert_right": ParameterDef(
                    type="boolean",
                    description=(
                        "Whether the new columns are inserted to the right "
                        "of the reference cell."
                    ),
                    required=False,
                    default=None,
                ),
                "number": ParameterDef(
                    type="integer",
                    description=(
                        "Number of columns to insert (max 20 per request)."
                    ),
                    required=False,
                    default=1,
                ),
            },
        ),
        ActionDefinition(
            name="insert_table_rows",
            description=(
                "Insert new rows into an existing table on a slide via the "
                "Slides batchUpdate InsertTableRowsRequest. Maximum 20 rows "
                "per request."
            ),
            parameters={
                "presentation_id": ParameterDef(
                    type="string",
                    description="ID of the target Google Slides presentation.",
                    required=True,
                ),
                "table_id": ParameterDef(
                    type="string",
                    description="Object ID of the table to modify.",
                    required=True,
                ),
                "row_index": ParameterDef(
                    type="integer",
                    description=(
                        "Optional 0-based row index of the reference cell."
                    ),
                    required=False,
                    default=None,
                ),
                "insert_below": ParameterDef(
                    type="boolean",
                    description=(
                        "Whether the new rows are inserted below the "
                        "reference cell."
                    ),
                    required=False,
                    default=None,
                ),
                "number": ParameterDef(
                    type="integer",
                    description=(
                        "Number of rows to insert (max 20 per request)."
                    ),
                    required=False,
                    default=1,
                ),
            },
        ),
        ActionDefinition(
            name="insert_text",
            description=(
                "Insert text into a shape (typically a TEXT_BOX) on a slide "
                "via the Slides batchUpdate InsertTextRequest."
            ),
            parameters={
                "presentation_id": ParameterDef(
                    type="string",
                    description="ID of the target Google Slides presentation.",
                    required=True,
                ),
                "shape_id": ParameterDef(
                    type="string",
                    description=(
                        "Object ID of the target shape (must contain a text "
                        "frame, e.g. a TEXT_BOX)."
                    ),
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Text content to insert into the shape.",
                    required=True,
                ),
                "insertion_index": ParameterDef(
                    type="integer",
                    description=(
                        "Optional 0-based character index at which to insert "
                        "the text. Omit to append at the end."
                    ),
                    required=False,
                    default=None,
                ),
            },
        ),
        ActionDefinition(
            name="insert_text_into_table",
            description=(
                "Insert text into a specific cell of a table on a slide via "
                "the Slides batchUpdate InsertTextRequest with cellLocation."
            ),
            parameters={
                "presentation_id": ParameterDef(
                    type="string",
                    description="ID of the target Google Slides presentation.",
                    required=True,
                ),
                "table_id": ParameterDef(
                    type="string",
                    description="Object ID of the target table.",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Text content to insert into the table cell.",
                    required=True,
                ),
                "row_index": ParameterDef(
                    type="integer",
                    description=(
                        "Optional 0-based row index of the target cell."
                    ),
                    required=False,
                    default=None,
                ),
                "column_index": ParameterDef(
                    type="integer",
                    description=(
                        "Optional 0-based column index of the target cell."
                    ),
                    required=False,
                    default=None,
                ),
                "insertion_index": ParameterDef(
                    type="integer",
                    description=(
                        "Optional 0-based character index within the cell at "
                        "which to insert the text. Omit to append at the end."
                    ),
                    required=False,
                    default=None,
                ),
            },
        ),
        ActionDefinition(
            name="replace_all_text",
            description=(
                "Replace every occurrence of a given text snippet inside a "
                "presentation via the Slides batchUpdate "
                "ReplaceAllTextRequest. Optionally restricted to specific "
                "slide pages."
            ),
            parameters={
                "presentation_id": ParameterDef(
                    type="string",
                    description="ID of the target Google Slides presentation.",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Text snippet to search for.",
                    required=True,
                ),
                "replace_text": ParameterDef(
                    type="string",
                    description=(
                        "Replacement text inserted for every match found."
                    ),
                    required=True,
                ),
                "slide_ids": ParameterDef(
                    type="array",
                    description=(
                        "Optional list of slide page object IDs (strings). "
                        "When supplied, only page elements on these pages "
                        "are searched."
                    ),
                    required=False,
                    default=None,
                ),
                "match_case": ParameterDef(
                    type="boolean",
                    description=(
                        "Whether the text match is case-sensitive."
                    ),
                    required=False,
                    default=None,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Google OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_SLIDES_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google Cloud OAuth 2.0 Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format=(
                        "1234567890-abcdefghijklmnop.apps.googleusercontent.com"
                    ),
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_SLIDES_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google Cloud OAuth 2.0 Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                scopes=[
                    "https://www.googleapis.com/auth/presentations",
                ],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://slides.googleapis.com/v1/presentations/1",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200, 404],
                    response_fields=None,
                ),
                cost_level="free",
                description=(
                    "Validates the OAuth token against the Slides API "
                    "(200 or 404 both confirm the token is accepted)."
                ),
            ),
        ),
    ],
)

"""Canvas LMS integration manifest."""
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
    name="canvas",
    display_name="Canvas LMS",
    description="Learning management system for course, assignment, and user management via the Canvas REST API.",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:canvas-themed",
    app_url="https://www.instructure.com/canvas",
    categories=["Education", "Learning Management"],
    actions=[
        ActionDefinition(
            name="list_accounts",
            description="List Canvas accounts accessible to the authenticated user.",
            parameters={},
        ),
        ActionDefinition(
            name="list_assignments",
            description="Retrieve a list of assignments for a user in a specific course.",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="The ID of the user whose assignments to list.",
                    required=True,
                ),
                "course_id": ParameterDef(
                    type="string",
                    description="The ID of the course to list assignments from.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_courses",
            description="List all courses associated with a given user.",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="The ID of the user whose courses to list.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search_course_content",
            description="Search for content in a course using Canvas smart search.",
            parameters={
                "course_id": ParameterDef(
                    type="string",
                    description="The ID of the course to search within.",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="The search query string.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_assignment",
            description="Update an existing assignment in a course.",
            parameters={
                "course_id": ParameterDef(
                    type="string",
                    description="The ID of the course containing the assignment.",
                    required=True,
                ),
                "assignment_id": ParameterDef(
                    type="string",
                    description="The ID of the assignment to update.",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="The new name of the assignment.",
                ),
                "description": ParameterDef(
                    type="string",
                    description="The new description of the assignment (supports HTML).",
                ),
                "submission_type": ParameterDef(
                    type="string",
                    description="Submission type: online_quiz, none, on_paper, discussion_topic, external_tool, online_upload, online_text_entry, online_url, media_recording, student_annotation.",
                ),
                "notify_of_update": ParameterDef(
                    type="boolean",
                    description="Whether to notify students of the update.",
                ),
                "points_possible": ParameterDef(
                    type="integer",
                    description="Maximum points possible on the assignment.",
                ),
                "grading_type": ParameterDef(
                    type="string",
                    description="Grading strategy: pass_fail, percent, letter_grade, gpa_scale, points, not_graded.",
                ),
                "due_at": ParameterDef(
                    type="string",
                    description="Due date/time in ISO 8601 format (e.g. 2014-10-21T18:48:00Z).",
                ),
                "omit_from_final_grade": ParameterDef(
                    type="boolean",
                    description="Whether to omit this assignment from the student's final grade.",
                ),
                "allowed_attempts": ParameterDef(
                    type="integer",
                    description="Number of submission attempts allowed (-1 for unlimited).",
                ),
            },
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="Canvas OAuth Token + Domain",
            description=(
                "Authenticate using a Canvas access token and your instance domain. "
                "Canvas LMS is self-hosted, so both the domain and token are required."
            ),
            setup_instructions=[
                "Log into your Canvas instance.",
                "Go to Account > Settings > Approved Integrations (or generate a new access token).",
                "Copy your access token and note your Canvas domain (e.g. myschool.instructure.com).",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="CANVAS_DOMAIN",
                    display_name="Canvas Domain",
                    description="Your Canvas instance domain (e.g. myschool.instructure.com)",
                    required=True,
                    sensitive=False,
                    sample_format="myschool.instructure.com",
                ),
                EnvVar(
                    name="CANVAS_ACCESS_TOKEN",
                    display_name="Access Token",
                    description="Your Canvas API access token",
                    required=True,
                    sensitive=True,
                    sample_format="7~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://community.canvaslms.com/t5/Admin-Guide/How-do-I-manage-API-access-tokens-as-an-admin/ta-p/89",
                ),
            ],
        ),
    ],
)

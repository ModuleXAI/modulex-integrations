"""Tests for the PostHog integration.

78 actions all share two patterns (project REST + ingest) and one
output envelope, so tests are shape-representative: one happy-path
per surface plus the multi-step quirks (`delete_action` rename
fallback, `delete_action_by_name` chain, `update_feature_flag`
key-to-id lookup, `delete_early_access_feature_by_name`).
"""
from __future__ import annotations

import re
from typing import Any

import pytest

from modulex_integrations.tools.posthog import (
    TOOLS,
    alias_user,
    batch_capture_events,
    bulk_delete_persons,
    capture_event,
    create_cohort,
    create_dashboard,
    delete_action,
    delete_action_by_name,
    delete_dashboard,
    delete_early_access_feature_by_name,
    delete_person,
    evaluate_feature_flags,
    find_group,
    get_actions,
    get_alerts,
    get_annotations,
    get_cohort,
    get_dashboard,
    get_dashboards,
    get_event_definitions,
    get_experiment_results,
    get_feature_flag,
    get_groups,
    get_insight,
    get_organizations,
    get_persons,
    get_session_recordings,
    get_survey,
    group_identify,
    identify_user,
    manifest,
    run_query,
    update_feature_flag,
)
from modulex_integrations.tools.posthog.outputs import PostHogResult

API = "https://app.posthog.com"
INGEST = "https://us.i.posthog.com"
KEY = "phx_test_xxxxxxxxxxxxxxxxxxxxxxxx"
PROJECT_API_KEY = "phc_proj_xxxxxxxxxxxxxxxxxxxx"
PROJECT_ID = 12345


def _proj_args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=KEY, project_id=PROJECT_ID, **extra)


def _ingest_args(**extra: Any) -> dict[str, Any]:
    return dict(project_api_key=PROJECT_API_KEY, **extra)


class TestManifest:
    def test_manifest_exposes_78_actions(self) -> None:
        assert len(manifest.actions) == 78

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth_with_three_env_vars(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["custom"]
        env_vars = {v.name for v in manifest.auth_schemas[0].setup_environment_variables}
        assert env_vars == {
            "POSTHOG_API_KEY",
            "POSTHOG_PROJECT_ID",
            "POSTHOG_BASE_URL",
        }


@pytest.mark.asyncio
async def test_get_dashboards_empty_key() -> None:
    result = PostHogResult.model_validate(
        await get_dashboards.ainvoke(
            {"api_key": "", "project_id": PROJECT_ID}
        )
    )
    assert result.success is False
    assert result.error is not None and "empty" in result.error


@pytest.mark.asyncio
async def test_get_dashboards(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/api/projects/{PROJECT_ID}/dashboards/\?.*"),
        json={"count": 1, "results": [{"id": 1, "name": "Main"}]},
    )
    result = PostHogResult.model_validate(
        await get_dashboards.ainvoke(_proj_args())
    )
    assert result.success is True
    assert result.result["count"] == 1


@pytest.mark.asyncio
async def test_get_dashboard(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/projects/{PROJECT_ID}/dashboards/1/",
        json={"id": 1, "name": "Main"},
    )
    result = PostHogResult.model_validate(
        await get_dashboard.ainvoke(_proj_args(dashboard_id=1))
    )
    assert result.success is True
    assert result.result["id"] == 1


@pytest.mark.asyncio
async def test_create_dashboard(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/projects/{PROJECT_ID}/dashboards/",
        status_code=201,
        json={"id": 99, "name": "New"},
    )
    result = PostHogResult.model_validate(
        await create_dashboard.ainvoke(_proj_args(name="New"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_dashboard(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/api/projects/{PROJECT_ID}/dashboards/1/",
        status_code=204,
    )
    result = PostHogResult.model_validate(
        await delete_dashboard.ainvoke(_proj_args(dashboard_id=1))
    )
    assert result.success is True
    assert result.result["deleted"] is True


@pytest.mark.asyncio
async def test_get_experiment_results(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/projects/{PROJECT_ID}/experiments/5/results/",
        json={"insight": []},
    )
    result = PostHogResult.model_validate(
        await get_experiment_results.ainvoke(_proj_args(experiment_id=5))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_feature_flag_by_id(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/projects/{PROJECT_ID}/feature_flags/42/",
        json={"id": 42, "key": "new-checkout"},
    )
    result = PostHogResult.model_validate(
        await get_feature_flag.ainvoke(_proj_args(flag_id=42))
    )
    assert result.success is True
    assert result.result["id"] == 42


@pytest.mark.asyncio
async def test_get_feature_flag_by_key_filters_results(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/api/projects/{PROJECT_ID}/feature_flags/\?.*"),
        json={
            "results": [
                {"id": 1, "key": "other-flag"},
                {"id": 42, "key": "new-checkout"},
            ]
        },
    )
    result = PostHogResult.model_validate(
        await get_feature_flag.ainvoke(_proj_args(flag_key="new-checkout"))
    )
    assert result.success is True
    assert result.result["id"] == 42


@pytest.mark.asyncio
async def test_update_feature_flag_translates_key_to_id(httpx_mock: Any) -> None:
    # First call: search by key.
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/api/projects/{PROJECT_ID}/feature_flags/\?.*"),
        json={"results": [{"id": 42, "key": "new-checkout"}]},
    )
    # Second call: PATCH by ID.
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/api/projects/{PROJECT_ID}/feature_flags/42/",
        json={"id": 42, "key": "new-checkout", "active": False},
    )
    result = PostHogResult.model_validate(
        await update_feature_flag.ainvoke(
            _proj_args(flag_key="new-checkout", active=False)
        )
    )
    assert result.success is True
    assert result.result["active"] is False


@pytest.mark.asyncio
async def test_get_insight(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/projects/{PROJECT_ID}/insights/7/",
        json={"id": 7, "name": "Pageviews"},
    )
    result = PostHogResult.model_validate(
        await get_insight.ainvoke(_proj_args(insight_id=7))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_run_query(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/projects/{PROJECT_ID}/query/",
        json={"results": [{"count": 100}]},
    )
    result = PostHogResult.model_validate(
        await run_query.ainvoke(_proj_args(query={"kind": "EventsQuery"}))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_survey(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/projects/{PROJECT_ID}/surveys/abc/",
        json={"id": "abc", "name": "NPS"},
    )
    result = PostHogResult.model_validate(
        await get_survey.ainvoke(_proj_args(survey_id="abc"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_organizations(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/organizations/",
        json={"results": [{"id": "o1", "name": "Org"}]},
    )
    result = PostHogResult.model_validate(
        await get_organizations.ainvoke({"api_key": KEY})
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_event_definitions(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/api/projects/{PROJECT_ID}/event_definitions/\?.*"),
        json={"results": [{"name": "$pageview"}]},
    )
    result = PostHogResult.model_validate(
        await get_event_definitions.ainvoke(_proj_args())
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_capture_event(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json as _json

        from httpx import Response

        captured.update(_json.loads(request.content.decode()))
        return Response(200, json={"status": 1})

    httpx_mock.add_callback(_capture, method="POST", url=f"{INGEST}/i/v0/e/")
    result = PostHogResult.model_validate(
        await capture_event.ainvoke(
            _ingest_args(distinct_id="user1", event="signup")
        )
    )
    assert result.success is True
    assert captured["api_key"] == PROJECT_API_KEY
    assert captured["event"] == "signup"
    assert captured["distinct_id"] == "user1"


@pytest.mark.asyncio
async def test_batch_capture_events(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST", url=f"{INGEST}/batch/", json={"status": 1}
    )
    events = [{"event": "view", "distinct_id": "u1"}] * 3
    result = PostHogResult.model_validate(
        await batch_capture_events.ainvoke(_ingest_args(events=events))
    )
    assert result.success is True
    assert result.result["event_count"] == 3


@pytest.mark.asyncio
async def test_identify_user_wraps_in_set(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json as _json

        from httpx import Response

        captured.update(_json.loads(request.content.decode()))
        return Response(200, json={"status": 1})

    httpx_mock.add_callback(_capture, method="POST", url=f"{INGEST}/i/v0/e/")
    result = PostHogResult.model_validate(
        await identify_user.ainvoke(
            _ingest_args(distinct_id="u1", properties={"plan": "pro"})
        )
    )
    assert result.success is True
    assert captured["event"] == "$identify"
    assert captured["properties"] == {"$set": {"plan": "pro"}}


@pytest.mark.asyncio
async def test_alias_user(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST", url=f"{INGEST}/i/v0/e/", json={"status": 1}
    )
    result = PostHogResult.model_validate(
        await alias_user.ainvoke(
            _ingest_args(distinct_id="user_canonical", alias="user_legacy")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_evaluate_feature_flags_uses_v2_path(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=re.compile(rf"{INGEST}/flags\?.*"),
        json={"featureFlags": {"new-checkout": True}},
    )
    result = PostHogResult.model_validate(
        await evaluate_feature_flags.ainvoke(_ingest_args(distinct_id="u1"))
    )
    assert result.success is True
    assert result.result["featureFlags"]["new-checkout"] is True


@pytest.mark.asyncio
async def test_group_identify(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json as _json

        from httpx import Response

        captured.update(_json.loads(request.content.decode()))
        return Response(200, json={"status": 1})

    httpx_mock.add_callback(_capture, method="POST", url=f"{INGEST}/i/v0/e/")
    result = PostHogResult.model_validate(
        await group_identify.ainvoke(
            _ingest_args(
                group_type="company",
                group_key="acme",
                properties={"plan": "enterprise"},
            )
        )
    )
    assert result.success is True
    assert captured["event"] == "$groupidentify"
    assert captured["properties"]["$group_type"] == "company"
    assert captured["properties"]["$group_set"] == {"plan": "enterprise"}


@pytest.mark.asyncio
async def test_get_persons(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/api/projects/{PROJECT_ID}/persons/\?.*"),
        json={"results": [{"id": 1}]},
    )
    result = PostHogResult.model_validate(
        await get_persons.ainvoke(_proj_args(email="user@example.com"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_person_with_events(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=re.compile(rf"{API}/api/projects/{PROJECT_ID}/persons/100/\?.*"),
        status_code=204,
    )
    result = PostHogResult.model_validate(
        await delete_person.ainvoke(
            _proj_args(person_id=100, delete_events=True)
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_bulk_delete_persons(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/projects/{PROJECT_ID}/persons/bulk_delete/",
        status_code=200,
        json={"status": 1},
    )
    result = PostHogResult.model_validate(
        await bulk_delete_persons.ainvoke(_proj_args(person_ids=[1, 2, 3]))
    )
    assert result.success is True
    assert result.result["count"] == 3


@pytest.mark.asyncio
async def test_get_groups(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/api/projects/{PROJECT_ID}/groups/\?.*"),
        json={"results": [{"group_key": "acme"}]},
    )
    result = PostHogResult.model_validate(
        await get_groups.ainvoke(_proj_args(group_type_index=0))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_find_group(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/api/projects/{PROJECT_ID}/groups/find/\?.*"),
        json={"group_key": "acme", "group_properties": {}},
    )
    result = PostHogResult.model_validate(
        await find_group.ainvoke(
            _proj_args(group_type_index=0, group_key="acme")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_cohort(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/projects/{PROJECT_ID}/cohorts/3/",
        json={"id": 3, "name": "Power users"},
    )
    result = PostHogResult.model_validate(
        await get_cohort.ainvoke(_proj_args(cohort_id=3))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_cohort_static(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/projects/{PROJECT_ID}/cohorts/",
        status_code=201,
        json={"id": 99, "name": "New cohort"},
    )
    result = PostHogResult.model_validate(
        await create_cohort.ainvoke(
            _proj_args(name="New cohort", is_static=True)
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_session_recordings(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/api/projects/{PROJECT_ID}/session_recordings/\?.*"),
        json={"results": [{"id": "rec1"}]},
    )
    result = PostHogResult.model_validate(
        await get_session_recordings.ainvoke(_proj_args())
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_actions(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/api/projects/{PROJECT_ID}/actions/\?.*"),
        json={"results": [{"id": 1, "name": "Signup"}]},
    )
    result = PostHogResult.model_validate(
        await get_actions.ainvoke(_proj_args())
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_action_soft_delete_succeeds(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/api/projects/{PROJECT_ID}/actions/5/",
        json={"deleted": True},
    )
    result = PostHogResult.model_validate(
        await delete_action.ainvoke(_proj_args(action_id=5))
    )
    assert result.success is True
    assert result.result["deleted"] is True


@pytest.mark.asyncio
async def test_delete_action_falls_back_to_rename(httpx_mock: Any) -> None:
    # First PATCH (soft-delete) returns 500.
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/api/projects/{PROJECT_ID}/actions/5/",
        status_code=500,
        text="internal error",
    )
    # Second PATCH (rename) returns 200.
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/api/projects/{PROJECT_ID}/actions/5/",
        status_code=200,
        json={"id": 5, "name": "__archived_5_xxx__"},
    )
    result = PostHogResult.model_validate(
        await delete_action.ainvoke(_proj_args(action_id=5))
    )
    assert result.success is True
    assert result.result["renamed"] is True


@pytest.mark.asyncio
async def test_delete_action_by_name_not_found_is_success(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/api/projects/{PROJECT_ID}/actions/\?.*"),
        json={"results": []},
    )
    result = PostHogResult.model_validate(
        await delete_action_by_name.ainvoke(_proj_args(name="missing"))
    )
    assert result.success is True
    assert result.result["deleted"] is False


@pytest.mark.asyncio
async def test_delete_action_by_name_hard_delete(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/api/projects/{PROJECT_ID}/actions/\?.*"),
        json={
            "results": [
                {"id": 7, "name": "Target", "deleted": False},
                {"id": 8, "name": "Other"},
            ]
        },
    )
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/api/projects/{PROJECT_ID}/actions/7/",
        status_code=204,
    )
    result = PostHogResult.model_validate(
        await delete_action_by_name.ainvoke(_proj_args(name="Target"))
    )
    assert result.success is True
    assert result.result["action_id"] == 7


@pytest.mark.asyncio
async def test_get_annotations(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/api/projects/{PROJECT_ID}/annotations/\?.*"),
        json={"results": [{"id": 1, "content": "Release"}]},
    )
    result = PostHogResult.model_validate(
        await get_annotations.ainvoke(_proj_args())
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_alerts(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}/api/projects/{PROJECT_ID}/alerts/\?.*"),
        json={"results": [{"id": "a1"}]},
    )
    result = PostHogResult.model_validate(
        await get_alerts.ainvoke(_proj_args())
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_early_access_feature_by_name(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/projects/{PROJECT_ID}/early_access_feature/",
        json={"results": [{"id": "feat1", "name": "Dark mode"}]},
    )
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/api/projects/{PROJECT_ID}/early_access_feature/feat1/",
        status_code=204,
    )
    result = PostHogResult.model_validate(
        await delete_early_access_feature_by_name.ainvoke(
            _proj_args(name="Dark mode")
        )
    )
    assert result.success is True
    assert result.result["feature_id"] == "feat1"

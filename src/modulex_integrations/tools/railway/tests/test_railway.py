"""Happy-path tests per action + a GraphQL-error failure path and an
empty-credential short-circuit test.

Railway's GraphQL endpoint always returns HTTP 200; logical errors come
back in a top-level ``errors`` array, which the tools surface as
``success=False`` + ``error``.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.railway import (
    TOOLS,
    create_environment,
    create_project,
    create_service,
    delete_environment,
    delete_project,
    delete_service,
    delete_variable,
    deploy_service,
    get_deployment,
    get_deployment_logs,
    get_project,
    list_deployments,
    list_project_members,
    list_projects,
    list_variables,
    manifest,
    restart_deployment,
    rollback_deployment,
    transfer_project,
    update_project,
    upsert_variable,
)
from modulex_integrations.tools.railway.outputs import (
    CreateEnvironmentOutput,
    CreateProjectOutput,
    CreateServiceOutput,
    DeleteEnvironmentOutput,
    DeleteProjectOutput,
    DeleteServiceOutput,
    DeleteVariableOutput,
    DeployServiceOutput,
    GetDeploymentLogsOutput,
    GetDeploymentOutput,
    GetProjectOutput,
    ListDeploymentsOutput,
    ListProjectMembersOutput,
    ListProjectsOutput,
    ListVariablesOutput,
    RestartDeploymentOutput,
    RollbackDeploymentOutput,
    TransferProjectOutput,
    UpdateProjectOutput,
    UpsertVariableOutput,
)

GRAPHQL = "https://backboard.railway.com/graphql/v2"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


def _data(payload: dict[str, Any]) -> dict[str, Any]:
    return {"data": payload}


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_20_actions(self) -> None:
        assert len(manifest.actions) == 20

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_list_projects(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data(
            {
                "projects": {
                    "edges": [
                        {
                            "node": {
                                "id": "p1",
                                "name": "web",
                                "description": "the app",
                                "createdAt": "2025-01-01",
                                "updatedAt": "2025-02-01",
                            }
                        }
                    ],
                    "pageInfo": {"hasNextPage": False, "endCursor": "cur1"},
                }
            }
        ),
    )

    result_dict = await list_projects.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListProjectsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.projects[0].id == "p1"
    assert result.projects[0].name == "web"
    assert result.count == 1
    assert result.page_info is not None
    assert result.page_info.end_cursor == "cur1"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


@pytest.mark.asyncio
async def test_list_projects_project_token_header(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data({"projects": {"edges": [], "pageInfo": {}}}),
    )

    result_dict = await list_projects.ainvoke(_args(token_type="project"))

    assert isinstance(result_dict, dict)
    result = ListProjectsOutput.model_validate(result_dict)
    assert result.success is True

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Project-Access-Token"] == _API_KEY
    assert "Authorization" not in sent.headers


@pytest.mark.asyncio
async def test_get_project(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data(
            {
                "project": {
                    "id": "p1",
                    "name": "web",
                    "description": None,
                    "createdAt": "2025-01-01",
                    "updatedAt": None,
                    "services": {"edges": [{"node": {"id": "s1", "name": "api", "icon": None}}]},
                    "environments": {"edges": [{"node": {"id": "e1", "name": "production"}}]},
                }
            }
        ),
    )

    result_dict = await get_project.ainvoke(_args(project_id="p1"))

    assert isinstance(result_dict, dict)
    result = GetProjectOutput.model_validate(result_dict)
    assert result.success is True
    assert result.project is not None
    assert result.project.id == "p1"
    assert result.project.services[0].name == "api"
    assert result.project.environments[0].name == "production"


@pytest.mark.asyncio
async def test_create_project(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data({"projectCreate": {"id": "p2", "name": "my-app"}}),
    )

    result_dict = await create_project.ainvoke(_args(name="my-app"))

    assert isinstance(result_dict, dict)
    result = CreateProjectOutput.model_validate(result_dict)
    assert result.success is True
    assert result.project is not None
    assert result.project.id == "p2"
    assert result.project.name == "my-app"


@pytest.mark.asyncio
async def test_update_project(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data({"projectUpdate": {"id": "p1", "name": "renamed", "description": "new"}}),
    )

    result_dict = await update_project.ainvoke(_args(project_id="p1", name="renamed"))

    assert isinstance(result_dict, dict)
    result = UpdateProjectOutput.model_validate(result_dict)
    assert result.success is True
    assert result.project is not None
    assert result.project.name == "renamed"
    assert result.project.description == "new"


@pytest.mark.asyncio
async def test_delete_project(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data({"projectDelete": True}),
    )

    result_dict = await delete_project.ainvoke(_args(project_id="p1"))

    assert isinstance(result_dict, dict)
    result = DeleteProjectOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted is True


@pytest.mark.asyncio
async def test_transfer_project(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data({"projectTransfer": True}),
    )

    result_dict = await transfer_project.ainvoke(_args(project_id="p1", workspace_id="w2"))

    assert isinstance(result_dict, dict)
    result = TransferProjectOutput.model_validate(result_dict)
    assert result.success is True
    assert result.transferred is True


@pytest.mark.asyncio
async def test_list_project_members(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data(
            {
                "projectMembers": [
                    {
                        "id": "u1",
                        "role": "ADMIN",
                        "name": "Alice",
                        "email": "alice@example.com",
                        "avatar": None,
                    }
                ]
            }
        ),
    )

    result_dict = await list_project_members.ainvoke(_args(project_id="p1"))

    assert isinstance(result_dict, dict)
    result = ListProjectMembersOutput.model_validate(result_dict)
    assert result.success is True
    assert result.members[0].role == "ADMIN"
    assert result.count == 1


@pytest.mark.asyncio
async def test_create_environment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data({"environmentCreate": {"id": "e2", "name": "staging"}}),
    )

    result_dict = await create_environment.ainvoke(_args(project_id="p1", name="staging"))

    assert isinstance(result_dict, dict)
    result = CreateEnvironmentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.environment is not None
    assert result.environment.name == "staging"


@pytest.mark.asyncio
async def test_delete_environment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data({"environmentDelete": True}),
    )

    result_dict = await delete_environment.ainvoke(_args(environment_id="e1"))

    assert isinstance(result_dict, dict)
    result = DeleteEnvironmentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted is True


@pytest.mark.asyncio
async def test_create_service(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data({"serviceCreate": {"id": "s2", "name": "worker"}}),
    )

    result_dict = await create_service.ainvoke(
        _args(project_id="p1", name="worker", repo="owner/repo")
    )

    assert isinstance(result_dict, dict)
    result = CreateServiceOutput.model_validate(result_dict)
    assert result.success is True
    assert result.service is not None
    assert result.service.name == "worker"


@pytest.mark.asyncio
async def test_delete_service(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data({"serviceDelete": True}),
    )

    result_dict = await delete_service.ainvoke(_args(service_id="s1"))

    assert isinstance(result_dict, dict)
    result = DeleteServiceOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted is True


@pytest.mark.asyncio
async def test_list_deployments(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data(
            {
                "deployments": {
                    "edges": [
                        {
                            "node": {
                                "id": "d1",
                                "status": "SUCCESS",
                                "createdAt": "2025-03-01",
                                "url": "https://d1.up.railway.app",
                                "staticUrl": None,
                                "canRollback": True,
                                "canRedeploy": True,
                            }
                        }
                    ],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        ),
    )

    result_dict = await list_deployments.ainvoke(
        _args(project_id="p1", service_id="s1", environment_id="e1")
    )

    assert isinstance(result_dict, dict)
    result = ListDeploymentsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deployments[0].status == "SUCCESS"
    assert result.deployments[0].can_rollback is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_get_deployment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data(
            {
                "deployment": {
                    "id": "d1",
                    "status": "SUCCESS",
                    "createdAt": "2025-03-01",
                    "url": "https://d1.up.railway.app",
                    "staticUrl": None,
                    "canRollback": True,
                    "canRedeploy": False,
                }
            }
        ),
    )

    result_dict = await get_deployment.ainvoke(_args(deployment_id="d1"))

    assert isinstance(result_dict, dict)
    result = GetDeploymentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deployment is not None
    assert result.deployment.status == "SUCCESS"
    assert result.deployment.can_redeploy is False


@pytest.mark.asyncio
async def test_deploy_service(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data({"serviceInstanceDeployV2": "d99"}),
    )

    result_dict = await deploy_service.ainvoke(_args(service_id="s1", environment_id="e1"))

    assert isinstance(result_dict, dict)
    result = DeployServiceOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deployment_id == "d99"


@pytest.mark.asyncio
async def test_restart_deployment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data({"deploymentRestart": True}),
    )

    result_dict = await restart_deployment.ainvoke(_args(deployment_id="d1"))

    assert isinstance(result_dict, dict)
    result = RestartDeploymentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.restarted is True


@pytest.mark.asyncio
async def test_rollback_deployment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data({"deploymentRollback": True}),
    )

    result_dict = await rollback_deployment.ainvoke(_args(deployment_id="d1"))

    assert isinstance(result_dict, dict)
    result = RollbackDeploymentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.rolled_back is True


@pytest.mark.asyncio
async def test_get_deployment_logs(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data(
            {
                "deploymentLogs": [
                    {"timestamp": "2025-03-01T00:00:00Z", "message": "booting", "severity": "info"}
                ]
            }
        ),
    )

    result_dict = await get_deployment_logs.ainvoke(_args(deployment_id="d1", limit=100))

    assert isinstance(result_dict, dict)
    result = GetDeploymentLogsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.logs[0].message == "booting"
    assert result.count == 1


@pytest.mark.asyncio
async def test_list_variables(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data({"variables": {"DATABASE_URL": "postgres://x", "PORT": "8080"}}),
    )

    result_dict = await list_variables.ainvoke(_args(project_id="p1", environment_id="e1"))

    assert isinstance(result_dict, dict)
    result = ListVariablesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.variables["PORT"] == "8080"
    assert result.count == 2


@pytest.mark.asyncio
async def test_upsert_variable(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data({"variableUpsert": True}),
    )

    result_dict = await upsert_variable.ainvoke(
        _args(project_id="p1", environment_id="e1", name="PORT", value="8080")
    )

    assert isinstance(result_dict, dict)
    result = UpsertVariableOutput.model_validate(result_dict)
    assert result.success is True
    assert result.upserted is True


@pytest.mark.asyncio
async def test_delete_variable(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        json=_data({"variableDelete": True}),
    )

    result_dict = await delete_variable.ainvoke(
        _args(project_id="p1", environment_id="e1", name="PORT")
    )

    assert isinstance(result_dict, dict)
    result = DeleteVariableOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted is True


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_graphql_error_returns_success_false(httpx_mock):  # type: ignore[no-untyped-def]
    """Railway answers HTTP 200 with an ``errors`` array on logical failure;
    the tool surfaces the first error message as ``success=False``."""
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        status_code=200,
        json={"errors": [{"message": "Not Authorized"}]},
    )

    result_dict = await list_projects.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListProjectsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "Not Authorized"


@pytest.mark.asyncio
async def test_non_2xx_returns_success_false(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=GRAPHQL,
        status_code=500,
        text="Internal Server Error",
    )

    result_dict = await get_project.ainvoke(_args(project_id="p1"))

    assert isinstance(result_dict, dict)
    result = GetProjectOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "500" in result.error


@pytest.mark.asyncio
async def test_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await list_projects.ainvoke({"api_key": ""})

    assert isinstance(result_dict, dict)
    result = ListProjectsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "token is empty" in result.error

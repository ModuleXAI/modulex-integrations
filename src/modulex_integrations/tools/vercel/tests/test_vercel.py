"""Tests for the Vercel integration.

A manifest-shape trio, one happy-path test per action (56), plus
failure-path (non-2xx -> success=False) and empty-credential tests.
The Vercel REST API does not raise on errors here: the tools wrap every
call and return ``success=False`` + ``error``.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.vercel import (
    TOOLS,
    add_domain,
    add_project_domain,
    cancel_deployment,
    create_alias,
    create_check,
    create_deployment,
    create_dns_record,
    create_edge_config,
    create_env_var,
    create_project,
    create_webhook,
    delete_alias,
    delete_deployment,
    delete_dns_record,
    delete_domain,
    delete_edge_config,
    delete_env_var,
    delete_project,
    delete_webhook,
    get_alias,
    get_check,
    get_deployment,
    get_deployment_events,
    get_domain,
    get_domain_config,
    get_edge_config,
    get_edge_config_items,
    get_env_vars,
    get_project,
    get_team,
    get_user,
    get_webhook,
    list_aliases,
    list_checks,
    list_deployment_files,
    list_deployments,
    list_dns_records,
    list_domains,
    list_edge_configs,
    list_project_domains,
    list_projects,
    list_team_members,
    list_teams,
    list_webhooks,
    manifest,
    pause_project,
    promote_deployment,
    remove_project_domain,
    rerequest_check,
    unpause_project,
    update_check,
    update_dns_record,
    update_edge_config_items,
    update_env_var,
    update_project,
    update_project_domain,
    verify_project_domain,
)
from modulex_integrations.tools.vercel.outputs import (
    AddDomainOutput,
    AddProjectDomainOutput,
    CancelDeploymentOutput,
    CheckOutput,
    CreateAliasOutput,
    CreateDeploymentOutput,
    CreateDnsRecordOutput,
    CreateEdgeConfigOutput,
    CreateEnvVarOutput,
    CreateProjectOutput,
    CreateWebhookOutput,
    DeleteAliasOutput,
    DeleteDeploymentOutput,
    DeleteDnsRecordOutput,
    DeleteDomainOutput,
    DeleteEdgeConfigOutput,
    DeleteEnvVarOutput,
    DeleteProjectOutput,
    DeleteWebhookOutput,
    GetAliasOutput,
    GetCheckOutput,
    GetDeploymentEventsOutput,
    GetDeploymentOutput,
    GetDomainConfigOutput,
    GetDomainOutput,
    GetEdgeConfigItemsOutput,
    GetEdgeConfigOutput,
    GetEnvVarsOutput,
    GetProjectOutput,
    GetTeamOutput,
    GetUserOutput,
    GetWebhookOutput,
    ListAliasesOutput,
    ListChecksOutput,
    ListDeploymentFilesOutput,
    ListDeploymentsOutput,
    ListDnsRecordsOutput,
    ListDomainsOutput,
    ListEdgeConfigsOutput,
    ListProjectDomainsOutput,
    ListProjectsOutput,
    ListTeamMembersOutput,
    ListTeamsOutput,
    ListWebhooksOutput,
    PauseProjectOutput,
    PromoteDeploymentOutput,
    RemoveProjectDomainOutput,
    RerequestCheckOutput,
    UnpauseProjectOutput,
    UpdateCheckOutput,
    UpdateDnsRecordOutput,
    UpdateEdgeConfigItemsOutput,
    UpdateEnvVarOutput,
    UpdateProjectDomainOutput,
    UpdateProjectOutput,
    VerifyProjectDomainOutput,
)

API = "https://api.vercel.com"
_API_KEY = "fake-vercel-token"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_56_actions(self) -> None:
        assert len(manifest.actions) == 56

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth_only(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_logo_is_themed(self) -> None:
        assert manifest.logo == "modulex:vercel-themed"

    def test_tools_tuple_has_56_entries(self) -> None:
        assert len(TOOLS) == 56


# --- Happy-path tests: deployments -----------------------------------------


@pytest.mark.asyncio
async def test_list_deployments(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v7/deployments",
        json={
            "deployments": [
                {"uid": "dpl_1", "name": "site", "url": "site.vercel.app", "state": "READY"}
            ],
            "pagination": {"next": 123},
        },
    )
    result = ListDeploymentsOutput.model_validate(
        await list_deployments.ainvoke(_args())
    )
    assert result.success is True
    assert result.deployments[0].uid == "dpl_1"
    assert result.count == 1
    assert result.has_more is True
    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


@pytest.mark.asyncio
async def test_get_deployment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v13/deployments/dpl_1",
        json={"id": "dpl_1", "name": "site", "readyState": "READY", "url": "site.vercel.app"},
    )
    result = GetDeploymentOutput.model_validate(
        await get_deployment.ainvoke(_args(deployment_id="dpl_1"))
    )
    assert result.success is True
    assert result.id == "dpl_1"
    assert result.ready_state == "READY"


@pytest.mark.asyncio
async def test_create_deployment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v13/deployments",
        json={"id": "dpl_2", "name": "site", "readyState": "QUEUED", "projectId": "prj_1"},
    )
    result = CreateDeploymentOutput.model_validate(
        await create_deployment.ainvoke(
            _args(name="site", git_source={"type": "github", "repo": "o/r", "ref": "main"})
        )
    )
    assert result.success is True
    assert result.id == "dpl_2"


@pytest.mark.asyncio
async def test_cancel_deployment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/v12/deployments/dpl_1/cancel",
        json={"id": "dpl_1", "readyState": "CANCELED"},
    )
    result = CancelDeploymentOutput.model_validate(
        await cancel_deployment.ainvoke(_args(deployment_id="dpl_1"))
    )
    assert result.success is True
    assert result.state == "CANCELED"


@pytest.mark.asyncio
async def test_delete_deployment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/v13/deployments/dpl_1",
        json={"uid": "dpl_1", "state": "DELETED"},
    )
    result = DeleteDeploymentOutput.model_validate(
        await delete_deployment.ainvoke(_args(deployment_id="dpl_1"))
    )
    assert result.success is True
    assert result.uid == "dpl_1"


@pytest.mark.asyncio
async def test_get_deployment_events(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v3/deployments/dpl_1/events",
        json=[{"type": "stdout", "text": "building", "id": "ev_1"}],
    )
    result = GetDeploymentEventsOutput.model_validate(
        await get_deployment_events.ainvoke(_args(deployment_id="dpl_1"))
    )
    assert result.success is True
    assert result.events[0].text == "building"
    assert result.count == 1


@pytest.mark.asyncio
async def test_list_deployment_files(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v6/deployments/dpl_1/files",
        json=[{"name": "index.html", "type": "file", "uid": "f_1"}],
    )
    result = ListDeploymentFilesOutput.model_validate(
        await list_deployment_files.ainvoke(_args(deployment_id="dpl_1"))
    )
    assert result.success is True
    assert result.files[0].name == "index.html"


@pytest.mark.asyncio
async def test_promote_deployment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=f"{API}/v10/projects/prj_1/promote/dpl_1", json={}
    )
    result = PromoteDeploymentOutput.model_validate(
        await promote_deployment.ainvoke(_args(project_id="prj_1", deployment_id="dpl_1"))
    )
    assert result.success is True
    assert result.promoted is True


# --- Happy-path tests: projects --------------------------------------------


@pytest.mark.asyncio
async def test_list_projects(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v10/projects",
        json={"projects": [{"id": "prj_1", "name": "site"}]},
    )
    result = ListProjectsOutput.model_validate(await list_projects.ainvoke(_args()))
    assert result.success is True
    assert result.projects[0].id == "prj_1"


@pytest.mark.asyncio
async def test_get_project(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v9/projects/prj_1",
        json={"id": "prj_1", "name": "site", "framework": "nextjs"},
    )
    result = GetProjectOutput.model_validate(
        await get_project.ainvoke(_args(project_id="prj_1"))
    )
    assert result.success is True
    assert result.framework == "nextjs"


@pytest.mark.asyncio
async def test_create_project(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v11/projects",
        json={"id": "prj_2", "name": "new-site"},
    )
    result = CreateProjectOutput.model_validate(
        await create_project.ainvoke(_args(name="new-site"))
    )
    assert result.success is True
    assert result.id == "prj_2"


@pytest.mark.asyncio
async def test_update_project(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/v9/projects/prj_1",
        json={"id": "prj_1", "name": "renamed"},
    )
    result = UpdateProjectOutput.model_validate(
        await update_project.ainvoke(_args(project_id="prj_1", name="renamed"))
    )
    assert result.success is True
    assert result.name == "renamed"


@pytest.mark.asyncio
async def test_delete_project(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="DELETE", url=f"{API}/v9/projects/prj_1", json={})
    result = DeleteProjectOutput.model_validate(
        await delete_project.ainvoke(_args(project_id="prj_1"))
    )
    assert result.success is True
    assert result.deleted is True


@pytest.mark.asyncio
async def test_pause_project(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=f"{API}/v1/projects/prj_1/pause", json={"id": "prj_1", "paused": True}
    )
    result = PauseProjectOutput.model_validate(
        await pause_project.ainvoke(_args(project_id="prj_1"))
    )
    assert result.success is True
    assert result.paused is True


@pytest.mark.asyncio
async def test_unpause_project(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v1/projects/prj_1/unpause",
        json={"id": "prj_1", "paused": False},
    )
    result = UnpauseProjectOutput.model_validate(
        await unpause_project.ainvoke(_args(project_id="prj_1"))
    )
    assert result.success is True
    assert result.paused is False


# --- Happy-path tests: project domains -------------------------------------


@pytest.mark.asyncio
async def test_list_project_domains(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v9/projects/prj_1/domains",
        json={"domains": [{"name": "ex.com", "apexName": "ex.com", "verified": True}]},
    )
    result = ListProjectDomainsOutput.model_validate(
        await list_project_domains.ainvoke(_args(project_id="prj_1"))
    )
    assert result.success is True
    assert result.domains[0].name == "ex.com"


@pytest.mark.asyncio
async def test_add_project_domain(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v10/projects/prj_1/domains",
        json={"name": "ex.com", "apexName": "ex.com", "verified": False},
    )
    result = AddProjectDomainOutput.model_validate(
        await add_project_domain.ainvoke(_args(project_id="prj_1", domain="ex.com"))
    )
    assert result.success is True
    assert result.name == "ex.com"


@pytest.mark.asyncio
async def test_update_project_domain(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/v9/projects/prj_1/domains/ex.com",
        json={"name": "ex.com", "verified": True, "redirect": "www.ex.com"},
    )
    result = UpdateProjectDomainOutput.model_validate(
        await update_project_domain.ainvoke(
            _args(project_id="prj_1", domain="ex.com", redirect="www.ex.com")
        )
    )
    assert result.success is True
    assert result.redirect == "www.ex.com"


@pytest.mark.asyncio
async def test_verify_project_domain(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v9/projects/prj_1/domains/ex.com/verify",
        json={"name": "ex.com", "verified": True},
    )
    result = VerifyProjectDomainOutput.model_validate(
        await verify_project_domain.ainvoke(_args(project_id="prj_1", domain="ex.com"))
    )
    assert result.success is True
    assert result.verified is True


@pytest.mark.asyncio
async def test_remove_project_domain(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/v9/projects/prj_1/domains/ex.com", json={}
    )
    result = RemoveProjectDomainOutput.model_validate(
        await remove_project_domain.ainvoke(_args(project_id="prj_1", domain="ex.com"))
    )
    assert result.success is True
    assert result.deleted is True


# --- Happy-path tests: environment variables -------------------------------


@pytest.mark.asyncio
async def test_get_env_vars(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v10/projects/prj_1/env",
        json={"envs": [{"id": "env_1", "key": "API_URL", "value": "x", "target": ["production"]}]},
    )
    result = GetEnvVarsOutput.model_validate(
        await get_env_vars.ainvoke(_args(project_id="prj_1"))
    )
    assert result.success is True
    assert result.envs[0].key == "API_URL"


@pytest.mark.asyncio
async def test_create_env_var(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v10/projects/prj_1/env",
        json={"created": {"id": "env_2", "key": "API_URL", "target": ["production"]}},
    )
    result = CreateEnvVarOutput.model_validate(
        await create_env_var.ainvoke(
            _args(project_id="prj_1", key="API_URL", value="x", target="production")
        )
    )
    assert result.success is True
    assert result.id == "env_2"


@pytest.mark.asyncio
async def test_update_env_var(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/v9/projects/prj_1/env/env_1",
        json={"id": "env_1", "key": "API_URL", "value": "y"},
    )
    result = UpdateEnvVarOutput.model_validate(
        await update_env_var.ainvoke(_args(project_id="prj_1", env_id="env_1", value="y"))
    )
    assert result.success is True
    assert result.value == "y"


@pytest.mark.asyncio
async def test_delete_env_var(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/v9/projects/prj_1/env/env_1", json={}
    )
    result = DeleteEnvVarOutput.model_validate(
        await delete_env_var.ainvoke(_args(project_id="prj_1", env_id="env_1"))
    )
    assert result.success is True
    assert result.deleted is True


# --- Happy-path tests: account domains -------------------------------------


@pytest.mark.asyncio
async def test_list_domains(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v5/domains",
        json={"domains": [{"id": "dom_1", "name": "ex.com", "verified": True}]},
    )
    result = ListDomainsOutput.model_validate(await list_domains.ainvoke(_args()))
    assert result.success is True
    assert result.domains[0].name == "ex.com"


@pytest.mark.asyncio
async def test_get_domain(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v5/domains/ex.com",
        json={"domain": {"id": "dom_1", "name": "ex.com", "verified": True}},
    )
    result = GetDomainOutput.model_validate(await get_domain.ainvoke(_args(domain="ex.com")))
    assert result.success is True
    assert result.id == "dom_1"


@pytest.mark.asyncio
async def test_add_domain(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v7/domains",
        json={"domain": {"id": "dom_2", "name": "new.com", "verified": False}},
    )
    result = AddDomainOutput.model_validate(await add_domain.ainvoke(_args(name="new.com")))
    assert result.success is True
    assert result.name == "new.com"


@pytest.mark.asyncio
async def test_delete_domain(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="DELETE", url=f"{API}/v6/domains/ex.com", json={"uid": "dom_1"})
    result = DeleteDomainOutput.model_validate(
        await delete_domain.ainvoke(_args(domain="ex.com"))
    )
    assert result.success is True
    assert result.deleted is True


@pytest.mark.asyncio
async def test_get_domain_config(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v6/domains/ex.com/config",
        json={"configuredBy": "CNAME", "misconfigured": False, "acceptedChallenges": ["dns-01"]},
    )
    result = GetDomainConfigOutput.model_validate(
        await get_domain_config.ainvoke(_args(domain="ex.com"))
    )
    assert result.success is True
    assert result.configured_by == "CNAME"


# --- Happy-path tests: DNS records -----------------------------------------


@pytest.mark.asyncio
async def test_list_dns_records(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v5/domains/ex.com/records",
        json={"records": [{"id": "rec_1", "name": "www", "type": "CNAME", "value": "x"}]},
    )
    result = ListDnsRecordsOutput.model_validate(
        await list_dns_records.ainvoke(_args(domain="ex.com"))
    )
    assert result.success is True
    assert result.records[0].type == "CNAME"


@pytest.mark.asyncio
async def test_create_dns_record(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/domains/ex.com/records",
        json={"uid": "rec_2", "updated": 1},
    )
    result = CreateDnsRecordOutput.model_validate(
        await create_dns_record.ainvoke(
            _args(domain="ex.com", record_name="www", record_type="CNAME", value="x")
        )
    )
    assert result.success is True
    assert result.uid == "rec_2"


@pytest.mark.asyncio
async def test_update_dns_record(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/v1/domains/records/rec_1",
        json={"id": "rec_1", "name": "www", "value": "y"},
    )
    result = UpdateDnsRecordOutput.model_validate(
        await update_dns_record.ainvoke(_args(record_id="rec_1", value="y"))
    )
    assert result.success is True
    assert result.value == "y"


@pytest.mark.asyncio
async def test_delete_dns_record(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/v2/domains/ex.com/records/rec_1", json={}
    )
    result = DeleteDnsRecordOutput.model_validate(
        await delete_dns_record.ainvoke(_args(domain="ex.com", record_id="rec_1"))
    )
    assert result.success is True
    assert result.deleted is True


# --- Happy-path tests: aliases ---------------------------------------------


@pytest.mark.asyncio
async def test_list_aliases(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v4/aliases",
        json={"aliases": [{"uid": "al_1", "alias": "ex.com"}]},
    )
    result = ListAliasesOutput.model_validate(await list_aliases.ainvoke(_args()))
    assert result.success is True
    assert result.aliases[0].alias == "ex.com"


@pytest.mark.asyncio
async def test_get_alias(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v4/aliases/al_1",
        json={"uid": "al_1", "alias": "ex.com", "deploymentId": "dpl_1"},
    )
    result = GetAliasOutput.model_validate(await get_alias.ainvoke(_args(alias_id="al_1")))
    assert result.success is True
    assert result.deployment_id == "dpl_1"


@pytest.mark.asyncio
async def test_create_alias(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/deployments/dpl_1/aliases",
        json={"uid": "al_2", "alias": "ex.com"},
    )
    result = CreateAliasOutput.model_validate(
        await create_alias.ainvoke(_args(deployment_id="dpl_1", alias="ex.com"))
    )
    assert result.success is True
    assert result.uid == "al_2"


@pytest.mark.asyncio
async def test_delete_alias(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/v2/aliases/al_1", json={"status": "SUCCESS"}
    )
    result = DeleteAliasOutput.model_validate(
        await delete_alias.ainvoke(_args(alias_id="al_1"))
    )
    assert result.success is True
    assert result.status == "SUCCESS"


# --- Happy-path tests: edge configs ----------------------------------------


@pytest.mark.asyncio
async def test_list_edge_configs(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/edge-config",
        json=[{"id": "ec_1", "slug": "my-config", "itemCount": 3}],
    )
    result = ListEdgeConfigsOutput.model_validate(await list_edge_configs.ainvoke(_args()))
    assert result.success is True
    assert result.edge_configs[0].slug == "my-config"


@pytest.mark.asyncio
async def test_get_edge_config(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/edge-config/ec_1",
        json={"id": "ec_1", "slug": "my-config", "itemCount": 3},
    )
    result = GetEdgeConfigOutput.model_validate(
        await get_edge_config.ainvoke(_args(edge_config_id="ec_1"))
    )
    assert result.success is True
    assert result.item_count == 3


@pytest.mark.asyncio
async def test_create_edge_config(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v1/edge-config",
        json={"id": "ec_2", "slug": "new-config"},
    )
    result = CreateEdgeConfigOutput.model_validate(
        await create_edge_config.ainvoke(_args(slug="new-config"))
    )
    assert result.success is True
    assert result.slug == "new-config"


@pytest.mark.asyncio
async def test_get_edge_config_items(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/edge-config/ec_1/items",
        json=[{"key": "flag", "value": True, "edgeConfigId": "ec_1"}],
    )
    result = GetEdgeConfigItemsOutput.model_validate(
        await get_edge_config_items.ainvoke(_args(edge_config_id="ec_1"))
    )
    assert result.success is True
    assert result.items[0].key == "flag"


@pytest.mark.asyncio
async def test_update_edge_config_items(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="PATCH", url=f"{API}/v1/edge-config/ec_1/items", json={})
    result = UpdateEdgeConfigItemsOutput.model_validate(
        await update_edge_config_items.ainvoke(
            _args(
                edge_config_id="ec_1",
                items=[{"operation": "upsert", "key": "flag", "value": True}],
            )
        )
    )
    assert result.success is True
    assert result.status == "ok"


@pytest.mark.asyncio
async def test_delete_edge_config(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="DELETE", url=f"{API}/v1/edge-config/ec_1", json={})
    result = DeleteEdgeConfigOutput.model_validate(
        await delete_edge_config.ainvoke(_args(edge_config_id="ec_1"))
    )
    assert result.success is True
    assert result.deleted is True


# --- Happy-path tests: webhooks --------------------------------------------


@pytest.mark.asyncio
async def test_list_webhooks(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/webhooks",
        json=[{"id": "wh_1", "url": "https://x.com/hook", "events": ["deployment.created"]}],
    )
    result = ListWebhooksOutput.model_validate(await list_webhooks.ainvoke(_args()))
    assert result.success is True
    assert result.webhooks[0].id == "wh_1"


@pytest.mark.asyncio
async def test_get_webhook(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/webhooks/wh_1",
        json={"id": "wh_1", "url": "https://x.com/hook", "events": ["deployment.created"]},
    )
    result = GetWebhookOutput.model_validate(
        await get_webhook.ainvoke(_args(webhook_id="wh_1"))
    )
    assert result.success is True
    assert result.url == "https://x.com/hook"


@pytest.mark.asyncio
async def test_create_webhook(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v1/webhooks",
        json={"id": "wh_2", "url": "https://x.com/hook", "secret": "s", "events": ["a"]},
    )
    result = CreateWebhookOutput.model_validate(
        await create_webhook.ainvoke(_args(url="https://x.com/hook", events="deployment.created"))
    )
    assert result.success is True
    assert result.secret == "s"


@pytest.mark.asyncio
async def test_delete_webhook(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="DELETE", url=f"{API}/v1/webhooks/wh_1", json={})
    result = DeleteWebhookOutput.model_validate(
        await delete_webhook.ainvoke(_args(webhook_id="wh_1"))
    )
    assert result.success is True
    assert result.deleted is True


# --- Happy-path tests: checks ----------------------------------------------


@pytest.mark.asyncio
async def test_create_check(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v1/deployments/dpl_1/checks",
        json={"id": "chk_1", "name": "perf", "status": "registered", "blocking": True},
    )
    result = CheckOutput.model_validate(
        await create_check.ainvoke(_args(deployment_id="dpl_1", name="perf", blocking=True))
    )
    assert result.success is True
    assert result.id == "chk_1"


@pytest.mark.asyncio
async def test_get_check(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/deployments/dpl_1/checks/chk_1",
        json={"id": "chk_1", "name": "perf", "status": "completed", "conclusion": "succeeded"},
    )
    result = GetCheckOutput.model_validate(
        await get_check.ainvoke(_args(deployment_id="dpl_1", check_id="chk_1"))
    )
    assert result.success is True
    assert result.conclusion == "succeeded"


@pytest.mark.asyncio
async def test_list_checks(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/deployments/dpl_1/checks",
        json={"checks": [{"id": "chk_1", "name": "perf", "status": "completed"}]},
    )
    result = ListChecksOutput.model_validate(
        await list_checks.ainvoke(_args(deployment_id="dpl_1"))
    )
    assert result.success is True
    assert result.checks[0].id == "chk_1"


@pytest.mark.asyncio
async def test_update_check(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/v1/deployments/dpl_1/checks/chk_1",
        json={"id": "chk_1", "name": "perf", "status": "completed", "conclusion": "failed"},
    )
    result = UpdateCheckOutput.model_validate(
        await update_check.ainvoke(
            _args(deployment_id="dpl_1", check_id="chk_1", conclusion="failed")
        )
    )
    assert result.success is True
    assert result.conclusion == "failed"


@pytest.mark.asyncio
async def test_rerequest_check(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=f"{API}/v1/deployments/dpl_1/checks/chk_1/rerequest", json={}
    )
    result = RerequestCheckOutput.model_validate(
        await rerequest_check.ainvoke(_args(deployment_id="dpl_1", check_id="chk_1"))
    )
    assert result.success is True
    assert result.rerequested is True


# --- Happy-path tests: teams & user ----------------------------------------


@pytest.mark.asyncio
async def test_list_teams(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/teams",
        json={"teams": [{"id": "team_1", "slug": "acme", "name": "Acme"}]},
    )
    result = ListTeamsOutput.model_validate(await list_teams.ainvoke(_args()))
    assert result.success is True
    assert result.teams[0].slug == "acme"


@pytest.mark.asyncio
async def test_get_team(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/teams/team_1",
        json={"id": "team_1", "slug": "acme", "name": "Acme"},
    )
    result = GetTeamOutput.model_validate(await get_team.ainvoke(_args(team_id="team_1")))
    assert result.success is True
    assert result.name == "Acme"


@pytest.mark.asyncio
async def test_list_team_members(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v3/teams/team_1/members",
        json={"members": [{"uid": "u_1", "username": "alice", "role": "OWNER"}]},
    )
    result = ListTeamMembersOutput.model_validate(
        await list_team_members.ainvoke(_args(team_id="team_1"))
    )
    assert result.success is True
    assert result.members[0].username == "alice"


@pytest.mark.asyncio
async def test_get_user(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/user",
        json={"user": {"id": "u_1", "username": "alice", "email": "a@x.com"}},
    )
    result = GetUserOutput.model_validate(await get_user.ainvoke(_args()))
    assert result.success is True
    assert result.username == "alice"


# --- Failure & credential paths --------------------------------------------


@pytest.mark.asyncio
async def test_non_2xx_returns_error(httpx_mock):  # type: ignore[no-untyped-def]
    """Vercel errors come back as 4xx/5xx; tools return success=False."""
    httpx_mock.add_response(
        method="GET", url=f"{API}/v10/projects", status_code=403, text="Forbidden"
    )
    result = ListProjectsOutput.model_validate(await list_projects.ainvoke(_args()))
    assert result.success is False
    assert result.error is not None
    assert "403" in result.error


@pytest.mark.asyncio
async def test_empty_api_key_short_circuits() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result = GetUserOutput.model_validate(await get_user.ainvoke({"api_key": ""}))
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_result_is_dict_at_tool_boundary(httpx_mock):  # type: ignore[no-untyped-def]
    """The @tool boundary returns a plain dict (serialize_pydantic_return)."""
    httpx_mock.add_response(
        method="GET", url=f"{API}/v2/user", json={"user": {"id": "u_1"}}
    )
    result_dict = await get_user.ainvoke(_args())
    assert isinstance(result_dict, dict)
    assert result_dict["success"] is True

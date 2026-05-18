"""Happy-path tests for every linkedin @tool, plus a manifest sanity check."""
from __future__ import annotations

import re
from typing import Any

import pytest

from modulex_integrations.tools.linkedin import (
    TOOLS,
    create_comment,
    create_image_post_organization,
    create_image_post_user,
    create_like_on_share,
    create_text_post_organization,
    create_text_post_user,
    delete_post,
    fetch_ad_account,
    get_current_member_profile,
    get_member_profile,
    get_multiple_member_profiles,
    get_org_member_access,
    get_organization_access_control,
    get_organization_administrators,
    get_profile_picture_fields,
    manifest,
    retrieve_comments_on_comments,
    retrieve_comments_shares,
    search_organization,
)
from modulex_integrations.tools.linkedin.outputs import (
    CreateCommentOutput,
    CreateImagePostOrganizationOutput,
    CreateImagePostUserOutput,
    CreateLikeOnShareOutput,
    CreateTextPostOrganizationOutput,
    CreateTextPostUserOutput,
    DeletePostOutput,
    FetchAdAccountOutput,
    GetCurrentMemberProfileOutput,
    GetMemberProfileOutput,
    GetMultipleMemberProfilesOutput,
    GetOrganizationAccessControlOutput,
    GetOrganizationAdministratorsOutput,
    GetOrgMemberAccessOutput,
    GetProfilePictureFieldsOutput,
    RetrieveCommentsOnCommentsOutput,
    RetrieveCommentsSharesOutput,
    SearchOrganizationOutput,
)

API = "https://api.linkedin.com/rest"
API_V2 = "https://api.linkedin.com/v2"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_18_actions(self) -> None:
        assert len(manifest.actions) == 18

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_comment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/socialActions/urn%3Ali%3Ashare%3A123/comments",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
        },
        status_code=201,
    )

    result_dict = await create_comment.ainvoke(
        _args(
            urn_to_comment="urn:li:share:123",
            actor="urn:li:person:ABC",
            message="Great post!",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateCommentOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_image_post_organization(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/images?action=initializeUpload",
        json={
            "value": {
                "uploadUrl": "https://www.linkedin.com/dms/uploads/fake",
                "image": "urn:li:image:fake123",
            },
        },
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/image.png",
        content=b"fakeimagebytes",
        status_code=200,
    )
    httpx_mock.add_response(
        method="PUT",
        url="https://www.linkedin.com/dms/uploads/fake",
        status_code=201,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/posts",
        status_code=201,
        headers={"x-restli-id": "urn:li:share:456"},
    )

    result_dict = await create_image_post_organization.ainvoke(
        _args(
            organization_id="12345",
            image_url="https://example.com/image.png",
            text="Check out this image!",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateImagePostOrganizationOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_image_post_user(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me",
        json={"id": "person123"},
        status_code=200,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/images?action=initializeUpload",
        json={
            "value": {
                "uploadUrl": "https://www.linkedin.com/dms/uploads/fake2",
                "image": "urn:li:image:fake456",
            },
        },
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/photo.jpg",
        content=b"fakephoto",
        status_code=200,
    )
    httpx_mock.add_response(
        method="PUT",
        url="https://www.linkedin.com/dms/uploads/fake2",
        status_code=201,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/posts",
        status_code=201,
        headers={"x-restli-id": "urn:li:share:789"},
    )

    result_dict = await create_image_post_user.ainvoke(
        _args(
            image_url="https://example.com/photo.jpg",
            text="My photo post",
            visibility="PUBLIC",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateImagePostUserOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_like_on_share(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/socialActions/urn%3Ali%3Ashare%3A456/likes",
        status_code=201,
    )

    result_dict = await create_like_on_share.ainvoke(
        _args(
            parent_urn="urn:li:share:456",
            actor="urn:li:person:ABC",
            object="urn:li:share:456",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateLikeOnShareOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_text_post_organization(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/posts",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
        },
        status_code=201,
    )

    result_dict = await create_text_post_organization.ainvoke(
        _args(
            organization_id="12345",
            text="Hello from our org!",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateTextPostOrganizationOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_text_post_user(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me",
        json={"id": "person123"},
        status_code=200,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/posts",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
        },
        status_code=201,
    )

    result_dict = await create_text_post_user.ainvoke(
        _args(
            visibility="PUBLIC",
            text="Hello LinkedIn!",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateTextPostUserOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_post(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/posts/urn%3Ali%3Ashare%3A123",
        status_code=204,
    )

    result_dict = await delete_post.ainvoke(
        _args(post_id="urn:li:share:123")
    )

    assert isinstance(result_dict, dict)
    result = DeletePostOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_fetch_ad_account(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/adAccounts/123456",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
        },
        status_code=200,
    )

    result_dict = await fetch_ad_account.ainvoke(
        _args(ad_account_id="123456")
    )

    assert isinstance(result_dict, dict)
    result = FetchAdAccountOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_current_member_profile(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me",
        json={
            "id": "abc123",
            "firstName": {"localized": {"en_US": "John"}},
            "lastName": {"localized": {"en_US": "Doe"}},
        },
        status_code=200,
    )

    result_dict = await get_current_member_profile.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = GetCurrentMemberProfileOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None
    assert result.data["id"] == "abc123"


@pytest.mark.asyncio
async def test_get_member_profile(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/people/(id:person456)",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
        },
        status_code=200,
    )

    result_dict = await get_member_profile.ainvoke(
        _args(person_id="person456")
    )

    assert isinstance(result_dict, dict)
    result = GetMemberProfileOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_multiple_member_profiles(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/people?ids=List((id:p1),(id:p2))",
        json={
            "results": {
                "p1": {"id": "p1", "firstName": "Alice"},
                "p2": {"id": "p2", "firstName": "Bob"},
            },
        },
        status_code=200,
    )

    result_dict = await get_multiple_member_profiles.ainvoke(
        _args(people_ids=["p1", "p2"])
    )

    assert isinstance(result_dict, dict)
    result = GetMultipleMemberProfilesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.results) == 2


@pytest.mark.asyncio
async def test_get_org_member_access(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{re.escape(API)}/organizationAcls\?.*"),
        json={
            "elements": [
                {
                    "role": "ADMINISTRATOR",
                    "state": "APPROVED",
                    "organization": "urn:li:organization:12345",
                },
            ],
        },
        status_code=200,
    )

    result_dict = await get_org_member_access.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = GetOrgMemberAccessOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None


@pytest.mark.asyncio
async def test_get_organization_access_control(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{re.escape(API)}/organizationAcls\?.*"),
        json={
            "elements": [
                {"role": "ADMINISTRATOR", "state": "APPROVED"},
            ],
        },
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{re.escape(API)}/organizationAcls\?.*"),
        json={"elements": []},
        status_code=200,
    )

    result_dict = await get_organization_access_control.ainvoke(
        _args(organization_id="12345")
    )

    assert isinstance(result_dict, dict)
    result = GetOrganizationAccessControlOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_organization_administrators(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{re.escape(API)}/organizationAcls\?.*"),
        json={
            "elements": [
                {"role": "ADMINISTRATOR", "state": "APPROVED", "roleAssignee": "urn:li:person:admin1"},
            ],
        },
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{re.escape(API)}/organizationAcls\?.*"),
        json={"elements": []},
        status_code=200,
    )

    result_dict = await get_organization_administrators.ainvoke(
        _args(organization_id="12345")
    )

    assert isinstance(result_dict, dict)
    result = GetOrganizationAdministratorsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_profile_picture_fields(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{re.escape(API_V2)}/me\??.*"),
        json={
            "id": "abc123",
            "profilePicture": {
                # TODO: fill in a representative response shape from the upstream API docs
            },
        },
        status_code=200,
    )

    result_dict = await get_profile_picture_fields.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = GetProfilePictureFieldsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_retrieve_comments_on_comments(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{re.escape(API)}/socialActions/urn%3Ali%3Acomment%3A123/comments\?.*"),
        json={
            "elements": [
                {"actor": "urn:li:person:ABC", "message": {"text": "Reply!"}},
            ],
        },
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{re.escape(API)}/socialActions/urn%3Ali%3Acomment%3A123/comments\?.*"),
        json={"elements": []},
        status_code=200,
    )

    result_dict = await retrieve_comments_on_comments.ainvoke(
        _args(comment_urn="urn:li:comment:123")
    )

    assert isinstance(result_dict, dict)
    result = RetrieveCommentsOnCommentsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.elements) == 1


@pytest.mark.asyncio
async def test_retrieve_comments_shares(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{re.escape(API)}/socialActions/urn%3Ali%3Ashare%3A789/comments\?.*"),
        json={
            "elements": [
                {"actor": "urn:li:person:XYZ", "message": {"text": "Nice share!"}},
            ],
        },
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{re.escape(API)}/socialActions/urn%3Ali%3Ashare%3A789/comments\?.*"),
        json={"elements": []},
        status_code=200,
    )

    result_dict = await retrieve_comments_shares.ainvoke(
        _args(entity_urn="urn:li:share:789")
    )

    assert isinstance(result_dict, dict)
    result = RetrieveCommentsSharesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.elements) == 1


@pytest.mark.asyncio
async def test_search_organization(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{re.escape(API)}/organizations\?.*"),
        json={
            "elements": [
                {"id": 12345, "vanityName": "acme-corp"},
            ],
        },
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{re.escape(API)}/organizations\?.*"),
        json={"elements": []},
        status_code=200,
    )

    result_dict = await search_organization.ainvoke(
        _args(search_by="vanityName", search_term="acme-corp")
    )

    assert isinstance(result_dict, dict)
    result = SearchOrganizationOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.elements) == 1


@pytest.mark.asyncio
async def test_get_current_member_profile_empty_token():  # type: ignore[no-untyped-def]
    """Failure path: empty credential returns success=False without hitting the wire."""
    result_dict = await get_current_member_profile.ainvoke(
        _args(auth_data={})
    )

    assert isinstance(result_dict, dict)
    result = GetCurrentMemberProfileOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None

"""Tests for the Wikipedia integration.

The JSON fixtures below are trimmed copies of real responses from
``en.wikipedia.org``: same field names, same nesting, same
protocol-relative thumbnail URLs on search hits, same ``W/"..."`` weak
ETag on the page-content response, and the same ``303``/``307`` redirects
the random-page and page-content endpoints answer with.
"""
from __future__ import annotations

from typing import Any

import httpx
import pytest

from modulex_integrations.tools.wikipedia import (
    TOOLS,
    content,
    manifest,
    random,
    search,
    summary,
)
from modulex_integrations.tools.wikipedia.outputs import (
    ContentOutput,
    RandomOutput,
    SearchOutput,
    SummaryOutput,
)

EN = "https://en.wikipedia.org"
TR = "https://tr.wikipedia.org"


def _args(**extra: Any) -> dict[str, Any]:
    """Build an ``.ainvoke`` payload as ``dict[str, Any]``.

    Bypasses mypy's TypedDict-spread check on LangChain's typed
    ``.ainvoke()`` overload.
    """
    return dict(extra)


_SUMMARY_JSON: dict[str, Any] = {
    "type": "standard",
    "title": "Python (programming language)",
    "displaytitle": '<span lang="en" dir="ltr">Python (programming language)</span>',
    "namespace": {"id": 0, "text": ""},
    "wikibase_item": "Q28865",
    "titles": {
        "canonical": "Python_(programming_language)",
        "normalized": "Python (programming language)",
    },
    "pageid": 23862,
    "thumbnail": {
        "source": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/"
            "Python-logo-notext.svg/330px-Python-logo-notext.svg.png"
        ),
        "width": 330,
        "height": 330,
    },
    "originalimage": {
        "source": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/"
            "Python-logo-notext.svg/120px-Python-logo-notext.svg.png"
        ),
        "width": 110,
        "height": 110,
    },
    "lang": "en",
    "dir": "ltr",
    "revision": "1366771536",
    "tid": "51f41fa2-8bc4-11f1-954c-8ff898df3539",
    "timestamp": "2026-07-30T03:11:13Z",
    "description": "General-purpose programming language",
    "description_source": "local",
    "content_urls": {
        "desktop": {
            "page": "https://en.wikipedia.org/wiki/Python_(programming_language)",
            "revisions": (
                "https://en.wikipedia.org/wiki/Python_(programming_language)?action=history"
            ),
            "edit": "https://en.wikipedia.org/wiki/Python_(programming_language)?action=edit",
            "talk": "https://en.wikipedia.org/wiki/Talk:Python_(programming_language)",
        },
        "mobile": {
            "page": "https://en.m.wikipedia.org/wiki/Python_(programming_language)",
            "revisions": (
                "https://en.m.wikipedia.org/wiki/Special:History/Python_(programming_language)"
            ),
            "edit": "https://en.m.wikipedia.org/wiki/Python_(programming_language)?action=edit",
            "talk": "https://en.m.wikipedia.org/wiki/Talk:Python_(programming_language)",
        },
    },
    "extract": "Python is a high-level, general-purpose programming language.",
    "extract_html": "<p><b>Python</b> is a high-level, general-purpose programming language.</p>",
}


_SUMMARY_WITH_COORDINATES_JSON: dict[str, Any] = {
    "type": "standard",
    "title": "Istanbul",
    "displaytitle": "Istanbul",
    "pageid": 15681,
    "lang": "en",
    "dir": "ltr",
    "timestamp": "2026-07-28T10:00:00Z",
    "description": "Largest city in Turkey",
    "extract": "Istanbul is the largest city in Turkey.",
    "coordinates": {"lat": 41.0136, "lon": 28.955},
    "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Istanbul"}},
}


_DISAMBIGUATION_JSON: dict[str, Any] = {
    "type": "disambiguation",
    "title": "Mercury",
    "displaytitle": "Mercury",
    "pageid": 18980,
    "lang": "en",
    "dir": "ltr",
    "timestamp": "2026-06-01T00:00:00Z",
    "extract": "Mercury most commonly refers to: Mercury (planet), Mercury (element).",
}


_SEARCH_JSON: dict[str, Any] = {
    "pages": [
        {
            "id": 23862,
            "key": "Python_(programming_language)",
            "title": "Python (programming language)",
            "excerpt": '<span class="searchmatch">Python</span> supports multiple paradigms.',
            "matched_title": None,
            "anchor": None,
            "description": "General-purpose programming language",
            "thumbnail": {
                "mimetype": "image/svg+xml",
                "width": 60,
                "height": 60,
                "duration": None,
                "url": (
                    "//upload.wikimedia.org/wikipedia/commons/thumb/c/c3/"
                    "Python-logo-notext.svg/60px-Python-logo-notext.svg.png"
                ),
            },
        },
        {
            "id": 21356332,
            "key": "History_of_Python",
            "title": "History of Python",
            "excerpt": 'The <span class="searchmatch">Python</span> language began in 1989.',
            "matched_title": None,
            "anchor": None,
            "description": "History of the Python programming language",
            "thumbnail": None,
        },
    ]
}


_WITH_HTML_JSON: dict[str, Any] = {
    "id": 9228,
    "key": "Earth",
    "title": "Earth",
    "latest": {"id": 1366037442, "timestamp": "2026-07-25T22:32:42Z"},
    "content_model": "wikitext",
    "license": {
        "url": "https://creativecommons.org/licenses/by-sa/4.0/deed.en",
        "title": "Creative Commons Attribution-Share Alike 4.0",
    },
    "html": "<!DOCTYPE html>\n<html><body><p>Earth is the third planet.</p></body></html>",
}

_WITH_HTML_ETAG = 'W/"1366037442/3ff601c3-8fb9-11f1-8a91-05a571ebd58f/view/with_html"'


_RANDOM_JSON: dict[str, Any] = {
    "type": "standard",
    "title": "Brown House (Rehoboth, Massachusetts)",
    "displaytitle": "Brown House (Rehoboth, Massachusetts)",
    "pageid": 21044553,
    "lang": "en",
    "dir": "ltr",
    "timestamp": "2026-02-11T04:21:00Z",
    "description": "Historic house in Massachusetts, United States",
    "extract": "The Brown House is a historic house in Rehoboth, Massachusetts.",
    "thumbnail": {
        "source": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Brown.jpg",
        "width": 320,
        "height": 240,
    },
    "content_urls": {
        "desktop": {"page": "https://en.wikipedia.org/wiki/Brown_House"},
        "mobile": {"page": "https://en.m.wikipedia.org/wiki/Brown_House"},
    },
}


# The Wikimedia REST API answers a missing page with 404 and a JSON body.
_NOT_FOUND_JSON: dict[str, Any] = {
    "type": "https://mediawiki.org/wiki/HyperSwitch/errors/not_found",
    "title": "Not found.",
    "method": "get",
    "detail": "Page or revision not found.",
}

# The MediaWiki core REST API uses a different error envelope.
_CORE_NOT_FOUND_JSON: dict[str, Any] = {
    "errorKey": "rest-nonexistent-title",
    "messageTranslations": {"en": "The specified page (Zzzq_no_such_page) does not exist"},
    "httpCode": 404,
    "httpReason": "Not Found",
}

_CORE_BAD_LIMIT_JSON: dict[str, Any] = {
    "error": "parameter-validation-failed",
    "name": "limit",
    "value": "101",
    "messageTranslations": {
        "en": 'The value "101" for parameter "limit" must be between 1 and 100.'
    },
    "httpCode": 400,
    "httpReason": "Bad Request",
}


class TestManifest:
    def test_manifest_exposes_four_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_modulex_key_auth(self) -> None:
        # The Wikipedia APIs take no credential of any kind; the single
        # modulex_key schema exists only so the runtime's credential
        # resolution step has something to resolve.
        assert {a.auth_type for a in manifest.auth_schemas} == {"modulex_key"}

    def test_manifest_declares_no_api_key_action_param(self) -> None:
        # api_key is injected by the runtime and must never be redeclared
        # as an action parameter.
        for action in manifest.actions:
            assert "api_key" not in action.parameters

    def test_manifest_logo_follows_convention(self) -> None:
        assert manifest.logo == "modulex:wikipedia-themed"

    def test_every_action_accepts_a_language(self) -> None:
        for action in manifest.actions:
            assert "language" in action.parameters
            assert action.parameters["language"].default == "en"


# --- Happy paths -----------------------------------------------------------


@pytest.mark.asyncio
async def test_summary(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/summary/Python_%28programming_language%29",
        json=_SUMMARY_JSON,
    )

    result_dict = await summary.ainvoke(_args(page_title="Python (programming language)"))
    assert isinstance(result_dict, dict)
    result = SummaryOutput.model_validate(result_dict)

    assert result.success is True
    assert result.error is None
    assert result.summary is not None
    assert result.summary.type == "standard"
    assert result.summary.title == "Python (programming language)"
    assert result.summary.pageid == 23862
    assert result.summary.description == "General-purpose programming language"
    assert result.summary.extract.startswith("Python is a high-level")  # type: ignore[union-attr]
    assert result.summary.lang == "en"
    assert result.summary.dir == "ltr"
    assert result.summary.wikibase_item == "Q28865"
    assert result.summary.thumbnail is not None
    assert result.summary.thumbnail.width == 330
    assert result.summary.originalimage is not None
    assert result.summary.originalimage.height == 110
    assert result.summary.content_urls is not None
    assert result.summary.content_urls.desktop is not None
    assert result.summary.content_urls.desktop.page == (
        "https://en.wikipedia.org/wiki/Python_(programming_language)"
    )
    assert result.summary.content_urls.mobile is not None
    assert result.summary.content_urls.mobile.talk is not None
    # No coordinates on this article — the block is absent, not empty.
    assert result.summary.coordinates is None


@pytest.mark.asyncio
async def test_summary_spaces_become_underscores(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/summary/Mercury",
        json=_DISAMBIGUATION_JSON,
    )

    # A disambiguation page is a successful lookup, not an error; the
    # caller distinguishes it via summary.type.
    result_dict = await summary.ainvoke(_args(page_title="  Mercury  "))
    result = SummaryOutput.model_validate(result_dict)

    assert result.success is True
    assert result.summary is not None
    assert result.summary.type == "disambiguation"


@pytest.mark.asyncio
async def test_summary_parses_coordinates(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/summary/Istanbul",
        json=_SUMMARY_WITH_COORDINATES_JSON,
    )

    result_dict = await summary.ainvoke(_args(page_title="Istanbul"))
    result = SummaryOutput.model_validate(result_dict)

    assert result.success is True
    assert result.summary is not None
    assert result.summary.coordinates is not None
    assert result.summary.coordinates.lat == pytest.approx(41.0136)
    assert result.summary.coordinates.lon == pytest.approx(28.955)


@pytest.mark.asyncio
async def test_summary_encodes_a_slash_in_the_title(httpx_mock: Any) -> None:
    # 'AC/DC' must not open a new path segment.
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/summary/AC%2FDC",
        json={"type": "standard", "title": "AC/DC", "pageid": 304, "lang": "en"},
    )

    result_dict = await summary.ainvoke(_args(page_title="AC/DC"))
    result = SummaryOutput.model_validate(result_dict)

    assert result.success is True
    assert result.summary is not None
    assert result.summary.title == "AC/DC"


@pytest.mark.asyncio
async def test_summary_uses_the_requested_language_edition(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{TR}/api/rest_v1/page/summary/Python_%28programlama_dili%29",
        json={
            "type": "standard",
            "title": "Python (programlama dili)",
            "pageid": 12345,
            "lang": "tr",
            "dir": "ltr",
        },
    )

    result_dict = await summary.ainvoke(
        _args(page_title="Python (programlama dili)", language="TR")
    )
    result = SummaryOutput.model_validate(result_dict)

    assert result.success is True
    assert result.summary is not None
    assert result.summary.lang == "tr"


@pytest.mark.asyncio
async def test_search(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/w/rest.php/v1/search/page?q=python+programming&limit=2",
        json=_SEARCH_JSON,
    )

    result_dict = await search.ainvoke(_args(query="python programming", search_limit=2))
    assert isinstance(result_dict, dict)
    result = SearchOutput.model_validate(result_dict)

    assert result.success is True
    assert result.error is None
    assert result.query == "python programming"
    assert result.total_hits == 2
    assert len(result.search_results) == 2

    first = result.search_results[0]
    assert first.id == 23862
    assert first.key == "Python_(programming_language)"
    assert first.title == "Python (programming language)"
    assert first.description == "General-purpose programming language"
    assert first.matched_title is None
    assert 'class="searchmatch"' in (first.excerpt or "")
    # The page URL is derived from the key; /search/page does not send one.
    assert first.url == f"{EN}/wiki/Python_%28programming_language%29"
    assert first.thumbnail is not None
    # Protocol-relative thumbnail URLs are expanded so they are fetchable.
    assert first.thumbnail.url is not None
    assert first.thumbnail.url.startswith("https://upload.wikimedia.org/")
    assert first.thumbnail.mimetype == "image/svg+xml"
    assert first.thumbnail.duration is None
    assert first.thumbnail.size is None

    assert result.search_results[1].thumbnail is None


@pytest.mark.asyncio
async def test_search_clamps_the_limit(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/w/rest.php/v1/search/page?q=python&limit=100",
        json={"pages": []},
    )

    result_dict = await search.ainvoke(_args(query="python", search_limit=5000))
    result = SearchOutput.model_validate(result_dict)

    assert result.success is True
    assert result.search_results == []
    assert result.total_hits == 0


@pytest.mark.asyncio
async def test_search_uses_the_default_limit(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/w/rest.php/v1/search/page?q=quantum&limit=10",
        json={"pages": []},
    )

    result_dict = await search.ainvoke(_args(query="quantum"))
    result = SearchOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_content(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/w/rest.php/v1/page/Earth/with_html",
        json=_WITH_HTML_JSON,
        headers={"etag": _WITH_HTML_ETAG},
    )

    result_dict = await content.ainvoke(_args(page_title="Earth"))
    assert isinstance(result_dict, dict)
    result = ContentOutput.model_validate(result_dict)

    assert result.success is True
    assert result.error is None
    assert result.content is not None
    assert result.content.title == "Earth"
    assert result.content.pageid == 9228
    assert result.content.revision == 1366037442
    assert result.content.timestamp == "2026-07-25T22:32:42Z"
    assert result.content.content_model == "wikitext"
    assert result.content.content_format == "text/html"
    assert result.content.tid == _WITH_HTML_ETAG
    assert result.content.html == _WITH_HTML_JSON["html"]
    assert result.content.html_length == len(_WITH_HTML_JSON["html"])
    assert result.content.truncated is False


@pytest.mark.asyncio
async def test_content_truncates_long_html(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/w/rest.php/v1/page/Earth/with_html",
        json=_WITH_HTML_JSON,
    )

    result_dict = await content.ainvoke(_args(page_title="Earth", max_length=20))
    result = ContentOutput.model_validate(result_dict)

    assert result.success is True
    assert result.content is not None
    assert result.content.html == _WITH_HTML_JSON["html"][:20]
    assert result.content.truncated is True
    assert result.content.html_length == len(_WITH_HTML_JSON["html"])
    # tid stays None when the response carries no ETag.
    assert result.content.tid is None


@pytest.mark.asyncio
async def test_content_can_disable_truncation(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/w/rest.php/v1/page/Earth/with_html",
        json=_WITH_HTML_JSON,
    )

    result_dict = await content.ainvoke(_args(page_title="Earth", max_length=0))
    result = ContentOutput.model_validate(result_dict)

    assert result.success is True
    assert result.content is not None
    assert result.content.html == _WITH_HTML_JSON["html"]
    assert result.content.truncated is False


@pytest.mark.asyncio
async def test_content_follows_the_redirect_for_a_redirect_title(httpx_mock: Any) -> None:
    # A redirect page answers 307 pointing at the canonical title.
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/w/rest.php/v1/page/Python_programming_language/with_html",
        status_code=307,
        headers={
            "Location": (
                f"{EN}/w/rest.php/v1/page/Python_%28programming_language%29"
                "/with_html?redirect=no"
            )
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{EN}/w/rest.php/v1/page/Python_%28programming_language%29"
            "/with_html?redirect=no"
        ),
        json=_WITH_HTML_JSON,
    )

    result_dict = await content.ainvoke(_args(page_title="Python programming language"))
    result = ContentOutput.model_validate(result_dict)

    assert result.success is True
    assert result.content is not None
    assert result.content.pageid == 9228


@pytest.mark.asyncio
async def test_random(httpx_mock: Any) -> None:
    # /page/random/summary answers 303 with the drawn article's URL.
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/random/summary",
        status_code=303,
        headers={
            "Location": (
                f"{EN}/api/rest_v1/page/summary/"
                "Brown_House_%28Rehoboth%2C_Massachusetts%29"
            )
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/summary/Brown_House_%28Rehoboth%2C_Massachusetts%29",
        json=_RANDOM_JSON,
    )

    result_dict = await random.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = RandomOutput.model_validate(result_dict)

    assert result.success is True
    assert result.error is None
    assert result.random_page is not None
    assert result.random_page.title == "Brown House (Rehoboth, Massachusetts)"
    assert result.random_page.pageid == 21044553
    assert result.random_page.type == "standard"
    assert result.random_page.thumbnail is not None
    assert result.random_page.thumbnail.width == 320
    assert result.random_page.content_urls is not None
    assert result.random_page.content_urls.mobile is not None
    assert result.random_page.content_urls.mobile.page == (
        "https://en.m.wikipedia.org/wiki/Brown_House"
    )


@pytest.mark.asyncio
async def test_random_in_another_language_edition(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{TR}/api/rest_v1/page/random/summary",
        json={"type": "standard", "title": "Bir sayfa", "pageid": 7, "lang": "tr"},
    )

    result_dict = await random.ainvoke(_args(language="tr"))
    result = RandomOutput.model_validate(result_dict)

    assert result.success is True
    assert result.random_page is not None
    assert result.random_page.lang == "tr"


@pytest.mark.asyncio
async def test_api_key_is_accepted_and_ignored(httpx_mock: Any) -> None:
    # The runtime injects api_key for modulex_key auth; the function must
    # accept it without sending it anywhere.
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/summary/Earth",
        json={"type": "standard", "title": "Earth", "pageid": 9228, "lang": "en"},
    )

    result_dict = await summary.ainvoke(_args(page_title="Earth", api_key="ignored-value"))
    result = SummaryOutput.model_validate(result_dict)

    assert result.success is True
    request = httpx_mock.get_requests()[0]
    assert "ignored-value" not in str(request.url)
    assert "ignored-value" not in str(dict(request.headers))


@pytest.mark.asyncio
async def test_requests_send_a_descriptive_user_agent(httpx_mock: Any) -> None:
    # Wikimedia throttles or refuses generic agents.
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/summary/Earth",
        json={"type": "standard", "title": "Earth", "pageid": 9228},
    )

    await summary.ainvoke(_args(page_title="Earth"))

    user_agent = httpx_mock.get_requests()[0].headers["user-agent"]
    assert user_agent == "modulex-integrations/1.0 (+https://modulex.dev)"


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_summary_reports_a_missing_page(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/summary/Zzzq_no_such_page",
        status_code=404,
        json=_NOT_FOUND_JSON,
    )

    result_dict = await summary.ainvoke(_args(page_title="Zzzq no such page"))
    result = SummaryOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "404" in result.error
    # Wikipedia's own 404 body is unhelpful ("Internal error" from the
    # cache layer), so the missing page is named explicitly instead.
    assert result.error == "Wikipedia has no page titled 'Zzzq no such page' (HTTP 404)."
    assert result.summary is None


@pytest.mark.asyncio
async def test_summary_reports_a_missing_page_behind_the_cache_error_body(
    httpx_mock: Any,
) -> None:
    # The cached summary endpoint answers a missing page with a body that
    # says "Internal error"; it must not be echoed back as a server fault.
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/summary/Zzzq_no_such_page",
        status_code=404,
        json={"status": 404, "type": "Internal error"},
    )

    result_dict = await summary.ainvoke(_args(page_title="Zzzq no such page"))
    result = SummaryOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "Internal error" not in result.error
    assert "has no page titled" in result.error


@pytest.mark.asyncio
async def test_content_reports_a_missing_page(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/w/rest.php/v1/page/Zzzq_no_such_page/with_html",
        status_code=404,
        json=_CORE_NOT_FOUND_JSON,
    )

    result_dict = await content.ainvoke(_args(page_title="Zzzq no such page"))
    result = ContentOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "404" in result.error
    assert result.error == "Wikipedia has no page titled 'Zzzq no such page' (HTTP 404)."
    assert result.content is None


@pytest.mark.asyncio
async def test_search_reports_a_rejected_parameter(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/w/rest.php/v1/search/page?q=python&limit=10",
        status_code=400,
        json=_CORE_BAD_LIMIT_JSON,
    )

    result_dict = await search.ainvoke(_args(query="python"))
    result = SearchOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "400" in result.error
    assert "must be between 1 and 100" in result.error
    assert result.search_results == []
    # The query is echoed back even on the failure branch.
    assert result.query == "python"


@pytest.mark.asyncio
async def test_random_reports_a_timeout(httpx_mock: Any) -> None:
    httpx_mock.add_exception(httpx.TimeoutException("timed out"))

    result_dict = await random.ainvoke(_args())
    result = RandomOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "timed out" in result.error
    assert result.random_page is None


@pytest.mark.asyncio
async def test_summary_reports_a_transport_error(httpx_mock: Any) -> None:
    httpx_mock.add_exception(httpx.ConnectError("nodename nor servname provided"))

    result_dict = await summary.ainvoke(_args(page_title="Earth"))
    result = SummaryOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "failed" in result.error


@pytest.mark.asyncio
async def test_summary_reports_a_non_json_body(httpx_mock: Any) -> None:
    # A cache or proxy in front of the API can answer 200 with HTML.
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/summary/Earth",
        text="<!DOCTYPE html><html><body>Our servers are experiencing a problem</body></html>",
    )

    result_dict = await summary.ainvoke(_args(page_title="Earth"))
    result = SummaryOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "not valid JSON" in result.error


@pytest.mark.asyncio
async def test_summary_reports_a_non_json_error_body(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/summary/Earth",
        status_code=403,
        text="Scripts should use an informative User-Agent string.",
    )

    result_dict = await summary.ainvoke(_args(page_title="Earth"))
    result = SummaryOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "403" in result.error
    assert "informative User-Agent" in result.error


# --- Envelope invariant: shape confusion -----------------------------------
#
# A 200 whose body is not the documented object must not raise past the
# @tool boundary.


@pytest.mark.asyncio
async def test_summary_survives_a_bare_array_body(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/summary/Earth",
        json=[],
    )

    result_dict = await summary.ainvoke(_args(page_title="Earth"))
    assert isinstance(result_dict, dict)
    result = SummaryOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "unexpected response shape" in result.error


@pytest.mark.asyncio
async def test_search_survives_a_bare_array_body(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/w/rest.php/v1/search/page?q=python&limit=10",
        json=["python", ["Python"], [""], ["https://en.wikipedia.org/wiki/Python"]],
    )

    result_dict = await search.ainvoke(_args(query="python"))
    result = SearchOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "unexpected response shape" in result.error


@pytest.mark.asyncio
async def test_search_survives_non_object_page_entries(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/w/rest.php/v1/search/page?q=python&limit=10",
        json={"pages": ["Python", None, 42]},
    )

    result_dict = await search.ainvoke(_args(query="python"))
    result = SearchOutput.model_validate(result_dict)

    assert result.success is True
    assert len(result.search_results) == 3
    assert all(hit.title is None and hit.url is None for hit in result.search_results)


@pytest.mark.asyncio
async def test_random_survives_a_null_body(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/random/summary",
        text="null",
        headers={"content-type": "application/json"},
    )

    result_dict = await random.ainvoke(_args())
    result = RandomOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "unexpected response shape" in result.error


@pytest.mark.asyncio
async def test_content_survives_a_bare_string_body(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/w/rest.php/v1/page/Earth/with_html",
        json="<html>just the html</html>",
    )

    result_dict = await content.ainvoke(_args(page_title="Earth"))
    result = ContentOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "unexpected response shape" in result.error


# --- Envelope invariant: type confusion ------------------------------------
#
# A 200 whose fields carry the wrong JSON type must not raise either. Each
# fixture below puts an int, a dict or a list where the model declares a
# string/int, which pydantic rejects outright — the coercers in the
# _parse_* helpers are the only thing keeping the envelope intact. Remove
# them and these tests fail with ValidationError.


@pytest.mark.asyncio
async def test_summary_survives_wrongly_typed_fields(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/summary/Earth",
        json={
            "type": 7,
            "title": 12345,
            "displaytitle": {"unexpected": "object"},
            "description": ["a", "list"],
            "extract": {"nested": "object"},
            "pageid": ["not", "an", "int"],
            "lang": False,
            "dir": None,
            "wikibase_item": 42,
            "thumbnail": {"source": 99, "width": "330", "height": None},
            "originalimage": "not-an-object",
            "content_urls": {"desktop": "not-an-object", "mobile": {"page": 5}},
            "coordinates": {"lat": "41.0", "lon": 28},
        },
    )

    result_dict = await summary.ainvoke(_args(page_title="Earth"))
    assert isinstance(result_dict, dict)
    result = SummaryOutput.model_validate(result_dict)

    assert result.success is True
    assert result.summary is not None
    # Scalars are stringified where the model declares a string...
    assert result.summary.type == "7"
    assert result.summary.title == "12345"
    assert result.summary.wikibase_item == "42"
    # ...containers degrade to None instead of raising.
    assert result.summary.displaytitle == "12345"  # falls back to the title
    assert result.summary.description is None
    assert result.summary.extract is None
    assert result.summary.pageid is None
    assert result.summary.dir is None
    assert result.summary.thumbnail is not None
    assert result.summary.thumbnail.source == "99"
    assert result.summary.thumbnail.width is None  # "330" is a string, not an int
    assert result.summary.originalimage is None
    assert result.summary.content_urls is not None
    assert result.summary.content_urls.desktop is None
    assert result.summary.content_urls.mobile is not None
    assert result.summary.content_urls.mobile.page == "5"
    assert result.summary.coordinates is not None
    assert result.summary.coordinates.lat is None  # "41.0" is a string, not a number
    assert result.summary.coordinates.lon == pytest.approx(28.0)


@pytest.mark.asyncio
async def test_search_survives_wrongly_typed_fields(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/w/rest.php/v1/search/page?q=python&limit=10",
        json={
            "pages": [
                {
                    "id": "23862",
                    "key": ["Python"],
                    "title": 99,
                    "excerpt": {"html": "x"},
                    "matched_title": 1,
                    "description": None,
                    "thumbnail": {
                        "mimetype": 1,
                        "size": "12",
                        "width": True,
                        "height": 60,
                        "duration": None,
                        "url": ["//upload.wikimedia.org/x.png"],
                    },
                }
            ]
        },
    )

    result_dict = await search.ainvoke(_args(query="python"))
    result = SearchOutput.model_validate(result_dict)

    assert result.success is True
    hit = result.search_results[0]
    assert hit.id is None  # "23862" is a string, not an int
    assert hit.key is None
    assert hit.url is None  # no key -> no derived URL
    assert hit.title == "99"
    assert hit.excerpt is None
    assert hit.matched_title == "1"
    assert hit.thumbnail is not None
    assert hit.thumbnail.mimetype == "1"
    assert hit.thumbnail.size is None
    assert hit.thumbnail.width is None  # bool is not an int here
    assert hit.thumbnail.height == 60
    assert hit.thumbnail.url is None


@pytest.mark.asyncio
async def test_content_survives_wrongly_typed_fields(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/w/rest.php/v1/page/Earth/with_html",
        json={
            "id": "9228",
            "title": 42,
            "latest": ["not", "an", "object"],
            "content_model": {"x": 1},
            "html": 1234,
        },
    )

    result_dict = await content.ainvoke(_args(page_title="Earth"))
    result = ContentOutput.model_validate(result_dict)

    assert result.success is True
    assert result.content is not None
    assert result.content.pageid is None
    assert result.content.title == "42"
    assert result.content.revision is None
    assert result.content.timestamp is None
    assert result.content.content_model is None
    assert result.content.html == "1234"


@pytest.mark.asyncio
async def test_random_survives_wrongly_typed_fields(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{EN}/api/rest_v1/page/random/summary",
        json={
            "type": ["standard"],
            "title": 5,
            "displaytitle": None,
            "extract": {"a": 1},
            "thumbnail": [1, 2, 3],
            "content_urls": "not-an-object",
            "pageid": "21044553",
            "timestamp": 20260211,
        },
    )

    result_dict = await random.ainvoke(_args())
    result = RandomOutput.model_validate(result_dict)

    assert result.success is True
    assert result.random_page is not None
    assert result.random_page.type is None
    assert result.random_page.title == "5"
    assert result.random_page.displaytitle == "5"
    assert result.random_page.extract is None
    assert result.random_page.thumbnail is None
    assert result.random_page.content_urls is None
    assert result.random_page.pageid is None
    assert result.random_page.timestamp == "20260211"


# --- Host-safety guard -----------------------------------------------------
#
# `language` lands in the request host, so a value that does not match the
# anchored pattern must be refused before any request is made. httpx_mock
# has no registered response in these tests: if a request escaped, it would
# fail rather than pass.


@pytest.mark.parametrize(
    "bad_language",
    [
        "en@attacker.example",
        "en.attacker.example",
        "en/../evil",
        "en:8080",
        "EN_US",
        "a",
        "en#",
        "127.0.0.1",
        "en wiki",
    ],
)
@pytest.mark.asyncio
async def test_summary_refuses_an_unsafe_language(bad_language: str) -> None:
    result_dict = await summary.ainvoke(_args(page_title="Earth", language=bad_language))
    result = SummaryOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "Invalid language code" in result.error
    assert result.summary is None


@pytest.mark.asyncio
async def test_search_refuses_an_unsafe_language() -> None:
    result_dict = await search.ainvoke(_args(query="python", language="en@evil.example"))
    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Invalid language code" in result.error


@pytest.mark.asyncio
async def test_content_refuses_an_unsafe_language() -> None:
    result_dict = await content.ainvoke(_args(page_title="Earth", language="en@evil.example"))
    result = ContentOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Invalid language code" in result.error


@pytest.mark.asyncio
async def test_random_refuses_an_unsafe_language() -> None:
    result_dict = await random.ainvoke(_args(language="en@evil.example"))
    result = RandomOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Invalid language code" in result.error


@pytest.mark.parametrize("good_language", ["en", "tr", "simple", "zh-min-nan", "be-tarask"])
@pytest.mark.asyncio
async def test_accepted_language_codes_reach_their_wiki(
    httpx_mock: Any, good_language: str
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"https://{good_language}.wikipedia.org/api/rest_v1/page/random/summary",
        json={"type": "standard", "title": "A page", "pageid": 1},
    )

    result_dict = await random.ainvoke(_args(language=good_language))
    result = RandomOutput.model_validate(result_dict)
    assert result.success is True


# --- Empty required-input paths -------------------------------------------
#
# The Wikipedia APIs take no credential, so there is no empty-credential
# path to exercise. These cover the equivalent short-circuit: an action
# with a blank required input never reaches the wire.


@pytest.mark.asyncio
async def test_summary_rejects_a_blank_title() -> None:
    result_dict = await summary.ainvoke(_args(page_title="   "))
    result = SummaryOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "page_title" in result.error


@pytest.mark.asyncio
async def test_content_rejects_a_blank_title() -> None:
    result_dict = await content.ainvoke(_args(page_title=""))
    result = ContentOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "page_title" in result.error


@pytest.mark.asyncio
async def test_search_rejects_a_blank_query() -> None:
    result_dict = await search.ainvoke(_args(query="  "))
    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "query" in result.error

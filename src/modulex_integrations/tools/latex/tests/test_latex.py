"""Tests for the LaTeX integration.

The JSON fixtures below mirror real ``latex.ytotech.com`` responses: the
same envelope keys (``packages``, ``package``, ``fonts``), the same TeX
Live key names (``shortdesc``, ``longdesc``, ``cat-license``,
``cat-topics``, ``cat-related``, ``cat-contact-home``, ``url_ctan``), and
the same ``{"error": "Package not found"}`` body the service returns with
a ``404``.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.latex import (
    TOOLS,
    get_package,
    list_fonts,
    manifest,
    search_packages,
)
from modulex_integrations.tools.latex.outputs import (
    GetPackageOutput,
    ListFontsOutput,
    SearchPackagesOutput,
)

API = "https://latex.ytotech.com"


def _args(**extra: Any) -> dict[str, Any]:
    """Build an ``.ainvoke`` payload as ``dict[str, Any]``.

    Bypasses mypy's TypedDict-spread check on LangChain's typed
    ``.ainvoke()`` overload.
    """
    return dict(extra)


_PACKAGES_LIST = {
    "packages": [
        {
            "installed": True,
            "name": "amsmath",
            "shortdesc": "AMS mathematical facilities for LaTeX",
            "url_ctan": "https://ctan.org/pkg/amsmath",
            "url_info": "/packages/amsmath",
        },
        {
            "installed": True,
            "name": "biblatex",
            "shortdesc": "Sophisticated Bibliographies in LaTeX",
            "url_ctan": "https://ctan.org/pkg/biblatex",
            "url_info": "/packages/biblatex",
        },
        {
            "installed": True,
            "name": "mhchem",
            "shortdesc": "Typeset chemical formulae/equations and risk and safety phrases",
            "url_ctan": "https://ctan.org/pkg/mhchem",
            "url_info": "/packages/mhchem",
        },
        {
            "installed": True,
            "name": "a0poster",
            "shortdesc": "Support for designing posters on large paper",
            "url_ctan": "https://ctan.org/pkg/a0poster",
            "url_info": "/packages/a0poster",
        },
    ]
}


_PACKAGE_DETAILS = {
    "package": {
        "cat-contact-announce": "https://github.com/plk/biblatex/wiki",
        "cat-contact-bugs": "https://github.com/plk/biblatex/issues",
        "cat-contact-home": "https://github.com/plk/biblatex",
        "cat-contact-repository": "https://github.com/plk/biblatex.git",
        "cat-license": "lppl1.3",
        "cat-related": "translation-biblatex-de biblatex-examples",
        "cat-topics": ["biblatex", "biblio", "tagged-pdf-partially"],
        "cat-version": "3.21",
        "category": "Package",
        "collection": "collection-bibtexextra",
        "installed": True,
        "longdesc": "BibLaTeX is a complete reimplementation of the bibliographic facilities.",
        "package": "biblatex",
        "relocatable": False,
        "revision": 74567,
        "shortdesc": "Sophisticated Bibliographies in LaTeX",
        "sizes": {"run": "2529k"},
        "url_ctan": "https://ctan.org/pkg/biblatex",
    }
}


_FONTS_LIST = {
    "fonts": [
        {"family": "Nimbus Roman", "name": "NimbusRoman-Bold", "styles": ["Bold"]},
        {
            "family": "Noto Serif",
            "name": "Noto Serif Condensed ExtraBold",
            "styles": ["ExtraBold", "Condensed"],
        },
        {"family": "Noto Serif", "name": "Noto Serif Thin", "styles": ["Thin"]},
        {"family": "DejaVu Sans", "name": "DejaVu Sans Book", "styles": ["Book"]},
    ]
}


class TestManifest:
    def test_manifest_exposes_three_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_modulex_key_auth(self) -> None:
        # The LaTeX-on-HTTP API takes no credential of any kind; the single
        # modulex_key schema exists only so the runtime's credential
        # resolution step has something to resolve.
        assert {a.auth_type for a in manifest.auth_schemas} == {"modulex_key"}

    def test_manifest_declares_no_api_key_action_param(self) -> None:
        # api_key is injected by the runtime and must never be redeclared
        # as an action parameter.
        for action in manifest.actions:
            assert "api_key" not in action.parameters

    def test_manifest_logo_follows_convention(self) -> None:
        assert manifest.logo == "modulex:latex-themed"


# --- Happy paths -----------------------------------------------------------


@pytest.mark.asyncio
async def test_search_packages(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="GET", url=f"{API}/packages", json=_PACKAGES_LIST)

    result_dict = await search_packages.ainvoke(_args(query="bibliograph"))
    assert isinstance(result_dict, dict)
    result = SearchPackagesOutput.model_validate(result_dict)

    assert result.success is True
    assert result.error is None
    # Matched on the short description, not the name.
    assert result.total_matches == 1
    assert len(result.packages) == 1

    first = result.packages[0]
    assert first.name == "biblatex"
    assert first.short_description == "Sophisticated Bibliographies in LaTeX"
    assert first.installed is True
    assert first.ctan_url == "https://ctan.org/pkg/biblatex"


@pytest.mark.asyncio
async def test_search_packages_matches_the_name_case_insensitively(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="GET", url=f"{API}/packages", json=_PACKAGES_LIST)

    result = SearchPackagesOutput.model_validate(
        await search_packages.ainvoke(_args(query="  AMSmath  "))
    )

    assert result.success is True
    assert [p.name for p in result.packages] == ["amsmath"]
    assert result.total_matches == 1


@pytest.mark.asyncio
async def test_search_packages_truncates_but_reports_every_match(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="GET", url=f"{API}/packages", json=_PACKAGES_LIST)

    result = SearchPackagesOutput.model_validate(
        await search_packages.ainvoke(_args(query="a", max_results=2))
    )

    assert result.success is True
    # 'a' appears in every fixture entry's name or description.
    assert result.total_matches == 4
    assert len(result.packages) == 2


@pytest.mark.asyncio
async def test_search_packages_falls_back_to_the_default_limit(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="GET", url=f"{API}/packages", json=_PACKAGES_LIST)

    result = SearchPackagesOutput.model_validate(
        await search_packages.ainvoke(_args(query="a", max_results=0))
    )

    assert result.success is True
    assert len(result.packages) == 4


@pytest.mark.asyncio
async def test_get_package(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/packages/biblatex", json=_PACKAGE_DETAILS
    )

    result_dict = await get_package.ainvoke(_args(name=" biblatex "))
    assert isinstance(result_dict, dict)
    result = GetPackageOutput.model_validate(result_dict)

    assert result.success is True
    assert result.error is None
    assert result.package is not None
    assert result.package.name == "biblatex"
    assert result.package.installed is True
    assert result.package.short_description == "Sophisticated Bibliographies in LaTeX"
    assert result.package.long_description is not None
    assert result.package.category == "Package"
    assert result.package.license == "lppl1.3"
    assert result.package.topics == ["biblatex", "biblio", "tagged-pdf-partially"]
    # cat-related is one whitespace-separated string upstream.
    assert result.package.related_packages == [
        "translation-biblatex-de",
        "biblatex-examples",
    ]
    assert result.package.homepage == "https://github.com/plk/biblatex"
    assert result.package.ctan_url == "https://ctan.org/pkg/biblatex"


@pytest.mark.asyncio
async def test_list_fonts(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="GET", url=f"{API}/fonts", json=_FONTS_LIST)

    result_dict = await list_fonts.ainvoke(_args(query="noto serif"))
    assert isinstance(result_dict, dict)
    result = ListFontsOutput.model_validate(result_dict)

    assert result.success is True
    assert result.error is None
    assert result.total_matches == 2
    assert [f.name for f in result.fonts] == [
        "Noto Serif Condensed ExtraBold",
        "Noto Serif Thin",
    ]
    assert result.fonts[0].family == "Noto Serif"
    assert result.fonts[0].styles == ["ExtraBold", "Condensed"]


@pytest.mark.asyncio
async def test_list_fonts_without_a_filter_returns_everything(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="GET", url=f"{API}/fonts", json=_FONTS_LIST)

    result = ListFontsOutput.model_validate(await list_fonts.ainvoke(_args()))

    assert result.success is True
    assert result.total_matches == 4
    assert len(result.fonts) == 4


@pytest.mark.asyncio
async def test_list_fonts_caps_the_requested_limit(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="GET", url=f"{API}/fonts", json=_FONTS_LIST)

    result = ListFontsOutput.model_validate(await list_fonts.ainvoke(_args(max_results=1)))

    assert result.success is True
    assert result.total_matches == 4
    assert len(result.fonts) == 1


@pytest.mark.asyncio
async def test_the_ignored_api_key_argument_is_accepted(httpx_mock: Any) -> None:
    # The API is credential-free: an empty api_key must not change anything.
    httpx_mock.add_response(method="GET", url=f"{API}/fonts", json=_FONTS_LIST)

    result = ListFontsOutput.model_validate(
        await list_fonts.ainvoke(_args(query="dejavu", api_key=""))
    )

    assert result.success is True
    assert [f.name for f in result.fonts] == ["DejaVu Sans Book"]


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_get_package_reports_a_missing_package(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/packages/no-such-package",
        status_code=404,
        json={"error": "Package not found"},
    )

    result = GetPackageOutput.model_validate(
        await get_package.ainvoke(_args(name="no-such-package"))
    )

    assert result.success is False
    assert result.package is None
    assert result.error is not None
    assert "404" in result.error
    assert "Package not found" in result.error


@pytest.mark.asyncio
async def test_get_package_reports_an_empty_package_object(httpx_mock: Any) -> None:
    # A 200 whose `package` object carries no name is not a usable result.
    httpx_mock.add_response(method="GET", url=f"{API}/packages/tikz", json={"package": {}})

    result = GetPackageOutput.model_validate(await get_package.ainvoke(_args(name="tikz")))

    assert result.success is False
    assert result.error is not None
    assert "not found" in result.error


@pytest.mark.asyncio
async def test_get_package_rejects_a_path_traversing_name() -> None:
    # No request is made at all — the name never reaches the URL.
    result = GetPackageOutput.model_validate(
        await get_package.ainvoke(_args(name="../../etc/passwd"))
    )

    assert result.success is False
    assert result.error is not None
    assert "not a valid TeX Live package name" in result.error


@pytest.mark.asyncio
async def test_search_packages_reports_a_server_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/packages", status_code=502, text="Bad Gateway"
    )

    result = SearchPackagesOutput.model_validate(
        await search_packages.ainvoke(_args(query="tikz"))
    )

    assert result.success is False
    assert result.packages == []
    assert result.total_matches == 0
    assert result.error is not None
    assert "502" in result.error


@pytest.mark.asyncio
async def test_list_fonts_reports_an_in_body_error(httpx_mock: Any) -> None:
    # A 200 carrying an `error` key is still a failure.
    httpx_mock.add_response(
        method="GET", url=f"{API}/fonts", json={"error": "fontconfig unavailable"}
    )

    result = ListFontsOutput.model_validate(await list_fonts.ainvoke(_args()))

    assert result.success is False
    assert result.error == "fontconfig unavailable"


@pytest.mark.asyncio
async def test_search_packages_rejects_a_blank_query() -> None:
    result = SearchPackagesOutput.model_validate(
        await search_packages.ainvoke(_args(query="   "))
    )

    assert result.success is False
    assert result.error is not None
    assert "query is required" in result.error


@pytest.mark.asyncio
async def test_get_package_rejects_a_blank_name() -> None:
    result = GetPackageOutput.model_validate(await get_package.ainvoke(_args(name="  ")))

    assert result.success is False
    assert result.error is not None
    assert "name is required" in result.error


# --- Envelope invariant: nothing between .json() and return may raise ------


@pytest.mark.asyncio
async def test_search_packages_survives_a_shape_confused_body(httpx_mock: Any) -> None:
    # A bare JSON array where an object was expected must not raise.
    httpx_mock.add_response(method="GET", url=f"{API}/packages", json=[])

    result = SearchPackagesOutput.model_validate(
        await search_packages.ainvoke(_args(query="tikz"))
    )

    assert result.success is True
    assert result.packages == []
    assert result.total_matches == 0


@pytest.mark.asyncio
async def test_list_fonts_survives_a_non_array_collection(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="GET", url=f"{API}/fonts", json={"fonts": "none"})

    result = ListFontsOutput.model_validate(await list_fonts.ainvoke(_args()))

    assert result.success is True
    assert result.fonts == []
    assert result.total_matches == 0


@pytest.mark.asyncio
async def test_search_packages_survives_a_non_json_body(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/packages", text="<html>gateway timeout</html>"
    )

    result = SearchPackagesOutput.model_validate(
        await search_packages.ainvoke(_args(query="tikz"))
    )

    # A 200 that is not JSON parses to an empty envelope, never an exception.
    assert result.success is True
    assert result.packages == []


@pytest.mark.asyncio
async def test_search_packages_survives_type_confused_fields(httpx_mock: Any) -> None:
    # Every scalar here has the wrong JSON type for its declared model field.
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/packages",
        json={
            "packages": [
                {
                    "name": 12345,
                    "shortdesc": {"nested": "object"},
                    "installed": "yes",
                    "url_ctan": ["https://ctan.org/pkg/x"],
                },
                "not-an-object",
            ]
        },
    )

    result = SearchPackagesOutput.model_validate(
        await search_packages.ainvoke(_args(query="12345"))
    )

    assert result.success is True
    assert len(result.packages) == 1
    entry = result.packages[0]
    assert entry.name == "12345"  # coerced from the number
    assert entry.short_description is None  # object -> None, never str(dict)
    assert entry.installed is None  # "yes" is not a bool
    assert entry.ctan_url is None  # array -> None


@pytest.mark.asyncio
async def test_get_package_survives_type_confused_fields(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/packages/weird",
        json={
            "package": {
                "package": 42,
                "installed": 1,
                "shortdesc": ["a", "b"],
                "longdesc": None,
                "category": {"x": 1},
                "cat-license": 7,
                "cat-topics": "not-a-list",
                "cat-related": ["translation-x"],
                "cat-contact-home": 3.5,
                "url_ctan": False,
            }
        },
    )

    result = GetPackageOutput.model_validate(await get_package.ainvoke(_args(name="weird")))

    assert result.success is True
    assert result.package is not None
    assert result.package.name == "42"
    assert result.package.installed is None  # 1 is not a bool
    assert result.package.short_description is None
    assert result.package.long_description is None
    assert result.package.category is None
    assert result.package.license == "7"
    assert result.package.topics == []
    assert result.package.related_packages == []
    assert result.package.homepage == "3.5"
    assert result.package.ctan_url == "False"


@pytest.mark.asyncio
async def test_list_fonts_survives_type_confused_fields(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/fonts",
        json={"fonts": [{"family": 1, "name": None, "styles": "Bold"}, 17]},
    )

    result = ListFontsOutput.model_validate(await list_fonts.ainvoke(_args()))

    assert result.success is True
    assert result.total_matches == 2
    assert result.fonts[0].family == "1"
    assert result.fonts[0].name is None
    assert result.fonts[0].styles == []
    assert result.fonts[1].family is None

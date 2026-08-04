"""Tests for the ArXiv integration.

The XML fixtures below mirror real ``export.arxiv.org/api/query``
responses: same namespace declarations, same element order, same
whitespace-wrapped ``<title>``/``<summary>`` text, and the same
``http://arxiv.org/abs/...`` identifier form the live API returns.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.arxiv import (
    TOOLS,
    get_author_papers,
    get_paper,
    manifest,
    search,
)
from modulex_integrations.tools.arxiv.outputs import (
    GetAuthorPapersOutput,
    GetPaperOutput,
    SearchOutput,
)

API = "https://export.arxiv.org/api/query"


def _args(**extra: Any) -> dict[str, Any]:
    """Build an ``.ainvoke`` payload as ``dict[str, Any]``.

    Bypasses mypy's TypedDict-spread check on LangChain's typed
    ``.ainvoke()`` overload.
    """
    return dict(extra)


_FEED_TWO_ENTRIES = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/" \
xmlns:arxiv="http://arxiv.org/schemas/atom" xmlns="http://www.w3.org/2005/Atom">
  <id>https://arxiv.org/api/cHxbiOdZaP56ODnBPIenZhzg5f8</id>
  <title>arXiv Query: search_query=all:electron&amp;start=0&amp;max_results=2</title>
  <updated>2026-08-04T01:46:25Z</updated>
  <opensearch:itemsPerPage>2</opensearch:itemsPerPage>
  <opensearch:totalResults>184463</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
  <entry>
    <id>http://arxiv.org/abs/cond-mat/0011267v1</id>
    <title>The electronic structure of cuprates
  from high energy spectroscopy</title>
    <updated>2000-11-15T16:19:15Z</updated>
    <link href="https://arxiv.org/abs/cond-mat/0011267v1" rel="alternate" type="text/html"/>
    <link href="https://arxiv.org/pdf/cond-mat/0011267v1" rel="related" \
type="application/pdf" title="pdf"/>
    <summary>  We report studies of the electronic structure
  of doped cuprate chains.</summary>
    <category term="cond-mat.supr-con" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cond-mat.str-el" scheme="http://arxiv.org/schemas/atom"/>
    <published>2000-11-15T16:19:15Z</published>
    <arxiv:comment>special issue on electron correlation, in press</arxiv:comment>
    <arxiv:primary_category term="cond-mat.supr-con"/>
    <arxiv:journal_ref>J. Electron Spectr. Relat. Phenom. 117-118, 203 (2001)</arxiv:journal_ref>
    <author>
      <name>Mark S. Golden</name>
    </author>
    <author>
      <name>Christian Duerr</name>
    </author>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2101.00001v2</id>
    <title>A second paper</title>
    <updated>2021-02-01T00:00:00Z</updated>
    <link href="https://arxiv.org/abs/2101.00001v2" rel="alternate" type="text/html"/>
    <link href="https://arxiv.org/pdf/2101.00001v2" rel="related" \
type="application/pdf" title="pdf"/>
    <summary>Second abstract.</summary>
    <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
    <published>2021-01-01T00:00:00Z</published>
    <arxiv:primary_category term="cs.LG"/>
    <author>
      <name>Ada Lovelace</name>
    </author>
  </entry>
</feed>
"""


_FEED_SINGLE_ENTRY_WITH_DOI = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/" \
xmlns:arxiv="http://arxiv.org/schemas/atom" xmlns="http://www.w3.org/2005/Atom">
  <id>https://arxiv.org/api/JAfp0lHmJ0Vw2vNH1LmpYbLTBOw</id>
  <title>arXiv Query: search_query=&amp;id_list=1706.03762</title>
  <updated>2026-08-04T00:00:00Z</updated>
  <opensearch:itemsPerPage>1</opensearch:itemsPerPage>
  <opensearch:totalResults>1</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
  <entry>
    <id>http://arxiv.org/abs/1706.03762v7</id>
    <title>Attention Is All You Need</title>
    <updated>2023-08-02T00:41:18Z</updated>
    <link href="http://dx.doi.org/10.1529/biophysj.104.047340" rel="related" title="doi"/>
    <link href="https://arxiv.org/abs/1706.03762v7" rel="alternate" type="text/html"/>
    <link href="https://arxiv.org/pdf/1706.03762v7" rel="related" \
type="application/pdf" title="pdf"/>
    <summary>  The dominant sequence transduction models are based on complex
  recurrent or convolutional neural networks.</summary>
    <category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
    <published>2017-06-12T17:57:34Z</published>
    <arxiv:comment>15 pages, 5 figures</arxiv:comment>
    <arxiv:primary_category term="cs.CL"/>
    <arxiv:doi>10.1529/biophysj.104.047340</arxiv:doi>
    <author>
      <name>Ashish Vaswani</name>
    </author>
    <author>
      <name>Noam Shazeer</name>
    </author>
  </entry>
</feed>
"""


_FEED_EMPTY = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/" \
xmlns:arxiv="http://arxiv.org/schemas/atom" xmlns="http://www.w3.org/2005/Atom">
  <id>https://arxiv.org/api/empty</id>
  <title>arXiv Query: search_query=au:%22Nobody%20Here%22</title>
  <updated>2026-08-04T00:00:00Z</updated>
  <opensearch:itemsPerPage>10</opensearch:itemsPerPage>
  <opensearch:totalResults>0</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
</feed>
"""


# arXiv answers a malformed identifier with HTTP 200 and a feed whose
# single entry is an error record.
_FEED_ERROR_ENTRY = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <id>http://arxiv.org/api/errors</id>
  <title type="html">ArXiv Query</title>
  <updated>2026-08-04T00:00:00Z</updated>
  <entry>
    <id>http://arxiv.org/api/errors#incorrect_id_format_for_1234.12345</id>
    <title>Error</title>
    <summary>incorrect id format for 1234.12345</summary>
    <updated>2026-08-04T00:00:00Z</updated>
    <link href="http://arxiv.org/api/errors#incorrect_id_format_for_1234.12345" \
rel="alternate" type="text/html"/>
  </entry>
</feed>
"""


_FEED_WITH_DOCTYPE = """<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE feed [<!ENTITY lol "lol">]>
<feed xmlns="http://www.w3.org/2005/Atom">
  <id>https://arxiv.org/api/hostile</id>
</feed>
"""


class TestManifest:
    def test_manifest_exposes_three_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_modulex_key_auth(self) -> None:
        # The arXiv API takes no credential of any kind; the single
        # modulex_key schema exists only so the runtime's credential
        # resolution step has something to resolve.
        assert {a.auth_type for a in manifest.auth_schemas} == {"modulex_key"}

    def test_manifest_declares_no_api_key_action_param(self) -> None:
        # api_key is injected by the runtime and must never be redeclared
        # as an action parameter.
        for action in manifest.actions:
            assert "api_key" not in action.parameters

    def test_manifest_logo_follows_convention(self) -> None:
        assert manifest.logo == "modulex:arxiv-themed"


# --- Happy paths -----------------------------------------------------------


@pytest.mark.asyncio
async def test_search(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}?search_query=all%3Aelectron&start=0&max_results=2"
            "&sortBy=relevance&sortOrder=descending"
        ),
        text=_FEED_TWO_ENTRIES,
    )

    result_dict = await search.ainvoke(
        _args(search_query="all:electron", max_results=2)
    )
    assert isinstance(result_dict, dict)
    result = SearchOutput.model_validate(result_dict)

    assert result.success is True
    assert result.error is None
    assert result.total_results == 184463
    assert result.query == "all:electron"
    assert len(result.papers) == 2

    first = result.papers[0]
    # The <id> element is stripped of its abs/ prefix but kept whole in `link`.
    assert first.id == "cond-mat/0011267v1"
    assert first.link == "http://arxiv.org/abs/cond-mat/0011267v1"
    # Multi-line title/summary text is whitespace-collapsed.
    assert first.title == "The electronic structure of cuprates from high energy spectroscopy"
    assert first.summary == "We report studies of the electronic structure of doped cuprate chains."
    assert first.authors == ["Mark S. Golden", "Christian Duerr"]
    assert first.pdf_link == "https://arxiv.org/pdf/cond-mat/0011267v1"
    assert first.categories == ["cond-mat.supr-con", "cond-mat.str-el"]
    assert first.primary_category == "cond-mat.supr-con"
    assert first.comment == "special issue on electron correlation, in press"
    assert first.journal_ref == "J. Electron Spectr. Relat. Phenom. 117-118, 203 (2001)"
    assert first.doi is None
    assert first.published == "2000-11-15T16:19:15Z"
    assert first.updated == "2000-11-15T16:19:15Z"

    assert result.papers[1].id == "2101.00001v2"
    assert result.papers[1].primary_category == "cs.LG"


@pytest.mark.asyncio
async def test_search_prefixes_the_selected_field(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}?search_query=ti%3Atransformer&start=0&max_results=10"
            "&sortBy=submittedDate&sortOrder=ascending"
        ),
        text=_FEED_EMPTY,
    )

    result_dict = await search.ainvoke(
        _args(
            search_query="transformer",
            search_field="ti",
            sort_by="submittedDate",
            sort_order="ascending",
        )
    )
    result = SearchOutput.model_validate(result_dict)

    assert result.success is True
    assert result.query == "ti:transformer"
    assert result.papers == []
    assert result.total_results == 0


@pytest.mark.asyncio
async def test_search_clamps_max_results_and_start(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}?search_query=quantum&start=0&max_results=2000"
            "&sortBy=relevance&sortOrder=descending"
        ),
        text=_FEED_EMPTY,
    )

    result_dict = await search.ainvoke(
        _args(search_query="quantum", max_results=99999, start=-5)
    )
    result = SearchOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_paper(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}?id_list=1706.03762",
        text=_FEED_SINGLE_ENTRY_WITH_DOI,
    )

    result_dict = await get_paper.ainvoke(_args(paper_id="1706.03762"))
    assert isinstance(result_dict, dict)
    result = GetPaperOutput.model_validate(result_dict)

    assert result.success is True
    assert result.paper is not None
    assert result.paper.id == "1706.03762v7"
    assert result.paper.title == "Attention Is All You Need"
    assert result.paper.authors == ["Ashish Vaswani", "Noam Shazeer"]
    assert result.paper.doi == "10.1529/biophysj.104.047340"
    assert result.paper.pdf_link == "https://arxiv.org/pdf/1706.03762v7"
    assert result.paper.categories == ["cs.CL", "cs.LG"]
    assert result.paper.comment == "15 pages, 5 figures"
    assert result.paper.journal_ref is None


@pytest.mark.asyncio
async def test_get_paper_accepts_a_full_abs_url(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}?id_list=1706.03762",
        text=_FEED_SINGLE_ENTRY_WITH_DOI,
    )

    result_dict = await get_paper.ainvoke(
        _args(paper_id="https://arxiv.org/abs/1706.03762")
    )
    result = GetPaperOutput.model_validate(result_dict)
    assert result.success is True
    assert result.paper is not None
    assert result.paper.id == "1706.03762v7"


@pytest.mark.asyncio
async def test_get_author_papers(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}?search_query=au%3A%22Ada+Lovelace%22&max_results=5"
            "&sortBy=submittedDate&sortOrder=descending"
        ),
        text=_FEED_TWO_ENTRIES,
    )

    result_dict = await get_author_papers.ainvoke(
        _args(author_name="Ada Lovelace", max_results=5)
    )
    assert isinstance(result_dict, dict)
    result = GetAuthorPapersOutput.model_validate(result_dict)

    assert result.success is True
    assert result.author_name == "Ada Lovelace"
    assert result.total_results == 184463
    assert len(result.author_papers) == 2
    assert result.author_papers[1].authors == ["Ada Lovelace"]


@pytest.mark.asyncio
async def test_get_author_papers_strips_quotes_from_the_name(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}?search_query=au%3A%22Ada+Lovelace%22&max_results=10"
            "&sortBy=submittedDate&sortOrder=descending"
        ),
        text=_FEED_EMPTY,
    )

    result_dict = await get_author_papers.ainvoke(_args(author_name='Ada "Lovelace"'))
    result = GetAuthorPapersOutput.model_validate(result_dict)
    assert result.success is True
    assert result.author_name == "Ada Lovelace"


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_search_reports_rate_limiting(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}?search_query=electron&start=0&max_results=10"
            "&sortBy=relevance&sortOrder=descending"
        ),
        status_code=429,
        text="Rate exceeded.",
    )

    result_dict = await search.ainvoke(_args(search_query="electron"))
    result = SearchOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "429" in result.error
    assert "Rate exceeded." in result.error
    assert result.papers == []


@pytest.mark.asyncio
async def test_get_author_papers_reports_an_html_error_page(httpx_mock: Any) -> None:
    # When the service is unavailable arXiv answers with an HTML body, not
    # Atom — the status check has to fire before the parser sees it.
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}?search_query=au%3A%22Ada+Lovelace%22&max_results=10"
            "&sortBy=submittedDate&sortOrder=descending"
        ),
        status_code=503,
        text="<!DOCTYPE html>\n<html>\n  <head><title>503</title></head>\n"
        "  <body>\n    503\n  </body>\n</html>\n",
    )

    result_dict = await get_author_papers.ainvoke(_args(author_name="Ada Lovelace"))
    result = GetAuthorPapersOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "503" in result.error
    assert result.author_papers == []


@pytest.mark.asyncio
async def test_get_paper_surfaces_the_in_feed_error_entry(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}?id_list=1234.12345",
        text=_FEED_ERROR_ENTRY,
    )

    result_dict = await get_paper.ainvoke(_args(paper_id="1234.12345"))
    result = GetPaperOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "incorrect id format for 1234.12345" in result.error
    assert result.paper is None


@pytest.mark.asyncio
async def test_get_paper_reports_a_missing_paper(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}?id_list=0000.00000",
        text=_FEED_EMPTY,
    )

    result_dict = await get_paper.ainvoke(_args(paper_id="0000.00000"))
    result = GetPaperOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "0000.00000" in result.error
    assert result.paper is None


@pytest.mark.asyncio
async def test_search_reports_unparseable_xml(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}?search_query=electron&start=0&max_results=10"
            "&sortBy=relevance&sortOrder=descending"
        ),
        text="<feed><entry>truncated",
    )

    result_dict = await search.ainvoke(_args(search_query="electron"))
    result = SearchOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "Atom XML" in result.error


@pytest.mark.asyncio
async def test_search_refuses_a_feed_carrying_a_doctype(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}?search_query=electron&start=0&max_results=10"
            "&sortBy=relevance&sortOrder=descending"
        ),
        text=_FEED_WITH_DOCTYPE,
    )

    result_dict = await search.ainvoke(_args(search_query="electron"))
    result = SearchOutput.model_validate(result_dict)

    assert result.success is False
    assert result.error is not None
    assert "document type declaration" in result.error


# --- Empty required-input paths -------------------------------------------
#
# The arXiv API takes no credential, so there is no empty-credential path
# to exercise. These cover the equivalent short-circuit: every action
# refuses to hit the wire when its required input is blank.


@pytest.mark.asyncio
async def test_search_rejects_a_blank_query() -> None:
    result_dict = await search.ainvoke(_args(search_query="   "))
    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "search_query" in result.error


@pytest.mark.asyncio
async def test_get_paper_rejects_a_blank_id() -> None:
    result_dict = await get_paper.ainvoke(_args(paper_id=""))
    result = GetPaperOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "paper_id" in result.error


@pytest.mark.asyncio
async def test_get_author_papers_rejects_a_blank_name() -> None:
    result_dict = await get_author_papers.ainvoke(_args(author_name='""'))
    result = GetAuthorPapersOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "author_name" in result.error

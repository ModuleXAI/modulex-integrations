"""Unit tests for ``serialize_pydantic_return``.

The decorator's role is to ensure ``@tool`` functions return plain
dicts at runtime — modulex's downstream code uses ``json.dumps()``
and cannot serialize pydantic ``BaseModel`` instances. The annotated
return type stays as the pydantic class so output_schema derivation
(via ``typing.get_type_hints`` on the consumer side) still works.

These tests pin down the contract independently of any specific
integration.
"""
from __future__ import annotations

import pytest
from pydantic import BaseModel

from modulex_integrations import serialize_pydantic_return


class _Out(BaseModel):
    success: bool
    msg: str
    nested: list[int] = []


@pytest.mark.asyncio
async def test_pydantic_return_becomes_dict() -> None:
    @serialize_pydantic_return
    async def fn() -> _Out:
        return _Out(success=True, msg="hi", nested=[1, 2])

    result = await fn()

    assert isinstance(result, dict)
    assert result == {"success": True, "msg": "hi", "nested": [1, 2]}


@pytest.mark.asyncio
async def test_non_pydantic_return_passes_through() -> None:
    @serialize_pydantic_return
    async def returns_dict() -> dict[str, int]:
        return {"a": 1, "b": 2}

    @serialize_pydantic_return
    async def returns_str() -> str:
        return "hello"

    @serialize_pydantic_return
    async def returns_none() -> None:
        return None

    assert await returns_dict() == {"a": 1, "b": 2}
    assert await returns_str() == "hello"
    assert await returns_none() is None


@pytest.mark.asyncio
async def test_return_type_annotation_preserved() -> None:
    """The annotated return type must stay as the pydantic class so
    consumers can derive JSONSchema via ``get_type_hints``."""
    import typing

    @serialize_pydantic_return
    async def fn() -> _Out:
        return _Out(success=True, msg="ok")

    hints = typing.get_type_hints(fn)
    assert hints["return"] is _Out
    assert hasattr(hints["return"], "model_json_schema")
    schema = hints["return"].model_json_schema()
    assert schema["title"] == "_Out"


@pytest.mark.asyncio
async def test_decorator_works_with_extra_fields_in_model() -> None:
    """``.model_dump()`` includes every field; defaults too."""

    class FullOut(BaseModel):
        a: int
        b: str | None = None
        c: list[str] = []

    @serialize_pydantic_return
    async def fn() -> FullOut:
        return FullOut(a=1)

    result = await fn()
    assert result == {"a": 1, "b": None, "c": []}

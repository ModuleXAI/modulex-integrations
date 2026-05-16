"""Auto-dump pydantic return values to plain dicts.

modulex's runtime contract for ``@tool`` functions is "return a
JSON-serializable value." The legacy inline tools returned plain
dicts; the migrated package tools were initially returning pydantic
``BaseModel`` instances (cleaner internal typing), which broke
downstream ``json.dumps()`` calls on the modulex side with
``TypeError: Object of type SearchOutput is not JSON serializable``.

The fix is to convert pydantic returns to dicts at the @tool boundary
while keeping the return-type *annotation* pointing at the pydantic
class. modulex's ``package_loader.py`` reads the annotation via
``typing.get_type_hints`` to derive the LLM-facing output_schema, so
the annotation must stay. Only the runtime value changes.

Usage::

    from langchain_core.tools import tool
    from modulex_integrations import serialize_pydantic_return

    @tool(args_schema=MyInput)
    @serialize_pydantic_return
    async def my_action(...) -> MyOutput:
        return MyOutput(...)         # at runtime, .ainvoke() yields a dict

Decorator order is mandatory: ``@tool`` outer, ``@serialize_pydantic_return``
inner. ``@tool`` is the LAST decorator applied (closest to the call
site) so LangChain's ``StructuredTool`` wraps the dict-coercing
function. Reverse the order and ``@tool`` would receive the typed
pydantic-returning version, and the dict coercion would never fire.
"""
from collections.abc import Awaitable, Callable
from functools import wraps

from pydantic import BaseModel

__all__ = ["serialize_pydantic_return"]


def serialize_pydantic_return[**P, R](
    fn: Callable[P, Awaitable[R]],
) -> Callable[P, Awaitable[R]]:
    """Wrap an async function so a pydantic ``BaseModel`` return becomes a dict.

    The annotated return type is preserved for static analysis and for
    downstream tooling that reads ``typing.get_type_hints(fn)["return"]``
    to derive a JSONSchema. Runtime, however, yields the model's
    ``.model_dump()`` dict.

    Non-pydantic returns pass through unchanged — strings, lists, dicts,
    ``None``, etc. all flow as-is.
    """

    @wraps(fn)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        result = await fn(*args, **kwargs)
        if isinstance(result, BaseModel):
            # The annotated return type is what the consumer's JSONSchema
            # derivation reads; at runtime we hand back the dict so modulex's
            # json.dumps() boundary works. The cast lies to mypy about the
            # runtime type, but that's fine — every consumer in the
            # pipeline (LangChain, modulex tool_executor, agents) treats
            # the result as Any/dict, never as the typed model.
            return result.model_dump()  # type: ignore[return-value]
        return result

    return wrapper

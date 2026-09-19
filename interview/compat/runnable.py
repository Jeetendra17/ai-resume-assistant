"""A standard-library stand-in for the LangChain Expression Language (LCEL).

Only the surface the interview pipeline uses: `invoke`, `batch`, composition with
`|`, and the four runnables below. When `langchain_core` is installed the pipeline
uses the real thing (see `interview/chains/lcel.py`); this exists so the site keeps
answering when it is not -- the same never-hard-fail rule as the provider chain.

Semantics match LangChain's for these cases, and `tests/test_interview.py` runs the
same pipeline definition through both implementations to keep it that way.
"""

from __future__ import annotations

from typing import Any, Callable


class Runnable:
    def invoke(self, value: Any, config: dict | None = None) -> Any:  # pragma: no cover
        raise NotImplementedError

    def batch(self, values: list, config: dict | None = None) -> list:
        return [self.invoke(v, config) for v in values]

    def __or__(self, other) -> "RunnableSequence":
        return RunnableSequence(self, coerce(other))

    def __ror__(self, other) -> "RunnableSequence":
        return RunnableSequence(coerce(other), self)


class RunnableSequence(Runnable):
    def __init__(self, *steps: Runnable):
        flat: list[Runnable] = []
        for step in steps:
            flat.extend(step.steps if isinstance(step, RunnableSequence) else [step])
        self.steps = flat

    def invoke(self, value, config=None):
        for step in self.steps:
            value = step.invoke(value, config)
        return value


class RunnableLambda(Runnable):
    def __init__(self, func: Callable[[Any], Any]):
        self.func = func

    def invoke(self, value, config=None):
        return self.func(value)


class RunnableParallel(Runnable):
    """Run every branch on the same input; return a dict of their outputs."""

    def __init__(self, steps: dict | None = None, **kwargs):
        self.branches = {k: coerce(v) for k, v in {**(steps or {}), **kwargs}.items()}

    def invoke(self, value, config=None):
        return {key: branch.invoke(value, config) for key, branch in self.branches.items()}


class RunnablePassthrough(Runnable):
    """Identity; `.assign(...)` adds computed keys to a dict input."""

    def invoke(self, value, config=None):
        return value

    @classmethod
    def assign(cls, **kwargs) -> Runnable:
        parallel = RunnableParallel(kwargs)

        class _Assign(Runnable):
            def invoke(self, value, config=None):
                return {**value, **parallel.invoke(value, config)}

        return _Assign()


def coerce(obj) -> Runnable:
    if isinstance(obj, Runnable):
        return obj
    if isinstance(obj, dict):
        return RunnableParallel(obj)
    if callable(obj):
        return RunnableLambda(obj)
    raise TypeError(f"cannot use {type(obj).__name__} as a runnable")

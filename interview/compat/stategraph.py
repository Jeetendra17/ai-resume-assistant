"""A standard-library stand-in for LangGraph's `StateGraph`.

Only the surface the interview agent uses: typed state with per-key reducers,
`add_node`, `add_edge`, `add_conditional_edges`, `compile()`, and `invoke()` with
a recursion limit. When `langgraph` is installed the agent uses the real thing
(see `interview/graph/engine.py`).

It exists for two reasons, both measured rather than assumed: the site must keep
answering with nothing but Flask installed, and importing `langgraph.graph` takes
~1.8 s on a cold start where this takes milliseconds. `INTERVIEW_GRAPH_ENGINE`
chooses between them at runtime.

State semantics follow LangGraph: a node returns a partial update; a key whose type
is `Annotated[T, reducer]` is merged with `reducer(old, new)`, any other key is
overwritten.
"""

from __future__ import annotations

import typing

START = "__start__"
END = "__end__"


class GraphRecursionError(RuntimeError):
    pass


def _reducers(schema) -> dict:
    hints = typing.get_type_hints(schema, include_extras=True)
    out = {}
    for key, hint in hints.items():
        if typing.get_origin(hint) is typing.Annotated:
            meta = typing.get_args(hint)[1:]
            if meta and callable(meta[0]):
                out[key] = meta[0]
    return out


class StateGraph:
    def __init__(self, state_schema):
        self.schema = state_schema
        self.nodes: dict[str, typing.Callable] = {}
        self.edges: dict[str, str] = {}
        self.branches: dict[str, tuple] = {}

    def add_node(self, name: str, func) -> "StateGraph":
        if name in (START, END) or name in self.nodes:
            raise ValueError(f"invalid or duplicate node name {name!r}")
        self.nodes[name] = func
        return self

    def add_edge(self, source: str, target: str) -> "StateGraph":
        self.edges[source] = target
        return self

    def add_conditional_edges(self, source: str, path, path_map: dict | None = None) -> "StateGraph":
        self.branches[source] = (path, path_map)
        return self

    def compile(self) -> "CompiledGraph":
        if START not in self.edges:
            raise ValueError("graph has no entry point: add_edge(START, <node>)")
        for source in list(self.edges) + list(self.branches):
            if source != START and source not in self.nodes:
                raise ValueError(f"edge from unknown node {source!r}")
        return CompiledGraph(self)


class CompiledGraph:
    def __init__(self, graph: StateGraph):
        self.g = graph
        self.reducers = _reducers(graph.schema)

    def _merge(self, state: dict, update: dict | None) -> dict:
        for key, value in (update or {}).items():
            reducer = self.reducers.get(key)
            state[key] = reducer(state[key], value) if reducer and key in state else value
        return state

    def _next(self, node: str, state: dict) -> str:
        if node in self.g.branches:
            path, path_map = self.g.branches[node]
            choice = path(state)
            return path_map[choice] if path_map else choice
        return self.g.edges.get(node, END)

    def invoke(self, state: dict, config: dict | None = None) -> dict:
        limit = (config or {}).get("recursion_limit", 25)
        state = self._merge({}, state)
        node = self.g.edges[START]
        steps = 0
        while node != END:
            steps += 1
            if steps > limit:
                raise GraphRecursionError(f"recursion limit of {limit} reached")
            state = self._merge(state, self.g.nodes[node](state))
            node = self._next(node, state)
        return state

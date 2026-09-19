"""The interview assistant as a LangGraph state machine.

    START -> route -> retrieve -> grade --answerable--> generate -> verify --ok--------> END
               |                   |                       ^          |--regenerate-> generate (once)
               |                   |--follow-up, retry --> rewrite -> retrieve          '--fallback--> fallback -> END
               '--empty------------'--no evidence--------> refuse -> END

Why a graph rather than a chain: two decisions depend on what an earlier step
produced. Whether to generate at all depends on what retrieval found; whether to
accept an answer depends on checking it against its sources. Both are conditional
edges, and one of them loops -- which a straight pipeline cannot express.

Every loop is bounded. At most one query rewrite and one regeneration: a system
that keeps trying is a system that eventually produces something whether or not it
should. The recursion limit is a second guard behind those counters, and a
regeneration only starts while the request can still finish inside the serverless
time limit (REGENERATE_WITHIN_S).

The rewrite step is deliberately narrow. It exists for follow-ups -- "how long did
that take?" retrieves nothing on its own, but does once it is read with the previous
question. It does not paraphrase a standalone question into something the corpus
happens to match; that would turn a correct decline into a stretched answer.

Verification is deterministic and cheap: every number in the answer must appear in
the retrieved entries or the question, and every citation must point at an entry
that was retrieved. It cannot check meaning, only what is checkable without another
model call inside a 10-second serverless budget -- and invented figures are the
fabrication a recruiter is most likely to act on.
"""

from __future__ import annotations

import operator
import re
import time
from typing import Annotated, TypedDict

from interview.chains import pipeline
from interview.graph import engine
from interview.prompting import registry
from interview.retrieval import hybrid
from interview.text import concise

MAX_REWRITES = 1
MAX_REGENERATIONS = 1
RECURSION_LIMIT = 14
MAX_QUESTION_CHARS = 1000
# A regeneration is another model call of up to LLM_TIMEOUT (6 s live). On Vercel's
# 10-second function limit, only start one while it can still finish; later than
# this, quote the source instead of risking a timed-out request.
REGENERATE_WITHIN_S = 3.5

_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
_LIST_NUMBER = re.compile(r"(?m)^\s*\d{1,2}[.)]\s")


class AgentState(TypedDict, total=False):
    question: str
    history: list
    started: float
    query: str
    rewrites: int
    regenerations: int
    docs: list
    retrieval: dict
    answerable: bool
    decision: str
    answer: str
    citations: list
    invalid_citations: list
    declined: bool
    live: bool
    provider: str
    model: str
    provider_errors: list
    prompt_version: str
    examples: list
    issues: list
    outcome: str
    trace: Annotated[list, operator.add]


def _step(node: str, started: float, **detail) -> list:
    return [{"node": node, "ms": round((time.perf_counter() - started) * 1000, 1), **detail}]


# ── nodes ──────────────────────────────────────────────────────────────────

def route(state: AgentState) -> dict:
    t = time.perf_counter()
    question = (state.get("question") or "").strip()[:MAX_QUESTION_CHARS]
    decision = "retrieve" if question else "refuse"
    return {"question": question, "query": question, "rewrites": 0, "regenerations": 0,
            "decision": decision, "trace": _step("route", t, decision=decision)}


def retrieve(state: AgentState) -> dict:
    t = time.perf_counter()
    result = pipeline.retrieval_chain.invoke(state["query"])
    answerable = hybrid.get_index().answerable(result["retrieval"])
    return {"docs": result["docs"], "retrieval": result["retrieval"], "answerable": answerable,
            "trace": _step("retrieve", t, query=state["query"],
                           retrievers=result["retrieval"]["retrievers"],
                           best=result["retrieval"]["best"],
                           top=[d["id"] for d in result["docs"]])}


def grade(state: AgentState) -> dict:
    t = time.perf_counter()
    if state["answerable"]:
        decision = "generate"
    elif state["rewrites"] < MAX_REWRITES and _previous_question(state):
        decision = "rewrite"
    else:
        decision = "refuse"
    return {"decision": decision, "trace": _step("grade", t, answerable=state["answerable"], decision=decision)}


def rewrite(state: AgentState) -> dict:
    t = time.perf_counter()
    query = f"{_previous_question(state)} {state['question']}"
    return {"query": query, "rewrites": state["rewrites"] + 1,
            "trace": _step("rewrite", t, query=query, reason="follow-up read with the previous question")}


def generate(state: AgentState) -> dict:
    t = time.perf_counter()
    strict = state.get("regenerations", 0) > 0
    out = pipeline.generation_chain.invoke({
        "question": state["question"],
        "docs": state["docs"],
        "history": state.get("history") or [],
        "version": registry.live(),
        "strict": strict,
    })
    return {**out, "trace": _step("generate", t, provider=out["provider"], live=out["live"],
                                   prompt=out["prompt_version"], strict=strict,
                                   declined=out["declined"])}


def check(answer: str, docs: list[dict], question: str, invalid_citations=()) -> list[str]:
    """Deterministic verification of a generated answer. Also used by the prompt eval."""
    issues = []
    source = " ".join([question] + [f"{d['question']} {d['answer']} {d['follow_up']}" for d in docs])
    allowed = {n.replace(",", "") for n in _NUMBER.findall(source)}
    allowed |= {n.replace(",", "") for n in _NUMBER.findall(registry.DECLINE)}
    # Citation markers and list numbering are structure, not claims.
    claims = _LIST_NUMBER.sub("", pipeline.CITATION.sub("", answer))
    unsupported = sorted({n.replace(",", "") for n in _NUMBER.findall(claims)} - allowed)
    if unsupported:
        issues.append(f"numbers not in sources: {', '.join(unsupported)}")
    if invalid_citations:
        issues.append(f"citations to entries that were not retrieved: {list(invalid_citations)}")
    return issues


def verify(state: AgentState) -> dict:
    t = time.perf_counter()
    issues = []
    if state["live"] and not state["declined"]:
        issues = check(state["answer"], state["docs"], state["question"],
                       state.get("invalid_citations") or ())
    retry_left = state["regenerations"] < MAX_REGENERATIONS
    in_time = time.perf_counter() - state.get("started", t) < REGENERATE_WITHIN_S
    if not issues:
        decision = "done"
    elif retry_left and in_time:
        decision = "regenerate"
    else:
        decision = "fallback"
    detail = {"note": "no time left to regenerate"} if issues and retry_left and not in_time else {}
    update = {"issues": issues, "decision": decision,
              "trace": _step("verify", t, issues=issues, decision=decision, **detail)}
    if decision == "regenerate":
        update["regenerations"] = state["regenerations"] + 1
    return update


def refuse(state: AgentState) -> dict:
    t = time.perf_counter()
    return {"answer": registry.DECLINE, "declined": True, "live": False, "citations": [],
            "provider": "Corpus index (no model)", "model": "retrieval", "outcome": "declined_before_model",
            "trace": _step("refuse", t, reason="no evidence in his record")}


def fallback(state: AgentState) -> dict:
    """The answer failed verification with no retry left: quote the top entry instead."""
    t = time.perf_counter()
    top = state["docs"][0]
    answer = (f"{concise(top['answer'])}\n\n*(Quoted directly from his record: \"{top['question']}\". "
              "A generated answer failed verification, so the source is shown instead.)*")
    return {"answer": answer, "citations": [top["id"]], "outcome": "verified_fallback",
            "trace": _step("fallback", t, reason="; ".join(state["issues"]))}


def _previous_question(state: AgentState) -> str:
    for turn in reversed(state.get("history") or []):
        if turn.get("role") == "user" and turn.get("content"):
            return turn["content"][:300]
    return ""


# ── graph ──────────────────────────────────────────────────────────────────

def _decision(state: AgentState) -> str:
    return state["decision"]


def build():
    StateGraph, START, END, name, import_ms = engine.load()
    g = StateGraph(AgentState)
    for node in (route, retrieve, grade, rewrite, generate, verify, refuse, fallback):
        g.add_node(node.__name__, node)
    g.add_edge(START, "route")
    g.add_conditional_edges("route", _decision, {"retrieve": "retrieve", "refuse": "refuse"})
    g.add_edge("retrieve", "grade")
    g.add_conditional_edges("grade", _decision,
                            {"generate": "generate", "rewrite": "rewrite", "refuse": "refuse"})
    g.add_edge("rewrite", "retrieve")
    g.add_edge("generate", "verify")
    g.add_conditional_edges("verify", _decision,
                            {"done": END, "regenerate": "generate", "fallback": "fallback"})
    g.add_edge("refuse", END)
    g.add_edge("fallback", END)
    return g.compile(), name, import_ms


_compiled = None


def run(question: str, history: list | None = None) -> dict:
    """Answer a visitor's question. Never raises for a bad question or a dead provider."""
    global _compiled
    started = time.perf_counter()
    cold = _compiled is None
    if cold:
        _compiled = build()
    graph, graph_engine, import_ms = _compiled

    state = graph.invoke({"question": question, "history": history or [], "started": started,
                          "trace": []},
                         {"recursion_limit": RECURSION_LIMIT})

    outcome = state.get("outcome") or (
        "declined_by_model" if state.get("declined") else "answered" if state.get("live") else "extractive")
    return {
        "answer": state["answer"],
        "sources": [{"id": d["id"], "title": d["question"], "part": d["topic"]} for d in state.get("docs", [])],
        "citations": state.get("citations", []),
        "live": bool(state.get("live")),
        "provider": state.get("provider"),
        "model": state.get("model"),
        "outcome": outcome,
        "prompt_version": state.get("prompt_version"),
        "trace": state["trace"],
        "engines": {
            "graph": graph_engine,
            "chain": pipeline.ENGINE,
            "retrieval": "+".join(state.get("retrieval", {}).get("retrievers", [])) or None,
        },
        "timing": {"total_ms": round((time.perf_counter() - started) * 1000),
                   "graph_import_ms": import_ms if cold else 0},
    }

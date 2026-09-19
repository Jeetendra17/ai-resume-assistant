"""The retrieval and generation chains, written in LCEL.

Two chains, composed with `|` from the same four primitives LangChain provides:

    retrieval_chain:   query -> {docs, retrieval trace}
    generation_chain:  {question, docs, history, version} -> {answer, provider, ...}
    rag_chain:         question -> retrieval_chain -> generation_chain   (standalone use)

The LangGraph agent calls the two halves from separate nodes, because it needs to
look at what retrieval found -- and possibly retry -- before generating. The prompt
eval uses `rag_chain` directly.

The model call goes through the site's own provider chain (Groq, then Gemini, then
the rest), not a LangChain chat-model integration: that keeps the nine-provider
failover and the extractive fallback, and adds no dependencies.
"""

from __future__ import annotations

import re

from core.llm import chain as provider_chain
from core.providers import ProviderError
from interview.chains.lcel import ENGINE, RunnableLambda, RunnablePassthrough
from interview.finetune.exemplars import select as select_examples
from interview.prompting import registry
from interview.retrieval import hybrid
from interview.text import concise

# "[2]" or a group, "[2, 3]" -- models write both. Matching only the single form
# once made the verify step read the "2" and "3" of a group as invented numbers.
CITATION = re.compile(r"\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]")


def _retrieve(query: str) -> dict:
    docs, trace = hybrid.get_index().search(query, top_k=3)
    return {"docs": docs, "retrieval": trace}


def _add_examples(state: dict) -> list[dict]:
    version = state["version"]
    if not version.examples:
        return []
    return select_examples(state["question"], {d["id"] for d in state["docs"]}, k=version.examples)


def _render(state: dict) -> dict:
    system, messages = registry.render(
        state["version"], state["question"], state["docs"], state["examples"], state.get("history"))
    if state.get("strict"):
        system += ("\n- Your previous draft stated numbers or citations the context does not support. "
                   "Use only figures that appear verbatim in CONTEXT, and cite only entries that exist.")
    return {**state, "system": system, "messages": messages}


def _extractive(docs: list[dict]) -> str:
    """Used when no provider answers: the top entry's answer, verbatim and labelled."""
    if not docs:
        return registry.DECLINE
    return (f"{concise(docs[0]['answer'])}\n\n"
            f"*(Taken directly from his record: \"{docs[0]['question']}\". "
            "The language model is unavailable right now.)*")


def _generate(state: dict) -> dict:
    errors = []
    for provider in provider_chain():
        try:
            text = provider.complete(state["system"], state["messages"])
        except ProviderError as exc:
            errors.append(f"{provider.name}: {str(exc)[:80]}")
            continue
        if text:
            return {**state, "answer": text, "live": True,
                    "provider": provider.label, "model": provider.model, "provider_errors": errors}
        errors.append(f"{provider.name}: empty response")
    return {**state, "answer": _extractive(state["docs"]), "live": False,
            "provider": "Corpus index (no model)", "model": "retrieval", "provider_errors": errors}


def _postprocess(state: dict) -> dict:
    answer = state["answer"].strip()
    cited = sorted({int(n) for group in CITATION.findall(answer) for n in group.split(",")})
    docs = state["docs"]
    return {
        "answer": answer,
        "citations": [docs[n - 1]["id"] for n in cited if 1 <= n <= len(docs)],
        "invalid_citations": [n for n in cited if not 1 <= n <= len(docs)],
        "declined": answer.strip() == registry.DECLINE.strip() or "isn't something" in answer[:80],
        "live": state["live"],
        "provider": state["provider"],
        "model": state["model"],
        "provider_errors": state["provider_errors"],
        "prompt_version": state["version"].id,
        "examples": [e["id"] for e in state["examples"]],
    }


retrieval_chain = RunnableLambda(_retrieve)

generation_chain = (
    RunnablePassthrough.assign(examples=RunnableLambda(_add_examples))
    | RunnableLambda(_render)
    | RunnableLambda(_generate)
    | RunnableLambda(_postprocess)
)

rag_chain = (
    RunnablePassthrough.assign(retrieved=RunnableLambda(lambda s: _retrieve(s["question"])))
    | RunnableLambda(lambda s: {**s, "docs": s["retrieved"]["docs"]})
    | generation_chain
)


def answer(question: str, version_id: str | None = None, history: list | None = None) -> dict:
    """One-shot RAG answer without the agent graph (used by the prompt eval)."""
    version = registry.VERSIONS[version_id] if version_id else registry.live()
    return rag_chain.invoke({"question": question, "version": version, "history": history or []})


__all__ = ["retrieval_chain", "generation_chain", "rag_chain", "answer", "ENGINE"]

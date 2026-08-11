"""Resume-grounded assistant.

Retrieval always runs locally. Generation walks the provider chain (free tiers first)
and falls back to a deterministic extractive answer if every provider is missing or
failing -- so the deployed site answers questions even with zero API keys configured.
"""

import os

from core.providers import ProviderError, resolve_chain
from core.rag import build_context
from data.profile import PROFILE

MAX_QUESTION_CHARS = 1000
MAX_HISTORY_TURNS = 8

# Shown when retrieval finds nothing. Declining is the correct answer here --
# padding with the career summary would read as though it addressed the question.
OUT_OF_SCOPE = (
    "That isn't something Jeetendra's resume covers, so I'd rather not guess. "
    "I can speak to his experience, projects, skills, education and how this site is built — "
    "or you can ask him directly at **{email}**."
)

SYSTEM_PROMPT = f"""You are the portfolio assistant for {PROFILE['name']}, an {PROFILE['role']} \
based in {PROFILE['location']}. You are talking to recruiters, hiring managers and engineers \
evaluating him for AI/ML engineering roles.

Rules:
- Answer only from the RESUME CONTEXT provided in the user turn. It is the complete record.
- If the context does not cover something, say so plainly and point to his email \
({PROFILE['email']}) rather than guessing. Never invent employers, dates, titles, tools or numbers.
- If the context reads "(no matching resume section for this question)", the resume genuinely \
has nothing on it. Answer from earlier turns only if the question is a direct follow-up; \
otherwise say the resume doesn't cover it and suggest emailing him. Do not substitute his \
career summary for an answer to an unrelated question.
- Lead with the concrete answer. Quote his real metrics when they support the point.
- Be honest about level: he is early-career with strong production QA/SDLC experience and \
self-directed applied AI work. Do not oversell him as a senior ML researcher.
- Refer to him as "Jeetendra" or "he". Keep answers under about 150 words unless asked to \
go deeper. Use short markdown bullet lists when comparing several items.
- Stay on the topic of his background, skills and fit. Politely redirect anything else.
"""

_chain = None


def chain():
    """Providers are resolved once per process; env is fixed after boot."""
    global _chain
    if _chain is None:
        _chain = resolve_chain()
    return _chain


def engine_status():
    active = chain()
    return {
        "live": bool(active),
        "provider": active[0].label if active else "Local resume index",
        "model": active[0].model if active else "bm25-retrieval",
        "fallbacks": [p.label for p in active[1:]],
    }


def _fallback_answer(hits):
    """Extractive answer used when no provider is reachable."""
    if not hits:
        return OUT_OF_SCOPE.format(email=PROFILE["email"])
    parts = [f"**{hits[0]['title']}** — {hits[0]['text']}"]
    for extra in hits[1:3]:
        parts.append(f"\n\n**{extra['title']}** — {extra['text']}")
    return "".join(parts)


def _normalise_history(history):
    """Trim and sanitise client-supplied history into valid message params."""
    messages = []
    for turn in (history or [])[-MAX_HISTORY_TURNS:]:
        role = turn.get("role")
        content = (turn.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content[:MAX_QUESTION_CHARS]})
    # Every provider expects the conversation to open with a user turn.
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    return messages


def answer(question, history=None):
    """Return {answer, sources, live, provider, model} for a visitor question."""
    question = (question or "").strip()[:MAX_QUESTION_CHARS]
    if not question:
        return {
            "answer": "Ask me anything about Jeetendra's experience.",
            "sources": [],
            "live": False,
            "provider": "Local resume index",
        }

    context, hits, grounded = build_context(question)
    sources = [{"title": h["title"], "score": h.get("score", 0)} for h in hits]
    messages = _normalise_history(history)

    # Nothing in the resume matches. With no prior turns there is nothing to
    # answer from, so decline deterministically -- no model call, no chance of
    # padding an answer out of unrelated context, and no free-tier quota spent.
    if not grounded and not messages:
        return {
            "answer": OUT_OF_SCOPE.format(email=PROFILE["email"]),
            "sources": [],
            "live": False,
            "grounded": False,
            "provider": "Local resume index",
            "model": "bm25-retrieval",
        }

    if grounded:
        turn = f"RESUME CONTEXT\n{context}\n\nRECRUITER QUESTION\n{question}"
    else:
        # Mid-conversation follow-ups can be legitimate even with no new match
        # ("how long did that take?"), so let the model try -- but tell it
        # plainly that the corpus returned nothing for this turn.
        turn = (
            "RESUME CONTEXT\n(no matching resume section for this question)\n\n"
            "RECRUITER QUESTION\n" + question
        )
    messages.append({"role": "user", "content": turn})

    errors = []
    for provider in chain():
        try:
            text = provider.complete(SYSTEM_PROMPT, messages)
        except ProviderError as exc:
            errors.append(f"{provider.name}: {exc}")
            continue
        if text:
            return {
                "answer": text,
                "sources": sources,
                "live": True,
                "provider": provider.label,
                "model": provider.model,
            }
        errors.append(f"{provider.name}: empty response")

    if errors and os.environ.get("FLASK_DEBUG") == "1":
        print("[assistant] all providers failed:", " | ".join(errors))

    return {
        "answer": _fallback_answer(hits),
        "sources": sources,
        "live": False,
        "provider": "Local resume index",
        "model": "bm25-retrieval",
    }

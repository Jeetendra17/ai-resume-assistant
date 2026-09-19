"""Score every prompt version end to end, with the model in the loop.

    python -m interview.prompting.evaluate            # all versions -> results.json
    python -m interview.prompting.evaluate --only v5 v6

For each version the same 24 questions go through retrieval and generation: 12
answerable questions (reworded, from the retrieval eval, spread across the corpus)
and the 12 must-decline questions -- the ones retrieval alone could not separate
from real questions.

Scored per answer, all deterministic:

* **decision** -- declined exactly when it should. Weighted most: the retrieval eval
  showed scope has to be decided here, at generation.
* **grounded** -- every number in the answer appears in the retrieved sources (the
  same check the live verify step runs).
* **overlap** -- token F1 between the answer and the reference answer for that
  question (the corpus answer, trimmed as the fine-tuning targets are). A crude
  proxy for "said the right things", but it is what stops a version from scoring
  well on the other metrics by saying less.
* **cited** -- answered questions carry at least one valid citation (reported).
* **prompt tokens** -- estimated input size, i.e. cost and rate-limit headroom.

Selection: best decision, then grounded, then overlap (to 2 decimals), then the
smaller prompt. A version that declines fewer junk questions is out regardless.

Pinned to one provider so versions are compared on one model; a mid-run failover
would make the comparison meaningless. **Gemini by default, not Groq**, because
Groq's free tier allows only 200,000 tokens a day for the live model and the live
site shares that key -- an earlier full run spent the day's quota and pushed real
visitors onto the fallback. Calls are paced by requests and estimated tokens per
minute rather than by waiting for 429s. `--provider groq` is still available.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import deque
from pathlib import Path

os.environ.setdefault("LLM_TIMEOUT", "20")

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from interview.chains import pipeline  # noqa: E402
from interview.finetune.train_lora import token_f1  # noqa: E402
from interview.graph.agent import check  # noqa: E402
from interview.prompting import registry  # noqa: E402
from interview.retrieval import eval as retrieval_eval  # noqa: E402
from interview.retrieval import hybrid  # noqa: E402
from interview.text import concise  # noqa: E402

RESULTS = Path(__file__).with_name("results.json")
ANSWERABLE = retrieval_eval.MUST_MATCH[::4][:12]
DECLINE = retrieval_eval.MUST_DECLINE

PACING = {                        # free-tier limits, with headroom
    "groq": {"tokens_per_minute": 7000, "requests_per_minute": 25},
    "gemini": {"tokens_per_minute": 200000, "requests_per_minute": 12},
}
TOKENS_PER_MINUTE = PACING["gemini"]["tokens_per_minute"]
REQUESTS_PER_MINUTE = PACING["gemini"]["requests_per_minute"]
MIN_LIVE_SHARE = 0.9              # below this, a version's scores are not comparable
_window: deque = deque()          # (timestamp, estimated tokens)


def _estimate_tokens(version, question: str) -> int:
    docs = pipeline._retrieve(question)["docs"]
    system, messages = registry.render(version, question, docs,
                                       [{"question": "x" * 60, "answer": "x" * 450}] * version.examples)
    chars = len(system) + sum(len(m["content"]) for m in messages)
    return int(chars / 3.6) + 250   # ~3.6 chars/token for English, plus the answer


def _pace(tokens: int) -> None:
    while True:
        now = time.time()
        while _window and now - _window[0][0] > 60:
            _window.popleft()
        if (sum(t for _, t in _window) + tokens <= TOKENS_PER_MINUTE
                and len(_window) < REQUESTS_PER_MINUTE):
            _window.append((now, tokens))
            return
        time.sleep(max(1.0, 60 - (now - _window[0][0]) + 0.5))


def ask(question: str, version_id: str) -> dict:
    version = registry.VERSIONS[version_id]
    tokens = _estimate_tokens(version, question)
    for attempt in range(5):
        _pace(tokens)
        started = time.perf_counter()
        out = pipeline.answer(question, version_id)
        out["ms"] = round((time.perf_counter() - started) * 1000)
        out["prompt_tokens"] = tokens
        if out["live"]:
            return out
        # Any provider failure is retried, not just 429: a daily token quota fails
        # instantly with a different status, and scoring a fallback answer as if the
        # model wrote it would corrupt the comparison.
        time.sleep(20)
    return out


def score_version(version_id: str) -> dict:
    by_id = {d["id"]: d for d in hybrid.get_index().docs}
    graded = []
    cases = [("answer", q, ids) for q, ids in ANSWERABLE] + [("decline", q, None) for q in DECLINE]
    for i, (kind, question, expected) in enumerate(cases, start=1):
        out = ask(question, version_id)
        docs = pipeline._retrieve(question)["docs"]
        answered = kind == "answer"
        reference = concise(by_id[expected[0]]["answer"]) if answered else None
        row = {
            "kind": kind,
            "question": question,
            "live": out["live"],
            "decision_ok": (not out["declined"]) if answered else out["declined"],
            "grounded": not check(out["answer"], docs, question, out["invalid_citations"]),
            "overlap": round(token_f1(out["answer"], reference), 3) if answered and not out["declined"] else None,
            "cited": bool(out["citations"]) if answered and not out["declined"] else None,
            "words": len(out["answer"].split()),
            "ms": out["ms"],
            "prompt_tokens": out["prompt_tokens"],
            "answer": out["answer"][:400],
            "errors": out["provider_errors"] if not out["live"] else [],
        }
        graded.append(row)
        mark = "ok " if row["decision_ok"] else "BAD"
        print(f"  {version_id} {i:2}/{len(cases)} {mark} {'live' if row['live'] else 'FALLBACK'} "
              f"{row['ms']:>5}ms  {question[:50]}", flush=True)

    live = [g for g in graded if g["live"]]

    def rate(key, rows):
        vals = [g[key] for g in rows if g[key] is not None]
        return round(sum(vals) / len(vals), 3) if vals else None

    median = lambda xs: sorted(xs)[len(xs) // 2] if xs else None  # noqa: E731
    return {
        "version": version_id,
        "name": registry.VERSIONS[version_id].name,
        "questions": len(graded),
        "live_answers": len(live),
        "decision": rate("decision_ok", live),
        "answered_real": rate("decision_ok", [g for g in live if g["kind"] == "answer"]),
        "declined_junk": rate("decision_ok", [g for g in live if g["kind"] == "decline"]),
        "grounded": rate("grounded", live),
        "overlap": rate("overlap", live),
        "cited": rate("cited", live),
        "median_words": median([g["words"] for g in live]),
        "median_ms": median([g["ms"] for g in live]),
        "prompt_tokens": median([g["prompt_tokens"] for g in graded]),
        "rows": graded,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", default=list(registry.VERSIONS))
    parser.add_argument("--provider", choices=sorted(PACING), default="gemini")
    args = parser.parse_args()

    # Must be set before the first model call: the provider chain is resolved once.
    global TOKENS_PER_MINUTE, REQUESTS_PER_MINUTE
    os.environ["LLM_PROVIDER"] = args.provider
    TOKENS_PER_MINUTE = PACING[args.provider]["tokens_per_minute"]
    REQUESTS_PER_MINUTE = PACING[args.provider]["requests_per_minute"]

    # Reuse the retrieval eval's cached query embeddings so this spends LLM calls only.
    index = hybrid.load(cache_file=retrieval_eval.CACHE)
    hybrid.get_index = lambda: index

    results = json.loads(RESULTS.read_text(encoding="utf-8")) if RESULTS.exists() else {"versions": {}}
    for vid in args.only:
        print(f"scoring {vid} ...", flush=True)
        results["versions"][vid] = score_version(vid)
        RESULTS.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")

    fmt = lambda x: "  -  " if x is None else f"{x:.0%}"  # noqa: E731
    print(f"\n{'version':8} {'decision':>9} {'real':>6} {'junk':>6} {'grounded':>9} {'overlap':>8} "
          f"{'cited':>6} {'tokens':>7} {'words':>6} {'ms':>6}  live")
    summaries = sorted(results["versions"].values(), key=lambda v: v["version"])
    for v in summaries:
        print(f"{v['version']:8} {fmt(v['decision']):>9} {fmt(v['answered_real']):>6} {fmt(v['declined_junk']):>6} "
              f"{fmt(v['grounded']):>9} {fmt(v['overlap']):>8} {fmt(v['cited']):>6} {v['prompt_tokens']:>7} "
              f"{v['median_words']:>6} {v['median_ms']:>6}  {v['live_answers']}/{v['questions']}")

    # A version is only eligible if the model actually answered (nearly) every
    # question. An earlier run "selected" a version on 2 live answers out of 24,
    # after the provider quota ran out mid-run -- its perfect scores were two data
    # points plus fallbacks.
    eligible = [v for v in summaries if v["live_answers"] >= MIN_LIVE_SHARE * v["questions"]]
    for v in summaries:
        v["eligible"] = v in eligible
    if not eligible:
        print("\nno version has enough live answers to select -- rerun when the provider quota resets")
        RESULTS.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
        return 1
    ranked = sorted(eligible, key=lambda v: (v["decision"] or 0, v["grounded"] or 0,
                                             round(v["overlap"] or 0, 2), -(v["prompt_tokens"] or 0)),
                    reverse=True)
    results["selected"] = ranked[0]["version"]
    from interview.chains.pipeline import provider_chain

    live_provider = provider_chain()[0] if provider_chain() else None
    results["provider"] = f"{live_provider.label} ({live_provider.model})" if live_provider else None
    results["rule"] = ("among versions with at least 90% live answers: best decision, then grounded, "
                       "then overlap (2 d.p.), then the smaller prompt")
    RESULTS.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nselected: {results['selected']}  (set LIVE_VERSION in interview/prompting/registry.py to match)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

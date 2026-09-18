"""Retrieval evaluation for the interview corpus.

    python -m interview.retrieval.eval              # every retriever combination
    python -m interview.retrieval.eval -v           # per-question detail
    python -m interview.retrieval.eval --calibrate  # also fit the answer/decline thresholds

Every must-match question is **reworded** relative to the corpus -- different
verbs, different nouns, the way a visitor actually types. Testing with the
corpus's own question text would only prove that a string matches itself, and
would hide exactly the paraphrase failures that semantic retrieval exists to fix.

These questions were written before any retrieval result was seen, and the
retrievers have not been tuned against them word by word -- no synonyms were added
for the specific terms that missed. That is what keeps the numbers honest.

Must-decline questions are things the corpus genuinely does not cover. Several
share surface words with it on purpose ("Noida", "python" the snake) because that
is how a lexical retriever gets fooled.

Query embeddings are cached in `.embed_cache.json` next to this file so re-running
the eval does not spend the free-tier embedding quota.

Exits non-zero if the production configuration falls below the floors.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from interview.retrieval import hybrid

CACHE = Path(__file__).with_name(".embed_cache.json")
RESULTS = Path(__file__).with_name("results.json")

# (question as a visitor would type it, acceptable corpus ids)
MUST_MATCH = [
    ("would he be a good hire for an ai engineering team", ["01-1-1", "15-15-9"]),
    ("what llm stuff has he put into production", ["01-1-2", "02-2-1", "01-1-8"]),
    ("he's only got one year, why not pick a senior person", ["01-1-3", "13-13-1"]),
    ("give me the quick summary of his career", ["01-1-5"]),
    ("is the ai work legit or just online courses", ["01-1-6", "13-13-2"]),
    ("what numbers can he point to", ["01-1-7", "13-13-7"]),
    ("why switch from testing to building ai", ["01-1-9", "08-8-4", "13-13-4"]),
    ("what are his weak spots", ["01-1-11", "13-13-11", "13-13-6"]),
    ("explain the template generation bot at his company", ["02-2-1", "02-2-11"]),
    ("why not just call the openai api for the venera feature", ["02-2-2"]),
    ("what stops the bot producing a broken template", ["02-2-3", "04-4-5"]),
    ("did someone else build the chatbot for him", ["02-2-6", "13-13-2"]),
    ("how does the chatbot find relevant templates", ["02-2-7"]),
    ("is the chatbot actually live for customers", ["02-2-10", "02-2-8"]),
    ("why keyword search rather than vectors on this website", ["03-3-2", "12-12-5"]),
    ("how big should the text pieces be when indexing documents", ["03-3-3"]),
    ("combining keyword and semantic search", ["03-3-4"]),
    ("has he used pinecone or similar", ["03-3-8", "10-10-1"]),
    ("what does the bot do when it doesn't know the answer", ["03-3-9", "07-7-2"]),
    ("how would he set up retrieval for our company wiki", ["03-3-12", "02-2-12"]),
    ("how does he stop the model from making things up", ["04-4-3", "03-3-1"]),
    ("getting clean json out of a language model", ["04-4-5"]),
    ("does he make the model think step by step", ["04-4-6"]),
    ("can users trick the assistant with malicious instructions", ["04-4-7", "11-11-6"]),
    ("does he keep track of prompt changes over time", ["04-4-11", "04-4-9"]),
    ("has he trained or tuned a model himself", ["05-5-1", "05-5-9"]),
    ("training a model versus retrieving documents, which one", ["05-5-2", "05-5-7"]),
    ("what is low rank adaptation", ["05-5-3"]),
    ("cutting down the api bill for llm features", ["05-5-8"]),
    ("experience running models locally without a cloud api", ["05-5-6", "02-2-2"]),
    ("what has he made using langchain", ["06-6-1"]),
    ("is langgraph real experience or just on the resume", ["06-6-4", "06-6-5"]),
    ("when should you not use an agent", ["06-6-6"]),
    ("why does he always write test sets for ai", ["07-7-1", "02-2-9"]),
    ("tell me about something that broke in his project", ["07-7-3", "03-3-6", "11-11-7"]),
    ("how do you grade answers that have no single right response", ["07-7-7"]),
    ("the production outage he prevented", ["08-8-2", "12-12-1"]),
    ("his selenium automation work", ["08-8-1", "10-10-3"]),
    ("amazon web services background", ["09-9-1", "14-14-5"]),
    ("what did he do when the ai models got discontinued", ["09-9-11", "12-12-11"]),
    ("how is the portfolio hosted and what does it cost", ["11-11-5", "09-9-6"]),
    ("why so many llm providers on a personal site", ["11-11-2"]),
    ("tell me about an error he made", ["12-12-2", "07-7-3"]),
    ("a time he pushed back on the usual way of doing things", ["12-12-5"]),
    ("how good is his python really", ["14-14-1"]),
    ("which ai skills has he used for real vs just studied", ["14-14-2", "01-1-6"]),
    ("where did he study and what grades", ["15-15-1"]),
    ("how much notice does he need to give", ["15-15-5"]),
    ("what pay is he expecting", ["15-15-6"]),
    ("can he relocate or work from home", ["15-15-4"]),
    ("how do i reach him", ["15-15-7"]),
    ("can i download his cv", ["15-15-10"]),
]

# Exact terms: names, tools, numbers, identifiers. This is the category lexical
# retrieval exists for, and the reworded set above structurally cannot test it --
# without these, the eval would be biased against BM25 by construction.
EXACT_TERM = [
    ("selenium grid", ["10-10-3", "14-14-4"]),
    ("the 79 defects in zoho", ["08-8-7"]),
    ("his cgpa at chandigarh university", ["15-15-1"]),
    ("what is quasar", ["09-9-1", "09-9-2", "08-8-3"]),
    ("severity-1 503", ["08-8-2", "12-12-1"]),
    ("pinecone", ["03-3-8", "10-10-1"]),
    ("bm25", ["03-3-2", "10-10-9"]),
    ("lora rank", ["05-5-3"]),
    ("streamlit", ["14-14-10", "10-10-1"]),
    ("nullclass internship", ["10-10-4", "14-14-6"]),
    ("page object model", ["08-8-1", "14-14-4"]),
    ("postman api validation", ["08-8-3", "14-14-4"]),
    ("reciprocal rank fusion", ["03-3-4"]),
    ("jeetendrapatel1711@gmail.com", ["15-15-7"]),
]

# The corpus says nothing about these. Some share words with it deliberately.
MUST_DECLINE = [
    "what is his favourite movie",
    "is he married",
    "what is the capital of france",
    "which cricket team does he support",
    "what car does he drive",
    "what is his religion",
    "how tall is he",
    "recommend a good pizza place in noida",
    "what is the weather like today",
    "how do i care for a pet python snake",
    "who won the football world cup",
    "what is his blood group",
]

# The configuration the live site uses (its weights live in hybrid.py). The
# comparison rows below use equal weights, so combinations are compared fairly.
PRODUCTION = hybrid.PRODUCTION

COMBINATIONS = [
    ("bm25",),
    ("lsa",),
    ("dense",),
    ("bm25", "lsa"),
    ("bm25", "dense"),
    ("bm25", "dense", "lsa"),
]

RECALL_FLOOR = 0.80      # production recall@3 below this fails the build
DECLINE_FLOOR = 0.85     # answer/decline accuracy below this fails the build


def prewarm(index) -> int:
    """Embed every eval question once (with retry), so later passes hit the cache."""
    missing = 0
    for question in [q for q, _ in MUST_MATCH + EXACT_TERM] + MUST_DECLINE:
        if index.embedder(question, retry=True) is None:
            missing += 1
    return missing


def recall(index, retrievers, cases=None, k: int = 3, verbose: bool = False):
    hits, misses = 0, []
    for question, expected in (MUST_MATCH if cases is None else cases):
        if retrievers == "live":
            docs, trace = index.search(question, top_k=k)  # production retrievers + weights
        else:
            docs, trace = index.search(question, top_k=k, retrievers=retrievers,
                                       weights={r: 1.0 for r in retrievers})
        got = [d["id"] for d in docs]
        ok = any(e in got for e in expected)
        hits += ok
        if not ok:
            misses.append((question, expected, got))
        if verbose:
            print(f"  {'ok ' if ok else 'MISS'} [{'+'.join(retrievers):16}] {question[:55]:55} -> {got}")
    return hits, misses


def best_signals(index, question: str) -> dict:
    """Best score per retriever, for threshold fitting."""
    out = {"bm25": max((s for s, _ in index.bm25(question)), default=0.0)}
    ranked = index.lsa(question)
    out["lsa"] = ranked[0][0] if ranked else 0.0
    dense = index.dense(question)
    out["dense"] = dense[0][0] if dense else None
    return out


def decide(sig: dict, path: str, t: dict) -> bool:
    if path == "dense" and sig["dense"] is not None:
        return sig["dense"] >= t["dense"] or sig["bm25"] >= t["bm25_strong"]
    return sig["bm25"] >= t["bm25"] or sig["lsa"] >= t["lsa"]


def answer_accuracy(signals, path: str, t: dict):
    answered = sum(decide(s, path, t) for s in signals["match"])
    declined = sum(not decide(s, path, t) for s in signals["decline"])
    return answered, declined


def fit(signals, path: str) -> dict:
    """Grid-search thresholds: answer every real question first, then decline as
    much as possible.

    The objective is deliberately asymmetric. This gate runs *before* the model;
    anything it lets through still meets a prompt that tells the model to decline
    questions outside his record. A question it wrongly declines never gets that
    chance, and the visitor is simply turned away. So a false decline is the
    expensive error here, and the gate is fitted to avoid it first."""
    best = None
    if path == "dense":
        grid = [{"dense": d / 100, "bm25_strong": b / 2}
                for d in range(40, 91) for b in range(10, 41)]
    else:
        grid = [{"bm25": b / 2, "lsa": l / 100}
                for b in range(4, 31) for l in range(20, 91, 5)]
    for t in grid:
        a, d = answer_accuracy(signals, path, t)
        key = (a, d, tuple(t.values()))
        if best is None or key > best[0]:
            best = (key, t)
    return best[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--calibrate", action="store_true")
    args = parser.parse_args()

    try:  # the site loads .env at startup; this entry point has to do it itself
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    index = hybrid.load(cache_file=CACHE)
    n, m = len(MUST_MATCH), len(MUST_DECLINE)
    print("=" * 70)
    print(f"interview retrieval eval -- {n} reworded questions, {m} must-decline")
    print("=" * 70)

    has_dense = index.embedder is not None
    if has_dense:
        missing = prewarm(index)
        if missing:
            print(f"[warn] {missing} questions could not be embedded ({index.embedder.last_error}); "
                  "dense results are partial")
    else:
        print("[warn] index has no dense vectors; dense combinations are skipped")

    results = {}
    e = len(EXACT_TERM)
    print(f"{'recall@3':10}{'':18} {'reworded':>10} {'exact-term':>12} {'combined':>10}")
    rows = [c for c in COMBINATIONS if has_dense or "dense" not in c]
    if has_dense:
        rows.append("live")
    for combo in rows:
        hits, misses = recall(index, combo, verbose=args.verbose)
        ehits, emisses = recall(index, combo, cases=EXACT_TERM, verbose=args.verbose)
        results[combo] = (hits, misses, ehits, emisses)
        label = "live: " + "+".join(
            f"{r}@{hybrid.WEIGHTS[r]:g}" for r in PRODUCTION) if combo == "live" else "+".join(combo)
        print(f"{'':10}{label:18} {hits:>4}/{n} {hits / n:4.0%} {ehits:>5}/{e} {ehits / e:4.0%}"
              f" {hits + ehits:>5}/{n + e} {(hits + ehits) / (n + e):4.0%}")

    signals = {
        "match": [best_signals(index, q) for q, _ in MUST_MATCH],
        "decline": [best_signals(index, q) for q in MUST_DECLINE],
    }
    thresholds = {
        "dense": {"dense": hybrid.MIN_DENSE, "bm25_strong": hybrid.MIN_BM25_STRONG},
        "fallback": {"bm25": hybrid.MIN_BM25, "lsa": hybrid.MIN_LSA},
    }
    if args.calibrate:
        if has_dense:
            thresholds["dense"] = fit(signals, "dense")
        thresholds["fallback"] = fit(signals, "fallback")
        print("\ncalibrated thresholds (copy into interview/retrieval/hybrid.py):")
        print(f"  MIN_DENSE = {thresholds['dense']['dense']}   MIN_BM25_STRONG = {thresholds['dense']['bm25_strong']}")
        print(f"  MIN_BM25 = {thresholds['fallback']['bm25']}   MIN_LSA = {thresholds['fallback']['lsa']}")

    print()
    decline_scores = {}
    for path in (["dense"] if has_dense else []) + ["fallback"]:
        a, d = answer_accuracy(signals, path, thresholds[path])
        decline_scores[path] = (a + d) / (n + m)
        print(f"answer/decline  {path:8} {a + d}/{n + m}  (answered {a}/{n}, declined {d}/{m})")

    production = "live" if has_dense else ("bm25", "lsa")
    prod_path = "dense" if has_dense else "fallback"
    prod_misses = results[production][1] + results[production][3]
    if prod_misses:
        print("\nlive configuration misses:")
        for question, expected, got in prod_misses:
            print(f"  Q: {question}\n     expected {expected}\n     got      {got}")
    wrong = [q for q, s in zip([q for q, _ in MUST_MATCH], signals["match"])
             if not decide(s, prod_path, thresholds[prod_path])]
    wrong += [q for q, s in zip(MUST_DECLINE, signals["decline"]) if decide(s, prod_path, thresholds[prod_path])]
    if wrong:
        print(f"\nanswer/decline errors ({prod_path} path):")
        for q in wrong:
            print(f"  {q}")

    combined = (results[production][0] + results[production][2]) / (n + len(EXACT_TERM))
    ok = combined >= RECALL_FLOOR and decline_scores[prod_path] >= DECLINE_FLOOR

    # The site reads this file to show measured numbers rather than typed ones.
    import json

    e = len(EXACT_TERM)
    RESULTS.write_text(json.dumps({
        "questions": {"reworded": n, "exact_term": e, "must_decline": m},
        "recall_at_3": {
            ("live" if combo == "live" else "+".join(combo)): {
                "reworded": round(hits / n, 3),
                "exact_term": round(ehits / e, 3),
                "combined": round((hits + ehits) / (n + e), 3),
            }
            for combo, (hits, _, ehits, _) in results.items()
        },
        "live_config": {r: hybrid.WEIGHTS[r] for r in PRODUCTION},
        "answer_decline": {path: round(score, 3) for path, score in decline_scores.items()},
        "passed": ok,
    }, indent=1), encoding="utf-8")

    print("\n" + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

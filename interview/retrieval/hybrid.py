"""Hybrid retrieval over the interview corpus.

Three retrievers, each weak where another is strong, fused by rank:

* **BM25** (lexical) -- the same scorer, tokenizer and synonym layer as the resume
  index. Exact on names, tools and numbers; blind to paraphrase. Local.
* **Dense** (embeddings) -- the query is embedded with the same model the answers
  were embedded with at build time, and compared by cosine. Carries general
  language knowledge, so "what pay is he expecting" reaches the salary answer even
  though the corpus never says "pay". One network call per new question.
* **LSA** (latent semantic) -- the query is folded into an SVD space built from the
  corpus alone. Weaker than dense, but local and free, so it is what stands in when
  the embedding call is unavailable.

**Reciprocal Rank Fusion** merges rankings by position, not score: BM25 scores and
cosine similarities live on incomparable scales, and a weighted sum of them needs a
normalisation that silently breaks whenever either side changes. RRF needs none.

**Nothing here depends on the network.** If the embedding call fails, times out or
hits the free-tier quota, dense retrieval drops out, LSA takes its place, and the
trace says so. The site degrades; it does not break.

Whether to answer at all is a separate decision (`answerable()`), because semantic
retrieval always returns *something* -- the nearest answer to an unrelated question
is still a nearest answer.
"""

from __future__ import annotations

import gzip
import json
import math
import os
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from functools import lru_cache
from pathlib import Path

from core.rag import BM25Index, tokenize
from interview.index.build_index import ARTIFACT, document_text

RRF_K = 60            # standard constant; damps the gap between rank 1 and rank 2
SEMANTIC_DEPTH = 20   # only the top of a semantic ranking votes in the fusion

# Production retrieval: embeddings lead, BM25 votes at a quarter weight.
# Chosen from interview/retrieval/eval.py on 52 reworded + 14 exact-term questions,
# measured 2026-09-18 when the choice was made:
#   dense alone 60/66, dense + bm25@0.25 60/66, @0.5 57/66, @1.0 58/66,
#   bm25 alone 36/66, bm25 + lsa 36/66.
# Current numbers move a little whenever the corpus is edited and re-embedded; the
# latest run is in interview/retrieval/results.json and on the Interview Lab page.
# The embedding model handles exact terms (tool names, numbers) about as well as
# BM25 on this corpus, so a full-weight lexical vote only dilutes it. The quarter
# weight costs nothing measurable and is kept as insurance for identifiers an
# embedding model has never seen (error codes, new product names) -- a case the
# eval does not cover, so that part is a judgement, not a measurement.
PRODUCTION = ("dense", "bm25")
WEIGHTS = {"dense": 1.0, "bm25": 0.25, "lsa": 1.0}
# When the embedding call is unavailable, BM25 and LSA vote equally.
FALLBACK_WEIGHTS = {"bm25": 1.0, "lsa": 1.0}

# The embedding call shares the request's time budget with the model call that
# follows it, so it gets a short leash -- a *total* deadline, enforced with a
# worker thread. urllib's own timeout applies per socket operation, not per
# request, and a single call was measured at 3.9 s against a 2.5 s "timeout".
# Missing the deadline costs a little recall for that question, not an answer.
EMBED_TIMEOUT = float(os.environ.get("INTERVIEW_EMBED_TIMEOUT", "2.0"))
_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="embed")

# Answer-or-decline gate, fitted by `python -m interview.retrieval.eval --calibrate`
# to answer every real question first and decline as much as possible second.
#
# Similarity cannot decide scope on this corpus, and the thresholds are set with
# that in mind. Real questions score as low as 0.596 ("what are his weak spots")
# while junk scores as high as 0.651 ("what car does he drive"): short personal
# questions about "him" land close to answers about him. No threshold separates
# those, so this gate only turns away what is clearly unrelated, and deciding
# whether a question is about his professional record is left to the model,
# whose prompt tells it to decline -- measured end to end in the prompt eval.
MIN_DENSE = 0.59          # with an embedding: best cosine must reach this ...
MIN_BM25_STRONG = 20.0    # ... unless the keyword match alone is this strong
MIN_BM25 = 4.5            # fallback path (no embedding): keyword threshold ...
MIN_LSA = 0.55            # ... or corpus-only semantic threshold


class QueryEmbedder:
    """Embeds questions with the model the corpus was built with.

    Results are cached per process. `cache_file` adds a persistent cache, used by
    the evaluation so re-running it does not spend the embedding quota.
    """

    def __init__(self, model: str, dims: int, cache_file: Path | None = None):
        self.model, self.dims = model, dims
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.cache_file = cache_file
        self.last_error: str | None = None
        self._cache: dict[str, list[float]] = {}
        if cache_file and cache_file.exists():
            self._cache = json.loads(cache_file.read_text(encoding="utf-8"))

    def __call__(self, text: str, retry: bool = False) -> list[float] | None:
        key = text.strip().lower()
        if key in self._cache:
            return self._cache[key]
        if not self.api_key:
            self.last_error = "no GEMINI_API_KEY"
            return None
        for attempt in range(4 if retry else 1):
            future = _POOL.submit(self._request, text)
            try:
                # The eval (retry=True) waits as long as it takes; the live path
                # gets a hard deadline.
                vector = future.result(timeout=None if retry else EMBED_TIMEOUT)
                break
            except FutureTimeout:
                self.last_error = f"timeout after {EMBED_TIMEOUT:g}s"
                # Let the call finish in the background and keep its result, so an
                # identical question asked again gets the embedding for free.
                future.add_done_callback(lambda f, k=key: self._store(k, f))
                return None
            except urllib.error.HTTPError as exc:
                self.last_error = f"HTTP {exc.code}"
                if exc.code == 429 and retry and attempt < 3:
                    time.sleep(35)
                    continue
                return None
            except Exception as exc:  # DNS, TLS, anything: degrade, don't fail
                self.last_error = type(exc).__name__
                return None
        self.last_error = None
        return self._store(key, vector)

    def _store(self, key: str, value) -> list[float] | None:
        """Normalise and cache a vector (or a finished future's vector)."""
        if hasattr(value, "result"):
            try:
                value = value.result()
            except Exception:
                return None
        norm = math.sqrt(sum(x * x for x in value)) or 1.0
        vector = [x / norm for x in value]
        self._cache[key] = vector
        if self.cache_file:
            self.cache_file.write_text(json.dumps(self._cache), encoding="utf-8")
        return vector

    def _request(self, text: str) -> list[float]:
        body = {
            "model": f"models/{self.model}",
            "content": {"parts": [{"text": text}]},
            "taskType": "RETRIEVAL_QUERY",
            "outputDimensionality": self.dims,
        }
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
                "User-Agent": "jeetendra-portfolio/1.0",
            },
        )
        # Socket timeout deliberately longer than EMBED_TIMEOUT: the deadline
        # protects the visitor's wait, while this only stops a stuck call from
        # lingering. A call that misses the deadline can still finish and be cached.
        with urllib.request.urlopen(req, timeout=max(10.0, EMBED_TIMEOUT)) as resp:
            return json.load(resp)["embedding"]["values"]


class CorpusIndex:
    def __init__(self, artifact: dict, cache_file: Path | None = None):
        self.docs = artifact["docs"]
        self.parts = artifact["parts"]
        self.stats = artifact["stats"]

        self._bm25 = BM25Index(
            [
                {"id": d["id"], "title": d["question"], "tags": d["tags"], "text": document_text(d)}
                for d in self.docs
            ]
        )
        self._pos = {d["id"]: i for i, d in enumerate(self.docs)}

        lsa = artifact["lsa"]
        self._vocab = {t: i for i, t in enumerate(lsa["vocab"])}
        self._idf = lsa["idf"]
        self._term_vecs = lsa["term_vecs"]
        self._lsa_docs = lsa["doc_vecs"]
        self._lsa_norms = [math.sqrt(sum(x * x for x in v)) or 1.0 for v in self._lsa_docs]
        self._lsa_dims = lsa["dims"]

        dense = artifact.get("dense")
        if dense:
            self._dense_docs = dense["doc_vecs"]
            self._dense_norms = [math.sqrt(sum(x * x for x in v)) or 1.0 for v in self._dense_docs]
            self.embedder = QueryEmbedder(dense["model"], dense["dims"], cache_file)
        else:
            self._dense_docs = None
            self.embedder = None

    # ── retrievers ─────────────────────────────────────────────────────────

    def bm25(self, query: str) -> list[tuple[float, int]]:
        hits = self._bm25.search(query, top_k=len(self.docs), min_score=0.0)
        return [(h["score"], self._pos[h["id"]]) for h in hits]

    def lsa(self, query: str) -> list[tuple[float, int]]:
        counts = Counter(t for t in tokenize(query) if t in self._vocab)
        if not counts:
            return []
        q = [0.0] * self._lsa_dims
        for term, tf in counts.items():
            i = self._vocab[term]
            weight = (1 + math.log(tf)) * self._idf[i]
            for d, x in enumerate(self._term_vecs[i]):
                q[d] += weight * x
        return self._rank_by_cosine(q, self._lsa_docs, self._lsa_norms)

    def dense(self, query: str, retry: bool = False) -> list[tuple[float, int]] | None:
        """Cosine ranking by embedding, or None when an embedding isn't available."""
        if self._dense_docs is None:
            return None
        vector = self.embedder(query, retry=retry)
        if vector is None:
            return None
        return self._rank_by_cosine(vector, self._dense_docs, self._dense_norms)

    @staticmethod
    def _rank_by_cosine(q, docs, norms) -> list[tuple[float, int]]:
        q_norm = math.sqrt(sum(x * x for x in q)) or 1.0
        scored = []
        for j, vec in enumerate(docs):
            cos = sum(a * b for a, b in zip(q, vec)) / (q_norm * norms[j])
            if cos > 0:
                scored.append((cos, j))
        scored.sort(key=lambda p: (-p[0], p[1]))
        return scored

    # ── fusion ─────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 5, retrievers=PRODUCTION,
               weights: dict | None = None, retry: bool = False) -> tuple[list[dict], dict]:
        """(top documents, trace). If dense is requested but unavailable, LSA stands in.

        `weights` defaults to the production weights; pass equal weights to compare
        retriever combinations fairly, as the eval does.
        """
        rankings: dict[str, list[tuple[float, int]]] = {}
        used = list(retrievers)
        if "bm25" in retrievers:
            rankings["bm25"] = self.bm25(query)
        if "dense" in retrievers:
            ranked = self.dense(query, retry=retry)
            if ranked is None:
                used.remove("dense")
                if "lsa" not in used:
                    used.append("lsa")
            else:
                rankings["dense"] = ranked[:SEMANTIC_DEPTH]
        if "lsa" in used:
            rankings["lsa"] = self.lsa(query)[:SEMANTIC_DEPTH]

        if weights is None:
            weights = WEIGHTS if "dense" in used else FALLBACK_WEIGHTS
        fused: dict[int, float] = {}
        signals: dict[int, dict] = {}
        for name, ranking in rankings.items():
            w = weights.get(name, 1.0)
            for rank, (score, j) in enumerate(ranking, start=1):
                fused[j] = fused.get(j, 0.0) + w / (RRF_K + rank)
                signals.setdefault(j, {})[name] = round(score, 3)

        order = sorted(fused, key=lambda j: (-fused[j], j))[:top_k]
        hits = [{**self.docs[j], "score": round(fused[j], 5), "signals": signals[j]} for j in order]
        best = {name: round(r[0][0], 3) if r else 0.0 for name, r in rankings.items()}
        trace = {
            "retrievers": used,
            "dense_fallback": ("dense" in retrievers and "dense" not in used),
            "dense_error": self.embedder.last_error if self.embedder else "no dense vectors in index",
            "best": best,
        }
        return hits, trace

    def answerable(self, trace: dict) -> bool:
        """Enough evidence to answer? Uses whichever signals the search actually had."""
        best = trace["best"]
        if "dense" in best:
            return best["dense"] >= MIN_DENSE or best.get("bm25", 0.0) >= MIN_BM25_STRONG
        return best.get("bm25", 0.0) >= MIN_BM25 or best.get("lsa", 0.0) >= MIN_LSA

    def by_part(self, part: int) -> list[dict]:
        return [d for d in self.docs if d["part"] == part]


def load(cache_file: Path | None = None) -> CorpusIndex:
    started = time.perf_counter()
    with gzip.open(ARTIFACT, "rt", encoding="utf-8") as fh:
        artifact = json.load(fh)
    index = CorpusIndex(artifact, cache_file)
    index.load_ms = round((time.perf_counter() - started) * 1000, 1)
    return index


@lru_cache(maxsize=1)
def get_index() -> CorpusIndex:
    """The process-wide index, loaded on first use."""
    return load()

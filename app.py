"""Flask app serving the portfolio and the resume-grounded assistant API."""

import os
import time
from collections import deque
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

try:  # optional: lets local dev pick up a .env without exporting vars by hand
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # Silently skipping is fine in production (real env vars, no .env file), but
    # locally it looks like the key was ignored for no reason -- so say something.
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")):
        print(
            "[warn] .env found but python-dotenv is not installed, so it was NOT loaded.\n"
            "       pip install python-dotenv   (or export the vars manually)"
        )

from core import llm
from data.profile import (
    ABOUT,
    BUGS,
    CERTIFICATIONS,
    EDUCATION,
    EXPERIENCE,
    FOCUS,
    HERO,
    METRICS,
    NAV,
    PROFILE,
    PROJECTS,
    SKILL_GROUPS,
    SUGGESTED_PROMPTS,
)

app = Flask(__name__)
ROOT = Path(__file__).parent


def _measured_about():
    """Fill the About stats from the running system instead of hardcoded numbers.

    These figures drifted three times while the corpus grew — the section presents
    them as measured, so measure them. Computed once at import; the corpus is
    static after boot.
    """
    about = {**ABOUT, "stats": [dict(s) for s in ABOUT["stats"]]}
    by_label = {s["label"]: s for s in about["stats"]}

    try:
        from data.knowledge import CHUNKS

        if "indexed resume chunks" in by_label:
            by_label["indexed resume chunks"]["value"] = str(len(CHUNKS))
    except Exception:
        pass

    try:
        import eval_retrieval

        passed, total = eval_retrieval.run_quiet()
        if "retrieval eval passing" in by_label:
            stat = by_label["retrieval eval passing"]
            stat["value"] = f"{passed}/{total}"
            stat["detail"] = (
                f"{len(eval_retrieval.CASES)} must-match + "
                f"{len(eval_retrieval.OUT_OF_SCOPE_CASES)} must-decline questions"
            )
    except Exception:
        pass  # never let a stat break the page

    try:
        import json

        results = json.loads((ROOT / "interview/retrieval/results.json").read_text(encoding="utf-8"))
        recall = results["recall_at_3"]
        if "interview retrieval recall@3" in by_label:
            stat = by_label["interview retrieval recall@3"]
            stat["value"] = f"{recall['live']['combined']:.0%}"
            stat["detail"] = f"vs {recall['bm25']['combined']:.0%} for keyword search alone"
    except Exception:
        pass

    try:
        from interview.retrieval import hybrid

        stats = hybrid.get_index().stats
        if "interview questions" in by_label:
            stat = by_label["interview questions"]
            stat["value"] = str(stats["questions"])
            stat["detail"] = f"{stats['pages']} pages at 500 words/page"
    except Exception:
        pass

    return about


ABOUT_MEASURED = _measured_about()

# Simple in-process rate limit. The site is single-instance and public, so this is
# about keeping a stray script from burning API credits, not about security.
RATE_LIMIT = int(os.environ.get("CHAT_RATE_LIMIT", "20"))
RATE_WINDOW = 60.0
_hits = {}


def _rate_limited(key):
    now = time.monotonic()
    bucket = _hits.setdefault(key, deque())
    while bucket and now - bucket[0] > RATE_WINDOW:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT:
        return True
    bucket.append(now)
    return False


@app.route("/")
def index():
    return render_template(
        "index.html",
        profile=PROFILE,
        hero=HERO,
        focus=FOCUS,
        about=ABOUT_MEASURED,
        bugs=BUGS,
        metrics=METRICS,
        experience=EXPERIENCE,
        projects=PROJECTS,
        skill_groups=SKILL_GROUPS,
        education=EDUCATION,
        certifications=CERTIFICATIONS,
        nav=NAV,
        prompts=SUGGESTED_PROMPTS,
        engine=llm.engine_status(),
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    question = payload.get("message", "")
    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "message is required"}), 400

    client_key = request.headers.get("X-Forwarded-For", request.remote_addr or "local").split(",")[0]
    if _rate_limited(client_key):
        return (
            jsonify(
                {
                    "answer": "That's a lot of questions at once. Give it a minute, or email "
                    f"{PROFILE['email']} directly.",
                    "sources": [],
                    "live": False,
                }
            ),
            429,
        )

    history = payload.get("history")
    if not isinstance(history, list):
        history = []
    # History arrives from the browser, so it is trimmed and validated the same
    # way the resume assistant does it before anything else sees it.
    history = llm._normalise_history(history)

    # The interview agent is imported on first use, not at startup: it pulls in
    # LangGraph (~1.8 s to import cold), and the homepage should not pay that.
    try:
        from interview.graph import agent

        return jsonify(agent.run(question, history))
    except Exception as exc:  # the agent must never be the reason the chat breaks
        app.logger.warning("interview agent failed, using resume assistant: %s", exc)
        result = llm.answer(question, history)
        result["engines"] = {"graph": None, "chain": None, "retrieval": "resume-bm25"}
        result["outcome"] = "agent_unavailable"
        return jsonify(result)


# ── interview corpus ────────────────────────────────────────────────────────

def _json_file(path):
    import json

    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


@app.route("/api/interview/stats")
def interview_stats():
    """Corpus size, and the latest measured results of every evaluation."""
    from interview.retrieval import hybrid

    index = hybrid.get_index()
    prompt_results = _json_file(ROOT / "interview/prompting/results.json") or {}
    return jsonify({
        "corpus": index.stats,
        "parts": [{k: p[k] for k in ("part", "topic", "count", "intro")} for p in index.parts],
        "retrieval": _json_file(ROOT / "interview/retrieval/results.json"),
        "prompts": {
            "selected": prompt_results.get("selected"),
            "rule": prompt_results.get("rule"),
            "versions": {
                vid: {k: v[k] for k in v if k != "rows"}
                for vid, v in (prompt_results.get("versions") or {}).items()
            },
        },
        "finetune": _json_file(ROOT / "interview/finetune/data/stats.json"),
    })


@app.route("/api/interview/questions")
def interview_questions():
    """Every question in the corpus, grouped by part, without the answers."""
    from interview.retrieval import hybrid

    index = hybrid.get_index()
    return jsonify([
        {
            "part": p["part"],
            "topic": p["topic"],
            "questions": [
                {"id": d["id"], "question": d["question"], "difficulty": d["difficulty"]}
                for d in index.by_part(p["part"])
            ],
        }
        for p in index.parts
    ])


@app.route("/interview/document")
def interview_document():
    """The full corpus as a PDF, generated from the same sources the assistant uses."""
    return send_from_directory(
        os.path.join(app.static_folder, "files"),
        "Jeetendra_Kumar_Patel_Interview_QA.pdf",
        as_attachment=False,
    )


@app.route("/api/interview/answer/<qid>")
def interview_answer(qid):
    from interview.retrieval import hybrid

    doc = next((d for d in hybrid.get_index().docs if d["id"] == qid), None)
    if doc is None:
        return jsonify({"error": "unknown question"}), 404
    return jsonify({k: doc[k] for k in ("id", "question", "answer", "follow_up", "grounded_in", "topic")})


@app.route("/api/health")
def health():
    """`?probe=1` makes one real provider call to prove the key actually works.

    Kept opt-in so uptime monitors pinging this every few minutes don't burn a
    free-tier quota.
    """
    probe = request.args.get("probe") in ("1", "true", "yes")
    return jsonify({"status": "ok", "engine": llm.engine_status(probe=probe)})


@app.route("/resume")
def resume():
    """Serve the resume PDF if it has been dropped into static/files/."""
    return send_from_directory(
        os.path.join(app.static_folder, "files"),
        PROFILE["resume_file"],
        as_attachment=False,
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
    )

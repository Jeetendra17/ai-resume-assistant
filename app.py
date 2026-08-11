"""Flask app serving the portfolio and the resume-grounded assistant API."""

import os
import time
from collections import deque

from flask import Flask, jsonify, render_template, request, send_from_directory

try:  # optional: lets local dev pick up a .env without exporting vars by hand
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

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
    return jsonify(llm.answer(question, history))


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "engine": llm.engine_status()})


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

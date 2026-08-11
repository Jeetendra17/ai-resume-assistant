"""Turns the structured profile into retrievable text chunks.

Everything the assistant can say is derived from `profile.py`, so the site and the
chatbot can never drift apart.
"""

from .profile import (
    ABOUT,
    BUGS,
    CERTIFICATIONS,
    EDUCATION,
    EXPERIENCE,
    METRICS,
    PROFILE,
    PROJECTS,
    SKILL_GROUPS,
)


def _identity_chunks():
    yield {
        "id": "identity",
        "title": "Who Jeetendra is",
        "tags": ["about", "summary", "profile", "who", "background", "introduction"],
        "text": (
            f"{PROFILE['name']} is an {PROFILE['role']} based in {PROFILE['location']}. "
            f"Current title: {PROFILE['title']}. {PROFILE['summary']}"
        ),
    }
    yield {
        "id": "pitch",
        "title": "Why hire him",
        "tags": ["hire", "fit", "why", "strength", "value", "recruiter", "candidate"],
        "text": PROFILE["pitch"],
    }
    yield {
        "id": "availability",
        "title": "Availability and contact",
        "tags": ["contact", "email", "phone", "hire", "available", "reach", "linkedin"],
        "text": (
            f"{PROFILE['availability_note']}. Email: {PROFILE['email']}. "
            f"Phone: {PROFILE['phone']}. LinkedIn: {PROFILE['linkedin']}. "
            f"Located in {PROFILE['location']}."
        ),
    }


def _metric_chunks():
    lines = [f"{m['value']} {m['label']} ({m['detail']}; {m['trend']})" for m in METRICS]
    yield {
        "id": "metrics",
        "title": "Headline results",
        "tags": ["metrics", "numbers", "impact", "results", "achievements", "measurable", "kpi"],
        "text": "Measurable results: " + "; ".join(lines) + ".",
    }


def _experience_chunks():
    for idx, job in enumerate(EXPERIENCE):
        body = " ".join(job["points"])
        yield {
            "id": f"exp-{idx}",
            "title": f"{job['role']} at {job['company']}",
            "tags": [
                "experience",
                "work",
                "job",
                "role",
                job["company"].lower(),
                job["role"].lower(),
            ]
            + [s.lower() for s in job["stack"]],
            "text": (
                f"{job['role']} at {job['company']}, {job['location']} ({job['period']}, {job['status']}). "
                f"{job['summary']} {body} Stack: {', '.join(job['stack'])}."
            ),
        }


def _project_chunks():
    for project in PROJECTS:
        yield {
            "id": f"proj-{project['name'].lower().replace(' ', '-')}",
            "title": project["name"],
            "tags": ["project", "built", "portfolio", project["category"].lower()]
            + [s.lower() for s in project["stack"]],
            "text": (
                f"Project: {project['name']} ({project['category']}). {project['blurb']} "
                f"Impact: {project['impact']}. Details: {' '.join(project['details'])} "
                f"Stack: {', '.join(project['stack'])}."
            ),
        }


def _skill_chunks():
    for group in SKILL_GROUPS:
        yield {
            "id": f"skill-{group['name'].lower().replace(' ', '-').replace('&', 'and')}",
            "title": f"Skills: {group['name']}",
            "tags": ["skills", "stack", "technologies", "tools"] + [i.lower() for i in group["items"]],
            "text": f"{group['name']} skills: {', '.join(group['items'])}.",
        }


def _education_chunks():
    for edu in EDUCATION:
        yield {
            "id": "education",
            "title": edu["degree"],
            "tags": ["education", "degree", "college", "university", "cgpa", "graduation", "study"],
            "text": f"{edu['degree']} from {edu['school']}. {edu['period']}. {edu['score']}.",
        }
    certs = "; ".join(f"{c['name']} ({c['issuer']}, {c['status']})" for c in CERTIFICATIONS)
    yield {
        "id": "certifications",
        "title": "Certifications and training",
        "tags": ["certification", "course", "training", "bootcamp", "learning", "udemy", "upskilling"],
        "text": f"Certifications and training: {certs}.",
    }


def _about_chunks():
    """The About section: personal narrative plus how this assistant is built."""
    yield {
        "id": "about-bio",
        "title": "About Jeetendra, in his own words",
        "tags": [
            "about", "story", "background", "journey", "himself", "personality",
            "motivation", "career", "transition", "qa", "why", "approach", "philosophy",
        ],
        "text": " ".join(ABOUT["bio"]),
    }

    stats = "; ".join(f"{s['value']} {s['label']} ({s['detail']})" for s in ABOUT["stats"])
    yield {
        "id": "case-overview",
        "title": "How this assistant is built",
        "tags": [
            "assistant", "chatbot", "architecture", "yourself", "you", "site", "portfolio",
            "built", "how", "work", "rag", "retrieval", "bm25", "design", "system",
        ],
        "text": (
            f"{ABOUT['lede']} Pipeline: "
            + " ".join(f"{s['step']}. {s['name']} — {s['text']}" for s in ABOUT["flow"])
            + f" Measured: {stats}. Stack: {', '.join(ABOUT['stack'])}."
        ),
    }

    for decision in ABOUT["decisions"]:
        yield {
            "id": f"case-{decision['title'].lower().replace(' ', '-').replace(',', '')}",
            "title": f"Design decision: {decision['title']}",
            "tags": [
                "decision", "tradeoff", "why", "architecture", "design", "assistant",
                "engineering", "chose", "approach",
            ],
            "text": f"{decision['title']} — {decision['call']}. {decision['why']}",
        }

    yield {
        "id": "case-guardrails",
        "title": "Assistant guardrails and safety",
        "tags": [
            "guardrail", "safety", "hallucination", "grounding", "accurate", "trust",
            "invent", "made", "reliable", "limits",
        ],
        "text": "Guardrails on this assistant: " + " ".join(ABOUT["guardrails"]),
    }

    yield {
        "id": "bugs",
        "title": "Bugs found and fixed while building this",
        "tags": [
            "bug", "broke", "failure", "mistake", "wrong", "debug", "fixed", "issue",
            "problem", "learned", "regression", "caught",
        ],
        "text": (
            "Build log — issues that shipped broken and were then caught and fixed: "
            + " ".join(
                f"({b['id']}) {b['title']}. Cause: {b['cause']} Fix: {b['fix']}" for b in BUGS
            )
        ),
    }

    yield {
        "id": "case-next",
        "title": "What I would build next on this system",
        "tags": ["next", "roadmap", "improve", "future", "evaluation", "streaming", "hybrid"],
        "text": "Planned improvements: " + " ".join(ABOUT["next"]),
    }


def build_chunks():
    """Return the full retrieval corpus as a list of chunk dicts."""
    chunks = []
    for source in (
        _identity_chunks,
        _metric_chunks,
        _experience_chunks,
        _project_chunks,
        _skill_chunks,
        _education_chunks,
        _about_chunks,
    ):
        chunks.extend(source())
    return chunks


CHUNKS = build_chunks()

# Jeetendra Kumar Patel — AI Engineer Portfolio

**Live: <https://jeetendra.vercel.app>**

A Flask portfolio with light and dark themes, and an assistant that recruiters can
question directly — a LangGraph agent over a ~100-page corpus of the questions people
actually ask about me.

- **RAG over 163 grounded Q&As.** Embeddings + BM25, fused by rank: the right answer is in
  the top 3 for about nine in ten reworded questions, against under half for keyword search
  alone (exact figures in the Interview Lab).
- **LangChain + LangGraph, live.** Route → retrieve → grade → generate → verify, with a
  trace of every answer shown under the reply.
- **Prompt engineering by measurement.** Six versioned prompts, scored end to end on 24
  questions; the live one is picked by a fixed rule, not by eye.
- **Fine-tuning dataset + LoRA trainer.** 179 chat-format examples, contamination-checked.
  The trainer is written and dry-run, not yet trained (needs a GPU).
- **Zero cost, never hard-fails.** Free tiers throughout; every stage has a local
  fallback, down to answering from the resume with no API key at all.

---

## Quick start

```bash
cd portfolio
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
cp .env.example .env            # optional — add a free key to switch on real answers
python app.py
```

Open <http://localhost:5000>.

### Retrieval eval

Retrieval has an eval set — 29 recruiter questions paired with the chunks that must
appear in the top 3. **Run it after any change to `data/profile.py` or `core/rag.py`:**

```bash
python eval_retrieval.py        # summary; exits non-zero on failure
python eval_retrieval.py -v     # per-question ranking
```

It exists because a real failure got shipped: *"what has he actually shipped with
LLMs?"* returned a Kotlin chat app and a Java CRUD app. Broad synonyms (`shipped` →
`project`) matched every project chunk equally and buried the one discriminating
term. The eval reproduced it at 26/29; the fix (stemming, phrase normalisation,
weighted expansion) took it to 29/29. A later round added 7 must-decline cases
after it answered a question about hobbies with the career summary — now 36/36.

---

## The interview assistant

The chat answers from `interview/corpus/source/` — 15 parts, 163 questions a recruiter,
hiring manager or engineer asks about me, each with the answer the assistant should give
and the resume facts it rests on. `static/files/Jeetendra_Kumar_Patel_Interview_QA.pdf`
is the same corpus as a document (109 pages).

```
question ─▶ route ─▶ retrieve ─▶ grade ─┬─▶ generate ─▶ verify ─┬─▶ answer + citations + trace
                    (embeddings    │    │   (LangChain chain,     ├─▶ regenerate once
                     + BM25@0.25)  │    │    versioned prompt,    └─▶ quote the source
                                   │    │    Groq → Gemini …)
                                   │    ├─▶ rewrite (follow-ups only, once) ─▶ retrieve
                                   │    └─▶ refuse (no model call)
```

| Piece | Where | Rebuild / run |
|---|---|---|
| Corpus (Markdown → records, validated) | `interview/corpus/` | `python -m interview.corpus.build` |
| Index: BM25 + LSA + Gemini embeddings | `interview/index/` | `python -m interview.index.build_index` |
| Retrieval eval (52 reworded + 14 exact-term + 12 decline) | `interview/retrieval/eval.py` | `python -m interview.retrieval.eval` |
| Prompt registry + end-to-end prompt eval | `interview/prompting/` | `python -m interview.prompting.evaluate` |
| LCEL chains | `interview/chains/pipeline.py` | — |
| LangGraph agent | `interview/graph/agent.py` | — |
| Fine-tuning dataset | `interview/finetune/` | `python -m interview.finetune.build_dataset` |
| LoRA trainer (GPU) | `interview/finetune/train_lora.py` | `python -m interview.finetune.train_lora --dry-run` |
| Document PDF | `interview/corpus/export_pdf.py` | `python -m interview.corpus.export_pdf` |
| Offline tests (both engines) | `tests/` | `python -m unittest discover tests` |

**After editing the corpus:** rebuild the index, rerun the retrieval eval, rebuild the
dataset and the PDF. The index build embeds 163 answers and waits out the free-tier
quota (100 embeddings/min), so it takes a couple of minutes.

LangChain and LangGraph are real dependencies (~38 MB), but `interview/compat/` holds
stdlib stand-ins with the same behaviour, chosen automatically if they are missing
(or forced with `INTERVIEW_GRAPH_ENGINE=stdlib` / `INTERVIEW_CHAIN_ENGINE=stdlib`).
LangGraph is imported on the first question, not at startup: it takes ~1.8 s to import
cold, and the homepage should not pay that.

## The resume assistant (fallback)

The original assistant, still used when the interview agent is unavailable:

```
question ──▶ BM25 over resume chunks ──▶ context block ──▶ provider chain ──▶ answer + source chips
                    (local)                                  (first that works)
```

`data/profile.py` is the single source of truth. The rendered pages, the retrieval
index (`data/knowledge.py`) and the system prompt all derive from it, so the site and
this assistant can never disagree. **To update the portfolio, edit that one file.**
The one exception is the hand-written interview corpus above: every answer names the
resume facts it rests on (`Grounded in`) and the build rejects one that doesn't, but
that is a rule, not a guarantee — when a fact in `profile.py` changes, grep the corpus
for it too.

The system prompt restricts answers to retrieved context, forbids inventing employers,
dates or numbers, and tells the model to be honest about early-career level rather than
overselling.

### Picking a provider

Providers are tried in this order, and the first one with a key set wins:

| Order | Provider | Free tier | Env var | Get a key |
|---|---|---|---|---|
| 1 | Groq | Yes — fastest | `GROQ_API_KEY` | <https://console.groq.com/keys> |
| 2 | Google Gemini | Yes — generous | `GEMINI_API_KEY` | <https://aistudio.google.com/apikey> |
| 3 | Cerebras | Yes | `CEREBRAS_API_KEY` | <https://cloud.cerebras.ai> |
| 4 | OpenRouter | Yes — open-weight `:free` models | `OPENROUTER_API_KEY` | <https://openrouter.ai/keys> |
| 5 | Mistral | Yes | `MISTRAL_API_KEY` | <https://console.mistral.ai/api-keys> |
| 6 | Together AI | Yes | `TOGETHER_API_KEY` | <https://api.together.ai/settings/api-keys> |
| 7 | Ollama (local) | Free, offline | `USE_OLLAMA=1` | <https://ollama.com> |
| 8 | Anthropic Claude | Paid | `ANTHROPIC_API_KEY` | <https://console.anthropic.com> |
| 9 | OpenAI | Paid | `OPENAI_API_KEY` | <https://platform.openai.com/api-keys> |
| — | Resume index (no model) | Always | *(none)* | built in |

Set **two or more** keys and you get automatic failover: if Groq is rate limited, the
request falls through to Gemini, and so on down to the local index.

Pin or reorder explicitly:

```bash
LLM_PROVIDER=groq                  # only Groq
LLM_PROVIDER=gemini,groq           # Gemini first, Groq as backup
GROQ_MODEL=qwen/qwen3.8-27b        # override any provider's model
```

> Note: a Claude Pro / ChatGPT Plus subscription is **not** API access — those are
> billed separately. The free providers above need no card.

---

## Deploy free

**How the live site deploys today:** it is on Vercel (project `jeetendra`), connected to
this repo, so **every push to `main` deploys to production**. Before pushing, run
`python eval_retrieval.py` (must be 36/36) and, if `data/profile.py` changed,
`python build_resume.py`. Keys and model settings are Vercel environment variables.
The step-by-step runbook, including changing keys, verifying and rolling back, is at the
top of [DEPLOYMENT_PLAN.md](DEPLOYMENT_PLAN.md).

> **Full guide with verification, guardrails and troubleshooting:
> [DEPLOYMENT_PLAN.md](DEPLOYMENT_PLAN.md).** The options below are for setting it up
> somewhere new.

### Option A — Render (recommended: real Flask, zero code changes)

1. Push this folder to a GitHub repo.
2. <https://render.com> → **New → Web Service** → connect the repo.
3. Render reads `render.yaml` automatically. If asked, set:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
4. **Environment → Add** `GROQ_API_KEY` (and any others).
5. Deploy. You get `https://<name>.onrender.com`.

Trade-off: the free instance sleeps after ~15 minutes idle, so the first visit after a
quiet spell takes ~50s to wake. Fine for a portfolio link you send deliberately; if you
want it hot, use Option B.

### Option B — Hugging Face Spaces (free, no sleep, fitting for an AI portfolio)

1. <https://huggingface.co/new-space> → SDK: **Docker** → blank template.
2. Push this folder to the Space repo (the included `Dockerfile` targets port 7860).
3. **Settings → Variables and secrets** → add `GROQ_API_KEY` as a *secret*.
4. Live at `https://huggingface.co/spaces/<user>/<space>`.

### Option C — Vercel (fastest cold start, custom domain on free tier)

```bash
npm i -g vercel
cd portfolio
vercel            # accept defaults; vercel.json + api/index.py are already set up
vercel env add GROQ_API_KEY
vercel --prod
```

Runs as a serverless function, so the in-process rate limiter resets per invocation —
harmless here.

> Avoid PythonAnywhere's free tier: it blocks outbound HTTPS to non-whitelisted hosts,
> which breaks every LLM provider call.

### After deploying

Set `SITE_URL=https://your-domain` (OpenRouter uses it for attribution) and confirm
`GET /api/health?probe=1` reports `"reachable": true`.

---

## Customising

| Want to change | Edit |
|---|---|
| Any resume content, metrics, projects, links | `data/profile.py` |
| The About write-up | `ABOUT` in `data/profile.py` |
| The build log | `BUGS` in `data/profile.py` |
| How questions map to resume sections | `_SYNONYMS` in `core/rag.py` |
| Assistant tone and guardrails | `SYSTEM_PROMPT` in `core/llm.py` |
| Add a provider | subclass `OpenAICompatible` in `core/providers.py`, add it to `ALL_PROVIDERS` |
| Colours, spacing, type | `:root` in `static/css/style.css` |
| Resume PDF | replace `static/files/…​.pdf`, update `resume_file` in `profile.py` |

---

## Layout

```
portfolio/
├── app.py                 Flask routes, rate limiting, live-computed About stats
├── core/
│   ├── rag.py             BM25 retrieval: stemming, phrase norm, weighted expansion
│   ├── providers.py       Pluggable LLM backends
│   └── llm.py             Prompt assembly, provider chain, fallback
├── data/
│   ├── profile.py         ← single source of truth (content, About, build log)
│   └── knowledge.py       Profile → retrieval chunks
├── eval_retrieval.py      36-case retrieval eval; exits non-zero on failure
├── build_resume.py        profile.py → one-page resume PDF (keeps site and PDF in sync)
├── interview/             ~100-page interview Q&A corpus the assistant is built on
├── templates/index.html
├── static/{css,js,img,files}
├── DEPLOYMENT_PLAN.md     Runbook for deploying changes, then first-time setup
├── deploy.ps1 · deploy.sh Push provider settings from .env to Vercel (keys never echoed)
└── Procfile · render.yaml · Dockerfile · vercel.json · .vercelignore
```

## API

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | The site |
| `/api/chat` | POST | `{message, history[]}` → `{answer, sources[], live, provider, model}` |
| `/api/health` | GET | Configured provider + chain. `?probe=1` makes one real call to prove it works |
| `/resume` | GET | Resume PDF |

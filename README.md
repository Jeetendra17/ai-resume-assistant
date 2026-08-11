# Jeetendra Kumar Patel — AI Engineer Portfolio

A Flask portfolio built as a light dashboard, with a resume-grounded assistant that
recruiters can question directly.

- **Retrieval runs locally** (BM25 over resume chunks, no external service, no vector DB bill).
- **Generation is multi-provider** and free-tier first — Groq, Gemini, Cerebras, OpenRouter,
  Mistral, Together, Ollama, Anthropic, OpenAI.
- **It never hard-fails.** With no API key at all the assistant still answers by pulling
  the matching resume sections verbatim.

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

## The assistant

```
question ──▶ BM25 over resume chunks ──▶ context block ──▶ provider chain ──▶ answer + source chips
                    (local)                                  (first that works)
```

`data/profile.py` is the single source of truth. The rendered pages, the retrieval
index (`data/knowledge.py`) and the system prompt all derive from it, so the site and
the chatbot can never disagree. **To update the portfolio, edit that one file.**

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
| — | Local resume index | Always | *(none)* | built in |

Set **two or more** keys and you get automatic failover: if Groq is rate limited, the
request falls through to Gemini, and so on down to the local index.

Pin or reorder explicitly:

```bash
LLM_PROVIDER=groq                  # only Groq
LLM_PROVIDER=gemini,groq           # Gemini first, Groq as backup
GROQ_MODEL=llama-3.3-70b-versatile # override any provider's model
```

> Note: a Claude Pro / ChatGPT Plus subscription is **not** API access — those are
> billed separately. The free providers above need no card.

---

## Deploy free

> **Full step-by-step guide with verification, guardrails and troubleshooting:
> [DEPLOYMENT_PLAN.md](DEPLOYMENT_PLAN.md).** The summary below is the short version.

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
`GET /api/health` reports the provider you expect.

---

## Customising

| Want to change | Edit |
|---|---|
| Any resume content, metrics, projects, links | `data/profile.py` |
| The case-study writeup | `CASE_STUDY` in `data/profile.py` |
| How questions map to resume sections | `_SYNONYMS` in `core/rag.py` |
| Assistant tone and guardrails | `SYSTEM_PROMPT` in `core/llm.py` |
| Add a provider | subclass `OpenAICompatible` in `core/providers.py`, add it to `ALL_PROVIDERS` |
| Colours, spacing, type | `:root` in `static/css/style.css` |
| Resume PDF | replace `static/files/…​.pdf`, update `resume_file` in `profile.py` |

---

## Layout

```
portfolio/
├── app.py                 Flask routes, rate limiting
├── core/
│   ├── rag.py             BM25 retrieval over resume chunks
│   ├── providers.py       Pluggable LLM backends
│   └── llm.py             Prompt assembly, provider chain, fallback
├── data/
│   ├── profile.py         ← single source of truth
│   └── knowledge.py       Profile → retrieval chunks
├── templates/index.html
├── static/{css,js,files}
└── Procfile · render.yaml · Dockerfile · vercel.json
```

## API

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | The site |
| `/api/chat` | POST | `{message, history[]}` → `{answer, sources[], live, provider, model}` |
| `/api/health` | GET | Active provider and failover chain |
| `/resume` | GET | Resume PDF |

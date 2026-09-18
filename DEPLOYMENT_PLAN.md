# Deployment Plan — $0/month

Ship the portfolio and its resume assistant to a public URL without entering a card
anywhere. Every service below has a permanent free tier, not a trial.

**Total time:** ~20 minutes. **Total cost:** $0.00/month.

The site is already deployed. **For day-to-day changes, use the runbook directly
below.** Sections 0–10 are the original first-time setup, kept for reference and for
redeploying somewhere new.

---

## Runbook — how this site deploys today

| | |
|---|---|
| Live URL | <https://jeetendra.vercel.app> |
| Host | Vercel, project **`jeetendra`** (Hobby plan, free) |
| Source | <https://github.com/Jeetendra17/ai-resume-assistant>, branch `main` |
| Trigger | **Every push to `main` deploys to production automatically.** Build takes ~15 s. |
| Model providers | Groq first, Gemini as automatic backup, local resume index if both fail |

You do not need the Vercel CLI to deploy. GitHub is connected to the Vercel project,
so pushing is deploying. (Deployments started from the CLI in this folder show up in
the Vercel dashboard under the name "portfolio" — same project, just a different
label taken from the folder name.)

### R1. Ship a content or code change

1. **Edit.** Resume content, projects, metrics and the About write-up all live in
   `data/profile.py`. Interview answers live in `interview/corpus/source/*.md`.
2. **Run the retrieval eval.** It must pass before anything ships.

   ```powershell
   python eval_retrieval.py
   ```

   Expect `recall@3 + out-of-scope: 36/36 (100%)`. It exits non-zero on failure. Run
   it after *content* edits too, not only code edits: in a retrieval system, changing
   the text changes the search results (build log #05 and #12).
3. **If `data/profile.py` changed, regenerate the resume PDF**, so the download and
   the site say the same thing:

   ```powershell
   python build_resume.py
   ```

   It should report `1 page`. If it reports more, cut a bullet in `profile.py` rather
   than shrinking the type.
4. **If the interview corpus changed, rebuild it** and check the page count:

   ```powershell
   python -m interview.corpus.build
   ```
5. **Commit and push to `main`.**

   ```powershell
   git add -A
   git commit -m "Describe the change"
   git push origin main
   ```
6. **Verify the live site** about 30 seconds later (§R4).

### R2. Change an API key, model or provider setting

Settings are **environment variables on the Vercel project**, never in git. The
local `.env` is ignored by both git and the Vercel upload. Two ways to change them:

**A. Vercel dashboard (always works):**
Project `jeetendra` → **Settings → Environment Variables** → edit the value for
**Production** → then **Deployments → latest → ⋯ → Redeploy**.
New values only apply to a *new* deployment, so the redeploy step is required.

**B. From a terminal where the Vercel CLI works** (update `.env` first):

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -EnvOnly
```

This copies the provider settings from `.env` to Vercel without printing any key,
and forces `LLM_TIMEOUT=6` and `FLASK_DEBUG=0`. Drop `-EnvOnly` to also deploy in the
same step; add `-DryRun` to see what it would set without changing anything. Git Bash
users can run `bash deploy.sh --env-only` instead.

> **If `vercel` is "not recognized":** the editor's built-in terminal cannot see the
> npm install folder, even by full path. Use option A, or a normal PowerShell window
> where `& "$env:APPDATA\npm\vercel.cmd" --version` works. Log in once with
> `& "$env:APPDATA\npm\vercel.cmd" login`.

**Current production settings:**

| Variable | Value | Why |
|---|---|---|
| `LLM_PROVIDER` | `groq,gemini` | Groq first (~1 s), Gemini takes over on any Groq failure |
| `GROQ_API_KEY` | Groq key named "portfolio" | primary provider |
| `GEMINI_API_KEY` | Gemini key for the portfolio | backup provider |
| `LLM_TIMEOUT` | `6` | Vercel Hobby kills a function at 10 s; the app must give up and fail over inside that window |
| `FLASK_DEBUG` | `0` | never debug mode in production |
| `GROQ_MODEL` / `GEMINI_MODEL` | *(unset)* | set only to override the defaults in `core/providers.py` |

Default models (in `core/providers.py`): Groq `qwen/qwen3.8-27b`, Gemini
`gemini-3.5-flash-lite` with automatic retry on `gemini-3.1-flash-lite`. Both were
chosen by timing real answers against the 6 s budget, not by version number.

### R3. Where the keys are kept

API keys are stored outside the repository in `D:\personal\keys\`. Never copy them
into the project folder. `.gitignore` and `.vercelignore` both exclude `.env` and
`keys/` as a backstop, but the rule is simply: keys don't go in the repo.

### R4. Verify a deployment

In PowerShell, use `Invoke-RestMethod` rather than `curl`. Windows PowerShell 5.1
strips the quotes out of JSON passed to `curl.exe`, and the site then replies
`message is required`.

**1. Health, with one real model call** (`probe=1` proves the key works rather than
merely exists):

```powershell
(Invoke-RestMethod "https://jeetendra.vercel.app/api/health?probe=1").engine
```

You want `provider : Groq`, `fallbacks : {Google Gemini}`, `reachable : True`,
`probe : ok`.

**2. A real question** — `live` should be `True`:

```powershell
Invoke-RestMethod -Method Post -Uri "https://jeetendra.vercel.app/api/chat" -ContentType "application/json" -Body '{"message":"Is he a fit for an AI Engineer role?"}'
```

A question the resume doesn't cover (for example about personal life) should come back
with `live : False` and a polite decline. That is correct behaviour, not a failure.

From Git Bash, `curl -s "https://jeetendra.vercel.app/api/health?probe=1"` works
as-is.

Finally, open the site in a normal browser and switch between light and dark mode.

### R5. When a model gets retired

Vendors retire models without warning; it has already happened to both providers here.

- **Symptom:** answers come from `"Resume index (no model)"`, and the health probe shows
  `HTTP 404` with "no longer available" or "model not found".
- **Fix, fast:** set `GROQ_MODEL` or `GEMINI_MODEL` on Vercel to a current model (§R2),
  then redeploy.
- **Fix, properly:** update `default_model` in `core/providers.py`, time a real answer
  locally with `LLM_TIMEOUT=6`, then commit and push.
- **Pick by speed, not by version number:** on Vercel's free plan a 9-second answer is a
  timeout, so a newer, larger model can be strictly worse than a lighter one.

### R6. Roll back

- **Vercel dashboard:** Deployments → the last good deployment → ⋯ → **Promote to Production**.
  Instant, no rebuild.
- **Git:** `git revert HEAD` then `git push origin main`. Deploys the previous code.

---

## 0. What "free" actually means here

| Piece | Service | Free tier | Card required? |
|---|---|---|---|
| Hosting | Vercel Hobby **or** Render Free | permanent | No |
| LLM inference | Groq (+ Gemini as backup) | permanent, rate-limited | No |
| Domain | `*.vercel.app` / `*.onrender.com` | permanent | No |
| HTTPS certificate | included, auto-renewed | permanent | No |
| Uptime monitor (optional) | UptimeRobot | 50 monitors | No |
| Source hosting | GitHub public repo | permanent | No |

**The one thing that could ever cost money** is an LLM API key on a paid provider.
This app defaults to free providers and, with no key at all, still answers from the
local resume index. There is no code path that can generate a bill you didn't opt into.

---

## 1. Pre-flight (5 min)

### 1.1 Get a free LLM key

Groq is the primary recommendation: fastest free tier, no card, generous limits.

1. Go to <https://console.groq.com/keys>
2. Sign in with Google/GitHub
3. **Create API Key** → copy it (starts `gsk_...`)

Optionally grab a second for automatic failover — the app chains them:

- Gemini: <https://aistudio.google.com/apikey>
- Cerebras: <https://cloud.cerebras.ai>

### 1.2 Verify locally before shipping

```bash
cd "D:\Sentinel\company\AI Engineering\portfolio"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# PowerShell:  $env:GROQ_API_KEY="gsk_..."
# Git Bash:    export GROQ_API_KEY="gsk_..."
python app.py
```

Open <http://localhost:5000/api/health?probe=1>. The `probe` parameter makes one real
API call — without it you only learn that a key is *present*, not that it *works*.
You want:

```json
{
  "status": "ok",
  "engine": {
    "live": true,
    "reachable": true,
    "probe": "ok",
    "provider": "Groq",
    "model": "qwen/qwen3.8-27b",
    "fallbacks": ["Google Gemini"]
  }
}
```

(`fallbacks` lists any additional providers in the chain — empty if you set only one key.
Model names change as vendors retire them; see runbook §R5.)

If `provider` says `"Resume index (no model)"`, the key isn't being read — fix that now,
not after deploying.

### 1.3 Final content pass

- [ ] `data/profile.py` — everything accurate? It's the single source of truth.
- [ ] Regenerate the resume PDF from it: `python build_resume.py` (must report 1 page).
- [ ] **Run the retrieval eval — it must be 36/36 before you ship:**

  ```bash
  python eval_retrieval.py
  ```

  If you edited `data/profile.py`, this is the check that catches a question
  silently routing to the wrong resume section. It exits non-zero on failure, so
  it also works as a pre-deploy gate.

---

## 2. Push to GitHub

The repo must be its own git root — `portfolio/`, not the parent folder.

```bash
cd "D:\Sentinel\company\AI Engineering\portfolio"
git init
git add .
git commit -m "AI portfolio with resume-grounded assistant"
```

**Confirm no secret is staged** before pushing:

```bash
git ls-files | grep -i "\.env$" && echo "STOP — .env is staged" || echo "clean"
```

`.gitignore` already excludes `.env`, so this should print `clean`.

Then create the repo (either works):

```bash
# GitHub CLI
gh repo create jeetendra-portfolio --public --source=. --push

# or manually: create an empty repo on github.com, then
git remote add origin https://github.com/<you>/jeetendra-portfolio.git
git branch -M main
git push -u origin main
```

> A **public** repo is fine and is itself a hiring signal — recruiters can read the
> retrieval and provider code. No secrets live in it.

---

## 3. Deploy — pick one

### Option A — Vercel *(recommended: no cold-start delay, free custom domain)*

`vercel.json` and `api/index.py` are already configured, including a route that
serves `/static/*` directly from the CDN instead of through the function.

**Via the dashboard (easiest):**

1. <https://vercel.com/new> → sign in with GitHub
2. **Import** your repo
3. Framework preset: **Other** (leave build settings empty — `vercel.json` handles it)
4. Expand **Environment Variables** and add:

   | Name | Value |
   |---|---|
   | `GROQ_API_KEY` | `gsk_...` |
   | `LLM_TIMEOUT` | `6` |
   | `FLASK_DEBUG` | `0` |
   | `SITE_URL` | `https://<your-app>.vercel.app` |

5. **Deploy**

**Via CLI:**

```bash
npm i -g vercel
cd "D:\Sentinel\company\AI Engineering\portfolio"
vercel                      # accept defaults
vercel env add GROQ_API_KEY  production
vercel env add LLM_TIMEOUT   production   # enter: 6
vercel env add FLASK_DEBUG   production   # enter: 0
vercel --prod
```

> ⚠️ **Why `LLM_TIMEOUT=6` matters.** Vercel Hobby caps serverless function
> execution (10s by default). The app's own default timeout is 45s — long enough
> that Vercel would kill the function *before* the app could fail over to the next
> provider, and the visitor would see an error instead of a graceful fallback.
> Setting 6s leaves headroom for the app to give up, try the next provider, or
> return the extractive answer within Vercel's window. Groq typically answers in
> 1–3s, so this rarely triggers.

**Pros:** ~1s cold start, free `*.vercel.app` domain, free custom domain, global CDN.
**Cons:** the function timeout above; Hobby plan is for non-commercial use (a
personal portfolio qualifies).

---

### Option B — Render *(a real always-on server, no timeout limits)*

`render.yaml` is already in the repo.

1. <https://render.com> → sign in with GitHub
2. **New → Web Service** → select your repo
3. Render reads `render.yaml`; confirm:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
   - Instance type: **Free**
4. **Environment → Add Environment Variable** → `GROQ_API_KEY`
5. **Create Web Service**

**The catch and its fix.** Free instances sleep after 15 minutes idle; the next
visitor waits ~50s for a cold boot — bad when that visitor is a recruiter. But the
free tier grants **750 instance-hours/month** and a month is ~730 hours, so one
service can stay awake continuously within the allowance. Keep it warm:

1. <https://uptimerobot.com> → free account
2. **Add New Monitor** → HTTP(s)
3. URL: `https://<your-app>.onrender.com/api/health`, interval **10 minutes**

**Pros:** real gunicorn server, no request-duration limit, simplest mental model.
**Cons:** needs the keep-alive trick; single region.

---

### Option C — Hugging Face Spaces *(thematically apt for an AI portfolio)*

`Dockerfile` is already set up for port 7860.

1. <https://huggingface.co/new-space> → SDK: **Docker** → **Blank** → Public
2. Push the code to the Space's git remote
3. **Settings → Variables and secrets → New secret**: `GROQ_API_KEY`

**Pros:** free, no card, credible venue for AI work.
**Cons:** URL is `huggingface.co/spaces/<you>/<name>`; sleeps after ~48h idle.

---

## 4. Verify the deployment

Run these against the live URL, not localhost:

```bash
URL=https://your-app.vercel.app

curl -s "$URL/api/health?probe=1"    # proves the key works, not just that it exists
curl -s -o /dev/null -w "home:   %{http_code}\n" $URL/
curl -s -o /dev/null -w "resume: %{http_code}\n" $URL/resume
curl -s -o /dev/null -w "css:    %{http_code}\n" $URL/static/css/style.css
curl -s -X POST $URL/api/chat -H "Content-Type: application/json" \
     -d '{"message":"Is he a fit for an AI Engineer role?"}'
```

Checklist:

- [ ] `/api/health?probe=1` reports `"reachable": true` and `"probe": "ok"`
- [ ] All four routes return `200`
- [ ] Chat returns a real answer with a `sources` array
- [ ] Open the site on a phone — sidebar collapses to the hamburger
- [ ] Profile photo and resume PDF load
- [ ] Click through all 7 nav sections

**If `"live": false`:** the key isn't reaching the app. Check the variable name is
exactly `GROQ_API_KEY`, that it's set for the **Production** environment, and
**redeploy** — most platforms don't apply new env vars to an existing build.

---

## 5. Custom domain (optional, free to connect)

The platform subdomain is free forever and perfectly respectable. If you already own
a domain, connecting it costs nothing:

- **Vercel:** Project → Settings → Domains → add → set the DNS records shown
- **Render:** Settings → Custom Domain → add → set the CNAME

HTTPS is provisioned automatically on both. Buying a domain (~₹800/yr) is the only
paid step in this entire document, and it is optional.

After connecting, update `SITE_URL` to the new domain.

---

## 6. Keeping it free — guardrails

The app already ships with these; this is what they're for.

| Risk | Already mitigated by |
|---|---|
| A script drains your free LLM quota | `CHAT_RATE_LIMIT=20`/min per IP in `app.py` |
| One provider rate-limits and the site breaks | Provider chain fails over automatically |
| Every provider is down | Extractive fallback from the local index |
| Runaway token spend | `ASSISTANT_MAX_TOKENS=800` cap per reply |
| Accidental paid usage | No paid provider key is set unless you add one |

**Never add billing details to an LLM provider** unless you deliberately want paid
capacity. Free tiers hard-stop; they don't silently overage.

Tighten the rate limit if the link gets wide exposure:

```
CHAT_RATE_LIMIT=10
```

---

## 7. Updating the site after launch

Follow **runbook §R1** at the top of this document: edit, run the eval, regenerate
the resume if `profile.py` changed, push to `main`. Vercel and Render both
auto-deploy on push.

The chunk count and eval score shown in the About section are **computed at
startup** from the running index (`_measured_about()` in `app.py`), so they can't
go stale when you edit `data/profile.py`. Everything else in that section is
hand-written prose — keep it honest if you change how the system works.

> ⚠️ Adding prose that *describes* a failure can reintroduce it. Writing the word
> "hobbies" into the write-up about the hobbies bug made that question match again,
> and the eval caught it. Prefer generic wording in indexed text.

---

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `"provider": "Resume index (no model)"` | key missing or not applied | Check exact var name, set for Production, redeploy |
| Health looks live but answers come from the index | provider rejecting calls | `curl "$URL/api/health?probe=1"` — the `probe` field carries the real error |
| `HTTP 403: error code: 1010` | CDN blocked the user-agent | Already fixed; ensure `USER_AGENT` in `core/providers.py` is still sent |
| Chat returns the fallback wording | every provider failed | Check quota; add a second provider key |
| Vercel: `FUNCTION_INVOCATION_TIMEOUT` | LLM call exceeded the window | Set `LLM_TIMEOUT=6` |
| First Render visit takes ~50s | free instance slept | Add the UptimeRobot monitor (§3B) |
| CSS missing / page unstyled | static route not matching | Confirm `vercel.json` `routes` order — `/static/(.*)` must come first |
| `500` on `/` | template or data error | Vercel: Deployments → Runtime Logs. Render: Logs tab |
| `/resume` returns 404 | PDF not committed | `git add -f static/files/*.pdf` |
| Photo missing | image not committed | `git ls-files static/img/` |
| Build fails on `anthropic` | optional dep uncommented | Leave it commented unless using Claude |
| Probe shows `HTTP 404` "no longer available" | the vendor retired the model | Runbook §R5: set `GROQ_MODEL` / `GEMINI_MODEL`, or update `core/providers.py` |
| Probe shows `HTTP 401` "Invalid API Key" | key deleted or mistyped | Create a new key, update it on Vercel (§R2), redeploy |
| Intermittent `HTTP 503` "high demand" | provider over capacity | Keep two providers in `LLM_PROVIDER`; Gemini already retries on a second model |
| Probe passes but real answers fall back | answer slower than `LLM_TIMEOUT` | Time a real answer; switch to a faster model (a short "ok" probe hides this) |
| `vercel` is not recognized | editor terminal can't see npm folder | Deploy by `git push`; change settings in the dashboard (§R2) |
| `deploy.ps1` stops on Vercel's own progress text | Windows PowerShell 5.1 + `Stop` preference | Fixed in the script; judge success by exit code, not stderr |

---

## 9. Rollback

- **Vercel:** Deployments → pick the last good one → **Promote to Production**
- **Render:** Events → **Rollback** to a previous deploy
- **Any:** `git revert HEAD && git push`

---

## 10. After it's live

- [ ] Add the URL to your LinkedIn headline and résumé header
- [x] Resume PDF is generated from `profile.py` and already links to the live site
- [ ] Ask a friend to try to break the assistant, then tune `_SYNONYMS` in `core/rag.py`
- [ ] Pin the GitHub repo on your profile

**Recommended stack for a recruiter-facing link:** Vercel + Groq + a free
`*.vercel.app` domain. No sleep, ~1s loads, $0/month, no card anywhere.

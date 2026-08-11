# Deployment Plan — $0/month

Ship the portfolio and its resume assistant to a public URL without entering a card
anywhere. Every service below has a permanent free tier, not a trial.

**Total time:** ~20 minutes. **Total cost:** $0.00/month.

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

Open <http://localhost:5000/api/health>. You want:

```json
{
  "status": "ok",
  "engine": {
    "live": true,
    "provider": "Groq",
    "model": "llama-3.3-70b-versatile",
    "fallbacks": []
  }
}
```

(`fallbacks` lists any additional providers in the chain — empty if you set only one key.)

If `provider` says `"Local resume index"`, the key isn't being read — fix that now,
not after deploying.

### 1.3 Final content pass

- [ ] `data/profile.py` — everything accurate? It's the single source of truth.
- [ ] `static/files/…Resume.pdf` — current version?
- [ ] Add your GitHub URL to `PROFILE["github"]` (currently empty).
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

curl -s $URL/api/health
curl -s -o /dev/null -w "home:   %{http_code}\n" $URL/
curl -s -o /dev/null -w "resume: %{http_code}\n" $URL/resume
curl -s -o /dev/null -w "css:    %{http_code}\n" $URL/static/css/style.css
curl -s -X POST $URL/api/chat -H "Content-Type: application/json" \
     -d '{"message":"Is he a fit for an AI Engineer role?"}'
```

Checklist:

- [ ] `/api/health` reports `"live": true` and your provider name
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

```bash
# edit data/profile.py — it drives pages, retrieval and the system prompt
git add .
git commit -m "Update experience"
git push
```

Vercel and Render both auto-deploy on push to `main`.

**Before every push, one check:**

```bash
python eval_retrieval.py    # must be 36/36; exits non-zero on failure
```

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
| `"provider": "Local resume index"` | key missing or not applied | Check exact var name, set for Production, redeploy |
| Chat returns the fallback wording | every provider failed | Check quota; add a second provider key |
| Vercel: `FUNCTION_INVOCATION_TIMEOUT` | LLM call exceeded the window | Set `LLM_TIMEOUT=6` |
| First Render visit takes ~50s | free instance slept | Add the UptimeRobot monitor (§3B) |
| CSS missing / page unstyled | static route not matching | Confirm `vercel.json` `routes` order — `/static/(.*)` must come first |
| `500` on `/` | template or data error | Vercel: Deployments → Runtime Logs. Render: Logs tab |
| `/resume` returns 404 | PDF not committed | `git add -f static/files/*.pdf` |
| Photo missing | image not committed | `git ls-files static/img/` |
| Build fails on `anthropic` | optional dep uncommented | Leave it commented unless using Claude |

---

## 9. Rollback

- **Vercel:** Deployments → pick the last good one → **Promote to Production**
- **Render:** Events → **Rollback** to a previous deploy
- **Any:** `git revert HEAD && git push`

---

## 10. After it's live

- [ ] Add the URL to your LinkedIn headline and résumé header
- [ ] Regenerate the resume PDF so it links to the live site
- [ ] Ask a friend to try to break the assistant, then tune `_SYNONYMS` in `core/rag.py`
- [ ] Pin the GitHub repo on your profile

**Recommended stack for a recruiter-facing link:** Vercel + Groq + a free
`*.vercel.app` domain. No sleep, ~1s loads, $0/month, no card anywhere.

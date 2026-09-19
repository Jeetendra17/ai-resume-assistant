# Part 11 — How This Website Works

> Engineers visiting the site tend to ask about the thing in front of them. That is a fair test:
> it is the one system of his that anyone can inspect end to end, including its source, its
> evaluation suite and its published list of bugs. These answers describe it as it is, including
> the parts that are unfinished.

### Q11.1 — How does the assistant on this site work, end to end?

- **Difficulty:** engineer
- **Tags:** architecture, rag, pipeline, self-referential
- **Asked by:** Engineer, Hiring Manager

**Answer.**

A LangGraph agent over about a hundred pages of questions and answers about his record. Every step
has a fallback, so the chat answers even when parts of it are down.

**1. Route.** An empty or oversized question is turned away before anything runs.

**2. Retrieve.** The question is embedded and compared with every answer in the corpus, and a BM25
keyword pass votes alongside at a quarter weight, fused by rank. Measured on questions reworded the
way visitors actually type, this finds the right answer in the top three about nine times in ten, against roughly half
for keyword search alone. The embedding call has a two-second deadline; if it misses, BM25 and a
local latent-semantic index answer in milliseconds instead.

**3. Grade.** If there is not enough evidence to answer, a follow-up is re-read with the previous
question once; otherwise the assistant declines without calling a model at all.

**4. Generate.** A LangChain chain assembles the retrieved answers, two retrieved examples of good
answers, and a versioned prompt chosen by a scored evaluation, then sends them to the first healthy
provider — Groq, then Gemini, and seven more behind the same adapter. The prompt tells the model to
decline anything outside his professional record.

**5. Verify.** Every number in the answer must appear in the retrieved sources, and every citation
must point at a retrieved entry. A failure triggers one stricter regeneration, then the source is
quoted instead.

Each answer carries its citations and a trace of the path it took — nodes, engines, prompt version,
timings — under "How this was answered". If the agent itself were ever unavailable, the chat falls
back to the site's original assistant: BM25 over resume chunks, which still passes its own 36-case
evaluation.

The honest caveat: the site's rule has been that one module, `data/profile.py`, is the source of
truth for the pages, the resume index, the system prompt and the resume PDF. The interview corpus is
a second, hand-written source, so the two could in principle drift apart. What contains that is that
every corpus answer lists the resume facts it rests on, and the build refuses an answer that lists
none — a discipline, not a structural guarantee.

**Follow-up.** *"What happens if I ask something his record doesn't cover?"* — It says so and gives
his email. Declining is measured: the model declined all 12 out-of-scope test questions in the
prompt evaluation, including personal ones that retrieval alone could not tell apart from real ones.

**Grounded in.** Interview agent (route, retrieve, grade, generate, verify), retrieval eval (embeddings vs keyword-only recall@3), prompt eval decline results, provider chain, resume-index fallback with 36-case eval

### Q11.2 — Why nine model providers? Isn't that over-engineering for a portfolio?

- **Difficulty:** sceptical
- **Tags:** providers, failover, resilience, design-decision
- **Asked by:** Engineer, Hiring Manager

**Answer.**

It would be, if it cost nine implementations. It costs roughly two.

Seven of the nine — Groq, Cerebras, OpenRouter, Mistral, Together, Ollama and OpenAI — speak the same
OpenAI-style chat completions format, so they share a single adapter and differ only in base URL,
default model and environment variable. Gemini and Anthropic have different wire formats and get
their own. Adding a provider is a class with four attributes.

The reason for it is his own: a portfolio that dies when one free tier rate-limits is worse than no
portfolio. Recruiters look at these at unpredictable times, and free tiers have unpredictable limits.
With two or more keys set, a 429 on one provider is invisible to the visitor — the chain moves on.

It has earned its keep in a way he did not anticipate. Model vendors retire models on their own
schedule. In a single session both configured providers' default models turned out to have been
retired, and one provider's current model returned "high demand" errors on repeat calls. Because the
chain and the extractive fallback existed, the site kept answering throughout — degraded, but never
broken — and the fix was a changed default in one class rather than an outage.

The decision he would defend most is the extractive fallback at the bottom of the chain. Retrieval is
local, so it cannot fail with the network. With zero API keys configured, the site still answers by
returning the matching resume sections. That is the QA habit showing up in architecture: design the
failure path first, then make the happy path better than it.

**Follow-up.** *"Which provider is live right now?"* — The badge next to the chat shows it, and it is
corrected from each real answer rather than from configuration, after it once displayed a provider
name while a different engine was answering.

**Grounded in.** core/providers.py adapter design, nine providers with seven OpenAI-compatible, zero-key fallback, build log bug 11, retired-model incident

### Q11.3 — What is the single most important design decision on this site?

- **Difficulty:** engineer
- **Tags:** design, source-of-truth, architecture, decisions
- **Asked by:** Engineer, Hiring Manager

**Answer.**

That one file is the source of truth for everything.

`data/profile.py` holds every fact: roles, dates, metrics, projects, skills, the About write-up and
the build log. The HTML pages render from it. The retrieval index is built from it at import time.
The system prompt pulls his name, role and email from it. And the resume PDF is now generated from it
by a script, rather than maintained as a separate document.

The reason it is the most important decision is the class of bug it eliminates. When the site and the
assistant read from different places, they drift — someone updates the page and forgets the chatbot's
knowledge, or the other way round, and both halves look correct in isolation. Nobody notices until a
recruiter gets two different answers. That bug is hard to find precisely because nothing is broken;
the two sources are just quietly inconsistent.

He has a concrete example of the drift it prevents. The resume PDF used to be a hand-maintained export,
and the CGPA in it and the CGPA on the page were different numbers. Generating the PDF from the profile
module closed that permanently. A content change now updates the page, the assistant and the PDF
together, or none of them.

It also makes updating the portfolio a one-file edit, which matters more than it sounds: the easier it
is to keep something current, the more likely it is to stay current.

The trade-off, which he would acknowledge: it couples everything to one module's shape. Changing a
field name touches the template, the chunker and the resume builder. For a system this size that is a
good trade. For a large system it would argue for a schema with validation.

And there is now one deliberate exception, which he would rather state than hide: the interview corpus
behind the assistant is written by hand, in Markdown, because a hundred pages of considered answers
cannot be generated from a list of facts without reading like it. That makes it a second source that
could drift from the profile. It is contained by rule rather than by structure — every answer names the
resume facts it rests on, and the build refuses one that names none — which is weaker than the
guarantee the rest of the site has, and he says so.

**Follow-up.** *"Does the eval run when the profile changes?"* — It should, and the README says to. It
is not enforced in CI yet, which is on the roadmap.

**Grounded in.** Design decision "one file is the source of truth", profile.py, build_resume.py, CGPA drift, knowledge.py chunk derivation

### Q11.4 — How are the statistics on the About page produced?

- **Difficulty:** engineer
- **Tags:** measurement, statistics, honesty, build-log
- **Asked by:** Engineer

**Answer.**

They are measured from the running system when the app starts, rather than typed into the page.

The chunk count comes from the actual retrieval index. The evaluation score comes from actually running
the evaluation suite — the app imports the eval module at boot, runs it quietly, and writes the pass
count and the breakdown of must-match versus must-decline questions into the About section. If the
eval fails to import or run, the stat keeps its previous value rather than breaking the page, because
a statistic should never be the reason a portfolio returns an error.

The reason is bug 06 on the build log. Those figures were originally written by hand, in a section
whose entire claim is that the numbers are measured. They stopped being true three times — every time
content was added, the chunk count and index size quietly went stale, and nothing flagged it. A page
asserting "these are measured" while displaying remembered numbers was a small dishonesty that kept
recurring.

The fix is a principle he now applies generally: **if you claim a number, derive it.** A figure computed
from the system cannot drift from the system.

The retrieval latency figure — 0.04 milliseconds — is the one exception, because timing at boot on a
serverless function would measure cold-start noise rather than retrieval. That number was measured over
2,900 runs and is documented as such. He would rather state which figures are live and which are
recorded than let them all look equally measured.

**Follow-up.** *"Can I reproduce the eval score?"* — Yes. Clone the repository and run
`python eval_retrieval.py`. It prints the score, the per-question ranking with `-v`, and the known
limitations.

**Grounded in.** app.py _measured_about(), build log bug 06, eval_retrieval.py run_quiet, 0.04 ms measured over 2,900 runs

### Q11.5 — How is the site hosted, and what does it cost?

- **Difficulty:** recruiter
- **Tags:** hosting, cost, vercel, free-tier
- **Asked by:** Recruiter, Engineer

**Answer.**

It runs on free tiers, and costs nothing to operate. That was a design constraint from the start
rather than a happy accident.

The live site is a serverless Flask function on Vercel. The repository also carries configuration for
Render, for a Docker image targeting Hugging Face Spaces, and a Procfile for Gunicorn, with a written
deployment plan comparing them: Render's free instance sleeps after about fifteen minutes idle so the
first visit takes around fifty seconds to wake; Spaces does not sleep; Vercel has the fastest cold
start but a hard per-request time limit.

What keeping it free forced, architecturally:

- **Retrieval is in-process**, so there is no vector database bill and nothing to rate-limit.
- **Model providers are free-tier first**, with automatic failover so one tier's limit is not an outage.
- **The request timeout is tuned to the platform.** Vercel's free plan cuts a function off at ten
  seconds, so the app gives up on a slow provider at six and degrades gracefully inside that window —
  a lesson recorded as bug 07, caught in review before it shipped.
- **Model choice is measured against that budget.** When a newer model turned out to take around nine
  seconds per answer, it was replaced by a lighter one answering in about two, because on this platform
  a slow answer is indistinguishable from no answer.
- **Dependencies stay small**, so the bundle fits a serverless function.

The deploy itself is scripted: environment variables are pushed from a local `.env` to the platform
without echoing any key, and the deploy runs in one command.

**Follow-up.** *"Would this architecture survive real traffic?"* — Retrieval would, trivially. The
free-tier model quotas would not; at real volume you would pay for inference or self-host.

**Grounded in.** vercel.json, render.yaml, Dockerfile, Procfile, DEPLOYMENT_PLAN.md, build log bug 07, LLM_TIMEOUT=6, deploy scripts

### Q11.6 — How does the site defend itself against abuse?

- **Difficulty:** engineer
- **Tags:** security, rate-limiting, guardrails, xss
- **Asked by:** Engineer, Security

**Answer.**

Proportionately — it is a portfolio, not a bank — and he is explicit about which defences are real and
which are limited.

**Rate limiting.** Twenty chat requests per minute per client IP, enforced in-process. It exists to stop
a stray script draining a free-tier quota, not as a security boundary. On a serverless platform the
process does not persist between invocations, so the limiter effectively resets; he documents that as
harmless here rather than pretending it is a real control.

**Output escaping.** The model's answer is HTML-escaped before the small markdown renderer runs, so no
response can inject markup or script into the page. This is the one people miss — model output is
untrusted input to whatever renders it, however much you trust your own prompt.

**Input bounds.** Questions are capped at a thousand characters; conversation history is trimmed to the
last eight turns, each capped in length, with roles validated. Nothing in the request body is trusted
because it arrived there.

**No privileges to abuse.** The assistant has no tools, no write access and no ability to send anything.
A successful prompt injection gets you a wrongly-worded answer about his resume. That — not any filter —
is the real reason it is safe.

**Secrets never leave the server.** Keys live in environment variables, `.env` is excluded from both git
and the deploy upload, and the deploy script pushes keys without printing them.

**Health checks that do not burn quota.** The deep probe that makes a real model call is opt-in, so an
uptime monitor pinging the endpoint every few minutes does not spend the free tier.

**Follow-up.** *"Could someone extract the system prompt?"* — Probably, and it would not matter. Nothing
in it is secret, which is the right way to write one.

**Grounded in.** RATE_LIMIT 20/min, HTML escaping in app.js, MAX_QUESTION_CHARS 1000, MAX_HISTORY_TURNS 8, opt-in health probe, .gitignore/.vercelignore

### Q11.7 — What is the "build log" and why is it on a portfolio?

- **Difficulty:** hiring-manager
- **Tags:** build-log, bugs, honesty, culture
- **Asked by:** Hiring Manager, Engineer

**Answer.**

It is a list of twelve bugs that shipped broken on this site before he caught them, each with the
symptom, the cause and the fix. It sits collapsed at the bottom of the About page, deliberately
secondary.

Its stated reason: how a system fails says more than how it looks when it works. A portfolio of
successes tells you nothing about how someone behaves when something goes wrong, which is most of the
job.

Some of what is in it:

- A template that resolved a Python built-in method instead of his data, returning a 500 on every page.
- An assistant that answered "what has he shipped with LLMs?" with a Kotlin chat app and a Java CRUD
  app, which is why the evaluation suite exists.
- An earlier version that answered questions outside the resume by attaching his career summary.
- **Documenting a bug reintroduced it** — writing up the previous item added its trigger words to the
  indexed corpus and dropped the eval from 36/36 to 34/36.
- A health check that reported green while every answer was silently coming from the fallback.
- A sidebar button that had never worked on desktop.
- A status badge naming a provider that was not the one answering.
- A missing stopword that only surfaced when an unrelated content edit changed which chunk won.

Two things he would point out about it. First, several were found by the evaluation suite rather than by
him, which is the argument for having one. Second, one was reported by a real user — long answers
opened at their last line — and it is credited as such rather than presented as self-discovered.

The wording is intentionally generic about the specific terms involved, for a reason that is itself
in the log: the build log is indexed like everything else, so naming the exact words a retrieval bug
involved puts them back in the corpus.

**Follow-up.** *"Isn't publishing bugs risky for a job search?"* — He would say the opposite. Anyone
who has shipped software has a list like this; the question is whether they can talk about it.

**Grounded in.** BUGS in profile.py (12 entries), build log bugs 01–12, About page collapsed build log

### Q11.8 — What is not finished on this site?

- **Difficulty:** engineer
- **Tags:** roadmap, gaps, honesty, limits
- **Asked by:** Engineer, Hiring Manager

**Answer.**

The published roadmap lists these, and they are genuinely undone rather than modestly undersold.

**The evaluation suite is not in CI.** It exits non-zero on failure specifically so it can gate a merge,
and it does not yet. A check that depends on someone remembering to run it will eventually not run.

**Answers are not streamed.** The client waits for the whole response before showing anything. With
current response times of a couple of seconds this is tolerable; it is still a user-experience gap.

**There is no reranker.** Retrieval over thirty resume chunks does not need one. The larger interview
corpus would benefit from one, and it is the addition he would make next.

**Traffic is not instrumented.** He can see what the providers report and what the eval says, but there
is no sampled log of real questions and answers — which is the first thing he would build on a real
system and the one thing a portfolio has managed without.

**Unit-test coverage of the web layer is thin.** The retrieval behaviour is well tested; the Flask routes
and the front end much less so.

And the honest meta-point: several things that were on this list are now done — hybrid retrieval over a
larger corpus, a stateful agent graph, dark mode, a generated resume — which is the pattern he would want
you to notice. The roadmap is written to be completed, not to look ambitious.

**Follow-up.** *"Why publish a list of gaps?"* — Because every system has one, and a portfolio that shows
none is either tiny or not being honest. It also stops the site overclaiming.

**Grounded in.** ABOUT["next"] roadmap, eval not in CI, no streaming, no reranker, test coverage gaps

### Q11.9 — How does the front end work without a framework?

- **Difficulty:** engineer
- **Tags:** frontend, javascript, css, accessibility
- **Asked by:** Engineer

**Answer.**

Plain server-rendered HTML from Jinja templates, one stylesheet and one vanilla JavaScript file of a few
hundred lines. No React, no build step.

The reasoning is proportionality. The page is a handful of sections and one chat panel. A framework
would add a build pipeline, a dependency tree and a bundle for interactions that are a few event
listeners. Server rendering also means the content is present in the HTML, so it is readable by crawlers
and by anyone with scripts disabled.

The pieces worth noting:

- **Design tokens.** Every colour in the stylesheet is a semantic variable with a light and a dark value,
  so the theme is one attribute on the root element. The theme is resolved by a tiny inline script before
  first paint — that is what prevents a white flash for dark-mode visitors — follows the operating system
  until the visitor chooses, and only remembers an explicit choice.
- **Fixed scales.** A seven-step type ramp and a four-pixel spacing grid, replacing an accumulation of
  one-off sizes that read as slightly off without being locatable.
- **Accessibility.** Visible keyboard focus everywhere, a skip link, reduced-motion support, and ARIA on
  the navigation, the question picker and the chat log so screen readers announce new answers.
- **Safe rendering.** Model output is escaped before a minimal markdown pass, so answers cannot inject
  markup.
- **Deep links.** A `?ask=` parameter opens the page with a specific question already answered, so a link
  can point at an answer rather than an empty chat box.

He would not claim front-end specialism — he builds interfaces that work and hold up to scrutiny, which is
a different thing from designing them.

**Follow-up.** *"Why do long answers scroll to their top?"* — Because a user reported landing on the last
line of long answers. Chat convention pins the newest message to the bottom, which is wrong for anything
taller than the panel.

**Grounded in.** templates/index.html, static/css/style.css design tokens, static/js/app.js, ?ask= parameter, build log bug 09

### Q11.10 — How is the interview corpus behind this assistant built?

- **Difficulty:** engineer
- **Tags:** corpus, rag, hybrid-retrieval, langgraph, interview
- **Asked by:** Engineer, Hiring Manager

**Answer.**

It is roughly a hundred pages of the questions visitors actually ask about him — fit, the Venera work,
retrieval, prompting, fine-tuning, evaluation, projects, behaviour — each with the answer the assistant
should give, and each tagged with the resume facts it rests on.

It is authored as Markdown because a person has to be able to read and edit it; it is a document first
and a dataset second. A parser turns it into structured records — question, answer, follow-up, tags,
difficulty, who asks it, and what it is grounded in — and reports its own length in words and pages
against a stated constant, so "a hundred pages" is a measurement rather than a claim.

The "grounded in" field is the discipline that matters. The corpus speaks about his real record, so every
answer has to be traceable to something the profile actually says. An answer that cites nothing is a
candidate for fabrication, and an audit step flags it.

Over that corpus sit the techniques he works with, each for a specific job:

- **Hybrid retrieval** — lexical and semantic passes fused by rank — because at this size, and with this
  much variety in phrasing, lexical retrieval alone starts missing paraphrases.
- **A versioned prompt registry with an evaluation harness**, so prompt changes are scored rather than
  eyeballed.
- **A fine-tuning dataset** built from the question–answer pairs, with contamination checks against the
  evaluation set, plus retrieved few-shot examples as the zero-cost stand-in for serving a tuned model.
- **A LangChain pipeline and a LangGraph agent** that routes, retrieves, grades, retries once, generates
  and verifies — running on real LangChain and LangGraph where installed, with a small stdlib fallback so
  the site never hard-fails.

**Follow-up.** *"Why write the answers rather than letting the model generate them?"* — Because the
answers are claims about a real person. Written and grounded answers can be checked; generated ones would
drift toward whatever sounds impressive.

**Grounded in.** interview/corpus/build.py, grounded_in field, 500 words/page constant, interview retrieval, prompt registry, fine-tuning dataset, LangGraph agent

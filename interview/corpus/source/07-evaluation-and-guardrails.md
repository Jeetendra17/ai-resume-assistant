# Part 7 — Evaluation, Guardrails and Honesty About Failure

> If there is one thread that runs through everything he has built, it is this one. Three systems,
> three evaluation sets, and a published log of twelve bugs that shipped broken before he caught
> them. These questions get at whether the discipline is real or decorative — and the test is
> always whether he can say what an eval *caught*, not whether he has one.

### Q7.1 — Why does he build an evaluation set for everything?

- **Difficulty:** engineer
- **Tags:** evaluation, methodology, measurement, discipline
- **Asked by:** Engineer, Hiring Manager

**Answer.**

Because with a generative system you genuinely cannot tell whether a change helped by looking at
the output, and he has been wrong about this in a way he can point to.

The mechanics of the problem: output variance between runs is wide enough that sampling three
responses confirms whatever you already believed. Changes to retrieval and prompts have non-local
effects, so improving one class of question routinely degrades another, and nothing tells you unless
both are in the set. And the failures that matter are quiet — a confident wrong answer looks exactly
like a confident right one.

The case that made it concrete: someone asked his assistant "what has he actually shipped with
LLMs?" and it returned a Kotlin chat app and a Java CRUD app. He wrote an eval set of 29 questions
with expected source chunks, reproduced the failure at 26/29, fixed the scoring until it reached
29/29, and then had a number that could detect the problem coming back.

It has since caught things he had no way to anticipate. Writing up a bug in the site's own build log
added text to the indexed corpus that reintroduced the matching behaviour the bug was about, dropping
the score from 36/36 to 34/36 — documenting a bug caused it to recur. More recently, editing his
experience section broke a retrieval case that had passed for months, because a question word was
missing from the stopword list and the content change was what exposed it. Neither was findable by
reading code.

The rule he works to now: **add the failing case to the eval before fixing it.** That way the fix is
provably a fix, and it cannot silently come back.

**Follow-up.** *"Does an eval set guarantee quality?"* — No. It measures the cases you thought of.
The failures that hurt most are the ones nobody put in the set, which is why it grows every time
something real goes wrong.

**Grounded in.** eval_retrieval.py 36/36, build log bugs 02, 05 and 12, Pulsar evaluation set, NLP prompt-evaluation loop

### Q7.2 — What is the must-decline half of an eval set, and why does he insist on it?

- **Difficulty:** engineer
- **Tags:** refusal, evaluation, out-of-scope, grounding
- **Asked by:** Engineer, Hiring Manager

**Answer.**

It is the set of questions the system is required to *not* answer, and he treats it as the more
important half.

On this site it is 7 of the 36 cases: questions his resume genuinely does not cover, asserted to
retrieve nothing so the system declines. On the Pulsar chatbot at Venera it is the requests the
system must refuse rather than generate a template for.

The argument for it: an eval made only of success cases rewards a system that always produces
something. That is precisely the behaviour that makes a grounded system untrustworthy, because the
failure is invisible — a plausible answer to a question you had no basis for answering looks
identical to a good answer.

He added it after being caught. An early version of the assistant substituted default chunks
whenever retrieval scored nothing, so there was always material to answer from. A question about his
hobbies came back with his career summary attached, reading as though it had addressed the question.
The fix was to let retrieval return empty and decline deterministically before any model call — and
then to put seven must-decline cases in the eval so the behaviour could not regress quietly.

The same logic applies at Venera with higher stakes: a confident QC template generated for an
ambiguous request is worse than a refusal, because the operator gets no signal that the system
guessed, and they run quality control with checks they did not ask for.

What he would say generalises: **the refusal set should be written first.** It is always the half
that gets deprioritised, and it is the half that determines whether the system is trustworthy.

**Follow-up.** *"Can I test it right now?"* — Yes. Ask this assistant something his resume does not
cover. It should decline and give you his email rather than improvising.

**Grounded in.** 7 must-decline cases in eval_retrieval.py, build log bug 04, Pulsar refusal cases, OUT_OF_SCOPE handling

### Q7.3 — Tell me about a bug he shipped.

- **Difficulty:** behavioural
- **Tags:** bugs, honesty, debugging, build-log
- **Asked by:** Hiring Manager, Engineer

**Answer.**

He publishes twelve of them on this site, deliberately, under a build log that says how a system
fails matters more than how it looks when it works. A few that show different things:

**The one where the health check lied (bug 08).** With a valid API key configured, the site reported
the engine live while every answer was actually coming from the local extractive fallback. Two
faults stacked: the HTTP layer sent Python's default user-agent, which the CDN in front of the
provider rejects outright, and the health check only asked whether a key was *present*, never
whether the provider would answer. The graceful fallback was hiding a total failure. He fixed both —
a real user-agent, and splitting health into a cheap "configured" check and an opt-in probe that
makes one live call. He only found it because answers report which engine produced them.

**The one where documenting a bug reintroduced it (bug 05).** Writing up an earlier bug in the build
log added that text to the indexed corpus, which put the matching behaviour back and dropped the eval
from 36/36 to 34/36. The write-up is now deliberately generic about the terms involved.

**The one a user found (bug 09).** Long answers opened scrolled to their last line, so you landed on
the closing sentence and had to scroll back up. Standard chat behaviour is to pin the newest message
to the bottom, which is right for short turns and wrong for anything taller than the panel. Reported
by a user, not caught in testing.

**The one that had never worked (bug 10).** The sidebar close button did nothing on desktop. Below
the breakpoint the sidebar is an overlay driven by a state class; above it, it is part of the layout,
so the same class is inert. One handler had been written for both.

**Follow-up.** *"Why publish these?"* — Because a portfolio of things that worked says nothing about
how someone handles things that do not. It is also a hedge against overclaiming.

**Grounded in.** Build log bugs 05, 08, 09 and 10, engine status reporting, eval regression

### Q7.4 — How does he think about guardrails?

- **Difficulty:** engineer
- **Tags:** guardrails, safety, grounding, architecture
- **Asked by:** Engineer, Hiring Manager

**Answer.**

As properties enforced in code, not behaviours requested in a prompt. The distinction is the whole
of his position.

A prompt saying "only produce valid output" is a preference the model will usually honour. A
validator is a guarantee. Anything that must be true has to be checked outside the model.

The guardrails on this site, which he documents publicly:

- **Answers are constrained to retrieved context**, and the prompt explicitly forbids inventing
  employers, dates, titles or numbers — the categories a model fabricates most fluently.
- **Unknown questions return a refusal plus his email**, decided by retrieval returning empty rather
  than by the model choosing to decline.
- **The prompt instructs honesty about his level** rather than overselling, which is a guardrail
  against the system being more flattering than the truth.
- **Model output is HTML-escaped before markdown rendering**, so a response cannot inject markup.
  This is the one people forget: model output is untrusted input to whatever consumes it.
- **Per-IP rate limiting**, so a stray script cannot drain a free tier.

On the Pulsar chatbot the equivalent hard gate is schema validation — a generated template that does
not validate does not reach the product, regardless of what the model produced.

The layering he would describe: retrieval decides what is available to say, the prompt shapes how it
is said, and validation decides what is allowed out. Each layer catches a different failure, and the
last one is the only one that is a guarantee.

What he is careful not to claim: that guardrails make a system safe against an adversary. Neither
system he has built has meaningful privileges — no tools, no side effects, no write access — and
that is the real reason they are safe rather than any filter he wrote.

**Follow-up.** *"What is the most commonly missed guardrail?"* — Escaping model output before
rendering it. People treat the model as trusted because they wrote the prompt.

**Grounded in.** Guardrails list in About section, HTML escaping, rate limiting, Pulsar schema validation, no-tool architecture

### Q7.5 — What metrics does he use to evaluate a RAG system?

- **Difficulty:** engineer
- **Tags:** metrics, evaluation, recall, groundedness
- **Asked by:** Engineer

**Answer.**

He separates the two halves, because conflating them is why teams cannot tell what is broken.

**For retrieval**, measured independently of generation: recall@k as the primary — did the passage
that supports the answer make the cut at all — plus rank position, because the lost-in-the-middle
effect means a hit at position nine is often a practical miss. Mean reciprocal rank and nDCG where
the ordering matters more finely. And the refusal rate on out-of-scope queries, which is the
must-decline half.

Measuring retrieval on its own is the step people skip, and it is the one that makes debugging
tractable. If retrieval recall is 60%, no prompt work will fix the system, and you will waste weeks
finding that out.

**For generation**, given correct retrieval:

- **Groundedness** — is every claim supported by a retrieved passage. This is the one that matters
  most for a system whose selling point is not making things up. On the document Q&A project he
  tracked unsupported answers as an explicit metric rather than estimating them.
- **Refusal correctness** — does it decline when it should, and not decline when it should not.
- **Format and schema validity** where output is structured, measured as a pass rate.
- **Answer correctness** against expected answers where a correct answer exists.

**End to end**, the number that actually matters is the pass rate on the labelled suite, with
latency and cost per request alongside it — because an accurate system nobody can afford is not
shipped.

What he avoids: perplexity, which is a training diagnostic rather than a product metric and is not
even comparable across tokenisers. And any metric he cannot tie to a user-visible failure.

**Follow-up.** *"How does he measure groundedness without a human?"* — Requiring citations at the
claim level and checking them programmatically against the retrieved text catches a lot. The agent on
this site has a verification node that does exactly that.

**Grounded in.** eval_retrieval.py recall methodology, Document Q&A unsupported-answer tracking, interview agent verify node, Pulsar eval set

### Q7.6 — How would he catch a regression before it reaches users?

- **Difficulty:** engineer
- **Tags:** regression, ci, testing, process
- **Asked by:** Engineer, Hiring Manager

**Answer.**

A scored suite that fails the build, plus the discipline of treating content changes as code changes.

The mechanics on this site: `eval_retrieval.py` runs in about a second, exits non-zero on failure,
and the README instructs running it after any change to the profile data or the retrieval code. It
is small enough and fast enough that there is no excuse for skipping it.

The part that is less obvious and that he has been caught by twice: **in a retrieval system, the
corpus is the index.** Editing content is editing the search behaviour. Bug 05 was documenting a bug
in the build log, which added that text to the corpus and reintroduced the matching behaviour the bug
described. Bug 12 was editing his experience section, which broke a retrieval case that had passed
for months — the underlying defect was a missing stopword, but the content edit is what exposed it.
Neither change touched retrieval code. So "run the eval on content changes" is not a nicety.

What he would add, and what is genuinely still on his roadmap for this site: wiring the eval into CI
so a bad retrieval change cannot merge. Right now it is a documented step rather than an enforced
one, and he would say a check that depends on someone remembering is a check that will eventually
not run.

From the quality-engineering side he brings the rest of the standard apparatus: acceptance criteria
agreed before work starts, test strategy reviewed with dev and product, and release readiness as an
explicit gate rather than an assumption. That is what he did on Venera's platform for six months, and
the defect escape rate came down sprint over sprint as a result.

**Follow-up.** *"Why is the eval not in CI already?"* — It is on the published roadmap and not done.
He lists it as a gap rather than claiming it.

**Grounded in.** eval_retrieval.py exit code, README instructions, build log bugs 05 and 12, site roadmap on CI, release readiness experience

### Q7.7 — How does he evaluate something with no single correct answer?

- **Difficulty:** engineer
- **Tags:** evaluation, subjective, rubrics, llm-judge
- **Asked by:** Engineer, Hiring Manager

**Answer.**

By converting "is this good" into a set of properties that can each be checked, rather than trying
to score quality directly.

On an open-ended answer, the properties he would actually assert:

- **Groundedness.** Every factual claim traceable to a retrieved passage. Checkable, and the most
  important one for his systems.
- **Refusal correctness.** Did it decline when it had no basis. Binary.
- **Format compliance.** Length bounds, structure, required elements. Programmatic.
- **Absence of specific failures.** Does it invent an employer, a date or a number. A targeted check
  against a known list catches the category that matters most here.

That covers most of what "good" means for a grounded assistant without needing a judgement call. What
is left over — is it well-written, is it the *most useful* framing — is genuinely subjective, and for
that the options are human review on a rubric, pairwise preference comparison, or an LLM judge.

His view on LLM judges: useful for scale, and requiring their own validation. A judge is a model with
its own biases — position bias favouring the first option, length bias favouring longer answers, and
self-preference for outputs resembling its own style. So the judge has to be calibrated against human
labels on a sample before you trust its scores, and reported as "agrees with human labels 85% of the
time" rather than as ground truth. Without that step you have replaced an unmeasured system with an
unmeasured measurement.

The pragmatic position he holds: a small hand-labelled set you actually wrote beats a large automated
one you have not validated. The prompt-evaluation loop on his NLP project uses a hand-labelled
question set for exactly that reason.

**Follow-up.** *"How many labelled examples are enough?"* — Fewer than people think to start. Thirty
cases covering the failure modes you know about is a real measurement; zero is not.

**Grounded in.** NLP Pipelines hand-labelled question set, unsupported-answer metric, must-decline eval design

### Q7.8 — What does his QA background actually contribute to AI work?

- **Difficulty:** hiring-manager
- **Tags:** qa, testing, transferable-skills, quality
- **Asked by:** Hiring Manager, Recruiter

**Answer.**

Three specific habits, and they are the ones that decide whether an LLM feature is shippable.

**Deciding what correct looks like before building.** A test strategy is a statement of expected
behaviour written in advance. Applied to a generative system that is an eval set, and it is the same
artifact doing the same job. The reason he writes one for everything is not diligence, it is that he
spent six months in a role where the deliverable *was* that artifact.

**Designing the failure path first.** In QA the question is always what this does when it is wrong.
That reflex produced the architecture of both systems he has built: this site returns retrieved
resume text directly when every model provider is unavailable, so it degrades rather than erroring;
the Pulsar chatbot validates generated templates against the schema so malformed output cannot reach
the product. Both are failure-path decisions made before the happy path was optimised.

**Knowing that the quiet failure is the dangerous one.** He intercepted a severity-1 503 before
release and coordinated a same-day hotfix, avoiding roughly four hours of customer-facing downtime.
The thing that generalises is that the failure was found because someone was looking, not because
anything alerted. LLM systems fail in exactly that mode — no stack trace, nothing red, just a
confident wrong answer — and the only defence is having decided in advance what to check.

The concrete evidence that it transferred rather than being a story he tells: bug 08 on this site,
where a valid key was configured, the health check said green, and every answer was silently coming
from the fallback. That is a QA finding in an AI system. He built the probe that distinguishes
"configured" from "actually working" because "it looks fine" is not a status he accepts.

**Follow-up.** *"Does the QA background limit him as a builder?"* — The risk would be over-caution. He
owns the implementation of the Pulsar feature, not just its testing, so the evidence is that he
builds as well as verifies.

**Grounded in.** Internship QA record, severity-1 interception, zero-key fallback design, Pulsar schema validation, build log bug 08

### Q7.9 — How does he decide what to measure versus what to assume?

- **Difficulty:** engineer
- **Tags:** measurement, judgement, pragmatism, metrics
- **Asked by:** Engineer, Hiring Manager

**Answer.**

He measures the things a decision depends on and the things that will drift, and he assumes the rest —
because measuring everything is a way of measuring nothing well.

The test he applies: would a different value change what I do? If yes, measure it. Retrieval recall
changes whether he works on chunking or on prompting, so it is measured. The exact latency of a
function that runs once at startup changes nothing, so it is not.

The second test: will this number stop being true without anyone noticing? Anything that drifts needs
measurement rather than a comment. He has a concrete example of getting this wrong — bug 06 on this
site was hand-written statistics in a section whose entire claim is that figures are measured. The
chunk count and index size were typed by hand and stopped being true every time content was added,
three times. The fix was to compute them from the running index at startup, so the page reports its
own state rather than a remembered one.

That is the principle he would state: **if you are claiming a number, derive it.** The eval score and
chunk count on the About section of this site are computed at boot from the actual index and the
actual test suite, not written down.

What he deliberately does not measure: things where the cost of measurement exceeds the value. He has
not built a latency budget for this site because it is a portfolio, not a service with an SLA, and
saying so is more honest than inventing a metric to look rigorous.

The failure mode on the other side, which he would acknowledge: measuring becomes a substitute for
deciding. A number is not a decision, and a team that instruments everything and changes nothing has
the same outcome as one that measures nothing.

**Follow-up.** *"What is the cheapest useful measurement?"* — Logging the inputs and outputs of a
sample of real traffic. Almost everything else can be reconstructed from that; nothing can be
reconstructed without it.

**Grounded in.** Build log bug 06, computed About statistics, eval_retrieval.py, measured 0.04 ms retrieval figure

### Q7.10 — What would he do if an eval set and a stakeholder disagreed?

- **Difficulty:** behavioural
- **Tags:** communication, stakeholders, conflict, judgement
- **Asked by:** Hiring Manager

**Answer.**

Take the disagreement as information about the eval set, not as a problem to win.

If a stakeholder says the system feels worse and the suite says it improved, the most likely
explanation is that the eval is measuring the wrong thing or is missing the cases they care about.
That is a genuinely common outcome — an eval set built by the engineer captures the failures the
engineer anticipated, and the person using it daily encounters a different distribution.

So the process would be: get specific examples from them. Not "it feels worse" but the actual
inputs where it disappointed. Then run those and see. Three outcomes:

- **The system does fail on them and they are not in the eval.** The eval was incomplete; add the
  cases and now the score reflects reality. This is the most common result and it makes the suite
  better.
- **The system handles them correctly.** Then the disagreement is about something else — expectations,
  a change in phrasing, a different mental model of what the feature does. Worth surfacing, because it
  is usually a product or communication issue rather than a quality one.
- **They are right and the metric is measuring a proxy.** For example scoring retrieval recall while
  they care about answer usefulness. That means changing what is measured.

The thing he would not do is defend the number. His whole position is that an eval set is a tool for
finding out, not evidence in an argument — and a suite that only ever confirms the engineer was right
has stopped being useful.

The same reasoning applies to the QA side of his experience, where the job involved agreeing
acceptance criteria with dev and product before work started. Disagreement discovered at review time
is usually a specification that was never actually shared.

**Follow-up.** *"What if they want to ship despite a failing eval?"* — State the risk plainly and in
terms of what it costs, once. It is their call; the job is making sure it is an informed one.

**Grounded in.** Eval-set methodology, acceptance criteria work with dev and product teams, build log discipline

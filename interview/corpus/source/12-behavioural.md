# Part 12 — Behavioural Questions

> The "tell me about a time" questions. Interviewers use these to check whether the technical
> story holds up when told as events rather than as claims. Every answer here is built from
> something that is on his record, told in situation–action–result order, with the result stated
> as honestly as the record supports.

### Q12.1 — Tell me about a time he caught a serious problem before it reached users.

- **Difficulty:** behavioural
- **Tags:** incident, severity-1, star, impact
- **Asked by:** Hiring Manager, Recruiter

**Answer.**

**Situation.** During his internship at Venera Technologies he was doing release checks on the media
quality control platform ahead of a build going out.

**Task.** Release readiness — confirming the build was safe to ship, not just that the tests were green.

**Action.** He found a severity-1 failure: a service returning 503 under conditions the build had not
been exercised against. Rather than logging it and moving on, he raised it immediately and coordinated
the same-day hotfix across dev and product — getting the fix specified, built, verified and into the
release rather than letting the build slip or ship with it.

**Result.** The failure never reached customers. The estimate is roughly four hours of user-facing
downtime avoided. It is also one of the reasons his internship record shows zero critical defects
reaching production across seven consecutive builds.

What he takes from it, which is the part worth listening for: nothing had flagged it. The build was
green. It was found because checking was somebody's job and that person bothered. He applies the same
lesson to LLM systems, where the characteristic failure is also silent — a fluent, confident, wrong
answer with no error anywhere — and the only defence is having decided in advance what to check.

He would also be precise that the zero-defect record is a team outcome he contributed to, not something
he achieved alone.

**Follow-up.** *"What was the hardest part?"* — The coordination, not the finding. Getting a fix through
several people under a same-day deadline was the part he describes as difficult.

**Grounded in.** Internship: severity-1 503 intercepted, same-day hotfix, ~4 hours downtime avoided, zero critical defects across 7 builds

### Q12.2 — Tell me about a mistake he made and what he did about it.

- **Difficulty:** behavioural
- **Tags:** mistakes, ownership, debugging, star
- **Asked by:** Hiring Manager

**Answer.**

**Situation.** An early version of his portfolio assistant was designed so that retrieval always
returned *something*. When nothing in the resume matched a question, it substituted a few default
sections so the model always had material to answer from.

**Task.** It felt like robustness. It was a design error, and he was the one who made it.

**Action.** The failure surfaced when someone asked about his hobbies — which the resume does not cover —
and the assistant replied with his career summary, reading as though it had answered the question. He
traced it back to his own substitution logic: by filling empty results with defaults he had destroyed the
only signal that meant "the resume doesn't cover this", so neither the prompt nor the fallback had any way
to decline. He removed the substitution so retrieval returns empty honestly, made the application decline
deterministically before any model call when that happens, and added seven must-decline cases to the
evaluation suite so the behaviour could never quietly regress.

**Result.** The assistant now declines out-of-scope questions reliably, with his email address, and the
evaluation suite enforces it — 36 of 36 cases passing, seven of which assert that nothing should be
retrieved.

The reflection he would add: the mistake came from optimising for the system always having an answer,
which is the wrong goal for anything grounded. "Always answers" and "never makes things up" are in
tension, and he had quietly chosen the wrong side. He publishes it on the site's build log as bug 04.

**Follow-up.** *"Would you have caught it without a user asking?"* — Probably not quickly. That is exactly
why the must-decline half of an eval set is the part he now writes first.

**Grounded in.** Build log bug 04, empty-retrieval design, 7 must-decline eval cases, 36/36

### Q12.3 — Tell me about a time he had to learn something new quickly.

- **Difficulty:** behavioural
- **Tags:** learning, adaptability, genai, star
- **Asked by:** Hiring Manager, Recruiter

**Answer.**

**Situation.** When he converted to full-time at Venera in August, he was moved onto the company's first
generative-AI feature — a chatbot to generate QC templates for Pulsar, their legacy on-premise product.
There was no internal precedent; nobody at the company had built one.

**Task.** Become the primary engineer on it, owning both the implementation and the testing, having spent
the previous six months in quality engineering rather than building AI systems in production.

**Action.** He worked alongside an external AI consultant brought in precisely because the expertise was
not in-house, and he learned the parts that were new to him in the context of the real constraint rather
than in the abstract: running open-weight Qwen models entirely inside an on-premise deployment with no
outbound calls, local embedding-based retrieval over the template corpus, and structured-output validation
against the existing schema. The parts he already knew — test strategy, release readiness, the product and
its domain — he brought straight across, which is why he wrote the evaluation set himself.

**Result.** The feature was built from scratch and is his primary ongoing work. He has owned it since
August.

He would frame the speed honestly: he did not learn generative AI from zero in August. He had been building
retrieval systems and LLM pipelines on his own for months — a LangChain and Pinecone document Q&A system, NLP
pipelines on Hugging Face, and this site. What was new was doing it inside someone else's constraints, and
having expert support available made that a reasonable bet for the company rather than a reckless one.

**Follow-up.** *"What would he do differently with more time?"* — Worth asking him directly; that is the
most specific thing he can offer about the project.

**Grounded in.** Pulsar chatbot since August, external AI consultant, prior self-directed projects, QA background on the same platform

### Q12.4 — Tell me about a time data told him something he didn't expect.

- **Difficulty:** behavioural
- **Tags:** evaluation, surprise, measurement, star
- **Asked by:** Hiring Manager, Engineer

**Answer.**

**Situation.** After fixing a retrieval bug on his assistant, he wrote it up in the site's public build log,
which is part of the corpus the assistant searches.

**Task.** It was documentation. It was not supposed to change any behaviour.

**Action.** The next run of the evaluation suite dropped from 36 of 36 to 34 of 36. Nothing in the retrieval
code had changed. He traced it and found that the write-up itself was the cause: describing the bug had
named the exact terms involved, and because the build log is indexed like every other part of the site,
those words were now in the corpus and reintroduced the very matching behaviour the bug was about. He
rewrote the entry in deliberately generic language and the suite returned to 36 of 36.

**Result.** Fixed, and a permanent change in how he thinks about it: in a retrieval system the corpus *is*
the index, so any content edit is a behaviour change. The build log's wording has stayed generic about
specific terms ever since, and the log itself says why.

It happened again in a different form later — editing his experience section broke a case that had passed
for months, because it exposed a missing stopword. Both times, reading the code would never have found it;
the only reason he knew was that a scored suite ran after a change that "could not" affect retrieval.

**Follow-up.** *"What is the lesson for a team?"* — Run the retrieval eval on content changes, not only on
code changes. Most teams do not.

**Grounded in.** Build log bugs 05 and 12, eval drop 36/36 to 34/36, indexed build log

### Q12.5 — Tell me about a time he disagreed with the conventional approach.

- **Difficulty:** behavioural
- **Tags:** judgement, trade-offs, decisions, star
- **Asked by:** Hiring Manager, Engineer

**Answer.**

**Situation.** Building the assistant for this site, the conventional recipe was obvious: embed the resume,
store the vectors in a hosted vector database, retrieve by similarity.

**Task.** Choose a retrieval approach for a corpus of about thirty short chunks, on free hosting, that had to
keep working with no API keys at all.

**Action.** He went against the default and used BM25 lexical retrieval in-process, then wrote down why:
embeddings would add a network round trip, a cold start and a bill, for a recall gain he could not measure at
that size. He identified that the real problem was not similarity at all but vocabulary — recruiters ask "can
he do X" and resumes say "built X" — and solved that directly with stemming, phrase normalisation and a
weighted synonym layer. Then he built an evaluation suite to prove the choice rather than just argue it.

**Result.** Retrieval runs in about 0.04 milliseconds, cannot fail with the network, costs nothing, and passes
36 of 36 evaluation cases. The site answers even when every model provider is down.

The part that makes it judgement rather than contrarianism: he made the *opposite* choice on the Pulsar chatbot
at work, where the vocabulary gap between how operators describe intent and how the schema encodes it is
genuinely semantic, and that system uses embeddings. And on the larger interview corpus behind this assistant
he moved to hybrid retrieval, exactly as the site's own roadmap had said he would once the corpus grew. The
position was never "BM25 is better"; it was "choose from the corpus, and measure".

**Follow-up.** *"How did he know he was right?"* — The eval set. Without it, it would have been an opinion.

**Grounded in.** Design decision "BM25 instead of embeddings", 0.04 ms, 36/36, Pulsar embedding retrieval, interview hybrid retrieval

### Q12.6 — Tell me about working with people outside engineering.

- **Difficulty:** behavioural
- **Tags:** collaboration, stakeholders, product, communication
- **Asked by:** Hiring Manager, Recruiter

**Answer.**

**Situation.** Throughout his time at Venera he has worked with dev and product teams on the media QC platform.

**Task.** Define what "done" means for features before they are built, and agree when a release is actually
ready.

**Action.** His concrete contribution has been defining acceptance criteria with product before work starts,
reviewing test strategies with developers, and making release readiness an explicit, agreed gate rather than a
feeling. The principle he works from is that most quality problems are specification problems — someone built
what they understood, someone else reviewed against what *they* understood, and the gap only appears at the end
when it is most expensive to close. Agreeing it up front is mostly a conversation, and it is the cheapest quality
intervention there is.

**Result.** The defect escape rate on the platform came down sprint over sprint, which is the measurable outcome
of that work.

It carried directly into the generative-AI feature. Deciding what the Pulsar chatbot should *refuse* to do was as
much a product decision as an engineering one — it is not the model's call — and getting it into the evaluation
set meant putting that question in front of product explicitly. Without that conversation, the refusal behaviour
would have been whatever the model happened to do.

He would describe himself as better at making requirements explicit than at persuading people, which is a fair
self-assessment at his stage.

**Follow-up.** *"How does he handle a stakeholder who wants to ship anyway?"* — State the risk plainly, once, in
terms of what it costs. Then it is their decision; his job is to make sure it is an informed one.

**Grounded in.** Current role: acceptance criteria with dev and product, release readiness, defect escape rate reduction, Pulsar refusal cases

### Q12.7 — Tell me about a time a user found a problem he missed.

- **Difficulty:** behavioural
- **Tags:** user-feedback, humility, ux, star
- **Asked by:** Hiring Manager

**Answer.**

**Situation.** His assistant gives answers that can run to several paragraphs, displayed in a chat panel.

**Task.** It worked in his testing. A user reported that it did not work for them.

**Action.** The report was that long answers opened scrolled to their *last* line — you landed on the closing
sentence and had to scroll back up to find the start. He had followed standard chat behaviour, which pins the
newest message to the bottom of the panel. That is right for short turns and wrong for anything taller than the
panel, and his own tests had mostly used short questions. He changed it so a new answer scrolls its first line to
the top, clamped so a short reply does not leave empty space.

**Result.** Fixed, and recorded on the site's build log as bug 09 — explicitly credited as reported by a user
rather than caught in testing.

Why he keeps it in the log, and credits it that way: the most useful thing about it is that it was not found by
him. His testing reflected his own usage pattern, and real users use things differently. Attributing it honestly
matters to him more than looking like he catches everything, and it is a cheap reminder that his evaluation sets
measure the cases he thought of, not the ones he did not.

**Follow-up.** *"How would he find this class of issue earlier?"* — Watch someone else use it. No test suite would
have caught a behaviour that was working exactly as designed.

**Grounded in.** Build log bug 09 (user-reported), scrollToStartOf in app.js

### Q12.8 — Tell me about a time he worked under a hard constraint.

- **Difficulty:** behavioural
- **Tags:** constraints, on-premise, design, star
- **Asked by:** Hiring Manager, Engineer

**Answer.**

**Situation.** Pulsar, the product his generative-AI feature lives in, is deployed on-premise at customer sites.
Those customers run it that way specifically so their media and workflows stay on their own infrastructure.

**Task.** Build a chatbot that turns an operator's plain-language description into a valid QC template — without
any call to an external AI service.

**Action.** Every decision followed from that constraint. The model had to run inside the deployment, so the
feature uses open-weight Qwen models. Retrieval had to be local too, so the embedding model ships with the
product and the vector store runs alongside it. And because the model is bounded by what customer hardware can
run, the usual escape hatch — upgrading to a bigger model when quality falls short — was not available. So
quality had to come from retrieval and grounding instead, and the validation layer that checks every generated
template against the schema became load-bearing rather than a safety net.

**Result.** A working feature built from scratch that respects the product's core promise, which he has owned
since August.

What he would say he learned: the constraint produced a better design than an unconstrained API would have. It
forced the parts that generalise — getting the right context in front of the model and refusing to let invalid
output through — to carry the weight, instead of relying on the model being excellent.

**Follow-up.** *"Would he choose open weights without the constraint?"* — For this feature, probably, for the
reproducibility. But he is clear the constraint came from the product, not from him.

**Grounded in.** Pulsar on-premise deployment, Qwen open-weight models, local embeddings and vector store, schema validation

### Q12.9 — Tell me about a time a system looked healthy but wasn't.

- **Difficulty:** behavioural
- **Tags:** observability, debugging, health-checks, star
- **Asked by:** Engineer, Hiring Manager

**Answer.**

**Situation.** His assistant had a valid API key configured, and its health check reported the model engine as
live.

**Task.** Everything looked green. The answers, though, were coming back as extracted resume text rather than
written responses.

**Action.** He noticed because every answer reports which engine actually produced it, and it kept saying the
local index rather than the model. He traced two faults stacked on top of each other. The HTTP layer was sending
Python's default user-agent, which the CDN in front of the provider rejected outright, so no request ever reached
the model. And the health check only asked whether a key was *present*, never whether the provider would actually
answer — so the graceful fallback was silently hiding a total failure. He set a real user-agent on every request,
and split health into a cheap "is it configured" check and an opt-in probe that makes one real call and reports the
true error.

**Result.** Both fixed, recorded as bug 08. The same wrong assumption resurfaced later in the status badge visitors
see, which showed a provider name while a different engine answered; that is bug 11, and it is now corrected from
each real answer.

The principle he took away: make the system report what it actually did, not what it was configured to do. It paid
off again later, when vendors retired the models this site used — the answers naming their own engine made it
obvious within minutes.

**Follow-up.** *"Why does graceful degradation make this worse?"* — Because it converts a loud failure into a quiet
one. The fallback was working exactly as designed, which is precisely what hid the problem.

**Grounded in.** Build log bugs 08 and 11, /api/health probe design, engine name on every answer, retired-model incident

### Q12.10 — Tell me about something he's proud of that isn't technical.

- **Difficulty:** behavioural
- **Tags:** values, honesty, character
- **Asked by:** Recruiter, Hiring Manager

**Answer.**

The honest version is that the resume does not cover much outside his work, and this assistant will not invent
hobbies or personal achievements for him. If you want to know him as a person, that is a conversation to have with
him directly — his email is jeetendrapatel1711@gmail.com.

What the record does show is a disposition, and it is visible in how he presents his own work rather than in any
single achievement:

- **He publishes his failures.** The site carries a log of twelve bugs that shipped broken before he caught them,
  including embarrassing ones, and one credited to a user rather than to himself.
- **He instructs his own assistant not to oversell him.** The system prompt behind this chat explicitly tells it to
  be honest that he is early-career and not to present him as a senior researcher. Most people building a
  self-promotional tool would do the opposite.
- **He credits help.** The resume states that the Pulsar feature was built with an external AI consultant, rather
  than implying he did it alone.
- **He lists what is unfinished.** The site's roadmap publishes its own gaps.

He would probably say the thing he values is being trustworthy about what he claims — that if he says something
works, it has been measured, and if he does not know, he says so. That is as much a character trait as an
engineering practice, and the site is built around it.

**Follow-up.** *"Is that just good marketing?"* — It is a strategy that only works if it is true. A recruiter can
check every claim here against the resume and the source code.

**Grounded in.** Build log (12 bugs, bug 09 user-credited), SYSTEM_PROMPT honesty instruction, consultant credit on resume, published roadmap, contact email

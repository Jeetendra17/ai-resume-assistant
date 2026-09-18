# Part 8 — Quality Engineering and Testing

> His first six months at Venera were quality engineering, and it is the most heavily quantified
> part of his record. These questions come up two ways: recruiters checking the numbers are real,
> and engineers checking whether the QA background is an asset or a sign he is not really a
> builder. Both are fair, and the answers below take both seriously.

### Q8.1 — Walk me through the 150 automated test scripts.

- **Difficulty:** hiring-manager
- **Tags:** testing, selenium, automation, python, metrics
- **Asked by:** Hiring Manager, Engineer

**Answer.**

Those were built during his six-month internship at Venera Technologies, on their media quality
control platform, in Python with Selenium WebDriver and the Page Object Model.

The measured outcomes: manual regression time down 65%, 78% coverage of P1 and P2 cases, and three
critical regressions caught before release as a direct result.

The Page Object Model detail matters more than it sounds. It means the locators and interactions for
each screen live in one class, and tests call methods on that class rather than addressing the DOM
directly. The reason is maintenance: without it, a UI change breaks every test that touched that
screen and you spend your time repairing the suite instead of extending it. A suite of 150 scripts
that nobody maintains stops being run within a couple of months, so the structure is what makes the
number mean anything.

The 65% figure is the one worth understanding, because it is the business case. Manual regression on
a platform like that is a person working through a checklist before every release. Automating the
bulk of it converts a recurring multi-day cost into a suite that runs unattended, which is what makes
a faster release cadence possible rather than just cheaper.

The 78% coverage number is deliberately *not* 100%, and he would defend that. Automating the long
tail of P3 and P4 cases costs more to build and maintain than the defects it catches are worth.
Choosing where to stop is the judgement in test automation; writing more tests is not.

What he would be precise about: this was QA automation, not production application code. The skill
that transfers is the discipline and the Python, not the domain.

**Follow-up.** *"What did the three critical regressions have in common?"* — Worth asking him
directly; the specifics are the interesting part and they are not on the resume.

**Grounded in.** Internship metrics: 150 scripts, 65% regression reduction, 78% P1/P2 coverage, 3 critical regressions, Selenium + POM

### Q8.2 — Tell me about the severity-1 incident.

- **Difficulty:** behavioural
- **Tags:** incident, production, severity-1, impact
- **Asked by:** Hiring Manager, Engineer

**Answer.**

During his internship he intercepted a severity-1 503 failure and coordinated a same-day hotfix,
which avoided roughly four hours of user-facing downtime.

What makes it the item he is proudest of is that the counterfactual is concrete. Most QA work has a
diffuse benefit — defects found, coverage raised — and it is hard to say what would have happened
otherwise. Here the alternative is specific: without the interception, that failure reaches
production and customers cannot use the service for about four hours.

Two things in it that generalise:

**It was found because someone was looking.** A 503 under specific conditions is not the kind of
thing that announces itself in a green build. It was caught because there was a person checking
release readiness rather than assuming it. That is exactly the habit he now applies to LLM systems,
where the characteristic failure also does not announce itself — nothing goes red, there is no stack
trace, and the output looks like every other output.

**Coordinating the fix was as much of the job as finding it.** A severity-1 found and reported is
half the work; getting a hotfix specified, built, verified and released the same day means working
across dev and product under time pressure. He describes the coordination as the part that was
actually hard.

The honest framing he would give: "zero critical defects across seven builds" is a team outcome he
contributed to, not a solo achievement. He was the person doing the coverage and the release checks,
not the only person responsible for quality.

**Follow-up.** *"What did he change afterwards?"* — Worth asking him directly. The generalisable
answer he gives is that a failure found once should become a check that runs every time, which is the
same reasoning behind adding cases to an eval set before fixing them.

**Grounded in.** Internship: severity-1 503 intercepted, same-day hotfix, ~4 hours downtime avoided, zero critical defects across 7 builds

### Q8.3 — What did validating 120 API endpoints actually involve?

- **Difficulty:** engineer
- **Tags:** api-testing, postman, rest, aws, microservices
- **Asked by:** Engineer, Hiring Manager

**Answer.**

Postman-based validation across Venera's AWS microservices — 75 endpoints on Quasar, the cloud QC
product, and 45 on Pulsar, the on-premise one. The measured outcome was a 98.3% pass rate with two
production-blocking defects found and resolved before deployment.

What that work involves beyond sending requests: checking status codes and response schemas,
validating behaviour at boundaries rather than only on the happy path, checking authentication and
authorisation actually enforce what they claim, and verifying error responses are correct rather than
merely present. Boundary value analysis is on his skills list and that is where it applies — the
defects live at the edges of ranges, not in the middle.

The two production-blocking defects are the point of the exercise. A 98.3% pass rate is not
impressive on its own; finding the two things that would have broken a deployment is. That is the
same asymmetry as the severity-1 interception — most of the value of this kind of work is
concentrated in a small number of findings.

Working across two products with different deployment models is also relevant background for what he
does now. Quasar is cloud-native on AWS; Pulsar ships on-premise to customer sites. Those have
genuinely different constraints — what you can assume about the network, how you release, what
"reproduce the environment" means. Knowing Pulsar's constraints from the QA side is part of why he
was a reasonable person to hand its first generative-AI feature to, and it is why the architecture of
that feature starts from "this has to run offline".

**Follow-up.** *"Was any of this automated?"* — The Selenium suite was his automation work; the API
validation was Postman-based. Worth asking him how much of the API layer he would automate today.

**Grounded in.** Internship: 120 endpoints, 75 Quasar / 45 Pulsar, 98.3% pass rate, 2 production-blocking defects, Postman, BVA

### Q8.4 — Is he a QA engineer or a software engineer?

- **Difficulty:** sceptical
- **Tags:** role, identity, career, objection
- **Asked by:** Hiring Manager, Recruiter

**Answer.**

His title is Associate Software Engineer, and his primary work is building a generative-AI feature.
So: software engineer, with a quality engineering background he has not discarded.

The full trajectory: six months as a graduate trainee and QA engineer on Venera's media QC platform,
converted to full-time in August, and since then the primary engineer on the Pulsar template-generation
chatbot — owning the implementation, not only the testing.

The reason the question comes up is that the QA work is the most quantified part of his resume, so it
takes up visual space. He keeps it prominent deliberately rather than burying it, which is a
defensible choice: it is a year of real production experience, and the habits it produced are the ones
that make his AI work different from a portfolio of notebooks.

The fair version of the concern underneath the question is whether someone from a QA background will
default to verifying rather than building — waiting for a specification instead of forming a view,
or over-testing instead of shipping. That is a real pattern.

The evidence against it in his case is that he owns the implementation of the Pulsar feature. He
designed the retrieval approach, the grounding, and the validation layer. Owning the eval set
alongside it is not a leftover QA obligation; he argues it is the right arrangement for a generative
system, because the person who knows where it is likely to be wrong is the person who built it, and
the risk of self-assessment is managed by the suite being written down and scored rather than
performed by intuition.

The fair summary: he is a builder whose instincts were formed in quality engineering, which shows up
as designing the failure path before the happy path.

**Follow-up.** *"Would he take a QA role?"* — He is looking for AI Engineer / ML Engineer roles. Worth
asking him directly about how he would feel if a role turned out to be mostly testing.

**Grounded in.** Title (Associate Software Engineer), Pulsar chatbot implementation ownership, internship QA role, career narrative

### Q8.5 — How does testing an LLM feature differ from testing normal software?

- **Difficulty:** engineer
- **Tags:** testing, llm, determinism, evaluation
- **Asked by:** Engineer, Hiring Manager

**Answer.**

The deterministic parts are tested normally. The model call is not testable that way at all, and
conflating the two is where most teams go wrong.

**Everything except the model call is ordinary code.** Chunking, retrieval ranking, prompt assembly,
response parsing, citation extraction, schema validation. These are pure functions over data and
should have real unit tests. If your architecture does not let you test them without a network call,
that is the finding — the fix is an adapter boundary at the provider, which this site has for exactly
that reason.

**The model call gets a stub in unit tests**, and the stub should return the awkward responses:
empty string, truncated JSON, a refusal, a 429, a timeout. Most production incidents in LLM systems
are mishandled non-happy responses, and those are trivially testable with a fake and untestable
against a live model.

**Quality is evaluated, not asserted.** `assert answer == "..."` is meaningless against a sampled
model. What works is a labelled set scored on properties — groundedness, refusal correctness, schema
validity, length — with a threshold that fails the build. That is a different artifact from a unit
test, it costs money and time, and it belongs on a schedule or on changes to prompts and retrieval
rather than on every commit.

**Determinism is not available, even at temperature 0.** Greedy decoding removes sampling randomness,
but floating-point reduction order on GPUs varies, batch composition on a shared endpoint changes
kernel selection, and providers repoint endpoint aliases at new checkpoints. Anyone building a suite
on exact-match against a hosted model will have a flaky suite within a month.

The half people forget, which he insists on: **test that it refuses**. A must-decline set of questions
the corpus does not cover, asserted to produce a refusal. Seven of his 36 cases on this site are
exactly that.

**Follow-up.** *"How often should the eval run?"* — Retrieval eval on every content or retrieval
change, because it is fast and free. Generation eval on prompt and model changes, because it is not.

**Grounded in.** Provider adapter boundary in core/providers.py, 36-case eval with 7 must-decline, Pulsar eval set, fallback path testing

### Q8.6 — What does he mean by release readiness?

- **Difficulty:** hiring-manager
- **Tags:** release, sdlc, process, acceptance-criteria
- **Asked by:** Hiring Manager, Engineer

**Answer.**

A decision made against agreed criteria, rather than a feeling that things look fine.

His formal experience of it is at Venera, working with dev and product teams to define acceptance
criteria, review test strategies, and make AWS cloud-native release readiness an explicit gate. The
measured outcome was the defect escape rate coming down sprint over sprint.

What it involves in practice:

**Acceptance criteria agreed before the work starts.** This is the highest-leverage part and the one
most often skipped. Disagreement discovered at review time is nearly always a specification that was
never actually shared — someone built what they understood and someone else reviewed against what
they understood. Agreeing it up front is cheaper than arguing about it at the end.

**A defined set of checks that must pass**, so "ready" is a state with a definition rather than a
judgement call made under schedule pressure.

**Knowing what is not covered.** A release decision made without knowing the gaps is not informed.
Saying "this has not been tested under concurrent load" is more useful than implying everything was
checked.

**Someone accountable for the call.** Release readiness diffused across a team is release readiness
nobody owns.

The reason this transfers to AI work directly: it is the same shape as an eval set. A statement of
expected behaviour, agreed in advance, checked before shipping. When he says the evaluation set for
the Pulsar chatbot covers both what it must generate and what it must refuse, that is acceptance
criteria for a generative system.

Where he would temper it: release gates can become theatre if they are long checklists nobody reads.
The value is in a small number of checks that would actually stop a release, not in comprehensiveness.

**Follow-up.** *"What is his criterion for shipping an AI feature?"* — The eval passes, the failure
path is defined and tested, and the known gaps are written down. Not "the demo went well".

**Grounded in.** Current role: acceptance criteria and release readiness work, defect escape rate reduction, Pulsar eval set

### Q8.7 — How did he manage 79 defects?

- **Difficulty:** recruiter
- **Tags:** defect-management, zoho, process, triage
- **Asked by:** Recruiter, Hiring Manager

**Answer.**

In Zoho, across his internship — 79 defects managed, 61 resolved, 10 of them critical, with test
assets maintained in Bitbucket under structured pull request review.

What "managed" covers beyond logging them: writing a reproduction that someone else can follow,
assigning severity honestly, tracking them to resolution, and verifying the fix rather than accepting
that it was marked done. The last one is the part that makes the number meaningful — a defect marked
resolved and never verified is a defect that comes back.

The skill in defect work that is not obvious is **severity assignment**. Marking everything critical
destroys the signal and means nothing gets prioritised; marking things low to avoid friction means
real problems sit in a backlog. Ten of 79 being critical is a plausible distribution, and calibrating
that is a judgement developed by being wrong a few times.

The other part is the write-up. A defect report that a developer cannot reproduce is work transferred
rather than work done. Clear reproduction steps, expected versus actual, environment, and severity
with a reason — that is the difference between a report that gets fixed and one that gets closed as
"cannot reproduce".

The habit shows up directly in his AI work. The build log on this site documents twelve bugs in
exactly that structure — symptom, cause, fix — which is a defect report format applied to his own
work. And the discipline of adding a failing case to the eval set before fixing it is the same
instinct as verifying a fix rather than trusting it.

**Follow-up.** *"Why were 18 not resolved?"* — Not covered on the resume. In any real backlog some
are deferred, some are not reproducible, and some are working as designed. Worth asking him.

**Grounded in.** Internship: 79 defects in Zoho, 61 resolved, 10 critical, Bitbucket PR reviews, build log format

### Q8.8 — What is the most useful thing QA taught him?

- **Difficulty:** behavioural
- **Tags:** lessons, quality, philosophy, transferable
- **Asked by:** Hiring Manager, Engineer

**Answer.**

That a system is not done when it produces output — it is done when you can show it produces the
right output. That sentence is the one he uses, and everything he has built since is an application
of it.

The experience behind it is watching a severity-1 failure get caught an hour before release because
someone bothered to check. Nothing had flagged it. The build was green. It was found because checking
was somebody's job.

Why that transfers unusually well to LLM systems: their characteristic failure is a confident wrong
answer. There is no exception, no stack trace, no alert. The output is fluent and well-formed and
wrong, and it looks exactly like the output that is fluent and well-formed and right. The only thing
that catches it is having decided in advance what correct looks like and measuring against it — which
is what a test strategy is, and what an eval set is.

The second thing, which is less about process: **the failure path is a design decision, not an error
handler.** In QA you spend your time on what happens when things go wrong, and you notice that most
systems have a well-considered happy path bolted to an afterthought. So he designs the failure first
now. This site returns retrieved resume text directly when every model provider is unavailable, so a
visitor gets an answer rather than a stack trace. The Pulsar chatbot refuses rather than guessing when
it cannot produce a valid template. Both of those were decided before the happy path was tuned.

The third, smaller one: **a fix you have not verified is a hypothesis.** Which is why failing cases go
into the eval before they are fixed.

**Follow-up.** *"Is there anything QA taught him that he has had to unlearn?"* — Worth asking. The
plausible answer is the instinct to wait for a specification rather than form a view, which building
a feature end to end forces you out of.

**Grounded in.** About section narrative, severity-1 interception, zero-key fallback design, Pulsar refusal behaviour, eval discipline

### Q8.9 — Does he write tests for his own code?

- **Difficulty:** engineer
- **Tags:** testing, practice, discipline, self
- **Asked by:** Engineer

**Answer.**

Yes, and this site is the auditable example, which is a fair thing to check rather than take on
trust.

What exists here: `eval_retrieval.py`, a 36-case retrieval suite that exits non-zero on failure and
is documented as the thing to run after any change to the profile data or the retrieval code. It
covers 29 questions that must retrieve the right resume section and 7 that must retrieve nothing at
all. It is fast enough — about a second — that there is no friction excuse for skipping it.

For the interview corpus and the agent pipeline there is a retrieval eval over the larger corpus plus
tests for the deterministic parts: the corpus parser, the retrieval fusion, the prompt registry and
the graph executor, including the stdlib fallback path so the claim that it degrades gracefully is
tested rather than asserted.

What he would be honest about: the coverage is not uniform. The evaluation suites are genuinely good
because they are the thing he cares most about; the unit-test coverage of the web layer is thinner.
And the eval is not yet wired into CI, which is on the published roadmap — a check that depends on
someone remembering is a check that will eventually not run, and he says so rather than claiming
otherwise.

The pattern worth noting is what he tests. He puts the effort into the suites that catch the failures
he cannot see by reading code — retrieval behaviour, refusal behaviour, the degraded path — rather
than into coverage percentage. Bug 05, where writing documentation reintroduced a bug, and bug 12,
where a content edit broke a retrieval case, are both things no unit test would have caught and the
eval did.

**Follow-up.** *"What is his test coverage percentage?"* — Not measured, and he would rather say that
than quote a number. The eval pass rate is the figure he stands behind.

**Grounded in.** eval_retrieval.py (36 cases, non-zero exit), interview corpus tests, site roadmap on CI, build log bugs 05 and 12

### Q8.10 — How would he improve quality on a team that has no tests?

- **Difficulty:** hiring-manager
- **Tags:** process, influence, pragmatism, quality
- **Asked by:** Hiring Manager

**Answer.**

By starting where the pain is, not by proposing a testing strategy.

A team without tests almost always knows it, and has reasons — usually that the last attempt produced
a slow, brittle suite that everybody ignored. Arriving with a coverage target confirms their prior
that testing is overhead. So:

**Find out what actually breaks.** Look at the last few incidents or the recurring defects. There is
usually a small number of failure modes responsible for most of the pain, and they are the cheapest
thing to protect.

**Write the first tests for those**, and make them fast. A suite that takes forty minutes will not be
run. The value of `eval_retrieval.py` on this site is as much that it runs in a second as that it is
thorough.

**Make one thing that would have caught a real incident.** Nothing argues for testing like a suite
that catches something the week after it is added. That is worth more than any amount of advocacy.

**Agree acceptance criteria before work starts**, which is process rather than tooling and is often
the higher-leverage change. Most quality problems he has seen are specification problems — someone
built what they understood against a shared understanding that was never actually shared.

**Do not gate on coverage.** Coverage percentage measures lines executed, not behaviour verified, and
targeting it produces tests written to satisfy the metric.

What he would avoid: being the person who blocks releases. Quality work that is experienced as
friction gets routed around. The version that works is making the fast path also the safe path, so
running the checks is easier than not running them.

The honest limit: he has done this as an individual contributor on a team that already had QA
practice, not as someone who turned a team around. He would be describing an approach rather than a
track record.

**Follow-up.** *"What if the team pushes back?"* — Pick the single most painful recurring failure and
protect that one thing. Argument loses; a suite that catches a real regression wins.

**Grounded in.** Internship QA practice, acceptance criteria work, eval_retrieval.py speed and design, experience level

# Part 9 — Production, Cloud and the SDLC

> Questions about whether he can operate in a real engineering organisation: AWS, CI/CD, version
> control, on-premise versus cloud, and how he works inside a release process. This is the part of
> his record with the most ordinary professional substance, and the answers stay concrete about
> what he has done rather than what he has read about.

### Q9.1 — What is his AWS experience?

- **Difficulty:** recruiter
- **Tags:** aws, cloud, microservices, experience
- **Asked by:** Recruiter, Hiring Manager

**Answer.**

Hands-on, from working on Venera's cloud-native platform, and it is worth being precise about the
shape of it.

Quasar is Venera's cloud media quality control product, built as AWS cloud-native microservices. He
has worked on it since February 2026 — first validating 75 REST endpoints across those microservices
during his internship, then continuing across the full SDLC including AWS cloud-native release
readiness as a defined part of his current role.

So the experience is: working within an AWS microservices architecture, validating and testing
services deployed on it, and owning release readiness for that environment. He understands how the
product is deployed, how services interact, and what makes a release safe there.

What he would not claim: he is not a cloud architect. He has not designed an AWS architecture from
scratch, has not owned infrastructure-as-code for a system, has not managed IAM policy at
organisation scale, and has not run cost optimisation across an account. If a role expects someone to
own the cloud infrastructure, that is beyond what he has done.

Azure also appears on his skills list, at a lower level of depth than AWS.

The related experience that is arguably more relevant to AI roles: the contrast between Quasar and
Pulsar. Quasar is cloud-native; Pulsar ships on-premise to customer sites. Having worked on both means
he has a real feel for what changes when you cannot assume the network — which is exactly the
constraint that shaped the generative-AI feature he built, where the model has to run inside the
customer's deployment with no outbound calls.

**Follow-up.** *"Which AWS services specifically?"* — Not enumerated on the resume. Worth asking him
directly rather than having an assistant guess at service names.

**Grounded in.** Quasar AWS cloud-native microservices, 75 endpoints validated, AWS release readiness in current role, skills list

### Q9.2 — What is the difference between working on a cloud product and an on-premise one?

- **Difficulty:** engineer
- **Tags:** on-premise, cloud, deployment, constraints
- **Asked by:** Engineer, Hiring Manager

**Answer.**

He has worked on both at Venera — Quasar in the cloud on AWS, Pulsar on-premise at customer sites —
and the differences that matter are about control and assumptions.

**You control the cloud environment; you do not control an on-premise one.** In the cloud you know
the machine, the versions, the network, and you can change them. On-premise, the software runs on
hardware you have never seen, on a version the customer chose to install, possibly with no route to
the internet. Everything has to work under assumptions rather than knowledge.

**Releases are different events.** A cloud release is something you do; an on-premise release is
something a customer chooses to apply, possibly months later. So you support multiple versions
simultaneously, cannot hotfix everyone at once, and cannot roll back centrally. That changes the
bar for what ships.

**Debugging is indirect.** No live logs, no metrics dashboard, no reproducing it on staging with the
customer's data. You get a description and whatever diagnostics the product itself collects.

**Data does not leave.** This is usually the reason customers choose on-premise, and it is the
constraint that determined the architecture of the generative-AI feature he built. A chatbot that
posted an operator's description to a hosted model API would violate the premise of the product they
bought. So the model runs inside the deployment on open weights, the embedding model ships with it,
and the vector store runs locally.

He would say the on-premise constraint made him a better engineer on that feature, because it removed
the easy escape hatches. You cannot fix a quality shortfall by upgrading to a bigger model when the
model is bounded by the customer's hardware, so the quality has to come from retrieval, grounding and
validation — which is where it should come from anyway.

**Follow-up.** *"Which would he rather work on?"* — Worth asking him. The interesting answer is that
the constrained one produced the better architecture.

**Grounded in.** Quasar (cloud, AWS) and Pulsar (on-premise), Pulsar chatbot offline requirement, Qwen open-weight choice, endpoint validation across both

### Q9.3 — What is his experience with CI/CD?

- **Difficulty:** recruiter
- **Tags:** cicd, jenkins, automation, pipelines
- **Asked by:** Recruiter, Engineer

**Answer.**

Working within CI/CD pipelines rather than owning them, which is the accurate framing for his level.

On his skills list: Jenkins, CI/CD, Git and GitHub, Bitbucket, Gradle, Maven. In practice that means
his automated test suites ran as part of the pipeline, he worked with builds and release processes as
part of release readiness, and he maintained test assets in Bitbucket under structured pull request
review.

The part he has genuinely owned is what goes *into* a pipeline as a quality gate — the automated
regression suite that runs before a release, and the decision about what must pass. That is the
intersection of CI and his actual expertise.

What he has not done: built a pipeline from scratch, owned build infrastructure, managed deployment
automation for a service, or set up the release tooling for a team. If a role needs a platform or
DevOps engineer, this is not deep enough.

There is one honest gap he flags about his own work: `eval_retrieval.py` on this site exits non-zero
on failure specifically so it *can* be a CI gate, and it is not wired into CI yet. It is on the
published roadmap as "expand the eval set and wire it into CI so a bad retrieval change cannot merge".
He would rather list that as an unfinished item than imply the automation exists — which is also the
answer to what he would do first on a team: make the check that matters run automatically rather than
by convention.

**Follow-up.** *"What would he put in CI for an LLM system?"* — The retrieval eval, because it is fast
and free, plus unit tests on the deterministic layers. The generation eval on a schedule or on prompt
changes, because it costs money and time.

**Grounded in.** Skills list (Jenkins, CI/CD, Bitbucket, Gradle, Maven), test suites in pipeline, eval_retrieval.py exit code, site roadmap

### Q9.4 — How does he work with version control and code review?

- **Difficulty:** recruiter
- **Tags:** git, code-review, collaboration, process
- **Asked by:** Recruiter, Engineer

**Answer.**

Bitbucket at Venera with structured pull request reviews, and Git and GitHub for his own work. This
site's source is public.

What he would say about review specifically, because it is where the useful answer is: the most
valuable thing a review catches is not a bug, it is a decision that looks wrong out of context. The
code on this site carries comments explaining *why* rather than what, specifically at the points where
the correct-looking thing is wrong. One example: a template variable is accessed with bracket notation
rather than attribute notation, with a comment saying the attribute form resolves a built-in method
instead of the data — because that bug shipped once and the attribute form looks correct enough that
anyone tidying the file would reintroduce it. That comment exists for a future reviewer.

He treats the same principle in the other direction: a review comment asking "why" is more useful than
one proposing an alternative, because it surfaces whether the author had a reason.

On commit and branch practice he is conventional — small changes, descriptive messages, review before
merge. On his own repository he keeps the build log as a record of bugs and their causes, which is
effectively a review artifact for himself.

What he has less of: he has worked in structured review as a participant, not as someone setting
review standards for a team or owning a branching strategy. And he has worked on a small team rather
than on a repository with many concurrent contributors.

**Follow-up.** *"What does he want from a reviewer?"* — Given his level, he would say challenge on
design decisions rather than style. He has explicitly named code review from someone more senior as
what he needs to grow.

**Grounded in.** Bitbucket with structured PR reviews, public GitHub repository, in-code comments explaining non-obvious decisions, build log bug 01

### Q9.5 — How does he handle a production incident?

- **Difficulty:** behavioural
- **Tags:** incident, production, process, debugging
- **Asked by:** Hiring Manager, Engineer

**Answer.**

His direct experience is the severity-1 503 he intercepted before release, where a same-day hotfix was
coordinated and roughly four hours of user-facing downtime avoided. So the honest framing is that he
has caught and coordinated a serious issue, rather than that he has been on call for a major outage.

The approach he would describe:

**Contain before diagnosing.** Reduce impact first — roll back, disable the feature, fail over — and
understand it afterwards. The instinct to find the root cause while users are affected gets the order
wrong.

**Establish what changed.** Most incidents follow a change. Deployment, configuration, a dependency, a
data shift.

**Reproduce with the real inputs**, which requires having logged them. This is the part that decides
whether debugging is possible at all. His position on LLM systems specifically is that inputs,
outputs, retrieved chunk ids and model versions must be logged for a sample of traffic from day one,
because without that trace an incident becomes archaeology.

**Communicate while working.** Coordinating the hotfix across dev and product was, in his description,
the part that was actually hard about the severity-1 — finding it was quicker than getting a fix
specified, built, verified and released the same day.

**Make the failure a check.** A failure found once should become something that runs every time. It is
the same rule he applies to eval sets: add the failing case before fixing it, so the fix is provable
and the case cannot silently return.

What he has not done: been the on-call owner of a system at 3am, run a formal incident command, or
written a postmortem for a major outage. The build log on this site is the closest artifact — twelve
bugs with symptom, cause and fix — and it is self-directed rather than organisational.

**Follow-up.** *"What is the first thing he would set up on a new AI system?"* — Logging of inputs,
outputs, retrieved sources and model version for a sample of traffic. Everything else can be
reconstructed from that.

**Grounded in.** Severity-1 503 interception and same-day hotfix, build log, eval discipline, experience level

### Q9.6 — How does this site get deployed?

- **Difficulty:** engineer
- **Tags:** deployment, vercel, docker, hosting, free-tier
- **Asked by:** Engineer

**Answer.**

It is deliberately deployable four ways, because the point of the exercise was that it should not
depend on any one platform.

The live site runs on Vercel as a serverless function. The repository also carries a `render.yaml` for
Render, a `Dockerfile` targeting port 7860 for Hugging Face Spaces, and a `Procfile` with Gunicorn for
anything that reads one. The deployment plan documents the trade-offs of each — Render's free instance
sleeps after about fifteen minutes idle so the first visit takes around fifty seconds to wake, Spaces
does not sleep, Vercel has the fastest cold start.

The design constraint behind all of it is cost: the whole thing runs on free tiers. That is why
retrieval is in-process rather than a hosted vector database, why the model providers are free-tier
first with automatic failover, and why the dependency footprint is kept small enough to fit a
serverless bundle.

One deployment-specific bug is on the build log and is worth mentioning because it was caught in
review rather than in production. On the free serverless tier, the platform kills a slow request
before the application's own timeout fires — which would have killed the provider failover, since the
whole point of the chain is to try the next provider when one is slow. The app's request timeout
defaulted higher than the platform's function limit, so it would never have reached the fallback. The
fix was documenting a lower timeout for that platform so the app gives up and degrades gracefully
inside the platform's window.

He also notes in the deployment plan which platform to avoid and why: PythonAnywhere's free tier
blocks outbound HTTPS to non-whitelisted hosts, which breaks every model provider call.

**Follow-up.** *"Does the serverless rate limiter work?"* — Only per invocation, since the process does
not persist. He documents that as harmless here rather than pretending it is a real limiter.

**Grounded in.** vercel.json, render.yaml, Dockerfile, Procfile, DEPLOYMENT_PLAN.md, build log bug 07, in-process rate limiter note

### Q9.7 — How does he think about monitoring an AI feature in production?

- **Difficulty:** engineer
- **Tags:** monitoring, observability, drift, production
- **Asked by:** Engineer, Hiring Manager

**Answer.**

He would separate what he has done from what he knows should be done, because this is an area where
his production exposure is short.

**What he has built:** the assistant on this site reports which provider actually produced each
answer, and the health endpoint separates a cheap "is a key configured" check from an opt-in probe
that makes one real call and reports the true error. That split exists because of a specific failure —
a valid key was configured, health reported green, and every answer was silently coming from the local
fallback because a CDN was rejecting the request. A health check that confirms configuration is not a
health check.

**What he would set up on any new system, in order:**

- **Traffic sampling.** Inputs, outputs, retrieved chunk ids and scores, prompt version, model version.
  Without this, debugging is guesswork. It is the first thing, not the last.
- **Real health probes**, not configuration checks.
- **Cost and token counts per request**, tagged by feature. Teams that cannot attribute spend cannot
  reduce it, and a runaway loop will find that out for you.
- **Refusal and fallback rates.** A rising fallback rate means the primary path is failing quietly,
  which is exactly the failure that hides. A falling refusal rate might mean the system has started
  answering things it should decline.
- **Latency split by stage** — retrieval versus generation — because a single end-to-end number hides
  which one is the problem.
- **Query drift.** People asking things the corpus never covered is the signal that the corpus needs
  extending, and it is visible in the refusal rate before anyone complains.

**What he has not done:** run a monitoring stack for model quality in production, set up drift
detection with labels arriving late, or owned alerting for an AI system. That is a genuine gap.

**Follow-up.** *"What single metric would he alert on?"* — The fallback rate. It is the one that goes
up silently when everything else looks fine.

**Grounded in.** Engine status reporting, /api/health probe design, build log bugs 08 and 11, rate limiting, provider chain

### Q9.8 — Has he worked in an Agile process?

- **Difficulty:** recruiter
- **Tags:** agile, sprints, process, collaboration
- **Asked by:** Recruiter, Hiring Manager

**Answer.**

Yes — sprint-based work at Venera across the full SDLC, working with dev and product teams.

The concrete artifacts of it in his record: defining acceptance criteria with dev and product before
work starts, reviewing test strategies, and defect escape rate tracked and reduced sprint over sprint.
That last one is a sprint-level metric and the fact that it moved is evidence of a feedback loop
actually operating rather than ceremony being performed.

The part he would emphasise as substance rather than process vocabulary: **acceptance criteria agreed
up front.** Most of the quality problems he has seen come from a specification that was never really
shared — someone builds what they understood, someone else reviews against what they understood, and
the gap surfaces at the end when it is most expensive. Agreeing it before the work starts is the
cheapest quality intervention available and it is mostly a conversation.

He would also say the useful thing about working with product on acceptance criteria for an AI feature
is that it forces the refusal question into the open. What should the system do when it cannot
confidently answer is a product decision as much as an engineering one, and it does not get decided
unless somebody puts it on the table early. The must-refuse half of the Pulsar chatbot's evaluation
set exists because that conversation happened.

What he would not claim: he has not run a sprint, owned a backlog, or been a scrum master, and he has
worked on a small team rather than in a large multi-team programme.

**Follow-up.** *"How does estimation work for AI features?"* — Worth asking him. The honest general
answer is that the retrieval and evaluation work is estimable and the "make the output good enough"
work is not, which is why having an eval set early matters for planning as well as quality.

**Grounded in.** Full SDLC work with dev and product teams, acceptance criteria definition, defect escape rate reduction, Pulsar eval refusal cases

### Q9.9 — What would he need from us to be productive quickly?

- **Difficulty:** hiring-manager
- **Tags:** onboarding, ramp-up, support, growth
- **Asked by:** Hiring Manager

**Answer.**

Four things, and the first two are the ones that would actually change his ramp time.

**Access to what already exists.** For any AI feature: the current prompts, whatever evaluation exists,
and a sample of real traffic — inputs, outputs and what people actually ask. A day with real query
logs teaches more about a system than a week of reading code, because it shows what the system is
being asked to do rather than what it was designed to do.

**A clear statement of what failure costs.** Whether a wrong answer is an annoyance or an incident
determines the whole architecture. The Pulsar chatbot's design was largely determined by "must run
offline" and "an invalid template reaches an operator", and knowing those on day one was worth more
than a month of exploration would have been.

**Code review from someone more senior.** He names this himself as what he needs. He has about a year
of professional experience, one production AI feature, and a narrow set of reference points. The gap
between him and a senior engineer is mostly having watched more systems fail in more ways, and review
is how that transfers fastest.

**Exposure to larger scale.** He has not worked at high traffic volumes. If the role involves that, he
would want to be honest that it is new rather than pretend otherwise.

What he brings that shortens his own ramp: he has worked inside a real SDLC, is comfortable with
release processes and structured review, and he has a habit of building the measurement before the
feature, which means his first contribution on an undocumented system is usually an eval set that
tells everyone where it actually stands.

**Follow-up.** *"What would make him unproductive?"* — A system with no way to tell whether a change
helped. He would likely spend his first week building that, and would want agreement that this is
worth the time.

**Grounded in.** Experience level, stated need for senior code review, Pulsar constraints, eval-first methodology, SDLC experience

### Q9.10 — Can he work independently, or does he need direction?

- **Difficulty:** hiring-manager
- **Tags:** autonomy, ownership, working-style, collaboration
- **Asked by:** Hiring Manager

**Answer.**

The evidence points to independent with judgement about when to check, which is the combination you
want at his level.

The case for independence: he was handed Venera's first generative-AI feature — something with no
internal precedent — and built it from scratch, owning both implementation and testing. That is not
ticket work. Everything outside his job is self-directed too: the document Q&A chatbot, the NLP
pipelines with a prompt-evaluation loop, and this site, which is roughly three thousand lines carrying
a retrieval index, nine provider integrations, an evaluation suite and a published build log. Nobody
asked for any of it.

The case for it being judged rather than stubborn: the Pulsar feature was built alongside an external
AI consultant, engaged because the company had no internal precedent for this work. He describes that
as the right arrangement rather than a limitation, and he names code review from someone more senior
as what he wants. Someone who could not ask for help would not say that.

The place he is most likely to need direction is on scope and priority rather than execution. His
instinct is to build the measurement infrastructure first — an eval set before the feature — and that
is right often enough to be a strength and wrong sometimes when the priority is to ship something
rough and learn from it. A manager saying "not this time" would be useful to him.

The honest limit: one year of experience means fewer reference points, so his independent judgement on
unfamiliar problems is less reliable than it will be. He is good at recognising what he does not know,
which is the version of this that works.

**Follow-up.** *"Would he push back on a decision he disagreed with?"* — The site is full of documented
disagreements with conventional practice — BM25 over embeddings, no framework where one was not needed
— each with reasoning attached. The pattern is arguing with evidence rather than deferring or digging
in.

**Grounded in.** Pulsar feature ownership with consultant support, self-directed projects, this site's scope, stated need for code review, documented design decisions

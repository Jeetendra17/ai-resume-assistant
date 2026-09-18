# Part 2 — The Venera Generative-AI Chatbot

> This is the work most visitors end up asking about, so it gets the most space. Everything
> here is described at the level of problem, constraint and engineering reasoning. Venera's
> template schema, customer names and internal architecture specifics are deliberately absent —
> it is their product, and a public portfolio is not the place for them. If you need that depth,
> ask him directly and he can talk about it under the appropriate terms.

### Q2.1 — Walk me through the generative-AI chatbot he built at Venera.

- **Difficulty:** hiring-manager
- **Tags:** pulsar, chatbot, rag, qwen, flagship, on-premise
- **Asked by:** Hiring Manager, Engineer

**Answer.**

The problem: Pulsar is Venera's on-premise media quality control product. To use it, an operator
configures a QC template — the set of checks a piece of media gets run through. Building one by
hand means knowing the schema and picking through options, which is slow and is the kind of task
where people copy an existing template and edit it until it roughly works.

The feature: describe the template you want in plain language, and the system generates it.

The architecture, at the level he would describe it publicly: it is a retrieval-augmented
generation pipeline. The user's description is used to retrieve relevant material from the
existing corpus of templates and the schema that defines what a valid template can contain. That
retrieved material is assembled into context for a Qwen model, which generates a candidate
template. The candidate is then validated programmatically against the schema before anything is
shown or used, and a template that does not validate does not get through.

Retrieval is embedding-based over a vector store rather than keyword matching, because operators
describe what they want in their own words rather than in schema terminology — the gap between
"check this will play on broadcast" and the specific fields that encode it is a semantic gap, not
a lexical one.

The whole thing runs inside the customer's deployment. No outbound API calls. That single
constraint drove most of the decisions and is covered in the next question.

He is the primary engineer on it, built it from scratch alongside an external AI consultant, and
owns both the implementation and the testing — including the evaluation set it is scored against.

**Follow-up.** *"How long has it been running?"* — He has owned it since August 2026, when he
converted to full-time. It is his primary work.

**Grounded in.** Pulsar generative-AI chatbot, current role at Venera Technologies, Qwen models, on-premise constraint

### Q2.2 — Why Qwen and open-weight models rather than an API like OpenAI or Claude?

- **Difficulty:** engineer
- **Tags:** qwen, open-weights, on-premise, architecture, constraints
- **Asked by:** Engineer, Hiring Manager

**Answer.**

It was not a preference, it was a requirement, and that distinction matters because it is what
makes the project interesting.

Pulsar is deployed on-premise at customer sites. For the customers who run it that way, the
reason they run it that way is that their media and their workflows do not leave their
infrastructure. A feature that took an operator's description of their QC requirements and posted
it to a third-party API would violate the premise of the product they bought. In some deployments
there is no outbound internet route at all.

So the model had to run inside the deployment, which rules out every hosted API and puts you in
open-weight territory. Qwen was the family chosen.

What follows from that constraint is most of the engineering:

- **You cannot reach for a bigger model when quality is short.** With an API the escape hatch is
  to upgrade the tier. Here the model is fixed by what the customer's hardware can run, so
  quality has to come from retrieval and grounding instead. Getting the right context in front of
  a smaller model does more than a larger model with worse context would.
- **Retrieval has to be local too.** No hosted embedding API, so the embedding model ships with
  the product and the vector store runs alongside it.
- **Validation matters more, not less.** A smaller model is more likely to produce a
  well-formed-looking template that is subtly wrong, so the schema validation layer is
  load-bearing rather than a safety net.
- **Versioning is your problem.** There is no provider silently updating the model, which is
  good for reproducibility and means upgrades are a deliberate release decision.

The honest upside: it forced a design where the system does not depend on the model being
excellent, which is a better design regardless.

**Follow-up.** *"Would he have chosen open weights without the constraint?"* — For this feature,
probably yes, for the versioning and reproducibility reasons. But he would not claim the
constraint was his idea; it came from the product.

**Grounded in.** Pulsar on-premise deployment, Qwen open-weight models, current role

### Q2.3 — How does he stop it generating an invalid template?

- **Difficulty:** engineer
- **Tags:** validation, structured-output, guardrails, schema, reliability
- **Asked by:** Engineer, Hiring Manager

**Answer.**

By not trusting the model, structurally.

The generated template is validated against Pulsar's template schema before it can be used. If it
does not validate, it does not get through. That is the guarantee, and it is enforced in code
rather than requested in a prompt — which is the whole point. A prompt that says "only produce
valid templates" is a preference the model will usually honour. A validator is a property the
system has.

The layers, in order:

1. **Retrieval grounds the generation.** The model is given real templates and the relevant parts
   of the schema, so it is completing a pattern that exists rather than inventing structure from
   its own priors. Most malformed output comes from the model having to guess at shape.
2. **Constrained, structured generation.** The output is asked for in a defined structure rather
   than as prose that gets parsed afterward.
3. **Schema validation.** The hard gate. Field names, types, required fields, allowed values.
4. **Rejection over repair-at-any-cost.** If validation fails, the system does not quietly patch
   the output into something that passes. A bounded retry is reasonable; silently coercing a
   wrong template into a valid-looking one is worse than failing, because the operator then runs
   QC with checks they did not ask for.

The failure mode he is most concerned with is not malformed output — that is caught. It is
*well-formed and wrong*: a template that validates perfectly and encodes a different intent than
the operator described. Schema validation cannot see that, and it is the reason the evaluation
set exists and includes expected outputs rather than only checking that something parseable came
back.

This is also where the QA background shows up most directly. The instinct to ask "what does this
do when it is wrong" before asking "how good is it when it is right" is the same instinct that
found a severity-1 failure before release.

**Follow-up.** *"What happens if it cannot produce a valid template?"* — It refuses rather than
guessing. The evaluation set includes requests it is expected to decline, which is the half of
the eval that people skip.

**Grounded in.** Schema validation of generated templates, evaluation set, quality engineering background

### Q2.4 — What does the evaluation set for the chatbot look like?

- **Difficulty:** engineer
- **Tags:** evaluation, testing, eval-set, quality
- **Asked by:** Engineer, Hiring Manager

**Answer.**

It has two halves, and he would say the second half is the one that matters.

**The must-generate half:** descriptions paired with the template that should come out of them.
These are the cases where a correct answer exists and the system either produces it or does not.
Scoring them tells you whether a change to retrieval, the prompt or the model helped or hurt.

**The must-refuse half:** requests the system is expected to decline. Things outside what a QC
template can express, requests that are too vague to produce a specific template, and things that
are simply not what the feature is for. Without this half, an eval rewards a system that always
produces *something*, which is exactly the behaviour you do not want — a confident template for
an ambiguous request is worse than a refusal, because the operator has no signal that it guessed.

He holds the same view on his own portfolio assistant, where the eval is 29 must-match cases plus
7 must-decline cases, and the must-decline half was added only after it answered an unrelated
personal question by padding it with his career summary. That failure is why he builds the refusal
half in from the start now.

Why an eval set at all, rather than trying things and looking at the output: because with a
generative system you cannot tell whether a change helped by reading a few examples. The variance
between runs is large enough that two or three samples will confirm whatever you already
believed. A scored set turns "this feels better" into a number that moved or did not.

It also protects against the specific danger of this kind of work: retrieval and prompt changes
have non-local effects. Improving the context for one class of request frequently degrades
another, and nothing tells you unless you are measuring both.

**Follow-up.** *"Who wrote the eval set?"* — He did. He owns the testing side of the feature as
well as the implementation.

**Grounded in.** Chatbot evaluation set, portfolio assistant eval (36 cases), build log bug 04

### Q2.5 — What was the hardest part of building it?

- **Difficulty:** engineer
- **Tags:** challenges, design, retrieval, constraints
- **Asked by:** Engineer, Hiring Manager

**Answer.**

The vocabulary gap between how operators describe what they want and how the schema expresses it.

An operator asks for something in the language of their job — what they are checking for, what
the media is for, what they are worried about. The template schema is a structured configuration
of specific checks with specific parameters. Those two vocabularies barely overlap in surface
terms, which is precisely why keyword retrieval was not going to work and the retrieval layer is
embedding-based.

That is the same class of problem he hit on his own portfolio assistant from the other direction:
recruiters ask "can he do X" while a resume says "built X", and closing that gap took stemming,
phrase normalisation and a weighted synonym layer rather than a better model. He would say
recognising it as a retrieval problem rather than a generation problem is the transferable part —
the instinct when output is wrong is to improve the prompt, and often the prompt is fine and the
model was handed the wrong context.

The second hard part, related: working within a fixed model. With a hosted API, a quality
shortfall has an expensive but easy answer — use a better model. Running inside an on-premise
deployment means the model is whatever the customer's hardware supports, so every improvement has
to come from retrieval quality, grounding and validation. That is more constrained and, he would
argue, better engineering practice, because it forces the parts that actually generalise.

The third, which is less technical: deciding what the system should refuse. It is easy to specify
what a feature should do and much harder to draw the line where it should stop and say it cannot
help. That line is a product decision as much as an engineering one, and getting it into the
evaluation set meant making it explicit rather than leaving it to the model's judgement.

**Follow-up.** *"What would he do differently?"* — Worth asking him directly; the answers to that
are the most specific thing he can offer about the project and are not reduced to a summary well.

**Grounded in.** Pulsar chatbot retrieval design, portfolio assistant vocabulary-gap work, on-premise model constraint

### Q2.6 — He worked with an external AI consultant. What did he actually do himself?

- **Difficulty:** sceptical
- **Tags:** ownership, consultant, credit, collaboration
- **Asked by:** Hiring Manager, Recruiter

**Answer.**

A fair question, and the resume says "with an external professional AI consultant" rather than
hiding it, which is the right way round.

The division as he describes it: he is the primary engineer on the feature and owns the
implementation and the testing. The consultant was engaged as expertise Venera did not have
in-house — this is the company's first generative-AI feature, so there was no internal precedent
for how to approach it.

What that means in practice is that he was the person building it day to day and the person
responsible for it working, with access to someone more experienced to check direction against.
Which is, frankly, a good arrangement for someone's first production AI feature, and a better
signal than "built it alone" would be — a company putting a junior engineer on a first-of-its-kind
feature with expert support and having them own it is a company that thought about how to make it
succeed.

The parts that are unambiguously his: the implementation, the evaluation set, and the testing
strategy. The testing half in particular is where his prior six months of quality engineering on
the same platform was the reason he was the right person for it — he already knew the product,
the schema domain and the release process.

What he would not claim: that he independently chose the overall approach with no input, or that
he has the depth of someone who has built many of these. This is his first production generative-AI
system and he has been on it since August.

The way to calibrate it in an interview is to ask him about a decision he made that the consultant
disagreed with, or a problem he solved after the consultant's involvement ended. Those questions
separate ownership from attendance.

**Follow-up.** *"Would he be able to build the next one without a consultant?"* — Worth asking him.
He has been through one full cycle of it now, including the parts that went wrong.

**Grounded in.** Pulsar chatbot built with external AI consultant, implementation and testing ownership, prior QA work on same platform

### Q2.7 — How does the retrieval part of the chatbot work?

- **Difficulty:** engineer
- **Tags:** rag, retrieval, embeddings, vector-store
- **Asked by:** Engineer

**Answer.**

It is embedding-based retrieval over a vector store, run locally alongside the model.

The corpus being retrieved over is the existing body of templates plus the schema material that
defines what a valid template can contain. When an operator describes what they want, that
description is embedded and used to find the most relevant existing templates and schema sections,
which become the context the model generates from.

Embeddings rather than keyword search, for the reason covered earlier: operators describe intent
in their own vocabulary and the schema uses its own. Lexical overlap between those is poor, so
BM25-style matching would miss the right template while confidently returning one that shared a
few words. This is the mirror image of the choice he made on his portfolio assistant, where the
corpus is thirty short chunks and lexical retrieval is the *right* call — the technique follows
from the corpus, not from fashion.

Everything runs inside the deployment, so the embedding model ships with the product rather than
being a hosted API call. That is a constraint with a real cost — you are limited to embedding
models small enough to run there — and it is another reason the validation layer carries weight.

What he would emphasise about the design is that retrieval quality, not model quality, is the
lever he actually has. With the model fixed by the deployment, the difference between a system
that works and one that does not is almost entirely whether the right template ends up in the
context window. That makes retrieval the thing worth measuring and the thing worth spending time
on, which is why the evaluation set scores end-to-end output rather than treating retrieval as
plumbing.

**Follow-up.** *"Which vector store and embedding model?"* — Not covered here; that is Venera's
implementation detail. Ask him directly.

**Grounded in.** Embedding-based retrieval over a vector store, on-premise constraint, portfolio assistant BM25 decision

### Q2.8 — What does this project prove that his side projects do not?

- **Difficulty:** hiring-manager
- **Tags:** production, credibility, constraints, ownership
- **Asked by:** Hiring Manager

**Answer.**

Three things, and they are the three that side projects structurally cannot demonstrate.

**Working inside constraints he did not choose.** Every side project is built on the stack its
author picked, targeting the requirements its author set. The Pulsar chatbot had to run
offline inside an on-premise product, on models small enough for customer hardware, producing
output conforming to an existing schema he did not design. Most real engineering is working
inside constraints like those, and a portfolio of self-directed projects gives no evidence of it.

**Consequences.** If his document Q&A chatbot returns a bad answer, he notices and fixes it. If
the Pulsar chatbot produces a template that validates but encodes the wrong checks, an operator
runs quality control with the wrong checks, and that reaches a customer. Designing for that
changes what you build — it is the reason the validation layer is a hard gate rather than a
best-effort repair.

**Someone else's timeline and someone else's product.** It shipped as part of a commercial
product on a release schedule, with the review, integration and readiness work that involves —
not when he decided it was finished.

What it does *not* prove, to be fair to the question: scale, longevity, or that he can do this
repeatedly. It is one feature, owned since August, in a product that is not consumer-scale. And
he had expert support from an external consultant. It is strong evidence for his level and weak
evidence for anything beyond it.

The side projects still carry information, just different information — they show what he does
when nobody sets the bar, which is where the eval sets and the published build log come from.

**Follow-up.** *"Which would you rather ask him about in an interview?"* — This one, because the
constraints make the reasoning visible. Side projects mostly reveal taste.

**Grounded in.** Pulsar chatbot constraints and ownership, Document Q&A project, portfolio assistant, build log

### Q2.9 — How does he know the chatbot is actually good?

- **Difficulty:** sceptical
- **Tags:** evaluation, measurement, quality, evidence
- **Asked by:** Hiring Manager, Engineer

**Answer.**

Through the evaluation set, and he would be the first to say that is the only honest answer
available.

There is no way to look at a generative system and know whether it is good. Sampling a few
outputs tells you almost nothing, because the variance between runs is wide enough that a handful
of examples will confirm whatever you expected to see. The only thing that produces a real answer
is deciding in advance what correct looks like across a spread of cases, and then scoring against
it whenever something changes.

So what he has is: a set of descriptions paired with the templates that should result, plus a set
of requests that should be refused, scored as a suite. When retrieval changes, the prompt changes,
or the model version changes, that number moves or it does not.

What he would not claim: that the number is a guarantee. An eval set measures the cases you
thought of. The failures that matter most are usually the ones nobody put in the set, which is why
the set grows — every real failure that gets reported should end up in it before the fix lands, so
the fix is provably a fix and the case cannot silently come back.

He has direct experience of that discipline mattering. On his portfolio assistant the eval caught
a regression he had no reason to expect: writing up a bug in the site's own build log added text
to the indexed corpus that reintroduced the exact matching behaviour the bug was about, dropping
the score from 36/36 to 34/36. Nothing about that failure was predictable by reading the code, and
without a scored suite it would have shipped.

**Follow-up.** *"What is the actual score on the Pulsar eval?"* — Not published here. The
portfolio assistant's is 36/36 and is reproducible by running `eval_retrieval.py` in this repo.

**Grounded in.** Chatbot evaluation set, portfolio assistant eval 36/36, build log bug 05

### Q2.10 — Is this a real production feature or an internal prototype?

- **Difficulty:** sceptical
- **Tags:** production, credibility, scope
- **Asked by:** Hiring Manager, Recruiter

**Answer.**

It is a feature in Pulsar, which is a commercial on-premise product that Venera's customers run.
That is what the resume claims and it is the claim worth testing directly with him rather than
through an assistant.

What supports it: the constraints are the constraints of a shipped product rather than a
prototype. A prototype does not need to run entirely offline inside a customer deployment. A
prototype does not need its generated output validated against a production schema before use. A
prototype does not need an evaluation set covering the requests it must refuse. Those requirements
come from the thing being used by people who are not you.

It is also worth being precise about what is being claimed. It is *a feature in a product*, not an
entire product, and it is his first production generative-AI system. It has been his primary work
since August 2026, which at time of writing is a matter of months rather than years. He has not
maintained it through a model upgrade, a year of accumulated edge cases, or significant drift in
how operators use it — and he would tell you that is where the genuinely hard parts of this job
live.

The site takes a deliberate position on this kind of question: the system prompt for this
assistant instructs it to be honest about his being early-career rather than overselling, and to
decline rather than guess when something is not covered. If an answer here sounds hedged, that is
the design rather than evasion.

**Follow-up.** *"How would you verify it?"* — Ask him what the feature does when an operator's
description is ambiguous. Prototype answers are about the happy path; production answers are
about the edges.

**Grounded in.** Pulsar product, chatbot constraints, current role since August 2026, assistant system prompt

### Q2.11 — What does he own on it day to day?

- **Difficulty:** hiring-manager
- **Tags:** ownership, responsibilities, role, day-to-day
- **Asked by:** Hiring Manager, Recruiter

**Answer.**

Both halves of it — the implementation and the testing — which is an unusual combination and is
the thing most worth understanding about his role.

**On the implementation side:** the retrieval layer over the template corpus and schema, prompt
design and grounding, and the structured-output validation that sits between the model and the
product. That is the pipeline from an operator's sentence to a template that is safe to use.

**On the testing side:** the evaluation set the system is scored against, covering both the
templates it must generate correctly and the requests it must refuse. He wrote it and he maintains
it.

Most teams split those roles, and the usual reason to split them is that the person who built
something is a poor judge of whether it works. His argument for holding both — and it is the same
argument his whole career makes — is that on a generative system the person who understands where
it is likely to be wrong is the person who built it, and the risk of self-assessment is managed by
the eval set being written down and scored rather than performed by intuition. A suite that runs
and produces a number does not care who wrote it.

Alongside that he continues to contribute across the full SDLC on the wider platform — acceptance
criteria, test strategy review, AWS cloud-native release readiness on the Quasar side.

The context that makes the combination make sense: he spent six months doing quality engineering
on this exact platform before building on it. He knew the product, the domain and the release
process before he wrote a line of the feature, which is why he was a reasonable person to hand it
to.

**Follow-up.** *"Is he a QA engineer or a developer now?"* — Developer, on this feature, who owns
its quality. His title is Associate Software Engineer.

**Grounded in.** Implementation and testing ownership, evaluation set, SDLC contributions, prior QA role on same platform

### Q2.12 — How would he approach building something similar for us?

- **Difficulty:** hiring-manager
- **Tags:** approach, methodology, process, transferable
- **Asked by:** Hiring Manager, Engineer

**Answer.**

The sequence he has actually used, which is visible in both the Pulsar work and his own projects:

**1. Find out what wrong looks like, first.** Before anything is built, what does a bad output do
to the user? For Pulsar, an invalid template is caught by validation; a valid template encoding
the wrong intent is not, and it reaches an operator. That distinction determined the architecture.

**2. Write the evaluation set early.** Cases it must get right, and cases it must refuse. Written
before the system is tuned, so it is a target rather than a description of what was built. He is
firm on the refusal half because he has been caught by omitting it.

**3. Establish the cheapest baseline that works.** On his portfolio assistant that meant BM25 over
thirty chunks rather than embeddings and a vector database — the corpus was small enough that the
extra infrastructure bought nothing measurable. On Pulsar the vocabulary gap made embeddings
necessary. The point is that the choice followed from the corpus, and he has a documented example
of choosing the *less* fashionable option because it measured better.

**4. Make grounding structural, not requested.** Retrieve the real material, constrain the output
shape, validate in code. A prompt asking for good behaviour is a preference; a validator is a
property.

**5. Design the failure path before improving the happy path.** This site returns retrieved resume
text directly when every model provider is unavailable, so it degrades rather than erroring.

**6. Measure after every change, including the ones that obviously help.** The regression that
taught him this was one where documenting a bug reintroduced it — entirely invisible without a
scored suite.

What he would want from you before starting: what the failure costs, what data already exists,
and what constraints are non-negotiable. The Pulsar architecture was largely determined by "must
run offline", and knowing that on day one is worth more than a month of exploration.

**Follow-up.** *"What if we do not have an eval set or labelled data?"* — Then building a small
one is the first task, not a blocker. Thirty cases you wrote yourself beats no measurement.

**Grounded in.** Pulsar chatbot approach, portfolio assistant BM25 decision, build log bugs 04 and 05, zero-key fallback design

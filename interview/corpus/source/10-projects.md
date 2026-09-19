# Part 10 — Projects

> Deep dives on the things he has built outside the Venera work. Visitors ask about these to test
> whether a project on a resume is a finished system or a tutorial that got a screenshot. The
> answers include what each one does not do, because that is usually the more informative half.

### Q10.1 — Tell me about the document Q&A chatbot.

- **Difficulty:** engineer
- **Tags:** rag, langchain, pinecone, project, streamlit
- **Asked by:** Recruiter, Engineer, Hiring Manager

**Answer.**

A retrieval-augmented question-answering system over a 200-page knowledge base, with grounded,
citation-friendly answers. The measured result was roughly a 70% reduction in retrieval time across
that corpus.

The stack: a chunking and embedding pipeline building an index in Pinecone as the vector store,
LangChain orchestrating retrieval and generation, the OpenAI API for the model, and Streamlit as the
interface.

The part he treats as the actual work is the grounding pass rather than the plumbing. Answers are
constrained to the retrieved passages, and unsupported responses — output asserting something the
retrieved material does not contain — are tracked as a metric rather than estimated. That distinction
matters: "we told it to stay grounded" is a prompt, and "we measured how often it did not" is
engineering. It is the same instinct that produced the eval sets on everything else he has built.

Where it sits in his record: this is the project that demonstrates the conventional RAG stack —
embeddings, a managed vector database, LangChain, a hosted model. It is the counterpart to the Pulsar
chatbot, which had to do the same job with none of those available, and to this site's original
resume assistant, which deliberately used none of them because its corpus was thirty chunks. Having
built all three is what lets him argue about when each is appropriate rather than defending one as
correct — and the site itself switched to embeddings once its corpus grew and measurement said to.

What it does not have: it is a self-directed project rather than a product, so it has no real users,
no operational history, and no exposure to the failure modes that only appear over time. He would
weight it well below the production work.

**Follow-up.** *"Where did the 70% come from?"* — It is a retrieval-time improvement over the baseline
approach to that corpus, not a claim about answer quality. Worth asking him for the specifics of the
comparison.

**Grounded in.** Document Q&A Chatbot project: 200-page knowledge base, LangChain, OpenAI API, Pinecone, Streamlit, ~70% faster retrieval, unsupported answers tracked

### Q10.2 — What are the NLP pipelines he built with Hugging Face?

- **Difficulty:** engineer
- **Tags:** nlp, hugging-face, transformers, prompt-evaluation
- **Asked by:** Engineer, Recruiter

**Answer.**

Transformer-based text pipelines for classification and summarisation, built on Hugging Face
Transformers — tokenisation, inference, and fine-tuning experiments.

The component he would actually talk about is the prompt-evaluation loop attached to it. Each prompt
variant is scored against a hand-labelled question set, so comparing two prompts produces a number
rather than an impression, and unsupported answers are tracked as a metric. He built it because
iterating on a prompt by running two or three examples and deciding it looks better is close to
worthless — generative output varies enough between runs that a small sample confirms whatever you
already expected.

That loop is the conceptual ancestor of the evaluation sets on everything else: the 36-case retrieval
eval on this site, and the must-generate plus must-refuse evaluation set for the Pulsar chatbot at
work. He describes "learn a technique, then build the thing that tells you whether it is working" as
the most consistent habit across his projects, and this is where it started.

The project also lists LangGraph in its stack as the direction he was extending toward — multi-agent,
stateful workflows — which is the honest positioning: the pipelines are built, the LangGraph part was
exploratory.

What it is not: it is not a trained model, not a published model, and not deployed anywhere with real
traffic. The fine-tuning is described as experiments, which is accurate — he has not run a production
fine-tune and does not claim to.

**Follow-up.** *"How big was the hand-labelled set?"* — Modest, and he would say so. Thirty cases you
wrote yourself is a real measurement; a benchmark it is not.

**Grounded in.** NLP Pipelines with Hugging Face project: classification, summarisation, tokenisation, fine-tuning experiments, prompt-evaluation loop, hand-labelled set, LangGraph

### Q10.3 — Tell me about the Selenium Grid automation project.

- **Difficulty:** recruiter
- **Tags:** selenium-grid, testing, parallel, automation
- **Asked by:** Recruiter, Engineer

**Answer.**

A parallel cross-browser regression suite running across three browsers and two operating systems,
which cut manual cross-browser effort by about 80% and halved pre-release validation time for the
team.

Selenium Grid is the piece that makes this more than a test suite: it distributes test execution
across multiple machines and browser configurations so the suite runs in parallel rather than
sequentially. Cross-browser testing is the case where that matters most, because the same suite has
to run N times against N configurations, and run serially that is N times the wall-clock cost.

The engineering judgement in it is about what to parallelise and how to keep tests independent. Tests
that share state — a fixture, a user account, a database row — cannot run concurrently without
flaking, and a flaky parallel suite is worse than a slow serial one because people stop trusting it.
So the work is as much about test isolation as about the grid configuration.

Where this fits his story: it is quality engineering rather than AI work, and he keeps it on the
resume because the pattern generalises. Halving pre-release validation time is the same category of
contribution as the 65% manual regression reduction — making the safe path fast enough that people
take it. Quality work that is experienced as friction gets routed around, and the way to prevent that
is to make checking cheap.

He would rank this below the AI projects in relevance for an AI engineering role, and above them in
demonstrating that he has shipped infrastructure that a team depended on daily.

**Follow-up.** *"Is Selenium relevant to AI work?"* — Not directly. The transferable parts are test
isolation, parallel execution and the judgement about what is worth automating.

**Grounded in.** Selenium Grid Automation project: 3 browsers, 2 operating systems, -80% manual cross-browser effort, halved pre-release validation

### Q10.4 — What are the older projects — the chat app and the Java CRUD system?

- **Difficulty:** recruiter
- **Tags:** android, kotlin, java, early-projects
- **Asked by:** Recruiter

**Answer.**

Both pre-date his move toward AI work and he keeps them on the resume as evidence of range rather
than as current skills.

**The real-time chat app** is an Android application in Kotlin with Firebase as the realtime backend,
with secure authentication and sub-second message sync, verified stable under concurrent multi-user
load. It connects to his NullClass internship, which was Android development — building and optimising
mobile applications, UI performance tuning, Firebase integration and mobile SDLC delivery.

**The student data entry system** is a Java servlet CRUD application over MySQL, where optimising the
JDBC queries reduced average database response time by 30%.

Their honest relevance to an AI engineering role is limited, and he would say so. What they show is
that he has built working software in more than one language and paradigm — mobile, backend, database
— before specialising.

There is one thing worth knowing about these two specifically, which is that they are the reason his
retrieval eval set exists. Someone asked his assistant "what has he actually shipped with LLMs?" and
it returned exactly these two projects — a Kotlin chat app and a Java CRUD app. The cause was
unweighted query expansion letting broad synonyms match every project chunk equally while the one
discriminating term was outvoted. He wrote an eval set of 29 questions, reproduced the failure at
26/29, and fixed the scoring until it reached 29/29. So these two projects are, indirectly, why every
retrieval change on this site is now scored.

**Follow-up.** *"Would he still write Kotlin or Java?"* — He has both on his skills list and would not
claim current depth in either. Python is his primary language by a wide margin.

**Grounded in.** Real-Time Chat App and Student Data Entry System projects, NullClass internship, build log bug 02, eval progression 26/29 to 29/29

### Q10.5 — Which project is he proudest of, and why?

- **Difficulty:** behavioural
- **Tags:** projects, motivation, self-assessment
- **Asked by:** Hiring Manager, Recruiter

**Answer.**

The Pulsar template-generation chatbot at Venera, because it shipped into a product with constraints
he did not choose and consequences he did not control.

His reasoning, which is worth stating because it says something about how he evaluates work: a side
project is built on the stack its author picked, targeting requirements its author set, and judged by
its author. The Pulsar feature had to run offline inside an on-premise deployment, on models small
enough for customer hardware, producing output conforming to a schema he did not design, for operators
whose failure case is running quality control with checks they did not ask for. Working inside that is
most of the engineering.

The runner-up is this site, for a different reason: it is where he got to make every decision and
document the reasoning, including the ones that went against convention. Choosing BM25 over embeddings
because the corpus is thirty chunks. Nine model providers behind one adapter so a rate limit on one is
invisible. A system that answers with zero API keys configured. And a published log of twelve bugs
that shipped broken before he caught them — including one where writing up a bug reintroduced it.

He would say the build log is the part he is most pleased with, which is an unusual thing to be proud
of. The argument is that a portfolio of things that worked says nothing about how someone handles
things that do not, and that publishing the failures is a hedge against overclaiming. It also means
the site's central claim — that he measures rather than assumes — is testable rather than asserted,
because the eval is in the repository and you can run it.

**Follow-up.** *"Which taught him the most?"* — The eval set, across all of them. Every significant
thing he has learned about retrieval came from a number moving in a direction he did not predict.

**Grounded in.** Pulsar chatbot constraints, portfolio assistant design decisions, build log (12 bugs), eval_retrieval.py

### Q10.6 — How much of this site did he actually build?

- **Difficulty:** sceptical
- **Tags:** portfolio, authorship, credibility
- **Asked by:** Engineer, Hiring Manager

**Answer.**

The source is public, which is the real answer — it is on GitHub and the reasoning is documented in
the code rather than only in the write-up.

What is in it: a Flask application, a BM25 retrieval index built in-process over chunks derived from
a single profile module, nine model provider adapters behind one interface with automatic failover,
a prompt and grounding layer, a 36-case retrieval evaluation suite, a front end in vanilla JavaScript
with no framework, and deployment configuration for four hosting platforms. Roughly three thousand
lines.

The signals that it is genuinely his, if you want to check rather than take it on trust:

- **The comments explain decisions, not syntax.** They cluster exactly where the correct-looking thing
  is wrong — the template variable that must be accessed by key because attribute access resolves a
  built-in method, the synonym weight that must stay below 1.0 so an expansion cannot outvote a typed
  term, the breakpoint branch in the sidebar handler.
- **The build log documents twelve bugs with cause and fix**, including embarrassing ones. Bug 10 is a
  button that had never worked on desktop. Bug 11 is a status badge that displayed a provider name
  while a different engine was answering.
- **The eval set is runnable.** `python eval_retrieval.py` reproduces the 36/36 claim, and it prints
  the two cases it does not pass cleanly along with why.
- **The statistics on the page are computed at boot** from the real index and the real test suite,
  because hand-written ones drifted three times.

What he had help with elsewhere: the Pulsar feature at work was built alongside an external AI
consultant, and the resume says so. This site is his.

**Follow-up.** *"Can I break the assistant?"* — There is a button on the About page that invites you
to try. Ask it something the resume does not cover and it should decline.

**Grounded in.** Public GitHub repository, ~3000 lines, build log bugs 01, 10 and 11, eval_retrieval.py, computed About statistics

### Q10.7 — What would he build next?

- **Difficulty:** engineer
- **Tags:** roadmap, future, improvement
- **Asked by:** Engineer, Hiring Manager

**Answer.**

The published roadmap for this site, plus what the Pulsar work exposed as gaps.

**On this site**, listed publicly as unfinished rather than claimed as done:

- **Hybrid retrieval** — BM25 plus embeddings — once the corpus grew past a few hundred chunks. That
  threshold has now been crossed by the interview corpus, and the retrieval over it is hybrid, so this
  one is done and the rest are not.
- **Wire the eval into CI** so a bad retrieval change cannot merge. It already exits non-zero for
  exactly this purpose; it is not automated yet, and a check that depends on someone remembering will
  eventually not run.
- **Stream tokens to the client** rather than waiting for the full response. A user-experience gap
  rather than a correctness one.

**Beyond it**, the things he would want to build to close real gaps in his experience:

- **A reranker in a production path.** He has not had one; it is the single highest-value addition to
  most RAG systems and his corpora have been small enough to avoid needing it, which is a reason
  rather than an excuse.
- **A real fine-tune with a proper before-and-after evaluation.** He has built the dataset and eval
  scaffolding and run experiments; he has not taken one to production.
- **An agent with actual tool access**, with the permission and cost controls that requires. His
  current graph has no side effects, which is what makes it safe, and that is also why it does not
  teach him the hard parts.

The pattern in that list is that he names what he has not done rather than what he would like to
demonstrate — which is consistent with a site whose main feature is a published log of its own bugs.

**Follow-up.** *"Why has he not done the CI wiring already?"* — No reason he defends. It is listed as
a gap.

**Grounded in.** Site roadmap (hybrid retrieval, eval in CI, streaming), interview corpus hybrid retrieval, no reranker in production, fine-tuning limits

### Q10.8 — Do his projects have real users?

- **Difficulty:** sceptical
- **Tags:** users, production, scale, honesty
- **Asked by:** Hiring Manager, Engineer

**Answer.**

One does. The rest do not, and that distinction is the right way to weigh them.

**The Pulsar template-generation chatbot** is a feature in a commercial product that Venera's customers
run. Operators use it. That is the only one of his systems with users who did not choose to look at
his portfolio.

**This site** has visitors — recruiters and engineers, which is the intended audience — and at least
one reported bug came from a real user rather than from testing: long answers opened scrolled to their
last line, so you landed on the closing sentence and had to scroll back up. That is logged as bug 09
and credited as user-reported. So there is some real usage signal, but it is a portfolio, not a
service.

**The document Q&A chatbot, the NLP pipelines and the Selenium work** are self-directed or internal.
The Selenium Grid suite was used by the team daily, which is a form of real usage — infrastructure
other people depended on — but not external users.

Why he would rather state this plainly than blur it: a system with users behaves differently from one
without. Users ask things you did not anticipate, use it in ways you did not design for, and surface
the failure modes that only appear over time. He has had a small amount of that, and he has not had
the experience of maintaining a system through a year of accumulated edge cases and drift, which he
names as where the genuinely hard parts of this work live.

**Follow-up.** *"How much traffic does the site get?"* — Not instrumented in a way that is published,
and he would rather say that than quote a number.

**Grounded in.** Pulsar chatbot in commercial product, build log bug 09 (user-reported), Selenium Grid team usage, experience level

### Q10.9 — What is the most technically interesting thing he has built?

- **Difficulty:** engineer
- **Tags:** technical-depth, design, retrieval, interesting
- **Asked by:** Engineer

**Answer.**

The retrieval layer on this site, which sounds like the least impressive option and is the one with
the most actual engineering in it.

The naive version is BM25 over resume chunks. The interesting problem is that it does not work, for a
reason that is specific and generalises: recruiters ask "can he do X" while a resume says "built X".
The vocabulary of hiring and the vocabulary of a CV barely overlap, so lexical matching fails on
exactly the questions that matter most.

What he built to close that gap, each piece added because the eval caught a failure:

- **Light suffix stemming**, so "LLMs" matches "LLM" and "hallucinating" matches "hallucination",
  with a minimum stem length so short technical tokens like "aws" and "api" survive intact.
- **Phrase normalisation**, collapsing known multi-word terms to a canonical token *before*
  tokenising. This exists because "large language model" was matching his *programming languages*
  list — token overlap with no meaning overlap.
- **Weighted query expansion.** A synonym layer maps hiring language onto resume vocabulary, but
  expansions carry 0.3 weight against 1.0 for terms the visitor actually typed. Unweighted, a broad
  synonym like "shipped" expanding to "project" matched every project chunk equally and drowned out
  the single discriminating term.
- **Doubled title and tag tokens**, so a tag match outweighs an incidental body match — but only 2×,
  because some tags are shared across a whole category and carry no discriminating signal.
- **Empty as an honest return value.** Retrieval returns nothing when nothing matches, rather than
  substituting defaults, because that empty result is the only signal meaning "not covered".

Every one of those is a small decision with a documented reason and a test case. That is the part he
finds interesting: the system is a few hundred lines and almost all of it is judgement.

**Follow-up.** *"Why not just use embeddings?"* — Because at thirty chunks it would have added a
network hop, a cold start and a bill for recall he could not measure a gain from. The vocabulary gap
was the real problem, and embeddings would not have fixed the phrase-sense failure either.

**Grounded in.** core/rag.py (stemming, phrase normalisation, 0.3 expansion weight, doubled tags, empty returns), build log bugs 02, 03 and 04

### Q10.10 — How do his projects connect to each other?

- **Difficulty:** hiring-manager
- **Tags:** narrative, progression, coherence
- **Asked by:** Hiring Manager, Recruiter

**Answer.**

Three retrieval systems with three different architectures, and a measurement habit that carries
through all of them.

**The progression.** The document Q&A chatbot is the conventional stack — embeddings, Pinecone,
LangChain, a hosted model. This site's resume assistant was the opposite: no embeddings, no vector
database, no framework, no required API key, because its corpus was thirty chunks and the
conventional stack would have added cost and failure modes for unmeasurable gain. When the site's
corpus grew to 163 questions and answers, keyword search found the right answer for under half of reworded questions and
embeddings for about nine in ten, so the live assistant now leads with embeddings — same principle, different
corpus, different answer. The Pulsar chatbot at work is a third
point — embeddings and a vector store, but everything running locally inside an on-premise deployment
because no outbound call is permitted.

Having built all three is what makes his opinions about retrieval architecture arguments rather than
preferences. He can say when a vector database is worth it because he has chosen for and against one
on defensible grounds.

**The habit.** Every one of them has an evaluation set. The prompt-evaluation loop on the NLP
pipelines scores prompt variants against a hand-labelled question set. This site has 36 retrieval
cases, seven of which assert that nothing should be retrieved. The Pulsar chatbot has a set covering
both what it must generate and what it must refuse. That is consistent enough across independent
projects to be a trait.

**The QA thread underneath.** The failure path is designed before the happy path in all of them — this
site answers with zero API keys, the Pulsar chatbot refuses rather than guessing, and the document
Q&A project tracks unsupported answers as a metric. That is the six months of quality engineering
showing up in the architecture rather than in a bullet point.

**Follow-up.** *"Is the coherence deliberate or retrospective?"* — The eval sets predate the site's
write-up, and the build log is dated by the bugs it describes. Worth judging from the repository
rather than the narrative.

**Grounded in.** Document Q&A (Pinecone/LangChain), portfolio assistant (BM25, no deps), Pulsar chatbot (local embeddings), three eval sets, failure-path designs

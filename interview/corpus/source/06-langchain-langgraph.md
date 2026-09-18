# Part 6 — LangChain and LangGraph

> He has shipped with LangChain and is actively building with LangGraph. The distinction matters
> and these answers keep it: the document Q&A chatbot is a finished LangChain project with a
> measured result, while LangGraph is where he is currently extending. The assistant answering
> this question runs a LangGraph agent over the interview corpus, so it is also a live example.

### Q6.1 — What has he built with LangChain?

- **Difficulty:** recruiter
- **Tags:** langchain, projects, rag, pinecone
- **Asked by:** Recruiter, Engineer

**Answer.**

The document Q&A chatbot, which is the clearest finished example.

That project answers questions over a 200-page knowledge base. LangChain orchestrates the pipeline:
the chunking and embedding stage that builds the index, retrieval against Pinecone as the vector
store, and the generation call to the OpenAI API with retrieved passages as context. It is served
through Streamlit. The measured result was roughly a 70% reduction in retrieval time over that
corpus.

The part he emphasises is not the framework usage but the grounding pass: answers are constrained
to the retrieved passages, and unsupported responses — where the output asserts something the
retrieved material does not contain — are tracked as a metric rather than estimated. That is the
same instinct that produced the eval sets on everything else he has built.

He also uses LangChain-style composition in the assistant backing this page. The pipeline is
expressed as a chain — retrieve, format context, build the prompt, call the model, parse the
answer — which is the LangChain Expression Language shape. There is a deliberate design choice
there worth knowing about: this site has to run when nothing is installed except Flask, so the
chain runs on real LangChain when it is available and on a small stdlib-only implementation of the
same interface when it is not. Same pipeline definition either way.

What he would not claim: deep experience with LangChain's broader surface area — the agent
toolkits, the document loader ecosystem, LangSmith in a team setting. He has used the parts that
build a retrieval pipeline.

**Follow-up.** *"Is LangChain necessary for a RAG system?"* — No, and he would say so. This site's
resume assistant does retrieval and generation in a few hundred lines with no framework at all. The
framework earns its place when you need composition, streaming and swappable components.

**Grounded in.** Document Q&A Chatbot project (LangChain, OpenAI, Pinecone, Streamlit), 70% retrieval improvement, interview assistant chain

### Q6.2 — What does he think of LangChain as a framework?

- **Difficulty:** engineer
- **Tags:** langchain, opinions, abstractions, trade-offs
- **Asked by:** Engineer, Hiring Manager

**Answer.**

Useful where it composes, a liability where it hides things, and the judgement is about which mode
you are in.

What it genuinely gives you: a common interface across models and vector stores so swapping a
component is a line rather than a rewrite; composition that makes a pipeline readable as a pipeline
rather than as nested function calls; streaming, batching and async handled once rather than per
project; and a large ecosystem of integrations so you are not writing yet another PDF loader.

What he is wary of, from having used it:

**Abstraction over a thin thing.** A RAG pipeline is retrieve, assemble, call, parse. That is not
complicated, and wrapping it in framework types can make it harder to see what is actually sent to
the model. When a RAG system gives a wrong answer the first thing you need is the assembled prompt,
verbatim, and a framework that makes that hard to inspect is costing you more than it saves.

**Debuggability.** Deep call stacks through generic runnables are harder to reason about than a
function you wrote. He mitigates this by logging the assembled prompt and the retrieved chunk ids,
which is the thing that actually makes RAG debuggable.

**Version churn.** The API has moved substantially, and code written against an older version is
often not a small upgrade.

**Dependency weight.** Relevant to him specifically — this site deploys on a free tier, and pulling
in a large dependency tree for something a few hundred lines can do is a real cost. It is why the
resume assistant uses no framework and why the interview pipeline can run without one.

His summary: use it when you want composition and swappability, skip it when the pipeline is fixed
and small, and either way make sure you can see the final prompt.

**Follow-up.** *"Does he prefer writing it himself?"* — For something small and fixed, yes, and this
site is the evidence. For anything that needs to swap models and stores, the framework wins.

**Grounded in.** Document Q&A Chatbot with LangChain, portfolio assistant no-framework design, free-tier deployment constraints

### Q6.3 — What is LangGraph and how is it different from LangChain?

- **Difficulty:** engineer
- **Tags:** langgraph, agents, state, control-flow
- **Asked by:** Engineer

**Answer.**

LangChain composes a pipeline; LangGraph composes a state machine. The difference is loops and
branching.

A LangChain chain is a directed acyclic pipeline — input goes in, passes through stages, output
comes out. That covers most RAG, and it is the right shape when the steps are known in advance.

LangGraph models the workflow as a graph with explicit nodes, explicit state, and **conditional
edges** — so the path through it is decided at runtime by the state, and it can cycle. That is what
you need when a step's outcome determines what happens next: retrieve, judge whether the retrieved
material is good enough, and if not rewrite the query and retrieve again before generating.

The pieces that matter:

- **State is explicit and typed.** Every node receives the state and returns an update to it, and
  the graph defines how updates merge. Compared to passing a growing dictionary between functions,
  that makes the data flow legible and the whole run inspectable.
- **Conditional edges** route based on state, which is how you express "retry" or "escalate" or
  "this is good enough".
- **Cycles with a recursion limit**, so a loop that never converges terminates rather than running
  up a bill.
- **Checkpointing**, so a run's state can be persisted, resumed, or interrupted for human approval.

The practical reason he cares: it makes the agent's trace a first-class artifact. Because every node
writes to shared state, you get a record of which path a request took and why, which is exactly what
you need to debug a system whose behaviour is not deterministic. On the assistant backing this page
the graph's node trace is available with the answer.

**Follow-up.** *"Could you build this without LangGraph?"* — Yes, and it is a few hundred lines. The
framework buys you the state-merge semantics, the checkpointing and the recursion guard rather than
anything you could not write.

**Grounded in.** Interview assistant LangGraph agent, LangGraph in skills list and certifications, exploring LangGraph for stateful workflows

### Q6.4 — Has he actually used LangGraph, or is it aspirational?

- **Difficulty:** sceptical
- **Tags:** langgraph, honesty, experience, limits
- **Asked by:** Hiring Manager, Engineer

**Answer.**

Both, and the resume says so — it lists LangGraph under "exploring" for the self-directed work
rather than claiming production depth.

The honest state of it:

**What is real and running:** the assistant answering this question routes through a LangGraph
agent over the interview corpus. It is a genuine stateful graph — route the question, retrieve,
grade whether the retrieved material actually supports an answer, rewrite the query and retrieve
again if not, generate, verify the answer against its citations, and either finish or retry within
a bounded number of iterations. The node trace is available with the response, so you can see which
path your question took.

**What is training:** LangGraph is part of the AI Engineer Bootcamp 2026 syllabus he is working
through.

**What is not true:** he has not shipped a LangGraph agent in a commercial product. The production
generative-AI work at Venera — the Pulsar template chatbot — is a RAG pipeline rather than an agent
graph, and he has not run a multi-agent system under real load.

He would also be straight about the scale of what "agent" means here. The graph on this site has a
handful of nodes and one retry loop. It is not an agent with tool access, external side effects or
autonomous multi-step planning, and those are where the genuinely hard problems live — permissions,
cost control on runaway loops, and failure modes that compound across steps.

So: real working code you can interrogate, on a personal system, not production experience. Anyone
hiring for deep agent experience should treat this as competence rather than expertise.

**Follow-up.** *"What would you ask to test it?"* — Ask what his graph does when retrieval comes back
weak twice in a row. The answer is specific: it stops rather than looping, and returns a refusal.

**Grounded in.** Interview assistant LangGraph agent, AI Engineer Bootcamp syllabus, "exploring LangGraph" on resume, Pulsar chatbot architecture

### Q6.5 — Describe the agent graph running on this site.

- **Difficulty:** engineer
- **Tags:** langgraph, architecture, agent, self-referential
- **Asked by:** Engineer

**Answer.**

It is a stateful graph over the interview corpus, and the design is deliberately conservative —
loops are bounded and every path terminates in either an answer or a refusal.

The state carries the question, the queries tried so far, retrieved documents, an attempt counter,
the draft answer, its citations, and a trace of nodes visited.

The nodes:

**Route.** Decides whether the question is in scope at all. Questions with no plausible match go
straight to a refusal without spending a model call — the same principle as the resume assistant,
where declining deterministically is both cheaper and more correct.

**Retrieve.** Hybrid retrieval over the corpus: a lexical pass and a semantic pass, fused by rank.
Both run in-process with no external service.

**Grade.** Judges whether what came back actually supports an answer. This is the node that makes it
a graph rather than a chain — its outcome determines the next edge.

**Rewrite.** If grading fails, reformulate the query and retrieve again. This is the cycle, and it is
capped. Two failed attempts ends in a refusal rather than a third try, because a system that keeps
trying is a system that eventually produces something regardless of whether it should.

**Generate.** Produce the answer constrained to the retrieved passages.

**Verify.** Check the answer's claims against the citations it carries. A claim that is not supported
sends it back or triggers a refusal.

The reason for the verify node specifically: the failure mode of this whole class of system is a
fluent answer that is not supported by its sources, and the only defence is checking rather than
trusting. It is the same reasoning behind validating generated templates against the schema on the
Pulsar chatbot.

The trace of which nodes ran is returned with the answer, which turns an opaque generation into
something you can inspect.

**Follow-up.** *"What happens when the model provider is down?"* — It degrades to returning the
retrieved corpus material directly, the same as the resume assistant. The graph runs; only the
generation node has a fallback.

**Grounded in.** Interview assistant graph design, hybrid retrieval, bounded retry, portfolio assistant refusal and fallback design

### Q6.6 — When is an agent the wrong architecture?

- **Difficulty:** engineer
- **Tags:** agents, architecture, over-engineering, judgement
- **Asked by:** Engineer, Hiring Manager

**Answer.**

Most of the time, and he would say the industry is currently over-applying it.

An agent is worth the complexity when the sequence of steps genuinely cannot be determined in
advance — when what to do next depends on what the previous step found. If you can draw the pipeline
on a whiteboard and it does not have a decision point in it, it is a chain, and expressing it as an
agent adds state management, non-determinism and a class of failure (loops that do not terminate)
for nothing.

Where he would argue against it:

**Fixed pipelines.** Retrieve, ground, generate, validate. That is the Pulsar chatbot and it is not
an agent, deliberately. The steps are known, so a graph would add moving parts to a system whose
main requirement is predictability.

**Anything where latency matters.** Each agent iteration is at least one model round trip. A
three-iteration loop is three times the latency and three times the cost of a single call, on an
interactive path where the user is waiting.

**Anything with real side effects and no supervision.** An agent that can send, delete, or spend
turns a reasoning error into a real-world action. That needs least privilege, allow-listed tools,
typed arguments and human confirmation for anything irreversible — and he has not built one with
those properties, so he would not propose one lightly.

**When you cannot bound the cost.** An unbounded loop is a denial-of-wallet incident. Every cycle
needs an iteration cap, and his own graph caps at two retries for exactly that reason.

Where an agent does earn it: retrieval that may need reformulation, tasks that decompose into
sub-tasks of unknown number, and workflows with genuine branching. The graph on this site qualifies
narrowly — it has one real decision point, whether the retrieved material is good enough.

His general position: start with the chain, and add the graph when you find the decision point that
justifies it. Not the other way round.

**Follow-up.** *"Why is the site's assistant a graph then?"* — Because query rewriting on weak
retrieval is a real decision point, and because a portfolio is a reasonable place to demonstrate the
technique. He would flag that as a legitimate reason and not pretend it was purely necessity.

**Grounded in.** Pulsar chatbot chain architecture, interview assistant graph with bounded retry, no-tool design

### Q6.7 — How does he handle state in a multi-turn conversation?

- **Difficulty:** engineer
- **Tags:** state, conversation, history, context-management
- **Asked by:** Engineer

**Answer.**

Explicitly, with bounds, and with an awareness that conversation history is the easiest place to
leak data between users.

On this site the history is client-supplied and then sanitised server-side before use: trimmed to
the last eight turns, each message capped in length, roles validated to be user or assistant, and
leading assistant turns dropped so the conversation always opens with a user message — which every
provider requires. Nothing is trusted because it arrived in the request body.

The bound exists for three reasons: cost, since history is re-sent on every request and grows
without limit otherwise; the lost-in-the-middle effect, where a long history pushes the actually
relevant material into the part of the context the model uses least reliably; and the hard limit of
the context window.

The design decision he would highlight is what happens on a follow-up with no new retrieval match.
A question like "how long did that take?" is legitimate mid-conversation and retrieves nothing,
because it has no content words. Declining it would be wrong. So the system distinguishes the two
cases: with no history and no retrieval match it refuses deterministically without a model call;
with history it lets the model try, but states plainly in the prompt that the corpus returned
nothing this turn and instructs it not to substitute unrelated material. That nuance exists because
an earlier version got it wrong in the other direction.

In the LangGraph agent, state is the graph's own typed state object rather than an ad-hoc dict,
which makes what is carried between nodes explicit and inspectable.

The thing he would warn about in any shared system: conversation state keyed per session and never
evicted is both a memory leak and a data-leak risk. Bounds are not optional.

**Follow-up.** *"Is conversation history stored server-side?"* — On this site, no. It is sent by the
client each turn and the server holds nothing between requests, which is the simplest way to avoid
cross-session leakage.

**Grounded in.** _normalise_history in core/llm.py, MAX_HISTORY_TURNS of 8, follow-up handling, build log bug 04

### Q6.8 — What is the value of the node trace the agent returns?

- **Difficulty:** engineer
- **Tags:** observability, debugging, trace, transparency
- **Asked by:** Engineer, Hiring Manager

**Answer.**

It turns a non-deterministic system into one you can actually debug, which is the single biggest
practical problem with this class of software.

When a RAG or agent system gives a bad answer, the question is which stage failed — and without a
trace, every hypothesis is equally plausible and people default to blaming the prompt. With one you
can see whether routing sent it to a refusal, whether retrieval came back empty, whether grading
rejected the first attempt and the rewrite helped, and whether verification passed. That collapses
the search space immediately.

He has direct experience of this mattering. The assistant on this site reports which provider
actually produced each answer, and that is how he found bug 08: with a valid key configured, the
health check reported the engine live while every answer was silently coming from the local
extractive fallback, because the HTTP layer was sending Python's default user-agent and the CDN in
front of the provider was rejecting it outright. The graceful fallback was hiding a total failure.
He only noticed because the answers named their own source.

The generalisation he took from that: **make the system report what it actually did, not what it was
configured to do.** A health check that confirms a key is present is not a health check. The same
reasoning is why the status badge on this page is corrected from the first real answer rather than
rendered from config, and why the trace is returned with the response here.

For a portfolio there is a second benefit: it makes the engineering visible. A visitor can see that
the answer came from retrieval over specific corpus sections rather than from a model's memory,
which is a claim the site would otherwise just be asserting.

**Follow-up.** *"Would you return the trace to end users in a real product?"* — Usually not; it is an
internal artifact. Here it is deliberate, because demonstrating how it works is the point.

**Grounded in.** Build log bugs 08 and 11, engine status reporting, interview agent trace, source citations

### Q6.9 — How would he choose between LangChain, LlamaIndex and writing it himself?

- **Difficulty:** engineer
- **Tags:** frameworks, tooling, decision-making, trade-offs
- **Asked by:** Engineer, Hiring Manager

**Answer.**

By how much of the pipeline is going to change, which is the question that actually decides it.

**Write it yourself** when the pipeline is fixed and small. A RAG system is retrieve, assemble, call,
parse — that is a few hundred lines you fully understand, with no dependency tree, no version churn
and a prompt you can see. This site's resume assistant is exactly that: BM25 retrieval, provider
adapters and prompt assembly in three modules, no framework, and it deploys on a free tier because
it weighs almost nothing. He would defend that choice for that system without hesitation.

**LangChain** when you need composition and swappability — several models, several stores, streaming,
async, and a pipeline whose shape will change. That is what the document Q&A chatbot needed.

**LlamaIndex** when the hard part is ingestion and indexing rather than orchestration: many document
formats, hierarchical or multi-index retrieval, and document-centric abstractions. It is the more
opinionated tool for the retrieval half specifically.

The factors he would actually weigh: how much of this is genuinely mine versus boilerplate; can I see
the final prompt without fighting the abstraction; what does this add to the deployment footprint;
and how stable is the API, because a framework that moves fast becomes a migration project.

The position he holds most firmly is that the framework question is usually less important than
people make it, because it is not where the quality comes from. Whether a RAG system works is
determined by chunking, retrieval quality, grounding and evaluation — and every framework lets you
do those well or badly. Choosing the framework first is optimising the part that matters least.

**Follow-up.** *"Does he regret using LangChain anywhere?"* — He would say the resume assistant was
right to avoid it and the document Q&A project was right to use it, which is a reasonable record.

**Grounded in.** Document Q&A Chatbot with LangChain, portfolio assistant framework-free design, free-tier deployment, Pulsar architecture

### Q6.10 — How does the site run LangGraph on a free hosting tier?

- **Difficulty:** engineer
- **Tags:** deployment, dependencies, free-tier, architecture
- **Asked by:** Engineer

**Answer.**

By checking the actual numbers rather than assuming, and then building a fallback anyway.

The assumption people make is that LangChain and LangGraph are too heavy for a serverless free tier.
He measured the real dependency closure — langgraph plus langchain-core and everything they pull in
— at about 38 MB unzipped, against a 250 MB serverless limit. So the assumption was wrong, and the
live site runs genuine LangChain and LangGraph rather than a simulation of them.

The design decision layered on top is the one worth explaining. This site's stated principle is that
it never hard-fails: it answers questions with zero API keys configured, because retrieval is local
and the fallback returns resume text directly. Introducing a hard dependency on two packages would
have broken that property — `python app.py` with only Flask installed would stop working.

So the chain and the graph are written against a thin interface, with two implementations behind it:
real LangChain and LangGraph when they are importable, and a small stdlib-only executor with the same
semantics when they are not. The pipeline definition is the same code either way; only the engine
underneath changes. Both paths are exercised by the test suite, so the fallback is not a claim.

He would describe this as the same pattern as the provider chain on the resume assistant — nine model
vendors behind one adapter, first working one wins, degrade to local extraction if all fail. Design
the failure path first, then make the happy path better than it.

The cost of the pattern, to be fair: it is more code than just depending on the library, and the
shim has to be kept honest with tests. It is justified here because graceful degradation is the
site's explicit thesis, and would be over-engineering in a system that could simply require its
dependencies.

**Follow-up.** *"Is the fallback a real implementation or a stub?"* — Real, and tested against the
same pipeline definition. The point is that the graph produces the same answer either way.

**Grounded in.** Measured 38 MB dependency closure, zero-key fallback principle, nine-provider chain, graceful degradation design

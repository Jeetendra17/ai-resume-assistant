# Part 3 — RAG and Retrieval

> Technical questions about retrieval, answered through what he has actually built rather than
> as definitions. He has shipped three distinct retrieval systems — an embedding-based one inside
> a production on-premise product, a Pinecone-backed one over a 200-page corpus, and a
> dependency-free lexical one running on this page — and the interesting part is that they use
> three different techniques for defensible reasons.

### Q3.1 — Explain RAG as he would, based on what he has built.

- **Difficulty:** engineer
- **Tags:** rag, retrieval, grounding, architecture
- **Asked by:** Engineer, Hiring Manager

**Answer.**

A language model knows what was in its training data and nothing about your documents. RAG fixes
that by retrieving the relevant material at question time and putting it in the model's context,
so the answer is generated from your content rather than from its memory.

The pipeline is four steps: chunk your corpus into retrievable pieces, index them, retrieve the
pieces relevant to a question, and generate an answer constrained to what was retrieved.

The way he would frame it from experience is that the interesting work is almost entirely in step
three, and most teams spend their time on step four. When a RAG system gives a wrong answer, the
instinct is to rewrite the prompt. In his experience the prompt is usually fine and the model was
handed the wrong passages — no amount of instruction fixes context that does not contain the
answer.

The second thing he would emphasise is that RAG buys you two properties beyond knowledge:
**citability** and **the ability to decline**. Because the answer is grounded in specific
retrieved passages, you can show which ones, and a user can check. And because retrieval can come
back empty, the system has a signal meaning "the corpus does not cover this" — which is the only
way to build something that says "I don't know" reliably rather than generating something
plausible.

He learned that second point the hard way on this site. An early version substituted default
chunks when retrieval scored nothing, so there was always something to answer from. That destroyed
the only signal meaning "not covered", and a question about his hobbies came back with his career
summary attached, reading as though it had answered. Retrieval returns empty now and the app
declines before any model call.

**Follow-up.** *"Does RAG eliminate hallucination?"* — No. It reduces it and introduces two new
failure modes: the model ignoring correct retrieved context, and answering confidently from
context that was retrieved wrongly. Retrieval quality becomes the dominant variable.

**Grounded in.** Pulsar chatbot RAG pipeline, portfolio assistant retrieval, build log bug 04

### Q3.2 — Why does this site use BM25 instead of embeddings?

- **Difficulty:** engineer
- **Tags:** bm25, embeddings, retrieval, trade-offs, cost
- **Asked by:** Engineer, Hiring Manager

**Answer.**

Because the corpus is thirty short chunks, and at that size embeddings would add an API round
trip, a cold start and a bill in exchange for a recall improvement he could not measure.

The reasoning he documented:

- **Latency.** BM25 runs in-process in about 0.04 milliseconds, measured over 2,900 runs. An
  embedding call is a network hop.
- **Failure modes.** A local lexical index cannot be rate-limited, cannot be down, and does not
  need a key. This site answers questions with zero API keys configured because retrieval never
  depends on the network.
- **Cost.** No vector database, no embedding API, no bill.
- **The actual problem was not similarity.** The hard part was that recruiters ask "can he do X"
  while a resume says "built X". That is a vocabulary gap, and he closed it with stemming, phrase
  normalisation and a weighted synonym layer that maps hiring language onto resume vocabulary —
  cheaper and far more targeted than reaching for a bigger model.

What makes this a defensible answer rather than a rationalisation is that he chose differently on
the Pulsar chatbot at work, where the corpus is larger and the vocabulary gap between how an
operator describes their intent and how the schema encodes it is genuinely semantic. That one uses
embedding-based retrieval over a vector store. Same engineer, opposite choice, because the corpora
are different.

He is also explicit about when this decision expires. The site's own roadmap says to move to
hybrid retrieval — BM25 plus embeddings — once the corpus grows past a few hundred chunks, and the
interface is already shaped for it. The interview corpus you are reading is precisely that growth,
which is why the retrieval built over it is hybrid rather than lexical alone.

**Follow-up.** *"Is BM25 not just keyword matching?"* — It is lexical, but it weights terms by
inverse document frequency and normalises for document length, so a rare discriminating term
outweighs a common one. That is why the weighted synonym layer mattered: unweighted expansion let
broad synonyms outvote the one term that discriminated.

**Grounded in.** Portfolio assistant BM25 design, 0.04 ms measurement, 30 chunks, synonym layer, Pulsar embedding retrieval

### Q3.3 — How does he decide on chunk size?

- **Difficulty:** engineer
- **Tags:** chunking, retrieval, evaluation, tuning
- **Asked by:** Engineer

**Answer.**

By measuring it, which sounds obvious and is uncommon — chunk size is usually picked once from a
blog post and never revisited.

His position is that chunk size is a hyperparameter of the retrieval system and should be tuned
against a retrieval eval set like any other. The trade-off is legible: chunks that are too small
lose the context that makes a passage meaningful, so a retrieved fragment refers to a subject
resolved in the previous chunk. Chunks that are too large dilute the signal — the passage matches
on something incidental, and the part that actually answers the question is buried among
paragraphs that are not about it, where the lost-in-the-middle effect means the model may not use
it.

What he does in practice:

- **Split on structure, not on character count.** Headings, paragraphs, list items. A split that
  respects the document's own boundaries produces chunks that are about one thing, which is the
  actual goal — fixed-width splitting is a proxy for it and a poor one.
- **Keep the unit of meaning intact.** On this site each chunk is one coherent thing: a job, a
  project, a skill group, a design decision. On the interview corpus each chunk is one question and
  its answer, because that is the unit a visitor's question maps to.
- **Overlap only where splitting was forced.** Overlap is a patch for having cut something that
  should not have been cut; if structure-aware splitting is doing its job, you need less of it.
- **Measure in tokens, not characters**, because the context budget and the embedding model's
  limit are both token-denominated.

The part he would insist on: none of this is decidable in the abstract. It depends on the corpus
and the questions. The only way to know is a labelled set of real queries with the passages that
must appear in the top-k, scored on every change — which is what `eval_retrieval.py` is for on this
site, and what the retrieval eval over the interview corpus is for.

**Follow-up.** *"What if a single answer is longer than a sensible chunk?"* — Split it and attach a
short contextual header to each piece so the fragment carries its own subject. Losing the subject
is the failure that matters.

**Grounded in.** Portfolio assistant chunk design, interview corpus chunking, retrieval eval sets

### Q3.4 — What does hybrid retrieval mean, and where has he used it?

- **Difficulty:** engineer
- **Tags:** hybrid-retrieval, bm25, embeddings, fusion, rrf
- **Asked by:** Engineer

**Answer.**

Hybrid retrieval runs a lexical search and a semantic search over the same corpus and combines
their rankings, because the two fail in opposite directions.

Lexical search — BM25 — is exact. It will find a specific product code, an error string, a person's
surname or an API symbol reliably, and it will completely miss a passage that means the same thing
in different words. Semantic search over embeddings is the reverse: it bridges vocabulary
gracefully and will confidently miss an exact identifier because the embedding model never learned
a distinctive vector for that token.

Running both and fusing them covers both failures. The standard fusion is Reciprocal Rank Fusion,
which combines by rank position rather than score. That detail matters: BM25 scores and cosine
similarities are on incomparable scales with no meaningful calibration between them, so any
weighted-sum approach requires tuning a normalisation that drifts the moment you change the
embedding model. RRF sidesteps it entirely by only using the ordering.

Where he uses it: over the interview corpus that backs this assistant. The portfolio resume index
is thirty chunks and BM25 alone measured better than adding complexity to it, but the interview
corpus is several hundred chunks with a much wider range of phrasing, which is exactly the
crossover point his own roadmap had identified — the site's write-up said to move to hybrid once
the corpus grew past a few hundred chunks, and it did.

The implementation detail he would highlight: the semantic half of it runs with no external
service and no embedding API, because this site's whole design principle is that retrieval must
never depend on the network. The vectors are built offline and shipped as a compact artifact, and
query-time scoring is plain arithmetic in-process.

**Follow-up.** *"Why not just use embeddings for everything?"* — Because exact-term misses are the
complaint users actually report, and they are the ones pure dense retrieval is worst at. Hybrid is
cheap insurance.

**Grounded in.** Interview corpus hybrid retrieval, portfolio assistant BM25, site roadmap on hybrid retrieval

### Q3.5 — How does he measure whether retrieval is working?

- **Difficulty:** engineer
- **Tags:** evaluation, retrieval-metrics, recall, measurement
- **Asked by:** Engineer, Hiring Manager

**Answer.**

A labelled set of real questions, each paired with the passages that must appear in the top-k,
scored as a suite that fails the build.

On this site that is `eval_retrieval.py`: 29 questions that must retrieve the right resume section
and 7 that must retrieve nothing at all, currently 36 out of 36. It runs in a second, exits
non-zero on failure, and is meant to be run after any change to the profile data or the retrieval
code.

The metrics he uses are the standard ones — recall@k as the primary (did the right passage make
the cut at all), with rank position mattering because of the lost-in-the-middle effect. A passage
retrieved at position 9 of 10 is technically a hit and practically often a miss.

Two things he would emphasise that are less standard:

**The must-decline half is not optional.** Seven of his 36 cases assert that retrieval returns
*nothing*. Without them, an eval rewards a retriever that always returns something, which is the
exact behaviour that makes a grounded system answer questions it should refuse. He added that half
only after the system answered an unrelated personal question by attaching his career summary, and
he now treats it as the first thing to build rather than the last.

**Known limitations are recorded rather than hidden.** The eval prints two cases it does not pass
cleanly and explains why each is the prompt layer's job rather than the index's — for instance, a
question about databases legitimately retrieves the certifications chunk, and refusing an off-task
request is not something retrieval can decide. Recording those is more useful than tuning the
index until the number is clean.

The discipline this enforces showed its value on a change that had nothing to do with retrieval:
editing his experience section broke a case that had passed for months, and the eval caught it
immediately.

**Follow-up.** *"What is the failure the eval was written for?"* — Asked what he had shipped with
LLMs, the assistant returned a Kotlin chat app and a Java CRUD app. He reproduced it at 26/29,
then fixed scoring until it hit 29/29.

**Grounded in.** eval_retrieval.py, 36/36 score, build log bugs 02, 04 and 12, known limitations output

### Q3.6 — What is the hardest retrieval bug he has fixed?

- **Difficulty:** engineer
- **Tags:** debugging, retrieval, bugs, synonyms
- **Asked by:** Engineer

**Answer.**

The one that taught him the most is documented as bug 02 on this site.

Someone asked the assistant "what has he actually shipped with LLMs?" and it answered with a
Kotlin chat app and a Java CRUD app — the two least relevant projects in the corpus.

The cause was his own query expansion. To bridge the gap between how recruiters ask and how
resumes are written, he expands query terms with synonyms. But the expansion was unweighted, so
a broad synonym like "shipped" expanding to "project" matched every project chunk equally — and
because his own chunk template stamps the word "project" onto every project, all of them scored
the same noise while "LLM", the single term that discriminated, was outvoted.

The fix had three parts: typed terms keep full weight while expansions carry 0.3, so a synonym can
never outvote a word the visitor actually typed; light suffix stemming so "LLMs" matches "LLM";
and phrase normalisation so multi-word terms collapse to one canonical token before tokenising.
That last one came from a related failure where "large language model" matched his *programming
languages* list — token overlap with no meaning overlap.

What makes it the hardest is not the fix, which is straightforward. It is that he only found it
because he wrote the eval set first, reproduced the failure at 26/29, and had a number to move.
Without that he would have tried a better prompt.

The second-hardest is stranger and is bug 05: writing up bug 04 in the site's build log added that
text to the indexed corpus, which reintroduced the exact matching behaviour the bug was about and
dropped the eval from 36/36 to 34/36. Documenting a bug caused it to recur. It is why the build
log's wording is deliberately generic about the terms involved.

**Follow-up.** *"What is the general lesson?"* — In a retrieval system the index is the product, and
anything that changes the corpus changes retrieval. Content edits are code changes.

**Grounded in.** Build log bugs 02, 03 and 05, weighted expansion at 0.3, phrase normalisation, eval progression 26/29 to 36/36

### Q3.7 — How would he improve a RAG system that returns the right documents but wrong answers?

- **Difficulty:** engineer
- **Tags:** rag, debugging, grounding, generation
- **Asked by:** Engineer, Hiring Manager

**Answer.**

First he would check that the premise is true, because it usually is not. "The right documents
were retrieved" normally means someone looked at the top result and recognised it. The questions
that matter are whether the supporting passage survived into the assembled prompt, and where it
landed.

Assuming it genuinely did, the causes in order of likelihood:

**Position.** Retrieval accuracy inside a context window is U-shaped — material at the start and
end is used far more reliably than material in the middle. A supporting passage sitting at
position nine of ten is frequently ignored. Retrieving fewer, better-ranked passages beats
retrieving more, which is also cheaper.

**Competing context.** Other retrieved passages contradict or dilute the right one. A reranker over
the shortlist helps here more than anything else, because it scores query and passage jointly
rather than comparing independent embeddings.

**The prompt does not say context wins.** When retrieved context conflicts with what the model
learned in training, behaviour is unpredictable unless you are explicit. His system prompt on this
site states that the retrieved context is the complete record and forbids answering outside it.

**Truncation.** The passage was in the retrieved set and got cut during assembly because the budget
was not managed explicitly. Reserve space for output and for instructions, then give retrieval what
remains — and truncate retrieval, never the instructions.

**Model capability.** Test by handing the identical context to a stronger model. If it answers
correctly, this is a routing decision, not a retrieval problem.

The discipline he would apply throughout: add the failing case to the eval set *before* fixing it,
so the fix is provably a fix and it cannot silently come back. And resist the instinct to patch it
by appending a sentence to the system prompt addressing this one instance — that is how prompts
become hundreds of tokens of accumulated scar tissue nobody will touch.

**Follow-up.** *"What would he check first?"* — Whether the assembled prompt actually contained the
passage, verbatim. That single check eliminates most hypotheses.

**Grounded in.** Portfolio assistant system prompt, retrieval eval discipline, Pulsar chatbot grounding

### Q3.8 — Does he have vector database experience?

- **Difficulty:** recruiter
- **Tags:** pinecone, vector-database, embeddings, tools
- **Asked by:** Recruiter, Engineer

**Answer.**

Yes, on two systems, with different stores.

**Pinecone**, on his document Q&A chatbot. That project indexes a 200-page knowledge base —
chunking and embedding pipeline into Pinecone as the vector store, LangChain orchestrating
retrieval over it, the OpenAI API for generation, served through Streamlit. It cut retrieval time
by roughly 70%.

**A locally-run vector store**, on the Pulsar chatbot at Venera. That one retrieves over the
existing template corpus and schema using embeddings, and everything runs inside the customer's
on-premise deployment — so both the embedding model and the store run locally rather than as
hosted services. The specific store is Venera's implementation detail and not something this
assistant will name.

Worth adding for accuracy: he has also deliberately *not* used one where it was not warranted.
This site's resume assistant runs BM25 in-process over thirty chunks, because at that size a vector
database adds a network hop, a cold start and a bill for recall he could not measure a gain from.
Being able to say why you did not use a tool is usually better evidence of understanding it than
having used it.

What he has not done: operated a vector database at large scale, tuned approximate-nearest-neighbour
index parameters under a real recall/latency budget, or run a sharded deployment. If a role needs
someone who has pushed HNSW parameters around at a hundred million vectors, that is beyond what he
has done.

**Follow-up.** *"Which would he pick for a new project?"* — He would ask how large the corpus is
first. His own record shows him choosing differently at thirty chunks and at production scale, and
that is the question that decides it.

**Grounded in.** Document Q&A Chatbot with Pinecone, Pulsar chatbot local vector store, portfolio assistant BM25 decision, skills list

### Q3.9 — How does he handle a question the corpus does not cover?

- **Difficulty:** engineer
- **Tags:** refusal, grounding, out-of-scope, guardrails
- **Asked by:** Engineer, Hiring Manager

**Answer.**

Declines, deterministically, before the model is ever called — and this is one of the design
decisions he is most opinionated about.

The mechanism on this site: retrieval returns an empty list when nothing scores above threshold.
That empty result is the signal meaning "the corpus genuinely has nothing on this". The
application checks it and returns a refusal directly, with his email address, without spending a
model call. No generation means no chance of the model padding an answer out of unrelated context.

The reason it works this way is that it did not, originally. An earlier version substituted a few
default chunks whenever retrieval scored nothing, so there was always *something* to answer from.
That felt safer and was strictly worse: it destroyed the only signal that meant "not covered", so
neither the prompt nor the fallback could decline, and a question about his hobbies came back with
his career summary attached — reading as though it had answered the question.

Three things followed from that fix:

- Empty is now the honest return value from retrieval, and callers decide how to decline.
- Seven must-decline cases went into the eval set, so the behaviour cannot silently regress.
- The system prompt handles the harder middle case: when there is no new match but there *is*
  conversation history, a follow-up like "how long did that take?" is legitimate, so the model is
  allowed to try — but is told plainly that the corpus returned nothing this turn.

The same principle is in the Pulsar chatbot at work, where the evaluation set includes requests it
must refuse rather than guess at. A confident template for an ambiguous request is worse than a
refusal, because the operator gets no signal that it guessed.

**Follow-up.** *"Can you make it answer something out of scope?"* — Try it. Ask this assistant
something his resume does not cover and it should decline and point you at his email.

**Grounded in.** Build log bug 04, empty-retrieval design, 7 must-decline eval cases, system prompt, Pulsar eval refusal cases

### Q3.10 — What would he do differently on his next RAG system?

- **Difficulty:** engineer
- **Tags:** retrospective, improvement, roadmap, reranking
- **Asked by:** Engineer, Hiring Manager

**Answer.**

The things on his own roadmap for this site, plus what the Pulsar work taught him.

**Write the must-decline cases first.** He has now been caught twice by evaluating only what a
system should get right. On the next one, the refusal set goes in before the success set, because
it is the half that determines whether the thing is trustworthy and the half that is always
deprioritised.

**Add a reranker earlier.** Retrieve a wider shortlist and rerank it with a model that scores query
and passage jointly. It is the single highest-value addition to most RAG systems and he has not
had one in production yet — on this site the corpus was too small to need it, which is a reason
and not an excuse.

**Instrument from day one.** Log the query, the retrieved chunk ids and scores, the assembled
prompt, and the response, for a sample of traffic. Every retrieval bug he has debugged was
tractable because the answers name their own sources; the ones that would have been hard are the
ones where that trace does not exist.

**Treat content edits as code changes.** Bug 05 on this site — where writing up a bug reintroduced
it — and bug 12, where editing his experience section broke a retrieval case that had passed for
months, are the same lesson. In a retrieval system the corpus *is* the index. Anything that edits
content should run the eval.

**Stream the response.** Currently this site waits for the full answer before rendering. That is a
user-experience gap rather than a correctness one, and it is on the roadmap.

**Hybrid from the start where the corpus warrants it**, rather than starting lexical and migrating.
He was right that thirty chunks did not need it; he would not make the same call at three hundred.

**Follow-up.** *"Which of those has he already done?"* — Hybrid retrieval, on the interview corpus
backing this assistant. The rest are genuinely still on the list.

**Grounded in.** Site roadmap (hybrid, expanded eval, streaming), build log bugs 04, 05 and 12, interview corpus hybrid retrieval

### Q3.11 — How large a corpus has he worked with?

- **Difficulty:** recruiter
- **Tags:** scale, corpus-size, limits, honesty
- **Asked by:** Recruiter, Engineer

**Answer.**

Modest, and it is one of the clearer limits on his experience.

The sizes on record:

- **A 200-page knowledge base** on the document Q&A chatbot, indexed into Pinecone with LangChain
  orchestration. Roughly 70% faster retrieval was the measured result.
- **The Pulsar template corpus** at Venera — the existing templates plus the schema material.
  Production, but a product's template library rather than a web-scale corpus.
- **Around 100 pages** of interview question-and-answer content backing this assistant, which is
  the largest corpus he has built retrieval over and the reason it uses hybrid retrieval.
- **Thirty chunks** for the resume index, which is small enough that lexical retrieval was
  measurably the right choice.

What he has not done: retrieval over millions of documents, distributed or sharded indexes, or
tuning approximate-nearest-neighbour parameters under a hard recall-versus-latency budget at scale.
The problems that only appear at volume — index build time, memory pressure, recall degradation
you cannot see without measuring against exact search — he has read about and not lived.

He would argue the techniques transfer more than the scale suggests, because the decisions that
determine whether a RAG system works are chunking, retrieval quality, grounding and evaluation, and
those are the same at every size. But the operational side genuinely does not transfer, and a role
that needs someone who has run retrieval infrastructure at scale should treat that as a real gap
rather than a formality.

**Follow-up.** *"Is the corpus size why this site uses BM25?"* — Yes, directly. Thirty chunks did
not justify a vector database. The 100-page interview corpus did justify hybrid retrieval, and got
it.

**Grounded in.** Document Q&A 200-page corpus, Pulsar template corpus, interview corpus, 30-chunk resume index

### Q3.12 — How would he build a RAG system over our internal documents?

- **Difficulty:** engineer
- **Tags:** rag, design, approach, retrieval
- **Asked by:** Hiring Manager, Engineer

**Answer.**

The order he would work in, drawn from the three retrieval systems he has built:

**1. Collect real questions before touching the documents.** Twenty or thirty questions people actually ask, each paired
with the passage that answers it — plus questions the documents do *not* answer. That set is the evaluation, and it is
built first because every later decision is judged against it. His own suite has 29 must-match and 7 must-decline cases.

**2. Understand the constraints.** Can data leave your network? On the Pulsar feature it could not, which meant local
open-weight models, local embeddings and a local vector store — a completely different architecture from calling a hosted
API. What does a wrong answer cost? Who is allowed to see which documents? Tenant or permission filtering belongs in the
query to the index, never as a post-filter and never in the prompt.

**3. Chunk by structure.** Split on the documents' own boundaries — headings, sections, list items — so each chunk is about
one thing, and attach a short header carrying the document and section so a fragment keeps its subject.

**4. Start with the cheapest retrieval that could work, then measure.** For a small corpus that may be lexical search, which
is what he chose for thirty resume chunks. For anything larger or phrased in varied language, hybrid: lexical and semantic
passes fused by rank, which covers exact terms and paraphrase at the same time. Add a reranker over the shortlist if the
eval says precision is the problem.

**5. Ground and constrain generation.** The prompt says retrieved context is the whole record; answers cite their sources;
empty retrieval declines rather than improvising; structured output is validated in code.

**6. Design the failure path.** What happens when the model provider is down or slow — his systems degrade to returning the
retrieved text rather than erroring.

**7. Log real traffic and grow the eval from it.** The questions people actually ask will differ from the ones you collected.

**Follow-up.** *"How long would a first version take?"* — Depends on the corpus and constraints. The evaluation set is the
part worth not rushing; the pipeline itself is fast to build.

**Grounded in.** Three retrieval systems (Pinecone RAG, portfolio BM25, Pulsar local embeddings), eval design 29+7, hybrid retrieval over interview corpus, refusal and fallback design

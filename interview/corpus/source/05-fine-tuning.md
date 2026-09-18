# Part 5 — Fine-Tuning and Model Adaptation

> This is the part of the stack where he is most careful about what he claims. He works with
> open-weight models in production and has built the dataset and evaluation scaffolding for
> fine-tuning, but he has not run a large training job and does not pretend otherwise. The
> answers below are as much about knowing when *not* to fine-tune as about the technique.

### Q5.1 — Has he fine-tuned a model?

- **Difficulty:** sceptical
- **Tags:** fine-tuning, honesty, limits, lora
- **Asked by:** Hiring Manager, Engineer

**Answer.**

Not at production scale, and this is a place where the honest answer is narrower than the resume
keyword suggests.

What he has done: fine-tuning experiments with Hugging Face Transformers as part of his NLP
pipelines work, and the dataset-and-evaluation scaffolding around fine-tuning — building an
instruction dataset from a corpus, splitting it, checking for contamination against the eval set,
and scoring a tuned model against a base one. He has worked with LoRA as the approach.

What he has not done: trained a foundation model, run a distributed or multi-GPU training job,
fine-tuned a model that then went into production serving real traffic, or owned a training
pipeline as an ongoing system. If a role's core requirement is running training infrastructure,
that is a genuine gap.

What he *has* done that is adjacent and more relevant to most AI engineering roles: shipped a
production system on open-weight models. The Pulsar chatbot runs Qwen inside an on-premise
deployment, which means he has dealt with model selection under hardware constraints, the quality
implications of a fixed smaller model, and getting adequate behaviour out of it through retrieval
and grounding rather than through more parameters. That is model adaptation without weight
updates, and for a lot of production work it is the more common skill.

His view, which he would state unprompted: fine-tuning is the option teams reach for too early. On
most problems he has seen, better retrieval and a rewritten prompt deliver more in two days than a
training pipeline delivers in two weeks — and he would rather be the engineer who says that than
the one who builds the pipeline first.

**Follow-up.** *"Would he be able to run a fine-tune if asked?"* — He has built the dataset and
evaluation side and worked with LoRA in experiments. He would be honest that his first production
fine-tune would be his first, and would want review.

**Grounded in.** NLP Pipelines fine-tuning experiments, Hugging Face Transformers, Pulsar on Qwen open-weight models, skills list

### Q5.2 — When would he fine-tune instead of using RAG?

- **Difficulty:** engineer
- **Tags:** fine-tuning, rag, decision-making, architecture
- **Asked by:** Engineer, Hiring Manager

**Answer.**

They solve different problems, and he would push back on the question being framed as a choice
between them.

The decomposition he uses:

- **Prompting** changes instructions — what the task is and how to respond.
- **RAG** changes knowledge — what facts are available at answer time.
- **Fine-tuning** changes behaviour — format, tone, task-specific skill, conventions that are
  tedious to specify.

So the diagnostic is what is actually wrong:

**"It doesn't know our data."** → RAG, essentially always. Fine-tuning is a poor way to inject
facts: it is expensive to update, it teaches the fact without teaching the model to cite it, and
facts seen a few times in training are learned unreliably. Anything that changes weekly must not
live in weights. The Pulsar chatbot is exactly this case — the template corpus changes, so it is
retrieved rather than trained in.

**"It knows the answer but formats it wrong or sounds wrong."** → Prompting first, fine-tuning if
the prompt has grown to hundreds of tokens replicated on every request.

**"It can't do the task at all, and examples don't help."** → Fine-tuning, if you have data.

**"It's right but too slow or expensive."** → This is where fine-tuning has its clearest return:
train a small model on outputs from a large one and get comparable quality on a narrow task at a
fraction of the cost.

The order he would actually work in is prompt, then retrieval, then fine-tuning, measuring at each
step — and he would say most teams invert it. Two weeks building a training pipeline frequently
produces less improvement than a better retriever and a rewritten prompt would have in two days,
and you cannot tell which without an eval set, which is the real prerequisite for the decision.

They also combine. The strongest production systems use all three: a tuned model that follows house
conventions, over retrieved context, with a versioned prompt.

**Follow-up.** *"Someone says they want to fine-tune on their documentation. What do you say?"* —
That is the textbook case for RAG. Documentation changes, and you want citations. Fine-tuning would
make it confidently wrong about last quarter's docs.

**Grounded in.** Pulsar RAG architecture, prompt-evaluation work, retrieval-first approach

### Q5.3 — Explain LoRA and why it matters.

- **Difficulty:** engineer
- **Tags:** lora, peft, fine-tuning, efficiency
- **Asked by:** Engineer

**Answer.**

Full fine-tuning updates every weight in the model, which means holding the weights, their
gradients and the optimiser state in memory simultaneously — for a 7B model in fp16 that is
roughly 14 GB of weights and several times that again in training state. It puts fine-tuning out
of reach without serious hardware.

LoRA — low-rank adaptation — freezes the base model entirely and inserts small trainable matrices
alongside the layers it adapts. The insight is that the *update* a fine-tune applies is
empirically low-rank: it lies in a much smaller subspace than the full parameter space. So rather
than learning a full-size weight delta, you learn two thin matrices whose product approximates it.
With a rank of 8 or 16 you train a fraction of a percent of the parameters.

What that buys, and why it changed practice:

- **Memory.** You only need gradients and optimiser state for the adapter, so fine-tuning a 7B
  model becomes feasible on a single consumer GPU. QLoRA goes further by quantising the frozen
  base to 4-bit.
- **Small artifacts.** An adapter is megabytes rather than gigabytes, so you can version them
  cheaply, store many, and swap them per customer or per task against one loaded base model. For a
  product with per-tenant behaviour that is a serving architecture, not just a training trick.
- **The base is untouched.** You cannot catastrophically forget what you never modified, and
  rolling back is deleting a file.
- **Rank is a regulariser.** Constraining the update to a low-dimensional subspace limits capacity,
  which is often why LoRA overfits less than full fine-tuning on small datasets.

The trade-off is that it does not match full fine-tuning on tasks requiring large behavioural
change, and rank and which modules to adapt become hyperparameters you have to tune.

For his context it is the relevant technique precisely because the constraint is always hardware —
the Pulsar deployment runs on customer machines, and anything requiring a training cluster is not
an option.

**Follow-up.** *"What rank would he start with?"* — 8 or 16 on attention projections, then measure.
Higher rank is more capacity and more overfitting risk; it is a hyperparameter like any other and
should be tuned against an eval set.

**Grounded in.** LoRA in skills list, NLP Pipelines fine-tuning experiments, on-premise hardware constraints

### Q5.4 — How would he build a fine-tuning dataset?

- **Difficulty:** engineer
- **Tags:** dataset, fine-tuning, data-quality, contamination
- **Asked by:** Engineer, Hiring Manager

**Answer.**

Carefully, because the dataset determines the outcome far more than the hyperparameters do, and
because the failure modes are silent.

His process:

**Define the target behaviour precisely first.** Fine-tuning teaches behaviour, so you need to be
able to state what the model should do differently. "Better" is not a target; "produces output in
this format, with these conventions, and refuses these categories" is.

**Build instruction–response pairs that demonstrate it**, including the refusals. A dataset made
only of successful cases teaches the model that every input has an answer — which is exactly the
behaviour that makes a grounded system dangerous. This is the same instinct behind the
must-decline half of his eval sets.

**Deduplicate, including near-duplicates.** Repeated examples are silent over-weighting. In a corpus
built from real content, near-duplicates are common and the model will memorise them.

**Check contamination against the eval set.** This is the step people skip and it invalidates
everything downstream. If evaluation examples appear in training, the score measures memorisation
and the model will look excellent and behave worse in production. He would run this as an explicit
check that fails loudly, not as a manual review.

**Split by group, not randomly**, wherever examples cluster — multiple questions from the same
document, or several variants of one task. Random splitting puts near-identical items on both sides
and inflates the score.

**Hold quality above volume.** The evidence on instruction tuning is consistently that a small
well-curated set outperforms a large noisy one. A thousand good examples is a realistic target;
a hundred thousand scraped ones is usually worse.

**Keep provenance.** Record where each example came from, so when the model develops a strange
behaviour you can find the examples that taught it.

**Follow-up.** *"What if you have no labelled data?"* — Use a strong model to generate candidates,
have a human correct a sample to measure the annotator's own accuracy, then train on the corrected
set. Skipping the accuracy measurement means not knowing whether you are training on 95% correct
labels or 70%.

**Grounded in.** NLP Pipelines fine-tuning experiments, must-decline eval design, prompt-evaluation labelled sets

### Q5.5 — How would he evaluate a fine-tuned model?

- **Difficulty:** engineer
- **Tags:** evaluation, fine-tuning, regression, measurement
- **Asked by:** Engineer, Hiring Manager

**Answer.**

Against the base model, on a held-out set the tuned model never saw, measuring both the thing he
was trying to improve and the things he might have broken.

The structure:

**A task set for the target behaviour.** The cases the fine-tune was supposed to fix, scored
identically for base and tuned so the comparison is apples to apples. Improvement here is the
reason the fine-tune exists.

**A regression set for everything else.** This is the half that matters and the half people omit.
Fine-tuning shifts a model's behaviour globally, not only on the target task, and catastrophic
forgetting is real — a model tuned to produce one output format can lose the ability to do things
it did fine before. So the evaluation has to include general capability cases outside the training
distribution.

**Refusal behaviour.** Whether the tuned model still declines what it should. Instruction tuning on
a dataset of successful completions teaches the model that every input has an answer, and refusal
quality degrades quietly.

**Format compliance, measured programmatically.** If the point was structured output, the metric is
what fraction parses and validates — a number, not an impression.

Two methodological points he would insist on. The eval set must be checked for contamination against
the training data, otherwise the score measures memorisation. And a perplexity improvement on held-out
text is a training diagnostic, not evidence the model is more useful — instruction tuning routinely
makes raw perplexity worse while making the model far better at the job.

If the fine-tune was for cost rather than capability, the evaluation is explicitly a comparison:
does the small tuned model match the large base model closely enough on this task to justify the
switch? That is a threshold decision, and without a scored set you are guessing at a downgrade.

**Follow-up.** *"How do you know it did not just memorise?"* — Contamination check, plus evaluating
on examples collected after the training data was assembled. Time-separated evaluation catches what
deduplication misses.

**Grounded in.** NLP Pipelines prompt-evaluation methodology, must-decline eval design, retrieval eval discipline

### Q5.6 — What does he know about running open-weight models?

- **Difficulty:** engineer
- **Tags:** open-weights, qwen, self-hosting, deployment
- **Asked by:** Engineer, Hiring Manager

**Answer.**

This is the strongest part of his model-layer experience, because it is what the Pulsar chatbot
required.

That system runs Qwen open-weight models inside Venera's on-premise deployment, with no outbound
API calls, because the customers who run Pulsar on-premise do so precisely so their media and
workflows stay on their own infrastructure. So he has had to work with:

**Model selection under hardware constraints.** The model is bounded by what the customer's machines
can run, not by what performs best. That flips the usual optimisation — you cannot buy quality with
a bigger model, so it has to come from retrieval, grounding and validation.

**Local embedding and retrieval.** No hosted embedding API either, so the embedding model ships
alongside and the vector store runs locally.

**Version control as an advantage.** A self-hosted model does not silently change under you. There
is no provider repointing an endpoint alias at a new checkpoint, which means behaviour is
reproducible and upgrades are a deliberate release decision. For a product that ships to customer
sites, that predictability is worth a lot.

**Designing around a fixed capability ceiling.** Which he would argue produced a better system than
an API would have, because it forced grounding and structured validation to be load-bearing rather
than optional.

What he has not done: served open-weight models at scale with a production inference stack, tuned
throughput with continuous batching, managed GPU capacity and utilisation economics, or quantised a
model and measured the quality cost. Those are the operational skills of someone running an
inference platform, and Pulsar's deployment model is different — it ships into customer environments
rather than being centrally served.

**Follow-up.** *"Would he know how to serve one at scale?"* — He knows the vocabulary — vLLM,
continuous batching, PagedAttention, KV cache pressure — and has not operated it. Worth treating as
knowledge rather than experience.

**Grounded in.** Pulsar chatbot on Qwen, on-premise offline deployment, local embedding and vector store, hardware constraints

### Q5.7 — When is fine-tuning the wrong answer?

- **Difficulty:** engineer
- **Tags:** fine-tuning, anti-patterns, decision-making
- **Asked by:** Engineer, Hiring Manager

**Answer.**

More often than it is proposed, in his experience. The cases where he would argue against it:

**To add knowledge that changes.** Weights are a bad database. Updating a fact means retraining,
the model learns the fact without learning to cite it, and facts seen rarely in training are learned
unreliably. Anything that changes on a weekly cadence belongs in a retrieval corpus. The most common
version of this request — "fine-tune it on our documentation" — is the textbook case for RAG.

**Before there is an eval set.** Without a scored set you cannot tell whether the fine-tune helped,
which means you cannot tell whether it was worth doing and cannot detect that it broke something
else. Building the eval is the prerequisite, not a follow-up.

**Before trying prompting and retrieval.** Two weeks on a training pipeline frequently produces less
improvement than two days on a better retriever. The ordering matters because the cheap options also
tell you more about the problem.

**When the training data is small or noisy.** A few hundred inconsistent examples will teach
inconsistency. The evidence on instruction tuning favours small and clean over large and noisy, and
"we have a lot of logs" is not a dataset.

**When you cannot maintain it.** A fine-tuned model is an ongoing obligation: base model upgrades
mean redoing it, behaviour drifts as the task evolves, and someone has to own the pipeline. A prompt
is edited in a pull request.

**When determinism or auditability matters more than quality.** A fine-tune makes behaviour harder to
explain, not easier.

The case where he *would* argue for it, to be balanced: cost and latency on a narrow, stable,
high-volume task, where a small tuned model matches a large one closely enough. That is where the
economics are unambiguous.

**Follow-up.** *"Has he ever talked someone out of fine-tuning?"* — Worth asking him directly. His
documented pattern is choosing the cheaper option and measuring it — this site uses BM25 rather than
embeddings for exactly that reason.

**Grounded in.** Retrieval-first approach, portfolio assistant BM25 decision, eval-set discipline, Pulsar RAG architecture

### Q5.8 — How would he reduce the cost of an LLM feature?

- **Difficulty:** engineer
- **Tags:** cost, optimisation, caching, routing, efficiency
- **Asked by:** Engineer, Hiring Manager

**Answer.**

In the order of effort-to-saving, which is roughly the opposite of the order people try.

**Avoid the call entirely where you can.** On this site, questions the resume does not cover are
declined deterministically before any model call — no tokens spent, and it is also the more correct
behaviour. Caching repeated queries is the other free win.

**Retrieve less, better.** Three well-ranked passages beat ten mediocre ones on cost *and* accuracy,
because of the lost-in-the-middle effect. A reranker that lets you cut top-k pays for itself twice.

**Shorten what is on every request.** The system prompt is billed on every call. A 400-token system
prompt at meaningful volume is pure recurring overhead. Structuring the stable part of a prompt
first also lets provider-side prompt caching do its job.

**Constrain output.** Output tokens typically cost several times input. Instruct for brevity, set a
maximum, return structured data rather than prose where a program consumes it, and do not add
chain-of-thought where it is not earning its cost.

**Route by difficulty.** Small model first, escalate only on failure or low confidence. With large
price differences between tiers this is usually the biggest single lever.

**Self-host when volume justifies it.** Which is where the Pulsar architecture sits — though there it
was a data-residency requirement rather than a cost decision. The honest version of this trade is
that a GPU costs the same idle, so it only wins at sustained utilisation.

**Make it visible.** Log tokens and cost per request. Teams that cannot attribute spend cannot reduce
it, and a runaway retry loop will find that out for you. This site rate-limits per IP for exactly
that reason.

**Follow-up.** *"Where do costs usually hide?"* — Retries, agent loops re-reading the same context
each iteration, re-embedding a corpus on every deploy, and evaluation runs nobody counted.

**Grounded in.** Portfolio assistant deterministic refusal, rate limiting, provider chain design, Pulsar self-hosted architecture

### Q5.9 — What is his experience with Hugging Face?

- **Difficulty:** recruiter
- **Tags:** hugging-face, transformers, nlp, tools
- **Asked by:** Recruiter, Engineer

**Answer.**

Hugging Face Transformers is on his resume for the NLP pipelines project, and it is where his
model-level work sits.

That project built transformer-based text pipelines for classification and summarisation —
tokenisation, inference, and fine-tuning experiments. Attached to it is the prompt-evaluation loop
that scores prompt variants against a hand-labelled question set, with unsupported answers tracked
as a metric rather than estimated. He describes the evaluation part as the point of the project more
than the pipelines themselves.

It is also the ecosystem behind the open-weight side of his production work, since Qwen models are
distributed through it.

What that means concretely for his skill level: he is comfortable loading models and tokenisers,
running inference, working with the tokenisation layer, and setting up fine-tuning experiments. He
has not trained a model from scratch on it, has not published a model, and has not used it for
large-scale distributed training.

One thing he would be precise about, because it is a common overstatement: using Transformers to run
and experiment with models is a different skill from training them, and most of what he has done is
the first. He would rather say that than let "Hugging Face Transformers" on a skills list imply
research-level depth it does not.

**Follow-up.** *"Which is stronger — his Hugging Face work or his LangChain work?"* — The LangChain
work has shipped in a project with measured results; the Hugging Face work is where the evaluation
methodology came from. Different kinds of evidence.

**Grounded in.** NLP Pipelines with Hugging Face project, prompt-evaluation loop, skills list, Qwen models

### Q5.10 — Could he take a model from an experiment into production?

- **Difficulty:** hiring-manager
- **Tags:** production, deployment, mlops, readiness
- **Asked by:** Hiring Manager

**Answer.**

He has done it once, which is the honest framing — the Pulsar chatbot went from nothing to a feature
in a commercial product, and he was the primary engineer on it.

What that involved beyond making a model produce good output: working inside a deployment model he
did not control, designing for an environment with no outbound network access, building a validation
layer that makes bad output structurally unable to reach the product, writing the evaluation set
that says whether it works, and integrating with an existing release process he already knew from six
months of QA work on the same platform.

The parts he brings from the quality-engineering side are the ones that usually decide whether an
experiment survives contact with production: defining acceptance criteria, thinking about the failure
path before the happy path, and having a scored suite that can say whether a change is safe. He has
done release readiness work on AWS cloud-native services as a formal part of his job.

Where he would want support: he has done this once, with an external consultant available, on a
system that is not high-traffic. He has not carried a model through a version upgrade, a year of
drift, or an incident caused by the model itself. He has not built a retraining pipeline or a
monitoring stack for model quality in production.

So: yes for a feature of comparable scope, with code review. Not yet for owning the ML platform that
other people's models go through.

**Follow-up.** *"What would he set up first on day one?"* — Logging of inputs, outputs and versions
for a sample of traffic, and an eval set. Without the first, debugging becomes archaeology; without
the second, nobody can tell whether a change is safe.

**Grounded in.** Pulsar chatbot end-to-end ownership, release readiness experience, evaluation set, experience level

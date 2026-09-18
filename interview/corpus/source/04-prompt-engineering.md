# Part 4 — Prompt Engineering

> He has written prompts for three systems that are still running: the Pulsar template generator
> at Venera, the assistant on this page, and a prompt-evaluation loop over Hugging Face NLP
> pipelines. The through-line in his answers is that he treats a prompt as a versioned artifact
> with an eval attached, rather than as a string that gets edited until the demo looks good.

### Q4.1 — What is his actual approach to prompt engineering?

- **Difficulty:** engineer
- **Tags:** prompting, methodology, versioning, evaluation
- **Asked by:** Engineer, Hiring Manager

**Answer.**

Treat the prompt as code: version it, test it, and never change it without measuring.

The concrete practice he follows:

**Prompts live in one place, not at the call site.** On this site the system prompt is a single
module-level constant with the retrieval layer feeding it. You cannot A/B test or roll back a
template that is spliced into a request handler, and once it is inline nobody knows which of the
three copies is the live one.

**Every prompt has an eval set behind it.** On the Hugging Face NLP work he built a
prompt-evaluation loop specifically for this — each prompt variant is scored against a
hand-labelled question set, so "this one is better" is a number rather than an impression. That
project exists because he did not trust his own judgement reading a handful of outputs, and he was
right not to: sampling three responses from a generative system will confirm whatever you already
believed.

**Constraints beat instructions.** A prompt asking for valid JSON is a preference; a schema
validator is a property. On the Pulsar chatbot the generated template is validated against the
schema in code, so "produce a valid template" is not something the prompt has to get right. He
puts guarantees in code and uses the prompt for the things code cannot express.

**Say what to do when there is no answer.** The hardest part of a grounded prompt is the refusal
path. His system prompt here states that retrieved context is the complete record, forbids
inventing employers, dates, titles or numbers, and gives explicit instructions for the case where
the context says nothing matched.

**Resist accretion.** The failure mode of prompt maintenance is that every bug gets a new sentence
appended addressing that one case, and eighteen months later the prompt is 800 tokens of scar
tissue nobody dares touch. If a fix belongs in retrieval or validation, it goes there.

**Follow-up.** *"How does he know a prompt change helped?"* — The eval score moved. Without a scored
set the honest answer is that he does not know, and he would say so.

**Grounded in.** Portfolio assistant SYSTEM_PROMPT, NLP Pipelines prompt-evaluation loop, Pulsar schema validation

### Q4.2 — Walk me through the system prompt on this site.

- **Difficulty:** engineer
- **Tags:** system-prompt, grounding, guardrails, honesty
- **Asked by:** Engineer, Hiring Manager

**Answer.**

It is short by design and every clause is there because of something that went wrong.

The structure: it establishes who the assistant is and who it is talking to — recruiters, hiring
managers and engineers evaluating him for AI/ML roles — then imposes rules.

**Answer only from the retrieved context, which is the complete record.** This is the grounding
clause. Without it the model fills gaps from its training data, and the gaps it fills most
confidently are exactly the plausible-sounding ones — an employer he never worked for, a
framework he has never used.

**Never invent employers, dates, titles, tools or numbers.** Named explicitly because those are the
categories a language model fabricates most fluently, and the ones a recruiter is most likely to
act on.

**When the context says nothing matched, say so and point to his email.** The explicit refusal
path. There is a subtlety here: mid-conversation follow-ups like "how long did that take?" are
legitimate even with no new retrieval match, so the model is allowed to use earlier turns — but it
is told plainly that the corpus returned nothing this turn, and told not to substitute his career
summary for an answer to an unrelated question. That last instruction is there because it did
exactly that.

**Be honest about level.** It states that he is early-career with production QA experience and
self-directed applied AI work, and instructs the model not to oversell him as a senior researcher.
He would rather a recruiter get an accurate picture than a flattering one that collapses in the
first interview.

**Lead with the concrete answer, quote real metrics, keep it under about 150 words.**

What is deliberately *not* in it: anything the retrieval layer or the validation layer should
handle. When the assistant answered an out-of-scope question badly, the fix was to make retrieval
return empty and decline before the model call — not to add a sentence to the prompt.

**Follow-up.** *"Is the system prompt a secret?"* — No, and treating one as a secret is a mistake.
Context is extractable. Nothing in it would matter if published.

**Grounded in.** SYSTEM_PROMPT in core/llm.py, build log bug 04, OUT_OF_SCOPE handling, guardrails list

### Q4.3 — How does he prevent hallucination in a system he builds?

- **Difficulty:** engineer
- **Tags:** hallucination, grounding, guardrails, validation
- **Asked by:** Engineer, Hiring Manager

**Answer.**

He would start by reframing it: hallucination is not a bug to be fixed, it is a property of
maximum-likelihood text generation. The model produces the most plausible continuation, and
plausible overlaps with true but is not the same thing. A design that assumes it can be eliminated
is a design that will fail.

So the question is containment, and his layers are:

**Ground the answer in retrieved context, and say so in the prompt.** The model is answering from
material rather than from memory.

**Give it a rewarded path to decline.** This is the one people skip. If "I don't know" is not an
available and explicitly instructed output, the model produces something, because a refusal is a
low-probability continuation in most contexts. On this site, retrieval returning empty triggers a
deterministic refusal before any model call.

**Validate structurally rather than asking nicely.** On the Pulsar chatbot the generated template
is checked against the schema in code. Malformed output cannot get through regardless of what the
model did.

**Cite sources so claims are checkable.** Every answer this assistant gives carries the resume
section titles it drew from, which is also how he found a bug: the answers naming their own engine
is how he discovered every model call was silently failing while the health check reported green.

**Measure the rate rather than assuming it.** Both his eval sets include cases that must be
refused, so the refusal behaviour is scored rather than hoped for.

The failure he is most alert to, because validation cannot catch it, is output that is well-formed
and wrong — a template that validates perfectly but encodes different intent than the operator
described. Only an eval set with expected outputs finds that.

**Follow-up.** *"Does temperature 0 fix it?"* — It reduces sampling-driven invention and does not
touch the underlying cause. It also does not make a hosted model deterministic: batching and
floating-point reduction order still move the logits.

**Grounded in.** Portfolio assistant guardrails, deterministic refusal path, Pulsar schema validation, source citations, build log bug 08

### Q4.4 — What is the prompt-evaluation loop he built?

- **Difficulty:** engineer
- **Tags:** prompt-eval, measurement, nlp, hugging-face
- **Asked by:** Engineer, Hiring Manager

**Answer.**

It is part of his Hugging Face NLP pipelines project, and it exists because he did not trust
eyeballing output.

The mechanics: a hand-labelled question set with known-correct answers, and a set of prompt
variants. Each variant is run across the whole set and scored, so comparing two prompts produces a
number rather than an impression. Unsupported answers — where the output asserts something the
source material does not contain — are tracked as a metric rather than estimated.

Why he built it: the standard way to iterate on a prompt is to change it, run two or three
examples, and decide it is better. That process is close to worthless, because output variance
between runs on the same prompt is wide enough that a small sample confirms whatever you expected.
He wanted a measurement that was not his own impression.

What it gives you beyond a score:

- **Regression detection.** Prompt changes have non-local effects. Improving behaviour on one class
  of question routinely degrades another, and nothing tells you unless both are in the set.
- **A record of why the current version is the current version.** Every prompt in a mature system
  is the way it is because of a specific failure, and the eval is where that reasoning is stored.
- **Grounds to reject a change.** Being able to say "that phrasing scored worse" ends an argument
  that otherwise runs on taste.

The same discipline is behind the two other systems he has shipped: the 36-case retrieval eval on
this site, and the must-generate plus must-refuse evaluation set for the Pulsar chatbot. He would
describe "learn a technique, then build the thing that tells you whether it is working" as the
most consistent habit across his projects.

**Follow-up.** *"How large was the labelled set?"* — Hand-labelled and modest, which he would be
upfront about. Thirty cases you wrote yourself beats no measurement; it is not a benchmark.

**Grounded in.** NLP Pipelines with Hugging Face project, prompt-evaluation loop, unsupported answers tracked as a metric

### Q4.5 — How does he get reliable structured output from a model?

- **Difficulty:** engineer
- **Tags:** structured-output, json, validation, schema, reliability
- **Asked by:** Engineer

**Answer.**

In layers, and with the assumption that the model will eventually produce something that does not
fit.

His ordering:

**Constrain the generation where the stack allows it.** Asking for output in a defined structure,
and constraining decoding to a schema where that is available, makes invalid output structurally
impossible rather than merely unlikely. This is the strongest layer and the one to use if you have
it.

**Provide the schema and one complete example in the prompt**, keep the structure shallow, and
prefer enums over free strings. Deeply nested optional structures fail far more often, and an enum
constrains what the model can choose at all.

**Validate, always.** This is the layer that must exist even if every other one is in place. On the
Pulsar chatbot the generated template is validated against the schema before anything is used, and
a template that does not validate does not get through. That is a hard gate.

**Bounded repair, then fail loudly.** Feeding the invalid output and the validation error back with
"fix this to match the schema" recovers most failures in one attempt. Cap it at two and then fail
visibly — an unbounded repair loop is a cost incident waiting to happen.

**Reject rather than coerce.** He is firm on this one. If validation fails, do not quietly patch
the output into something that passes. On a QC template, silently coercing a malformed generation
into a valid-looking one means the operator runs quality control with checks they did not ask for,
and nothing anywhere says so. Failing is better than being wrong quietly.

The failure that validation cannot catch, and which he designs the eval set around: output that
parses perfectly and means the wrong thing. Schema validation confirms shape, not intent.

**Follow-up.** *"What if the model must sometimes say it cannot?"* — Make refusal a valid value in
the schema. A nullable field or an explicit variant is far more reliable than hoping for an empty
object.

**Grounded in.** Pulsar structured-output validation, schema gating, refusal cases in eval set

### Q4.6 — Does he use chain-of-thought prompting?

- **Difficulty:** engineer
- **Tags:** chain-of-thought, reasoning, cost, latency
- **Asked by:** Engineer

**Answer.**

Selectively, and he is wary of it as a reflex.

Where it earns its cost: multi-step reasoning, where the model needs to work through intermediate
results. The mechanism is that a transformer does a fixed amount of computation per token, so
forcing an immediate answer caps the compute available, while generating intermediate tokens
creates more forward passes and writes intermediate results into the context where later steps can
use them. More tokens is literally more computation.

Where it costs more than it returns, which is most of what he builds:

- **Extraction and classification.** Producing a structured template from a description, or
  retrieving and summarising a resume section, does not benefit from a reasoning preamble. It
  multiplies output tokens and latency for no accuracy gain.
- **Latency-sensitive paths.** Reasoning tokens generate serially. On an interactive assistant that
  is seconds of visible delay for an answer that was not going to change.
- **Anywhere it gets shown to a user as justification.** This is his strongest objection. The
  stated chain is not a faithful account of the computation that produced the answer — models
  produce correct answers via flawed reasoning and plausible reasoning leading to wrong answers.
  Displaying it makes a wrong answer *more* convincing, which is the opposite of what a grounded
  system should do.

The compromise he would use when it is warranted: reason into a field that is not displayed, then
present a concise answer. You get the accuracy and the user gets an answer rather than a
monologue.

On a constrained model in an on-premise deployment there is an additional consideration — output
tokens cost latency on hardware you do not control, so a reasoning chain is a real budget decision
rather than a free accuracy improvement.

**Follow-up.** *"What about self-consistency?"* — Sampling several chains and majority-voting is one
of the more reliable accuracy gains available, at k times the cost. Justifiable on high-value
low-volume decisions, not on an interactive assistant.

**Grounded in.** Pulsar chatbot on constrained hardware, portfolio assistant latency design, structured-output focus

### Q4.7 — How does he handle prompt injection?

- **Difficulty:** engineer
- **Tags:** security, prompt-injection, guardrails, owasp
- **Asked by:** Engineer, Security

**Answer.**

By assuming it succeeds and limiting what that buys an attacker, because there is no reliable way
to prevent it — instructions and data share one channel, which is architectural rather than a bug
to patch.

The distinction he works from: *direct* injection is a user typing "ignore previous instructions",
which is mostly a nuisance. *Indirect* injection is instructions hidden in content the system
retrieves and reads while doing something legitimate, and that is the dangerous one for any RAG
system — including both of his.

What he actually relies on:

**Scope of action.** Neither system he has built can do anything consequential. This site's
assistant reads a resume index and returns text; it has no tools, no write access, no ability to
send anything. The Pulsar chatbot produces a candidate template that is validated against a schema
before use. A successful injection against either gets you wrong text, not a side effect.

**Treat retrieved content as data, never instructions.** The corpus is his own content in both
cases, which lowers the risk considerably — but the principle holds regardless.

**Validate output structurally.** An injected instruction that makes the model produce a different
template still has to pass schema validation.

**Escape model output before rendering.** On this site the model's response is HTML-escaped before
the markdown renderer runs, so a response cannot inject markup. This is the "insecure output
handling" risk rather than injection proper, and it is the one most people miss — model output is
untrusted input to whatever consumes it.

**Rate limit.** Per-IP limiting keeps a stray script from draining a free tier, which is the
denial-of-wallet variant.

What he would not claim: that he has hardened a system against a motivated adversary. Neither
system has meaningful privileges, which is the real reason they are safe.

**Follow-up.** *"What changes if you give it tools?"* — Everything. Least privilege, allow-listed
tools, typed and validated arguments, and human confirmation for anything irreversible. He has not
built an agent with real permissions.

**Grounded in.** Portfolio assistant guardrails (HTML escaping, rate limiting), Pulsar schema validation, no-tool architecture

### Q4.8 — How does he decide between changing the prompt and changing the retrieval?

- **Difficulty:** engineer
- **Tags:** debugging, retrieval, prompting, diagnosis
- **Asked by:** Engineer, Hiring Manager

**Answer.**

By looking at what was actually retrieved before touching anything — and he would say the instinct
to edit the prompt first is the single most common mistake in RAG work, including his own.

The test is direct. Look at the passages that ended up in the assembled prompt. If the material
needed to answer the question is not there, no prompt change can help, and any improvement you
think you see from rewording is noise. If it *is* there and the answer is still wrong, then it is a
prompt, position or model problem.

The diagnostic order he uses:

1. **Was it retrieved at all?** If not, it is chunking, scoring, or the vocabulary gap between how
   the question is phrased and how the content is written.
2. **Did it survive into the prompt?** Truncation and budget management live here.
3. **Where did it land?** Position matters — a passage at the bottom of ten is frequently ignored.
4. **Does the prompt say context wins?** If retrieved context conflicts with the model's training
   knowledge, behaviour is undefined unless you are explicit.
5. **Is it a capability problem?** Hand the same context to a stronger model. If that fixes it, the
   answer is routing, not prompting.

His clearest example is bug 02 on this site. Asked what he had shipped with LLMs, the assistant
returned a Kotlin chat app and a Java CRUD app. Every instinct says rewrite the prompt. The actual
cause was unweighted query expansion letting a broad synonym outvote the one discriminating term,
and the fix was entirely in the scoring — weighted expansion, stemming, phrase normalisation. A
prompt change would have produced a differently-worded wrong answer.

The habit that makes this tractable is that his answers cite the sections they came from, so
looking at what was retrieved is a glance rather than an investigation.

**Follow-up.** *"When is it genuinely the prompt?"* — When the right passage is present, near the
top, and the answer contradicts it or ignores its framing. That is a grounding instruction problem.

**Grounded in.** Build log bug 02, source citations on answers, retrieval eval methodology

### Q4.9 — What makes a prompt maintainable a year later?

- **Difficulty:** engineer
- **Tags:** maintainability, versioning, prompt-management
- **Asked by:** Engineer, Hiring Manager

**Answer.**

Four things, and he has watched the absence of each cause problems.

**It lives in one place and is versioned.** Not inline at the call site, not duplicated across three
handlers. On this site it is a single constant in the module that assembles the request. You cannot
roll back or compare something you cannot locate.

**Every clause has a recorded reason.** The most dangerous prompt is one where nobody knows why a
sentence is there, because then nobody will remove it and it accumulates. His system prompt's
clauses each map to a specific failure — the "do not substitute the career summary" instruction
exists because it did exactly that, and that is documented in the build log. A clause with a
recorded cause can be deleted when the cause is gone.

**It has an eval attached.** Without one, nobody will touch it, because nobody can tell whether a
change made it worse. A prompt with a scored set behind it is editable; a prompt without one is
frozen.

**Fixes go to the right layer.** The strongest force degrading a prompt over time is that every bug
gets a sentence appended addressing that one instance. Eighteen months of that produces 800 tokens
of accumulated special cases, on every single request, that nobody dares to touch. His discipline
is to ask whether a fix belongs in retrieval or validation first — the out-of-scope failure on this
site was fixed by making retrieval return empty and declining before the model call, not by adding
a "do not answer questions outside the resume" line.

The cost argument reinforces all of this: the system prompt is on every request, so length is a
recurring bill as well as a maintenance problem.

**Follow-up.** *"How does he decide when to rewrite rather than patch?"* — When the clauses start
contradicting each other, or when the eval shows a change helping one case and hurting another.
That is the signal the prompt is doing too many jobs.

**Grounded in.** SYSTEM_PROMPT structure, build log bug 04, guardrails documentation, retrieval-layer fixes

### Q4.10 — Has he done anything with few-shot prompting?

- **Difficulty:** engineer
- **Tags:** few-shot, in-context-learning, examples, prompting
- **Asked by:** Engineer

**Answer.**

Yes, and the interesting version is on the Pulsar chatbot, where the retrieved templates function
as the examples.

That is worth unpacking because it is the thing that makes RAG and few-shot prompting the same
mechanism in practice. When an operator describes a template they want, the system retrieves real
existing templates relevant to that description and puts them in the context. The model is
completing a pattern demonstrated by genuine examples from the corpus, not inventing structure from
its priors. That is dynamic few-shot — examples selected per request by similarity, rather than a
fixed set — and it is materially better than a static set because the examples are always relevant
to the specific request.

It also matters more on a constrained model. Running a smaller open-weight model in an on-premise
deployment means the escape hatch of upgrading the model tier is unavailable, so the quality has to
come from the context. Good retrieved examples do more for a small model than a large model does
with poor ones.

The details he would flag from doing it:

- **Format consistency matters more than people expect** — keeping the structure and delimiters
  identical across examples is the highest-leverage detail, because much of what few-shot examples
  communicate is the shape of the task rather than its content.
- **Examples cost tokens on every single request.** Twenty examples in a prompt is twenty examples
  billed, or twenty examples of prefill latency, every time. That cost is the main economic argument
  for fine-tuning once volume justifies it.
- **Order affects output**, and recency bias means the last example carries extra weight.

On the prompt-evaluation work with Hugging Face, prompt variants included different example
selections scored against the labelled set, so "which examples" was a measured decision rather than
a guess.

**Follow-up.** *"Is dynamic few-shot just RAG?"* — Mechanically, nearly. The difference is intent:
RAG retrieves facts to answer from, dynamic few-shot retrieves examples to imitate. The Pulsar
chatbot does both at once.

**Grounded in.** Pulsar retrieval of existing templates as context, constrained on-premise model, NLP prompt-evaluation loop

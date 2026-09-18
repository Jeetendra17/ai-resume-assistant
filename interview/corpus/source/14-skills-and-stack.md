# Part 14 — Skills, Tools and Stack

> Questions that check a skills list against reality. The pattern in these answers is to separate
> three levels honestly — used in production, used in finished projects, and learned or explored —
> because a flat list of keywords hides exactly the distinction a hiring manager needs.

### Q14.1 — How strong is his Python?

- **Difficulty:** engineer
- **Tags:** python, skills, depth
- **Asked by:** Engineer, Hiring Manager

**Answer.**

Python is his primary language by a wide margin, and it is the one skill on his list used everywhere: in
production at Venera, in every project, and throughout this site.

The evidence of level, rather than the claim:

- **Production:** 150 automated test scripts in Python with Selenium and the Page Object Model on a live
  platform, and the generative-AI chatbot he is building now.
- **This site's backend** is Python with no framework beyond Flask: a BM25 index written from scratch, with
  stemming, phrase normalisation and weighted query expansion; a provider layer where seven vendors share one
  adapter through subclassing; prompt assembly and history sanitisation; and an evaluation harness that exits
  non-zero for use as a build gate. Plus a PDF generator that auto-fits the resume to one page, and the parser for
  this interview corpus.
- **Idioms that show up in the code**: dataclasses for records, generators for streaming data, decorators, careful
  use of `None` versus empty, type hints on public interfaces, standard-library HTTP to avoid a dependency where one
  was not needed, and comments that explain *why* at the exact points where the obvious-looking code is wrong.

Where it stops: he has not built a large Python service with many contributors, has not done serious performance
work below the level of choosing the right algorithm, and has not worked much with async at scale. Call it solid
working Python for application and tooling code, applied with care, at an early-career level of breadth.

The honest way to check it is to read the repository. It is public, and most of it is his own.

**Follow-up.** *"Does he write tests in Python?"* — Yes: the retrieval evaluation suite and the checks around the
interview corpus, plus six months of pytest and Selenium work professionally.

**Grounded in.** Skills list (Python primary), internship 150 Python scripts, core/rag.py, core/providers.py, build_resume.py, interview corpus parser

### Q14.2 — Which of his AI skills are production-grade and which are learned?

- **Difficulty:** hiring-manager
- **Tags:** skills, levels, honesty, ai
- **Asked by:** Hiring Manager, Recruiter

**Answer.**

The skills list is flat; the reality is layered. Sorted honestly:

**Used in production, at Venera:**
- Retrieval-augmented generation, with embedding-based retrieval over a local vector store
- Open-weight models (Qwen) running inside an on-premise deployment
- Prompt engineering and grounding
- Structured output with schema validation
- LLM evaluation — writing and maintaining the eval set

**Used in finished projects with measured results:**
- LangChain and Pinecone (document Q&A over 200 pages, ~70% faster retrieval)
- OpenAI API, Streamlit
- Hugging Face Transformers for classification and summarisation, with a prompt-evaluation loop
- BM25 and lexical retrieval engineering, multi-provider LLM integration with failover (this site)
- Hybrid retrieval and a LangGraph agent over the interview corpus behind this assistant

**Learned, explored, or experimental:**
- LangGraph beyond the graph on this site — listed on his resume as "exploring"
- Fine-tuning with LoRA — dataset and evaluation scaffolding plus experiments, not a production fine-tune
- The breadth of the AI Engineer Bootcamp syllabus, which is in progress

**Not claimed:** model training from scratch, distributed training, inference serving at scale, research.

The reason to lay it out this way is that the bottom tier is where resumes usually overstate, and a hiring manager
who discovers one inflated keyword discounts all the others. The top tier is the part worth testing in an interview,
because it is where he has had to make decisions under constraints.

**Follow-up.** *"Is anything on the list there just for keyword matching?"* — The items he would defend least are the
ones in the third tier, and they are labelled as such here.

**Grounded in.** Skills list, Pulsar chatbot, Document Q&A and NLP projects, portfolio assistant, certifications, "exploring LangGraph"

### Q14.3 — Does he know SQL and databases?

- **Difficulty:** recruiter
- **Tags:** sql, mysql, databases, skills
- **Asked by:** Recruiter, Engineer

**Answer.**

SQL and MySQL are on his skills list, supported by one project and one certification.

- **Student Data Entry System** — a Java servlet CRUD application backed by MySQL, where optimising the JDBC queries
  reduced average database response time by 30%. That is the concrete evidence of working database code, including
  some query tuning.
- **Database Fundamentals** from LinkedIn Learning — relational modelling and SQL — completed.

What that adds up to: comfortable with relational modelling, writing and tuning queries, and application-level database
access. It is not a claim of database administration, large-schema design, or performance work on big datasets.

For AI engineering specifically, the relevant database skills are shifting. Vector stores are the new part — he has used
Pinecone on a project and a locally run vector store in production at Venera — and relational databases remain where the
metadata, filtering and access control around a retrieval system usually live. A well-built RAG system filters by metadata
in the query to the index, not after retrieval, and that is a SQL-shaped way of thinking even when the store is not
relational.

He would say plainly that SQL is a supporting skill for him rather than a strength, and that he would expect to deepen it
on a team that uses it heavily.

**Follow-up.** *"Has he used Postgres or pgvector?"* — Not covered by the resume. Worth asking him directly rather than
assuming.

**Grounded in.** Skills list (SQL/MySQL), Student Data Entry System (-30% DB response time), Database Fundamentals certification, Pinecone, Pulsar vector store

### Q14.4 — What testing tools does he know?

- **Difficulty:** recruiter
- **Tags:** testing, tools, selenium, pytest, postman
- **Asked by:** Recruiter, Engineer

**Answer.**

This is the most thoroughly exercised part of his toolset, because it was his job for six months.

- **pytest** — Python test framework, used professionally and in his own work.
- **Selenium WebDriver** with the **Page Object Model** — 150 automated scripts on Venera's platform; the POM
  structure is what keeps a suite that size maintainable.
- **Selenium Grid** — parallel cross-browser execution across three browsers and two operating systems, which cut
  manual cross-browser effort by about 80%.
- **Postman** — REST API validation across 120 endpoints on AWS microservices, at a 98.3% pass rate.
- **JUnit** — Java unit testing.
- **Practices:** SDLC, boundary value analysis, exploratory testing, defect lifecycle management in Zoho, and test
  assets under pull-request review in Bitbucket.

And the one that matters most for an AI role, which is not a tool: **evaluation design for non-deterministic systems.**
Knowing that you cannot assert exact output from a sampled model, that the deterministic layers around it should be unit
tested normally, that quality is measured on a labelled set scored on properties, and that the must-refuse cases are the
half people forget. He has built three such evaluation sets.

What he has less of: load and performance testing tools, contract testing, and property-based testing. If a role needs
someone to own performance testing, that is new ground.

**Follow-up.** *"Does he still write tests now that he's building?"* — Yes. He owns the testing of the feature he built,
including the evaluation set, and he argues that is the right arrangement.

**Grounded in.** Skills list (Testing & Quality), internship metrics, Selenium Grid project, Postman endpoint validation, eval sets

### Q14.5 — What cloud and DevOps experience does he have?

- **Difficulty:** recruiter
- **Tags:** aws, azure, devops, cicd, skills
- **Asked by:** Recruiter, Engineer

**Answer.**

Working experience within established systems rather than ownership of infrastructure — accurate for his level.

**AWS** is the substantive one. He has worked since February 2026 on Quasar, Venera's cloud-native media QC product
built as microservices on AWS: validating 75 of its REST endpoints, and doing AWS cloud-native release readiness as a
defined part of his role.

**CI/CD and tooling:** Jenkins, Git and GitHub, Bitbucket, Gradle and Maven are on his list. In practice he has worked
within pipelines — automated suites running as quality gates, builds and releases as part of release readiness — rather
than building them.

**Deployment of his own work:** this site runs on Vercel's free tier with deployment configuration for Render, Docker on
Hugging Face Spaces and Gunicorn as alternatives, deploys automatically when he pushes to GitHub, and has scripts that
push environment configuration to the platform without echoing secrets. He tuned the request timeout to the platform's
function limit so the model failover can complete inside it.

**Azure** is on the list at a lower level of depth than AWS.

What he has not done: designed cloud architecture from scratch, written infrastructure as code for a real system, managed
IAM or networking at organisation scale, run Kubernetes, or done cloud cost optimisation. If a role needs a DevOps or
platform engineer, he is not that.

**Follow-up.** *"Can he containerise an application?"* — The repository includes a working Dockerfile for the site. He has
not operated containers in production at scale.

**Grounded in.** Quasar AWS microservices, 75 endpoints, release readiness, skills list (Cloud & DevOps), Dockerfile, deploy scripts, Vercel GitHub integration

### Q14.6 — Does he know Java, Kotlin or C++?

- **Difficulty:** recruiter
- **Tags:** languages, java, kotlin, cpp
- **Asked by:** Recruiter

**Answer.**

They are on his skills list, each backed by specific work, and he would not claim current depth in any of them.

- **Java** — the Student Data Entry System, a servlet-based CRUD application over MySQL with JDBC query tuning, plus JUnit
  on the testing side and object-oriented design generally.
- **Kotlin** — his Android internship at NullClass, building and optimising mobile applications, and a real-time chat app
  with Firebase, secure authentication and sub-second message sync.
- **C and C++** — from his computer science degree.

The honest ranking is Python far ahead, then Java and Kotlin as languages he has shipped something in, then C and C++ as
academic. If a role needs production Java or Kotlin, he would be ramping up rather than contributing at full speed from the
first week.

The part worth knowing about the older projects: they are why his retrieval evaluation exists. Asked what he had shipped
with LLMs, an early version of his assistant returned the Kotlin chat app and the Java CRUD system, because broad synonyms
matched every project equally. So the projects are less relevant to an AI role than the lesson they produced.

**Follow-up.** *"Would he rather work in Python?"* — For AI engineering, yes, since that is where the ecosystem is. Worth
asking him about openness to other languages if the role needs one.

**Grounded in.** Skills list (Languages), Student Data Entry System, NullClass internship, Real-Time Chat App, build log bug 02

### Q14.7 — What is his experience with Git and collaboration tools?

- **Difficulty:** recruiter
- **Tags:** git, collaboration, tools
- **Asked by:** Recruiter, Engineer

**Answer.**

Routine professional use.

At Venera: **Bitbucket** for source control with structured pull-request reviews on test assets, and **Zoho** for defect
tracking — 79 defects managed, 61 resolved, 10 critical.

For his own work: **Git and GitHub**. This site's repository is public, and its history is written the way he would want
a teammate's to be — small commits with messages that explain *why* the change was made, not just what changed. The build
log on the site is effectively a set of structured incident notes.

He has worked in structured review as a participant rather than as someone setting review standards, and on a small team
rather than a large repository with many concurrent contributors. He has not had to manage complex branching, long-lived
release branches, or large merge conflicts across a big team.

What he would say about review, from being reviewed: the most valuable review comment is a "why" rather than a proposed
alternative, because it surfaces whether the author had a reason. And the code comments he writes are aimed at a future
reviewer — they appear exactly where the correct-looking code is wrong, so nobody "tidies" a deliberate choice back into
a bug.

**Follow-up.** *"Is the portfolio history clean?"* — Look at it; it is public. Commits are scoped to one concern each and
explain the reasoning.

**Grounded in.** Bitbucket with PR reviews, Zoho defect management, public GitHub repository, build log

### Q14.8 — How good is he at explaining technical work to non-technical people?

- **Difficulty:** hiring-manager
- **Tags:** communication, writing, stakeholders
- **Asked by:** Hiring Manager, Recruiter

**Answer.**

The best evidence is the site itself, since most of it is technical work written for an audience that is not purely
technical.

The About section explains a retrieval system — why BM25 instead of embeddings, why nine providers, why it answers with no
API keys — in terms of the decision and its consequence rather than the mechanism. The build log explains twelve bugs as
symptom, cause and fix, in plain language, without hiding the embarrassing ones. That is a structure that works for a
recruiter and an engineer at the same time.

His professional communication is the other evidence: defining acceptance criteria with product teams, which is translating
between what product wants and what engineering can verify; and defect reports, which are only useful if a developer can
reproduce the problem from the write-up alone.

The specific habit he has is naming consequences instead of mechanisms. "An invalid template means an operator runs quality
control with checks they did not ask for" lands with a product manager where "the output failed schema validation" does not.
Same fact, different audience.

What he would not claim: presentation experience to large audiences or executive stakeholders. His communication is mostly
written and one-to-one, at the level you would expect a year into a career.

**Follow-up.** *"Can he write documentation?"* — The repository's README and deployment guide are his, including a runbook
for deploying changes. Judge from those.

**Grounded in.** About section write-up, build log format, acceptance criteria work, defect management, README and DEPLOYMENT_PLAN

### Q14.9 — What tools would he need to learn to be effective here?

- **Difficulty:** hiring-manager
- **Tags:** onboarding, learning, gaps
- **Asked by:** Hiring Manager

**Answer.**

It depends on your stack, and this assistant does not know your stack — so the useful answer is which categories are new
to him and which transfer immediately.

**Transfers immediately:** Python, retrieval and RAG design, prompt engineering and grounding, evaluation design, structured
output and validation, LangChain, Git-based workflows, AWS basics, working inside a release process.

**Short ramp — he has adjacent experience:**
- A different vector store or embedding model (he has used Pinecone and a local store; the concepts carry over).
- A different LLM provider or SDK (he has integrated nine behind one interface).
- A different agent framework (he has built with LangGraph).
- A different CI system (he has worked within Jenkins-based pipelines).

**Genuinely new — expect real learning time:**
- Inference serving at scale (vLLM, TensorRT-LLM, GPU capacity planning).
- Observability for model quality in production, beyond logging.
- Infrastructure as code, Kubernetes, or container orchestration.
- Any language other than Python at production depth.
- Tools specific to your domain.

His learning pattern is visible across his projects: he learns a technique and then immediately builds the thing that
tells him whether it is working. The Hugging Face work came with a prompt-evaluation loop; this site came with a retrieval
evaluation suite; the Venera feature came with an evaluation set he wrote himself. That habit is probably a better predictor
of ramp-up speed than any list of tools.

**Follow-up.** *"How fast did he pick up the Venera AI stack?"* — He moved onto it in August and it is his primary work now,
with an external consultant available for direction. Ask him what was hardest.

**Grounded in.** Skills list, provider integrations, LangGraph agent, Pinecone and local vector store, learning pattern across projects

### Q14.10 — Has he used Streamlit, Flask or other app frameworks?

- **Difficulty:** recruiter
- **Tags:** flask, streamlit, frameworks, web
- **Asked by:** Recruiter, Engineer

**Answer.**

Two, for different purposes, and he chose each for a reason.

**Streamlit** — on the document Q&A chatbot. It is the right tool for putting an interface on a data or ML workflow quickly:
a working UI in a few dozen lines with no front-end code. The trade-off is limited control over layout and behaviour, which is
fine for an internal tool or a demo and constraining for a public product.

**Flask** — for this site. He needed full control over the page, a public API for the chat, server-rendered HTML so the content
is readable without JavaScript, and something small enough to deploy as a serverless function on a free tier. Flask with Jinja
templates, one stylesheet and a vanilla JavaScript file does all of that with almost no dependency weight. The API has a chat
route, a health route with an opt-in live probe, and a resume route.

The deliberate absence on the list is a front-end framework such as React. For a handful of sections and one chat panel it would
have added a build pipeline and a bundle for interactions that are a few event listeners, so he did not use one. That is a
proportionality call, not a claim that he could not.

He has not used FastAPI or Django in anything significant, and he would not claim otherwise; for an async model-serving API,
FastAPI would be the more natural choice than Flask, and he would expect to pick it up quickly.

**Follow-up.** *"Why not FastAPI for the site?"* — The site is a few routes with synchronous calls under a strict timeout, and
Flask's footprint suited the free serverless target. For a high-concurrency inference gateway he would choose differently.

**Grounded in.** Document Q&A Chatbot (Streamlit), portfolio Flask app, app.py routes, vanilla JS front end

### Q14.11 — What does his AI Engineer Bootcamp cover, and is it worth anything?

- **Difficulty:** recruiter
- **Tags:** certification, bootcamp, learning, credibility
- **Asked by:** Recruiter, Hiring Manager

**Answer.**

It is **The AI Engineer Bootcamp 2026** from 365 Careers on Udemy, currently in progress. The syllabus covers LLMs, NLP,
LangChain, LangGraph, Hugging Face, Pinecone, the OpenAI API, RAG and Streamlit.

On its worth, he would give the same answer a sceptical hiring manager would: a course certificate on its own proves very
little. It shows that someone chose to learn a subject, not that they can apply it.

What makes it more useful in his case is what it sits next to. The techniques on that syllabus show up in things he actually
built and measured:

- RAG, LangChain and Pinecone → the document Q&A chatbot, with a measured ~70% retrieval-time reduction.
- Hugging Face and NLP → the pipelines with a prompt-evaluation loop scored against a labelled set.
- LangGraph → the agent graph running over the interview corpus behind this assistant.
- LLMs and RAG generally → the production feature at Venera, which runs on open-weight models rather than the hosted API the
  course centres on — so he has had to apply the ideas beyond what the course covered.

He would describe the course as where he learned the vocabulary and the job as where he learned the work. Worth weighting
accordingly: low on its own, a reasonable signal of deliberate learning when it lines up with shipped work.

Other certifications, all completed: Android Developer Badges from Google, and Database Fundamentals and Design Thinking from
LinkedIn Learning.

**Follow-up.** *"When will he finish it?"* — Not covered by the resume. It is listed as in progress.

**Grounded in.** Certifications list (AI Engineer Bootcamp 2026 in progress; Google and LinkedIn completed), projects mapped to syllabus

"""Single source of truth for everything the site renders and the assistant knows.

Edit this file to update the portfolio — the UI, the chat retrieval index and the
system prompt all read from here.
"""

PROFILE = {
    "name": "Jeetendra Kumar Patel",
    "initials": "JP",
    "role": "AI Engineer",
    "title": "Associate Software Engineer -> AI Engineer",
    "tagline": "Shipping reliable systems today, building intelligent ones next.",
    "location": "Noida, Uttar Pradesh, India",
    "email": "jeetendrapatel1711@gmail.com",
    "phone": "+91 7000957216",
    "linkedin": "https://linkedin.com/in/jeetendra-kumar-patel-b73650239",
    "github": "https://github.com/Jeetendra17/ai-resume-assistant",
    "site": "https://jeetendra.vercel.app",
    "resume_file": "Jeetendra_Kumar_Patel_AI_Engineer_Resume.pdf",
    "photo": "img/profile.jpg",
    "available": True,
    "availability_note": "Open to AI Engineer / ML Engineer roles",
    "summary": (
        "Associate Software Engineer at Venera Technologies, converted to full-time after a "
        "6-month internship that delivered 150 automated Python test scripts, 120 validated API "
        "endpoints and zero critical defects shipped across AWS cloud-native microservices. "
        "Strong foundation in SDLC, OOP and quality engineering, now building on it with applied "
        "AI engineering — LLMs, LangChain, LangGraph, Hugging Face and RAG."
    ),
    "pitch": (
        "I bring something most junior AI engineers do not: production discipline. I have shipped "
        "into a real AWS cloud media platform, owned release readiness, and measured everything I "
        "built. I am applying that same rigour to LLM systems — retrieval quality, grounding and "
        "latency are things I measure, not things I assume."
    ),
}

# Split hero. `accent` renders in serif italic — the one deliberate typographic
# moment on the page, borrowed from the SaaS landing reference.
HERO = {
    "eyebrow": "Available for AI Engineer roles",
    "line_1": "I build AI systems the same way I",
    "accent": "ship production software",
    "line_2": "",
    "sub": (
        "Associate Software Engineer at Venera Technologies by day, building LLM and RAG "
        "systems the rest of the time. Everything below has a number attached to it."
    ),
    "primary_cta": "Ask my AI assistant",
    "secondary_cta": "View resume",
    "proof": "Zero critical defects across 7 production builds",
}

# Three-up "what I actually do" strip under the hero.
FOCUS = [
    {
        "title": "Retrieval systems",
        "icon": "layers",
        "tone": "purple",
        "text": "Chunking, embeddings and vector search that returns the right passage — then proving it does with evaluation, not vibes.",
        "tools": ["LangChain", "Pinecone", "Embeddings"],
    },
    {
        "title": "LLM application engineering",
        "icon": "spark",
        "tone": "blue",
        "text": "Prompt design, grounding and structured outputs, wired into apps people can actually use.",
        "tools": ["OpenAI API", "Hugging Face", "Streamlit"],
    },
    {
        "title": "Production discipline",
        "icon": "check",
        "tone": "green",
        "text": "The part most AI portfolios skip: test coverage, release readiness and defect triage on live AWS services.",
        "tools": ["Python", "pytest", "AWS", "CI/CD"],
    },
]

# Headline numbers — the first thing a recruiter should see.
METRICS = [
    {
        "label": "Automated test scripts",
        "value": "150",
        "detail": "Python + Selenium, Page Object Model",
        "trend": "-65% manual regression time",
        "tone": "blue",
    },
    {
        "label": "REST endpoints validated",
        "value": "120",
        "detail": "Postman across AWS microservices",
        "trend": "98.3% pass rate",
        "tone": "green",
    },
    {
        "label": "Critical defects in production",
        "value": "0",
        "detail": "Across 7 consecutive builds",
        "trend": "sev-1 intercepted pre-release",
        "tone": "purple",
    },
    {
        "label": "Retrieval time reduced",
        "value": "~70%",
        "detail": "RAG chatbot over a 200-page corpus",
        "trend": "LangChain + Pinecone",
        "tone": "amber",
    },
]

SKILL_GROUPS = [
    {
        "name": "AI & LLM Engineering",
        "icon": "sparkle",
        "focus": True,
        "items": [
            "LLMs (OpenAI API)",
            "LangChain",
            "LangGraph",
            "Hugging Face Transformers",
            "RAG",
            "Pinecone",
            "Embeddings",
            "Prompt Engineering",
            "NLP",
            "Streamlit",
        ],
    },
    {
        "name": "Languages",
        "icon": "code",
        "focus": False,
        "items": ["Python", "SQL / MySQL", "Java", "Kotlin", "C / C++"],
    },
    {
        "name": "Testing & Quality",
        "icon": "check",
        "focus": False,
        "items": [
            "pytest",
            "Selenium WebDriver",
            "Page Object Model",
            "Selenium Grid",
            "Postman",
            "JUnit",
            "SDLC",
            "BVA",
        ],
    },
    {
        "name": "Cloud & DevOps",
        "icon": "cloud",
        "focus": False,
        "items": ["AWS", "Azure", "Jenkins", "CI/CD", "Git / GitHub", "Bitbucket", "Gradle", "Maven", "Zoho"],
    },
]

EXPERIENCE = [
    {
        "role": "Associate Software Engineer",
        "company": "Venera Technologies",
        "location": "Noida",
        "period": "Aug 2026 - Present",
        "current": True,
        "status": "Current",
        "summary": "Full-time conversion after a 6-month internship. Working across the full SDLC on Venera's media QC platform — Quasar (cloud, AWS) and Pulsar (on-premise).",
        "points": [
            "Contribute across the full SDLC using OOP principles and QA best practices to improve product quality and reliability for Venera's cloud media QC platform.",
            "Collaborate with dev and product teams to define acceptance criteria, review test strategies and ensure AWS cloud-native release readiness — reducing defect escape rate sprint over sprint.",
        ],
        "stack": ["Python", "AWS", "OOP", "SDLC", "CI/CD"],
    },
    {
        "role": "Graduate Trainee / QA Engineer",
        "company": "Venera Technologies",
        "location": "Noida",
        "period": "Feb 2026 - Aug 2026",
        "current": False,
        "status": "Converted to full-time",
        "summary": "Six-month internship that converted to a full-time offer on measured impact.",
        "points": [
            "Engineered 150 automated Python test scripts (Selenium + POM) — cut manual regression time by 65%, reached 78% P1/P2 coverage and caught 3 critical regressions pre-release.",
            "Validated 120 REST API endpoints via Postman across AWS microservices (75 on Quasar, the cloud QC product; 45 on Pulsar, the on-premise one); 98.3% pass rate and 2 production-blocking defects resolved before deployment.",
            "Delivered zero critical defects to production across 7 builds; intercepted a severity-1 503 failure and coordinated a same-day hotfix, saving roughly 4 hours of user-facing downtime.",
            "Managed 79 defects in Zoho (61 resolved, 10 critical) and maintained test assets in Bitbucket with structured PR reviews.",
        ],
        "stack": ["Python", "Selenium", "Postman", "AWS", "Zoho", "Bitbucket"],
    },
    {
        "role": "AI Engineering Projects",
        "company": "Self-directed / Bootcamp",
        "location": "Remote",
        "period": "2026 - Present",
        "current": True,
        "status": "Ongoing",
        "summary": "Deliberate practice track: building LLM systems end to end, not just calling APIs.",
        "points": [
            "Architected a document Q&A chatbot (LangChain + OpenAI + Pinecone + Streamlit) — reduced retrieval time by roughly 70% across a 200-page knowledge base.",
            "Built NLP pipelines with Hugging Face Transformers, plus a prompt-evaluation loop that scores variants against a hand-labelled question set so answer quality is measured rather than eyeballed.",
            "Exploring LangGraph for multi-agent, stateful AI workflows.",
        ],
        "stack": ["LangChain", "OpenAI API", "Pinecone", "Hugging Face", "LangGraph", "Streamlit"],
    },
    {
        "role": "Android Developer (Internship)",
        "company": "NullClass",
        "location": "Remote",
        "period": "Prior to Feb 2026",
        "current": False,
        "status": "Completed",
        "summary": "Mobile delivery experience before pivoting to backend and AI.",
        "points": [
            "Built and optimised Android mobile applications, gaining hands-on experience in Kotlin, UI performance tuning, Firebase integration and mobile SDLC delivery.",
        ],
        "stack": ["Kotlin", "Firebase", "Android"],
    },
]

PROJECTS = [
    {
        "name": "This Portfolio + Resume Assistant",
        "category": "AI / Full-stack",
        "featured": True,
        "case_study": True,
        "blurb": (
            "The site you're reading. A Flask app with a retrieval-grounded assistant that answers "
            "recruiter questions from my resume — sub-millisecond local retrieval, nine "
            "interchangeable model providers, and a fallback that still answers with zero API keys."
        ),
        "impact": "0 vendor lock-in",
        "details": [
            "BM25 index over the resume, built in-process — no vector database, no embedding API, ~0.04 ms per query, 36/36 on its eval set.",
            "Nine LLM providers behind one interface; the chain fails over automatically and degrades to extractive answers if every one is unavailable.",
            "Answers cite the resume section they came from, so a recruiter can check the source.",
        ],
        "stack": ["Python", "Flask", "BM25", "RAG", "Groq", "Gemini", "Vanilla JS"],
        "source": "https://github.com/Jeetendra17/ai-resume-assistant",
        "tone": "purple",
    },
    {
        "name": "Document Q&A Chatbot (RAG)",
        "category": "AI / LLM",
        "featured": True,
        "blurb": "Retrieval-augmented Q&A over a 200-page knowledge base with grounded, citation-friendly answers.",
        "impact": "~70% faster retrieval",
        "details": [
            "Chunking + embedding pipeline with Pinecone as the vector store.",
            "LangChain orchestration over the OpenAI API, served through Streamlit.",
            "Prompting pass focused on grounding: answers constrained to retrieved passages, with unsupported responses tracked as a metric rather than estimated.",
        ],
        "stack": ["LangChain", "OpenAI API", "Pinecone", "Streamlit", "Python"],
        "tone": "purple",
    },
    {
        "name": "NLP Pipelines with Hugging Face",
        "category": "AI / NLP",
        "featured": True,
        "blurb": "Transformer-based text pipelines for classification and summarisation, with prompt variants scored against a labelled set instead of judged by eye.",
        "impact": "measured, not guessed",
        "details": [
            "Hugging Face Transformers for tokenisation, inference and fine-tuning experiments.",
            "Prompt-evaluation loop: each variant scored against a hand-labelled question set, tracking unsupported answers as a metric.",
            "Currently extending toward LangGraph multi-agent, stateful workflows.",
        ],
        "stack": ["Hugging Face", "Transformers", "Python", "LangGraph"],
        "tone": "blue",
    },
    {
        "name": "Selenium Grid Automation",
        "category": "Quality Engineering",
        "featured": False,
        "blurb": "Parallel cross-browser regression suite across 3 browsers and 2 operating systems.",
        "impact": "-80% manual cross-browser effort",
        "details": [
            "Selenium Grid running suites in parallel across browser/OS combinations.",
            "Halved pre-release validation time for the team.",
        ],
        "stack": ["Selenium Grid", "Python", "pytest", "CI/CD"],
        "tone": "green",
    },
    {
        "name": "Real-Time Chat App",
        "category": "Mobile",
        "featured": False,
        "blurb": "Android chat application with secure auth and sub-second message sync.",
        "impact": "stable under concurrent load",
        "details": [
            "Kotlin + Firebase realtime backend with secure authentication.",
            "Sub-second sync, verified stable under concurrent multi-user load.",
        ],
        "stack": ["Kotlin", "Firebase", "Android"],
        "tone": "amber",
    },
    {
        "name": "Student Data Entry System",
        "category": "Backend",
        "featured": False,
        "blurb": "Java servlet CRUD application backed by MySQL with tuned JDBC access.",
        "impact": "-30% avg DB response time",
        "details": [
            "Servlet-based CRUD app over MySQL.",
            "Optimised JDBC queries reduced average database response time by 30%.",
        ],
        "stack": ["Java", "MySQL", "JDBC", "Servlets"],
        "tone": "blue",
    },
]

# The About section: a short professional bio, then a technical write-up of this
# site. Every figure here is measured from the running app, not estimated.
ABOUT = {
    "eyebrow": "About",
    "title": "Engineer first, then AI engineer",
    "bio": [
        "I started where most AI engineers do not: in quality engineering, on a product that real "
        "customers depend on. Six months into an internship at Venera Technologies I had written "
        "150 automated test scripts, validated 120 API endpoints across AWS microservices, and "
        "shipped seven builds without a single critical defect reaching production. That converted "
        "into a full-time offer.",
        "What that taught me is the part I now bring to AI work: a system is not done when it "
        "produces output, it is done when you can show it produces the right output. I have watched "
        "a severity-1 failure get caught an hour before release because someone bothered to check. "
        "That instinct transfers directly to LLM systems, where the failure mode is a confident "
        "wrong answer rather than a stack trace.",
        "So I am building in that direction deliberately — retrieval, grounding, prompt evaluation, "
        "and agent workflows with LangGraph — and measuring as I go. The assistant on this page is "
        "the clearest example, and the write-up below is the honest version of how it works.",
    ],
    "build_title": "About this site",
    "lede": (
        "Most portfolios claim AI experience. This one runs it. The chat box on this page is a "
        "retrieval-augmented assistant over my own resume — and the engineering decisions behind "
        "it are the real portfolio piece, so here they are in full."
    ),
    # Measured against the running app — re-run the timing snippet in the README
    # if the corpus changes, rather than letting these drift.
    "stats": [
        {"value": "36/36", "label": "retrieval eval passing", "detail": "29 must-match + 7 must-decline questions"},
        {"value": "0.04 ms", "label": "retrieval per query", "detail": "in-process BM25, measured over 2,900 runs"},
        {"value": "9", "label": "interchangeable providers", "detail": "7 with free tiers"},
        {"value": "28", "label": "indexed resume chunks", "detail": "no vector database"},
    ],
    "flow": [
        {"step": "1", "name": "Question", "text": "Recruiter asks in plain language — \"is he a fit?\", not resume keywords."},
        {"step": "2", "name": "Retrieve", "text": "BM25 scores every resume chunk. A synonym layer maps hiring language onto resume vocabulary."},
        {"step": "3", "name": "Ground", "text": "Top chunks become a labelled context block. The system prompt forbids answering outside it."},
        {"step": "4", "name": "Generate", "text": "First healthy provider in the chain answers. If all fail, the retrieved text is returned directly."},
        {"step": "5", "name": "Cite", "text": "The response carries the chunk titles it drew from, so claims are checkable."},
    ],
    "decisions": [
        {
            "title": "BM25 instead of embeddings",
            "tone": "purple",
            "call": "Lexical search, no vector database",
            "why": (
                "The corpus is a few dozen short chunks. Embeddings would add an API round trip, a cold "
                "start and a bill for recall I can't measure a gain from at this scale. BM25 runs "
                "in-process in 0.04 ms and has no failure mode. The interesting problem here isn't "
                "similarity — it's that recruiters ask \"can he do X\" while resumes say \"built X\", "
                "so I added stemming, phrase normalisation and a weighted synonym layer to bridge "
                "that vocabulary gap. Cheaper and more targeted than reaching for a bigger model."
            ),
        },
        {
            "title": "An eval set, because I got it wrong",
            "tone": "amber",
            "call": "29 recruiter questions, scored on every change",
            "why": (
                "Someone asked the assistant \"what has he actually shipped with LLMs?\" and it "
                "returned a Kotlin chat app and a Java CRUD app. The cause was mine: broad synonyms "
                "like \"shipped\" → \"project\" matched every project chunk equally and drowned out "
                "the one word that mattered. I wrote an eval set of 29 questions with expected "
                "source chunks, reproduced the failure at 26/29, then fixed scoring until it hit "
                "29/29. A second round added must-decline cases, after it padded an unrelated personal "
                "question with the career summary instead of saying the resume doesn't cover it. "
                "Retrieval changes are scored now, not eyeballed — which is the whole claim "
                "this site makes, so it should hold here first."
            ),
        },
        {
            "title": "Nine providers, one interface",
            "tone": "blue",
            "call": "Provider-agnostic with automatic failover",
            "why": (
                "A portfolio that dies when one free tier rate-limits is worse than no portfolio. "
                "Groq, Gemini, Cerebras, OpenRouter, Mistral, Together, Ollama, Anthropic and "
                "OpenAI sit behind one adapter — the seven OpenAI-compatible ones share a single "
                "implementation. The chain tries each in turn, so a 429 on one is invisible to the "
                "visitor. Swapping the default model is one environment variable."
            ),
        },
        {
            "title": "It answers with zero API keys",
            "tone": "green",
            "call": "Graceful degradation, not an error page",
            "why": (
                "If every provider is missing or down, the app returns the retrieved resume text "
                "directly instead of a stack trace. Retrieval is local, so it cannot fail with the "
                "network. This is the QA habit showing up in AI work: design the failure path first, "
                "then make the happy path better than it."
            ),
        },
        {
            "title": "One file is the source of truth",
            "tone": "amber",
            "call": "Rendered pages and retrieval index share an origin",
            "why": (
                "Every page, the retrieval corpus and the system prompt all derive from a single "
                "profile module. It's structurally impossible for the site to say one thing and the "
                "assistant another — a class of bug I've watched cost real debugging time. Updating "
                "my experience means editing one file."
            ),
        },
    ],
    "guardrails": [
        "Answers are constrained to retrieved context; the prompt forbids inventing employers, dates, titles or numbers.",
        "Unknown questions return \"that's not in the resume\" plus my email, rather than a plausible guess.",
        "The prompt explicitly instructs honesty about early-career level instead of overselling.",
        "Model output is HTML-escaped before markdown rendering, so a response can't inject markup.",
        "Per-IP rate limiting keeps a stray script from draining a free tier.",
    ],
    "next": [
        "Swap in hybrid retrieval (BM25 + embeddings) once the corpus grows past a few hundred chunks — the interface is already in place for it.",
        "Expand the eval set beyond 29 questions and wire it into CI so a bad retrieval change can't merge.",
        "Stream tokens to the client instead of waiting for the full response.",
    ],
    "stack": ["Python", "Flask", "BM25 / RAG", "Groq", "Gemini", "Jinja2", "Vanilla JS", "Gunicorn", "Docker"],
}

# Build log. Kept deliberately small on the page — a collapsed list under the
# write-up — but real: these all shipped broken before they were caught.
# NOTE: wording here is intentionally generic. Prose that names the terms a bug
# involved gets indexed and can reintroduce the exact match it describes (see #05).
BUGS = [
    {
        "id": "01",
        "title": "Template silently resolved a method instead of my data",
        "symptom": "Every page returned a 500 as soon as the skills section rendered.",
        "cause": (
            "The skills group is a dict with an \"items\" key, and Jinja resolves attributes "
            "before keys — so `g.items` returned Python's built-in dict method, not my list."
        ),
        "fix": (
            "Switched to `g['items']` and left a comment explaining why, since the attribute "
            "form looks correct and would be re-introduced by anyone tidying the template."
        ),
    },
    {
        "id": "02",
        "title": "Questions about LLM work returned unrelated projects",
        "symptom": (
            "Asked what had actually been shipped in the AI space, the assistant answered with "
            "a mobile chat app and a Java CRUD app."
        ),
        "cause": (
            "Query expansion was unweighted. Broad synonyms resolved to words my own chunk "
            "template stamps onto every project, so all projects scored the same noise while "
            "the single discriminating term was outvoted."
        ),
        "fix": (
            "Wrote an eval set first, reproduced the failure at 26/29, then gave typed terms "
            "full weight and expansions 0.3, and added light suffix stemming. 29/29."
        ),
    },
    {
        "id": "03",
        "title": "A multi-word term matched on the wrong sense",
        "symptom": "A question about model architecture surfaced the programming-languages list.",
        "cause": (
            "Token overlap without meaning overlap — the individual words matched a chunk "
            "about something entirely different."
        ),
        "fix": (
            "Added phrase normalisation so known multi-word terms collapse to a single "
            "canonical token before tokenising."
        ),
    },
    {
        "id": "04",
        "title": "Questions outside the resume got answered anyway",
        "symptom": (
            "Personal questions the resume says nothing about came back with the career "
            "summary attached, reading as though it had answered them."
        ),
        "cause": (
            "When retrieval scored nothing I substituted a few default chunks so there was "
            "always something to answer from. That destroyed the only signal meaning "
            "\"not covered\", so neither the prompt nor the fallback could decline."
        ),
        "fix": (
            "Retrieval returns empty now, and the app declines deterministically before any "
            "model call. Added must-decline cases to the eval so it can't come back."
        ),
    },
    {
        "id": "05",
        "title": "Documenting a bug reintroduced it",
        "symptom": "The eval dropped from 36/36 to 34/36 right after I wrote up bug #04.",
        "cause": (
            "The write-up is indexed like everything else, so naming the term that bug "
            "involved put it back in the corpus and made the question match again."
        ),
        "fix": (
            "Reworded the write-up generically. It is why this list avoids naming the "
            "specific terms involved — the eval is the only reason I noticed."
        ),
    },
    {
        "id": "06",
        "title": "Hand-written stats drifted from reality three times",
        "symptom": (
            "The write-up claimed a chunk count and index size that stopped being true every "
            "time content was added."
        ),
        "cause": "They were typed by hand in a section whose whole claim is that figures are measured.",
        "fix": (
            "The chunk count and eval score are computed from the running index at startup. "
            "The page now reports its own state instead of a remembered one."
        ),
    },
    {
        "id": "07",
        "title": "Serverless timeout would have killed the failover",
        "symptom": (
            "Caught in review before shipping: on the free serverless tier the platform would "
            "kill a slow request before the app could fall back to the next provider."
        ),
        "cause": "The app's own request timeout defaulted higher than the platform's function limit.",
        "fix": (
            "Documented a lower timeout for that platform in the deployment plan, so the app "
            "gives up and degrades gracefully inside the platform's window."
        ),
    },
    {
        "id": "08",
        "title": "Every model call was failing, and the health check said fine",
        "symptom": (
            "With a valid key configured, health reported the engine live — but every answer "
            "came back from the local index instead of the model."
        ),
        "cause": (
            "Two faults stacked. The HTTP layer sent Python's default user-agent, which the "
            "CDN in front of the provider rejects outright before the request reaches them. "
            "And the health check only asked whether a key was present, never whether the "
            "provider would actually answer — so the graceful fallback hid the failure."
        ),
        "fix": (
            "Set a real user-agent on every request, and split health into a cheap "
            "\"configured\" check and an opt-in probe that makes one live call and reports "
            "the true error. Only found it because the answers named their own source."
        ),
    },
    {
        "id": "09",
        "title": "Long answers opened at their last line",
        "symptom": (
            "Ask something with a multi-paragraph answer and the chat jumped to the bottom of "
            "it, so you landed on the closing sentence and had to scroll back up to read."
        ),
        "cause": (
            "Standard chat behaviour is to pin the newest message to the bottom, which is right "
            "for short turns and wrong for anything taller than the panel."
        ),
        "fix": (
            "New answers now scroll their first line to the top instead, clamped so a short "
            "reply doesn't leave dead space. Reported by a user, not caught in testing."
        ),
    },
    {
        "id": "10",
        "title": "The sidebar close button did nothing on desktop",
        "symptom": (
            "Clicking the close control in the sidebar header had no effect on a desktop "
            "window. No error, no movement, nothing."
        ),
        "cause": (
            "Below the breakpoint the sidebar is an overlay drawer driven by a state class; "
            "above it, the sidebar is part of the page layout, so that same class is inert. "
            "One handler was written for both. The button had never worked on desktop."
        ),
        "fix": (
            "The control now branches on breakpoint: dismiss the drawer on small screens, "
            "collapse the layout column on large ones. Collapsing also reveals the header "
            "menu button, since without a way back the close button would be a one-way trip."
        ),
    },
    {
        "id": "11",
        "title": "The status badge named a provider that wasn't answering",
        "symptom": (
            "With a rejected key, the badge on the page still displayed that provider's name "
            "with a green dot, while every reply was actually coming from the local index."
        ),
        "cause": (
            "The badge was rendered from what was configured, not from what responded — the "
            "same wrong assumption behind an earlier bug, which I fixed in the health endpoint "
            "and then failed to carry through to the part visitors actually see."
        ),
        "fix": (
            "Every reply already reports which engine produced it, so the badge is now "
            "corrected from that on the first answer. Probing at page load would be honest "
            "too, but it would spend a real API call on every visitor."
        ),
    },
]

EDUCATION = [
    {
        "degree": "B.E. Computer Science Engineering",
        "school": "Chandigarh University, Punjab",
        "period": "Graduated June 2026",
        "score": "CGPA 8.4 / 10",
    },
]

CERTIFICATIONS = [
    {
        "name": "The AI Engineer Bootcamp 2026",
        "issuer": "365 Careers, Udemy",
        "status": "In Progress",
        "detail": "LLMs, NLP, LangChain, LangGraph, Hugging Face, Pinecone, OpenAI API, RAG, Streamlit",
    },
    {"name": "Android Developer Badges", "issuer": "Google", "status": "Completed", "detail": "Kotlin, Android SDK"},
    {"name": "Database Fundamentals", "issuer": "LinkedIn", "status": "Completed", "detail": "Relational modelling, SQL"},
    {"name": "Design Thinking", "issuer": "LinkedIn", "status": "Completed", "detail": "Product discovery and problem framing"},
]

# Recruiter-facing quick prompts shown around the chat bar.
SUGGESTED_PROMPTS = [
    "Is Jeetendra a fit for an AI Engineer role?",
    "What has he actually shipped with LLMs?",
    "Walk me through his RAG project",
    "What are his strongest measurable results?",
    "How do you actually work? Explain your own architecture.",
    "What is he learning right now?",
]

NAV = [
    {"id": "home", "label": "Overview", "icon": "home"},
    {"id": "experience", "label": "Experience", "icon": "briefcase"},
    {"id": "projects", "label": "Projects", "icon": "layers"},
    {"id": "about", "label": "About", "icon": "user"},
    {"id": "skills", "label": "Skills", "icon": "chip"},
    {"id": "education", "label": "Education", "icon": "cap"},
    {"id": "contact", "label": "Contact", "icon": "mail"},
]

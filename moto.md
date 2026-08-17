Haan bhai. Tu **PaperPilot ka proper project spec/README-style MD** chahta hai, jisme idea, goal, architecture, workflow, MVP, future scope, preview sab ho. Ye le, seedha repo me `README.md` me daal dena. Human civilization survives another README. 😭

# PaperPilot 📚🚀

> Your autonomous daily research-paper radar.

PaperPilot is a personal research-paper aggregation and discovery system that automatically searches academic sources every day, identifies relevant and interesting papers, and publishes them as clean Markdown files directly to a GitHub repository.

The goal is not to build a state-of-the-art research framework.

The goal is to build a **well-engineered personal tool that removes the repetitive work of finding research papers**.

---

## 🎯 Goal

Reading research papers is important for staying current in Machine Learning, Data Science, AI, and related fields.

The problem is that discovering useful papers every day is repetitive:

```text
Search sources
      ↓
Check new papers
      ↓
Filter irrelevant papers
      ↓
Compare papers
      ↓
Collect links
      ↓
Save them somewhere
      ↓
Repeat tomorrow

PaperPilot automates this entire process.
```

Every morning, GitHub Actions automatically runs the pipeline, fetches newly published papers from academic APIs, processes them, removes duplicates, ranks or filters them, and generates a structured Markdown report.

The generated report is committed directly to the GitHub repository.

```text
GitHub Actions
      ↓
Fetch Papers
      ↓
Normalize Data
      ↓
Filter
      ↓
Deduplicate
      ↓
Rank
      ↓
Generate Markdown
      ↓
Git Commit
      ↓
Git Push
      ↓
📚 Daily Research Archive
```

---

# 🧠 Core Idea

PaperPilot treats research-paper discovery as an automated data pipeline.

Instead of manually visiting multiple websites every morning, the system becomes a small autonomous research assistant.

The system should answer:

> **"What interesting research papers appeared today that I might actually care about?"**

Each day's results are stored as a separate Markdown file.

Example:

```text
papers/
├── 2026-08-17.md
├── 2026-08-18.md
├── 2026-08-19.md
└── ...
```

This creates a permanent, searchable personal research archive.

---

# ✨ Main Features

## 1. Automated Daily Execution

GitHub Actions runs the pipeline automatically once every morning.

No local machine needs to be running.

```text
08:00 AM
   ↓
GitHub Action starts
   ↓
PaperPilot runs
   ↓
Daily report generated
   ↓
Git commit
   ↓
GitHub repository updated
```

---

## 2. Multiple Research Sources

PaperPilot should support multiple academic sources through a common interface.

Initial sources:

* arXiv
* Semantic Scholar
* Crossref
* OpenAlex
* Unpaywall

Future sources can be added without changing the core pipeline.

Example architecture:

```text
                 ┌──────────────┐
                 │    arXiv     │
                 └──────┬───────┘
                        │
                 ┌──────▼───────┐
                 │  Semantic    │
                 │   Scholar    │
                 └──────┬───────┘
                        │
                 ┌──────▼───────┐
                 │   OpenAlex   │
                 └──────┬───────┘
                        │
                        ▼
               ┌─────────────────┐
               │ Source Adapter  │
               └────────┬────────┘
                        ▼
               ┌─────────────────┐
               │ Common Paper    │
               │     Model       │
               └─────────────────┘
```

The core system should never depend directly on one provider's response format.

---

# 🏗️ Architecture

```text
┌───────────────────────────────────────────┐
│              GitHub Actions               │
│                                           │
│        Scheduled Daily Execution          │
└─────────────────────┬─────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────┐
│              Source Layer                 │
│                                           │
│  arXiv │ Semantic Scholar │ OpenAlex      │
│  Crossref │ Unpaywall                     │
└─────────────────────┬─────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────┐
│              Fetch Layer                  │
│                                           │
│     API requests / pagination / retry     │
└─────────────────────┬─────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────┐
│           Normalization Layer             │
│                                           │
│ Convert different API responses into      │
│ one common Paper representation            │
└─────────────────────┬─────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────┐
│             Processing Layer              │
│                                           │
│ Filtering │ Deduplication │ Ranking       │
└─────────────────────┬─────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────┐
│            Presentation Layer             │
│                                           │
│       Generate Markdown Report            │
└─────────────────────┬─────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────┐
│               Git Layer                   │
│                                           │
│       git add → commit → push             │
└─────────────────────┬─────────────────────┘
                      │
                      ▼
              📚 GitHub Repository
```

---

# 📄 Paper Data Model

All sources should eventually produce a common paper representation.

Example:

```text
Paper
├── id
├── title
├── authors
├── abstract
├── published_date
├── updated_date
├── source
├── categories
├── doi
├── paper_url
├── pdf_url
├── citation_count
├── relevance_score
├── open_access
└── fetched_at
```

The exact implementation can evolve.

The important design principle is:

> **External API formats should not leak into the rest of the application.**

---

# 🔌 Source Adapter Design

Each academic source should have its own adapter.

Conceptually:

```text
Source
│
├── ArxivSource
├── SemanticScholarSource
├── OpenAlexSource
├── CrossrefSource
└── UnpaywallSource
```

Each adapter is responsible for:

1. Calling its API
2. Handling API-specific response formats
3. Handling pagination
4. Handling rate limits
5. Handling temporary failures
6. Converting results into the common Paper model

The rest of the system should not care where the paper came from.

---

# 🔄 Daily Pipeline

Every scheduled execution follows the same pipeline.

```text
START
  │
  ▼
Load configuration
  │
  ▼
Fetch papers from sources
  │
  ▼
Validate responses
  │
  ▼
Normalize papers
  │
  ▼
Remove duplicates
  │
  ▼
Filter unwanted papers
  │
  ▼
Calculate ranking/relevance
  │
  ▼
Select top papers
  │
  ▼
Generate Markdown
  │
  ▼
Save daily report
  │
  ▼
Commit changes
  │
  ▼
Push to GitHub
  │
  ▼
DONE
```

---

# 🧹 Deduplication

The same paper may appear on multiple sources.

For example:

```text
arXiv
   ↓
Paper A

Semantic Scholar
   ↓
Paper A

OpenAlex
   ↓
Paper A
```

PaperPilot should detect that these represent the same paper.

Preferred identifiers:

1. DOI
2. arXiv ID
3. Canonical paper URL
4. Normalized title as fallback

The final report should contain the paper only once.

---

# ⭐ Ranking

The initial ranking system should remain simple and deterministic.

Possible signals:

```text
Relevance
+ Recency
+ Citation information
+ Source quality
+ Topic match
+ Open-access availability
```

Example conceptual score:

```text
score =
    topic_relevance
    + recency_score
    + citation_score
    + source_score
```

The ranking system should be modular so that more sophisticated ranking can be introduced later.

---

# 📝 Daily Markdown Output

Each day generates a Markdown file.

Example:

```text
papers/
└── 2026-08-17.md
```

Preview:

# 📚 Research Papers — August 17, 2026

> Automatically generated by PaperPilot.

## 🔥 Top Papers

### 1. Example Research Paper

**Authors:** Author One, Author Two

**Published:** August 17, 2026

**Source:** arXiv

**Topics:** Machine Learning, LLMs, Representation Learning

**Relevance Score:** 94/100

**Why it was selected:**

A short explanation of why this paper is relevant to the configured research interests.

🔗 [Paper](https://example.com)

📄 [PDF](https://example.com/pdf)

---

### 2. Another Research Paper

**Authors:** Author Three

**Published:** August 17, 2026

**Source:** Semantic Scholar

**Topics:** Computer Vision, Multimodal Learning

**Relevance Score:** 89/100

🔗 [Paper](https://example.com)

📄 [PDF](https://example.com/pdf)

---

## 📊 Daily Summary

| Metric              | Value |
| ------------------- | ----: |
| Papers fetched      |   143 |
| After filtering     |    48 |
| After deduplication |    37 |
| Final papers        |    10 |
| Sources             |     3 |

---

# ⚙️ Configuration

Research interests should not be hardcoded into the application.

Example configuration:

```yaml
topics:
  - machine learning
  - deep learning
  - llm
  - generative ai
  - computer vision
  - data science
  - reinforcement learning

daily_limit: 10

sources:
  - arxiv
  - semantic_scholar
  - openalex

open_access_only: false
```

This allows the same system to be customized without modifying application code.

---

# 🤖 GitHub Actions

GitHub Actions is responsible for scheduling and executing the pipeline.

Conceptually:

```text
.github/
└── workflows/
    └── daily-papers.yml
```

The workflow should:

1. Start on schedule
2. Checkout repository
3. Install dependencies
4. Run PaperPilot
5. Generate daily Markdown
6. Check whether files changed
7. Commit changes
8. Push changes

The workflow should also support manual execution for development and testing.

```text
Schedule
   +
Manual Trigger
      ↓
PaperPilot
      ↓
GitHub Repository
```

---

# 🔐 Secrets

API keys should never be committed into the repository.

Secrets should be provided through GitHub Actions secrets/environment variables.

Example:

```text
SEMANTIC_SCHOLAR_API_KEY
OTHER_API_KEY
```

Public APIs that do not require authentication should not unnecessarily use secrets.

---

# 🛡️ Reliability

The system should be designed to survive normal API problems.

Handle:

* API timeout
* HTTP errors
* Rate limits
* Empty responses
* Invalid responses
* Missing metadata
* Duplicate papers
* Partial source failure
* Git commit when there are no changes

One failed source should ideally not destroy the entire daily pipeline.

Example:

```text
arXiv             ✅
Semantic Scholar  ✅
OpenAlex          ❌
Crossref          ✅

             ↓

Generate report anyway
```

The daily report should record source failures when appropriate.

---

# 📁 Project Structure

Proposed structure:

```text
PaperPilot/
│
├── .github/
│   └── workflows/
│       └── daily-papers.yml
│
├── src/
│   ├── sources/
│   │   ├── base.py
│   │   ├── arxiv.py
│   │   ├── semantic_scholar.py
│   │   ├── openalex.py
│   │   └── crossref.py
│   │
│   ├── models/
│   │   └── paper.py
│   │
│   ├── pipeline/
│   │   ├── fetch.py
│   │   ├── normalize.py
│   │   ├── deduplicate.py
│   │   ├── rank.py
│   │   └── process.py
│   │
│   ├── output/
│   │   └── markdown.py
│   │
│   ├── config.py
│   └── main.py
│
├── papers/
│   ├── 2026-08-17.md
│   └── ...
│
├── tests/
│
├── config.yaml
├── requirements.txt
└── README.md
```

This structure is intentionally modular.

---

# 🚀 MVP

The first version should NOT attempt to solve everything.

## Phase 1

* [ ] arXiv integration
* [ ] Semantic Scholar integration
* [ ] Common Paper model
* [ ] Basic deduplication
* [ ] Basic topic filtering
* [ ] Markdown generation
* [ ] Daily GitHub Action
* [ ] Automatic commit and push

## Phase 2

* [ ] OpenAlex integration
* [ ] Crossref integration
* [ ] Better ranking
* [ ] Open-access detection
* [ ] Better error handling
* [ ] Tests
* [ ] Configuration system

## Phase 3

* [ ] Personal semantic relevance
* [ ] Embedding-based ranking
* [ ] LLM-generated summaries
* [ ] "Why should I read this?" section
* [ ] GitHub repository detection
* [ ] Research trend analysis

---

# 🧠 Future Vision

PaperPilot could eventually become a personal research intelligence system.

Instead of simply:

```text
"Here are today's papers."
```

it could eventually provide:

```text
Today's Research
       ↓
Relevant Papers
       ↓
Personal Interest Ranking
       ↓
Important Papers
       ↓
Paper Summaries
       ↓
Related GitHub Repositories
       ↓
Research Trends
       ↓
Previously Read Papers
       ↓
Recommended Next Papers
```

The system could learn from which papers are opened, saved, ignored, or marked as interesting.

However, these features are intentionally outside the initial scope.

---

# 🎯 Non-Goals

PaperPilot is NOT intended to be:

* A state-of-the-art research framework
* A replacement for researchers
* A complete academic search engine
* A social network for researchers
* A massive distributed system
* A commercial SaaS product

The primary objective is simple:

> **Build a reliable personal tool that automatically finds useful research papers every day.**

---

# 💡 Why This Project Exists

The project exists primarily for personal utility.

The best software project is sometimes not the one that sounds impressive.

It is the one that removes an annoying task you repeatedly have to perform.

PaperPilot automates one of those tasks:

> **Finding what is worth reading.**

---

# 🏁 Definition of Done

PaperPilot can be considered an MVP when:

```text
Every morning
      ↓
GitHub Action automatically runs
      ↓
Research APIs are queried
      ↓
New papers are collected
      ↓
Duplicates are removed
      ↓
Relevant papers are selected
      ↓
Markdown report is generated
      ↓
Report is committed to GitHub
      ↓
Repository contains today's papers
```

No manual intervention should be required.

---

# 📌 Example Repository Experience

A user opens the repository in the morning:

```text
PaperPilot
│
├── 📁 papers
│   ├── 📄 2026-08-17.md
│   ├── 📄 2026-08-18.md
│   └── 📄 2026-08-19.md
│
├── 📁 src
├── 📁 tests
├── ⚙️ config.yaml
└── 📖 README.md
```

They open today's file:

```text
📚 Research Papers
August 19, 2026

🔥 Top 10 Papers

1. Paper A
2. Paper B
3. Paper C
4. Paper D
5. Paper E
...

📊 187 papers scanned
🎯 10 selected
🔗 All links available
```

That is the entire point of PaperPilot.

**Wake up → open GitHub → see what is worth reading.**


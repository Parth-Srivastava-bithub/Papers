# PaperPilot 📚🚀

> Your autonomous daily research-paper radar.

PaperPilot is a personal research-paper discovery pipeline that automatically searches academic sources every day, identifies relevant papers matching your topics, and publishes structured Markdown reports directly to your repository via GitHub Actions.

---

## ✨ Features

- 🤖 **100% Automated:** Runs every morning via GitHub Actions (no server or local PC needed).
- 🔌 **Multiple Sources:** Fetches from **arXiv** and **Semantic Scholar** (with built-in support to add OpenAlex/Crossref).
- 🧹 **Smart Deduplication:** Merges papers sharing the same DOI, arXiv ID, or title.
- 🎯 **Topic-Based Ranking:** Scores papers by topic match, recency, and citation count.
- 📝 **Clean Markdown Archive:** Saves formatted reports in `papers/YYYY-MM-DD.md`.
- 🛡️ **Zero Required API Keys:** Works out of the box with public APIs.

---

## 📁 Project Structure

```text
ResearchIt/
│
├── .github/workflows/
│   └── daily.yml        # Scheduled GitHub Action (8:00 AM daily)
│
├── papers/              # 📚 The Daily Archive (Auto-committed markdown)
│   └── 2026-08-17.md
│
├── src/
│   ├── sources/         # Academic API fetchers
│   │   ├── arxiv.py     # arXiv Atom API
│   │   └── semantic.py  # Semantic Scholar Graph API
│   │
│   ├── models.py        # Pydantic Paper & Stats models
│   ├── pipeline.py      # Fetch, deduplicate, filter & rank
│   ├── markdown.py      # Daily markdown report generator
│   └── main.py          # CLI runner & orchestrator
│
├── config.yaml          # Topics, source settings, daily limits
├── requirements.txt     # Minimal dependencies
└── README.md
```

---

## 🛠️ Local Quickstart

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure your topics
Edit `config.yaml` to specify what topics you care about:
```yaml
topics:
  - "large language models"
  - "reasoning"
  - "agentic"
  - "machine learning"

daily_limit: 10
```

### 3. Run PaperPilot
```bash
# Generate today's report
python -m src.main

# Preview without saving (dry run)
python -m src.main --dry-run

# Run for a specific past date
python -m src.main --date 2026-08-17
```

---

## 🤖 GitHub Actions Setup

1. Push this repository to GitHub.
2. Go to **Settings > Actions > General > Workflow permissions**, select **"Read and write permissions"** and click **Save**.
3. (Optional) If you have a Semantic Scholar API key, add it to **Settings > Secrets and variables > Actions** as `SEMANTIC_SCHOLAR_API_KEY`.
4. Done! GitHub Actions will run every morning at 08:00 AM IST and push reports to `papers/`.

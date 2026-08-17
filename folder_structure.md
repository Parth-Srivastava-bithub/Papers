# 🚀 PaperPilot — Minimal Project Structure

```text
ResearchIt/
│
├── .github/
│   └── workflows/
│       └── daily.yml        # GitHub Action (runs daily at 8 AM + manual trigger)
│
├── papers/                  # 📚 Daily generated markdown reports
│   └── 2026-08-17.md
│
├── src/
│   ├── sources/             # Academic API fetchers
│   │   ├── arxiv.py         # arXiv API
│   │   └── semantic.py      # Semantic Scholar API
│   │
│   ├── models.py            # Single clean Paper data model
│   ├── pipeline.py          # Fetch, deduplicate, filter & rank in one place
│   ├── markdown.py          # Generates the daily .md report
│   └── main.py              # CLI / Entrypoint orchestrator
│
├── config.yaml              # Topics, source toggles, daily limit
├── requirements.txt         # requests, pyyaml, pydantic
└── README.md
```

---

### 📄 What each file does (Zero Fluff)

| File | Purpose |
| :--- | :--- |
| **`src/models.py`** | 1 dataclass/model: `Paper` (`title`, `authors`, `url`, `abstract`, `source`, `doi`, `published_date`, `score`). |
| **`src/sources/*.py`** | Functions that hit APIs and return `list[Paper]`. |
| **`src/pipeline.py`** | Takes all papers -> removes duplicate DOIs/titles -> filters by keywords -> sorts by score. |
| **`src/markdown.py`** | Takes top papers and outputs `papers/YYYY-MM-DD.md`. |
| **`src/main.py`** | Calls `sources -> pipeline -> markdown`. |
| **`config.yaml`** | Change keywords & paper limit without touching Python code. |
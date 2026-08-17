import sys
from pathlib import Path

# Add project root to sys.path so tests can be run from any directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from src.models import Paper, PipelineStats
from src.pipeline import (
    normalize_title,
    match_topic,
    deduplicate_papers,
    filter_papers,
    calculate_score,
    rank_papers,
)
from src.markdown import generate_daily_markdown


def test_paper_model():
    paper = Paper(
        id="arxiv_1234.5678",
        title="Attention Is All You Need",
        authors=["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"],
        source="arXiv",
        paper_url="https://arxiv.org/abs/1234.5678",
    )
    assert paper.formatted_authors == "Ashish Vaswani, Noam Shazeer, Niki Parmar et al."
    assert paper.citation_count == 0


def test_normalize_title():
    t1 = "Attention Is All You Need!"
    t2 = "attention is all you need"
    t3 = "Attention is: all you need --"
    assert normalize_title(t1) == normalize_title(t2) == normalize_title(t3)


def test_match_topic_word_boundary():
    # Should match standalone acronyms
    assert match_topic("rag", "We present a novel RAG framework for LLMs.")
    assert match_topic("llm", "Evaluating LLM performance on benchmarks.")
    
    # Should NOT match substring inside other words
    assert not match_topic("rag", "This algorithm provides wide coverage and fragmented trees.")
    assert not match_topic("rag", "A pragmatic approach to compiler design.")


def test_deduplication():
    p1 = Paper(
        id="arxiv_2401.0001",
        title="Reasoning with Large Language Models",
        authors=["Alice", "Bob"],
        source="arXiv",
        paper_url="https://arxiv.org/abs/2401.0001",
        arxiv_id="2401.0001",
        doi="10.1234/test.1",
        citation_count=5,
    )
    p2 = Paper(
        id="s2_abc123",
        title="Reasoning with Large Language Models!",
        authors=["Alice", "Bob", "Charlie"],
        source="Semantic Scholar",
        paper_url="https://semanticscholar.org/paper/abc123",
        doi="10.1234/test.1",  # Same DOI
        pdf_url="https://example.com/paper.pdf",
        citation_count=12,
    )
    p3 = Paper(
        id="arxiv_2401.0002",
        title="A Totally Different Paper",
        authors=["David"],
        source="arXiv",
        paper_url="https://arxiv.org/abs/2401.0002",
    )

    deduped = deduplicate_papers([p1, p2, p3])
    assert len(deduped) == 2

    # Verify richer metadata was merged
    merged = [p for p in deduped if "Reasoning" in p.title][0]
    assert merged.citation_count == 12
    assert merged.pdf_url == "https://example.com/paper.pdf"


def test_filter_and_rank():
    topics = ["reasoning", "agentic"]

    p1 = Paper(
        id="1",
        title="Agentic Workflow for LLM Reasoning",
        abstract="We show how agentic patterns improve complex reasoning.",
        published_date="2026-08-15",
        source="arXiv",
        paper_url="https://arxiv.org/abs/1",
        citation_count=10,
    )
    p2 = Paper(
        id="2",
        title="Quantum Mechanics in Superconductors",
        abstract="Study of electron pairing at low temperatures.",
        published_date="2026-08-15",
        source="arXiv",
        paper_url="https://arxiv.org/abs/2",
    )
    p3 = Paper(
        id="3",
        title="A Simple Study on Agentic Loops",
        abstract="Testing basic agentic behaviors.",
        published_date="2026-01-01",  # older
        source="arXiv",
        paper_url="https://arxiv.org/abs/3",
        citation_count=0,
    )

    filtered = filter_papers([p1, p2, p3], topics)
    assert len(filtered) == 2
    assert all(p.id in ["1", "3"] for p in filtered)

    ranked = rank_papers(filtered, topics, limit=1)
    assert len(ranked) == 1
    assert ranked[0].id == "1"  # p1 scores higher due to multiple topics + recency + citations


def test_markdown_generation():
    paper = Paper(
        id="1",
        title="Sample Paper on Machine Learning",
        authors=["John Doe"],
        published_date="2026-08-17",
        source="arXiv",
        paper_url="https://arxiv.org/abs/1",
        pdf_url="https://arxiv.org/pdf/1.pdf",
        matched_topics=["machine learning"],
        score=95.0,
        abstract="This is a test abstract."
    )
    stats = PipelineStats(
        total_fetched=10,
        after_dedup=8,
        after_filter=5,
        final_selected=1,
        sources_used=["arXiv"]
    )

    md = generate_daily_markdown([paper], stats, run_date="2026-08-17")
    assert "# 📚 Research Papers — August 17, 2026" in md
    assert "Sample Paper on Machine Learning" in md
    assert "[🔗 Paper Link](https://arxiv.org/abs/1)" in md
    assert "[📄 Direct PDF](https://arxiv.org/pdf/1.pdf)" in md
    assert "## 📊 Daily Summary" in md
    assert "| 📥 Papers fetched | 10 |" in md

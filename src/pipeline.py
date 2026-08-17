import re
import math
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Tuple
from dateutil import parser as date_parser

from src.models import Paper, PipelineStats
from src.sources.arxiv import fetch_arxiv_papers
from src.sources.semantic import fetch_semantic_scholar_papers

logger = logging.getLogger(__name__)


def normalize_title(title: str) -> str:
    """Normalize title for fuzzy exact-character deduplication."""
    return re.sub(r"[^a-z0-9]", "", title.lower())


def fetch_all_papers(config: Dict[str, Any], stats: PipelineStats) -> List[Paper]:
    """Fetch papers concurrently or sequentially from all active sources."""
    all_papers: List[Paper] = []

    # 1. arXiv
    try:
        arxiv_papers = fetch_arxiv_papers(config)
        all_papers.extend(arxiv_papers)
        if arxiv_papers:
            stats.sources_used.append("arXiv")
    except Exception as e:
        logger.error(f"arXiv source crashed: {e}")
        stats.sources_failed.append("arXiv")

    # 2. Semantic Scholar
    try:
        s2_papers = fetch_semantic_scholar_papers(config)
        all_papers.extend(s2_papers)
        if s2_papers:
            stats.sources_used.append("Semantic Scholar")
    except Exception as e:
        logger.error(f"Semantic Scholar source crashed: {e}")
        stats.sources_failed.append("Semantic Scholar")

    stats.total_fetched = len(all_papers)
    return all_papers


def deduplicate_papers(papers: List[Paper]) -> List[Paper]:
    """Deduplicate papers by DOI, arXiv ID, or normalized title."""
    unique_papers: Dict[str, Paper] = {}
    doi_map: Dict[str, str] = {}
    arxiv_map: Dict[str, str] = {}
    title_map: Dict[str, str] = {}

    for paper in papers:
        # Check if already indexed
        existing_key = None
        if paper.doi and paper.doi.lower() in doi_map:
            existing_key = doi_map[paper.doi.lower()]
        elif paper.arxiv_id and paper.arxiv_id in arxiv_map:
            existing_key = arxiv_map[paper.arxiv_id]
        else:
            norm_title = normalize_title(paper.title)
            if norm_title in title_map:
                existing_key = title_map[norm_title]

        if existing_key and existing_key in unique_papers:
            # Merge richer metadata into existing record
            existing = unique_papers[existing_key]
            if not existing.pdf_url and paper.pdf_url:
                existing.pdf_url = paper.pdf_url
            if not existing.doi and paper.doi:
                existing.doi = paper.doi
            if not existing.arxiv_id and paper.arxiv_id:
                existing.arxiv_id = paper.arxiv_id
            if paper.citation_count > existing.citation_count:
                existing.citation_count = paper.citation_count
            # Merge categories
            for cat in paper.categories:
                if cat not in existing.categories:
                    existing.categories.append(cat)
        else:
            # Register new paper
            key = paper.id
            unique_papers[key] = paper
            if paper.doi:
                doi_map[paper.doi.lower()] = key
            if paper.arxiv_id:
                arxiv_map[paper.arxiv_id] = key
            norm_title = normalize_title(paper.title)
            if norm_title:
                title_map[norm_title] = key

    logger.info(f"Deduplication: {len(papers)} -> {len(unique_papers)} papers.")
    return list(unique_papers.values())


def match_topic(topic: str, text: str) -> bool:
    """Check if topic matches text with word boundary matching for short acronyms."""
    topic_clean = topic.strip().lower()
    if not topic_clean or not text:
        return False
    # If topic is short acronym (<= 4 chars like 'rag', 'llm'), enforce word boundaries
    if len(topic_clean) <= 4:
        pattern = r"\b" + re.escape(topic_clean) + r"\b"
        return bool(re.search(pattern, text.lower()))
    return topic_clean in text.lower()


def filter_papers(papers: List[Paper], topics: List[str]) -> List[Paper]:
    """Filter papers by checking if any topic matches title, abstract or categories."""
    if not topics:
        return papers

    matched_papers: List[Paper] = []

    for paper in papers:
        title = paper.title
        abstract = paper.abstract
        cats = " ".join(paper.categories)
        full_text = f"{title} {abstract} {cats}"

        matched = []
        for topic in topics:
            if match_topic(topic, full_text):
                matched.append(topic)

        if matched:
            paper.matched_topics = matched
            matched_papers.append(paper)

    logger.info(f"Filtering: {len(papers)} -> {len(matched_papers)} relevant papers.")
    return matched_papers


def calculate_score(paper: Paper, topics: List[str]) -> float:
    """Calculate relevance score based on topic match, recency, and citations."""
    score = 40.0  # Base score for passing filter

    # 1. Topic Relevance (Up to 35 points)
    for topic in paper.matched_topics:
        score += 8.0
        if match_topic(topic, paper.title):
            score += 12.0  # Extra weight for topic appearing in title

    # 2. Recency (Up to 20 points)
    if paper.published_date:
        try:
            pub_date = date_parser.parse(paper.published_date).date()
            today = date.today()
            age_days = (today - pub_date).days
            if age_days <= 1:
                score += 20.0
            elif age_days <= 7:
                score += 15.0
            elif age_days <= 30:
                score += 10.0
            elif age_days <= 90:
                score += 5.0
        except Exception:
            pass

    # 3. Citation Bonus (Up to 15 points)
    if paper.citation_count > 0:
        score += min(math.log(paper.citation_count + 1, 2) * 2.5, 15.0)

    return round(min(score, 100.0), 1)


def rank_papers(papers: List[Paper], topics: List[str], limit: int = 10) -> List[Paper]:
    """Score and sort papers, returning top `limit` results."""
    for paper in papers:
        paper.score = calculate_score(paper, topics)

    # Sort descending by score, then citation count
    sorted_papers = sorted(papers, key=lambda p: (p.score, p.citation_count), reverse=True)
    return sorted_papers[:limit]

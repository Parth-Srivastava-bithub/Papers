import os
import logging
import re
from typing import List, Dict, Any
import requests

from src.models import Paper

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Normalize whitespace and strip linebreaks."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def fetch_semantic_scholar_papers(config: Dict[str, Any]) -> List[Paper]:
    """Fetch recent papers from the Semantic Scholar Academic Graph API."""
    source_cfg = config.get("sources", {}).get("semantic_scholar", {})
    if not source_cfg.get("enabled", True):
        return []

    query = source_cfg.get("query", "machine learning OR deep learning OR large language models")
    max_results = min(source_cfg.get("max_results", 30), 50)  # S2 max page is 100

    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    fields = "paperId,title,abstract,authors,year,publicationDate,citationCount,openAccessPdf,url,externalIds,fieldsOfStudy"
    params = {
        "query": query,
        "limit": max_results,
        "fields": fields,
    }

    headers = {"User-Agent": "PaperPilot/1.0 (https://github.com/)"}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key

    logger.info(f"Fetching papers from Semantic Scholar (query: {query[:40]}...)...")

    try:
        response = requests.get(url, params=params, headers=headers, timeout=20)
        if response.status_code == 429:
            logger.warning("Semantic Scholar rate limit hit (429). Skipping for this run.")
            return []
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"Failed to fetch papers from Semantic Scholar: {e}")
        return []

    items = data.get("data", [])
    papers: List[Paper] = []

    for item in items:
        paper_id = item.get("paperId")
        title = clean_text(item.get("title", ""))
        if not paper_id or not title:
            continue

        abstract = clean_text(item.get("abstract", "") or "")
        published_date = item.get("publicationDate") or (str(item.get("year")) if item.get("year") else "")
        citation_count = item.get("citationCount") or 0
        
        # Authors
        authors = [a.get("name") for a in item.get("authors", []) if a.get("name")]
        
        # External IDs
        ext_ids = item.get("externalIds") or {}
        doi = ext_ids.get("DOI")
        arxiv_id = ext_ids.get("ArXiv")

        # URLs
        paper_url = item.get("url") or f"https://www.semanticscholar.org/paper/{paper_id}"
        pdf_info = item.get("openAccessPdf") or {}
        pdf_url = pdf_info.get("url")
        if not pdf_url and arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        # Categories / Fields of Study
        categories = item.get("fieldsOfStudy") or []

        papers.append(
            Paper(
                id=f"s2_{paper_id}",
                title=title,
                authors=authors,
                abstract=abstract,
                published_date=published_date,
                source="Semantic Scholar",
                paper_url=paper_url,
                pdf_url=pdf_url,
                doi=doi,
                arxiv_id=arxiv_id,
                citation_count=citation_count,
                categories=categories,
            )
        )

    logger.info(f"Successfully fetched {len(papers)} papers from Semantic Scholar.")
    return papers

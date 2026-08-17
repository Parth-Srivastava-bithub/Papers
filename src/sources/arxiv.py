import logging
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import requests

from src.models import Paper

logger = logging.getLogger(__name__)

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def clean_text(text: str) -> str:
    """Normalize whitespace and strip linebreaks."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def extract_arxiv_id(raw_id: str) -> str:
    """Extract standard arXiv ID from the raw entry ID url."""
    match = re.search(r"arxiv\.org/abs/([^/]+)", raw_id)
    if match:
        return match.group(1).split("v")[0]  # Strip version suffix
    return raw_id.split("/")[-1]


def fetch_arxiv_papers(config: Dict[str, Any]) -> List[Paper]:
    """Fetch recent papers from the arXiv API based on categories."""
    source_cfg = config.get("sources", {}).get("arxiv", {})
    if not source_cfg.get("enabled", True):
        return []

    categories = source_cfg.get("categories", ["cs.AI", "cs.CL", "cs.CV", "cs.LG"])
    max_results = source_cfg.get("max_results", 35)

    # Build search query: cat:cs.AI OR cat:cs.LG ...
    cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": cat_query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "start": 0,
        "max_results": max_results,
    }
    headers = {"User-Agent": "PaperPilot/1.0 (https://github.com/)"}

    logger.info(f"Fetching papers from arXiv (query: {cat_query}, max: {max_results})...")

    try:
        response = requests.get(url, params=params, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to fetch papers from arXiv: {e}")
        return []

    root = ET.fromstring(response.content)
    papers: List[Paper] = []

    for entry in root.findall("atom:entry", ATOM_NS):
        raw_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
        arxiv_id = extract_arxiv_id(raw_id)
        title = clean_text(entry.findtext("atom:title", default="", namespaces=ATOM_NS))
        abstract = clean_text(entry.findtext("atom:summary", default="", namespaces=ATOM_NS))
        published_raw = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
        published_date = published_raw[:10] if published_raw else ""

        # Extract authors
        authors = []
        for author in entry.findall("atom:author", ATOM_NS):
            name = author.findtext("atom:name", default="", namespaces=ATOM_NS)
            if name:
                authors.append(clean_text(name))

        # Extract URLs
        paper_url = f"https://arxiv.org/abs/{arxiv_id}"
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        for link in entry.findall("atom:link", ATOM_NS):
            if link.get("title") == "pdf" or link.get("type") == "application/pdf":
                pdf_url = link.get("href", pdf_url)

        # Extract categories
        entry_cats = []
        for cat in entry.findall("atom:category", ATOM_NS):
            term = cat.get("term")
            if term:
                entry_cats.append(term)

        # Extract DOI if present
        doi_elem = entry.find("arxiv:doi", ATOM_NS)
        doi = clean_text(doi_elem.text) if doi_elem is not None and doi_elem.text else None

        if title and arxiv_id:
            papers.append(
                Paper(
                    id=f"arxiv_{arxiv_id}",
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    published_date=published_date,
                    source="arXiv",
                    paper_url=paper_url,
                    pdf_url=pdf_url,
                    doi=doi,
                    arxiv_id=arxiv_id,
                    categories=entry_cats,
                )
            )

    logger.info(f"Successfully fetched {len(papers)} papers from arXiv.")
    return papers

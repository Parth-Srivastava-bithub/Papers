import os
from datetime import datetime
from typing import List
from pathlib import Path

from src.models import Paper, PipelineStats


def format_topics(topics: List[str]) -> str:
    """Format topics as clean capitalized badges/list."""
    if not topics:
        return "General AI / ML"
    return ", ".join([t.title() for t in topics[:4]])


def generate_daily_markdown(papers: List[Paper], stats: PipelineStats, run_date: str = "") -> str:
    """Generate structured markdown report for the given papers and stats."""
    if not run_date:
        run_date = datetime.now().strftime("%Y-%m-%d")

    # Format human-readable date e.g. "August 17, 2026"
    try:
        date_obj = datetime.strptime(run_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")
    except Exception:
        formatted_date = run_date

    md_lines = [
        f"# 📚 Research Papers — {formatted_date}",
        "",
        "> Autonomous daily research radar curated by **PaperPilot**.",
        "",
        "## 🔥 Top Selected Papers",
        "",
    ]

    if not papers:
        md_lines.extend([
            "_No papers matched the configured topics and criteria for today._",
            "",
        ])
    else:
        for idx, paper in enumerate(papers, 1):
            md_lines.append(f"### {idx}. {paper.title}")
            md_lines.append("")
            md_lines.append(f"**👤 Authors:** {paper.formatted_authors}")
            if paper.published_date:
                md_lines.append(f"**📅 Published:** {paper.published_date}")
            md_lines.append(f"**🏛️ Source:** `{paper.source}`")
            if paper.matched_topics:
                md_lines.append(f"**🏷️ Topics:** {format_topics(paper.matched_topics)}")
            if paper.citation_count > 0:
                md_lines.append(f"**⭐ Citations:** {paper.citation_count}")
            md_lines.append(f"**🎯 Relevance Score:** `{paper.score}/100`")
            md_lines.append("")

            # Abstract snippet (trim to 350 chars if too long)
            if paper.abstract:
                abstract_clean = paper.abstract
                if len(abstract_clean) > 400:
                    abstract_clean = abstract_clean[:397].rsplit(" ", 1)[0] + "..."
                md_lines.append(f"> **Abstract:** {abstract_clean}")
                md_lines.append("")

            # Links
            links = [f"[🔗 Paper Link]({paper.paper_url})"]
            if paper.pdf_url:
                links.append(f"[📄 Direct PDF]({paper.pdf_url})")
            if paper.doi:
                links.append(f"[DOI: {paper.doi}](https://doi.org/{paper.doi})")

            md_lines.append(" • ".join(links))
            md_lines.append("")
            md_lines.append("---")
            md_lines.append("")

    # Summary table
    sources_used_str = ", ".join(stats.sources_used) if stats.sources_used else "None"
    md_lines.extend([
        "## 📊 Daily Summary",
        "",
        "| Metric | Value |",
        "| :--- | ---: |",
        f"| 📥 Papers fetched | {stats.total_fetched} |",
        f"| 🧹 After deduplication | {stats.after_dedup} |",
        f"| 🎯 After topic filtering | {stats.after_filter} |",
        f"| 🏆 Final papers selected | {stats.final_selected} |",
        f"| 🔌 Active sources | {sources_used_str} |",
        "",
        "---",
        "_Generated automatically with [PaperPilot](https://github.com/)_",
    ])

    return "\n".join(md_lines)


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def save_markdown_report(content: str, output_dir: str = "papers", run_date: str = "") -> str:
    """Save markdown content to papers/YYYY-MM-DD.md."""
    if not run_date:
        run_date = datetime.now().strftime("%Y-%m-%d")

    target_dir = Path(output_dir)
    if not target_dir.is_absolute():
        target_dir = PROJECT_ROOT / output_dir

    target_dir.mkdir(parents=True, exist_ok=True)

    file_path = target_dir / f"{run_date}.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(file_path)

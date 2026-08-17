import os
import sys
from pathlib import Path

# Add project root to sys.path so execution works from any working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set stdout/stderr to UTF-8 for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import argparse
import logging
import yaml
from datetime import datetime
from dotenv import load_dotenv

from src.models import PipelineStats
from src.pipeline import fetch_all_papers, deduplicate_papers, filter_papers, rank_papers
from src.markdown import generate_daily_markdown, save_markdown_report

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("paperpilot")


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    path = Path(config_path)
    if not path.is_absolute() and not path.exists():
        path = PROJECT_ROOT / config_path

    if not path.exists():
        logger.warning(f"Config file not found at {path}. Using default settings.")
        return {
            "topics": ["machine learning", "large language models", "artificial intelligence"],
            "daily_limit": 10,
            "sources": {
                "arxiv": {"enabled": True, "categories": ["cs.AI", "cs.LG", "cs.CL"]},
                "semantic_scholar": {"enabled": True},
            },
            "output_dir": "papers",
        }

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run_paperpilot(date_str: str = "", dry_run: bool = False, config_path: str = "config.yaml"):
    """Main orchestration pipeline for PaperPilot."""
    # Load .env if present
    load_dotenv()

    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    print("\n" + "=" * 55)
    print(f"🚀 PaperPilot — Daily Research Radar ({date_str})")
    print("=" * 55 + "\n")

    config = load_config(config_path)
    topics = config.get("topics", [])
    limit = config.get("daily_limit", 10)
    output_dir = config.get("output_dir", "papers")

    stats = PipelineStats()

    # Step 1: Fetch
    logger.info("Step 1/4: Fetching papers from academic sources...")
    raw_papers = fetch_all_papers(config, stats)
    if not raw_papers:
        logger.warning("No papers retrieved from any source.")

    # Step 2: Deduplicate
    logger.info("Step 2/4: Deduplicating papers...")
    unique_papers = deduplicate_papers(raw_papers)
    stats.after_dedup = len(unique_papers)

    # Step 3: Filter
    logger.info("Step 3/4: Filtering papers by interest topics...")
    filtered_papers = filter_papers(unique_papers, topics)
    stats.after_filter = len(filtered_papers)

    # Step 4: Rank
    logger.info(f"Step 4/4: Ranking and picking top {limit} papers...")
    top_papers = rank_papers(filtered_papers, topics, limit=limit)
    stats.final_selected = len(top_papers)

    # Generate Markdown
    md_content = generate_daily_markdown(top_papers, stats, run_date=date_str)

    if dry_run:
        print("\n" + "-" * 20 + " [DRY RUN PREVIEW] " + "-" * 20)
        print(md_content[:1500])
        print("...\n" + "-" * 55)
        print(f"⚡ Dry run complete! {len(top_papers)} papers selected. No file written.")
    else:
        out_file = save_markdown_report(md_content, output_dir=output_dir, run_date=date_str)
        print("\n" + "=" * 55)
        print(f"✅ Success! Daily report saved to: {out_file}")
        print(f"📊 Summary: {stats.total_fetched} fetched -> {stats.after_dedup} deduped -> {stats.after_filter} filtered -> {stats.final_selected} published")
        print("=" * 55 + "\n")


def main():
    parser = argparse.ArgumentParser(description="PaperPilot: Autonomous Daily Research-Paper Radar")
    parser.add_argument("--date", type=str, default="", help="Date for the report (YYYY-MM-DD), defaults to today")
    parser.add_argument("--dry-run", action="store_true", help="Run pipeline and preview output without saving files")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config YAML file")

    args = parser.parse_args()
    run_paperpilot(date_str=args.date, dry_run=args.dry_run, config_path=args.config)


if __name__ == "__main__":
    main()

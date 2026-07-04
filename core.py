"""
research_pipeline.py
────────────────────
LangGraph pipeline:
  user query → LLM clarifying Q&A (one-by-one) → refined arxiv query
  → download PDFs → extract paragraphs → summarise each → save MD files

Models (both on Groq):
  llama-3.3-70b-versatile  — structured JSON output (questions, refined query)
  openai/gpt-oss-120b      — reading & paragraph summarisation
"""

import os
import re
import urllib.request
from pathlib import Path
from typing import TypedDict

import arxiv
import fitz  # PyMuPDF
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# LLM clients
# ─────────────────────────────────────────────────────────────────────────────

_KEY = os.getenv("GROQ_API_KEY")

json_llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=_KEY, temperature=0)
reader_llm = ChatGroq(model="openai/gpt-oss-120b",   api_key=_KEY, temperature=0)

# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schemas (used with .with_structured_output)
# ─────────────────────────────────────────────────────────────────────────────

class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(description="3–5 focused questions to clarify research intent")

class RefinedQuery(BaseModel):
    query: str     = Field(description="Optimised arxiv query using ti:, abs:, AND/OR/NOT syntax")
    reasoning: str = Field(description="One-line explanation of why this query is better")

class ParagraphSummary(BaseModel):
    summary:   str       = Field(description="2–3 sentence summary of the paragraph")
    key_terms: list[str] = Field(description="5–10 important technical terms")

# ─────────────────────────────────────────────────────────────────────────────
# Graph state
# ─────────────────────────────────────────────────────────────────────────────

class PipelineState(TypedDict):
    user_query:    str
    questions:     list[str]
    current_q_idx: int
    answers:       list[str]
    refined_query: str
    paper_infos:   list[dict]   # serialisable dicts, not arxiv.Result objects
    output_dir:    str

# ─────────────────────────────────────────────────────────────────────────────
# Shared retry decorator (5 attempts, exponential back-off 2–60 s)
# ─────────────────────────────────────────────────────────────────────────────

_retry = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    reraise=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Node 1 — Generate clarifying questions
# ─────────────────────────────────────────────────────────────────────────────

def generate_questions_node(state: PipelineState) -> dict:
    print("\n🔍 Generating clarifying questions...")
    structured = json_llm.with_structured_output(ClarifyingQuestions)

    @_retry
    def _call():
        return structured.invoke([
            SystemMessage(content=(
                "You are a research assistant. Given a rough topic, generate 3–5 concise "
                "questions to clarify: scope, time range, sub-domain, application area, "
                "and technical depth. One thing per question. Be direct."
            )),
            HumanMessage(content=f"Topic: {state['user_query']}"),
        ])

    result = _call()
    print(f"   ✓ {len(result.questions)} questions ready")
    return {"questions": result.questions, "current_q_idx": 0, "answers": []}

# ─────────────────────────────────────────────────────────────────────────────
# Node 2 — Ask questions one-by-one (human-in-the-loop via interrupt)
# ─────────────────────────────────────────────────────────────────────────────

def ask_question_node(state: PipelineState) -> dict:
    idx      = state["current_q_idx"]
    question = state["questions"][idx]
    total    = len(state["questions"])

    print(f"\n❓ [{idx + 1}/{total}] {question}")
    answer = interrupt({"question": question, "idx": idx, "total": total})

    return {
        "answers":       state["answers"] + [answer],
        "current_q_idx": idx + 1,
    }

def _questions_router(state: PipelineState) -> str:
    """Loop back while there are more questions, then move on."""
    return "ask_question" if state["current_q_idx"] < len(state["questions"]) else "refine_query"

# ─────────────────────────────────────────────────────────────────────────────
# Node 3 — Refine the arxiv query from Q&A
# ─────────────────────────────────────────────────────────────────────────────

def refine_query_node(state: PipelineState) -> dict:
    print("\n✏️  Refining search query...")
    structured = json_llm.with_structured_output(RefinedQuery)

    qa_block = "\n".join(
        f"Q: {q}\nA: {a}"
        for q, a in zip(state["questions"], state["answers"])
    )

    @_retry
    def _call():
        return structured.invoke([
            SystemMessage(content=(
                "Write an optimised arxiv search query from the user's intent.\n"
                "Use: ti:(title terms), abs:(abstract terms), AND / OR / NOT.\n"
                "Example: ti:(structured output) AND abs:(language model JSON schema)"
            )),
            HumanMessage(content=f"Original topic: {state['user_query']}\n\n{qa_block}"),
        ])

    result = _call()
    print(f"   Query : {result.query}")
    print(f"   Why   : {result.reasoning}")
    return {"refined_query": result.query}

# ─────────────────────────────────────────────────────────────────────────────
# Node 4 — Search arxiv
# ─────────────────────────────────────────────────────────────────────────────

def search_arxiv_node(state: PipelineState) -> dict:
    print(f"\n🔎 Searching arxiv: {state['refined_query']}")

    @_retry
    def _search():
        client = arxiv.Client()
        search = arxiv.Search(
            query=state["refined_query"],
            max_results=10,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )
        return list(client.results(search))

    papers = _search()
    paper_infos = []
    for r in papers:
        paper_infos.append({
            "title":     r.title,
            "paper_id":  r.get_short_id(),
            "pdf_url":   r.pdf_url,
            "abstract":  r.summary,
            "authors":   [str(a) for a in r.authors],
            "published": str(r.published),
        })
        print(f"   📄 {r.title[:75]}")

    print(f"\n   Found {len(paper_infos)} papers")
    return {"paper_infos": paper_infos}

# ─────────────────────────────────────────────────────────────────────────────
# Node 5 — Download PDFs and extract paragraphs
# ─────────────────────────────────────────────────────────────────────────────

def download_parse_node(state: PipelineState) -> dict:
    out = state.get("output_dir", "research_output")
    Path(out).mkdir(parents=True, exist_ok=True)
    updated = []

    for paper in state["paper_infos"]:
        # Build a safe directory name from the title
        safe      = re.sub(r"[^\w\s-]", "", paper["title"])[:50].strip().replace(" ", "_")
        paper_dir = Path(out) / safe
        paper_dir.mkdir(exist_ok=True)
        pdf_path  = paper_dir / "paper.pdf"

        print(f"\n⬇️  {paper['title'][:65]}...")

        @_retry
        def _download(url=paper["pdf_url"], dest=pdf_path):
            urllib.request.urlretrieve(url, dest)

        try:
            _download()

            doc       = fitz.open(str(pdf_path))
            full_text = "".join(page.get_text() for page in doc)
            doc.close()

            # Split on double-newline; keep only substantive paragraphs
            paras = [s.strip() for s in full_text.split("\n\n") if len(s.strip()) > 150]

            paper["paragraphs"] = paras
            paper["paper_dir"]  = str(paper_dir)
            print(f"   ✅ {len(paras)} paragraphs extracted")

        except Exception as e:
            print(f"   ❌ {e}")
            paper["paragraphs"] = []
            paper["paper_dir"]  = str(paper_dir)

        updated.append(paper)

    return {"paper_infos": updated, "output_dir": out}

# ─────────────────────────────────────────────────────────────────────────────
# Node 6 — Summarise each paragraph → summary.md + terms.md
# ─────────────────────────────────────────────────────────────────────────────

def summarize_node(state: PipelineState) -> dict:
    print("\n📝 Summarising papers…")
    structured_reader = reader_llm.with_structured_output(ParagraphSummary)

    # Define once; reused for every paragraph (retry resets per call)
    @_retry
    def _summarise(para: str) -> ParagraphSummary:
        return structured_reader.invoke([
            SystemMessage(content=(
                "You are a research analyst. Summarise this paragraph from an academic paper "
                "in 2–3 clear sentences. Then list 5–10 important technical terms found in it."
            )),
            HumanMessage(content=para),
        ])

    for paper in state["paper_infos"]:
        paras = paper.get("paragraphs", [])
        if not paras:
            print(f"   ⚠️  Skipping (no content): {paper['title'][:50]}")
            continue

        paper_dir  = Path(paper["paper_dir"])
        all_terms: list[str] = []
        cap        = min(len(paras), 25)   # cap at 25 paragraphs per paper

        # ── Build summary.md ────────────────────────────────────────────────
        md = [
            f"# {paper['title']}\n",
            f"**Authors:** {', '.join(paper['authors'])}  ",
            f"**Published:** {paper['published']}\n",
            "## Abstract\n",
            paper["abstract"] + "\n",
            "## Paragraph Summaries\n",
        ]

        print(f"\n   📄 {paper['title'][:60]} ({cap} paras)")

        for i, para in enumerate(paras[:cap]):
            try:
                res = _summarise(para)
                md += [
                    f"### Para {i + 1}\n",
                    f"**Summary:** {res.summary}\n",
                    f"**Key Terms:** {', '.join(res.key_terms)}\n",
                ]
                all_terms.extend(res.key_terms)
                if (i + 1) % 5 == 0 or (i + 1) == cap:
                    print(f"      ✓ {i + 1}/{cap}")
            except Exception as e:
                print(f"      ❌ Para {i + 1}: {e}")

        (paper_dir / "summary.md").write_text("\n".join(md), encoding="utf-8")

        # ── Build terms.md ───────────────────────────────────────────────────
        unique_terms = sorted(set(t.strip().lower() for t in all_terms if t.strip()))
        terms_md     = f"# Key Terms — {paper['title']}\n\n" + "\n".join(f"- {t}" for t in unique_terms)
        (paper_dir / "terms.md").write_text(terms_md, encoding="utf-8")

        print(f"      ✅ summary.md + terms.md saved  ({len(unique_terms)} unique terms)")

    print(f"\n🎉 Output → {state['output_dir']}/")
    return {}

# ─────────────────────────────────────────────────────────────────────────────
# Graph builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_graph() -> StateGraph:
    g = StateGraph(PipelineState)

    g.add_node("generate_questions", generate_questions_node)
    g.add_node("ask_question",       ask_question_node)
    g.add_node("refine_query",       refine_query_node)
    g.add_node("search_arxiv",       search_arxiv_node)
    g.add_node("download_parse",     download_parse_node)
    g.add_node("summarize",          summarize_node)

    g.set_entry_point("generate_questions")
    g.add_edge("generate_questions", "ask_question")

    g.add_conditional_edges("ask_question", _questions_router, {
        "ask_question": "ask_question",   # loop until all questions done
        "refine_query": "refine_query",
    })

    g.add_edge("refine_query",   "search_arxiv")
    g.add_edge("search_arxiv",   "download_parse")
    g.add_edge("download_parse", "summarize")
    g.add_edge("summarize",      END)

    return g

# ─────────────────────────────────────────────────────────────────────────────
# ResearchPipeline — the main class you interact with
# ─────────────────────────────────────────────────────────────────────────────

class ResearchPipeline:
    """
    Usage:
        pipeline = ResearchPipeline(output_dir="my_research")
        pipeline.run("json schema enforcement in language models")
    """

    def __init__(self, output_dir: str = "research_output"):
        self.output_dir = output_dir
        self.memory     = MemorySaver()          # keeps state across interrupt/resume
        self.app        = _build_graph().compile(checkpointer=self.memory)

    def run(self, user_query: str, thread_id: str = "session-1") -> None:
        config  = {"configurable": {"thread_id": thread_id}}
        initial = {
            "user_query":    user_query,
            "questions":     [],
            "current_q_idx": 0,
            "answers":       [],
            "refined_query": "",
            "paper_infos":   [],
            "output_dir":    self.output_dir,
        }

        print(f'\n🚀 Research Pipeline — "{user_query}"')

        graph_input = initial
        while True:
            interrupted = False
            for chunk in self.app.stream(graph_input, config, stream_mode="updates"):
                if "__interrupt__" in chunk:
                    # Node already printed the question via print(); just collect answer
                    interrupted  = True
                    answer       = input("Your answer: ").strip()
                    graph_input  = Command(resume=answer)
                    break
            if not interrupted:
                break   # graph ran to END with no interrupt → done

        print("\n✅ Pipeline complete!")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    topic = input("Enter research topic: ").strip()
    ResearchPipeline().run(topic)
#!/usr/bin/env python3
"""
Research Radar - Daily Paper Fetcher
Fetches from arXiv cs.CL + cs.AI + Semantic Scholar,
uses Gemini Flash (free) to tag and summarize each paper,
then writes papers.json to public/ for the static site.
"""

import os
import json
import time
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# ── Config ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]  # set in GitHub Actions secret
OUTPUT_PATH    = os.path.join(os.path.dirname(__file__), "..", "public", "papers.json")
MAX_PAPERS     = 30   # papers to fetch per run
ARXIV_CATS     = ["cs.CL", "cs.AI", "cs.LG"]

VALID_TAGS = [
    "LLMs", "RAG", "Agents", "Reasoning", "Fine-tuning",
    "NLP", "Evaluation", "Multimodal", "Alignment", "RLHF",
    "Prompting", "Retrieval", "Efficient Training", "Datasets",
    "Interpretability", "Code Generation", "Speech", "Vision-Language",
    "Knowledge Graphs", "Reinforcement Learning"
]

# ── arXiv fetch ───────────────────────────────────────────────────────────────
def fetch_arxiv(max_results=20):
    query = "+OR+".join(f"cat:{c}" for c in ARXIV_CATS)
    params = urllib.parse.urlencode({
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    })
    url = f"https://export.arxiv.org/api/query?{params}"
    with urllib.request.urlopen(url, timeout=30) as r:
        raw = r.read()

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(raw)
    papers = []
    for entry in root.findall("atom:entry", ns):
        arxiv_id = entry.find("atom:id", ns).text.split("/abs/")[-1]
        title    = entry.find("atom:title", ns).text.strip().replace("\n", " ")
        summary  = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
        authors  = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
        published = entry.find("atom:published", ns).text[:10]
        link     = f"https://arxiv.org/abs/{arxiv_id}"
        papers.append({
            "id": f"arxiv-{arxiv_id}",
            "arxiv_id": arxiv_id,
            "title": title,
            "abstract": summary[:1000],
            "authors": authors[:4],
            "date": published,
            "url": link,
            "source": "arXiv",
        })
    return papers

# ── Semantic Scholar fetch ────────────────────────────────────────────────────
def fetch_semantic_scholar(max_results=10):
    """Fetch recent NLP/LLM papers from Semantic Scholar public API (no key needed)."""
    fields = "paperId,title,abstract,authors,year,publicationDate,externalIds,venue"
    query  = urllib.parse.quote("large language model NLP transformer")
    url = (
        f"https://api.semanticscholar.org/graph/v1/paper/search"
        f"?query={query}&limit={max_results}&fields={fields}"
        f"&sort=publicationDate:desc"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "ResearchRadar/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
    except Exception as e:
        print(f"Semantic Scholar fetch failed: {e}")
        return []

    papers = []
    for p in data.get("data", []):
        if not p.get("abstract"):
            continue
        arxiv_id = (p.get("externalIds") or {}).get("ArXiv")
        paper_id = arxiv_id or p["paperId"]
        url_link = (f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id
                    else f"https://www.semanticscholar.org/paper/{p['paperId']}")
        papers.append({
            "id": f"ss-{paper_id}",
            "arxiv_id": arxiv_id,
            "title": p["title"],
            "abstract": p["abstract"][:1000],
            "authors": [a["name"] for a in (p.get("authors") or [])[:4]],
            "date": (p.get("publicationDate") or str(p.get("year", "")))[:10],
            "url": url_link,
            "source": "Semantic Scholar",
        })
    return papers

# ── Gemini tagging + summarisation ───────────────────────────────────────────
def gemini_enrich(paper):
    """Call Gemini Flash to tag and summarise one paper. Returns (tags, summary)."""
    prompt = f"""You are a research assistant specialising in NLP and LLMs.

Paper title: {paper['title']}
Abstract: {paper['abstract']}

Tasks:
1. Pick 2–5 tags that best describe this paper from this list ONLY:
   {', '.join(VALID_TAGS)}
2. Write a 2–3 sentence plain-English summary of what the paper does and why it matters for NLP/LLM researchers.

Respond with valid JSON only (no markdown fences):
{{"tags": ["tag1", "tag2"], "summary": "Your summary here."}}"""

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 300},
    }).encode()

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read())

    text = resp["candidates"][0]["content"]["parts"][0]["text"].strip()
    # strip accidental markdown fences
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    result = json.loads(text)
    tags    = [t for t in result.get("tags", []) if t in VALID_TAGS][:5]
    summary = result.get("summary", "")
    return tags, summary

# ── Dedup helpers ─────────────────────────────────────────────────────────────
def load_existing():
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH) as f:
            return json.load(f)
    return {"papers": [], "last_updated": ""}

def merge(existing_papers, new_papers):
    seen = {p["id"] for p in existing_papers}
    merged = list(existing_papers)
    added  = 0
    for p in new_papers:
        if p["id"] not in seen:
            merged.append(p)
            seen.add(p["id"])
            added += 1
    # keep newest 500 papers max
    merged.sort(key=lambda p: p.get("date", ""), reverse=True)
    return merged[:500], added

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=== Research Radar Fetcher ===")
    print(f"Run date: {datetime.date.today()}")

    print("\n[1/3] Fetching arXiv papers…")
    arxiv_papers = fetch_arxiv(MAX_PAPERS)
    print(f"      Got {len(arxiv_papers)} from arXiv")

    print("[1/3] Fetching Semantic Scholar papers…")
    ss_papers = fetch_semantic_scholar(10)
    print(f"      Got {len(ss_papers)} from Semantic Scholar")

    raw_papers = arxiv_papers + ss_papers

    print(f"\n[2/3] Enriching {len(raw_papers)} papers with Gemini Flash…")
    enriched = []
    for i, p in enumerate(raw_papers):
        print(f"      [{i+1}/{len(raw_papers)}] {p['title'][:70]}…")
        try:
            tags, summary = gemini_enrich(p)
            p["tags"]    = tags
            p["summary"] = summary
        except Exception as e:
            print(f"      ⚠ Gemini error: {e}")
            p["tags"]    = []
            p["summary"] = p["abstract"][:300]
        enriched.append(p)
        time.sleep(0.5)   # stay under free-tier rate limit

    print("\n[3/3] Merging with existing papers and saving…")
    existing_data = load_existing()
    all_papers, added = merge(existing_data["papers"], enriched)

    output = {
        "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
        "total": len(all_papers),
        "papers": all_papers,
    }
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone. Added {added} new papers. Total: {len(all_papers)}")

if __name__ == "__main__":
    main()

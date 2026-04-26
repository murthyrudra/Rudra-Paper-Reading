#!/usr/bin/env python3
"""
Research Radar - Daily Paper Fetcher
Sources: arXiv cs.CL/cs.AI, Semantic Scholar, ACL Anthology, ICLR (OpenReview)
Uses Gemini Flash (free tier) to auto-tag and summarise each paper.
Writes public/papers.json for the static site.
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
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "public", "papers.json")
MAX_PAPERS = 200  # papers to fetch per run
ARXIV_CATS = ["cs.CL"]  # drop cs.LG to stay focused on NLP/LLMs
MAX_ARXIV = 50
MAX_SS = 10
MAX_ACL = 50  # per venue fetch
MAX_ICLR = 50

# ── Interest filter — papers not matching any keyword are skipped ─────────────
# Edit this list to focus on what YOU care about.
INTEREST_KEYWORDS = [
    # --- RAG ---
    "retrieval augmented generation",
    "retrieval-augmented generation",
    "rag",
    "dense retrieval",
    "hybrid retrieval",
    "document retrieval",
    "retriever",
    "reranker",
    # --- Embedding models ---
    "embedding model",
    "text embedding",
    "sentence embedding",
    "dense embedding",
    "contrastive learning",
    "dual encoder",
    "bi-encoder",
    "representation learning",
    # --- Pretraining ---
    "pretraining",
    "pre-training",
    "language model pretraining",
    "foundation model",
    "self-supervised learning",
    "masked language modeling",
    "causal language modeling",
    "next token prediction",
]


def is_relevant(paper):
    text = (paper.get("title", "") + " " + paper.get("abstract", "")).lower()
    rag = any(
        kw in text
        for kw in [
            "retrieval augmented",
            "rag",
            "retriever",
            "reranker",
            "dense retrieval",
        ]
    )

    embedding = any(
        kw in text
        for kw in ["embedding", "bi-encoder", "dual encoder", "contrastive learning"]
    )

    pretraining = any(
        kw in text
        for kw in [
            "pretraining",
            "pre-training",
            "masked language modeling",
            "causal language modeling",
            "self-supervised",
        ]
    )

    return rag or embedding or pretraining


VALID_TAGS = [
    "LLMs",
    "RAG",
    "Agents",
    "Reasoning",
    "Fine-tuning",
    "NLP",
    "Evaluation",
    "Alignment",
    "RLHF",
    "Prompting",
    "Retrieval",
    "Efficient Training",
    "Datasets",
    "Knowledge Graphs",
    "Reinforcement Learning",
]


# ── arXiv fetch ───────────────────────────────────────────────────────────────
def fetch_arxiv(max_results=20):
    query = "+OR+".join(f"cat:{c}" for c in ARXIV_CATS)
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": max_results,
        }
    )
    url = f"https://export.arxiv.org/api/query?{params}"
    with urllib.request.urlopen(url, timeout=30) as r:
        raw = r.read()

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(raw)
    papers = []
    for entry in root.findall("atom:entry", ns):
        arxiv_id = entry.find("atom:id", ns).text.split("/abs/")[-1]
        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
        summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
        authors = [
            a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)
        ]
        published = entry.find("atom:published", ns).text[:10]
        link = f"https://arxiv.org/abs/{arxiv_id}"
        papers.append(
            {
                "id": f"arxiv-{arxiv_id}",
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": summary[:1000],
                "authors": authors[:4],
                "date": published,
                "url": link,
                "source": "arXiv",
            }
        )
    return papers


# ── ACL Anthology ─────────────────────────────────────────────────────────────
# Uses the Semantic Scholar API filtered by ACL venues — no scraping needed.
ACL_VENUES = [
    "ACL",
    "EMNLP",
    "NAACL",
    "EACL",
    "COLING",
    "Findings of ACL",
    "Findings of EMNLP",
    "Findings of NAACL",
    "TACL",
    "CL",
]


def safe_urlopen(req, retries=5):
    for i in range(retries):
        try:
            return urllib.request.urlopen(req, timeout=20)
        except Exception as e:
            if "429" in str(e):
                sleep = (2**i) + 1
                print(f"    Rate limited. Sleeping {sleep}s")
                time.sleep(sleep)
            else:
                raise
    raise Exception("Max retries exceeded")


def fetch_acl_anthology(max_results=MAX_ACL):
    """
    Pull recent papers from ACL venues via Semantic Scholar's venue filter.
    Falls back to the ACL Anthology RSS feed for the current year.
    """
    papers = []

    # --- Method 1: Semantic Scholar venue search (gets abstracts) ---
    for venue in ["ACL", "EMNLP", "NAACL"]:
        fields = "paperId,title,abstract,authors,year,publicationDate,externalIds,venue"
        query = urllib.parse.quote(f"language model NLP {venue}")
        url = (
            f"https://api.semanticscholar.org/graph/v1/paper/search"
            f"?query={query}&limit=8&fields={fields}&sort=publicationDate:desc"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "ResearchRadar/1.0"})
        try:
            with safe_urlopen(req) as r:
                data = json.loads(r.read())
            for p in data.get("data", []):
                v = (p.get("venue") or "").upper()
                if not any(
                    acl in v
                    for acl in ["ACL", "EMNLP", "NAACL", "EACL", "COLING", "TACL"]
                ):
                    continue
                if not p.get("abstract"):
                    continue
                arxiv_id = (p.get("externalIds") or {}).get("ArXiv")
                acl_id = (p.get("externalIds") or {}).get("ACL")
                pid = acl_id or arxiv_id or p["paperId"]
                link = (
                    f"https://aclanthology.org/{acl_id}"
                    if acl_id
                    else (
                        f"https://arxiv.org/abs/{arxiv_id}"
                        if arxiv_id
                        else f"https://www.semanticscholar.org/paper/{p['paperId']}"
                    )
                )
                papers.append(
                    {
                        "id": f"acl-{pid}",
                        "title": p["title"],
                        "abstract": p["abstract"][:1000],
                        "authors": [a["name"] for a in (p.get("authors") or [])[:4]],
                        "date": (p.get("publicationDate") or str(p.get("year", "")))[
                            :10
                        ],
                        "url": link,
                        "source": "ACL Anthology",
                        "venue": p.get("venue", venue),
                    }
                )
            time.sleep(1.3)
        except Exception as e:
            print(f"  ⚠ ACL S2 fetch ({venue}) failed: {e}")

    # --- Method 2: ACL Anthology RSS (recent additions, no abstracts) ---
    # Use as a fallback / supplement when S2 doesn't return enough
    if len(papers) < 5:
        try:
            rss_url = "https://aclanthology.org/feed.xml"
            req = urllib.request.Request(
                rss_url, headers={"User-Agent": "ResearchRadar/1.0"}
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                rss_raw = r.read()
            root = ET.fromstring(rss_raw)
            seen_ids = {p["id"] for p in papers}
            for item in root.findall(".//item")[:max_results]:
                title_el = item.find("title")
                link_el = item.find("link")
                desc_el = item.find("description")
                pub_el = item.find("pubDate")
                if title_el is None or link_el is None:
                    continue
                link = link_el.text or ""
                acl_id = link.rstrip("/").split("/")[-1]
                pid = f"acl-rss-{acl_id}"
                if pid in seen_ids:
                    continue
                abstract = ""
                if desc_el is not None and desc_el.text:
                    abstract = desc_el.text.strip()[:1000]
                date_str = ""
                if pub_el is not None and pub_el.text:
                    try:
                        from email.utils import parsedate_to_datetime

                        date_str = parsedate_to_datetime(pub_el.text).date().isoformat()
                    except Exception:
                        pass
                papers.append(
                    {
                        "id": pid,
                        "title": title_el.text.strip() if title_el.text else "",
                        "abstract": abstract,
                        "authors": [],
                        "date": date_str,
                        "url": link,
                        "source": "ACL Anthology",
                        "venue": "ACL Anthology",
                    }
                )
        except Exception as e:
            print(f"  ⚠ ACL RSS fallback failed: {e}")

    return papers[:max_results]


# ── ICLR (OpenReview) ─────────────────────────────────────────────────────────
def fetch_iclr(max_results=MAX_ICLR):
    """
    Fetch recent ICLR papers via the OpenReview public API.
    Gets accepted papers from the most recent ICLR venue available.
    """
    # Try the two most recent years
    current_year = datetime.date.today().year
    papers = []

    for year in [current_year, current_year - 1]:
        venue_id = urllib.parse.quote(f"ICLR.cc/{year}/Conference")
        url = (
            f"https://api2.openreview.net/notes"
            f"?content.venue=ICLR+{year}+poster"
            f"&details=replyCount"
            f"&limit={max_results}"
            f"&offset=0"
            f"&sort=cdate:desc"
        )
        # Also try oral/spotlight
        urls_to_try = [
            (
                f"https://api2.openreview.net/notes"
                f"?content.venueid=ICLR.cc%2F{year}%2FConference"
                f"&limit={max_results}&offset=0&sort=cdate:desc"
            ),
        ]
        for u in urls_to_try:
            req = urllib.request.Request(u, headers={"User-Agent": "ResearchRadar/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    data = json.loads(r.read())
                notes = data.get("notes", [])
                if not notes:
                    continue
                for note in notes:
                    content = note.get("content", {})

                    # OpenReview v2 wraps values in {"value": ...}
                    def val(field):
                        v = content.get(field, "")
                        return v.get("value", "") if isinstance(v, dict) else v

                    title = val("title")
                    abstract = val("abstract")
                    authors = val("authors")
                    if isinstance(authors, str):
                        authors = [authors]
                    pdf = val("pdf")
                    forum = note.get("forum", "")
                    venue = val("venue") or f"ICLR {year}"

                    if not title or not abstract:
                        continue

                    link = (
                        f"https://openreview.net/forum?id={forum}"
                        if forum
                        else "https://openreview.net"
                    )
                    date_ts = note.get("cdate") or note.get("mdate") or 0
                    if date_ts:
                        date_str = (
                            datetime.datetime.utcfromtimestamp(date_ts / 1000)
                            .date()
                            .isoformat()
                        )
                    else:
                        date_str = str(year)

                    papers.append(
                        {
                            "id": f"iclr-{forum or title[:40]}",
                            "title": title,
                            "abstract": abstract[:1000],
                            "authors": authors[:4],
                            "date": date_str,
                            "url": link,
                            "source": "ICLR",
                            "venue": venue,
                        }
                    )
                if papers:
                    break  # got results for this year, stop
            except Exception as e:
                print(f"  ⚠ ICLR OpenReview ({year}) failed: {e}")
        if papers:
            break

    return papers[:max_results]


# ── Gemini tagging + summarisation (STRICT FILTERING) ────────────────────────
def gemini_enrich(paper):
    """
    Call Gemini Flash to:
    1. Classify paper into: RAG / Embedding Models / LLM Pretraining / Irrelevant
    2. Tag + summarise relevant papers

    Returns: (is_relevant, category, tags, summary)
    """

    prompt = f"""You are a research assistant focused ONLY on these areas:
1. Retrieval-Augmented Generation (RAG)
2. Training embedding models (dense retrieval, bi-encoders, contrastive learning)
3. Pretraining of large language models

If a paper is NOT primarily about one of these, mark it as IRRELEVANT.

Paper title: {paper['title']}
Abstract: {paper['abstract']}

Tasks:
1. Classify into EXACTLY one of:
   - "RAG"
   - "Embedding Models"
   - "LLM Pretraining"
   - "Irrelevant"

2. If relevant, pick 2–5 tags from:
   {', '.join(VALID_TAGS)}

3. If relevant, write a 2–3 sentence summary.

Return JSON ONLY:
{{
  "category": "...",
  "tags": ["tag1", "tag2"],
  "summary": "..."
}}"""

    payload = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 300},
        }
    ).encode()

    url = (
        "https://generativelanguage.googleapis.com/v1/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
    except Exception:
        return False, "Irrelevant", [], paper.get("abstract", "")[:300]

    # --- Extract text safely ---
    try:
        text = resp["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return False, "Irrelevant", [], paper.get("abstract", "")[:300]

    # --- Clean markdown fences ---
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    # --- Parse JSON safely ---
    try:
        result = json.loads(text)
    except Exception:
        return False, "Irrelevant", [], paper.get("abstract", "")[:300]

    category = result.get("category", "").strip()
    tags = result.get("tags", [])
    summary = result.get("summary", "")

    # --- HARD FILTER ---
    if category not in ["RAG", "Embedding Models", "LLM Pretraining"]:
        return False, "Irrelevant", [], ""

    # --- Clean tags ---
    tags = [t for t in tags if t in VALID_TAGS][:5]

    return True, category, tags, summary


# ── Dedup helpers ─────────────────────────────────────────────────────────────
def load_existing():
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH) as f:
            return json.load(f)
    return {"papers": [], "last_updated": ""}


def merge(existing_papers, new_papers):
    seen = {p["id"] for p in existing_papers}
    merged = list(existing_papers)
    added = 0
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
    print(f"Run date: {datetime.date.today()}\n")

    all_raw = []

    print("[1/3] arXiv cs.CL + cs.AI…")
    papers = fetch_arxiv()
    print(f"      Fetched {len(papers)}")
    all_raw += papers

    print("[2/3] ACL Anthology…")
    papers = fetch_acl_anthology()
    print(f"      Fetched {len(papers)}")
    all_raw += papers

    print("[3/3] ICLR (OpenReview)…")
    papers = fetch_iclr()
    print(f"      Fetched {len(papers)}")
    all_raw += papers

    # Deduplicate by id before enrichment
    seen, unique = set(), []
    for p in all_raw:
        if p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)

    # Interest filter — skip papers clearly outside NLP/LLM
    relevant = [p for p in unique if is_relevant(p)]
    skipped = len(unique) - len(relevant)
    print(
        f"\nInterest filter: {len(relevant)} relevant / {skipped} skipped out of {len(unique)} total"
    )

    print(f"\nEnriching {len(relevant)} papers with Gemini Flash…")
    enriched = []
    for i, p in enumerate(relevant):
        print(f"  [{i+1}/{len(relevant)}] [{p['source']}] {p['title'][:65]}…")
        try:
            is_rel, category, tags, summary = gemini_enrich(p)

            if not is_rel:
                continue

            p["category"] = category
            p["tags"] = tags
            p["summary"] = summary
            enriched.append(p)
        except Exception as e:
            print(f"  ⚠ Gemini error: {e}")
            p["tags"] = []
            p["summary"] = p.get("abstract", "")[:300]

        time.sleep(0.5)  # stay within free-tier rate limit

    print("\nMerging with existing papers and saving…")
    existing_data = load_existing()
    all_papers, added = merge(existing_data.get("papers", []), enriched)

    output = {
        "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
        "total": len(all_papers),
        "papers": all_papers,
    }
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone ✓  Added {added} new papers. Total in store: {len(all_papers)}")


if __name__ == "__main__":
    main()

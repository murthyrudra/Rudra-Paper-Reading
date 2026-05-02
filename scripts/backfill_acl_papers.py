#!/usr/bin/env python3
"""
Backfill ACL Anthology with historical papers
Uses ACL Anthology Python library to search by keywords
Filters by relevance and auto-tags with Gemini
"""

import os
import json
import time
import datetime
from openai import OpenAI
import requests
from dotenv import dotenv_values

config = dotenv_values(".env")
RITS_API_KEY = config.get("RITS_API_KEY")

if not RITS_API_KEY:
    raise ValueError("Set RITS_API_KEY in .env")


def get_rits_model_list(api_key):
    url = "https://rits.fmaas.res.ibm.com/ritsapi/inferenceinfo"
    response = requests.get(url, headers={"RITS_API_KEY": api_key})
    if response.status_code == 200:
        return {m["model_name"]: m["endpoint"] for m in response.json()}
    else:
        raise Exception(response.text)


# pick a model (you can change this)
RITS_MODEL_NAME = "meta-llama/llama-3-3-70b-instruct"

minfo = get_rits_model_list(RITS_API_KEY)
endpoint = minfo[RITS_MODEL_NAME]

client = OpenAI(
    api_key=RITS_API_KEY,
    base_url=f"{endpoint}/v1",
    default_headers={"RITS_API_KEY": RITS_API_KEY},
)


OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "public", "papers.json")

# Search keywords - papers matching ANY of these will be included
SEARCH_KEYWORDS = [
    "retrieval augmented generation",
    " rag ",
    "dense retrieval",
    "neural retrieval",
    "passage retrieval",
    "document retrieval",
    "embedding model",
    "bi-encoder",
    "dual encoder",
    "language model pretraining",
    "masked language modeling",
    "self-supervised learning",
]

# Venues to search
VENUES = ["acl", "emnlp", "naacl", "eacl", "coling", "tacl", "findings"]

# Year range
START_YEAR = 2020
END_YEAR = datetime.date.today().year

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


# ── Helper functions ──────────────────────────────────────────────────────────
def load_existing():
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH) as f:
            return json.load(f)
    return {"papers": [], "last_updated": ""}


def save_papers(data):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(data, f, indent=2)


def matches_keywords(text):
    """Check if text contains any of our keywords"""
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in SEARCH_KEYWORDS)


MONTH_MAP = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def parse_month(m):
    if not m:
        return 1
    m = str(m).strip().lower()

    # numeric string
    if m.isdigit():
        return max(1, min(12, int(m)))

    # textual month
    return MONTH_MAP.get(m[:3], 1)


def search_acl_anthology():
    """
    Search ACL Anthology using the official Python library
    """
    try:
        from acl_anthology import Anthology
    except ImportError:
        print("❌ ACL Anthology library not installed!")
        print("   Install with: pip install acl-anthology")
        return []

    print("Loading ACL Anthology database...")
    anthology = Anthology(datadir="/Users/rudramurthy/Downloads/acl-anthology/data/")

    papers = []
    total_checked = 0

    print(VENUES)

    for event_id in anthology.events:
        event = anthology.events[event_id]
        # event.id examples: acl-2023, emnlp-2022, etc.
        event_id = event.id.lower()

        # Filter by venue + year
        for venue in VENUES:
            if not any(v in event_id for v in VENUES):
                continue

            import re

            match = re.search(r"\b(20\d{2})\b", event_id)
            if not match:
                continue

            year = int(match.group(1))

            if year < START_YEAR or year > END_YEAR:
                continue

            print(f"\n📅 {event_id.upper()}")

            for volume in event.volumes():
                for paper in volume.papers():
                    total_checked += 1

                    title = str(paper.title or "")
                    abstract = str(paper.abstract or "")

                    # Skip weak metadata
                    if not abstract or len(abstract) < 100:
                        continue

                    if not matches_keywords(title):
                        continue

                    # Authors
                    authors = []
                    if paper.authors:
                        authors = [str(a) for a in paper.authors[:4]]

                    # Date handling
                    month_raw = paper.month if paper.month else 1

                    month = parse_month(month_raw)

                    papers.append(
                        {
                            "id": f"acl-{paper.id}",
                            "title": title,
                            "abstract": abstract[:1000],
                            "authors": authors,
                            "date": f"{year}-{int(month):02d}-01",
                            "url": f"https://aclanthology.org/{paper.id}/",
                            "source": "ACL Anthology",
                            "venue": f"{event_id.upper()}",
                        }
                    )
                    print(title)

            print(f"  ✓ processed")

    print(f"\nTotal papers checked: {total_checked}")
    print(f"Papers matching keywords: {len(papers)}")

    return papers


def build_batch_prompt(batch):
    prompt = """You are an NLP research assistant.

Classify each paper.

Only keep:
- RAG
- Embedding Models
- LLM Pretraining

Return ONLY JSON list:

[
  {
    "id": "...",
    "category": "...",
    "tags": ["..."],
    "summary": "..."
  }
]
"""

    for p in batch:
        prompt += f"""
ID: {p['id']}
Title: {p['title']}
Abstract: {p['abstract'][:500]}
"""

    return prompt


def rits_batch(batch):
    prompt = build_batch_prompt(batch)

    try:
        completion = client.chat.completions.create(
            model=RITS_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a strict JSON generator."},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=1500,
            temperature=0,
        )

        text = completion.choices[0].message.content.strip()

        # clean markdown
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        return json.loads(text)

    except Exception as e:
        print("⚠️ RITS batch error:", e)
        return None

    finally:
        time.sleep(2)  # RITS is more tolerant, lower sleep


def rits_batch_retry(batch, retries=3):
    for i in range(retries):
        result = rits_batch(batch)
        if result:
            return result
        time.sleep(2**i)
    return []


def main():
    print("=== ACL Anthology Backfill ===")
    print(f"Searching papers from {START_YEAR} to {END_YEAR}")
    print(f"Venues: {', '.join(v.upper() for v in VENUES)}")
    print(f"Keywords: {len(SEARCH_KEYWORDS)} search terms\n")

    # Check if library is installed
    try:
        import acl_anthology
    except ImportError:
        print("❌ ACL Anthology library not installed!")
        print("\nInstall with:")
        print("  pip install acl-anthology")
        print("\nOr add to requirements.txt and run:")
        print("  pip install -r requirements.txt")
        return

    # Load existing papers
    existing_data = load_existing()
    existing_ids = {p["id"] for p in existing_data.get("papers", [])}
    print(f"Current papers in database: {len(existing_ids)}\n")

    # Search ACL Anthology
    all_papers = search_acl_anthology()

    if not all_papers:
        print("\n❌ No papers found matching keywords.")
        return

    # Deduplicate
    new_papers = [p for p in all_papers if p["id"] not in existing_ids]

    print(f"\n{'='*60}")
    print(f"Total papers found: {len(all_papers)}")
    print(f"New papers (not in database): {len(new_papers)}")
    print(f"{'='*60}\n")

    if not new_papers:
        print("No new papers to add. Exiting.")
        return

    # Ask user confirmation
    print(f"Found {len(new_papers)} new papers to process.")

    # Enrich with Gemma (batched)
    print(f"\nEnriching {len(new_papers)} papers with Gemma (batched)...")

    enriched = []
    skipped = 0
    BATCH_SIZE = 5

    print(f"\nEnriching {len(new_papers)} papers with RITS (batched)...")

    enriched = []
    skipped = 0

    for i in range(0, len(new_papers), BATCH_SIZE):
        batch = new_papers[i : i + BATCH_SIZE]

        print(f"  [Batch {i//BATCH_SIZE + 1}]")

        results = rits_batch_retry(batch)

        if not results:
            skipped += len(batch)
            continue

        for r in results:
            if r.get("category") not in ["RAG", "Embedding Models", "LLM Pretraining"]:
                skipped += 1
                continue

            original = next((p for p in batch if p["id"] == r.get("id")), None)
            if not original:
                continue

            original["category"] = r.get("category")
            original["tags"] = [t for t in r.get("tags", []) if t in VALID_TAGS][:5]
            original["summary"] = r.get("summary", "")

            enriched.append(original)

    print(f"\n{'='*60}")
    print(f"✓ Enriched: {len(enriched)} papers")
    print(f"✗ Filtered out: {skipped} papers")
    print(f"{'='*60}\n")

    if not enriched:
        print("No relevant papers after filtering. Exiting.")
        return

    # Merge with existing
    all_existing = existing_data.get("papers", [])
    all_existing.extend(enriched)

    # Sort by date and keep most recent 500
    all_existing.sort(key=lambda p: p.get("date", ""), reverse=True)
    all_existing = all_existing[:500]

    # Save
    output = {
        "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
        "total": len(all_existing),
        "papers": all_existing,
    }

    save_papers(output)

    print(f"✅ Done! Added {len(enriched)} papers.")
    print(f"   Total papers in database: {len(all_existing)}")
    print(f"\n💡 Don't forget to commit and push:")
    print(f"   git add public/papers.json")
    print(f"   git commit -m 'chore: backfill ACL papers {START_YEAR}-{END_YEAR}'")
    print(f"   git push")


if __name__ == "__main__":
    main()

# Made with Bob

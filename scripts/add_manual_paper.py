#!/usr/bin/env python3
"""
Manual Paper Addition Tool
Add papers you find interesting directly to papers.json
"""

import os
import json
import datetime
import sys

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "public", "papers.json")

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

VALID_CATEGORIES = ["RAG", "Embedding Models", "LLM Pretraining", "Other"]


def load_existing():
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH) as f:
            return json.load(f)
    return {"papers": [], "last_updated": ""}


def save_papers(data):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(data, f, indent=2)


def add_paper_interactive():
    """Interactive mode - prompts for paper details"""
    print("=== Add Manual Paper ===\n")

    # Get paper details
    title = input("Paper title: ").strip()
    if not title:
        print("❌ Title is required")
        return False

    url = input("Paper URL (arXiv/ACL/etc): ").strip()
    if not url:
        print("❌ URL is required")
        return False

    # Extract source and ID from URL
    source = "Manual"
    paper_id = f"manual-{hash(url) % 100000}"

    if "arxiv.org" in url:
        source = "arXiv"
        arxiv_id = url.split("/")[-1].replace(".pdf", "")
        paper_id = f"arxiv-{arxiv_id}"
    elif "aclanthology.org" in url:
        source = "ACL Anthology"
        acl_id = url.rstrip("/").split("/")[-1]
        paper_id = f"acl-{acl_id}"
    elif "openreview.net" in url:
        source = "ICLR"
        if "id=" in url:
            iclr_id = url.split("id=")[-1].split("&")[0]
            paper_id = f"iclr-{iclr_id}"

    abstract = input("Abstract (optional, press Enter to skip): ").strip()

    authors_input = input("Authors (comma-separated, optional): ").strip()
    authors = [a.strip() for a in authors_input.split(",")] if authors_input else []

    notion_url = input("Notion notes URL (optional): ").strip()
    github_url = input("GitHub summary URL (optional): ").strip()

    # Category
    print(f"\nCategory (choose number):")
    for i, cat in enumerate(VALID_CATEGORIES, 1):
        print(f"  {i}. {cat}")
    cat_choice = input("Choice [1-4]: ").strip()
    try:
        category = VALID_CATEGORIES[int(cat_choice) - 1]
    except (ValueError, IndexError):
        category = "Other"

    # Tags
    print(f"\nAvailable tags:")
    for i, tag in enumerate(VALID_TAGS, 1):
        print(f"  {i:2d}. {tag}")
    tags_input = input("Select tags (comma-separated numbers, e.g., 1,2,5): ").strip()
    tags = []
    if tags_input:
        try:
            tag_indices = [int(x.strip()) - 1 for x in tags_input.split(",")]
            tags = [VALID_TAGS[i] for i in tag_indices if 0 <= i < len(VALID_TAGS)]
        except (ValueError, IndexError):
            print("⚠ Invalid tag selection, skipping tags")

    summary = input("\nSummary (2-3 sentences, optional): ").strip()

    venue = input("Venue (optional, e.g., ACL 2024): ").strip()

    # Create paper object
    paper = {
        "id": paper_id,
        "title": title,
        "abstract": abstract or summary[:1000],
        "authors": authors[:4],
        "date": datetime.date.today().isoformat(),
        "url": url,
        "source": source,
        "category": category,
        "tags": tags,
        "summary": summary or abstract[:300],
    }

    if venue:
        paper["venue"] = venue

    if notion_url:
        paper["notion_url"] = notion_url

    if github_url:
        paper["github_url"] = github_url

    # Load existing and add
    data = load_existing()

    # Check for duplicates
    existing_ids = {p["id"] for p in data.get("papers", [])}
    if paper_id in existing_ids:
        print(f"\n⚠ Paper with ID '{paper_id}' already exists!")
        overwrite = input("Overwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            print("❌ Cancelled")
            return False
        # Remove old version
        data["papers"] = [p for p in data["papers"] if p["id"] != paper_id]

    data["papers"].insert(0, paper)  # Add at the beginning
    data["last_updated"] = datetime.datetime.utcnow().isoformat() + "Z"
    data["total"] = len(data["papers"])

    # Keep only 500 most recent
    data["papers"] = data["papers"][:500]

    save_papers(data)

    print(f"\n✅ Paper added successfully!")
    print(f"   ID: {paper_id}")
    print(f"   Source: {source}")
    print(f"   Category: {category}")
    print(f"   Tags: {', '.join(tags) if tags else 'None'}")

    return True


def add_paper_from_args(
    title,
    url,
    tags=None,
    category="Other",
    summary="",
    authors=None,
    notion_url=None,
    github_url=None,
):
    """Programmatic mode - add paper from command line args"""

    # Extract source and ID from URL
    source = "Manual"
    paper_id = f"manual-{hash(url) % 100000}"

    if "arxiv.org" in url:
        source = "arXiv"
        arxiv_id = url.split("/")[-1].replace(".pdf", "")
        paper_id = f"arxiv-{arxiv_id}"
    elif "aclanthology.org" in url:
        source = "ACL Anthology"
        acl_id = url.rstrip("/").split("/")[-1]
        paper_id = f"acl-{acl_id}"
    elif "openreview.net" in url:
        source = "ICLR"
        if "id=" in url:
            iclr_id = url.split("id=")[-1].split("&")[0]
            paper_id = f"iclr-{iclr_id}"

    paper = {
        "id": paper_id,
        "title": title,
        "abstract": summary[:1000] if summary else "",
        "authors": authors[:4] if authors else [],
        "date": datetime.date.today().isoformat(),
        "url": url,
        "source": source,
        "category": category if category in VALID_CATEGORIES else "Other",
        "tags": [t for t in (tags or []) if t in VALID_TAGS],
        "summary": summary or "",
    }

    if notion_url:
        paper["notion_url"] = notion_url

    if github_url:
        paper["github_url"] = github_url

    data = load_existing()

    # Check for duplicates
    existing_ids = {p["id"] for p in data.get("papers", [])}
    if paper_id in existing_ids:
        print(f"⚠ Paper '{paper_id}' already exists, skipping")
        return False

    data["papers"].insert(0, paper)
    data["last_updated"] = datetime.datetime.utcnow().isoformat() + "Z"
    data["total"] = len(data["papers"])
    data["papers"] = data["papers"][:500]

    save_papers(data)
    print(f"✅ Added: {title}")
    return True


def main():
    if len(sys.argv) == 1:
        # Interactive mode
        add_paper_interactive()
    elif len(sys.argv) >= 3:
        # Command line mode
        # Usage: python add_manual_paper.py "Title" "URL" ["tag1,tag2"] ["category"] ["summary"]
        title = sys.argv[1]
        url = sys.argv[2]
        tags = sys.argv[3].split(",") if len(sys.argv) > 3 else []
        category = sys.argv[4] if len(sys.argv) > 4 else "Other"
        summary = sys.argv[5] if len(sys.argv) > 5 else ""

        add_paper_from_args(title, url, tags, category, summary)
    else:
        print("Usage:")
        print("  Interactive: python scripts/add_manual_paper.py")
        print(
            '  CLI: python scripts/add_manual_paper.py "Title" "URL" "tag1,tag2" "category" "summary"'
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob

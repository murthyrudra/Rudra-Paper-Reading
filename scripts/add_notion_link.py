#!/usr/bin/env python3
"""
Add Notion link to an existing paper in papers.json
Usage: python scripts/add_notion_link.py
"""

import os
import json
import datetime

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "public", "papers.json")


def load_papers():
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH) as f:
            return json.load(f)
    return {"papers": [], "last_updated": ""}


def save_papers(data):
    with open(OUTPUT_PATH, "w") as f:
        json.dump(data, f, indent=2)


def search_papers(query):
    """Search papers by title or ID"""
    data = load_papers()
    query_lower = query.lower()
    matches = []

    for paper in data.get("papers", []):
        if (
            query_lower in paper.get("title", "").lower()
            or query_lower in paper.get("id", "").lower()
        ):
            matches.append(paper)

    return matches


def main():
    print("=== Add Notion Link to Paper ===\n")

    # Search for paper
    search_query = input("Search for paper (title or ID): ").strip()
    if not search_query:
        print("❌ Search query required")
        return

    matches = search_papers(search_query)

    if not matches:
        print(f"❌ No papers found matching '{search_query}'")
        return

    if len(matches) == 1:
        paper = matches[0]
        print(f"\n✓ Found: {paper['title']}")
    else:
        print(f"\n✓ Found {len(matches)} papers:\n")
        for i, p in enumerate(matches, 1):
            notion_status = "📝" if p.get("notion_url") else "  "
            print(f"  {i}. {notion_status} {p['title'][:70]}")
            print(f"     [{p['source']}] {p['date']}")

        choice = input(f"\nSelect paper (1-{len(matches)}): ").strip()
        try:
            paper = matches[int(choice) - 1]
        except (ValueError, IndexError):
            print("❌ Invalid selection")
            return

    # Show current Notion link if exists
    if paper.get("notion_url"):
        print(f"\n⚠ Paper already has a Notion link:")
        print(f"   {paper['notion_url']}")
        overwrite = input("\nOverwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            print("❌ Cancelled")
            return

    # Get new Notion URL
    notion_url = input("\nNotion page URL: ").strip()
    if not notion_url:
        print("❌ URL required")
        return

    # Validate it's a Notion URL
    if "notion.so" not in notion_url and "notion.site" not in notion_url:
        print("⚠ Warning: This doesn't look like a Notion URL")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != "y":
            print("❌ Cancelled")
            return

    # Update paper
    data = load_papers()
    for p in data["papers"]:
        if p["id"] == paper["id"]:
            p["notion_url"] = notion_url
            break

    data["last_updated"] = datetime.datetime.utcnow().isoformat() + "Z"
    save_papers(data)

    print(f"\n✅ Notion link added successfully!")
    print(f"   Paper: {paper['title'][:60]}...")
    print(f"   Link: {notion_url}")
    print(f"\n💡 Don't forget to commit and push:")
    print(f"   git add public/papers.json")
    print(f"   git commit -m 'chore: add notion link'")
    print(f"   git push")


if __name__ == "__main__":
    main()

# Made with Bob

#!/usr/bin/env python3
"""
Add GitHub summary link to an existing paper in papers.json
Links to markdown files in papers_git_summary/
"""

import os
import json
import datetime
import glob

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "public", "papers.json")
SUMMARIES_DIR = os.path.join(os.path.dirname(__file__), "..", "papers_git_summary")


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


def list_summary_files():
    """List all markdown files in papers_git_summary/"""
    pattern = os.path.join(SUMMARIES_DIR, "*.md")
    files = glob.glob(pattern)
    # Exclude .gitkeep
    files = [f for f in files if not f.endswith(".gitkeep")]
    return sorted(files)


def main():
    print("=== Add GitHub Summary Link to Paper ===\n")

    # Option 1: Search for paper
    print("Option 1: Search for paper by title/ID")
    print("Option 2: List all summary files and select\n")

    choice = input("Choose option (1/2): ").strip()

    if choice == "2":
        # List summary files
        summary_files = list_summary_files()
        if not summary_files:
            print("❌ No summary files found in papers_git_summary/")
            print("   Create one with: python scripts/generate_paper_summary.py")
            return

        print(f"\n✓ Found {len(summary_files)} summary files:\n")
        for i, filepath in enumerate(summary_files, 1):
            filename = os.path.basename(filepath)
            print(f"  {i}. {filename}")

        file_choice = input(f"\nSelect file (1-{len(summary_files)}): ").strip()
        try:
            selected_file = summary_files[int(file_choice) - 1]
            filename = os.path.basename(selected_file)

            # Try to match paper by filename
            # Extract title from filename (remove year and .md)
            title_part = filename[5:-3] if filename[4] == "-" else filename[:-3]
            title_part = title_part.replace("-", " ")

            print(f"\nSearching for papers matching: '{title_part}'")
            matches = search_papers(title_part)

            if not matches:
                print(f"❌ No papers found. Enter paper title manually:")
                search_query = input("Paper title: ").strip()
                matches = search_papers(search_query)

                if not matches:
                    print("❌ Still no matches found")
                    return

        except (ValueError, IndexError):
            print("❌ Invalid selection")
            return
    else:
        # Search for paper
        search_query = input("Search for paper (title or ID): ").strip()
        if not search_query:
            print("❌ Search query required")
            return

        matches = search_papers(search_query)

        if not matches:
            print(f"❌ No papers found matching '{search_query}'")
            return

        selected_file = None

    # Select paper if multiple matches
    if len(matches) == 1:
        paper = matches[0]
        print(f"\n✓ Found: {paper['title']}")
    else:
        print(f"\n✓ Found {len(matches)} papers:\n")
        for i, p in enumerate(matches, 1):
            github_status = "📝" if p.get("github_url") else "  "
            notion_status = "📔" if p.get("notion_url") else "  "
            print(f"  {i}. {github_status}{notion_status} {p['title'][:70]}")
            print(f"     [{p['source']}] {p['date']}")

        paper_choice = input(f"\nSelect paper (1-{len(matches)}): ").strip()
        try:
            paper = matches[int(paper_choice) - 1]
        except (ValueError, IndexError):
            print("❌ Invalid selection")
            return

    # Show current links
    if paper.get("github_url"):
        print(f"\n⚠ Paper already has a GitHub link:")
        print(f"   {paper['github_url']}")
        overwrite = input("\nOverwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            print("❌ Cancelled")
            return

    # Get GitHub URL
    if selected_file:
        # Auto-generate GitHub URL from file
        filename = os.path.basename(selected_file)
        # Assuming repo is on GitHub
        github_url = f"https://github.com/YOUR_USERNAME/research-radar/blob/main/papers_git_summary/{filename}"
        print(f"\n📝 Auto-generated GitHub URL:")
        print(f"   {github_url}")
        print(f"\n⚠ Update YOUR_USERNAME in the URL above")
        use_auto = input("Use this URL? (y/n): ").strip().lower()
        if use_auto != "y":
            github_url = input("\nEnter GitHub URL manually: ").strip()
    else:
        print("\n📝 Enter the GitHub URL for your summary:")
        print(
            "   Example: https://github.com/username/research-radar/blob/main/papers_git_summary/2024-paper-title.md"
        )
        github_url = input("GitHub URL: ").strip()

    if not github_url:
        print("❌ URL required")
        return

    # Update paper
    data = load_papers()
    for p in data["papers"]:
        if p["id"] == paper["id"]:
            p["github_url"] = github_url
            break

    data["last_updated"] = datetime.datetime.utcnow().isoformat() + "Z"
    save_papers(data)

    print(f"\n✅ GitHub link added successfully!")
    print(f"   Paper: {paper['title'][:60]}...")
    print(f"   Link: {github_url}")
    print(f"\n💡 Don't forget to commit and push:")
    print(f"   git add public/papers.json")
    print(f"   git commit -m 'chore: add github summary link'")
    print(f"   git push")


if __name__ == "__main__":
    main()

# Made with Bob

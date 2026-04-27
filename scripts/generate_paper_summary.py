#!/usr/bin/env python3
"""
Generate a GitHub markdown template for a paper summary
Creates a structured markdown file in papers_git_summary/
"""

import os
import json
import re
import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "papers_git_summary")
PAPERS_JSON = os.path.join(os.path.dirname(__file__), "..", "public", "papers.json")


def load_papers():
    if os.path.exists(PAPERS_JSON):
        with open(PAPERS_JSON) as f:
            return json.load(f)
    return {"papers": []}


def slugify(text):
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text[:60]


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


def generate_markdown_template(paper):
    """Generate a markdown template for the paper"""

    title = paper.get("title", "Untitled")
    authors = paper.get("authors", [])
    date = paper.get("date", "")
    url = paper.get("url", "")
    abstract = paper.get("abstract", "")
    venue = paper.get("venue", paper.get("source", ""))
    tags = paper.get("tags", [])
    category = paper.get("category", "")

    # Create filename
    year = date[:4] if date else datetime.date.today().year
    slug = slugify(title)
    filename = f"{year}-{slug}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # Generate markdown content
    markdown = f"""# {title}

**Authors:** {', '.join(authors) if authors else 'N/A'}  
**Venue:** {venue}  
**Year:** {year}  
**Paper:** [{url}]({url})  
**Category:** {category}  
**Tags:** {', '.join(f'`{t}`' for t in tags)}

---

## 📄 Abstract

{abstract}

---

## 🎯 Key Contributions

<!-- What are the main contributions of this paper? -->

1. 
2. 
3. 

---

## 🔍 Methodology

<!-- How did they approach the problem? -->

### Architecture/Approach


### Key Techniques


---

## 📊 Results

<!-- What were the main findings? -->

### Main Results


### Comparisons


---

## 💡 Key Insights

<!-- What did you learn? What stood out? -->

- 
- 
- 

---

## 🤔 Critical Analysis

### Strengths

- 

### Weaknesses

- 

### Questions/Future Work

- 

---

## 🔗 Related Work

<!-- Papers cited or related to this work -->

- 
- 

---

## 📝 Personal Notes

<!-- Your thoughts, ideas, potential applications -->



---

## 🏷️ Tags for Reference

{', '.join(f'#{t.lower().replace(" ", "-")}' for t in tags)}

---

**Date Read:** {datetime.date.today().isoformat()}  
**Status:** 📖 In Progress / ✅ Completed / 🔄 Revisit
"""

    return filepath, markdown


def main():
    print("=== Generate Paper Summary Template ===\n")

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
            github_status = "📝" if p.get("github_url") else "  "
            notion_status = "📔" if p.get("notion_url") else "  "
            print(f"  {i}. {github_status}{notion_status} {p['title'][:70]}")
            print(f"     [{p['source']}] {p['date']}")

        choice = input(f"\nSelect paper (1-{len(matches)}): ").strip()
        try:
            paper = matches[int(choice) - 1]
        except (ValueError, IndexError):
            print("❌ Invalid selection")
            return

    # Generate template
    filepath, markdown = generate_markdown_template(paper)

    # Check if file exists
    if os.path.exists(filepath):
        print(f"\n⚠ File already exists: {os.path.basename(filepath)}")
        overwrite = input("Overwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            print("❌ Cancelled")
            return

    # Write file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(filepath, "w") as f:
        f.write(markdown)

    print(f"\n✅ Template created!")
    print(f"   File: {filepath}")
    print(f"\n📝 Next steps:")
    print(f"   1. Edit the file and fill in your notes")
    print(f"   2. Commit to git:")
    print(f"      git add {filepath}")
    print(f"      git commit -m 'docs: add summary for {paper['title'][:40]}'")
    print(f"   3. Link it to the paper:")
    print(f"      python scripts/add_github_link.py")


if __name__ == "__main__":
    main()

# Made with Bob

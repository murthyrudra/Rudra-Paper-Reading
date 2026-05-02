#!/usr/bin/env python3

import json
import sys
import re


def format_author(a):
    """
    Convert ACL NameSpecification object (string form) → clean name
    Works even if already a string.
    """
    if isinstance(a, dict):
        # In case already serialized differently
        first = a.get("first", "")
        last = a.get("last", "")
        return " ".join([first, last]).strip()

    if isinstance(a, str):
        # Try to extract from string repr
        import re

        match = re.search(r"first='([^']*)'.*last='([^']*)'", a)
        if match:
            return f"{match.group(1)} {match.group(2)}".strip()

        return a  # fallback

    return str(a)


def normalize_title(title):
    """
    Normalize title for deduplication:
    - lowercase
    - remove punctuation
    - collapse whitespace
    """
    if not title:
        return ""

    title = title.lower()
    title = re.sub(r"[^\w\s]", "", title)  # remove punctuation
    title = re.sub(r"\s+", " ", title).strip()
    return title


def clean_papers(input_path, output_path=None):
    with open(input_path, "r") as f:
        data = json.load(f)

    papers = data.get("papers", [])
    original_count = len(papers)

    cleaned = []
    seen_titles = set()
    duplicate_count = 0
    removed_no_tags = 0

    for p in papers:
        # ── filter: must have tags ──
        tags = p.get("tags")
        if not tags or not isinstance(tags, list) or len(tags) == 0:
            removed_no_tags += 1
            continue

        # ── fix authors ──
        if "authors" in p and isinstance(p["authors"], list):
            p["authors"] = [format_author(a) for a in p["authors"]]

        # ── deduplication using title ──
        norm_title = normalize_title(p.get("title", ""))

        if norm_title in seen_titles:
            duplicate_count += 1
            continue

        seen_titles.add(norm_title)
        cleaned.append(p)

    data["papers"] = cleaned

    if output_path is None:
        output_path = input_path

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Original papers: {original_count}")
    print(f"Removed (no tags): {removed_no_tags}")
    print(f"Duplicates removed (by title): {duplicate_count}")
    print(f"Remaining: {len(cleaned)}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_papers.py <input_json> [output_json]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    clean_papers(input_file, output_file)

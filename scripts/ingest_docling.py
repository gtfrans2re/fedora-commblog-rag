"""
ingest_docling.py

Processes raw articles from both Fedora Community Blog and Fedora Magazine
using Docling, converting HTML into structured Markdown for the RamaLama
RAG pipeline.

Usage:
    python scripts/ingest_docling.py              # ingest both
    python scripts/ingest_docling.py --source commblog
    python scripts/ingest_docling.py --source magazine

Input:
    - data/raw/commblog/<slug>.json
    - data/raw/magazine/<slug>.json

Output:
    - data/cleaned/commblog/<slug>.md
    - data/cleaned/magazine/<slug>.md
"""

import json
import argparse
import tempfile
import os
from pathlib import Path
from tqdm import tqdm
from docling.document_converter import DocumentConverter

# ── Config ────────────────────────────────────────────────────────────────────

SOURCES = {
    "commblog": {
        "raw_dir":     Path("data/raw/commblog"),
        "cleaned_dir": Path("data/cleaned/commblog"),
        "label":       "Fedora Community Blog",
    },
    "magazine": {
        "raw_dir":     Path("data/raw/magazine"),
        "cleaned_dir": Path("data/cleaned/magazine"),
        "label":       "Fedora Magazine",
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_raw_article(filepath: Path) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_html_content(article: dict) -> str:
    return article.get("content", {}).get("rendered", "")


def extract_metadata(article: dict, source: str) -> dict:
    return {
        "id":       article.get("id"),
        "slug":     article.get("slug"),
        "title":    article.get("title", {}).get("rendered", ""),
        "date":     article.get("date"),
        "modified": article.get("modified"),
        "link":     article.get("link"),
        "source":   source,
        "excerpt":  article.get("excerpt", {}).get("rendered", ""),
    }


def html_to_markdown_via_docling(html_content: str) -> str:
    converter = DocumentConverter()
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(html_content)
        tmp_path = tmp.name
    try:
        result   = converter.convert(tmp_path)
        markdown = result.document.export_to_markdown()
    finally:
        os.unlink(tmp_path)
    return markdown


def build_document(metadata: dict, markdown_content: str) -> str:
    source_label = {
        "commblog": "Fedora Community Blog",
        "magazine":  "Fedora Magazine",
    }.get(metadata.get("source", ""), metadata.get("source", ""))

    frontmatter = (
        f"---\n"
        f"id: {metadata['id']}\n"
        f"slug: {metadata['slug']}\n"
        f"title: \"{metadata['title']}\"\n"
        f"date: {metadata['date']}\n"
        f"modified: {metadata['modified']}\n"
        f"link: {metadata['link']}\n"
        f"source: {source_label}\n"
        f"---\n\n"
    )

    excerpt_block = ""
    if metadata.get("excerpt"):
        from html2text import html2text
        clean_excerpt = html2text(metadata["excerpt"]).strip()
        if clean_excerpt:
            excerpt_block = f"> {clean_excerpt}\n\n"

    return frontmatter + excerpt_block + markdown_content


def save_cleaned(content: str, slug: str, output_dir: Path) -> None:
    filepath = output_dir / f"{slug}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


# ── Ingest one source ─────────────────────────────────────────────────────────

def ingest_source(source_key: str) -> None:
    source      = SOURCES[source_key]
    raw_dir     = source["raw_dir"]
    cleaned_dir = source["cleaned_dir"]
    label       = source["label"]

    cleaned_dir.mkdir(parents=True, exist_ok=True)

    raw_files = [
        f for f in raw_dir.glob("*.json")
        if f.name != "index.json"
    ]

    if not raw_files:
        print(f"\n  No raw articles in {raw_dir}/. Run fetch_articles.py first.")
        return

    print(f"\n{'='*55}")
    print(f"  Ingesting: {label} ({len(raw_files)} articles)")
    print(f"{'='*55}")

    success, failed = 0, []

    for filepath in tqdm(raw_files, desc="  Ingesting"):
        try:
            article  = load_raw_article(filepath)
            metadata = extract_metadata(article, source_key)
            html     = extract_html_content(article)

            if not html.strip():
                continue

            markdown = html_to_markdown_via_docling(html)
            document = build_document(metadata, markdown)
            save_cleaned(document, metadata["slug"], cleaned_dir)
            success += 1
        except Exception as e:
            print(f"\n  Failed: {filepath.name}: {e}")
            failed.append(filepath.name)

    print(f"\n  Done: {success} succeeded, {len(failed)} failed.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Ingest articles from CommBlog and/or Magazine with Docling."
    )
    parser.add_argument(
        "--source",
        choices=["commblog", "magazine", "both"],
        default="both",
    )
    args = parser.parse_args()

    if args.source == "both":
        ingest_source("commblog")
        ingest_source("magazine")
    else:
        ingest_source(args.source)

    print("\nAll ingestion complete.")


if __name__ == "__main__":
    main()
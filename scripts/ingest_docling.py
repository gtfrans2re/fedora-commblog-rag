"""
ingest_docling.py

Processes raw articles fetched from the WordPress REST API using Docling,
converting them into structured, clean documents ready for the RamaLama
RAG pipeline.

Usage:
    python scripts/ingest_docling.py

Input:
    - data/raw/<slug>.json

Output:
    - data/cleaned/<slug>.md   : Markdown version of each article
"""

import json
from pathlib import Path
from tqdm import tqdm
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import PdfFormatOption
import tempfile
import os

# ── Config ────────────────────────────────────────────────────────────────────

RAW_DIR     = Path("data/raw")
CLEANED_DIR = Path("data/cleaned")
SKIP_INDEX  = True   # Skip index.json when processing

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_raw_article(filepath: Path) -> dict:
    """Load a raw article JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_html_content(article: dict) -> str:
    """Extract the rendered HTML content from a WordPress article."""
    return article.get("content", {}).get("rendered", "")


def extract_metadata(article: dict) -> dict:
    """Extract useful metadata from the article."""
    return {
        "id":       article.get("id"),
        "slug":     article.get("slug"),
        "title":    article.get("title", {}).get("rendered", ""),
        "date":     article.get("date"),
        "modified": article.get("modified"),
        "link":     article.get("link"),
        "excerpt":  article.get("excerpt", {}).get("rendered", ""),
    }


def html_to_markdown_via_docling(html_content: str) -> str:
    """
    Convert raw HTML content to Markdown using Docling.
    Writes HTML to a temp file, then converts with DocumentConverter.
    """
    converter = DocumentConverter()

    # Write HTML to a temporary file for Docling to process
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(html_content)
        tmp_path = tmp.name

    try:
        result = converter.convert(tmp_path)
        markdown = result.document.export_to_markdown()
    finally:
        os.unlink(tmp_path)  # Clean up temp file

    return markdown


def build_document(metadata: dict, markdown_content: str) -> str:
    """
    Assemble the final document with a YAML-style frontmatter header
    followed by the article content in Markdown.
    """
    frontmatter = (
        f"---\n"
        f"id: {metadata['id']}\n"
        f"slug: {metadata['slug']}\n"
        f"title: \"{metadata['title']}\"\n"
        f"date: {metadata['date']}\n"
        f"modified: {metadata['modified']}\n"
        f"link: {metadata['link']}\n"
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
    """Save the cleaned Markdown document."""
    filepath = output_dir / f"{slug}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    raw_files = [
        f for f in RAW_DIR.glob("*.json")
        if f.name != "index.json"
    ]

    if not raw_files:
        print(f" No raw articles found in {RAW_DIR}/. Run fetch_articles.py first.")
        return

    print(f"📂 Found {len(raw_files)} raw articles to process.")
    success, failed = 0, []

    for filepath in tqdm(raw_files, desc="Ingesting with Docling"):
        try:
            article  = load_raw_article(filepath)
            metadata = extract_metadata(article)
            html     = extract_html_content(article)

            if not html.strip():
                print(f"\n  Skipping empty article: {metadata['slug']}")
                continue

            markdown = html_to_markdown_via_docling(html)
            document = build_document(metadata, markdown)
            save_cleaned(document, metadata["slug"], CLEANED_DIR)
            success += 1

        except Exception as e:
            print(f"\n Failed to process {filepath.name}: {e}")
            failed.append(filepath.name)

    print(f"\n Ingestion complete: {success} succeeded, {len(failed)} failed.")
    if failed:
        print(f"   Failed files: {', '.join(failed)}")


if __name__ == "__main__":
    main()
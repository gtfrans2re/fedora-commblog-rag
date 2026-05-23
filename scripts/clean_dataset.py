"""
clean_dataset.py

Cleans and prepares the Docling-processed Markdown articles for ingestion
into the RamaLama RAG pipeline.

Cleaning steps:
    1. Strip residual HTML tags
    2. Normalize whitespace and line breaks
    3. Remove boilerplate footer/navigation text
    4. Validate required fields (title, date, content)
    5. Flag articles missing key editorial elements (featured image, --more-- tag)
    6. Save cleaned files and a quality report

Usage:
    python scripts/clean_dataset.py

Input:
    - data/cleaned/<slug>.md

Output:
    - data/cleaned/<slug>.md        : Cleaned in-place
    - data/cleaned/quality_report.json : Per-article quality flags
"""

import re
import json
from pathlib import Path
from tqdm import tqdm

# ── Config ────────────────────────────────────────────────────────────────────

CLEANED_DIR = Path("data/cleaned")

# Patterns to strip from content
BOILERPLATE_PATTERNS = [
    r"(?i)share this:.*$",
    r"(?i)like this:.*$",
    r"(?i)related posts.*$",
    r"(?i)filed under.*$",
    r"(?i)tagged with.*$",
    r"(?i)^posted in.*$",
    r"(?i)leave a (comment|reply).*$",
]

# Editorial quality checks
QUALITY_CHECKS = {
    "has_featured_image": r"!\[.*?\]\(.*?\)",       # Markdown image syntax
    "has_more_tag":       r"<!--more-->",            # WordPress <!--more--> tag
    "has_headings":       r"^#{1,3} .+",             # H1–H3 headings
    "has_min_length":     None,                      # Handled separately
    "has_title":          None,                      # Handled via frontmatter
}

MIN_CONTENT_LENGTH = 300   # Characters — below this is likely a stub

# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Split YAML frontmatter from body content.
    Returns (metadata dict, body string).
    """
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_raw = parts[1].strip()
    body = parts[2].strip()

    metadata = {}
    for line in frontmatter_raw.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip().strip('"')

    return metadata, body


def strip_html_tags(text: str) -> str:
    """Remove any residual HTML tags."""
    return re.sub(r"<[^>]+>", "", text)


def normalize_whitespace(text: str) -> str:
    """Collapse excessive blank lines (max 2 consecutive)."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def remove_boilerplate(text: str) -> str:
    """Strip known boilerplate patterns from article body."""
    for pattern in BOILERPLATE_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.MULTILINE)
    return text


def run_quality_checks(metadata: dict, body: str) -> dict:
    """
    Run editorial quality checks on a cleaned article.
    Returns a dict of check_name → bool.
    """
    results = {}

    for check, pattern in QUALITY_CHECKS.items():
        if pattern is None:
            continue
        results[check] = bool(re.search(pattern, body, re.MULTILINE))

    # Manual checks
    results["has_min_length"] = len(body) >= MIN_CONTENT_LENGTH
    results["has_title"]      = bool(metadata.get("title", "").strip())
    results["has_date"]       = bool(metadata.get("date", "").strip())

    # Overall pass/fail
    results["passed"] = all(results.values())

    return results


def clean_article(content: str) -> tuple[dict, str, dict]:
    """
    Full cleaning pipeline for a single article.
    Returns (metadata, cleaned_body, quality_report).
    """
    metadata, body = parse_frontmatter(content)
    body = strip_html_tags(body)
    body = remove_boilerplate(body)
    body = normalize_whitespace(body)
    quality = run_quality_checks(metadata, body)
    return metadata, body, quality


def rebuild_document(metadata: dict, body: str) -> str:
    """Reconstruct the full Markdown document with frontmatter."""
    fm_lines = "\n".join(f"{k}: {v}" for k, v in metadata.items())
    return f"---\n{fm_lines}\n---\n\n{body}"


def save_report(report: list[dict], output_dir: Path) -> None:
    """Save the quality report as JSON."""
    filepath = output_dir / "quality_report.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n Quality report saved → {filepath}")


def print_summary(report: list[dict]) -> None:
    """Print a human-readable summary of the quality report."""
    total   = len(report)
    passed  = sum(1 for r in report if r["quality"].get("passed"))
    failed  = total - passed

    print(f"\n{'─'*50}")
    print(f"  Dataset Quality Summary")
    print(f"{'─'*50}")
    print(f"  Total articles  : {total}")
    print(f"  Passed          : {passed}")
    print(f"  Failed          : {failed}")
    print(f"{'─'*50}")

    if failed:
        print("\n  Articles with issues:")
        for entry in report:
            if not entry["quality"].get("passed"):
                issues = [k for k, v in entry["quality"].items()
                          if not v and k != "passed"]
                print(f"    • {entry['slug']}: {', '.join(issues)}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    md_files = [
        f for f in CLEANED_DIR.glob("*.md")
    ]

    if not md_files:
        print(f" No cleaned articles found in {CLEANED_DIR}/. Run ingest_docling.py first.")
        return

    print(f" Cleaning {len(md_files)} articles...")
    report = []

    for filepath in tqdm(md_files, desc="Cleaning articles"):
        try:
            raw_content = filepath.read_text(encoding="utf-8")
            metadata, body, quality = clean_article(raw_content)

            # Save cleaned file in-place
            cleaned_content = rebuild_document(metadata, body)
            filepath.write_text(cleaned_content, encoding="utf-8")

            report.append({
                "slug":    metadata.get("slug", filepath.stem),
                "title":   metadata.get("title", ""),
                "quality": quality,
            })

        except Exception as e:
            print(f"\n Failed to clean {filepath.name}: {e}")

    save_report(report, CLEANED_DIR)
    print_summary(report)
    print(f"\n Cleaning complete.")


if __name__ == "__main__":
    main()
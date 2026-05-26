"""
clean_dataset.py

Cleans and quality-checks cleaned Markdown articles from both
Fedora Community Blog and Fedora Magazine.

Usage:
    python scripts/clean_dataset.py              # clean both
    python scripts/clean_dataset.py --source commblog
    python scripts/clean_dataset.py --source magazine

Input / Output:
    - data/cleaned/commblog/<slug>.md  (cleaned in-place)
    - data/cleaned/magazine/<slug>.md  (cleaned in-place)
    - data/cleaned/commblog/quality_report.json
    - data/cleaned/magazine/quality_report.json
"""

import re
import json
import argparse
from pathlib import Path
from tqdm import tqdm

# ── Config ────────────────────────────────────────────────────────────────────

SOURCES = {
    "commblog": Path("data/cleaned/commblog"),
    "magazine":  Path("data/cleaned/magazine"),
}

BOILERPLATE_PATTERNS = [
    r"(?i)share this:.*$",
    r"(?i)like this:.*$",
    r"(?i)related posts.*$",
    r"(?i)filed under.*$",
    r"(?i)tagged with.*$",
    r"(?i)^posted in.*$",
    r"(?i)leave a (comment|reply).*$",
]

QUALITY_CHECKS = {
    "has_featured_image": r"!\[.*?\]\(.*?\)",
    "has_more_tag":       r"<!--more-->",
    "has_headings":       r"^#{1,3} .+",
    "has_min_length":     None,
    "has_title":          None,
}

MIN_CONTENT_LENGTH = 300

# ── Helpers (same as before) ──────────────────────────────────────────────────

def parse_frontmatter(content: str) -> tuple[dict, str]:
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    metadata = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip().strip('"')
    return metadata, parts[2].strip()


def strip_html_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def remove_boilerplate(text: str) -> str:
    for pattern in BOILERPLATE_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.MULTILINE)
    return text


def run_quality_checks(metadata: dict, body: str) -> dict:
    results = {}
    for check, pattern in QUALITY_CHECKS.items():
        if pattern is None:
            continue
        results[check] = bool(re.search(pattern, body, re.MULTILINE))
    results["has_min_length"] = len(body) >= MIN_CONTENT_LENGTH
    results["has_title"]      = bool(metadata.get("title", "").strip())
    results["has_date"]       = bool(metadata.get("date", "").strip())
    results["passed"]         = all(results.values())
    return results


def clean_article(content: str) -> tuple[dict, str, dict]:
    metadata, body = parse_frontmatter(content)
    body    = strip_html_tags(body)
    body    = remove_boilerplate(body)
    body    = normalize_whitespace(body)
    quality = run_quality_checks(metadata, body)
    return metadata, body, quality


def rebuild_document(metadata: dict, body: str) -> str:
    fm_lines = "\n".join(f"{k}: {v}" for k, v in metadata.items())
    return f"---\n{fm_lines}\n---\n\n{body}"


def print_summary(report: list[dict], label: str) -> None:
    total  = len(report)
    passed = sum(1 for r in report if r["quality"].get("passed"))
    failed = total - passed
    print(f"\n  {label}")
    print(f"  {'─'*40}")
    print(f"  Total   : {total}")
    print(f"  Passed  : {passed}")
    print(f"  Failed  : {failed}")
    if failed:
        print(f"\n  Articles with issues:")
        for entry in report:
            if not entry["quality"].get("passed"):
                issues = [k for k, v in entry["quality"].items()
                          if not v and k != "passed"]
                print(f"    - {entry['slug']}: {', '.join(issues)}")


# ── Clean one source ──────────────────────────────────────────────────────────

def clean_source(source_key: str) -> None:
    cleaned_dir = SOURCES[source_key]
    md_files    = [f for f in cleaned_dir.glob("*.md")]

    if not md_files:
        print(f"\n  No cleaned articles in {cleaned_dir}/. Run ingest_docling.py first.")
        return

    print(f"\n{'='*55}")
    print(f"  Cleaning: {source_key} ({len(md_files)} articles)")
    print(f"{'='*55}")

    report = []

    for filepath in tqdm(md_files, desc="  Cleaning"):
        try:
            raw_content            = filepath.read_text(encoding="utf-8")
            metadata, body, quality = clean_article(raw_content)
            cleaned_content        = rebuild_document(metadata, body)
            filepath.write_text(cleaned_content, encoding="utf-8")
            report.append({
                "slug":    metadata.get("slug", filepath.stem),
                "title":   metadata.get("title", ""),
                "source":  source_key,
                "quality": quality,
            })
        except Exception as e:
            print(f"\n  Failed: {filepath.name}: {e}")

    report_path = cleaned_dir / "quality_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    label = {"commblog": "Fedora Community Blog", "magazine": "Fedora Magazine"}[source_key]
    print_summary(report, label)
    print(f"\n  Quality report saved -> {report_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Clean and quality-check articles from CommBlog and/or Magazine."
    )
    parser.add_argument(
        "--source",
        choices=["commblog", "magazine", "both"],
        default="both",
    )
    args = parser.parse_args()

    if args.source == "both":
        clean_source("commblog")
        clean_source("magazine")
    else:
        clean_source(args.source)

    print("\nAll cleaning complete.")


if __name__ == "__main__":
    main()
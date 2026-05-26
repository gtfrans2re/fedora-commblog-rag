"""
fetch_articles.py

Fetches all published articles from:
  - Fedora Community Blog  (communityblog.fedoraproject.org)
  - Fedora Magazine        (fedoramagazine.org)

Each source is saved in its own subdirectory under data/raw/.

Usage:
    python scripts/fetch_articles.py              # fetch both
    python scripts/fetch_articles.py --source commblog
    python scripts/fetch_articles.py --source magazine

Output:
    - data/raw/commblog/<slug>.json
    - data/raw/commblog/index.json
    - data/raw/magazine/<slug>.json
    - data/raw/magazine/index.json
"""

import os
import json
import time
import argparse
import requests
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────

load_dotenv()

SOURCES = {
    "commblog": {
        "label":       "Fedora Community Blog",
        "api_base":    os.getenv(
            "WP_COMMBLOG_API_URL",
            "https://communityblog.fedoraproject.org/wp-json/wp/v2"
        ),
        "output_dir":  Path("data/raw/commblog"),
    },
    "magazine": {
        "label":       "Fedora Magazine",
        "api_base":    os.getenv(
            "WP_MAGAZINE_API_URL",
            "https://fedoramagazine.org/wp-json/wp/v2"
        ),
        "output_dir":  Path("data/raw/magazine"),
    },
}

API_KEY       = os.getenv("WP_API_KEY", None)
PER_PAGE      = 100
DELAY_SECONDS = 0.5

# ── Helpers ───────────────────────────────────────────────────────────────────

def build_headers() -> dict:
    headers = {
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "fedora-commblog-rag/1.0 "
            "(https://github.com/gtfrans2re/fedora-commblog-rag)"
        ),
    }
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    return headers


def fetch_total_pages(api_base: str, headers: dict) -> int:
    response = requests.get(
        f"{api_base}/posts",
        headers=headers,
        params={"per_page": PER_PAGE, "page": 1},
        timeout=30,
    )
    response.raise_for_status()
    return int(response.headers.get("X-WP-TotalPages", 1))


def fetch_page(api_base: str, page: int, headers: dict) -> list[dict]:
    params = {
        "per_page": PER_PAGE,
        "page": page,
        "_fields": (
            "id,slug,title,date,modified,link,"
            "content,excerpt,categories,tags,author"
        ),
    }
    response = requests.get(
        f"{api_base}/posts",
        headers=headers,
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def save_article(article: dict, output_dir: Path, source: str) -> None:
    article["_source"] = source
    slug = article.get("slug", str(article["id"]))
    filepath = output_dir / f"{slug}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(article, f, ensure_ascii=False, indent=2)


def save_index(index: list[dict], output_dir: Path) -> None:
    filepath = output_dir / "index.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"\n  Index saved -> {filepath} ({len(index)} articles)")


# ── Fetch one source ──────────────────────────────────────────────────────────

def fetch_source(source_key: str) -> None:
    source     = SOURCES[source_key]
    label      = source["label"]
    api_base   = source["api_base"]
    output_dir = source["output_dir"]

    output_dir.mkdir(parents=True, exist_ok=True)
    headers = build_headers()

    print(f"\n{'='*55}")
    print(f"  Fetching: {label}")
    print(f"  API    : {api_base}")
    print(f"{'='*55}")

    total_pages = fetch_total_pages(api_base, headers)
    print(f"  Total pages: {total_pages}")

    index = []

    for page in tqdm(range(1, total_pages + 1), desc=f"  Pages"):
        try:
            articles = fetch_page(api_base, page, headers)
            for article in articles:
                save_article(article, output_dir, source_key)
                index.append({
                    "id":     article["id"],
                    "slug":   article.get("slug"),
                    "title":  article["title"].get("rendered", ""),
                    "date":   article.get("date"),
                    "link":   article.get("link"),
                    "source": source_key,
                })
            time.sleep(DELAY_SECONDS)
        except requests.HTTPError as e:
            print(f"\n  HTTP error on page {page}: {e}")
            continue
        except Exception as e:
            print(f"\n  Error on page {page}: {e}")
            continue

    save_index(index, output_dir)
    print(f"  Done: {len(index)} articles saved to {output_dir}/")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Fetch articles from Fedora CommBlog and/or Magazine."
    )
    parser.add_argument(
        "--source",
        choices=["commblog", "magazine", "both"],
        default="both",
        help="Which source to fetch (default: both)",
    )
    args = parser.parse_args()

    if args.source == "both":
        fetch_source("commblog")
        fetch_source("magazine")
    else:
        fetch_source(args.source)

    print("\nAll fetching complete.")


if __name__ == "__main__":
    main()
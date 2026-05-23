"""
fetch_articles.py

Fetches all published articles from the Fedora Community Blog
via the WordPress REST API and saves them to data/raw/.

Usage:
    python scripts/fetch_articles.py

Output:
    - data/raw/<slug>.json  : One JSON file per article
    - data/raw/index.json   : Index of all fetched articles
"""

import os
import json
import time
import requests
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────

load_dotenv()

API_BASE_URL = os.getenv(
    "WP_API_BASE_URL",
    "https://communityblog.fedoraproject.org/wp-json/wp/v2"
)
API_KEY       = os.getenv("WP_API_KEY", None)   # Only needed if rate-limited
OUTPUT_DIR    = Path("data/raw")
PER_PAGE      = 100   # Max allowed by WordPress REST API
DELAY_SECONDS = 0.5   # Polite delay between requests

# ── Helpers ───────────────────────────────────────────────────────────────────

def build_headers() -> dict:
    """Build request headers, adding auth if an API key is set."""
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


def fetch_page(page: int, headers: dict) -> list[dict]:
    """Fetch a single page of posts from the WordPress REST API."""
    params = {
        "per_page": PER_PAGE,
        "page": page,
        "_fields": (
            "id,slug,title,date,modified,link,"
            "content,excerpt,categories,tags,author"
        ),
    }
    response = requests.get(
        f"{API_BASE_URL}/posts",
        headers=headers,
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def fetch_total_pages(headers: dict) -> int:
    """Get the total number of pages available."""
    response = requests.get(
        f"{API_BASE_URL}/posts",
        headers=headers,
        params={"per_page": PER_PAGE, "page": 1},
        timeout=30,
    )
    response.raise_for_status()
    return int(response.headers.get("X-WP-TotalPages", 1))


def save_article(article: dict, output_dir: Path) -> None:
    """Save a single article as a JSON file named by its slug."""
    slug = article.get("slug", str(article["id"]))
    filepath = output_dir / f"{slug}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(article, f, ensure_ascii=False, indent=2)


def save_index(index: list[dict], output_dir: Path) -> None:
    """Save a lightweight index of all fetched articles."""
    filepath = output_dir / "index.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"\n Index saved → {filepath} ({len(index)} articles)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    headers = build_headers()

    print(f" Connecting to: {API_BASE_URL}")
    total_pages = fetch_total_pages(headers)
    print(f" Total pages to fetch: {total_pages}")

    all_articles = []
    index = []

    for page in tqdm(range(1, total_pages + 1), desc="Fetching pages"):
        try:
            articles = fetch_page(page, headers)
            for article in articles:
                save_article(article, OUTPUT_DIR)
                index.append({
                    "id":       article["id"],
                    "slug":     article.get("slug"),
                    "title":    article["title"].get("rendered", ""),
                    "date":     article.get("date"),
                    "link":     article.get("link"),
                })
                all_articles.append(article)
            time.sleep(DELAY_SECONDS)
        except requests.HTTPError as e:
            print(f"\n  HTTP error on page {page}: {e}")
            continue
        except Exception as e:
            print(f"\n Unexpected error on page {page}: {e}")
            continue

    save_index(index, OUTPUT_DIR)
    print(f" Done! {len(all_articles)} articles saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
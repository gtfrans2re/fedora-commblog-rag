# Dev Notes — fedora-commblog-rag

Running log of decisions, findings, blockers, and observations throughout
the mini-project. Updated as work progresses.

---

## Project Context

- **Internship:** Outreachy — Fedora Project
- **Mentors:** Carol Chen, Dominik Kawka, Justin Wheeler
- **Sprint cadence:** Weekly, planning on Tuesdays
- **Communication:** Matrix / Element (daily stand-ups)
- **Repo:** https://github.com/gtfrans2re/fedora-commblog-rag

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05-21 | Chose CommBlog as mini-project scope | Focused corpus, clear evaluation criteria, real editorial utility |
| 2026-05-21 | Single model approach (not separate per publication) | Prioritize depth over breadth within sprint timeframe |
| 2026-05-21 | Personal repo for initial dev | Easier to experiment before migrating to team infrastructure |
| 2026-05-21 | WordPress REST API for data collection | Preserves formatting better than scraping |
| 2026-05-21 | Apache 2.0 license | Aligns with RamaLama and Fedora/Red Hat ecosystem |

---

## Setup Notes

### Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### RamaLama Installation

Follow the official docs: https://github.com/containers/ramalama

```bash
# Pull models locally before benchmarking
ramalama pull qwen2.5:7b
ramalama pull smollm2:1.7b
ramalama pull gemma3:4b
ramalama pull granite3.3:8b
```

### WordPress API

- Base URL: `https://communityblog.fedoraproject.org/wp-json/wp/v2`
- No auth required for public posts
- Max `per_page=100` per request
- Rate limiting: add a polite delay between requests (`DELAY_SECONDS = 0.5`)
- API key only needed if rate-limited — Justin Wheeler offered to help obtain one

---

## Data Notes

### WordPress REST API Findings

- [ ] Total articles fetched: TBD
- [ ] Date range of corpus: TBD
- [ ] Average article length: TBD
- [ ] API rate limits hit: Yes / No

### Docling Ingestion Findings

- Docling handles HTML → Markdown conversion cleanly
- Preserves heading structure, lists, and code blocks
- Watch out for: embedded shortcodes from WordPress (e.g. `[caption]`)
- HTML comments like `<!--more-->` are preserved and useful for quality checks

### Dataset Quality (from quality_report.json)

- [ ] Total articles: TBD
- [ ] Articles passing all checks: TBD
- [ ] Most common failure: TBD
- Notable findings:
  - Missing featured images is the most common editorial issue (per meeting notes)
  - Missing `<!--more-->` tag is the second most common

### Good vs Bad Article Examples (from project spec)

**Good examples (positive training signals):**
- https://communityblog.fedoraproject.org/f44-election-nominations-now-open/
- https://communityblog.fedoraproject.org/code-of-conduct-report-2025/
- https://communityblog.fedoraproject.org/throwing-random-arguments-at-system-binaries-real-segfaults-vs-ticket-noise/
- https://communityblog.fedoraproject.org/the-forge-is-our-new-home/
- https://communityblog.fedoraproject.org/two-shell-functions-to-simplify-pagure-pull-request-reviews/

**Bad examples (useful for evaluation):**
- No featured image: https://communityblog.fedoraproject.org/fedora-and-centos-scale-23x-2026/
- No `--more--` tag: https://communityblog.fedoraproject.org/community-update-week-20/

---

## Chunking Experiments

| Chunk Size | Overlap | Num Chunks (sample) | Notes |
|-----------|---------|---------------------|-------|
| 128 | 32 | TBD | Very granular — may lose context |
| 256 | 64 | TBD | |
| 512 | 64 | TBD | Starting default per ramalama_rag.yaml |
| 1024 | 128 | TBD | May be too large for smaller models |

---

## Model Benchmarking Notes

### Models

| Model | Size | Local Performance | Notes |
|-------|------|-------------------|-------|
| Qwen 2.5 7B | 7B | TBD | Fast, efficient |
| SmolLM2 1.7B | 1.7B | TBD | Best for local/low-resource |
| Gemma 3 4B | 4B | TBD | Strong general performance |
| Granite 3.3 8B | 8B | TBD | Open weights, Fedora-friendly; may be heavier |

### Hardware Constraints

- **Local:** Laptop — suitable for 7B–8B models max
- **Remote VM (GPU1):** Access pending (Dominik Kawka provisioning)
  - Will enable testing 20B–30B parameter models
  - Needed for fair Granite benchmarking

### Benchmark Results Summary

> Fill in after running `scripts/benchmark.py`

| Model | Avg Latency | Avg Score | Best Prompt | Worst Prompt |
|-------|-------------|-----------|-------------|--------------|
| Qwen 2.5 7B | | | | |
| SmolLM2 1.7B | | | | |
| Gemma 3 4B | | | | |
| Granite 3.3 8B | | | | |

---

## Blockers & Open Questions

- [ ] GPU1 VM access — pending Dominik
- [ ] Replicate sharing permissions — need to reply to Carol's email
- [ ] API key for WordPress if rate-limited — Justin offered to help
- [ ] Feedback session with Michal Konecny (CommBlog editor) — schedule TBD

---

## Stand-up Log

> Keep entries short (max 5 words per task per Carol's guidance)

| Date | Done | Blockers |
|------|------|----------|
| | | |

---

## References

- RamaLama docs: https://github.com/containers/ramalama
- Docling docs: https://github.com/DS4SD/docling
- WordPress REST API: https://developer.wordpress.org/rest-api/
- Fedora CommBlog: https://communityblog.fedoraproject.org/
- Outreachy project page: TBD
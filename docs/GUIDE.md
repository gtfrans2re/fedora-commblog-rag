# Complete Pipeline Guide — fedora-commblog-rag

A step-by-step guide to run the full pipeline from a fresh clone
to benchmarked RAG results.

---

## Prerequisites

Before starting, make sure you have the following installed on your machine:

| Tool | Min Version | Check |
|------|-------------|-------|
| Python | 3.10+ | `python --version` |
| Git | any | `git --version` |
| pip | 23+ | `pip --version` |
| RamaLama | latest | `ramalama --version` |
| Podman | latest | `podman --version` |

### Install RamaLama (if not already installed)

```bash
# On Fedora / RHEL-based systems
sudo dnf install ramalama

# Or via pip
pip install ramalama
```

> For full RamaLama installation options, see:
> https://github.com/containers/ramalama

---

## Step 0 — Clone the Repo

```bash
git clone https://github.com/gtfrans2re/fedora-commblog-rag.git
cd fedora-commblog-rag
```

Confirm the structure looks right:

```bash
ls -la
```

Expected output:

```
data/
docs/
models/
notebooks/
scripts/
.gitignore
LICENSE
README.md
requirements.txt
```

---

## Step 1 — Set Up the Python Environment

### 1.1 Create a virtual environment

```bash
python -m venv venv
```

### 1.2 Activate it

```bash
# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

Your terminal prompt should now show `(venv)` at the start.

### 1.3 Upgrade pip

```bash
pip install --upgrade pip
```

### 1.4 Install all dependencies

```bash
pip install -r requirements.txt
```

### 1.5 Verify key packages installed correctly

```bash
python -c "import requests; print('requests ok')"
python -c "import docling; print('docling ok')"
python -c "import pandas; print('pandas ok')"
python -c "import tqdm; print('tqdm ok')"
python -c "import matplotlib; print('matplotlib ok')"
```

---

## Step 2 — Configure Environment Variables

### 2.1 Create your `.env` file

```bash
cp .env.example .env 2>/dev/null || touch .env
```

### 2.2 Open and edit `.env`

```bash
nano .env
```

Add the following:

```env
WP_API_BASE_URL=https://communityblog.fedoraproject.org/wp-json/wp/v2
WP_API_KEY=      # Leave blank unless you hit rate limits
```

Save and close (`Ctrl+O`, `Enter`, `Ctrl+X`).

> **Note:** No API key is needed for public articles.
> Only add one if you start hitting rate limit errors (HTTP 429).

---

## Step 3 — Add the Editorial Guidelines

The RAG pipeline uses both past articles and the editorial
guidelines as its knowledge base. The guidelines need to be added
manually as they are not available via the API.

### 3.1 Create a guidelines file

```bash
nano data/guidelines/commblog_guidelines.md
```

Paste in the CommBlog editorial guidelines (tone, structure,
required elements, topic scope, etc.) from:
- https://docs.fedoraproject.org/en-US/commops/commblog/
- Any internal style guide shared by your mentors

Save and close.

> **Tip:** Even a rough first version is fine here.
> You can refine the guidelines file as you learn more
> from the editors (Michal Konecny).

---

## Step 4 — Fetch Articles from the WordPress API

This script downloads all published articles from the Fedora
Community Blog and saves them as JSON files in `data/raw/`.

### 4.1 Run the fetcher

```bash
python scripts/fetch_articles.py
```

### 4.2 What to expect

```
Connecting to: https://communityblog.fedoraproject.org/wp-json/wp/v2
Total pages to fetch: 12
Fetching pages: 100%|████████████| 12/12 [00:08<00:00]
Index saved -> data/raw/index.json (1147 articles)
Done! 1147 articles saved to data/raw/
```

### 4.3 Verify the output

```bash
# Count how many articles were saved
ls data/raw/*.json | wc -l

# Peek at the index
cat data/raw/index.json | python -m json.tool | head -30

# Inspect a single article file
ls data/raw/ | grep -v index | head -1 | xargs -I{} cat data/raw/{}
```

### Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `HTTP 403` | Server blocking default User-Agent | Add `User-Agent` header in `build_headers()` |
| `HTTP 429` | Rate limited | Add `WP_API_KEY` to `.env` or increase `DELAY_SECONDS` |
| `ConnectionError` | No internet / wrong URL | Check `WP_API_BASE_URL` in `.env` |
| `0 articles saved` | API returned empty | Check the API directly in your browser |

---

## Step 5 — Ingest with Docling

This script converts each raw HTML article into clean Markdown
with YAML frontmatter, using Docling.

### 5.1 Run the ingestion

```bash
python scripts/ingest_docling.py
```

### 5.2 What to expect

```
Found 1147 raw articles to process.
Ingesting with Docling: 100%|████████████| 1147/1147 [04:30<00:00]
Ingestion complete: 1143 succeeded, 4 failed.
```

### 5.3 Verify the output

```bash
# Count cleaned Markdown files
ls data/cleaned/*.md | wc -l

# Inspect a cleaned article
ls data/cleaned/*.md | head -1 | xargs cat | head -40
```

A correctly processed file should look like:

```markdown
---
id: 12345
slug: my-article-slug
title: "My Article Title"
date: 2025-03-14T10:00:00
modified: 2025-03-15T08:00:00
link: https://communityblog.fedoraproject.org/my-article-slug/
---

> Brief excerpt text here.

## Introduction

Article body content in clean Markdown...
```

### Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `docling not found` | Package missing | `pip install docling` |
| `Failed to process X.json` | Malformed HTML | Check the raw JSON; may be an empty post |
| Slow processing | Large corpus | Normal — Docling processes files sequentially |

---

## Step 6 — Clean the Dataset

This script cleans the Markdown files in-place and runs
editorial quality checks on every article.

### 6.1 Run the cleaner

```bash
python scripts/clean_dataset.py
```

### 6.2 What to expect

```
Cleaning 1143 articles...
Cleaning articles: 100%|████████████| 1143/1143 [00:45<00:00]

Quality report saved -> data/cleaned/quality_report.json

--------------------------------------------------
  Dataset Quality Summary
--------------------------------------------------
  Total articles  : 1143
  Passed          : 891
  Failed          : 252
--------------------------------------------------
```

### 6.3 Review the quality report

```bash
# Pretty-print the report
cat data/cleaned/quality_report.json | python -m json.tool | head -60

# Count articles that failed each specific check
python -c "
import json
report = json.load(open('data/cleaned/quality_report.json'))
checks = ['has_featured_image','has_more_tag','has_headings','has_min_length','has_title']
for c in checks:
    failed = sum(1 for r in report if not r['quality'].get(c, True))
    print(f'{c}: {failed} failed')
"
```

> **Note:** Articles that fail quality checks are not removed —
> they are kept in the corpus but flagged. The quality report is
> used by the RAG pipeline to understand what "bad" looks like,
> which is just as useful as knowing what "good" looks like.

---

## Step 7 — Pull the Models

Before running the RAG pipeline, pull each model locally with RamaLama.
Use the HuggingFace format — the `ollama://` format is deprecated.

```bash
ramalama pull hf://Qwen/Qwen3-4B-GGUF
ramalama pull hf://Qwen/Qwen3-1.7B-GGUF
ramalama pull hf://ggml-org/gemma-3-4b-it-GGUF
ramalama pull hf://instructlab/granite-7b-lab-GGUF/granite-7b-lab-Q4_K_M.gguf
```

> **Hardware note:**
> - 4B–8B models: require ~4–8 GB RAM/VRAM — fine on most laptops
> - If you run into memory issues, start with `hf://Qwen/Qwen3-1.7B-GGUF` only
> - For 20B+ models, use the GPU1 VM (coordinate with Dominik Kawka)

Verify models are available:

```bash
ramalama list
```

---

## Step 8 — Build the RAG Vector Store

This is a two-step process: first build the vector store from your
corpus, then run queries against it. Both steps use `localhost/`
as the image prefix — never `quay.io/` (that tries to pull from
the internet and will fail).

### 8.1 Build the vector store

```bash
ramalama rag --chunk-size 256 data/cleaned localhost/fedora-commblog-rag
```

> **Why `--chunk-size 256`?** The default chunk size of 400 tokens
> occasionally produces chunks of 500+ tokens, which exceeds the
> embedder's 512-token batch limit and crashes the build. 256 keeps
> all chunks safely within the limit.

### 8.2 What to expect

```
Reading article-slug.md (1/1789)...
...
Reading youre-invited-to-the-fedora-linux-37-release-party.md (1789/1789)...
Chunking documents...
  7340 chunks created
Embedding chunks via llama.cpp...
  Embedding 7340/7340 chunks...
Stored 7340 vectors in Qdrant
```

### 8.3 Verify the image was created locally

```bash
podman images | grep fedora-commblog-rag
```

Expected output:

```
localhost/fedora-commblog-rag   latest   <image-id>   X minutes ago   XXX MB
```

### Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `input (N tokens) is too large` | Chunk too big for embedder | Lower `--chunk-size` further, e.g. `--chunk-size 200` |
| `image does not exist` on run | Used `quay.io/` prefix | Always use `localhost/` prefix |
| Podman not running | Podman daemon inactive | `systemctl --user start podman` |

---

## Step 9 — Test a Single RAG Query

Do a quick sanity check with a single query before running
the full benchmark.

```bash
ramalama run --rag localhost/fedora-commblog-rag hf://Qwen/Qwen3-4B-GGUF
```

This opens an interactive prompt. Type your query and press Enter:

```
What tone should a Fedora Community Blog article use?
```

A good response will reference specific guidelines from the corpus,
be constructive and grounded, and mention things like professional
tone, Fedora community audience, and technical accuracy.

Press `Ctrl+D` to exit the interactive session.

---

## Step 10 — Test the Reference Articles

Test the RAG model against the known good and bad articles from
the project spec to validate editorial feedback quality.

### Good articles (model should confirm they meet standards)

```
https://communityblog.fedoraproject.org/f44-election-nominations-now-open/
https://communityblog.fedoraproject.org/code-of-conduct-report-2025/
https://communityblog.fedoraproject.org/throwing-random-arguments-at-system-binaries-real-segfaults-vs-ticket-noise/
https://communityblog.fedoraproject.org/the-forge-is-our-new-home/
https://communityblog.fedoraproject.org/two-shell-functions-to-simplify-pagure-pull-request-reviews/
```

### Bad articles (model should flag specific issues)

```
https://communityblog.fedoraproject.org/fedora-and-centos-scale-23x-2026/
  Issue: missing featured image

https://communityblog.fedoraproject.org/community-update-week-20/
  Issue: missing --more-- tag
```

### 10.1 Test in the terminal

Start an interactive RAG session:

```bash
ramalama run --rag localhost/fedora-commblog-rag hf://Qwen/Qwen3-4B-GGUF
```

Then paste each of these prompts one at a time:

```
# Good article test — paste the article content and ask:
Review this article draft. Does it meet Fedora Community Blog
editorial standards for tone, structure, and required elements?

[paste article content here]
```

```
# Bad article test — explicitly mention the missing elements:
This article has no featured image and no --more-- tag.
What Fedora Community Blog guidelines does it violate and
what should the author fix?
```

### 10.2 Test in the notebook

Open the notebook:

```bash
jupyter notebook notebooks/exploration.ipynb
```

Navigate to **Section 4 — RAG Query Testing** and run the
following in the ad-hoc query cells:

```python
# --- Good article test ---
GOOD_ARTICLE_PROMPT = """
Review this article. Does it meet Fedora Community Blog editorial
standards for tone, structure, featured image, and use of the
--more-- tag?

Title: F44 Election Nominations Now Open
Link: https://communityblog.fedoraproject.org/f44-election-nominations-now-open/

[paste article body here]
"""

response = query_rag_adhoc('hf://Qwen/Qwen3-4B-GGUF', GOOD_ARTICLE_PROMPT)
print(response)
```

```python
# --- Bad article test (missing featured image) ---
BAD_ARTICLE_PROMPT_1 = """
This article was published without a featured image.
According to Fedora Community Blog guidelines, is a featured image
required? What impact does a missing featured image have and
what should the author do to fix it?

Link: https://communityblog.fedoraproject.org/fedora-and-centos-scale-23x-2026/
"""

response = query_rag_adhoc('hf://Qwen/Qwen3-4B-GGUF', BAD_ARTICLE_PROMPT_1)
print(response)
```

```python
# --- Bad article test (missing --more-- tag) ---
BAD_ARTICLE_PROMPT_2 = """
This article is missing the --more-- tag.
According to Fedora Community Blog guidelines, what is the
--more-- tag, why is it required, and what happens to the
article homepage listing when it is absent?

Link: https://communityblog.fedoraproject.org/community-update-week-20/
"""

response = query_rag_adhoc('hf://Qwen/Qwen3-4B-GGUF', BAD_ARTICLE_PROMPT_2)
print(response)
```

```python
# --- Run all reference articles in a loop ---
REFERENCE_TESTS = [
    {
        "label": "Good — F44 Election Nominations",
        "expected": "pass",
        "prompt": "Does this article meet CommBlog standards? Title: F44 Election Nominations Now Open. [paste content]"
    },
    {
        "label": "Good — Code of Conduct Report 2025",
        "expected": "pass",
        "prompt": "Does this article meet CommBlog standards? Title: Code of Conduct Report 2025. [paste content]"
    },
    {
        "label": "Good — Throwing Random Arguments at System Binaries",
        "expected": "pass",
        "prompt": "Does this article meet CommBlog standards? Title: Throwing Random Arguments at System Binaries. [paste content]"
    },
    {
        "label": "Good — The Forge Is Our New Home",
        "expected": "pass",
        "prompt": "Does this article meet CommBlog standards? Title: The Forge Is Our New Home. [paste content]"
    },
    {
        "label": "Good — Two Shell Functions to Simplify Pagure Pull Request Reviews",
        "expected": "pass",
        "prompt": "Does this article meet CommBlog standards? Title: Two Shell Functions to Simplify Pagure. [paste content]"
    },
    {
        "label": "Bad — Missing featured image",
        "expected": "fail",
        "prompt": "This article has no featured image. What CommBlog guideline does this violate?"
    },
    {
        "label": "Bad — Missing --more-- tag",
        "expected": "fail",
        "prompt": "This article is missing the --more-- tag. What CommBlog guideline does this violate?"
    },
]

MODEL = 'hf://Qwen/Qwen3-4B-GGUF'

for test in REFERENCE_TESTS:
    print(f"\n{'='*60}")
    print(f"  {test['label']}  [expected: {test['expected']}]")
    print(f"{'='*60}")
    response = query_rag_adhoc(MODEL, test['prompt'])
    print(response)
```

---

## Step 11 — Run the Full Benchmark

This script runs 5 editorial test prompts across all models
and saves results to `results/`.

### 11.1 Run the benchmark

```bash
python scripts/benchmark.py
```

### 11.2 Review the results

```bash
# Read the Markdown summary table
cat results/benchmark_summary.md

# Or open the full JSON
cat results/benchmark_*.json | python -m json.tool
```

---

## Step 12 — Explore Results in the Notebook

```bash
jupyter notebook notebooks/exploration.ipynb
```

Run the cells in order:
1. **Setup** — confirms paths and file counts
2. **Dataset Overview** — articles per year chart
3. **Quality Report** — pass rate charts, failed article list
4. **Chunking Experiments** — compare chunk sizes on a sample article
5. **RAG Query Testing** — reference article tests (Section 10 above)
6. **Benchmark Visualization** — latency/score bar charts + heatmap

---

## Step 13 — Iterate

Based on your results, iterate on the key variables:

### Tune chunking

Rebuild the RAG store with a different chunk size:

```bash
ramalama rag --chunk-size 128 data/cleaned localhost/fedora-commblog-rag
```

Try values: `128`, `200`, `256`, `384`. Re-test after each rebuild.

### Refine the system prompt

Edit `models/ramalama_config/ramalama_rag.yaml` and update the
`system_prompt` field to be more or less specific, then rebuild.

### Add more guidelines

Drop additional `.md` files into `data/guidelines/` and rebuild:

```bash
ramalama rag --chunk-size 256 data/cleaned localhost/fedora-commblog-rag
```

---

## Full Pipeline — Quick Reference

```bash
# Activate environment
source venv/bin/activate

# 1. Fetch data
python scripts/fetch_articles.py

# 2. Ingest with Docling
python scripts/ingest_docling.py

# 3. Clean dataset
python scripts/clean_dataset.py

# 4. Pull models (first time only)
ramalama pull hf://Qwen/Qwen3-4B-GGUF
ramalama pull hf://Qwen/Qwen3-1.7B-GGUF
ramalama pull hf://ggml-org/gemma-3-4b-it-GGUF
ramalama pull hf://instructlab/granite-7b-lab-GGUF/granite-7b-lab-Q4_K_M.gguf

# 5. Build RAG vector store
ramalama rag --chunk-size 256 data/cleaned localhost/fedora-commblog-rag

# 6. Verify image exists
podman images | grep fedora-commblog-rag

# 7. Interactive RAG session
ramalama run --rag localhost/fedora-commblog-rag hf://Qwen/Qwen3-4B-GGUF

# 8. Full benchmark
python scripts/benchmark.py

# 9. Explore results
jupyter notebook notebooks/exploration.ipynb
```

---

## Commit Your Results

```bash
git add results/ docs/notes.md data/cleaned/quality_report.json
git commit -m "feat: add benchmark results for qwen/smollm/gemma/granite"
git push
```

---

## Getting Help

| Channel | Use for |
|---------|---------|
| Matrix / Element | Daily stand-ups, quick blockers |
| GitHub Issues | Bug reports, feature requests |
| Justin Wheeler | WordPress API key, RamaLama questions |
| Dominik Kawka | GPU1 VM access, tech stack advice |
| Carol Chen | Sprint process, scope questions |
| Michal Konecny | CommBlog editorial feedback |
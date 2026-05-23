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
python -c "import requests; print('requests ✅')"
python -c "import docling; print('docling ✅')"
python -c "import pandas; print('pandas ✅')"
python -c "import tqdm; print('tqdm ✅')"
```

---

## Step 2 — Configure Environment Variables

### 2.1 Create your `.env` file

```bash
cp .env.example .env 2>/dev/null || touch .env
```

### 2.2 Open and edit `.env`

```bash
nano .env   # or use your preferred editor
```

Add the following:

```env
WP_API_BASE_URL=https://communityblog.fedoraproject.org/wp-json/wp/v2
WP_API_KEY=      # Leave blank unless you hit rate limits
```

Save and close (`Ctrl+O`, `Enter`, `Ctrl+X` in nano).

> **Note:** No API key is needed for public articles.
> Only add one if you start hitting rate limit errors (HTTP 429).
> Justin Wheeler offered to help obtain one if needed.

---

## Step 3 — Add the Editorial Guidelines

The RAG pipeline uses both past articles **and** the editorial
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
🔗 Connecting to: https://communityblog.fedoraproject.org/wp-json/wp/v2
📦 Total pages to fetch: 12
Fetching pages: 100%|████████████| 12/12 [00:08<00:00]
📄 Index saved → data/raw/index.json (1147 articles)
✅ Done! 1147 articles saved to data/raw/
```

### 4.3 Verify the output

```bash
# Count how many articles were saved
ls data/raw/*.json | wc -l

# Peek at one article
cat data/raw/index.json | python -m json.tool | head -30

# Inspect a single article file
ls data/raw/ | grep -v index | head -1 | xargs -I{} cat data/raw/{}
```

### Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `HTTP 429` | Rate limited | Add `WP_API_KEY` to `.env` or increase `DELAY_SECONDS` in the script |
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
📂 Found 1147 raw articles to process.
Ingesting with Docling: 100%|████████████| 1147/1147 [04:30<00:00]
✅ Ingestion complete: 1143 succeeded, 4 failed.
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
| `Failed to process X.json` | Malformed HTML | Check the raw JSON file; may be an empty post |
| Slow processing | Large corpus | Normal — Docling processes each file sequentially |

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
🧹 Cleaning 1143 articles...
Cleaning articles: 100%|████████████| 1143/1143 [00:45<00:00]

📊 Quality report saved → data/cleaned/quality_report.json

──────────────────────────────────────────────────
  Dataset Quality Summary
──────────────────────────────────────────────────
  Total articles  : 1143
  Passed          : 891 ✅
  Failed          : 252 ⚠️
──────────────────────────────────────────────────

  Articles with issues:
    • some-article-slug: has_featured_image, has_more_tag
    • another-article: has_more_tag
    ...

✅ Cleaning complete.
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

> **Note:** Articles that fail quality checks are **not removed** —
> they are kept in the corpus but flagged. The quality report is
> used by the RAG pipeline to understand what "bad" looks like,
> which is just as useful as knowing what "good" looks like.

---

## Step 7 — Pull the Models

Before running the RAG pipeline, pull each model locally with RamaLama.

```bash
ramalama pull qwen2.5:7b
ramalama pull smollm2:1.7b
ramalama pull gemma3:4b
ramalama pull granite3.3:8b
```

> **Hardware note:**
> - 7B–8B models: require ~6–8 GB RAM/VRAM — fine on most laptops
> - If you run into memory issues, start with `smollm2:1.7b` only
> - For 20B+ models, use the GPU1 VM (coordinate with Dominik Kawka)

Verify models are available:

```bash
ramalama list
```

---

## Step 8 — Test a Single RAG Query

Before running the full benchmark, do a quick sanity check
with a single query to confirm the pipeline works end to end.

```bash
ramalama rag \
  --model qwen2.5:7b \
  --corpus data/cleaned \
  --query "What tone should a Fedora Community Blog article use?"
```

A good response will:
- Reference specific guidelines from the corpus
- Be constructive and grounded (not generic)
- Mention things like: professional tone, Fedora community audience,
  technical accuracy, etc.

If the response looks reasonable, you're ready to benchmark.

---

## Step 9 — Run the Full Benchmark

This script runs 5 editorial test prompts across all 4 models
and saves results to `results/`.

### 9.1 Run the benchmark

```bash
python scripts/benchmark.py
```

### 9.2 What to expect

```
═══════════════════════════════════════════════════════
  Testing model: Qwen 2.5 7B
═══════════════════════════════════════════════════════
  ▶ Running: tone_check...        ✅ (4.2s, score=0.750)
  ▶ Running: structure_check...   ✅ (3.8s, score=0.800)
  ▶ Running: technical_accuracy.. ✅ (5.1s, score=0.625)
  ▶ Running: topic_scope...       ✅ (3.5s, score=0.714)
  ▶ Running: new_author_guidance. ✅ (4.7s, score=0.875)

  Summary → avg latency: 4.26s | avg score: 0.753 | errors: 0
...
📄 Full results saved → results/benchmark_20260522_143201.json
📊 Summary table saved → results/benchmark_summary.md
✅ Benchmark complete for 4 models × 5 prompts.
```

### 9.3 Review the results

```bash
# Read the Markdown summary table
cat results/benchmark_summary.md

# Or open the full JSON
cat results/benchmark_*.json | python -m json.tool
```

---

## Step 10 — Explore Results in the Notebook

Launch Jupyter to visualize and dig deeper into the results.

```bash
jupyter notebook notebooks/exploration.ipynb
```

Run the cells in order:
1. **Setup** — confirms paths and file counts
2. **Dataset Overview** — articles per year chart
3. **Quality Report** — pass rate charts, failed article list
4. **Chunking Experiments** — compare chunk sizes on a sample article
5. **RAG Query Testing** — run live queries interactively
6. **Benchmark Visualization** — latency/score bar charts + heatmap

---

## Step 11 — Iterate

Based on your results, iterate on the key variables:

### Tune chunking

Edit `models/ramalama_config/ramalama_rag.yaml`:

```yaml
chunking:
  chunk_size: 256    # Try 128, 256, 512, 1024
  chunk_overlap: 32  # Try 32, 64, 128
```

Re-run the benchmark after each change and compare results.

### Refine the system prompt

In `ramalama_rag.yaml`, edit the `system_prompt` field to
be more or less specific and observe how responses change.

### Add more guidelines

Drop additional `.md` files into `data/guidelines/` —
for example, a Fedora Magazine style guide — and re-run
the pipeline from Step 8.

---

## Full Pipeline — Quick Reference

Once everything is set up, the full pipeline runs in this order:

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
ramalama pull qwen2.5:7b
ramalama pull smollm2:1.7b
ramalama pull gemma3:4b
ramalama pull granite3.3:8b

# 5. Quick sanity check
ramalama rag --model qwen2.5:7b --corpus data/cleaned \
  --query "What are the required elements for a CommBlog article?"

# 6. Full benchmark
python scripts/benchmark.py

# 7. Explore results
jupyter notebook notebooks/exploration.ipynb
```

---

## Commit Your Results

After each meaningful run, commit your findings:

```bash
# Stage results and notes
git add results/ docs/notes.md data/cleaned/quality_report.json

# Commit with a descriptive message
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
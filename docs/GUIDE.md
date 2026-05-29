# Complete Pipeline Guide — fedora-commblog-rag

A step-by-step guide to run the full pipeline from a fresh clone
to benchmarked RAG results across both the Fedora Community Blog
and Fedora Magazine.

---

## Prerequisites

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

> Full RamaLama installation options: https://github.com/containers/ramalama

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

~~~
app.py
data/
docs/
models/
notebooks/
scripts/
.gitignore
LICENSE
README.md
requirements.txt
~~~

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

### 1.3 Upgrade pip and install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 1.4 Verify key packages

```bash
python -c "import requests; print('requests ok')"
python -c "import docling; print('docling ok')"
python -c "import pandas; print('pandas ok')"
python -c "import tqdm; print('tqdm ok')"
python -c "import matplotlib; print('matplotlib ok')"
python -c "import streamlit; print('streamlit ok')"
```

---

## Step 2 — Configure Environment Variables

### 2.1 Create your `.env` file

```bash
touch .env
nano .env
```

Add the following:

```env
WP_COMMBLOG_API_URL=https://communityblog.fedoraproject.org/wp-json/wp/v2
WP_MAGAZINE_API_URL=https://fedoramagazine.org/wp-json/wp/v2
WP_API_KEY=      # Leave blank unless you hit rate limits
```

Save and close (`Ctrl+O`, `Enter`, `Ctrl+X`).

---

## Step 3 — Add the Editorial Guidelines

Both publications have guidelines files already provided in `data/guidelines/`.
Review and expand them as needed:

```bash
# CommBlog guidelines
nano data/guidelines/commblog_guidelines.md

# Magazine guidelines
nano data/guidelines/magazine_guidelines.md
```

Sources:
- CommBlog: https://docs.fedoraproject.org/en-US/commops/commblog/
- Magazine: https://docs.fedoraproject.org/en-US/fedora-magazine/

> **Tip:** Refine both files as you get feedback from editors
> (Michal Konecny for CommBlog, Magazine editorial team).

---

## Step 4 — Fetch Articles from Both WordPress APIs

The fetcher supports three modes: `commblog`, `magazine`, or `both`.

### 4.1 Fetch both sources (recommended)

```bash
python scripts/fetch_articles.py
```

### 4.2 Fetch a single source

```bash
python scripts/fetch_articles.py --source commblog
python scripts/fetch_articles.py --source magazine
```

### 4.3 What to expect

```
=======================================================
  Fetching: Fedora Community Blog
  API    : https://communityblog.fedoraproject.org/wp-json/wp/v2
=======================================================
  Total pages: 12
  Pages: 100%|████████████| 12/12 [00:08<00:00]
  Index saved -> data/raw/commblog/index.json (1147 articles)
  Done: 1147 articles saved to data/raw/commblog/

=======================================================
  Fetching: Fedora Magazine
  API    : https://fedoramagazine.org/wp-json/wp/v2
=======================================================
  Total pages: 38
  Pages: 100%|████████████| 38/38 [00:25<00:00]
  Index saved -> data/raw/magazine/index.json (3742 articles)
  Done: 3742 articles saved to data/raw/magazine/
```

### 4.4 Verify the output

```bash
# Count CommBlog articles
ls data/raw/commblog/*.json | wc -l

# Count Magazine articles
ls data/raw/magazine/*.json | wc -l

# Peek at the CommBlog index
cat data/raw/commblog/index.json | python -m json.tool | head -20
```

### Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `HTTP 403` | Server blocking User-Agent | User-Agent header already set in script |
| `HTTP 429` | Rate limited | Add `WP_API_KEY` to `.env` or increase `DELAY_SECONDS` |
| `ConnectionError` | No internet / wrong URL | Check `.env` API URLs |
| `0 articles saved` | API returned empty | Test the URL directly in your browser |

---

## Step 5 — Ingest with Docling

Converts raw HTML articles into clean Markdown with YAML frontmatter.
Each source gets its own output directory.

### 5.1 Ingest both sources

```bash
python scripts/ingest_docling.py
```

### 5.2 Ingest a single source

```bash
python scripts/ingest_docling.py --source commblog
python scripts/ingest_docling.py --source magazine
```

### 5.3 What to expect

```
=======================================================
  Ingesting: Fedora Community Blog (1147 articles)
=======================================================
  Ingesting: 100%|████████████| 1147/1147 [04:30<00:00]
  Done: 1143 succeeded, 4 failed.

=======================================================
  Ingesting: Fedora Magazine (3742 articles)
=======================================================
  Ingesting: 100%|████████████| 3742/3742 [14:10<00:00]
  Done: 3738 succeeded, 4 failed.
```

### 5.4 Verify the output

```bash
ls data/cleaned/commblog/*.md | wc -l
ls data/cleaned/magazine/*.md | wc -l

# Inspect a cleaned article — note the source field in frontmatter
ls data/cleaned/commblog/*.md | head -1 | xargs cat | head -12
```

A correctly processed file looks like:

```markdown
---
id: 12345
slug: my-article-slug
title: "My Article Title"
date: 2025-03-14T10:00:00
modified: 2025-03-15T08:00:00
link: https://communityblog.fedoraproject.org/my-article-slug/
source: Fedora Community Blog
---

> Brief excerpt here.

## Introduction
```

### Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `docling not found` | Package missing | `pip install docling` |
| `Failed to process X.json` | Malformed HTML | May be an empty post — safe to ignore |
| Slow processing | Large Magazine corpus | Normal — runs sequentially |

---

## Step 6 — Clean the Dataset

Cleans Markdown files in-place and runs editorial quality checks.
Generates a `quality_report.json` per source.

### 6.1 Clean both sources

```bash
python scripts/clean_dataset.py
```

### 6.2 Clean a single source

```bash
python scripts/clean_dataset.py --source commblog
python scripts/clean_dataset.py --source magazine
```

### 6.3 What to expect

```
  Fedora Community Blog
  ----------------------------------------
  Total   : 1143
  Passed  : 891
  Failed  : 252

  Fedora Magazine
  ----------------------------------------
  Total   : 3738
  Passed  : 3201
  Failed  : 537
```

### 6.4 Review the quality reports

```bash
# CommBlog report
cat data/cleaned/commblog/quality_report.json | python -m json.tool | head -40

# Magazine report
cat data/cleaned/magazine/quality_report.json | python -m json.tool | head -40

# Count failures per check for CommBlog
python -c "
import json
report = json.load(open('data/cleaned/commblog/quality_report.json'))
checks = ['has_featured_image','has_more_tag','has_headings','has_min_length','has_title']
for c in checks:
    failed = sum(1 for r in report if not r['quality'].get(c, True))
    print(f'{c}: {failed} failed')
"
```

---

## Step 7 — Pull the Models

Use HuggingFace format — `ollama://` is deprecated in RamaLama.

```bash
ramalama pull hf://Qwen/Qwen3-4B-GGUF
ramalama pull hf://HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF
ramalama pull hf://ggml-org/gemma-3-4b-it-GGUF
ramalama pull hf://instructlab/granite-7b-lab-GGUF/granite-7b-lab-Q4_K_M.gguf
```

> **Hardware note:**
> - 4B–8B models: ~4–8 GB RAM/VRAM — fine on most laptops
> - Start with `hf://HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF` if memory is tight
> - For 20B+ models, use the GPU1 VM (coordinate with Dominik Kawka)

```bash
ramalama list
```

---

## Step 8 — Build the RAG Vector Stores

Build a separate OCI image for each publication, plus one combined image.
Always use the `quay.io/gtfrans2re/` prefix — the images are hosted on Quay.
internet and will fail.

### 8.1 CommBlog vector store

```bash
ramalama rag --chunk-size 200 data/cleaned/commblog quay.io/gtfrans2re/fedora-commblog-rag
```

### 8.2 Magazine vector store

```bash
ramalama rag --chunk-size 200 data/cleaned/magazine quay.io/gtfrans2re/fedora-magazine-rag
```

### 8.3 Combined vector store (both publications)

```bash
ramalama rag --chunk-size 200 data/cleaned quay.io/gtfrans2re/fedora-editorial-rag
```

> **Why `--chunk-size 200`?** The default (400 tokens) occasionally produces
> chunks exceeding the embedder's 512-token batch limit, crashing the build.
> 256 keeps all chunks safely within the limit.

### 8.4 Verify all images exist

```bash
podman images | grep fedora
```

Expected output:

~~~
quay.io/gtfrans2re/fedora-commblog-rag    latest   <id>   X min ago   XXX MB
quay.io/gtfrans2re/fedora-magazine-rag    latest   <id>   X min ago   XXX MB
quay.io/gtfrans2re/fedora-editorial-rag   latest   <id>   X min ago   XXX MB
~~~

### Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `input (N tokens) is too large` | Chunk too big | Lower further, e.g. `--chunk-size 150` |
| `image does not exist` on run | Image not pushed yet | Run `podman push` to Quay first |
| Podman not running | Daemon inactive | `systemctl --user start podman` |

---

## Step 9 — Test a Single RAG Query

Quick sanity check before running the full benchmark.

### CommBlog

```bash
ramalama run --rag quay.io/gtfrans2re/fedora-commblog-rag hf://Qwen/Qwen3-4B-GGUF
```

### Magazine

```bash
ramalama run --rag quay.io/gtfrans2re/fedora-magazine-rag hf://Qwen/Qwen3-4B-GGUF
```

Each opens an interactive prompt. Type a test query:

```
What tone should a Fedora Community Blog article use?
```

```
What are the required elements for a Fedora Magazine article?
```

Press `Ctrl+D` to exit.

---

## Step 10 — Test the Reference Articles

### CommBlog reference articles

**Good** (model should confirm they meet standards):
```
https://communityblog.fedoraproject.org/f44-election-nominations-now-open/
https://communityblog.fedoraproject.org/code-of-conduct-report-2025/
https://communityblog.fedoraproject.org/throwing-random-arguments-at-system-binaries-real-segfaults-vs-ticket-noise/
https://communityblog.fedoraproject.org/the-forge-is-our-new-home/
https://communityblog.fedoraproject.org/two-shell-functions-to-simplify-pagure-pull-request-reviews/
```

**Bad** (model should flag specific issues):
```
https://communityblog.fedoraproject.org/fedora-and-centos-scale-23x-2026/
  Issue: missing featured image

https://communityblog.fedoraproject.org/community-update-week-20/
  Issue: missing --more-- tag
```

### 10.1 Test in the terminal

```bash
# CommBlog session
ramalama run --rag quay.io/gtfrans2re/fedora-commblog-rag hf://Qwen/Qwen3-4B-GGUF

# Magazine session
ramalama run --rag quay.io/gtfrans2re/fedora-magazine-rag hf://Qwen/Qwen3-4B-GGUF
```

Paste one of these prompts at the interactive prompt:

```
Review this article draft. Does it meet the editorial standards
for tone, structure, featured image, and the Read More tag?
[paste article content here]
```

```
This article is missing a featured image and the Read More tag.
What guidelines does it violate and what should the author fix?
```

### 10.2 Test in the notebook

```bash
jupyter notebook notebooks/exploration.ipynb
```

Navigate to **Section 6 — Reference Article Tests** and run
the good/bad article cells there.

### 10.3 Use the GUI (easiest)

```bash
streamlit run app.py
```

Select the publication in the sidebar, paste the article in the
**Paste your draft** tab, and click **Review Article**. Use the
**Load good example** and **Load bad example** tabs to quickly
test the reference articles.

---

## Step 11 — Run the Full Benchmark

```bash
python scripts/benchmark.py
```

Review results:

```bash
cat results/benchmark_summary.md
cat results/benchmark_*.json | python -m json.tool
```

---

## Step 12 — Explore Results in the Notebook

```bash
jupyter notebook notebooks/exploration.ipynb
```

Sections:
1. **Setup** — confirms paths and file counts for both sources
2. **Dataset Overview** — articles per year, per publication
3. **Quality Report** — pass rates and failure breakdown per source
4. **Chunking Experiments** — compare chunk sizes on sample articles
5. **RAG Query Testing** — live queries against CommBlog and Magazine
6. **Reference Article Tests** — good/bad article validation
7. **Benchmark Visualization** — latency/score charts + heatmap

---

## Step 13 — Iterate

### Tune chunking

```bash
# Rebuild with a different chunk size
ramalama rag --chunk-size 200 data/cleaned/commblog quay.io/gtfrans2re/fedora-commblog-rag
ramalama rag --chunk-size 200 data/cleaned/magazine  quay.io/gtfrans2re/fedora-magazine-rag
```

Try values: `128`, `200`, `256`, `384`. Re-test after each rebuild.

### Refine the system prompt

Edit `models/ramalama_config/ramalama_rag.yaml` → `generation.system_prompt`,
rebuild, and compare responses.

### Expand guidelines

Add or refine content in:
- `data/guidelines/commblog_guidelines.md`
- `data/guidelines/magazine_guidelines.md`

Then rebuild the relevant vector store.

---

## Full Pipeline — Quick Reference

```bash
# Activate environment
source venv/bin/activate

# 1. Fetch both sources
python scripts/fetch_articles.py

# 2. Ingest with Docling
python scripts/ingest_docling.py

# 3. Clean both datasets
python scripts/clean_dataset.py

# 4. Pull models (first time only)
ramalama pull hf://Qwen/Qwen3-4B-GGUF
ramalama pull hf://HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF
ramalama pull hf://ggml-org/gemma-3-4b-it-GGUF
ramalama pull hf://instructlab/granite-7b-lab-GGUF/granite-7b-lab-Q4_K_M.gguf

# 5. Build RAG vector stores
ramalama rag --chunk-size 200 data/cleaned/commblog quay.io/gtfrans2re/fedora-commblog-rag
ramalama rag --chunk-size 200 data/cleaned/magazine  quay.io/gtfrans2re/fedora-magazine-rag
ramalama rag --chunk-size 200 data/cleaned           quay.io/gtfrans2re/fedora-editorial-rag

# 6. Verify images
podman images | grep fedora

# 7. Launch the GUI
streamlit run app.py

# 8. Or use terminal sessions directly
ramalama run --rag quay.io/gtfrans2re/fedora-commblog-rag hf://Qwen/Qwen3-4B-GGUF
ramalama run --rag quay.io/gtfrans2re/fedora-magazine-rag  hf://Qwen/Qwen3-4B-GGUF

# 9. Full benchmark
python scripts/benchmark.py

# 10. Explore results
jupyter notebook notebooks/exploration.ipynb
```

---

## Commit Your Results

```bash
git add results/ docs/notes.md
git add data/cleaned/commblog/quality_report.json
git add data/cleaned/magazine/quality_report.json
git commit -m "feat: add benchmark results for commblog and magazine"
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
| Fedora Magazine editors | Magazine editorial feedback |
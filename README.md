```markdown
# fedora-commblog-rag

A RamaLama-powered RAG tool enhanced on Fedora Community Blog articles and guidelines — helping new authors write better posts.

## Overview

This project builds a Retrieval-Augmented Generation (RAG) pipeline using [RamaLama](https://github.com/containers/ramalama) on the [Fedora Community Blog](https://communityblog.fedoraproject.org/) writing guidelines and past published articles.

**Use case:** A reviewer pastes a draft article and the model flags whether it meets editorial standards — tone, structure, topic scope, and technical accuracy.

## Project Roadmap

### Goal
> Build a RAG model trained on the Fedora Community Blog writing guidelines and past
> articles — to help reviewers flag whether draft posts meet standards for tone,
> structure, and technical accuracy.

---

### Deliverables

```
+------------------------------------------------------------------+
|                                                                  |
|  1  Curate dataset via WordPress REST API                        |
|     └─ Preserves formatting better than scraping                 |
|                         |                                        |
|                         v                                        |
|  2  Ingest & clean with Docling                                  |
|     └─ Supports HTML, PDF, Markdown -- feed into RamaLama        |
|                         |                                        |
|                         v                                        |
|  3  Test use case                                                |
|     └─ Paste draft -- model flags editorial issues               |
|                         |                                        |
|                         v                                        |
|  4  Collect editor feedback (Michal Konecny) & iterate           |
|     └─ Validate usefulness for new authors                       |
|                         |                                        |
|                         v                                        |
|  5  Expand scope decision                                        |
|     +-- Works     --> adopt for Fedora Magazine too              |
|     +-- Does not  --> stay CommBlog-only                         |
|                         |                                        |
|                         v                                        |
|  6  Write a Community Blog article summarizing the work          |
|                                                                  |
+------------------------------------------------------------------+
```

---

### Pipeline

```
WordPress REST API
       |
       v
  data/raw/*.json
       |
       v  (Docling)
  data/cleaned/*.md
       |
       v  (RamaLama RAG)
  Vector Store (Qdrant)
       |
       v
  Editorial Assistant
```

---

### Models Benchmarked

| Model      | Size    | Hardware             |
|------------|---------|----------------------|
| Qwen3      | 4B      | Local laptop         |
| SmolLM2    | 1.7B    | Local laptop         |
| Gemma 3    | 4B      | Local laptop         |
| Granite    | 7B      | Local + GPU VM       |
| TBD larger | 20B-30B | Remote GPU VM (GPU1) |

---

### Success Criteria & Constraints

| | |
|---|---|
| **Success**   | Tool validated by CommBlog editors as useful for new authors |
| **Scope**     | CommBlog only -- single model, intentionally narrow          |
| **Timeline**  | ~10 weeks -- iterate on chunking size and model performance  |
| **Variables** | Chunk size · overlap · model choice · system prompt          |

## Project Structure

```
fedora-commblog-rag/
├── data/
│   ├── raw/                  # Articles as fetched from WordPress API
│   ├── cleaned/              # Processed, ready-for-ingestion data
│   └── guidelines/           # CommBlog editorial guidelines
├── scripts/
│   ├── fetch_articles.py     # WordPress REST API scraper
│   ├── ingest_docling.py     # Docling ingestion pipeline
│   ├── clean_dataset.py      # Data cleaning & preparation
│   └── benchmark.py          # Model benchmarking
├── models/
│   └── ramalama_config/      # RamaLama RAG configs per model
├── notebooks/
│   └── exploration.ipynb     # Experimentation & results analysis
├── docs/
│   ├── notes.md              # Dev notes & findings
│   └── blog_draft.md         # Draft of the CommBlog article
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Setup

### Prerequisites

- Python 3.10+
- [RamaLama](https://github.com/containers/ramalama) installed
- Access to the Fedora Community Blog WordPress REST API

### Installation

```bash
# Clone the repo
git clone https://github.com/gtfrans2re/fedora-commblog-rag.git
cd fedora-commblog-rag

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file at the root of the project:

```env
WP_API_BASE_URL=https://communityblog.fedoraproject.org/wp-json/wp/v2
WP_API_KEY=your_api_key_here  # Only needed if rate-limited
```

## Usage

### 1. Fetch Articles

```bash
python scripts/fetch_articles.py
```

Fetches all published articles from the Fedora Community Blog via the WordPress REST API and saves them to `data/raw/`.

### 2. Ingest with Docling

```bash
python scripts/ingest_docling.py
```

Processes raw articles using Docling and outputs structured documents to `data/cleaned/`.

### 3. Clean Dataset

```bash
python scripts/clean_dataset.py
```

Cleans and prepares the dataset for ingestion into the RamaLama RAG pipeline.

### 4. Benchmark Models

```bash
python scripts/benchmark.py
```

Tests RAG performance across supported models: **Qwen**, **SmolLM**, **Gemma**, and **Granite**.

## Models Tested

| Model | Size | Notes |
|-------|------|-------|
| Qwen | 7B | Fast, efficient |
| SmolLM | 1.7B | Lightweight, good for local |
| Gemma | 7B | Strong general performance |
| Granite (IBM) | 8B | Open weights, Fedora-friendly |

## Evaluation

Success is measured by workshopping the tool with Fedora Community Blog editors to determine usefulness for new authors.

## Contributing

This project is part of an [Outreachy](https://www.outreachy.org/) internship with the Fedora Project. Contributions, feedback, and suggestions are welcome!

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
```
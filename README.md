# fedora-commblog-rag

A RamaLama-powered RAG tool trained on Fedora Community Blog and Fedora Magazine
articles and guidelines — helping new authors write better posts.

## Overview

This project builds a Retrieval-Augmented Generation (RAG) pipeline using
[RamaLama](https://github.com/containers/ramalama) on the writing guidelines
and past published articles of two Fedora publications:

- [Fedora Community Blog](https://communityblog.fedoraproject.org/) — for contributors
- [Fedora Magazine](https://fedoramagazine.org/) — for the broader Linux community

**Use case:** A reviewer pastes a draft article and the model flags whether it
meets editorial standards — tone, structure, topic scope, and technical accuracy.

---

## Project Roadmap

### Goal

> Build a RAG model trained on Fedora Community Blog and Fedora Magazine writing
> guidelines and past articles — to help reviewers flag whether draft posts meet
> standards for tone, structure, and technical accuracy.

---

### Deliverables

~~~
+------------------------------------------------------------------+
|                                                                  |
|  1  Curate dataset via WordPress REST API                        |
|     ├─ Fedora Community Blog                                     |
|     └─ Fedora Magazine                                           |
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
|  4  Collect editor feedback & iterate                            |
|     ├─ CommBlog: Michal Konecny                                  |
|     └─ Magazine: editorial team                                  |
|                         |                                        |
|                         v                                        |
|  5  Expand scope decision                                        |
|     +-- Works for Magazine --> adopt for both publications       |
|     +-- Does not fit       --> stay CommBlog-only                |
|                         |                                        |
|                         v                                        |
|  6  Write a Community Blog article summarizing the work          |
|                                                                  |
+------------------------------------------------------------------+
~~~

---

### Pipeline

~~~
WordPress REST API (CommBlog + Magazine)
              |
              v
   data/raw/commblog/*.json
   data/raw/magazine/*.json
              |
              v  (Docling)
   data/cleaned/commblog/*.md
   data/cleaned/magazine/*.md
              |
              v  (RamaLama RAG)
   localhost/fedora-commblog-rag
   localhost/fedora-magazine-rag
   localhost/fedora-editorial-rag  (combined)
              |
              v
   Editorial Assistant (app.py)
~~~

---

### Models Benchmarked

| Model      | Size    | Hardware             |
|------------|---------|----------------------|
| Qwen3      | 4B      | Local laptop         |
| Qwen3      | 1.7B    | Local laptop         |
| Gemma 3    | 4B      | Local laptop         |
| Granite    | 7B      | Local + GPU VM       |
| TBD larger | 20B-30B | Remote GPU VM (GPU1) |

---

### Success Criteria & Constraints

| | |
|---|---|
| **Success**   | Tool validated by CommBlog and Magazine editors as useful for new authors |
| **Scope**     | CommBlog first, then Magazine if the pipeline generalizes                 |
| **Timeline**  | ~10 weeks -- iterate on chunking size and model performance               |
| **Variables** | Chunk size · overlap · model choice · system prompt                       |

---

## Project Structure

~~~
fedora-commblog-rag/
├── app.py                    # Streamlit editorial assistant GUI
├── data/
│   ├── raw/
│   │   ├── commblog/         # CommBlog articles from WordPress API
│   │   └── magazine/         # Magazine articles from WordPress API
│   ├── cleaned/
│   │   ├── commblog/         # Cleaned CommBlog Markdown
│   │   └── magazine/         # Cleaned Magazine Markdown
│   └── guidelines/
│       ├── commblog_guidelines.md
│       └── magazine_guidelines.md
├── scripts/
│   ├── fetch_articles.py     # WordPress REST API scraper (both sources)
│   ├── ingest_docling.py     # Docling ingestion pipeline
│   ├── clean_dataset.py      # Data cleaning & quality checks
│   └── benchmark.py          # Model benchmarking
├── models/
│   └── ramalama_config/      # RamaLama RAG config
├── notebooks/
│   └── exploration.ipynb     # Experimentation & results analysis
├── docs/
│   ├── GUIDE.md              # Complete step-by-step pipeline guide
│   ├── notes.md              # Dev notes & findings
│   └── blog_draft.md         # Draft of the CommBlog article
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
~~~

---

## Setup

### Prerequisites

- Python 3.10+
- [RamaLama](https://github.com/containers/ramalama) installed
- Podman installed and running
- Access to the Fedora WordPress REST APIs (no key needed for public posts)

### Installation

```bash
# Clone the repo
git clone https://github.com/gtfrans2re/fedora-commblog-rag.git
cd fedora-commblog-rag

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file at the root of the project:

```env
WP_COMMBLOG_API_URL=https://communityblog.fedoraproject.org/wp-json/wp/v2
WP_MAGAZINE_API_URL=https://fedoramagazine.org/wp-json/wp/v2
WP_API_KEY=      # Only needed if rate-limited
```

---

## Usage

### 1. Fetch Articles (both sources)

```bash
python scripts/fetch_articles.py

# Or fetch individually
python scripts/fetch_articles.py --source commblog
python scripts/fetch_articles.py --source magazine
```

### 2. Ingest with Docling

```bash
python scripts/ingest_docling.py

# Or individually
python scripts/ingest_docling.py --source commblog
python scripts/ingest_docling.py --source magazine
```

### 3. Clean Dataset

```bash
python scripts/clean_dataset.py

# Or individually
python scripts/clean_dataset.py --source commblog
python scripts/clean_dataset.py --source magazine
```

### 4. Build the RAG Vector Stores

```bash
# CommBlog only
ramalama rag --chunk-size 256 data/cleaned/commblog localhost/fedora-commblog-rag

# Magazine only
ramalama rag --chunk-size 256 data/cleaned/magazine localhost/fedora-magazine-rag

# Combined
ramalama rag --chunk-size 256 data/cleaned localhost/fedora-editorial-rag
```

### 5. Run the Editorial Assistant GUI

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Select the publication in the sidebar,
paste a draft article, and the model flags whether it meets editorial standards.

### 6. Benchmark Models

```bash
python scripts/benchmark.py
```

---

## Models Tested

| Model | Size | Notes |
|-------|------|-------|
| Qwen3 4B | 4B | Fast, recommended default |
| Qwen3 1.7B | 1.7B | Lightweight, good for local |
| Gemma 3 4B | 4B | Strong general performance |
| Granite 7B (IBM) | 7B | Open weights, Fedora-friendly |

---

## Evaluation

Success is measured by workshopping the tool with Fedora Community Blog
and Fedora Magazine editors to determine usefulness for new authors.

---

## Contributing

This project is part of an [Outreachy](https://www.outreachy.org/) internship
with the Fedora Project. Contributions, feedback, and suggestions are welcome!

---

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
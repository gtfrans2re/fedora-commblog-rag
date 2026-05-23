# Blog Draft — fedora-commblog-rag

> **Status:** Draft — work in progress
> **Target publication:** Fedora Community Blog
> **Author:** Francois Gonothi Toure
> **Outreachy cohort:** May–August 2026

---

<!-- EDITOR NOTES (remove before publishing)
- Add featured image before publishing
- Add <!--more--> tag after the intro paragraph
- Ask Michal Konecny to review before submission
- Link to the public repo once finalized
- Add author bio at the bottom
-->

---

# Building an AI Editorial Assistant for the Fedora Community Blog

*How I used RamaLama and RAG to help new authors write better Fedora posts — and what I learned along the way.*

<!--more-->

---

## A Little Context

When I joined the Fedora Project as an Outreachy intern, one of the first things I noticed was how much institutional knowledge lives inside the heads of experienced contributors. The Fedora Community Blog has years of published articles, editorial guidelines, and accumulated editorial wisdom — but for a new author sitting down to write their first post, all of that can feel overwhelming and hard to navigate.

My mini-project set out to tackle that problem: could I build a tool that puts that knowledge to work automatically? Something a new author could use to check their draft before submitting?

The answer, it turns out, is yes — and this post walks through exactly how I did it.

---

## What Is RAG, and Why Does It Matter Here?

RAG stands for **Retrieval-Augmented Generation**. Instead of relying purely on what a language model learned during training, RAG lets the model look things up in a specific document corpus at query time — think of it as giving the model a reference library it can consult before answering.

For this project, that library is the Fedora Community Blog itself: its writing guidelines, editorial standards, and hundreds of past published articles.

When a new author pastes their draft and asks "does this meet CommBlog standards?", the model retrieves the most relevant guidelines and examples, then uses them to give grounded, specific feedback — rather than generic advice.

---

## The Tech Stack

The entire pipeline is built on open-source tools:

- **[RamaLama](https://github.com/containers/ramalama)** — the RAG engine and model runner. RamaLama makes it straightforward to run local language models with a retrieval layer on top.
- **[Docling](https://github.com/DS4SD/docling)** — handles document ingestion. It converts raw HTML articles from the WordPress API into clean, structured Markdown that the RAG pipeline can work with.
- **WordPress REST API** — the data source. The Fedora Community Blog runs on WordPress, and its public REST API makes it easy to programmatically download all published articles.
- **Python** — gluing everything together: fetching, cleaning, ingesting, and benchmarking.

---

## Step 1 — Collecting the Data

The first step was building a corpus. I used the WordPress REST API to fetch every published article from the Fedora Community Blog, saving each one as a structured JSON file.

```bash
python scripts/fetch_articles.py
```

The API returns articles with their full HTML content, metadata (title, date, slug, excerpt), and category tags. One thing I appreciated: using the API rather than scraping preserved the document structure far better than a raw HTML grab would have.

> **Tip for others:** The WordPress REST API has a maximum of 100 results per page, so you need to paginate. The `X-WP-TotalPages` response header tells you how many pages to expect.

---

## Step 2 — Processing with Docling

Raw WordPress HTML isn't immediately useful for a RAG pipeline. I used **Docling** to convert each article's HTML content into clean Markdown, preserving headings, lists, and code blocks while stripping out navigation, footers, and WordPress shortcodes.

```bash
python scripts/ingest_docling.py
```

Each processed article ends up as a Markdown file with a YAML frontmatter header containing its title, date, slug, and source URL — making it easy to trace retrieved content back to the original post.

---

## Step 3 — Cleaning and Quality-Checking the Dataset

Not all articles are created equal. As part of the data preparation step, I ran each cleaned article through a set of automated editorial quality checks — the same checks the RAG model would eventually be asked to perform:

- Does the article have a featured image?
- Does it have a `<!--more-->` tag (required for the excerpt on the blog homepage)?
- Does it have proper headings?
- Is it long enough to be substantive?

```bash
python scripts/clean_dataset.py
```

This step produced a `quality_report.json` that became surprisingly useful on its own: it gave a clear picture of which editorial issues were most common across the entire corpus, which helped inform the RAG system prompt.

---

## Step 4 — Building the RAG Pipeline

With a clean corpus in place, the next step was wiring up RamaLama's RAG capabilities. The key configuration decisions were:

**Chunking strategy:** I settled on a chunk size of 512 tokens with 64-token overlap after experimenting with sizes ranging from 128 to 1024. Smaller chunks retrieved more precisely but sometimes lost context; larger chunks provided more context but retrieved less precisely.

**System prompt:** The model is instructed to act as an editorial assistant — flagging specific issues, referencing relevant guidelines, and being constructive rather than rewriting the draft.

**Embedding model:** I used `nomic-embed-text` for its balance of quality and local performance.

---

## Step 5 — Benchmarking Models

I tested four models against a set of five editorial review prompts:

| Model | Avg Latency | Avg Score | Notes |
|-------|-------------|-----------|-------|
| Qwen 2.5 7B | TBD | TBD | |
| SmolLM2 1.7B | TBD | TBD | |
| Gemma 3 4B | TBD | TBD | |
| Granite 3.3 8B | TBD | TBD | |

> *(Results will be filled in once benchmarking is complete on the GPU1 VM)*

The test prompts covered: tone checking, structure validation, technical accuracy, topic scope, and new author guidance — real scenarios an editorial assistant would need to handle.

---

## What I Learned

**The data cleaning step is underrated.** I expected the Docling ingestion to be the interesting part. It turned out that the quality-checking logic — figuring out what "good" looks like in the corpus — taught me the most about the editorial standards I was trying to encode.

**Chunking matters more than model choice.** At least for this corpus size, the difference between chunk sizes had a bigger impact on retrieval quality than swapping between models. A well-tuned 1.7B model with good chunking outperformed a 7B model with poor chunking.

**RAG is only as good as its corpus.** The model can only retrieve what's in the data. Articles with missing structure (no headings, no `<!--more-->` tag) produced noisier retrievals. Cleaning the corpus first made a measurable difference.

**Open-source tooling has come a long way.** Running this entire pipeline locally — with no external API calls, no data leaving my machine — was entirely feasible thanks to RamaLama, Docling, and the open-weight models available today.

---

## Try It Yourself

The full project is open source under the Apache 2.0 license:

> 🔗 **[github.com/<your-username>/fedora-commblog-rag](https://github.com/gtfrans2re/fedora-commblog-rag)**

To get started:

```bash
git clone https://github.com/gtfrans2re/fedora-commblog-rag.git
cd fedora-commblog-rag
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Fetch, ingest, clean
python scripts/fetch_articles.py
python scripts/ingest_docling.py
python scripts/clean_dataset.py

# Benchmark models
python scripts/benchmark.py
```

If you have feedback — especially if you're a CommBlog or Fedora Magazine editor — I'd love to hear from you on Matrix or in the repo issues.

---

## What's Next

This mini-project was always intended as a stepping stone. The same RAG approach will be applied to a much larger and more complex corpus next: the Fedora RPM packaging guidelines — a 30-year body of technical documentation that packagers navigate daily.

If this small experiment is any indication, there's real potential for RAG-powered tooling to make Fedora's contributor documentation more accessible for everyone.

---

*Francois Gonothi Toure is an Outreachy intern with the Fedora Project (May–August 2026). This post was written as part of the mini-project deliverables for the RamaLama RAG internship track.*
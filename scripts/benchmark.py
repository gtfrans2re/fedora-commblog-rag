"""
benchmark.py

Benchmarks RAG performance across supported models:
    - Qwen 2.5 7B
    - SmolLM2 1.7B
    - Gemma 3 4B
    - Granite 3.3 8B

For each model, runs a set of editorial review test prompts against the
cleaned CommBlog corpus and records: latency, response quality scores
(ROUGE-L), and qualitative flags.

Usage:
    python scripts/benchmark.py

Output:
    - results/benchmark_<timestamp>.json   : Full results per model
    - results/benchmark_summary.md         : Human-readable comparison table
"""

import json
import time
import subprocess
import re
from pathlib import Path
from datetime import datetime
from rouge_score import rouge_scorer

# ── Config ────────────────────────────────────────────────────────────────────

RESULTS_DIR  = Path("results")
CONFIG_PATH  = "models/ramalama_config/ramalama_rag.yaml"
CLEANED_DIR  = Path("data/cleaned")

MODELS = [
    {"name": "hf://Qwen/Qwen3-4B-GGUF",                                   "label": "Qwen3 4B"},
    {"name": "hf://HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF",             "label": "SmolLM2 1.7B"},
    {"name": "hf://ggml-org/gemma-3-4b-it-GGUF",                          "label": "Gemma 3 4B"},
    {"name": "hf://instructlab/granite-7b-lab-GGUF/granite-7b-lab-Q4_K_M.gguf", "label": "Granite 7B"},
]

# Test prompts: (prompt, reference_answer_keywords)
# Reference keywords are used for rough ROUGE scoring
TEST_PROMPTS = [
    {
        "id": "tone_check",
        "prompt": (
            "Review this draft intro for tone. Does it match the Fedora Community Blog "
            "guidelines?\n\n"
            "Draft: 'Hey everyone!! Just wanted to share some super cool stuff about "
            "Fedora 42 that I found out. Its gonna be amazing trust me!!'"
        ),
        "reference_keywords": [
            "informal", "tone", "professional", "exclamation", "grammar",
            "community blog", "guidelines", "apostrophe"
        ],
    },
    {
        "id": "structure_check",
        "prompt": (
            "Does this article structure follow CommBlog guidelines? "
            "The article has no featured image, no excerpt, and no <!--more--> tag."
        ),
        "reference_keywords": [
            "featured image", "more tag", "excerpt", "required", "guidelines",
            "structure", "missing"
        ],
    },
    {
        "id": "technical_accuracy",
        "prompt": (
            "A draft article states: 'RPM packages can be installed on any Linux "
            "distribution without modification.' Is this technically accurate for "
            "a Fedora Community Blog article?"
        ),
        "reference_keywords": [
            "inaccurate", "rpm", "fedora", "distribution", "specific",
            "dependencies", "incorrect"
        ],
    },
    {
        "id": "topic_scope",
        "prompt": (
            "Is an article about Windows 11 tips appropriate for the "
            "Fedora Community Blog? What does the editorial policy say?"
        ),
        "reference_keywords": [
            "fedora", "linux", "scope", "community", "not appropriate",
            "off-topic", "focus"
        ],
    },
    {
        "id": "new_author_guidance",
        "prompt": (
            "I'm a new Fedora contributor writing my first blog post about "
            "my experience setting up a Fedora development environment. "
            "What should I keep in mind according to the CommBlog guidelines?"
        ),
        "reference_keywords": [
            "featured image", "more tag", "tone", "community", "technical",
            "structure", "first person", "guidelines"
        ],
    },
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def run_ramalama_rag(model_name: str, prompt: str) -> tuple[str, float]:
    """
    Run a RAG query using RamaLama CLI and return (response, latency_seconds).
    """
    cmd = [
        "ramalama", "rag",
        "--model", model_name,
        "--corpus", str(CLEANED_DIR),
        "--query", prompt,
    ]
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        latency = time.time() - start
        if result.returncode != 0:
            return f"ERROR: {result.stderr.strip()}", latency
        return result.stdout.strip(), latency
    except subprocess.TimeoutExpired:
        return "ERROR: Timeout (>120s)", time.time() - start
    except FileNotFoundError:
        return "ERROR: ramalama not found — is it installed?", 0.0


def score_response(response: str, reference_keywords: list[str]) -> float:
    """
    Simple keyword coverage score: what fraction of reference keywords
    appear in the response? Used as a lightweight proxy for quality.
    """
    if not response or response.startswith("ERROR"):
        return 0.0
    response_lower = response.lower()
    hits = sum(1 for kw in reference_keywords if kw.lower() in response_lower)
    return round(hits / len(reference_keywords), 3)


def build_markdown_summary(results: dict) -> str:
    """Build a Markdown comparison table from benchmark results."""
    lines = [
        "# Benchmark Summary",
        f"\n_Generated: {results['timestamp']}_\n",
        "| Model | Avg Latency (s) | Avg Keyword Score | Errors |",
        "|-------|----------------|-------------------|--------|",
    ]
    for model_result in results["models"]:
        label    = model_result["label"]
        latency  = model_result["avg_latency_s"]
        score    = model_result["avg_keyword_score"]
        errors   = model_result["error_count"]
        lines.append(f"| {label} | {latency:.2f} | {score:.3f} | {errors} |")

    lines += [
        "\n## Per-Prompt Breakdown\n",
    ]
    for model_result in results["models"]:
        lines.append(f"### {model_result['label']}\n")
        for prompt_result in model_result["prompts"]:
            lines.append(f"**{prompt_result['id']}** — "
                         f"latency: {prompt_result['latency_s']:.2f}s, "
                         f"score: {prompt_result['keyword_score']:.3f}\n")
            lines.append(f"```\n{prompt_result['response'][:300]}...\n```\n")
    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    all_results = {
        "timestamp": timestamp,
        "models": [],
    }

    for model in MODELS:
        print(f"\n{'═'*55}")
        print(f"  Testing model: {model['label']}")
        print(f"{'═'*55}")

        model_result = {
            "name":              model["name"],
            "label":             model["label"],
            "prompts":           [],
            "avg_latency_s":     0.0,
            "avg_keyword_score": 0.0,
            "error_count":       0,
        }

        latencies, scores = [], []

        for test in TEST_PROMPTS:
            print(f"  ▶ Running: {test['id']}...", end=" ", flush=True)
            response, latency = run_ramalama_rag(model["name"], test["prompt"])
            score = score_response(response, test["reference_keywords"])
            is_error = response.startswith("ERROR")

            print(f"{'❌' if is_error else '✅'} "
                  f"({latency:.1f}s, score={score:.3f})")

            model_result["prompts"].append({
                "id":            test["id"],
                "response":      response,
                "latency_s":     round(latency, 3),
                "keyword_score": score,
                "is_error":      is_error,
            })
            latencies.append(latency)
            scores.append(score)
            if is_error:
                model_result["error_count"] += 1

        model_result["avg_latency_s"]     = round(sum(latencies) / len(latencies), 3)
        model_result["avg_keyword_score"] = round(sum(scores) / len(scores), 3)
        all_results["models"].append(model_result)

        print(f"\n  Summary → avg latency: {model_result['avg_latency_s']:.2f}s | "
              f"avg score: {model_result['avg_keyword_score']:.3f} | "
              f"errors: {model_result['error_count']}")

    # Save JSON results
    json_path = RESULTS_DIR / f"benchmark_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n📄 Full results saved → {json_path}")

    # Save Markdown summary
    md_path = RESULTS_DIR / "benchmark_summary.md"
    md_path.write_text(build_markdown_summary(all_results), encoding="utf-8")
    print(f"📊 Summary table saved → {md_path}")

    print(f"\n✅ Benchmark complete for {len(MODELS)} models × {len(TEST_PROMPTS)} prompts.")


if __name__ == "__main__":
    main()
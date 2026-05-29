#!/usr/bin/env bash
#
# review_good_examples.sh
#
# Runs each of the 4 benchmark models against the 5 known "good" Community Blog
# articles, using the RAG editorial assistant prompt, and saves every review
# to data/reviews/FP_CommBlog_Good_Examples_Review/.
#
# Output naming: <model>_<articlekey>.txt   e.g. gemma_f44.txt
#
# Usage (from repo root):
#   bash scripts/review_good_examples.sh
#
# Prerequisites:
#   - ramalama installed, models pulled
#   - the commblog RAG image available (quay.io/gtfrans2re/fedora-commblog-rag)
#   - cleaned articles present in data/cleaned/commblog/

set -u

# ── Config ────────────────────────────────────────────────────────────────────

RAG_IMAGE="quay.io/gtfrans2re/fedora-commblog-rag"
CORPUS_DIR="data/cleaned/commblog"
OUT_DIR="data/reviews/FP_CommBlog_Good_Examples_Review"

# Models: short key -> full ramalama model string
declare -A MODELS=(
  ["gemma"]="hf://bartowski/google_gemma-4-E4B-it-GGUF"
  ["granite"]="hf://ibm-granite/granite-4.0-micro-GGUF"
)

# The 5 good articles: short key -> cleaned markdown filename (no path)
declare -A ARTICLES=(
  ["f44"]="f44-election-nominations-now-open.md"
  ["coc"]="code-of-conduct-report-2025.md"
  ["segfaults"]="throwing-random-arguments-at-system-binaries-real-segfaults-vs-ticket-noise.md"
  ["forge"]="the-forge-is-our-new-home.md"
  ["pagure"]="two-shell-functions-to-simplify-pagure-pull-request-reviews.md"
)

# The editorial review prompt (prepended to each article body)
read -r -d '' PROMPT_HEADER << 'EOF'
You are an editorial assistant for the Fedora Community Blog. Review the
following draft article against the CommBlog editorial guidelines. Check ALL of
the following and report PASS, FAIL, or NEEDS REVIEW on each, then explain briefly:

1. Featured image — is one included or mentioned?
2. Read More tag — is <!--more--> placed after the first paragraph?
3. Tone — is it appropriate for the target audience?
4. Headers — are they used if the article is over 400 words?
5. Tags — are 3-6 appropriate tags suggested?
6. Category — is a single appropriate category suggested?
7. Link text — is 'here' avoided as link text?
8. Key info first — is the main takeaway in the first paragraph?
9. Images — are any images hotlinked rather than uploaded?
10. SEO snippet — is an excerpt/focus keyword suggested?

End with an overall verdict: READY TO PUBLISH or NEEDS REVISION.

--- ARTICLE ---

EOF

# ── Run ───────────────────────────────────────────────────────────────────────

mkdir -p "$OUT_DIR"

total=$(( ${#MODELS[@]} * ${#ARTICLES[@]} ))
count=0

echo "Running $total reviews (${#MODELS[@]} models x ${#ARTICLES[@]} articles)..."
echo "Output dir: $OUT_DIR"
echo

for mkey in "${!MODELS[@]}"; do
  model="${MODELS[$mkey]}"
  for akey in "${!ARTICLES[@]}"; do
    article_file="$CORPUS_DIR/${ARTICLES[$akey]}"
    out_file="$OUT_DIR/${mkey}_${akey}.txt"
    count=$(( count + 1 ))

    printf "[%2d/%2d] %-8s x %-10s -> %s\n" "$count" "$total" "$mkey" "$akey" "$out_file"

    if [[ ! -f "$article_file" ]]; then
      echo "  SKIP: article not found: $article_file"
      echo "ERROR: article file not found: $article_file" > "$out_file"
      continue
    fi

    # Build the full prompt: header + article body
    full_prompt="$(printf '%s\n%s' "$PROMPT_HEADER" "$(cat "$article_file")")"

    # Pipe the prompt into the model via the RAG image, capture the review
    if printf '%s' "$full_prompt" | \
        ramalama run --rag "$RAG_IMAGE" "$model" 2> /dev/null \
        | grep -vE '^[0-9a-f]{64}$' > "$out_file"; then
      echo "  done."
    else
      echo "  WARN: ramalama returned non-zero (see $out_file)"
    fi
  done
done

echo
echo "All reviews complete. Results in: $OUT_DIR"
echo "Files:"
ls -1 "$OUT_DIR"
"""
app.py — Fedora Editorial Assistant

Interactive GUI for reviewing draft articles against the
Fedora Community Blog and Fedora Magazine editorial guidelines
using RamaLama RAG.

Usage:
    streamlit run app.py

Requirements:
    pip install streamlit
    ramalama must be installed and the RAG store(s) built:
        ramalama rag --chunk-size 256 data/cleaned/commblog quay.io/gtfrans2re/fedora-commblog-rag
        ramalama rag --chunk-size 256 data/cleaned/magazine  quay.io/gtfrans2re/fedora-magazine-rag
"""

import subprocess
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Fedora Editorial Assistant",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}
.main-header {
    background: linear-gradient(135deg, #003764 0%, #06b6d4 100%);
    padding: 2rem 2.5rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    color: white;
}
.main-header h1 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.8rem;
    font-weight: 600;
    margin: 0 0 0.4rem 0;
}
.main-header p { font-size: 0.95rem; opacity: 0.85; margin: 0; }
.pub-badge {
    display: inline-block;
    padding: 0.25rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
    margin-right: 0.5rem;
}
.badge-commblog { background: #dbeafe; color: #1e40af; }
.badge-magazine  { background: #fce7f3; color: #9d174d; }
.badge-both      { background: #f3e8ff; color: #6b21a8; }
.result-box {
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    margin-top: 1rem;
    font-size: 0.95rem;
    line-height: 1.7;
    border-left: 5px solid;
}
.result-pass    { background: #f0fdf4; border-color: #22c55e; color: #14532d; }
.result-fail    { background: #fff7ed; border-color: #f97316; color: #7c2d12; }
.result-neutral { background: #f8fafc; border-color: #94a3b8; color: #1e293b; }
.sidebar-section {
    background: #f1f5f9;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    font-size: 0.85rem;
}
.sidebar-section h4 {
    margin: 0 0 0.5rem 0;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #64748b;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────

PUBLICATIONS = {
    "Fedora Community Blog": {
        "key":        "commblog",
        "oci_image":  "quay.io/gtfrans2re/fedora-commblog-rag",
        "corpus_dir": "data/cleaned/commblog",
        "badge":      "badge-commblog",
    },
    "Fedora Magazine": {
        "key":        "magazine",
        "oci_image":  "quay.io/gtfrans2re/fedora-magazine-rag",
        "corpus_dir": "data/cleaned/magazine",
        "badge":      "badge-magazine",
    },
    "Both publications": {
        "key":        "both",
        "oci_image":  "quay.io/gtfrans2re/fedora-editorial-rag",
        "corpus_dir": "data/cleaned",
        "badge":      "badge-both",
    },
}

MODELS = {
    "Qwen3 4B (recommended)": "hf://Qwen/Qwen3-4B-GGUF",
    "Qwen3 1.7B (fastest)":   "hf://Qwen/Qwen3-1.7B-GGUF",
    "Gemma 3 4B":             "hf://ggml-org/gemma-3-4b-it-GGUF",
    "Granite 7B (IBM)":       "hf://instructlab/granite-7b-lab-GGUF/granite-7b-lab-Q4_K_M.gguf",
}

REVIEW_MODES = {
    "Full editorial review":   "full",
    "Tone & structure only":   "tone",
    "Technical accuracy only": "technical",
    "Required elements check": "elements",
}

COMMBLOG_CHECKS = [
    ("Featured image",      "A featured image is recommended"),
    ("Read More tag",       "<!--more--> placed after first paragraph"),
    ("Tone",                "Professional, contributor-focused"),
    ("Headers",             "Used for articles over 400 words"),
    ("Tags",                "3-6 specific, strategic tags"),
    ("Single category",     "One category (+ Events if applicable)"),
    ("No hotlinked images", "All images uploaded to WordPress"),
    ("No 'here' links",     "Avoid 'here' as link text"),
    ("Key info first",      "Main takeaway in the first paragraph"),
    ("Yoast SEO snippet",   "Excerpt/snippet set for social sharing"),
]

MAGAZINE_CHECKS = [
    ("Featured image",      "Required — high quality, relevant"),
    ("Read More tag",       "<!--more--> placed after first paragraph"),
    ("Tone",                "Accessible to a wider Linux/Fedora audience"),
    ("Technical depth",     "Appropriate technical level for the audience"),
    ("Headers",             "Clear structure for longer articles"),
    ("Tags & category",     "Accurate tagging for discoverability"),
    ("License compliance",  "All images properly attributed"),
    ("Yoast SEO snippet",   "Focus keyword and snippet set"),
]

EXAMPLE_GOOD = """Title: F44 Election Nominations Now Open

The Fedora Project is now accepting nominations for the upcoming Fedora Council
and FESCo elections. If you are interested in contributing to Fedora's governance,
this is your chance to get involved.

<!--more-->

Nominations are open until [date]. Any Fedora contributor in good standing is
eligible to run. To nominate yourself or someone else, visit the Fedora Elections
application and follow the instructions.

## Why Run?

Fedora's governing bodies shape the direction of the project. Council members set
strategic goals, while FESCo members guide technical decisions.

## How to Nominate

1. Visit the Fedora Elections app
2. Log in with your Fedora Account
3. Submit a nomination with a brief statement

Questions? Ask in #fedora-elections on Matrix.
"""

EXAMPLE_BAD = """Title: Fedora and CentOS at SCaLE 23x 2026

We had a great time at SCaLE this year! The Fedora and CentOS booths were busy
all weekend and we talked to hundreds of people about open source.

Lots of great conversations about Fedora 42 and the new features coming up.
People were really excited about the improvements to the installer.

Thanks to everyone who stopped by and to all the volunteers who made it happen.
See you next year!
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def build_prompt(article: str, mode: str, pub_key: str, custom_focus: str) -> str:
    pub_label = {
        "commblog": "Fedora Community Blog",
        "magazine":  "Fedora Magazine",
        "both":      "Fedora Community Blog or Fedora Magazine",
    }[pub_key]

    base = (
        f"You are an editorial assistant for the {pub_label}. "
        "Review the following draft article against the editorial guidelines "
        "for this publication.\n\n"
    )

    if mode == "full":
        instructions = (
            "Check ALL of the following and report on each:\n"
            "1. Featured image — is one included or mentioned?\n"
            "2. Read More tag — is <!--more--> placed after the first paragraph?\n"
            "3. Tone — is it appropriate for the target audience?\n"
            "4. Headers — are they used if the article is over 400 words?\n"
            "5. Tags — are 3-6 appropriate tags suggested?\n"
            "6. Category — is a single appropriate category suggested?\n"
            "7. Link text — is 'here' avoided as link text?\n"
            "8. Key info first — is the main takeaway in the first paragraph?\n"
            "9. Images — are any images hotlinked rather than uploaded?\n"
            "10. SEO snippet — is an excerpt/focus keyword suggested?\n\n"
            "For each: state PASS, FAIL, or NEEDS REVIEW, then explain briefly.\n"
            "End with: READY TO PUBLISH or NEEDS REVISION.\n\n"
        )
    elif mode == "tone":
        instructions = (
            "Focus only on tone and structure. Is the writing style appropriate "
            "for the target audience? Are headers used correctly? "
            "Is the key takeaway in the first paragraph? "
            "Give specific, actionable feedback.\n\n"
        )
    elif mode == "technical":
        instructions = (
            "Focus only on technical accuracy. Are the technical claims correct "
            "for a Fedora/Linux context? Flag anything inaccurate or outdated.\n\n"
        )
    elif mode == "elements":
        instructions = (
            "Check only the required structural elements:\n"
            "1. Featured image present?\n"
            "2. <!--more--> Read More tag present?\n"
            "3. At least one header (for articles over 400 words)?\n"
            "4. 3-6 tags suggested?\n"
            "5. Category assigned?\n"
            "State PASS or FAIL for each.\n\n"
        )

    if custom_focus.strip():
        instructions += f"Additional focus: {custom_focus.strip()}\n\n"

    return base + instructions + f"--- ARTICLE ---\n\n{article.strip()}"


def run_rag_query(model_id: str, prompt: str, pub: dict, use_oci: bool) -> str:
    if use_oci:
        cmd = ["ramalama", "run", "--rag", pub["oci_image"], model_id]
    else:
        cmd = ["ramalama", "run", "--nocontainer", "--rag", pub["corpus_dir"], model_id]

    result = subprocess.run(
        cmd, input=prompt, capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        return f"ERROR: {result.stderr.strip()}"
    return result.stdout.strip()


def detect_verdict(response: str) -> str:
    r = response.upper()
    if "READY TO PUBLISH" in r:
        return "pass"
    if "NEEDS REVISION" in r or "FAIL" in r:
        return "fail"
    return "neutral"


def count_words(text: str) -> int:
    return len(text.split())


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style='font-family: IBM Plex Mono, monospace; font-size: 1rem;
                font-weight: 600; color: #003764; margin-bottom: 1.2rem;'>
        Fedora Editorial RAG
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Publication**")
    pub_label = st.selectbox(
        "publication",
        list(PUBLICATIONS.keys()),
        label_visibility="collapsed",
    )
    pub = PUBLICATIONS[pub_label]

    st.markdown("**Model**")
    model_label = st.selectbox(
        "model",
        list(MODELS.keys()),
        label_visibility="collapsed",
    )
    model_id = MODELS[model_label]

    st.markdown("**Review Mode**")
    review_label = st.selectbox(
        "review mode",
        list(REVIEW_MODES.keys()),
        label_visibility="collapsed",
    )
    review_mode = REVIEW_MODES[review_label]

    st.markdown("**Custom Focus** *(optional)*")
    custom_focus = st.text_input(
        "custom focus",
        placeholder="e.g. check for inclusive language",
        label_visibility="collapsed",
    )

    use_oci = st.toggle(
        "Use OCI vector store",
        value=True,
        help="Use the pre-built RAG image. Disable for ad-hoc mode (slower).",
    )

    st.divider()

    checks = MAGAZINE_CHECKS if pub["key"] == "magazine" else COMMBLOG_CHECKS
    pub_name = pub_label if pub["key"] != "both" else "CommBlog"
    st.markdown(f"**{pub_name} Checklist**")
    st.markdown(
        "<div class='sidebar-section'>" +
        "".join(
            f"<div style='margin-bottom:0.4rem;'>&#x25A1; <b>{name}</b><br>"
            f"<span style='color:#64748b;font-size:0.8rem'>{desc}</span></div>"
            for name, desc in checks
        ) +
        "</div>",
        unsafe_allow_html=True,
    )

    st.divider()
    st.caption(
        f"OCI image: `{pub['oci_image']}`  \n"
        f"Corpus: `{pub['corpus_dir']}`"
    )

# ── Main ──────────────────────────────────────────────────────────────────────

badge_html = f"<span class='pub-badge {pub['badge']}'>{pub_label}</span>"

st.markdown(f"""
<div class="main-header">
    <h1>Fedora Editorial Assistant</h1>
    <p>
        {badge_html}
        Paste a draft article and the RAG model will review it against
        the Fedora editorial guidelines and flag any issues.
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([3, 2], gap="large")

with col1:
    st.markdown("**Draft Article**")

    tab_paste, tab_good, tab_bad = st.tabs([
        "Paste your draft", "Load good example", "Load bad example"
    ])

    with tab_paste:
        article_input = st.text_area(
            "article",
            height=420,
            placeholder=(
                "Paste your draft article here — include the title, body, "
                "and any metadata (tags, category, excerpt)..."
            ),
            label_visibility="collapsed",
        )

    with tab_good:
        st.caption("Known good article — should pass all editorial checks.")
        article_input_good = st.text_area(
            "good example",
            value=EXAMPLE_GOOD,
            height=360,
            label_visibility="collapsed",
        )
        article_input = article_input_good

    with tab_bad:
        st.caption(
            "Known bad article — missing featured image and `<!--more-->` tag."
        )
        article_input_bad = st.text_area(
            "bad example",
            value=EXAMPLE_BAD,
            height=360,
            label_visibility="collapsed",
        )
        article_input = article_input_bad

    word_count = count_words(article_input) if article_input.strip() else 0
    st.caption(f"Word count: **{word_count}** words")

    run_btn = st.button(
        "Review Article",
        type="primary",
        use_container_width=True,
        disabled=not article_input.strip(),
    )

with col2:
    st.markdown("**Review Result**")

    if "last_response" not in st.session_state:
        st.markdown("""
        <div class="result-box result-neutral">
            The review result will appear here after you click
            <strong>Review Article</strong>.
        </div>
        """, unsafe_allow_html=True)
    else:
        response  = st.session_state["last_response"]
        verdict   = st.session_state["last_verdict"]
        css_class = {"pass": "result-pass", "fail": "result-fail", "neutral": "result-neutral"}[verdict]
        label     = {"pass": "READY TO PUBLISH", "fail": "NEEDS REVISION", "neutral": "REVIEW RESPONSE"}[verdict]
        st.markdown(
            f"<div class='result-box {css_class}'>"
            f"<strong>{label}</strong><br><br>"
            f"{response.replace(chr(10), '<br>')}"
            f"</div>",
            unsafe_allow_html=True,
        )
        if verdict != "neutral":
            st.download_button(
                label="Download review as .txt",
                data=response,
                file_name="editorial_review.txt",
                mime="text/plain",
                use_container_width=True,
            )

# ── Run review ────────────────────────────────────────────────────────────────

if run_btn and article_input.strip():
    prompt = build_prompt(article_input, review_mode, pub["key"], custom_focus)
    with col2:
        with st.spinner(f"Reviewing with {model_label}..."):
            response = run_rag_query(model_id, prompt, pub, use_oci)

        verdict = detect_verdict(response)
        st.session_state["last_response"] = response
        st.session_state["last_verdict"]  = verdict

        css_class = {"pass": "result-pass", "fail": "result-fail", "neutral": "result-neutral"}[verdict]
        label     = {"pass": "READY TO PUBLISH", "fail": "NEEDS REVISION", "neutral": "REVIEW RESPONSE"}[verdict]
        st.markdown(
            f"<div class='result-box {css_class}'>"
            f"<strong>{label}</strong><br><br>"
            f"{response.replace(chr(10), '<br>')}"
            f"</div>",
            unsafe_allow_html=True,
        )
        if verdict != "neutral":
            st.download_button(
                label="Download review as .txt",
                data=response,
                file_name="editorial_review.txt",
                mime="text/plain",
                use_container_width=True,
            )

# ── Footer ────────────────────────────────────────────────────────────────────

st.divider()
st.caption(
    "Fedora Editorial RAG — Outreachy mini-project · "
    "[GitHub](https://github.com/gtfrans2re/fedora-commblog-rag) · "
    "Apache 2.0"
)
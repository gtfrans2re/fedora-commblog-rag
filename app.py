"""
app.py — Fedora CommBlog Editorial Assistant

Interactive GUI for reviewing draft articles against the
Fedora Community Blog editorial guidelines using RamaLama RAG.

Usage:
    streamlit run app.py

Requirements:
    pip install streamlit
    ramalama must be installed and the RAG store built:
        ramalama rag --chunk-size 256 data/cleaned localhost/fedora-commblog-rag
"""

import subprocess
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CommBlog Editorial Assistant",
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

/* Header */
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
    letter-spacing: -0.5px;
}
.main-header p {
    font-size: 0.95rem;
    opacity: 0.85;
    margin: 0;
}

/* Result boxes */
.result-box {
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    margin-top: 1rem;
    font-size: 0.95rem;
    line-height: 1.7;
    border-left: 5px solid;
}
.result-pass {
    background: #f0fdf4;
    border-color: #22c55e;
    color: #14532d;
}
.result-fail {
    background: #fff7ed;
    border-color: #f97316;
    color: #7c2d12;
}
.result-neutral {
    background: #f8fafc;
    border-color: #94a3b8;
    color: #1e293b;
}

/* Check badges */
.badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 0.2rem 0.2rem 0.2rem 0;
    font-family: 'IBM Plex Mono', monospace;
}
.badge-pass { background: #dcfce7; color: #166534; }
.badge-fail { background: #fee2e2; color: #991b1b; }
.badge-warn { background: #fef9c3; color: #854d0e; }

/* Sidebar */
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
    font-size: 0.8rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Fedora blue accent */
.fedora-accent { color: #003764; font-weight: 600; }

/* Spinner override */
.stSpinner > div { border-top-color: #003764 !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────

RAG_IMAGE  = "localhost/fedora-commblog-rag"
CORPUS_DIR = "data/cleaned"

MODELS = {
    "Qwen3 4B (recommended)":    "hf://Qwen/Qwen3-4B-GGUF",
    "Qwen3 1.7B (fastest)":      "hf://Qwen/Qwen3-1.7B-GGUF",
    "Gemma 3 4B":                "hf://ggml-org/gemma-3-4b-it-GGUF",
    "Granite 7B (IBM)":          "hf://instructlab/granite-7b-lab-GGUF/granite-7b-lab-Q4_K_M.gguf",
}

REVIEW_MODES = {
    "Full editorial review":     "full",
    "Tone & structure only":     "tone",
    "Technical accuracy only":   "technical",
    "Required elements check":   "elements",
}

GUIDELINES_CHECKLIST = [
    ("Featured image",        "Does the article have a featured image?"),
    ("Read More tag",         "Is there a <!--more--> tag after the first paragraph?"),
    ("Tone",                  "Is the tone professional and appropriate for Fedora contributors?"),
    ("Headers",               "Are headers used for articles over 400 words?"),
    ("Tags",                  "Are between 3 and 6 tags used?"),
    ("Single category",       "Does the article have a single appropriate category?"),
    ("No hotlinked images",   "Are all images uploaded to WordPress (not hotlinked)?"),
    ("No 'here' links",       "Is 'here' avoided as link text?"),
    ("Important info first",  "Is the key takeaway in the first paragraph?"),
    ("Excerpt/snippet set",   "Is the Yoast SEO snippet/excerpt set?"),
]

EXAMPLE_GOOD = """Title: F44 Election Nominations Now Open

The Fedora Project is now accepting nominations for the upcoming Fedora Council and FESCo elections. If you are interested in contributing to Fedora's governance, this is your chance to get involved.

<!--more-->

Nominations are open from now until [date]. Any Fedora contributor in good standing is eligible to run. To nominate yourself or someone else, visit the Fedora Elections application and follow the instructions.

## Why Run?

Fedora's governing bodies shape the direction of the project. Council members set strategic goals, while FESCo members guide technical decisions. Both roles are critical to keeping Fedora healthy and moving forward.

## How to Nominate

1. Visit the Fedora Elections app
2. Log in with your Fedora Account
3. Submit a nomination with a brief statement

Questions? Ask in #fedora-elections on Matrix.
"""

EXAMPLE_BAD = """Title: Fedora and CentOS at SCaLE 23x 2026

We had a great time at SCaLE this year! The Fedora and CentOS booths were busy all weekend and we talked to hundreds of people about open source.

Lots of great conversations about Fedora 42 and the new features coming up. People were really excited about the improvements to the installer and the new default apps.

Thanks to everyone who stopped by and to all the volunteers who made it happen. See you next year!
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def build_prompt(article: str, mode: str, custom_focus: str) -> str:
    base = (
        "You are an editorial assistant for the Fedora Community Blog. "
        "Review the following draft article against the CommBlog editorial guidelines.\n\n"
    )

    if mode == "full":
        instructions = (
            "Check ALL of the following and report on each one:\n"
            "1. Featured image — is one included or mentioned?\n"
            "2. Read More tag — is <!--more--> placed after the first paragraph?\n"
            "3. Tone — is it professional and appropriate for Fedora contributors?\n"
            "4. Headers — are they used if the article is over 400 words?\n"
            "5. Tags — are between 3 and 6 appropriate tags suggested?\n"
            "6. Category — is a single appropriate category suggested?\n"
            "7. Link text — is 'here' avoided as link text?\n"
            "8. Key info first — is the main takeaway in the first paragraph?\n"
            "9. Images — are any images hotlinked (not uploaded to WordPress)?\n"
            "10. Yoast snippet — is an SEO excerpt suggested?\n\n"
            "For each point: state PASS, FAIL, or NEEDS REVIEW, then explain briefly.\n"
            "End with an overall verdict: READY TO PUBLISH or NEEDS REVISION.\n\n"
        )
    elif mode == "tone":
        instructions = (
            "Focus only on tone and structure. Is the writing style professional "
            "and appropriate for Fedora contributors? Are headers used correctly? "
            "Is the key takeaway in the first paragraph? "
            "Give specific, actionable feedback.\n\n"
        )
    elif mode == "technical":
        instructions = (
            "Focus only on technical accuracy. Are the technical claims correct "
            "for a Fedora/Linux context? Flag anything that seems inaccurate, "
            "outdated, or that needs a technical review.\n\n"
        )
    elif mode == "elements":
        instructions = (
            "Check only the required structural elements:\n"
            "1. Is there a featured image?\n"
            "2. Is there a <!--more--> Read More tag?\n"
            "3. Is there at least one header (for articles over 400 words)?\n"
            "4. Are 3-6 tags suggested?\n"
            "5. Is a category assigned?\n"
            "State PASS or FAIL for each.\n\n"
        )

    if custom_focus.strip():
        instructions += f"Additional focus area: {custom_focus.strip()}\n\n"

    return base + instructions + f"--- ARTICLE ---\n\n{article.strip()}"


def run_rag_query(model_id: str, prompt: str, use_oci: bool) -> str:
    if use_oci:
        cmd = ["ramalama", "run", "--rag", RAG_IMAGE, model_id]
        result = subprocess.run(
            cmd, input=prompt, capture_output=True, text=True, timeout=300
        )
    else:
        cmd = ["ramalama", "run", "--nocontainer", "--rag", CORPUS_DIR, model_id]
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
                font-weight: 600; color: #003764; margin-bottom: 1rem;'>
        CommBlog RAG
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Model**")
    model_label = st.selectbox(
        "Select model",
        list(MODELS.keys()),
        label_visibility="collapsed",
    )
    model_id = MODELS[model_label]

    st.markdown("**Review Mode**")
    review_label = st.selectbox(
        "Select review mode",
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
        help=f"Use the pre-built RAG image ({RAG_IMAGE}). Faster and more accurate. "
             f"Disable to use ad-hoc mode directly against data/cleaned/.",
    )

    st.divider()

    st.markdown("**Guidelines Checklist**")
    st.markdown(
        "<div class='sidebar-section'>" +
        "".join(
            f"<div style='margin-bottom:0.4rem;'>&#x25A1; <b>{name}</b><br>"
            f"<span style='color:#64748b;font-size:0.8rem'>{desc}</span></div>"
            for name, desc in GUIDELINES_CHECKLIST
        ) +
        "</div>",
        unsafe_allow_html=True,
    )

    st.divider()
    st.caption(
        "RAG image: `localhost/fedora-commblog-rag`  \n"
        "Corpus: `data/cleaned/`  \n"
        "Guidelines: `data/guidelines/commblog_guidelines.md`"
    )

# ── Main ──────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <h1>Fedora CommBlog Editorial Assistant</h1>
    <p>
        Paste a draft article below. The RAG model will review it against the
        Fedora Community Blog editorial guidelines and flag any issues.
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
                "and any metadata you have (tags, category, excerpt)..."
            ),
            label_visibility="collapsed",
        )

    with tab_good:
        st.caption(
            "Known good article — should pass all editorial checks.  \n"
            "[F44 Election Nominations Now Open]"
            "(https://communityblog.fedoraproject.org/f44-election-nominations-now-open/)"
        )
        if st.button("Load good example", use_container_width=True):
            st.session_state["loaded_example"] = EXAMPLE_GOOD
        article_input_good = st.text_area(
            "good example",
            value=st.session_state.get("loaded_example", EXAMPLE_GOOD),
            height=360,
            label_visibility="collapsed",
        )
        article_input = article_input_good

    with tab_bad:
        st.caption(
            "Known bad article — missing featured image and `<!--more-->` tag.  \n"
            "[Fedora and CentOS at SCaLE 23x]"
            "(https://communityblog.fedoraproject.org/fedora-and-centos-scale-23x-2026/)"
        )
        article_input_bad = st.text_area(
            "bad example",
            value=EXAMPLE_BAD,
            height=360,
            label_visibility="collapsed",
        )
        if tab_bad:
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
        css_class = {
            "pass":    "result-pass",
            "fail":    "result-fail",
            "neutral": "result-neutral",
        }[verdict]
        verdict_label = {
            "pass":    "READY TO PUBLISH",
            "fail":    "NEEDS REVISION",
            "neutral": "REVIEW RESPONSE",
        }[verdict]

        st.markdown(
            f"<div class='result-box {css_class}'>"
            f"<strong>{verdict_label}</strong><br><br>"
            f"{response.replace(chr(10), '<br>')}"
            f"</div>",
            unsafe_allow_html=True,
        )

        if verdict != "neutral":
            st.download_button(
                label="Download review as .txt",
                data=response,
                file_name="commblog_review.txt",
                mime="text/plain",
                use_container_width=True,
            )

# ── Run review ────────────────────────────────────────────────────────────────

if run_btn and article_input.strip():
    prompt = build_prompt(article_input, review_mode, custom_focus)

    with col2:
        with st.spinner(f"Reviewing with {model_label}..."):
            response = run_rag_query(model_id, prompt, use_oci)

        verdict = detect_verdict(response)
        st.session_state["last_response"] = response
        st.session_state["last_verdict"]  = verdict

        css_class = {
            "pass":    "result-pass",
            "fail":    "result-fail",
            "neutral": "result-neutral",
        }[verdict]
        verdict_label = {
            "pass":    "READY TO PUBLISH",
            "fail":    "NEEDS REVISION",
            "neutral": "REVIEW RESPONSE",
        }[verdict]

        st.markdown(
            f"<div class='result-box {css_class}'>"
            f"<strong>{verdict_label}</strong><br><br>"
            f"{response.replace(chr(10), '<br>')}"
            f"</div>",
            unsafe_allow_html=True,
        )

        if verdict != "neutral":
            st.download_button(
                label="Download review as .txt",
                data=response,
                file_name="commblog_review.txt",
                mime="text/plain",
                use_container_width=True,
            )

# ── Footer ────────────────────────────────────────────────────────────────────

st.divider()
st.caption(
    "Fedora CommBlog RAG — Outreachy mini-project · "
    "[GitHub](https://github.com/gtfrans2re/fedora-commblog-rag) · "
    "Apache 2.0"
)
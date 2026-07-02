from myapp import app
import os
import re
import numpy as np
import pandas as pd
from openai import OpenAI
from flask_login import current_user
from myapp.routes.apps._utils import make_except_toast
from myapp.routes.apps._embedding import get_model, encode_query

# BM25 is optional — if rank_bm25 isn't installed we fall back to semantic-only
# retrieval (still fully functional). Install with: pip install rank_bm25
try:
    from rank_bm25 import BM25Okapi
    _BM25_OK = True
except Exception:
    _BM25_OK = False


PYFLASKI_VERSION = str(os.environ.get("PYFLASKI_VERSION", ""))

# ── jawm chunk store (two files built by jawm_assist_bot/build_chunks_sectioned.py) ──
path_to_files = "/flaski_private/jawmbot/"
CHUNKS_FILE = f"{path_to_files}chunks.parquet"          # one row per doc/code chunk
EMB_FILE    = f"{path_to_files}chunk_embeddings.npy"    # (N, 1024) L2-normalized

# Shared BGE model + query-prefix contract live in _embedding (one instance/process).
# Chunks were embedded prefix-free at build time; encode_query() prefixes queries.

# Retrieval tuning (see the smoke-test findings): main jawm docs are the source of
# truth, so nudge them up; for "how do I" questions prefer docs over implementation
# code. Bonuses are on the RRF scale (~0.016 per rank-0 hit).
IS_MAIN_BONUS = 0.004
DOC_BONUS     = 0.012
HOWTO_RE = re.compile(
    r"\b(how (do|can|would|should) i|how to|run|install|set ?up|configure|use|usage|"
    r"example|get(ting)? started|tutorial|guide|steps?|command)\b", re.I)

_tok = lambda t: re.findall(r"[a-z0-9]+", t.lower())     # BM25 tokenizer (query + corpus)

chunks_df = None
embeddings = None
embedding_model = None
bm25 = None
STORE_LOADED = False

try:
    if os.path.exists(CHUNKS_FILE) and os.path.exists(EMB_FILE):
        chunks_df = pd.read_parquet(CHUNKS_FILE).reset_index(drop=True)
        for col in ("repo", "file_path", "kind", "heading_or_symbol", "text", "url", "title"):
            if col in chunks_df.columns:
                chunks_df[col] = chunks_df[col].fillna("")
        chunks_df["is_main"] = (chunks_df["is_main"].fillna(False).astype(bool)
                                if "is_main" in chunks_df.columns else False)

        embeddings = np.load(EMB_FILE).astype(np.float32)         # already normalized
        embedding_model = get_model()                             # shared instance (once/process)

        if _BM25_OK:
            bm25 = BM25Okapi([_tok(t) for t in chunks_df["text"]])   # exact-term recall

        STORE_LOADED = len(chunks_df) == embeddings.shape[0]
except Exception as _store_err:
    # Never let a missing/corrupt store or model-load failure break app import.
    import logging
    logging.getLogger(__name__).warning("jawm chunk store failed to load: %s", _store_err)
    chunks_df = embeddings = embedding_model = bm25 = None
    STORE_LOADED = False

# ── LLM client ─────────────────────────────────────────────
api_key = app.config.get("MAGE_LLM_KEY", "sk-hamin-c39396ea2ea7c856263b89b11769d0b7281a42020e31714f")
base_url = app.config.get("MAGE_LLM_URL", "https://gpu.bioinformatics.studio/v1")

client = OpenAI(
    api_key = api_key,
    base_url = base_url,
    max_retries = 0,        # timeout is a hard ceiling (no hidden 3x retry multiplier)
)

# Model served by the LLM gateway (a valid id from `client.models.list()`).
LLM_MODEL = "gemma4-31b"

SYSTEM_PROMPT = (
    "You are the jawm AssistBot — an assistant for jawm, a Python-based workflow "
    "orchestrator. Answer using the provided excerpts from jawm's documentation and "
    "source code. The main jawm documentation is authoritative; the pipeline repos "
    "(named jawm_*) are usage examples, not the spec. When you use a source, cite its "
    "link so the user can open the exact docs page or file, and give runnable examples "
    "where helpful. If the provided material doesn't cover the question, say so plainly "
    "— you may add well-established general knowledge, but never invent jawm features, "
    "flags, or citations. If the user references another workflow manager (Nextflow, "
    "Snakemake, etc.), map the concept to the jawm equivalent using the provided "
    "material. Take the conversation history into account; for greetings, respond naturally."
)

USER_TEMPLATE = (
    "Here are relevant excerpts from jawm's docs and code (the user cannot see these):\n\n"
    "{context}\n\n"
    "Answer the QUERY below using these excerpts and the conversation so far, citing the "
    "sources (with their links) you draw on. If they aren't relevant to the QUERY (e.g. a "
    "greeting), just answer normally.\n\n"
    "QUERY: {query}"
)


# ── Retrieval ──────────────────────────────────────────────
def _semantic_scores(query):
    qv = encode_query(query).astype(np.float32)   # shared BGE encode (prefix + normalize)
    return embeddings @ qv                       # cosine vs every chunk


def _rrf(rankings, k=60):
    """Reciprocal-rank fusion of several ranked index lists -> {idx: score}."""
    fused = {}
    for ranked in rankings:
        for rank, idx in enumerate(ranked):
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (k + rank)
    return fused


def retrieve(query, top_k=8):
    """Top-k chunk rows for the query: semantic + BM25 fused (RRF), with a small
    main-docs boost and a doc-over-code boost for how-to questions, then deduped so
    the LLM gets distinct sources (not multiple slices of the same section)."""
    sem = _semantic_scores(query)
    sem_rank = np.argsort(-sem)
    if bm25 is not None:
        bm_rank = np.argsort(-np.asarray(bm25.get_scores(_tok(query))))
        fused = _rrf([list(sem_rank[:60]), list(bm_rank[:60])])
    else:
        fused = {int(i): 1.0 / (60 + r) for r, i in enumerate(sem_rank[:60])}

    how_to = bool(HOWTO_RE.search(query))
    for i in list(fused):
        row = chunks_df.iloc[i]
        if row["is_main"]:
            fused[i] += IS_MAIN_BONUS
        if how_to and row["kind"] == "doc":
            fused[i] += DOC_BONUS
    order = sorted(fused, key=lambda i: -fused[i])

    seen, picked = set(), []
    for i in order:
        row = chunks_df.iloc[i]
        key = (row["repo"], row["file_path"], row["heading_or_symbol"])
        if key in seen:                            # dedup near-duplicate slices
            continue
        seen.add(key)
        picked.append(i)
        if len(picked) >= top_k:
            break
    return chunks_df.iloc[picked]


def _chunk_block(row):
    return (
        f"Source: {row['title']}  [{row['kind']}]\n"
        f"Link: {row['url']}\n"
        f"{row['text']}\n---"
    )


def _condense_query(query, conversation_history):
    """Rewrite a follow-up into a standalone search query using recent turns, so
    retrieval works on multi-turn questions ("how do I run it", "what about on
    kubernetes"). Returns the query unchanged on the first turn or if rewriting fails."""
    prior = [m for m in conversation_history if m.get("role") in ("user", "assistant")]
    if not prior:
        return query
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in prior[-4:])
    prompt = (
        "Rewrite the follow-up question into a standalone search query that includes any "
        "topic, command, function, or concept implied by the conversation. Keep it concise. "
        "Output ONLY the rewritten query, nothing else.\n\n"
        f"Conversation:\n{convo}\n\nFollow-up: {query}\n\nStandalone query:"
    )
    try:
        r = client.chat.completions.create(
            model=LLM_MODEL, messages=[{"role": "user", "content": prompt}],
            temperature=0, max_tokens=80, timeout=30,
        )
        rewritten = (r.choices[0].message.content or "").strip()
        return rewritten or query
    except Exception:
        return query


def chat_jawm(query, conversation_history=None, model=None, top_k=8):
    """Retrieve relevant jawm docs/code and answer the query.
    Returns (response_text, conversation_history)."""
    model = model or LLM_MODEL
    if not query or not query.strip():
        return "You may have forgotten to input your question 🤔", conversation_history

    if not STORE_LOADED:
        return ("The jawm knowledge base isn't available right now, so I can't look "
                "anything up. Please try again later."), conversation_history

    if not conversation_history or conversation_history[0].get("role") != "system":
        conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]

    try:
        # History-aware retrieval: rewrite follow-ups into a standalone query first.
        search_query = _condense_query(query, conversation_history)
        hits = retrieve(search_query, top_k=top_k)
        context = "\n\n".join(_chunk_block(row) for _, row in hits.iterrows())

        # Always use our own system prompt + the last few user/assistant turns.
        recent = [m for m in conversation_history if m.get("role") in ("user", "assistant")]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + recent[-6:]
        messages.append({"role": "user",
                         "content": USER_TEMPLATE.format(context=context, query=query)})

        chat_completion = client.chat.completions.create(
            messages=messages, model=model, timeout=90,
        )
        response = chat_completion.choices[0].message.content

        conversation_history.append({"role": "user", "content": query})
        conversation_history.append({"role": "assistant", "content": response})
        return response, conversation_history

    except Exception as e:
        make_except_toast("There was a problem with the jawm assistant:", "jawmbot_issue", e, current_user, "jawmbot")
        return ("Sorry — something went wrong while answering your question. "
                "Please try again in a moment."), conversation_history

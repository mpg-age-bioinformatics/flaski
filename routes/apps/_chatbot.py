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

# ── Paper store (the two files built by fetch_papers/build_store_sectioned.py) ──
path_to_files = "/flaski_private/chatbot/"
PAPERS_FILE = f"{path_to_files}papers.parquet"           # one row per paper
EMB_FILE    = f"{path_to_files}abstract_embeddings.npy"  # (N, 1024) L2-normalized

# The BGE model + query-prefix contract live in the shared _embedding module so
# every retrieval app loads a single instance. Passages were embedded prefix-free
# at build time; encode_query() applies the query prefix + normalization to match.

papers_df = None
embeddings = None
embedding_model = None
bm25 = None
STORE_LOADED = False

try:
    if os.path.exists(PAPERS_FILE) and os.path.exists(EMB_FILE):
        papers_df = pd.read_parquet(PAPERS_FILE).reset_index(drop=True)
        for col in ("title", "authors", "journal", "year", "abstract", "web_link", "full_text"):
            if col in papers_df.columns:
                papers_df[col] = papers_df[col].fillna("")
        papers_df["_authors_lc"] = papers_df["authors"].str.lower()   # for author filtering

        embeddings = np.load(EMB_FILE).astype(np.float32)             # already normalized
        embedding_model = get_model()                                 # shared instance (loaded once per process)

        if _BM25_OK:
            # Token corpus for exact-term recall: prefer full text, fall back to abstract.
            _tok = lambda t: re.findall(r"[a-z0-9]+", t.lower())
            _corpus = [_tok(ft if ft else ab)
                       for ft, ab in zip(papers_df["full_text"], papers_df["abstract"])]
            bm25 = BM25Okapi(_corpus)

        STORE_LOADED = len(papers_df) == embeddings.shape[0]
except Exception as _store_err:
    # Never let a missing/corrupt store or a model-load failure break app import.
    # The chatbot just reports itself unavailable (see the STORE_LOADED guard in
    # chat_age_high); the rest of flaski is unaffected.
    import logging
    logging.getLogger(__name__).warning("Chatbot paper store failed to load: %s", _store_err)
    papers_df = embeddings = embedding_model = bm25 = None
    STORE_LOADED = False

# ── LLM client ─────────────────────────────────────────────

api_key = app.config.get("MAGE_LLM_KEY", "")
base_url = app.config.get("MAGE_LLM_URL", "")

client = OpenAI(
    api_key = api_key,
    base_url = base_url,
    max_retries = 0,        # timeout is a hard ceiling (no hidden 3x retry multiplier)
)

# Model served by the LLM gateway. Must be a valid id from `client.models.list()`
# (run /v1/models on the key). Update here if the gateway's offering changes.
LLM_MODEL = "gemma4-31b"

SYSTEM_PROMPT = (
    "You are an AI assistant for the Max Planck Institute for Biology of Ageing (MPI-AGE), "
    "specializing in ageing biology. You have access to the institute's published research "
    "(each item has a title, authors, journal/year, link, and abstract — some include a "
    "full-text excerpt). Ground your answers primarily in this research, and when you draw on a "
    "paper, mention its title and link so the user can follow up. "
    "Always refer to your knowledge source as 'the institute's publications' or 'MPI-AGE "
    "research' — never as 'the provided context', 'the research materials provided', or anything "
    "implying the user gave you documents (they did not). If the institute's publications don't "
    "cover the question, say so naturally — e.g. 'The institute's publications don't seem to "
    "cover this, but in general…' — and you may then answer from well-established general "
    "knowledge, keeping a rigorous scientific perspective and never inventing citations. Take the "
    "full conversation history into account and avoid repeating yourself. For greetings or small "
    "talk, respond naturally."
)

USER_TEMPLATE = (
    "Here are relevant excerpts from the institute's publications (the user cannot see these):\n\n"
    "{context}\n\n"
    "Answer the QUERY below using these publications and the conversation so far, citing the "
    "papers (title + link) you draw on. If they aren't relevant to the QUERY (e.g. a greeting), "
    "just answer normally.\n\n"
    "QUERY: {query}"
)

# Queries that signal the user wants depth -> include full-text excerpts of the top hits.
DEPTH_RE = re.compile(
    r"\b(in detail|detailed|method|methodolog|how did|how was|how were|results?|findings?|"
    r"in depth|deep[- ]?dive|elaborate|full text|step by step|specifically|mechanism)\b", re.I)


# ── Author handling ────────────────────────────────────────
# Natural-language variants -> the "Lastname Initials" form used in papers.parquet.
AUTHOR_VARIANTS = {
    ("adam antebi", "antebi adam"): "Antebi A",
    ("joris deelen", "deelen joris"): "Deelen J",
    ("constantinos demetriades", "demetriades"): "Demetriades C",
    ("martin denzel", "denzel martin"): "Denzel MS",
    ("zak frentz", "zachary frentz", "frentz"): "Frentz Z",
    ("martin graef", "graef martin"): "Graef M",
    ("ina huppertz", "huppertz ina"): "Huppertz I",
    ("ron jachimowicz", "jachimowicz ron", "ron d jachimowicz"): "Jachimowicz RD",
    ("thomas langer", "langer thomas"): "Langer T",
    ("nils-göran larsson", "nils-goran larsson", "larsson"): "Larsson NG",
    ("ivan matic", "matic ivan"): "Matic I",
    ("stephanie panier", "panier stephanie"): "Panier S",
    ("linda partridge", "partridge linda"): "Partridge L",
    ("lena pernas", "pernas lena"): "Pernas L",
    ("anne schaefer", "schaefer anne"): "Schaefer A",
    ("james stewart", "jim stewart", "stewart"): "Stewart JB",
    ("peter tessarz", "tessarz peter"): "Tessarz P",
    ("dario valenzano", "riccardo valenzano", "dario riccardo valenzano"): "Valenzano DR",
    ("sara wickström", "sara wickstrom", "wickström", "wickstrom"): "Wickstrom SA",
    ("hannah scheiblich", "scheiblich"): "Scheiblich H",
    ("hans-georg sprenger", "sprenger"): "Sprenger HG",
    ("eline slagboom", "pe slagboom", "slagboom"): "Slagboom PE",
    ("alexander tarakhovsky", "tarakhovsky"): "Tarakhovsky A",
    ("stephanie fernandes", "fernandes"): "Fernandes SA",
}
# Lookup from any name form -> the "Lastname Initials" string used in
# papers.parquet. Built from the variants above PLUS each canonical name's bare
# surname and canonical form, so "fernandes", "stephanie fernandes", and
# "Fernandes SA" all resolve — with or without a "papers by…" trigger phrase.
_NAME_LOOKUP = {}
for _variants, _canon in AUTHOR_VARIANTS.items():
    for _v in _variants:
        _NAME_LOOKUP[_v.lower()] = _canon
for _canon in set(AUTHOR_VARIANTS.values()):
    _NAME_LOOKUP.setdefault(_canon.split()[0].lower(), _canon)   # bare surname
    _NAME_LOOKUP.setdefault(_canon.lower(), _canon)              # canonical form


def extract_author_from_query(query):
    """Return the "Lastname Initials" form of any known institute PI mentioned in
    the query (else None). Handles explicit phrasing ("papers by X") and bare
    names ("Stephanie Fernandes", "Fernandes SA", "langer")."""
    q = query.lower()
    # Multi-word names first (more specific), then single-word surnames as whole words.
    for name, canon in _NAME_LOOKUP.items():
        if " " in name and name in q:
            return canon
    for w in re.findall(r"[a-zà-ÿ]+", q):
        if w in _NAME_LOOKUP:
            return _NAME_LOOKUP[w]
    return None


# ── Retrieval ──────────────────────────────────────────────
def _semantic_scores(query):
    qv = encode_query(query).astype(np.float32)   # shared BGE encode (prefix + normalize)
    return embeddings @ qv                       # cosine vs every paper


def _rrf(rankings, k=60):
    """Reciprocal-rank fusion of several ranked index lists -> {idx: score}."""
    fused = {}
    for ranked in rankings:
        for rank, idx in enumerate(ranked):
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (k + rank)
    return fused


def retrieve(query, top_k=8, author=None):
    """Return the top_k paper rows for the query.
    Author (if given) restricts the candidate set; ranking blends semantic
    similarity with BM25 (when available) via reciprocal-rank fusion."""
    sem = _semantic_scores(query)

    cand = np.arange(len(papers_df))
    if author:
        mask = papers_df["_authors_lc"].str.contains(re.escape(author.lower())).values
        if mask.any():
            cand = np.where(mask)[0]                # scope to that author's papers

    sem_rank = cand[np.argsort(-sem[cand])]
    if bm25 is not None:
        bm = np.asarray(bm25.get_scores(re.findall(r"[a-z0-9]+", query.lower())))
        bm_rank = cand[np.argsort(-bm[cand])]
        fused = _rrf([list(sem_rank[:50]), list(bm_rank[:50])])
        order = sorted(fused, key=lambda i: -fused[i])
    else:
        order = list(sem_rank)

    return papers_df.iloc[order[:top_k]]


def _paper_block(row, with_fulltext=False, ft_chars=6000):
    block = (
        f"Title: {row['title']}\n"
        f"Authors: {row['authors']}\n"
        f"Journal: {row['journal']} ({row['year']})\n"
        f"Link: {row['web_link']}\n"
        f"Abstract: {row['abstract']}"
    )
    if with_fulltext and row["full_text"]:
        block += f"\nFull text (excerpt):\n{row['full_text'][:ft_chars]}"
    return block + "\n---"


def _condense_query(query, conversation_history):
    """Rewrite a follow-up into a standalone search query using recent turns, so
    retrieval works on multi-turn questions ("tell me more", "what about in mice?",
    "what else did she find?"). Returns the query unchanged on the first turn or if
    rewriting fails."""
    prior = [m for m in conversation_history if m.get("role") in ("user", "assistant")]
    if not prior:
        return query                               # first turn: nothing to condense
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in prior[-4:])
    prompt = (
        "Rewrite the follow-up question into a standalone search query that includes any "
        "topic, author, gene, or entity implied by the conversation. Keep it concise and "
        "factual. Output ONLY the rewritten query, nothing else.\n\n"
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
        return query                               # any hiccup -> fall back to raw query


def chat_age_high(query, conversation_history=None, model=None, top_k=8):
    """Retrieve relevant institute papers and answer the query.
    Returns (response_text, conversation_history)."""
    model = model or LLM_MODEL
    if not query or not query.strip():
        return "You may have forgotten to input your query 🤔", conversation_history

    if not STORE_LOADED:
        return ("The paper database isn't available right now, so I can't look anything up. "
                "Please try again later."), conversation_history

    if not conversation_history or conversation_history[0].get("role") != "system":
        conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]

    try:
        # History-aware retrieval: rewrite follow-ups into a standalone query first,
        # so semantic search + author detection use the full conversational context.
        search_query = _condense_query(query, conversation_history)
        # Detect the PI from the user's own wording first (a bare name survives
        # here even if condensation rephrases it), then fall back to the rewrite.
        author = extract_author_from_query(query) or extract_author_from_query(search_query)
        hits = retrieve(search_query, top_k=top_k, author=author)

        want_depth = bool(DEPTH_RE.search(query))   # depth from the user's actual wording
        blocks = [
            _paper_block(row, with_fulltext=(want_depth and i < 2))   # full text for top-2 on deep questions
            for i, (_, row) in enumerate(hits.iterrows())
        ]
        context = "\n\n".join(blocks)

        # Always use our own system prompt (never trust a client-supplied one),
        # plus the last few user/assistant turns for continuity.
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
        # Full detail goes to the server-side log/toast; the user sees a generic message.
        make_except_toast("There was a problem with the chatbot:", "chatbot_issue", e, current_user, "chatbot")
        return ("Sorry — something went wrong while answering your question. "
                "Please try again in a moment."), conversation_history

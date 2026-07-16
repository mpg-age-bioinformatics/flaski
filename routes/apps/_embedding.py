"""Shared BGE embedding model for retrieval apps.

The model is loaded ONCE per process and shared by reference, so multiple apps in
the same flaski server don't each hold their own ~1.3 GB copy. Import
``get_model()`` / ``encode_query()`` from here instead of instantiating
``SentenceTransformer`` directly.

Usage:
    from myapp.routes.apps._embedding import get_model, encode_query
    model = get_model()                 # shared instance, loaded on first use
    q = encode_query("some question")   # prefixed + normalized query vector
"""
import os
import threading
from sentence_transformers import SentenceTransformer

# The embedding model and its query convention. BGE is ASYMMETRIC: passages are
# embedded with NO prefix (at build time); every QUERY must be prefixed. The
# prefix belongs to the MODEL, not the app — any app using this model shares it.
# (If a future app uses a different model, give it its own module/prefix.)
MODEL_NAME   = "BAAI/bge-large-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# Where to find the model cache. In prod the model is pre-seeded on the shared
# private volume; locally we fall back to the default HF cache
# (~/.cache/huggingface/hub). This is resolved in code — no HF_HOME / offline env
# needed anywhere, and it can't be defeated by import order.
_VOLUME_HUB = "/flaski_private/hf_cache/hub"
_CACHE_DIR  = _VOLUME_HUB if os.path.isdir(_VOLUME_HUB) else None   # None → default HF cache

_bge_model = None
_lock_model = threading.Lock()


def _resolve_model_path():
    """Return a local filesystem path to the model, WITHOUT blocking on the network
    when it's already cached.

    Step 1 — cache only (``local_files_only=True``): if the model is present (the
    pre-seeded volume in prod, or ~/.cache locally) this returns instantly with no
    network call, so startup never hangs on an HF outage.

    Step 2 — only if it isn't cached, fall back to a normal (online) download. This
    keeps local first-run auto-download working. In prod the volume is seeded so this
    branch isn't taken; if it were and HF were unreachable, the error propagates to the
    caller's try/except, which marks the app unavailable (flaski itself never crashes).
    """
    from huggingface_hub import snapshot_download
    try:
        return snapshot_download(MODEL_NAME, cache_dir=_CACHE_DIR, local_files_only=True)
    except Exception:
        return snapshot_download(MODEL_NAME, cache_dir=_CACHE_DIR)   # not cached: fetch


def get_model():
    """Return the single shared SentenceTransformer instance for this process,
    loading it on first use (thread-safe via double-checked locking)."""
    global _bge_model
    if _bge_model is None:
        with _lock_model:
            if _bge_model is None:                    # only the first caller loads
                _bge_model = SentenceTransformer(_resolve_model_path())
    return _bge_model


def encode_query(text, normalize=True):
    """Encode a user query with the BGE instruction prefix (asymmetric retrieval),
    normalized by default so cosine similarity == dot product against the stored
    passage vectors. Centralizes the query-side contract across all apps."""
    return get_model().encode(QUERY_PREFIX + text, normalize_embeddings=normalize)

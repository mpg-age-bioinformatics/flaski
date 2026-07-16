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

# The embedding model and its query convention. BGE is ASYMMETRIC: passages are
# embedded with NO prefix (at build time); every QUERY must be prefixed. The
# prefix belongs to the MODEL, not the app — any app using this model shares it.
# (If a future app uses a different model, give it its own module/prefix.)
MODEL_NAME   = "BAAI/bge-large-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# Model is pre-seeded on the shared private volume, which is treated as READ-ONLY source data
_VOLUME_HUB = "/flaski_private/hf_cache/hub"
_HAS_VOLUME = os.path.isdir(_VOLUME_HUB)

_bge_model = None
_lock_model = threading.Lock()


def _resolve_model_path():
    """Return a local filesystem path to the model — never writing to the read-only
    private volume, and never blocking on the network when the model is cached.

    1. Prod: read the pre-seeded volume with ``local_files_only=True`` — a pure read
       (no writes to /flaski_private, no network). Returns instantly when present.
    2. Otherwise (local dev, or a missing seed): use the default HF cache (~/.cache) —
       read it if present, else download into it. Any download goes to the writable
       default cache, NEVER the volume.

    A failure here propagates to the caller's try/except, which marks the app
    unavailable; flaski itself never crashes.
    """
    from huggingface_hub import snapshot_download
    # 1. Read-only lookup on the pre-seeded volume (never writes there).
    if _HAS_VOLUME:
        try:
            return snapshot_download(MODEL_NAME, cache_dir=_VOLUME_HUB, local_files_only=True)
        except Exception:
            pass   # not on the volume → fall through to the default (writable) cache
    # 2. Default cache: use if present, else download here (into ~/.cache, not the volume).
    try:
        return snapshot_download(MODEL_NAME, local_files_only=True)
    except Exception:
        return snapshot_download(MODEL_NAME)   # local dev / self-heal into ~/.cache


def get_model():
    """Return the single shared SentenceTransformer instance for this process,
    loading it on first use (thread-safe via double-checked locking)."""
    global _bge_model
    if _bge_model is None:
        with _lock_model:
            if _bge_model is None:                    # only the first caller loads
                # Import here (not at module top) so that merely importing this module
                # — and the apps that import it — can never fail on a broken/missing
                # sentence-transformers install. Every failure path now lands in the
                # caller's try/except (STORE_LOADED=False), so flaski keeps running.
                from sentence_transformers import SentenceTransformer
                _bge_model = SentenceTransformer(_resolve_model_path())
    return _bge_model


def encode_query(text, normalize=True):
    """Encode a user query with the BGE instruction prefix (asymmetric retrieval),
    normalized by default so cosine similarity == dot product against the stored
    passage vectors. Centralizes the query-side contract across all apps."""
    return get_model().encode(QUERY_PREFIX + text, normalize_embeddings=normalize)

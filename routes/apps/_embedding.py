"""Shared BGE embedding model for retrieval apps (Chatbot AGE…).

The model is loaded ONCE per process and shared by reference, so multiple apps in
the same flaski server don't each hold their own ~1.3 GB copy. Import
``get_model()`` / ``encode_query()`` from here instead of instantiating
``SentenceTransformer`` directly.

Usage:
    from myapp.routes.apps._embedding import get_model, encode_query
    model = get_model()                 # shared instance, loaded on first use
    q = encode_query("some question")   # prefixed + normalized query vector
"""
import threading
from sentence_transformers import SentenceTransformer

# The embedding model and its query convention. BGE is ASYMMETRIC: passages are
# embedded with NO prefix (at build time); every QUERY must be prefixed. The
# prefix belongs to the MODEL, not the app — any app using this model shares it.
# (If a future app uses a different model, give it its own module/prefix.)
MODEL_NAME   = "BAAI/bge-large-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

_bge_model = None
_lock_model = threading.Lock()


def get_model():
    """Return the single shared SentenceTransformer instance for this process,
    loading it on first use (thread-safe via double-checked locking)."""
    global _bge_model
    if _bge_model is None:
        with _lock_model:
            if _bge_model is None:                    # only the first caller loads
                _bge_model = SentenceTransformer(MODEL_NAME)
    return _bge_model


def encode_query(text, normalize=True):
    """Encode a user query with the BGE instruction prefix (asymmetric retrieval),
    normalized by default so cosine similarity == dot product against the stored
    passage vectors. Centralizes the query-side contract across all apps."""
    return get_model().encode(QUERY_PREFIX + text, normalize_embeddings=normalize)

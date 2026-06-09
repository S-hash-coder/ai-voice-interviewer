# rag.py

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# -------------------------
# GLOBAL STORAGE (FIX 1)
# -------------------------
model = None
index = None
chunks_store = None


# -------------------------
# MODEL LOADER (FIX 2)
# -------------------------
def get_model():
    global model
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")
    return model


# -------------------------
# BUILD INDEX (FIX 3)
# -------------------------
def build_index(chunks):
    global index, chunks_store

    model = get_model()

    chunks_store = chunks
    embeddings = model.encode(chunks, normalize_embeddings=True)

    dim = len(embeddings[0])

    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))


# -------------------------
# SEARCH FUNCTION (FIX 4)
# -------------------------
def search(query):
    global index, chunks_store

    if index is None:
        return "Index not ready"

    model = get_model()

    q_emb = model.encode(
    [query],
    normalize_embeddings=True
)

    D, I = index.search(np.array(q_emb), k=5)
    
    return "\n".join([chunks_store[i] for i in I[0]])
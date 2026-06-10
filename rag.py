from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = None
index = None
chunks_store = None


def get_model():
    global model
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")
    return model


def preload():
    get_model()


def build_index(chunks):
    global index, chunks_store

    embedder = get_model()
    chunks_store = chunks
    embeddings = embedder.encode(chunks, normalize_embeddings=True, show_progress_bar=False)

    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))


def search(query, k=2):
    global index, chunks_store

    if index is None:
        return ""

    embedder = get_model()
    q_emb = embedder.encode([query], normalize_embeddings=True, show_progress_bar=False)
    _, indices = index.search(np.array(q_emb), k=min(k, len(chunks_store)))

    return "\n".join(chunks_store[i] for i in indices[0] if i >= 0)

import os
import hashlib
import pickle
from rag_core.config import EMBEDDINGS_CACHE_PATH

# Hash a file's bytes for unique cache key
def get_file_hash(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()

# Get the cache file path for a given hash
def get_cache_path(file_hash):
    os.makedirs(EMBEDDINGS_CACHE_PATH, exist_ok=True)
    return f"{EMBEDDINGS_CACHE_PATH}/{file_hash}.pkl"

# Save embeddings to cache
def save_embeddings_to_cache(file_hash, embeddings):
    with open(get_cache_path(file_hash), "wb") as f:
        pickle.dump(embeddings, f)

# Load embeddings from cache
def load_embeddings_from_cache(file_hash):
    with open(get_cache_path(file_hash), "rb") as f:
        return pickle.load(f)

# --- Global embedding cache ---
GLOBAL_EMBEDDINGS_PATH = os.path.join(os.path.dirname(__file__), '..', 'log', 'global_embeddings')

def get_global_embedding_path(file_hash):
    os.makedirs(GLOBAL_EMBEDDINGS_PATH, exist_ok=True)
    return os.path.join(GLOBAL_EMBEDDINGS_PATH, f"{file_hash}.pkl")

def save_global_embeddings(file_hash, embeddings):
    with open(get_global_embedding_path(file_hash), "wb") as f:
        pickle.dump(embeddings, f)

def load_global_embeddings(file_hash):
    path = get_global_embedding_path(file_hash)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)

def global_embeddings_exist(file_hash):
    return os.path.exists(get_global_embedding_path(file_hash))

# --- Per-chat embedding management ---
def get_chat_embedding_path(chat_id, file_hash):
    if chat_id is None or file_hash is None:
        return None
    dir_path = os.path.join(os.path.dirname(__file__), '..', 'log', 'conversations', chat_id, 'embeddings')
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, f"{file_hash}.pkl")

def save_chat_file_embeddings(chat_id, file_hash, embeddings):
    if chat_id is None or file_hash is None:
        return False
    path = get_chat_embedding_path(chat_id, file_hash)
    if path is None:
        return False
    with open(path, "wb") as f:
        pickle.dump(embeddings, f)
    return True

def load_chat_file_embeddings(chat_id, file_hash):
    if chat_id is None or file_hash is None:
        return None
    path = get_chat_embedding_path(chat_id, file_hash)
    if path is None or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)

def chat_file_embeddings_exist(chat_id, file_hash):
    if chat_id is None or file_hash is None:
        return False
    path = get_chat_embedding_path(chat_id, file_hash)
    return path is not None and os.path.exists(path) 
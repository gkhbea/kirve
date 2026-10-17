"""
KİRVE AI OS - Embedding Layer
Generates vector embeddings for user messages, documents, and search queries.
Uses Ollama (/api/embeddings) when available, with a fast deterministic fallback.
"""
import math
import json
import urllib.request
import urllib.error
import hashlib
from typing import List, Optional
from kirve.config import OLLAMA_BASE_URL

EMBEDDING_DIM = 384  # Standard dimension (all-MiniLM / nomic-embed)

class EmbeddingEngine:
    """
    Embedding generator for pgvector and semantic search.
    """
    def __init__(self, model_name: str = "nomic-embed-text", base_url: str = OLLAMA_BASE_URL, dim: int = EMBEDDING_DIM):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.dim = dim

    def embed_text(self, text: str) -> List[float]:
        """
        Embeds a single string into a vector of float values.
        """
        if not text or not text.strip():
            return [0.0] * self.dim

        # Attempt Ollama local embedding API first
        vector = self._embed_via_ollama(text)
        if vector is not None and len(vector) > 0:
            return self._normalize(self._fit_dim(vector))

        # Fallback: Deterministic semantic hashing vectorizer (always available offline)
        return self._generate_fallback_embedding(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embeds a batch of texts."""
        return [self.embed_text(t) for t in texts]

    def _embed_via_ollama(self, text: str) -> Optional[List[float]]:
        url = f"{self.base_url}/api/embeddings"
        payload = json.dumps({"model": self.model_name, "prompt": text}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data.get("embedding")
        except Exception:
            return None
        return None

    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """
        Generates a normalized, deterministic embedding vector using word
        and character subword n-gram hashing (FastText style).
        Preserves morphological and semantic similarity for Turkish and multi-lingual words.
        """
        clean_text = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in text.lower())
        words = clean_text.split()
        if not words:
            return [0.0] * self.dim

        vec = [0.0] * self.dim

        for pos, word in enumerate(words):
            if not word:
                continue
            
            # Position-aware decay
            pos_weight = 1.0 / (1.0 + pos * 0.05)

            # 1. Full word hashing
            h_word = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx_word = h_word % self.dim
            vec[idx_word] += 2.0 * pos_weight

            # 2. Character n-grams (3-grams and 4-grams) for subword similarity
            for n in (3, 4):
                if len(word) >= n:
                    for i in range(len(word) - n + 1):
                        ngram = word[i:i + n]
                        h_ngram = int(hashlib.md5(ngram.encode("utf-8")).hexdigest(), 16)
                        idx_ngram = h_ngram % self.dim
                        vec[idx_ngram] += 0.8 * pos_weight

        return self._normalize(vec)

    def _fit_dim(self, vec: List[float]) -> List[float]:
        if len(vec) == self.dim:
            return vec
        elif len(vec) > self.dim:
            return vec[:self.dim]
        else:
            return vec + [0.0] * (self.dim - len(vec))

    def _normalize(self, vec: List[float]) -> List[float]:
        norm = math.sqrt(sum(x * x for x in vec))
        if norm < 1e-9:
            return [0.0] * len(vec)
        return [round(x / norm, 6) for x in vec]

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Calculates cosine similarity between two vectors (1.0 = identical)."""
        if len(v1) != len(v2) or not v1:
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 < 1e-9 or norm2 < 1e-9:
            return 0.0
        return max(-1.0, min(1.0, dot / (norm1 * norm2)))

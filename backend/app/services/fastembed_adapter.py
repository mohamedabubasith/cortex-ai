
from typing import List
from fastembed import TextEmbedding
from cognee.infrastructure.databases.vector.embeddings.EmbeddingEngine import EmbeddingEngine

class FastEmbedAdapter(EmbeddingEngine):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = TextEmbedding(model_name=model_name)
        self.vector_size = 384  # Default for all-MiniLM-L6-v2

    def embed_text(self, text: List[str]) -> List[List[float]]:
        # FastEmbed returns a generator, convert to list
        embeddings = list(self.model.embed(text))
        # Convert numpy arrays to lists
        return [e.tolist() for e in embeddings]

    def get_vector_size(self) -> int:
        return self.vector_size

    def get_batch_size(self) -> int:
        return 32

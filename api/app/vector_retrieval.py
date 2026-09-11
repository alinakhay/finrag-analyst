from app.config import Settings
from app.corpus import Chunk
from app.retrieval import BM25Retriever, SearchResult


class QdrantDenseRetriever:
    """Sentence Transformer retrieval backed by Qdrant (in-memory or remote)."""

    name = "qdrant-dense"

    def __init__(self, chunks: tuple[Chunk, ...], settings: Settings):
        try:
            from qdrant_client import QdrantClient, models
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise RuntimeError(
                "Install the semantic extra before using CATALYSTLENS_RETRIEVER_BACKEND=hybrid"
            ) from error
        self.chunks = chunks
        self.models = models
        self.model = SentenceTransformer(settings.embedding_model)
        self.client = (
            QdrantClient(url=settings.qdrant_url)
            if settings.qdrant_url
            else QdrantClient(location=":memory:")
        )
        self.collection = settings.qdrant_collection
        vectors = self.model.encode([chunk.text for chunk in chunks], normalize_embeddings=True)
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(
                    size=int(vectors.shape[1]), distance=models.Distance.COSINE
                ),
            )
            self.client.upsert(
                collection_name=self.collection,
                points=[
                    models.PointStruct(
                        id=index,
                        vector=vector.tolist(),
                        payload={"chunk_index": index, "filing_id": chunk.filing_id},
                    )
                    for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
                ],
            )

    def search(self, query: str, filing_id: str, top_k: int = 3) -> list[SearchResult]:
        vector = self.model.encode(query, normalize_embeddings=True).tolist()
        response = self.client.query_points(
            collection_name=self.collection,
            query=vector,
            query_filter=self.models.Filter(
                must=[
                    self.models.FieldCondition(
                        key="filing_id", match=self.models.MatchValue(value=filing_id)
                    )
                ]
            ),
            limit=top_k,
        )
        return [
            SearchResult(
                chunk=self.chunks[int(point.payload["chunk_index"])],
                score=round(max(0.0, min(1.0, float(point.score))), 3),
            )
            for point in response.points
        ]


class HybridRetriever:
    name = "bm25-qdrant-hybrid"

    def __init__(self, chunks: tuple[Chunk, ...], settings: Settings):
        self.sparse = BM25Retriever(chunks)
        self.dense = QdrantDenseRetriever(chunks, settings)

    def search(self, query: str, filing_id: str, top_k: int = 3) -> list[SearchResult]:
        sparse = self.sparse.search(query, filing_id, top_k * 2)
        dense = self.dense.search(query, filing_id, top_k * 2)
        combined: dict[str, tuple[Chunk, float]] = {}
        for result in sparse:
            combined[result.chunk.id] = (result.chunk, result.score * 0.45)
        for result in dense:
            chunk, score = combined.get(result.chunk.id, (result.chunk, 0.0))
            combined[result.chunk.id] = (chunk, score + result.score * 0.55)
        ranked = sorted(combined.values(), key=lambda item: item[1], reverse=True)[:top_k]
        return [SearchResult(chunk=chunk, score=round(score, 3)) for chunk, score in ranked]


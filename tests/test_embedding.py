"""
Unit tests for Embedding Layer
"""
import unittest
import math
from kirve.embedding import EmbeddingEngine, EMBEDDING_DIM

class TestEmbeddingEngine(unittest.TestCase):
    def setUp(self):
        self.engine = EmbeddingEngine()

    def test_embedding_dimension_and_normalization(self):
        vec = self.engine.embed_text("KİRVE AI OS test metni")
        self.assertEqual(len(vec), EMBEDDING_DIM)
        
        # Test unit length (normalization)
        norm = math.sqrt(sum(x * x for x in vec))
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_empty_string_handling(self):
        vec = self.engine.embed_text("")
        self.assertEqual(len(vec), EMBEDDING_DIM)
        self.assertEqual(vec, [0.0] * EMBEDDING_DIM)

    def test_cosine_similarity(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]

        # Identical
        self.assertAlmostEqual(EmbeddingEngine.cosine_similarity(v1, v2), 1.0, places=5)
        # Orthogonal
        self.assertAlmostEqual(EmbeddingEngine.cosine_similarity(v1, v3), 0.0, places=5)

    def test_semantic_clustering(self):
        vec_togg_1 = self.engine.embed_text("Togg T10X elektrikli otomobil şarjı")
        vec_togg_2 = self.engine.embed_text("Togg batarya doluluk oranı ve şarj istasyonu")
        vec_recipe = self.engine.embed_text("Fırında karnıyarık yemeği tarifi ve malzemeleri")

        sim_togg = EmbeddingEngine.cosine_similarity(vec_togg_1, vec_togg_2)
        sim_diff = EmbeddingEngine.cosine_similarity(vec_togg_1, vec_recipe)

        # Related texts should have higher similarity than unrelated cooking recipe
        self.assertGreater(sim_togg, sim_diff)

    def test_embed_batch(self):
        texts = ["Birinci cümle", "İkinci cümle", "Üçüncü cümle"]
        batch = self.engine.embed_batch(texts)
        self.assertEqual(len(batch), 3)
        for v in batch:
            self.assertEqual(len(v), EMBEDDING_DIM)

if __name__ == "__main__":
    unittest.main()

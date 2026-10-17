"""
Unit tests for Vector Memory (PostgreSQL + pgvector Architecture & Similarity Search)
"""
import unittest
import tempfile
import os
from pathlib import Path
from kirve.memory_vector import VectorMemory
from kirve.embedding import EmbeddingEngine

class TestVectorMemory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_vector.db")
        self.embedder = EmbeddingEngine()
        self.memory = VectorMemory(fallback_sqlite_path=self.db_path, embedding_engine=self.embedder)

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_add_and_search_conversations(self):
        # Insert conversations
        self.memory.add_message("user", "Togg şarj durumunu kontrol et patron", session_id="s1")
        self.memory.add_message("assistant", "Togg T10X %78 dolu, menzil 395 km", session_id="s1")
        self.memory.add_message("user", "Akşam yemeğinde ne yesek acaba?", session_id="s1")

        # Search for vehicle related conversation
        results = self.memory.search_similar_messages("elektrikli araba şarjı ve batarya", limit=2)
        self.assertGreaterEqual(len(results), 1)
        top_result = results[0]
        self.assertIn("togg", top_result["content"].lower())
        self.assertIn("similarity", top_result)

    def test_add_and_search_documents(self):
        # Insert documents
        self.memory.add_document(
            title="KİRVE Master Talimatları",
            content="Patrona her zaman patron diye hitap et, robotik dilden uzak dur.",
            tags=["kimlik", "kurallar"]
        )
        self.memory.add_document(
            title="Roborock Q8 Kılavuzu",
            content="LiDAR sensörü 360 derece haritalama yapar. Bölge temizliği komutla başlar.",
            tags=["donanim", "temizlik"]
        )

        # Search for vacuum cleaner guide
        res = self.memory.search_documents("robot süpürge haritalama", limit=1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["title"], "Roborock Q8 Kılavuzu")
        self.assertIn("donanim", res[0]["tags"])

if __name__ == "__main__":
    unittest.main()

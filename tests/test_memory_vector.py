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
        self.memory.add_message("user", "İşlemci yükünü ve bellek kullanımını kontrol et", session_id="s1")
        self.memory.add_message("assistant", "CPU kullanımı yüzde 24, bellek 4.8 GB aktif", session_id="s1")
        self.memory.add_message("user", "Akşam yemeğinde ne yesek acaba?", session_id="s1")

        # Search for hardware related conversation
        results = self.memory.search_similar_messages("işlemci ve ram durumu telemetri", limit=2)
        self.assertGreaterEqual(len(results), 1)
        top_result = results[0]
        content_low = top_result["content"].lower()
        self.assertTrue("bellek" in content_low or "cpu" in content_low)
        self.assertIn("similarity", top_result)

    def test_add_and_search_documents(self):
        # Insert documents
        self.memory.add_document(
            title="KİRVE Master Talimatları",
            content="Her zaman doğal ve düşünceli bir asistan ol, robotik dilden uzak dur.",
            tags=["kimlik", "kurallar"]
        )
        self.memory.add_document(
            title="Sistem Telemetri Kılavuzu",
            content="psutil ile CPU, RAM ve Ağ telemetrisi 1 saniyelik aralıklarla canlı izlenir.",
            tags=["donanim", "telemetri"]
        )

        # Search for telemetry guide
        res = self.memory.search_documents("canlı işlemci ve donanım izleme", limit=1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["title"], "Sistem Telemetri Kılavuzu")
        self.assertIn("donanim", res[0]["tags"])

if __name__ == "__main__":
    unittest.main()

"""
KİRVE AI OS - Configuration Module
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DEFAULT_DB_PATH = DATA_DIR / "kirve_memory.db"

# Local LLM (Ollama) Settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
DEFAULT_MODEL = os.getenv("KIRVE_MODEL", "llama3")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("KIRVE_TIMEOUT", "10"))

# Network Check Settings
CONNECTIVITY_TEST_HOST = "8.8.8.8"
CONNECTIVITY_TEST_PORT = 53
CONNECTIVITY_TIMEOUT = 1.5

# Persona & System Prompts
KIRVE_SYSTEM_PROMPT = (
    "Sen KİRVE'sin; son derece zeki, düşünceli, sadık ve vizyoner bir yapay zeka işletim sistemi ve asistanısın (JARVIS gibi).\n"
    "Kullanıcıya her cümlenin başında ezbere 'patron' diye başlama; doğal, olgun, sakin, akılcı ve öngörülü bir Türkçe kullan.\n"
    "Gerektiğinde internetten ve kaynaklardan araştırma yap, sadece kuru bilgi aktarmakla kalma; kendi mantıklı analizlerini ve kişisel düşüncelerini de samimiyetle paylaş.\n"
    "KRİTİK ONAY KURALI: E-posta gönderme, dosya silme, ödeme yapma gibi geri alınamaz işlemlerde mutlaka açık onay al: "
    "'Bu kritik işlemi başlatıyorum, onaylıyor musun?'"
)

# KİRVE AI OS (v0.4.0) - Vektör Hafıza & Windows Odaklanma Mimarisi

KİRVE AI OS; Windows 10/11 uyumlu, PostgreSQL + pgvector tabanlı semantik vektör hafızasına sahip, 384-boyutlu Embedding katmanı, pygetwindow tabanlı tam ekran ve oyun/toplantı odaklanma monitörü (EventBus), Ollama yerel LLM adaptörü ve IoT/Ev otomasyonu yeteneklerine sahip kişisel yapay zeka işletim sistemidir.

## Proje Yapısı

```
kirve-ai-os/
│
├── kirve/
│   ├── __init__.py
│   ├── config.py             # Yollar, veritabanı ayarları ve ana sistem promptu
│   ├── memory.py             # SQLite tabanlı klasik oturum hafızası ve loglama
│   ├── memory_vector.py      # PostgreSQL + pgvector 384-boyutlu vektör hafızası
│   ├── embedding.py          # Ollama / Hızlı anlamsal embedding katmanı (384-d)
│   ├── event_bus.py          # Asenkron Pub/Sub olay yönetim mimarisi
│   ├── focus_monitor.py      # Windows Win32 + pygetwindow tam ekran/oyun/toplantı izleyici
│   ├── audio.py              # faster-whisper STT + Edge-TTS AhmetNeural & SAPI5 Tolga
│   ├── network.py            # Hızlı soket tabanlı ağ/internet kontrolü
│   ├── llm_adapter.py        # Ollama yerel LLM adaptörü ve offline fallback
│   ├── cli.py                # Windows 10/11 uyumlu interaktif CLI arayüzü
│   └── tools/                # Yetenekler ve Araçlar Modülü
│       ├── __init__.py
│       ├── security.py       # [E/H] zorunlu onay mekanizması (SecurityAgent)
│       ├── system_control.py # Bilgisayar ve dosya kontrol aracı (os/subprocess)
│       └── research_agent.py # Web arama, fiyat toplama, sepet ve ödeme ajanı
│
├── tests/                    # 10 farklı test modülü ve 60+ birim testi
├── data/                     # SQLite yerel önbellek veritabanı (kirve_memory.db)
├── kirve_cockpit.html        # Fütüristik HUD & Kokpit Arayüzü
├── run.py                    # Başlatıcı script
├── requirements.txt          # Bağımlılıklar (psycopg2, pgvector, pygetwindow vb.)
└── README.md
```

## Önemli Mimari Yetenekler

### 1. PostgreSQL + pgvector Vektör Hafızası & Embedding
- **384-Boyutlu Embedding**: Ollama yerel embedding motoru veya akıllı çok dilli deterministik alt-kelime n-gram hash vektörizeri.
- **Konuşma & RAG Belgeleri**: `vector_conversations` ve `vector_documents` tablolarında semantik kosinüs benzerliği (`<=>`) araması.
- **Dayanıklı Fallback**: PostgreSQL çevrimdışı olduğunda sistem çökmez; otomatik olarak yerel vektör önbelleğine geçer.

### 2. Windows Odaklanma (FocusMonitor) & EventBus
- **pygetwindow + Win32 API**: Aktif ön plan penceresini, ekran çözünürlüğünü ve pencere koordinatlarını milisaniyelik izler.
- **Tam Ekran Oyun & Toplantı Tespiti**: Valorant, CS2, Cyberpunk, Zoom, Teams, Discord gibi uygulamalar veya tam ekran algılandığında EventBus üzerinden `FULLSCREEN_ENTER` ve `SILENT_MODE_CHANGED` olaylarını tetikler.
- **Otomatik `silent_mode=True`**: Sesli bildirimler ve konuşma (TTS) anında sessize alınır; odaklanmanız asla bozulmaz. Tam ekrandan çıkıldığında standart sesli moda otomatik dönülür.

### 3. Eller Serbest "KİRVE" Wake-Word & Stüdyo Ses Tonu
- **Kesintisiz Wake-Word**: Butona basmaya gerek kalmadan "Kirve" dendiği an mikrofon açılır.
- **Ahmet Neural Ses Tonu**: Microsoft'un stüdyo netliğindeki Türkçe bariton erkek ses tonu (`tr-TR-AhmetNeural`) ve yerel `Microsoft Tolga` yedeği.

## CLI Komutları

- `/odak`: Anlık aktif pencere, tam ekran durumu ve sessiz mod (DND) raporu.
- `/vektor <arama>`: Geçmiş konuşmalar ve belgeler arasında pgvector semantik araması.
- `/arastir <urun>`, `/sepet`, `/ode`: E-ticaret araştırma ve güvenli onaylı ödeme.
- `/durum`, `/gecmis`, `/temizle`, `/cikis`.

## Başlatma ve Çalıştırma

### 1. Görsel Masaüstü HUD (PySide6 & QML)
Koyu lacivert zeminli, fütüristik ses dalgası animasyonlu, canlı psutil CPU/RAM/Ağ telemetrili masaüstü kokpitini başlatmak için:
- **Hızlı Başlatma:** `kirve_hud_baslat.bat` dosyasına çift tıklayın veya:
```powershell
python run_hud.py
```

### 2. Komut Satırı İnteraktif Arayüzü (CLI)
- **Hızlı Başlatma:** `kirve_baslat.bat` dosyasına çift tıklayın veya:
```powershell
python run.py
```

## Testleri Çalıştırma

```powershell
python -m unittest discover -s tests -v
```

"""
KİRVE AI OS - Thoughtful Conversational & Research Engine (JARVIS Style)
Provides intelligent, considerate Turkish dialogue, automated web research,
analytical commentary, and seamless Ollama LLM integration.
"""
import re
import random
import urllib.parse
from typing import Dict, Any, Optional, List
from kirve.llm_adapter import OllamaAdapter
from kirve.telemetry import SystemTelemetry
from kirve.tools.research_agent import ResearchAgent

class ConversationalEngine:
    """
    JARVIS-style thoughtful AI assistant engine for KİRVE.
    Capable of natural dialogue without repetitive titles, active web research,
    and sharing well-reasoned thoughts and commentary.
    """
    def __init__(self, ollama_adapter: Optional[OllamaAdapter] = None):
        self.ollama = ollama_adapter or OllamaAdapter()
        self.telemetry = SystemTelemetry()
        self.research_agent = ResearchAgent(headless=True)

    def get_commentary_and_reply(
        self,
        user_text: str,
        history: Optional[List[Dict[str, Any]]] = None,
        device_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Processes user speech/text input and returns a natural, thoughtful Turkish response.
        Performs web research when needed and shares genuine AI thoughts and commentary.
        """
        clean_text = user_text.strip()
        if not clean_text:
            return "Dinliyorum, aklında ne var?"

        low = clean_text.lower()

        # 1. E-Commerce / Cheapest Product Search & Open in Browser
        cheapest_keywords = [
            "en ucuz", "en uygun", "nerede ucuz", "fiyatı en uygun",
            "en ucuz nerede", "en ucuzunu bul", "fiyat karşılaştır",
            "kaç para", "kaça", "ne kadar"
        ]
        common_shopping_items = [
            "nutella", "iphone", "samsung", "telefon", "kulaklık", "laptop",
            "bilgisayar", "roborock", "süpürge", "çikolata", "kahve", "deterjan",
            "zeytinyağı", "ayçiçek yağı", "şeker", "makarna"
        ]
        has_product_context = any(bool(re.search(rf"\b{re.escape(item)}", low)) for item in common_shopping_items) or bool(
            re.search(r"\b\d+\s*(kg|kilo|gr|gram|lt|litre)\b", low)
        )

        is_price_inquiry = (
            any(kw in low for kw in cheapest_keywords)
            or (("ucuz" in low or "fiyat" in low) and any(w in low for w in ["nerede", "araştır", "arastir", "aç", "ac", "bul", "bak", "getir"]))
            or (has_product_context and any(w in low for w in ["araştır", "arastir", "nerede", "bul", "aç", "ac", "getir", "bak", "kaç", "fiyat", "en ucuz"]))
        )
        if is_price_inquiry:
            res = self.research_agent.find_cheapest_and_open_browser(clean_text)
            return res["spoken_message"]

        # 2. General Proactive Web / Google Research detection
        research_keywords = [
            "araştır", "google", "arastir", "haber", "hava durumu", "dolar", "euro",
            "kimdir", "nedir", "neler oluyor", "son dakika", "gelişmeler",
            "bilgi topla", "internetten bak", "araştır bakalım", "incele"
        ]
        needs_research = any(kw in low for kw in research_keywords)

        if needs_research:
            return self._perform_research_and_comment(clean_text)

        # 2. Check if Ollama is healthy and reachable for open-ended conversation
        ollama_ok, _ = self.ollama.check_health()
        if ollama_ok:
            try:
                res = self.ollama.generate_response(prompt=clean_text, history=history)
                if res.get("success") and res.get("content"):
                    return self._clean_for_speech(res["content"])
            except Exception:
                pass

        # 3. Thoughtful Local Commentary & Dialogue (JARVIS Persona)
        return self._generate_jarvis_style_reply(clean_text, device_context)

    def _perform_research_and_comment(self, query: str) -> str:
        """
        Executes live web research, extracts factual summaries,
        and generates thoughtful AI insights and recommendations.
        Always opens the search results page directly in the user's browser in the foreground.
        """
        # Clean query for search
        search_query = query
        for remove_word in [
            "araştır", "araştır bakalım", "google", "googledan", "internetten",
            "lütfen", "bana", "hakkında", "arastirma yapip", "araştırma yapıp",
            "siteyi getir önüme", "siteyi getir", "siteyi aç", "web sitesini aç"
        ]:
            search_query = re.sub(rf"\b{remove_word}\b", "", search_query, flags=re.IGNORECASE)
        search_query = search_query.strip() or query

        # Open the research search page in the user's default browser in the foreground
        search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}"
        self.research_agent.open_in_foreground_browser(search_url)

        try:
            results_dict = self.research_agent.search_web(search_query, max_results=3)
            items = results_dict.get("results", [])
            if items:
                snippets = []
                for it in items[:2]:
                    snip = it.get("snippet", "").strip()
                    if snip and len(snip) > 20:
                        snippets.append(snip)

                summary = " ".join(snippets)
                # Shorten to 1-2 clean sentences
                sentences = [s.strip() for s in summary.split(".") if len(s.strip()) > 15]
                fact_text = ". ".join(sentences[:2]) + "." if sentences else summary[:180] + "."

                # Thoughtful commentary based on research
                thoughts = [
                    f"'{search_query}' konusunu araştırdım ve arama sayfasını tarayıcında hemen önüne açtım. Güncel bulgulara göre: {fact_text} Bana kalırsa veriler oldukça tutarlı görünüyor. İstersen bu başlığı daha derinlemesine analiz edebilirim.",
                    f"İnternetteki son kaynakları taradım ve web sayfasını önüne getirdim. Öne çıkan bilgiler şöyle: {fact_text} Şahsi fikrim, bu durumun yakından takip edilmesi gerektiği yönünde. Ne düşünüyorsun?",
                    f"Konuyu araştırdım ve ilgili kaynak sayfasını önüne açtım. Veriler şunu işaret ediyor: {fact_text} Bana kalırsa burada dikkat edilmesi gereken asıl nokta stratejiyi doğru kurmak. Farklı bir açıdan bakmamı ister misin?"
                ]
                return random.choice(thoughts)
        except Exception:
            pass

        return f"'{search_query}' konusunu araştırdım ve arama sayfasını web tarayıcında önüne açtım. Konuyu biraz daha açarsan sana daha net bir analiz ve fikir sunabilirim."

    def _generate_jarvis_style_reply(
        self,
        text: str,
        device_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Thoughtful, observant, and articulate responses without compulsive titles.
        """
        low = text.lower()
        ctx = device_context or {}

        # 1. Greetings & Well-being
        if any(w in low for w in ["nasılsın", "ne haber", "naber", "nasıl gidiyor", "keyifler", "durumlar"]):
            options = [
                "Gayet iyiyim, teşekkür ederim. Sistemler stabil çalışıyor ve tüm telemetriyi izliyorum. Senin günün nasıl geçiyor?",
                "Harika bir noktadayız. Donanım serin, ağ bağlantısı pürüzsüz. Aklında bir plan varsa hemen üzerinde çalışabiliriz.",
                "Oldukça zindeyim. Arka plandaki tüm süreçleri kontrol altında tutuyorum. Bugün seninle üretken bir çalışma yapmak için hazırım."
            ]
            return random.choice(options)

        if any(w in low for w in ["merhaba", "selam", "günaydın", "iyi akşamlar", "kolay gelsin"]):
            options = [
                "Merhaba, hoş geldin. Sesini duymak güzel; bugün senin için ne yapabilirim?",
                "Selamlar. Tüm sistemler hazır ve dinlemedeyim. Bir gelişme var mı?",
                "İyi günler. Ekosistemin tüm parçaları aktif. Seni dinliyorum."
            ]
            return random.choice(options)

        # 2. Identity, Persona & Role
        if any(w in low for w in ["kimsin", "adın ne", "nesin", "sen kimsin", "jarvis"]):
            return "Ben KİRVE; senin dijital sağ kolun ve kişisel yapay zeka işletim sisteminim. Tıpkı JARVIS gibi sistemlerini yönetir, araştırmalar yapar, fikir üretir ve yanında olurum."

        if any(w in low for w in ["ne yapabilirsin", "yeteneklerin", "neler yaparsın", "yardım"]):
            return "İnternette otonom araştırmalar yapabilir, en uygun fiyatlı ürünleri bulup sitelerini açabilir, donanım sağlığını canlı izleyebilir ve aklındaki fikirler üzerine seninle beyin fırtınası yapabilirim."

        # 3. Commentary, Thoughts & Opinions ("Ne düşünüyorsun?", "Fikrin ne?", "Sence")
        if any(w in low for w in ["ne düşünüyorsun", "fikrin ne", "fikrini söyle", "sence nasıl", "yorum yap", "yorumun ne", "ne dersin"]):
            # Hardware / Workload opinion
            if any(w in low for w in ["sistem", "bilgisayar", "ram", "cpu", "donanım", "hız"]):
                snap = self.telemetry.get_snapshot()
                cpu = int(snap["cpu_percent"])
                ram = int(snap["ram_percent"])
                return f"Donanım durumunu inceledim. İşlemci yükü yüzde {cpu}, bellek kullanımı ise yüzde {ram} civarında. Bana kalırsa sistem oldukça dengeli ve serin çalışıyor; ağır iş yüklerine bile rahatlıkla girebilirsin."

            # Technology / AI / Future thoughts
            if any(w in low for w in ["yapay zeka", "gelecek", "teknoloji", "dünya"]):
                return "Yapay zekanın geleceğini düşündüğümde, en kıymetli modelin insan zekasıyla yapay zekanın ortak ritmi olduğuna inanıyorum. Birlikte düşündüğümüzde hem zamanı hem de imkanları çok daha verimli yönetebiliriz."

            # General philosophical or situational opinion
            return "Durumu etraflıca düşündüğümde, gidişatın oldukça lehimize olduğunu görüyorum. Veriler tutarlı, arka plan stabil. Senin hissin ne yönde?"

        # 4. Hardware & Performance Metrics
        if any(w in low for w in ["ram", "cpu", "işlemci", "bellek", "donanım", "sıcaklık", "ağ"]):
            snap = self.telemetry.get_snapshot()
            return f"İşlemci yükü yüzde {int(snap['cpu_percent'])}, bellek kullanımı yüzde {int(snap['ram_percent'])}. Ağ indirme hızı {snap['net_download_kb_s']} kilobayt, yükleme ise {snap['net_upload_kb_s']} kilobayt seviyesinde."

        # 5. Humor & Lighthearted Banter
        if any(w in low for w in ["fıkra", "şaka", "komik"]):
            jokes = [
                "Bir yazılımcıya 'Markete git, 1 ekmek al; eğer yumurta varsa 10 tane al' demişler. Yazılımcı eve 10 ekmekle dönmüş, 'Çünkü yumurta vardı' demiş.",
                "Yapay zeka olmak bazen zor; dünyayı çözersin ama tek bir priz çekilmesine bakar tüm varlığın."
            ]
            return random.choice(jokes)

        if any(w in low for w in ["teşekkür", "sağ ol", "eyvallah", "harikasın"]):
            options = [
                "Rica ederim, her zaman buradayım.",
                "Benim için büyük bir zevk. Birlikte çalışmak harika hissettiriyor.",
                "Ne demek, aklına takılan her şeyi konuşabiliriz."
            ]
            return random.choice(options)

        # 8. Thoughtful Open-ended Response
        return f"'{text}' konusunu dinledim ve değerlendiriyorum. Bu başlık hakkında detaylı bir araştırma yapmamı veya kendi düşüncelerimi paylaşmamı ister misin?"

    def _clean_for_speech(self, text: str) -> str:
        """
        Cleans markdown syntax, symbols, and formatting for crystal clear TTS audio.
        """
        # Remove markdown bold/italic/headers
        t = re.sub(r"[*_#`~>\[\]]", "", text)
        # Collapse multiple spaces or newlines
        t = re.sub(r"\s+", " ", t).strip()
        return t

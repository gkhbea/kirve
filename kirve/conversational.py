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
        Performs Google web research when any question is asked, opens the browser,
        and shares genuine AI thoughts and commentary.
        """
        clean_text = user_text.strip()
        if not clean_text:
            return "Dinliyorum, aklında ne var?"

        low = clean_text.replace("İ", "i").replace("I", "ı").lower()

        # 1. User Rule / Directive: "sana soru sorduğumda google araştır"
        rule_phrases = [
            "sana soru sordugumda google arastır",
            "sana soru sorduğumda google araştır",
            "sana soru sordugumda google arastir",
            "soru sorduğumda google araştır",
            "soru sordugumda google arastir",
            "soru sorduğumda araştır",
            "soru sordugumda arastir",
            "soru sorunca google'da ara",
            "sorularımı google'da ara"
        ]
        if any(p in low for p in rule_phrases):
            return "Anlaşıldı! Bundan sonra bana sorduğun her soruda doğrudan Google'da araştırma yapacak, arama sayfasını web tarayıcında hemen önüne açacak ve elde ettiğim bilgileri sana sesli olarak özetleyeceğim. Merak ettiğin her şeyi sorabilirsin."

        # 2. E-Commerce / Cheapest Product Search & Open in Browser (Akakçe)
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

        # 3. Automatic Google Web Research whenever a question or research topic is asked
        if self._is_user_question(clean_text):
            return self._perform_research_and_comment(clean_text, is_direct_question=True)

        # 4. Check if Ollama is healthy and reachable for open-ended conversation
        ollama_ok, _ = self.ollama.check_health()
        if ollama_ok:
            try:
                res = self.ollama.generate_response(prompt=clean_text, history=history)
                if res.get("success") and res.get("content"):
                    return self._clean_for_speech(res["content"])
            except Exception:
                pass

        # 5. Thoughtful Local Commentary & Dialogue (JARVIS Persona)
        return self._generate_jarvis_style_reply(clean_text, device_context)

    def _is_user_question(self, text: str) -> bool:
        """
        Determines whether the input text is a question, factual inquiry, or research query
        directed at Google/the web, while preserving assistant internal dialogues
        (chit-chat greetings, assistant identity, internal hardware telemetry, AI thoughts).
        """
        low = text.replace("İ", "i").replace("I", "ı").lower().strip()
        if not low:
            return False

        # Exclude assistant conversational chit-chat & identity
        chit_chat_phrases = [
            "nasılsın", "ne haber", "naber", "nasıl gidiyor", "keyifler", "durumlar",
            "merhaba", "selam", "günaydın", "iyi akşamlar", "kolay gelsin",
            "sen kimsin", "kimsin", "adın ne", "nesin",
            "ne yapabilirsin", "neler yapabilirsin", "yeteneklerin", "neler yaparsın",
            "beni duyuyor musun", "beni duyabiliyor musun", "sesim geliyor mu",
            "hazır mısın", "burada mısın", "oradasın mı"
        ]
        if any(p in low for p in chit_chat_phrases):
            return False

        # Exclude hardware telemetry or AI opinion questions handled internally
        if any(w in low for w in ["ne düşünüyorsun", "fikrin ne", "fikrini söyle", "sence nasıl", "yorum yap", "yorumun ne", "ne dersin"]):
            if any(w in low for w in ["sistem", "donanım", "ram", "cpu", "işlemci", "bilgisayar", "yapay zeka"]):
                return False

        # 1. Contains Question Mark
        if "?" in text:
            return True

        # 2. Turkish Interrogatives
        question_words = [
            r"\bkim\b", r"\bkimdir\b", r"\bkimi\b", r"\bkime\b", r"\bkimin\b", r"\bkiminle\b",
            r"\bnedir\b", r"\bnelerdir\b", r"\bne\s+zaman\b", r"\bnerede\b", r"\bneredir\b",
            r"\bneresi\b", r"\bneresidir\b", r"\bnereye\b", r"\bnereden\b",
            r"\bnasıl\b", r"\bnasıldır\b",
            r"\bkaç\b", r"\bkaçtır\b", r"\bkaça\b", r"\bkaçta\b", r"\bkaçıncı\b", r"\bne\s+kadar\b",
            r"\bneden\b", r"\bniçin\b", r"\bniye\b",
            r"\bhangi\b", r"\bhangisi\b", r"\bhangileri\b"
        ]
        for qw in question_words:
            if re.search(qw, low):
                return True

        # 3. Turkish Interrogative Clitics / Particles
        particle_pattern = r"\b(mı|mi|mu|mü|mısın|misin|musun|müsün|mıyız|miyiz|muyuz|müyüz|mıdır|midir|mudur|müdür|mıydı|miydi|muydu|müydü|mısınız|misiniz|musunuz|müsünüz)\b"
        if re.search(particle_pattern, low):
            return True

        # 4. Explicit Research / Google triggers
        research_keywords = [
            "araştır", "arastir", "google", "googledan", "internetten", "araştır bakalım",
            "bilgi topla", "incele", "öğren", "haber", "hava durumu", "dolar", "euro",
            "borsa", "son dakika", "gelişmeler", "son durum"
        ]
        if any(kw in low for kw in research_keywords):
            return True

        return False

    def _clean_search_query(self, query: str) -> str:
        """
        Cleans conversational prefixes, commands, and fillers from natural queries
        to produce clean, high-relevance Google search terms.
        """
        search_query = query.strip()
        # Remove question marks and trailing punctuation
        search_query = re.sub(r"[?!.,;]+$", "", search_query).strip()

        # Remove Google / internet prefixes with Turkish declensions
        search_query = re.sub(r"\bgoogle(\'|’)?(da|de|dan|den)?\b", "", search_query, flags=re.IGNORECASE)
        search_query = re.sub(r"\binternet(\'|’)?(te|ta|ten|tan)?\b", "", search_query, flags=re.IGNORECASE)

        remove_phrases = [
            "araştır bakalım", "araştırır mısın", "araştır", "arastir",
            "ara bakalım", "arama yap", "ara", "bak bakalım", "bak",
            "bana söyler misin", "bana söyle", "söyler misin", "söyle bakalım", "söyler misiniz",
            "öğrenir misin", "bakar mısın", "bulur musun", "bilgi ver", "bilgi topla",
            "siteyi getir önüme", "siteyi getir", "siteyi aç", "web sitesini aç",
            "lütfen", "hakkında", "hakkinda"
        ]
        for remove_word in sorted(remove_phrases, key=len, reverse=True):
            search_query = re.sub(rf"\b{re.escape(remove_word)}\b", "", search_query, flags=re.IGNORECASE)

        search_query = " ".join(search_query.split()).strip()
        return search_query or query.strip()

    def _perform_research_and_comment(self, query: str, is_direct_question: bool = False) -> str:
        """
        Executes live Google web research, extracts factual summaries,
        and generates thoughtful AI insights and recommendations.
        Always opens the Google search results page directly in the user's browser in the foreground.
        """
        search_query = self._clean_search_query(query)

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
                if is_direct_question:
                    thoughts = [
                        f"'{search_query}' sorunu Google'da araştırdım ve arama sayfasını tarayıcında hemen önüne açtım. Elde ettiğim bilgilere göre: {fact_text} Aklına takılan başka bir detay olursa dinliyorum.",
                        f"Sorunu Google üzerinde araştırdım ve sonuçları önüne getirdim. Öne çıkan bilgiler şöyle: {fact_text} Tarayıcından sonuçlara göz atabilirsin.",
                        f"Google'da senin için araştırdım ve ilgili sayfayı web tarayıcında önüne getirdim. Veriler şunu gösteriyor: {fact_text} Başka bir şey öğrenmek istersen buradayım."
                    ]
                else:
                    thoughts = [
                        f"'{search_query}' konusunu araştırdım ve Google arama sayfasını tarayıcında hemen önüne açtım. Güncel bulgulara göre: {fact_text} Bana kalırsa veriler oldukça tutarlı görünüyor. İstersen bu başlığı daha derinlemesine analiz edebilirim.",
                        f"Google üzerindeki güncel kaynakları taradım ve web sayfasını önüne getirdim. Öne çıkan bilgiler şöyle: {fact_text} Şahsi fikrim, bu durumun yakından takip edilmesi gerektiği yönünde. Ne düşünüyorsun?",
                        f"Konuyu Google'da araştırdım ve ilgili kaynak sayfasını önüne açtım. Veriler şunu işaret ediyor: {fact_text} Bana kalırsa burada dikkat edilmesi gereken asıl nokta stratejiyi doğru kurmak. Farklı bir açıdan bakmamı ister misin?"
                    ]
                return random.choice(thoughts)
        except Exception:
            pass

        if is_direct_question:
            return f"'{search_query}' sorunu Google'da araştırdım ve arama sayfasını web tarayıcında hemen önüne açtım. Ekranda listelenen kaynaklardan detayları inceleyebilirsin; sormak istediğin başka bir soru varsa sendeyim."
        return f"'{search_query}' konusunu Google'da araştırdım ve arama sayfasını web tarayıcında önüne açtım. Konuyu biraz daha açarsan sana daha net bir analiz ve fikir sunabilirim."

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

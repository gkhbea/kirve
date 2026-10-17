"""
KİRVE AI OS - Interactive CLI Chat Interface
Windows 10/11 compatible command line interface.
"""
import sys
import os
from typing import Optional
from kirve.config import DEFAULT_MODEL, OLLAMA_BASE_URL
from kirve.memory import KirveMemory
from kirve.network import NetworkChecker
from kirve.llm_adapter import OllamaAdapter
from kirve.tools.security import default_security_agent
from kirve.tools.system_control import SystemControlTool
from kirve.tools.research_agent import ResearchAgent
from kirve.tools.ev_otomasyon import (
    EvOtomasyonAraci,
    ToggClimateRequest,
    ToggLockRequest,
    RoborockCleanRequest
)
from kirve.memory_vector import VectorMemory
from kirve.focus_monitor import FocusMonitor
from kirve.event_bus import default_event_bus

# ANSI Color codes for Windows 10/11 Terminal
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

# Ensure VT100 / ANSI escape sequence processing on Windows
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

class KirveCLI:
    """
    Main CLI Interface for KİRVE AI OS.
    """
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.memory = KirveMemory()
        self.vector_memory = VectorMemory()
        self.adapter = OllamaAdapter()
        self.security = default_security_agent
        self.system_control = SystemControlTool(security_agent=self.security)
        self.research_agent = ResearchAgent(security_agent=self.security)
        self.ev_otomasyon = EvOtomasyonAraci(memory=self.memory)
        self.event_bus = default_event_bus
        self.focus_monitor = FocusMonitor(event_bus=self.event_bus)
        self.focus_monitor.start_monitoring()
        
    def render_banner(self) -> None:
        """Prints a stylish and clear system banner."""
        is_online, net_desc = NetworkChecker.get_network_status()
        ollama_ok, ollama_desc = self.adapter.check_health()
        
        net_badge = f"{GREEN}[● Çevrimiçi]{RESET}" if is_online else f"{YELLOW}[○ Çevrimdışı (Yerel Mod)]{RESET}"
        llm_badge = f"{GREEN}[Ollama: {ollama_desc}]{RESET}" if ollama_ok else f"{RED}[Ollama: Bağlanamadı]{RESET}"
        
        print("\n" + "=" * 65)
        print(f"{CYAN}{BOLD}  KİRVE AI OS - Kişisel Yapay Zeka İşletim Sistemi (v0.1.0){RESET}")
        print(f"  Ağ Durumu: {net_badge} | {llm_badge}")
        print(f"  Model: {CYAN}{DEFAULT_MODEL}{RESET} | Hafıza: {DIM}{self.memory.db_path}{RESET}")
        print("=" * 65)
        print(f"{DIM}Komutlar: /durum, /gecmis, /temizle, /cikis{RESET}\n")

    def show_status(self) -> None:
        """Detailed status report."""
        is_online, _ = NetworkChecker.get_network_status()
        ollama_ok, ollama_msg = self.adapter.check_health()
        models = self.adapter.get_installed_models() if ollama_ok else []
        history = self.memory.get_history(self.session_id, limit=100)
        
        vec_status = "PostgreSQL + pgvector (Aktif)" if self.vector_memory.is_pg_active else "Yerel Vektör Deposu (Aktif/Fallback)"
        silent_status = f"{YELLOW}Açık (DND / Tam Ekran){RESET}" if self.focus_monitor.silent_mode else f"{GREEN}Kapalı (Normal){RESET}"

        print(f"\n{BOLD}--- Sistem Durum Raporu ---{RESET}")
        print(f"• İnternet Bağlantısı : {GREEN + 'Aktif' if is_online else YELLOW + 'Çevrimdışı (Offline)'}{RESET}")
        print(f"• Ollama Servisi      : {GREEN + 'Çalışıyor' if ollama_ok else RED + 'Ulaşılamıyor'}{RESET} ({ollama_msg})")
        print(f"• Vektör Veritabanı   : {CYAN}{vec_status}{RESET}")
        print(f"• Odaklanma / DND     : {silent_status}")
        print(f"• Yüklü Modeller      : {', '.join(models) if models else 'Yok / Servis Kapalı'}")
        print(f"• Aktif Oturum        : {self.session_id}")
        print(f"• Kayıtlı Mesaj Sayısı: {len(history)}")
        print(f"---------------------------\n")

    def show_history(self, limit: int = 5) -> None:
        """Displays recent conversation history from SQLite."""
        history = self.memory.get_history(self.session_id, limit=limit)
        if not history:
            print(f"{YELLOW}Kayıtlı geçmiş mesaj bulunamadı patron.{RESET}\n")
            return
            
        print(f"\n{BOLD}--- Son {len(history)} Mesaj (Hafıza) ---{RESET}")
        for item in history:
            role_label = f"{CYAN}Patron{RESET}" if item["role"] == "user" else f"{GREEN}KİRVE{RESET}"
            print(f"[{item['timestamp'][:19]}] {role_label}: {item['content']}")
        print(f"------------------------------------\n")

    def handle_command(self, cmd: str) -> bool:
        """
        Handles system slash commands.
        Returns True if command was processed, False otherwise.
        """
        raw = cmd.strip()
        c = raw.lower()
        if c in ["/cikis", "exit", "quit", ":q"]:
            print(f"\n{CYAN}KİRVE:{RESET} Görüşmek üzere patron, sistem beklemede.")
            self.focus_monitor.stop_monitoring()
            self.research_agent.close()
            self.ev_otomasyon.close()
            sys.exit(0)
        elif c in ["/durum", "/status"]:
            self.show_status()
            return True
        elif c in ["/odak", "/focus"]:
            state = self.focus_monitor.inspect_active_window()
            print(f"\n{BOLD}--- Windows Odak & Tam Ekran Durumu ---{RESET}")
            print(f"• Aktif Pencere : {state['title'] or '(Masaüstü / Sistem)'}")
            print(f"• Tam Ekran     : {'Evet' if state['is_fullscreen'] else 'Hayır'}")
            print(f"• Toplantı/Oyun : {'Evet' if state['is_meeting_or_game'] else 'Hayır'}")
            print(f"• Sessiz Mod    : {'Aktif (DND)' if self.focus_monitor.silent_mode else 'Pasif'}\n")
            return True
        elif c.startswith("/vektor"):
            query = raw[7:].strip()
            if not query:
                print(f"{YELLOW}Lütfen aranacak anlamı belirt patron. Örn: /vektor araba menzili{RESET}\n")
                return True
            print(f"{CYAN}KİRVE:{RESET} Vektör veritabanında semantik arama yapıyorum...\n")
            results = self.vector_memory.search_similar_messages(query, limit=3)
            if not results:
                print(f"{YELLOW}Benzer anlamlı kayıt bulunamadı patron.{RESET}\n")
            else:
                print(f"{BOLD}--- Semantik Vektör Eşleşmeleri ---{RESET}")
                for r in results:
                    print(f"• [Benzerlik: %{int(r['similarity'] * 100)}] {r['role']}: {r['content']}")
                print()
            return True
        elif c in ["/gecmis", "/history"]:
            self.show_history(limit=10)
            return True
        elif c.startswith("/togg"):
            parts = raw.split()
            if len(parts) > 1:
                sub = parts[1].lower()
                if sub in ["sarj", "şarj"]:
                    action = parts[2].lower() if len(parts) > 2 else "baslat"
                    start = action in ["baslat", "başlat", "start", "ac", "aç", "1"]
                    res = self.ev_otomasyon.set_togg_charging(start)
                    print(f"{GREEN}KİRVE:{RESET} {res['message']}\n")
                    return True
                elif sub in ["klima"]:
                    temp = float(parts[2]) if len(parts) > 2 else 22.0
                    res = self.ev_otomasyon.send_togg_climate_request(ToggClimateRequest(vin="TR-TOGG-01", action="START", target_temperature_c=temp))
                    print(f"{GREEN}KİRVE:{RESET} {res.message}\n")
                    return True
                elif sub in ["kilitle", "kilit"]:
                    lock_state = False if (len(parts) > 2 and parts[2].lower() in ["ac", "aç", "open"]) else True
                    res = self.ev_otomasyon.send_togg_lock_request(ToggLockRequest(vin="TR-TOGG-01", lock=lock_state))
                    print(f"{GREEN}KİRVE:{RESET} {res.message}\n")
                    return True

            togg = self.ev_otomasyon.get_togg_status()
            if togg["success"]:
                telem = togg["telemetry"]
                charge_str = f"{GREEN}Şarj Oluyor ({telem['charging_power_kw']} kW){RESET}" if telem["is_charging"] else f"{DIM}Şarjda Değil{RESET}"
                print(f"\n{BOLD}--- Togg T10X Durumu ---{RESET}")
                print(f"• Batarya: %{telem['battery_percentage']} | Kalan Menzil: {telem['range_km']} km")
                print(f"• Şarj Durumu: {charge_str}")
                print(f"• Kapılar: {'Kilitli' if telem['doors_locked'] else 'Açık'} | Klima: {'Açık' if telem['climate_active'] else 'Kapalı'}\n")
            else:
                print(f"{YELLOW}KİRVE:{RESET} {togg['message']}\n")
            return True
        elif c.startswith("/roborock"):
            parts = raw.split()
            if len(parts) > 1 and parts[1].lower() == "temizle":
                zone = parts[2] if len(parts) > 2 else "Salon"
                res = self.ev_otomasyon.send_roborock_clean_request(RoborockCleanRequest(device_id="RR-Q8", command="clean_zone", zone_name=zone))
                print(f"{GREEN}KİRVE:{RESET} {res.message}\n")
            elif len(parts) > 1 and parts[1].lower() == "dock":
                res = self.ev_otomasyon.dock_roborock()
                print(f"{GREEN}KİRVE:{RESET} {res['message']}\n")
            else:
                rr = self.ev_otomasyon.get_roborock_status()
                if rr["success"]:
                    telem = rr["telemetry"]
                    lidar_str = f"{GREEN}Aktif ({telem['lidar_status']}){RESET}" if telem['lidar_status'] == "OK" else f"{RED}Uyarı: {telem['lidar_status']}{RESET}"
                    print(f"\n{BOLD}--- Roborock Q8 Durumu ---{RESET}")
                    print(f"• LiDAR Sensörü: {lidar_str}")
                    print(f"• Batarya: %{telem['battery_percentage']} | Durum: {telem['cleaning_state']}")
                    print(f"• Son Temizlik: {telem['cleaned_area_m2']} m² ({telem['cleaning_time_minutes']} dk)\n")
                else:
                    print(f"{YELLOW}KİRVE:{RESET} {rr['message']}\n")
            return True
        elif c.startswith("/ev"):
            parts = raw.split()
            if len(parts) > 2 and parts[1].lower() in ["ac", "aç", "on"]:
                dev_id = parts[2].lower()
                res = self.ev_otomasyon.control_home_device(dev_id, "turn_on")
                msg = f"{dev_id} açıldı patron." if res["success"] else f"Hata: {res['message']}"
                print(f"{GREEN}KİRVE:{RESET} {msg}\n")
                return True
            elif len(parts) > 2 and parts[1].lower() in ["kapat", "off"]:
                dev_id = parts[2].lower()
                res = self.ev_otomasyon.control_home_device(dev_id, "turn_off")
                msg = f"{dev_id} kapatıldı patron." if res["success"] else f"Hata: {res['message']}"
                print(f"{GREEN}KİRVE:{RESET} {msg}\n")
                return True

            devices = self.ev_otomasyon.list_home_devices()
            retry_tasks = self.ev_otomasyon.get_retry_status()
            print(f"\n{BOLD}--- Google Home Cihazları ---{RESET}")
            for d in devices:
                status = f"{GREEN}Açık{RESET}" if d["state"].get("on") else f"{DIM}Kapalı{RESET}"
                print(f"• [{d['device_id']}] {d['name']} ({d['room']}): {status}")
            if retry_tasks:
                print(f"\n{YELLOW}Arka Planda Yeniden Denenen Cihazlar (Timeout / Retry):{RESET}")
                for r in retry_tasks:
                    print(f"• {r['device_name']}: Deneme {r['current_retry']}/{r['max_retries']} (Son Hata: {r['last_error']})")
            print()
            return True
        elif c in ["/sepet", "/cart"]:
            cart = self.research_agent.get_cart()
            if not cart["items"]:
                print(f"{YELLOW}Sepetiniz boş patron.{RESET}\n")
            else:
                print(f"\n{BOLD}--- Mevcut Alışveriş Sepeti ---{RESET}")
                for item in cart["items"]:
                    print(f"• {item['name']} x{item['quantity']} - {item['subtotal']} TL ({item['platform']})")
                print(f"Toplam Tutar: {GREEN}{BOLD}{cart['total_amount']} TL{RESET}\n")
            return True
        elif c in ["/ode", "/checkout"]:
            print(f"\n{YELLOW}Ödeme işlemi başlatılıyor...{RESET}")
            res = self.research_agent.checkout()
            if res.get("aborted"):
                print(f"{YELLOW}KİRVE:{RESET} {res['message']}\n")
            elif res["success"]:
                print(f"{GREEN}KİRVE:{RESET} {res['message']}\n")
            else:
                print(f"{RED}KİRVE:{RESET} {res.get('error', 'Hata oluştu')}\n")
            return True
        elif c.startswith("/arastir"):
            query = raw[8:].strip()
            if not query:
                print(f"{YELLOW}Lütfen aranacak ürünü belirt patron. Örnek: /arastir Roborock Q8{RESET}\n")
                return True
            print(f"{CYAN}KİRVE:{RESET} '{query}' için e-ticaret sitelerinden fiyatları topluyorum patron...\n")
            prices = self.research_agent.collect_prices(query)
            print(f"{BOLD}--- Fiyat Karşılaştırması ({prices['product_name']}) ---{RESET}")
            for offer in prices["offers"]:
                print(f"• {offer['platform']}: {offer['price']} {offer['currency']} (Puan: {offer['rating']})")
            print(f"En Uygun: {GREEN}{prices['cheapest_offer']['platform']} ({prices['cheapest_offer']['price']} TL){RESET}")
            print(f"Ortalama Fiyat: {prices['average_price']} TL\n")
            # Ask if patron wants to add cheapest to cart
            self.research_agent.add_to_cart(prices['cheapest_offer'])
            print(f"{DIM}En uygun teklif sepete eklendi. Sepeti görmek için /sepet, ödeme için /ode yazabilirsin.{RESET}\n")
            return True
        elif c in ["/temizle", "/clear"]:
            self.memory.clear_history(self.session_id)
            os.system("cls" if os.name == "nt" else "clear")
            self.render_banner()
            print(f"{GREEN}Ekran ve bu oturumun sohbet hafızası temizlendi patron.{RESET}\n")
            return True
        elif c in ["/yardim", "/help"]:
            print(f"\n{BOLD}Mevcut Komutlar:{RESET}")
            print("  /durum     - İnternet, Ollama ve veritabanı durumunu gösterir")
            print("  /arastir   - E-ticaret sitelerinden fiyat toplar (Örn: /arastir Roborock Q8)")
            print("  /sepet     - Sepetteki ürünleri ve toplam tutarı gösterir")
            print("  /ode       - Sepeti onaylar ve güvenli ödeme adımını başlatır")
            print("  /gecmis    - Son sohbet geçmişini SQLite'tan listeler")
            print("  /temizle   - Oturum hafızasını ve ekranı temizler")
            print("  /cikis     - KİRVE AI OS'tan güvenle çıkar\n")
            return True
        return False

    def run(self) -> None:
        """Starts the interactive CLI loop."""
        self.render_banner()
        print(f"{CYAN}KİRVE:{RESET} Emrindeyim patron, sistem hazır. Ne yapıyoruz?\n")
        
        while True:
            try:
                user_input = input(f"{BOLD}Patron > {RESET}").strip()
                if not user_input:
                    continue
                    
                # Handle slash commands
                if user_input.startswith("/") or user_input.lower() in ["exit", "quit"]:
                    if self.handle_command(user_input):
                        continue
                
                # Critical action guard check (Master Prompt rule)
                critical_keywords = ["e-posta gönder", "dosya sil", "ödeme yap", "sepeti onayla", "satın al"]
                is_critical = any(kw in user_input.lower() for kw in critical_keywords)
                
                # Save user message to SQLite memory and Vector Memory (PostgreSQL + pgvector)
                self.memory.add_message(role="user", content=user_input, session_id=self.session_id)
                try:
                    self.vector_memory.add_message(role="user", content=user_input, session_id=self.session_id)
                except Exception:
                    pass
                
                if is_critical:
                    # Explicit confirmation enforcement
                    warning_msg = f"{user_input} işlemini başlatıyorum, onaylıyor musun patron?"
                    print(f"\n{YELLOW}{BOLD}KİRVE (Kritik Onay):{RESET} {warning_msg}\n")
                    self.memory.add_message(role="assistant", content=warning_msg, session_id=self.session_id)
                    try:
                        self.vector_memory.add_message(role="assistant", content=warning_msg, session_id=self.session_id)
                    except Exception:
                        pass
                    continue

                # Fetch recent history for context
                recent_history = self.memory.get_history(session_id=self.session_id, limit=6)
                
                print(f"{DIM}[Düşünüyor...]{RESET}", end="\r")
                
                # Query local LLM adapter with fallback protection
                response = self.adapter.generate_response(
                    prompt=user_input,
                    history=recent_history
                )
                
                # Clear thinking indicator
                print(" " * 20, end="\r")
                
                reply_content = response["content"]
                
                # Display response
                prefix = f"{GREEN}KİRVE:{RESET}" if response["success"] else f"{YELLOW}KİRVE (Sistem/Fallback):{RESET}"
                print(f"{prefix} {reply_content}\n")
                
                # Save assistant response to SQLite and Vector memory
                meta = {"local": response.get("is_local"), "success": response.get("success")}
                self.memory.add_message(
                    role="assistant",
                    content=reply_content,
                    session_id=self.session_id,
                    metadata=meta
                )
                try:
                    self.vector_memory.add_message(
                        role="assistant",
                        content=reply_content,
                        session_id=self.session_id,
                        metadata=meta
                    )
                except Exception:
                    pass

            except (KeyboardInterrupt, EOFError):
                print(f"\n\n{CYAN}KİRVE:{RESET} Görüşmek üzere patron, kendine iyi bak.")
                break
            except Exception as e:
                print(f"\n{RED}Beklenmeyen bir hata oluştu: {str(e)}{RESET}\n")

if __name__ == "__main__":
    cli = KirveCLI()
    cli.run()

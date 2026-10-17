"""
KİRVE AI OS - Local LLM Adapter (Ollama)
Handles interaction with Ollama local LLM server and offline fallback logic.
"""
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Tuple, Optional
from kirve.config import OLLAMA_BASE_URL, DEFAULT_MODEL, REQUEST_TIMEOUT_SECONDS, KIRVE_SYSTEM_PROMPT
from kirve.network import NetworkChecker

class OllamaAdapter:
    """
    Adapter for communicating with the local Ollama LLM instance.
    Includes offline verification and fallback mechanisms.
    """
    def __init__(self, base_url: str = OLLAMA_BASE_URL, default_model: str = DEFAULT_MODEL, timeout: int = REQUEST_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout = timeout

    def check_health(self) -> Tuple[bool, str]:
        """
        Checks if the local Ollama daemon is reachable.
        Returns: (is_healthy, status_message)
        """
        url = f"{self.base_url}/api/version"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    version = data.get("version", "unknown")
                    return True, f"Ollama aktif (v{version})"
                return False, f"Ollama beklenmeyen durum kodu döndürdü: {response.status}"
        except urllib.error.URLError as e:
            return False, f"Ollama servisine ulaşılamadı ({e.reason})"
        except Exception as e:
            return False, f"Ollama bağlantı hatası: {str(e)}"

    def get_installed_models(self) -> List[str]:
        """
        Lists models currently installed locally in Ollama.
        """
        url = f"{self.base_url}/api/tags"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                    return models
                return []
        except Exception:
            return []

    def is_model_available(self, model_name: Optional[str] = None) -> bool:
        """
        Checks if the requested model exists locally in Ollama.
        """
        target = model_name or self.default_model
        models = self.get_installed_models()
        return any(target in m for m in models)

    def generate_response(
        self,
        prompt: str,
        history: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends chat conversation to Ollama /api/chat.
        Includes network and local model fallback mechanisms.
        """
        is_online = NetworkChecker.is_online()
        model = model_name or self.default_model
        sys_prompt = system_prompt or KIRVE_SYSTEM_PROMPT

        # Check local Ollama health first
        ollama_healthy, health_msg = self.check_health()

        if not ollama_healthy:
            # Fallback handling based on connectivity state
            return self._build_offline_fallback(
                is_online=is_online,
                reason=health_msg,
                model_name=model
            )

        # Prepare messages
        messages = [{"role": "system", "content": sys_prompt}]
        if history:
            for item in history:
                messages.append({
                    "role": item["role"],
                    "content": item["content"]
                })
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }

        url = f"{self.base_url}/api/chat"
        headers = {"Content-Type": "application/json"}
        req_data = json.dumps(payload).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    resp_data = json.loads(response.read().decode("utf-8"))
                    message = resp_data.get("message", {})
                    content = message.get("content", "").strip()
                    return {
                        "success": True,
                        "content": content,
                        "model": model,
                        "is_online": is_online,
                        "is_local": True,
                        "error": None
                    }
                else:
                    return {
                        "success": False,
                        "content": f"Patron, yerel model hata kodu döndürdü: {response.status}",
                        "model": model,
                        "is_online": is_online,
                        "is_local": True,
                        "error": f"HTTP {response.status}"
                    }
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass
            return {
                "success": False,
                "content": f"Patron, yerel model isteği işleyemedi ({e.code}). Modelin yüklü olduğunu doğrula ('ollama pull {model}').",
                "model": model,
                "is_online": is_online,
                "is_local": True,
                "error": f"HTTPError {e.code}: {error_body}"
            }
        except (urllib.error.URLError, TimeoutError) as e:
            return self._build_offline_fallback(
                is_online=is_online,
                reason=f"Zaman aşımı veya bağlantı kesintisi ({str(e)})",
                model_name=model
            )
        except Exception as e:
            return {
                "success": False,
                "content": f"Patron, beklenmeyen bir hata oluştu: {str(e)}",
                "model": model,
                "is_online": is_online,
                "is_local": True,
                "error": str(e)
            }

    def _build_offline_fallback(self, is_online: bool, reason: str, model_name: str) -> Dict[str, Any]:
        """
        Builds a structured fallback response preserving KİRVE's persona and tone.
        """
        if not is_online:
            message = (
                f"Patron, şu an çevrimdışıyız (internet bağlantısı yok) ve yerel Ollama servisine de ulaşılamadı. "
                f"Yerel yapay zeka moduna devam edebilmemiz için lütfen terminalden 'ollama serve' veya "
                f"'ollama run {model_name}' komutuyla servisi başlat."
            )
        else:
            message = (
                f"Patron, internet bağlantımız var fakat yerel Ollama servisi ({self.base_url}) kapalı görünüyor. "
                f"Yerel modelle çalışabilmem için lütfen Ollama'yı başlat: ({reason})."
            )

        return {
            "success": False,
            "content": message,
            "model": model_name,
            "is_online": is_online,
            "is_local": False,
            "error": reason
        }

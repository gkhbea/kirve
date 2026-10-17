"""
KİRVE AI OS - Security Layer (Security Agent)
Enforces strict patron confirmation for critical, irreversible operations
such as file deletion, payments, checkouts, and external data transmissions.
"""
from typing import Callable, Optional, Any, Dict
import functools

class SecurityAgent:
    """
    Mandatory security gatekeeper for KİRVE.
    Intercepts dangerous actions and demands explicit CLI confirmation [E/H].
    """
    def __init__(self, input_provider: Optional[Callable[[str], str]] = None):
        # input_provider defaults to Python built-in input()
        self._input_provider = input_provider or input

    def request_confirmation(self, action_description: str) -> bool:
        """
        Requests explicit confirmation from the patron via CLI.
        Expected format:
        '{action_description} yapıyorum, onaylıyor musun patron? [E/H]: '
        
        Returns True ONLY if user explicitly responds with 'E' / 'e' / 'evet'.
        """
        prompt_text = f"\n[GÜVENLİK UYARISI] {action_description} yapıyorum, onaylıyor musun patron? [E/H]: "
        try:
            response = self._input_provider(prompt_text).strip().lower()
            return response in ["e", "evet", "y", "yes"]
        except (KeyboardInterrupt, EOFError):
            return False

    def guard_action(self, action_name: str, action_func: Callable[[], Any]) -> Dict[str, Any]:
        """
        Executes action_func only if patron confirms.
        Otherwise safely halts and returns an audit record.
        """
        approved = self.request_confirmation(action_name)
        if not approved:
            return {
                "success": False,
                "aborted": True,
                "message": f"Patron onayı verilmediği için '{action_name}' işlemi iptal edildi."
            }
        
        # Execute guarded action
        try:
            result = action_func()
            if isinstance(result, dict):
                result["approved_by_patron"] = True
                if "success" not in result:
                    result["success"] = True
                return result
            return {
                "success": True,
                "approved_by_patron": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "approved_by_patron": True,
                "error": str(e)
            }

# Default singleton instance
default_security_agent = SecurityAgent()

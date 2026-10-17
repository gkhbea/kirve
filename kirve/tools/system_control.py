"""
KİRVE AI OS - System Control Tool
Controls local system operations using os and subprocess:
- File reading, writing, and guarded deletion
- Application launcher
- Directory listing
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from kirve.tools.security import SecurityAgent, default_security_agent

class SystemControlTool:
    """
    PC control module for KİRVE.
    Manages local filesystem and initiates applications safely on Windows.
    """
    def __init__(self, security_agent: Optional[SecurityAgent] = None):
        self.security = security_agent or default_security_agent

    def read_file(self, filepath: str) -> Dict[str, Any]:
        """
        Reads content of a file on the local filesystem.
        """
        p = Path(filepath).resolve()
        if not p.exists():
            return {"success": False, "error": f"Dosya bulunamadı: {filepath}"}
        if not p.is_file():
            return {"success": False, "error": f"Belirtilen yol bir dosya değil: {filepath}"}

        try:
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "success": True,
                "path": str(p),
                "size_bytes": p.stat().st_size,
                "content": content
            }
        except UnicodeDecodeError:
            # Fallback to binary/latin-1 if needed
            try:
                with open(p, "r", encoding="latin-1") as f:
                    content = f.read()
                return {
                    "success": True,
                    "path": str(p),
                    "size_bytes": p.stat().st_size,
                    "content": content,
                    "encoding": "latin-1"
                }
            except Exception as e:
                return {"success": False, "error": f"Dosya okuma hatası: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Dosya açılamadı: {str(e)}"}

    def write_file(self, filepath: str, content: str, append: bool = False) -> Dict[str, Any]:
        """
        Writes or appends text content to a target file.
        Creates parent directories automatically if they don't exist.
        """
        try:
            p = Path(filepath).resolve()
            p.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if append else "w"
            with open(p, mode, encoding="utf-8") as f:
                f.write(content)
            return {
                "success": True,
                "path": str(p),
                "bytes_written": len(content.encode("utf-8")),
                "mode": mode
            }
        except Exception as e:
            return {"success": False, "error": f"Dosya yazma hatası: {str(e)}"}

    def delete_file(self, filepath: str) -> Dict[str, Any]:
        """
        CRITICAL ACTION: Deletes a target file.
        MANDATORY SECURITY GUARD: Prompts patron for explicit [E/H] confirmation.
        """
        p = Path(filepath).resolve()
        if not p.exists():
            return {"success": False, "error": f"Silinecek dosya bulunamadı: {filepath}"}

        action_name = f"'{p.name}' dosyasını kalıcı olarak silme işlemini"

        def _do_delete() -> Dict[str, Any]:
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                # Directory deletion
                os.rmdir(p)
            return {
                "success": True,
                "deleted": True,
                "path": str(p),
                "message": f"'{p.name}' dosyası başarıyla silindi patron."
            }

        return self.security.guard_action(action_name=action_name, action_func=_do_delete)

    def open_application(self, app_name_or_path: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Launches an application or executable using subprocess.Popen.
        Works across Windows standard commands and custom executable paths.
        """
        try:
            cmd = [app_name_or_path]
            if args:
                cmd.extend(args)

            # On Windows, use shell=True for system commands like 'notepad', 'calc', 'explorer'
            is_windows = sys.platform == "win32"
            proc = subprocess.Popen(
                cmd if not is_windows else app_name_or_path,
                shell=is_windows,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS if is_windows else 0
            )

            return {
                "success": True,
                "pid": proc.pid,
                "application": app_name_or_path,
                "message": f"'{app_name_or_path}' uygulaması başlatıldı (PID: {proc.pid})."
            }
        except Exception as e:
            return {
                "success": False,
                "application": app_name_or_path,
                "error": f"Uygulama başlatılamadı: {str(e)}"
            }

    def list_directory(self, dirpath: str = ".") -> Dict[str, Any]:
        """
        Lists directory contents.
        """
        try:
            p = Path(dirpath).resolve()
            if not p.exists():
                return {"success": False, "error": f"Dizin bulunamadı: {dirpath}"}
            if not p.is_dir():
                return {"success": False, "error": f"Belirtilen yol bir dizin değil: {dirpath}"}

            items = []
            for item in p.iterdir():
                items.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size_bytes": item.stat().st_size if item.is_file() else 0
                })

            return {
                "success": True,
                "path": str(p),
                "items": items,
                "total_items": len(items)
            }
        except Exception as e:
            return {"success": False, "error": f"Dizin listeleme hatası: {str(e)}"}

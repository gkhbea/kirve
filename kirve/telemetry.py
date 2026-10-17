"""
KİRVE AI OS - Live Hardware & Network Telemetry (psutil)
Collects real system CPU, RAM, and Network data for the HUD dashboard.
"""
import time
import psutil
from typing import Dict, Any

class SystemTelemetry:
    """
    Live hardware monitor using real OS data via psutil.
    """
    def __init__(self):
        self._last_net_time = time.time()
        self._last_net_io = psutil.net_io_counters()

    def get_snapshot(self) -> Dict[str, Any]:
        """
        Samples real system metrics:
        - CPU percent (overall & per core count)
        - Virtual memory (RAM used, total, percent)
        - Network transmission rates (KB/s upload/download)
        """
        # 1. CPU
        cpu_pct = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count(logical=True)

        # 2. RAM (Memory)
        vmem = psutil.virtual_memory()
        ram_pct = vmem.percent
        ram_used_gb = round(vmem.used / (1024 ** 3), 2)
        ram_total_gb = round(vmem.total / (1024 ** 3), 2)

        # 3. Network I/O
        now = time.time()
        dt = max(now - self._last_net_time, 0.001)
        current_net = psutil.net_io_counters()

        bytes_sent_delta = max(current_net.bytes_sent - self._last_net_io.bytes_sent, 0)
        bytes_recv_delta = max(current_net.bytes_recv - self._last_net_io.bytes_recv, 0)

        upload_kb_s = round((bytes_sent_delta / 1024) / dt, 1)
        download_kb_s = round((bytes_recv_delta / 1024) / dt, 1)

        self._last_net_time = now
        self._last_net_io = current_net

        return {
            "cpu_percent": cpu_pct,
            "cpu_count": cpu_count,
            "ram_percent": ram_pct,
            "ram_used_gb": ram_used_gb,
            "ram_total_gb": ram_total_gb,
            "net_download_kb_s": download_kb_s,
            "net_upload_kb_s": upload_kb_s,
            "net_total_sent_mb": round(current_net.bytes_sent / (1024 ** 2), 1),
            "net_total_recv_mb": round(current_net.bytes_recv / (1024 ** 2), 1),
            "timestamp": now
        }

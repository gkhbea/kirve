"""
KİRVE AI OS - Network & Connectivity Module
"""
import socket
from typing import Tuple
from kirve.config import CONNECTIVITY_TEST_HOST, CONNECTIVITY_TEST_PORT, CONNECTIVITY_TIMEOUT

class NetworkChecker:
    @staticmethod
    def is_online(host: str = CONNECTIVITY_TEST_HOST, 
                  port: int = CONNECTIVITY_TEST_PORT, 
                  timeout: float = CONNECTIVITY_TIMEOUT) -> bool:
        """
        Quickly checks if there is an active internet connection
        by attempting a lightweight socket handshake to a public DNS server.
        """
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (OSError, socket.timeout):
            return False

    @classmethod
    def get_network_status(cls) -> Tuple[bool, str]:
        """
        Returns boolean status and human-readable description.
        """
        online = cls.is_online()
        if online:
            return True, "Çevrimiçi (Online)"
        return False, "Çevrimdışı (Offline)"

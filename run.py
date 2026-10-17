#!/usr/bin/env python3
"""
KİRVE AI OS Entrypoint
Usage: python run.py
"""
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from kirve.cli import KirveCLI

def main():
    cli = KirveCLI()
    cli.run()

if __name__ == "__main__":
    main()

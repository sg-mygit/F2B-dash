#!/usr/bin/env python3
"""
ban-app main runner
Runs collector then generator in sequence.
Usage: python3 banapp.py [--collect-only] [--generate-only]
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    args = sys.argv[1:]
    collect_only  = "--collect-only"  in args
    generate_only = "--generate-only" in args

    if not generate_only:
        print("=== Collecting fail2ban data ===")
        from collector import collect
        collect()

    if not collect_only:
        print("=== Generating HTML dashboard ===")
        from generator import generate
        generate()

if __name__ == "__main__":
    main()

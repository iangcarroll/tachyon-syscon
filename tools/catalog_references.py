"""Compatibility entrypoint for pinned reference fetching and verification.

Use --check for read-only cache verification; hardware groups are opt-in.
"""
from fetch_references import main

if __name__ == '__main__':
    main()

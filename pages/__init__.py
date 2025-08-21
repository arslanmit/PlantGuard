"""Pages package for Streamlit app.

This file makes the `pages` directory a proper Python package so static
analysis tools treat modules as `pages.<module>` only.
"""

__all__ = [
    "compare",
    "guide",
    "history",
    "home",
    "settings",
]

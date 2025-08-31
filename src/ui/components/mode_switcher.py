"""Lightweight ModeSwitcher component for simple mode selection."""


import streamlit as st


class ModeSwitcher:
    """Simple mode switcher used by the app and tests."""

    def __init__(self, session_key: str = "input_mode", default_mode: str = "vision") -> None:
        self.session_key = session_key
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = default_mode

    def render(self) -> str:
        return st.session_state.get(self.session_key, "vision")


__all__ = ["ModeSwitcher"]

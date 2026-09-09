"""
Signal Lab. Read SUBSTRATE.md first; it is the constitution of this repository.

Namespaced under `signal_lab` rather than as flat top-level packages, per
decisions/0010: `stats`, `results` and `signals` are all plausible names for a
third-party dependency, and a shadowing collision would be diagnosed as a
mysterious import error rather than as a layout problem. SUBSTRATE section 15
was amended to match.
"""

__all__ = ["params"]

"""
Secrets read from the environment, refused when malformed.

Task 23 lost a day to a `401` that was, in part, a trailing carriage return on
`DQ_CLIENT_ID`: a CRLF `.env` sourced in WSL leaves `\\r` on every value, and
the vendor reports it as bad credentials, which points everywhere but here.

A malformed value is **refused, not repaired** (SUBSTRATE section 10's
fail-loud rule): silently stripping it would hide which file is wrong. The
error names the variable and the defect only -- never the value, its length or
any slice of it.
"""

from __future__ import annotations


def secret_defect(value: str) -> str | None:
    """What is wrong with `value`, in words that do not reveal it, or None."""
    if value.endswith("\r"):
        return "a trailing carriage return -- is .env CRLF? run: sed -i 's/\\r$//' .env"
    if "\r" in value or "\n" in value:
        return "an embedded line break -- is .env CRLF or a value split across lines?"
    if value != value.lstrip():
        return "leading whitespace"
    if value != value.rstrip():
        return "trailing whitespace"
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        return "a control character"
    return None


def check_secret(name: str, value: str) -> str:
    """Return `value` unchanged if well-formed; otherwise raise naming `name`."""
    defect = secret_defect(value)
    if defect:
        raise RuntimeError(f"{name} has {defect}")
    return value

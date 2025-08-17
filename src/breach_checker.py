# breach_checker.py
from __future__ import annotations
import hashlib, urllib.request, urllib.error, ssl
from typing import Dict

API_BASE = "https://api.pwnedpasswords.com/range/"
USER_AGENT = "PasswordStrengthBreachChecker/1.0 (+local)"
ADD_PADDING = "true"  # privacy hardening

_CACHE: Dict[str, str] = {}
_MAX_CACHE = 256

def sha1_hex(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest().upper()

def _fetch_prefix(prefix: str, timeout: float = 8.0) -> str:
    if prefix in _CACHE:
        return _CACHE[prefix]
    req = urllib.request.Request(
        API_BASE + prefix,
        headers={"User-Agent": USER_AGENT, "Add-Padding": ADD_PADDING},
        method="GET",
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        text = resp.read().decode("utf-8", errors="ignore")
    if len(_CACHE) >= _MAX_CACHE:
        _CACHE.clear()
    _CACHE[prefix] = text
    return text

def check_pwned_password(password: str, timeout: float = 8.0) -> dict:
    """Return dict: {'ok': bool, 'found': bool, 'count': int, 'error': str|None}"""
    if not password:
        return {"ok": False, "found": False, "count": 0, "error": "empty_password"}
    full = sha1_hex(password)
    prefix, suffix = full[:5], full[5:]
    try:
        blob = _fetch_prefix(prefix, timeout=timeout)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            retry = e.headers.get("Retry-After", "2")
            return {"ok": False, "found": False, "count": 0, "error": f"rate_limited:{retry}"}
        return {"ok": False, "found": False, "count": 0, "error": "http_error"}
    except Exception:
        return {"ok": False, "found": False, "count": 0, "error": "network_error"}
    count = 0
    for line in blob.splitlines():
        if ":" not in line:
            continue
        sfx, cnt = line.split(":", 1)
        if sfx.strip().upper() == suffix:
            try:
                count = int(cnt.strip())
            except Exception:
                count = 1
            break
    return {"ok": True, "found": count > 0, "count": count, "error": None}

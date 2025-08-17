import math
import string

def char_pool_size(pwd: str) -> int:
    pool = 0
    if any(c.islower() for c in pwd): pool += 26
    if any(c.isupper() for c in pwd): pool += 26
    if any(c.isdigit() for c in pwd): pool += 10
    if any(c in string.punctuation for c in pwd): pool += len(string.punctuation)
    if " " in pwd: pool += 1
    return pool

def estimate_entropy_bits(pwd: str) -> float:
    if not pwd:
        return 0.0
    pool = char_pool_size(pwd)
    if pool <= 1:
        return 0.0
    return len(pwd) * math.log2(pool)

def estimate_crack_time_seconds(bits: float, guesses_per_sec: float) -> float:
    if bits <= 0:
        return 0.0
    total = 0.5 * math.pow(2.0, bits)
    return total / max(guesses_per_sec, 1.0)

def format_duration(seconds: float) -> str:
    if seconds < 1:
        return "<1 sec"
    units = [
        ("year", 365*24*3600),
        ("day", 24*3600),
        ("hour", 3600),
        ("min", 60),
        ("sec", 1),
    ]
    parts = []
    remaining = int(seconds)
    for name, size in units:
        if remaining >= size:
            qty = remaining // size
            remaining -= qty * size
            parts.append(f"{qty} {name}{'' if qty==1 else 's'}")
        if len(parts) >= 2:
            break
    return " ".join(parts)

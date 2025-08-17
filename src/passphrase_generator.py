# passphrase_generator.py
import secrets, math, os, sys
from pathlib import Path

# --- helper for PyInstaller bundled files ---
def resource_path(*parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)

FALLBACK_WORDLIST = [
    "correct","horse","battery","staple","orbit","cable","spice","velvet",
    "coconut","window","planet","random","forest","silver","puzzle","ember",
    "rocket","coffee","yellow","tiger","lamp","garden","velcro","pebble",
    "ocean","paper","guitar","marble","castle","jungle","soda","meteor",
]
SYMBOLS = "!@#$%^&*?-_=+."

# updated paths: first check bundled, then fallback
WORDLIST_PATHS = [
    Path(resource_path("data", "eff_large_wordlist.txt")),
    Path("data/eff_large_wordlist.txt"),
    Path("eff_large_wordlist.txt"),
]

def _load_words():
    for p in WORDLIST_PATHS:
        if p.exists():
            words = []
            with p.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    w = line.split()[-1].lower()  # accept '11111 aardvark' or 'aardvark'
                    # allow letters, hyphen, apostrophe
                    if all(ch.isalpha() or ch in "-'" for ch in w):
                        words.append(w)
            if words:
                return words
    return FALLBACK_WORDLIST

_WORDS = _load_words()

def generate_passphrase(num_words=4, separator="-", capitalize=False, add_number=False, add_symbol=False):
    k = max(3, int(num_words))
    words = [secrets.choice(_WORDS) for _ in range(k)]
    if capitalize:
        words = [w.capitalize() for w in words]
    phrase = separator.join(words)
    if add_number:
        phrase += separator + str(secrets.randbelow(10))
    if add_symbol:
        phrase += separator + secrets.choice(SYMBOLS)
    return phrase

def estimate_entropy_bits(num_words, add_number=False, add_symbol=False, wordlist_size=None):
    n = int(wordlist_size) if wordlist_size else len(_WORDS)
    k = max(3, int(num_words))
    bits = k * math.log2(n)
    if add_number: bits += math.log2(10)
    if add_symbol: bits += math.log2(len(SYMBOLS))
    return round(bits, 2)

def get_wordlist_size():
    return len(_WORDS)

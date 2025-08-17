import re

COMMON_WORDS = {
    "password","admin","welcome","letmein","dragon","monkey",
    "login","qwerty","iloveyou","abc123","football","baseball",
    "princess","shadow","master","superman","hello"
}

KEYBOARD_ROWS = [
    "1234567890",
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm"
]

def leet_normalize(s: str) -> str:
    table = str.maketrans({
        "@": "a", "4": "a",
        "0": "o",
        "1": "l",
        "!": "i",
        "$": "s", "5": "s",
        "3": "e",
        "7": "t"
    })
    return s.lower().translate(table)

def has_repeated_runs(s: str, run_len: int = 3) -> bool:
    return re.search(r"(.)\1{" + str(run_len-1) + r",}", s) is not None

def has_simple_sequence(s: str, min_len: int = 4) -> bool:
    if len(s) < min_len:
        return False
    lower = s.lower()
    for i in range(len(lower) - min_len + 1):
        chunk = lower[i:i+min_len]
        if all(ord(chunk[j+1]) - ord(chunk[j]) == 1 for j in range(len(chunk)-1)):
            return True
    return False

def has_keyboard_walk(s: str, min_len: int = 4) -> bool:
    lower = re.sub(r"[^a-z0-9]", "", s.lower())
    if len(lower) < min_len:
        return False
    for row in KEYBOARD_ROWS:
        for i in range(len(row) - min_len + 1):
            seq = row[i:i+min_len]
            if seq in lower:
                return True
    return False

def contains_year(s: str, start=2010, end=2030) -> bool:
    m = re.search(r"(20[1-3]\d)", s)
    return bool(m and start <= int(m.group(1)) <= end)

def contains_common_word_or_leet(s: str) -> bool:
    plain = s.lower()
    leet  = leet_normalize(s)
    for w in COMMON_WORDS:
        if w in plain or w in leet:
            return True
    return False

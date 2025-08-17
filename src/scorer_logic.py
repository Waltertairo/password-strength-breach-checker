import string
from entropy import estimate_entropy_bits, estimate_crack_time_seconds
from patterns import (
    has_repeated_runs, has_simple_sequence, has_keyboard_walk,
    contains_year, contains_common_word_or_leet
)

def compute_score(pwd: str):
    length = len(pwd)
    reasons = []

    has_lower = any(c.islower() for c in pwd)
    has_upper = any(c.isupper() for c in pwd)
    has_digit = any(c.isdigit() for c in pwd)
    has_symbol = any(c in string.punctuation for c in pwd)
    classes = sum([has_lower, has_upper, has_digit, has_symbol])

    length_score  = min(50, int(length * 50 / 16))
    variety_score = (classes * 10)

    bonus = 0
    if length >= 12 and classes >= 3:
        bonus += 5
    if length >= 16 and classes == 4:
        bonus += 10

    raw = length_score + variety_score + bonus

    deduction = 0
    max_deduction = 35
    if has_repeated_runs(pwd, 3):
        deduction += 8; reasons.append("Avoid repeating characters like 'aaa' or '111'.")
    if has_simple_sequence(pwd, 4):
        deduction += 8; reasons.append("Avoid simple sequences like 'abcd' or '1234'.")
    if has_keyboard_walk(pwd, 4):
        deduction += 6; reasons.append("Avoid keyboard patterns like 'qwerty' or 'asdf'.")
    if contains_year(pwd):
        deduction += 5; reasons.append("Avoid using a year (e.g., 2024).")
    if contains_common_word_or_leet(pwd):
        deduction += 10; reasons.append("Avoid common words (even with leetspeak).")
    deduction = min(deduction, max_deduction)

    score = max(0, min(100, raw - deduction))

    if length < 12:
        reasons.append("Use at least 12 characters.")
    if classes < 4:
        missing = []
        if not has_lower:  missing.append("lowercase")
        if not has_upper:  missing.append("uppercase")
        if not has_digit:  missing.append("digits")
        if not has_symbol: missing.append("symbols")
        reasons.append("Add " + ", ".join(missing) + ".")
    if length >= 12 and classes >= 3 and score < 90:
        reasons.append("Make it a bit longer (14–16) or add more variety.")

    label = "Weak" if score < 50 else ("Medium" if score < 80 else "Strong")

    bits = estimate_entropy_bits(pwd)
    t1 = estimate_crack_time_seconds(bits, 1e9)    # 1e9 guesses/s
    t2 = estimate_crack_time_seconds(bits, 1e12)   # 1e12 guesses/s
    return score, label, reasons, bits, t1, t2

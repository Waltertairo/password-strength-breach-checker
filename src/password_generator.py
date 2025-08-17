import string
import secrets

def generate_password(length: int = 16, include_symbols: bool = True) -> str:
    """
    Crypto-strong generator using secrets.
    Ensures at least one lower, upper, digit, (symbol if selected).
    """
    if length < 8:
        length = 8  # safety floor

    lowers = string.ascii_lowercase
    uppers = string.ascii_uppercase
    digits = string.digits
    symbols = string.punctuation if include_symbols else ""

    required = [secrets.choice(lowers), secrets.choice(uppers), secrets.choice(digits)]
    if include_symbols:
        required.append(secrets.choice(symbols))

    pool = lowers + uppers + digits + symbols
    while len(required) < length:
        required.append(secrets.choice(pool))

    # Fisher–Yates shuffle using secrets.randbelow
    pwd_list = required[:]
    for i in range(len(pwd_list) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        pwd_list[i], pwd_list[j] = pwd_list[j], pwd_list[i]

    return "".join(pwd_list)

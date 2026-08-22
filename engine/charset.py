LOOKALIKES = set("0O1lI")

NUMERIC = "0123456789"
LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWER = "abcdefghijklmnopqrstuvwxyz"
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"
SYMBOLS = "!@#$%^&*()-_=+[]{}"

PIN_TYPES = {
    "numeric": NUMERIC,
    "letters": LETTERS,
    "alphanumeric": LETTERS + NUMERIC,
}


class CharsetError(ValueError):
    pass


def apply_lookalikes(alphabet, avoid):
    if not avoid:
        return alphabet
    return "".join(ch for ch in alphabet if ch not in LOOKALIKES)


def pin_alphabet(kind, avoid_lookalikes=False):
    if kind not in PIN_TYPES:
        raise CharsetError("unknown PIN type: %s" % kind)
    alphabet = apply_lookalikes(PIN_TYPES[kind], avoid_lookalikes)
    if not alphabet:
        raise CharsetError("PIN alphabet is empty")
    return alphabet


def password_alphabet(lower, upper, digits, symbols, avoid_lookalikes=False):
    parts = []
    if lower:
        parts.append(LOWER)
    if upper:
        parts.append(UPPER)
    if digits:
        parts.append(DIGITS)
    if symbols:
        parts.append(SYMBOLS)
    if not parts:
        raise CharsetError("select at least one character class")
    alphabet = apply_lookalikes("".join(parts), avoid_lookalikes)
    classes = []
    if lower:
        classes.append(apply_lookalikes(LOWER, avoid_lookalikes))
    if upper:
        classes.append(apply_lookalikes(UPPER, avoid_lookalikes))
    if digits:
        classes.append(apply_lookalikes(DIGITS, avoid_lookalikes))
    if symbols:
        classes.append(apply_lookalikes(SYMBOLS, avoid_lookalikes))
    classes = [c for c in classes if c]
    if not alphabet or not classes:
        raise CharsetError("character set is empty")
    return alphabet, classes


PRESETS = {
    "simple": {
        "lower": True,
        "upper": True,
        "digits": True,
        "symbols": False,
        "length": 16,
    },
    "strong": {
        "lower": True,
        "upper": True,
        "digits": True,
        "symbols": True,
        "length": 20,
    },
    "paranoid": {
        "lower": True,
        "upper": True,
        "digits": True,
        "symbols": True,
        "length": 32,
    },
}

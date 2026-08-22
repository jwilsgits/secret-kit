import hashlib
import hmac
import os
import re

INFO = b"secret-kit-v1"
RANKS = "A23456789TJQK"
SUITS = "CDHS"
ALL_CARDS = [r + s for r in RANKS for s in SUITS]


class EntropyError(ValueError):
    pass


def require_urandom():
    probe = os.urandom(32)
    if len(probe) != 32:
        raise EntropyError("os.urandom is unavailable")
    return probe


def hkdf_sha256(ikm, salt, info, length):
    if length <= 0 or length > 255 * 32:
        raise EntropyError("invalid HKDF length")
    if salt is None:
        salt = b"\x00" * hashlib.sha256().digest_size
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    okm = b""
    block = b""
    counter = 1
    while len(okm) < length:
        block = hmac.new(prk, block + info + bytes([counter]), hashlib.sha256).digest()
        okm += block
        counter += 1
    return okm[:length]


def parse_dice(text):
    """Return the normalized dice string, or '' if unused. Reject bad input."""
    if text is None:
        return ""
    compact = re.sub(r"\s+", "", str(text))
    if not compact:
        return ""
    if not re.fullmatch(r"[1-6]+", compact):
        raise EntropyError("dice must be digits 1-6 only")
    return compact


def parse_cards(text):
    """Return the 52-card sequence, or '' if unused. Reject incomplete/dup decks."""
    if text is None:
        return ""
    raw = str(text).strip()
    if not raw:
        return ""
    tokens = re.findall(r"[A-Za-z0-9]{2}", raw.upper().replace("10", "T"))
    if len(tokens) != 52:
        raise EntropyError("card shuffle must list all 52 unique cards")
    normalized = []
    seen = set()
    for tok in tokens:
        if tok[0] not in RANKS or tok[1] not in SUITS:
            raise EntropyError("invalid card: %s" % tok)
        if tok in seen:
            raise EntropyError("duplicate card: %s" % tok)
        seen.add(tok)
        normalized.append(tok)
    if seen != set(ALL_CARDS):
        raise EntropyError("card shuffle must be a complete 52-card deck")
    return " ".join(normalized)


class ByteSource(object):
    def __init__(self, data):
        self.data = data
        self.i = 0

    def need(self, n):
        if self.i + n > len(self.data):
            extra = os.urandom(n)
            return extra
        chunk = self.data[self.i : self.i + n]
        self.i += n
        return chunk

    def randbelow(self, n):
        if n <= 0:
            raise EntropyError("randbelow requires n > 0")
        if n == 1:
            return 0
        if n <= 256:
            limit = (256 // n) * n
            while True:
                x = self.need(1)[0]
                if x < limit:
                    return x % n
        limit = (2 ** 32 // n) * n
        while True:
            x = int.from_bytes(self.need(4), "big")
            if x < limit:
                return x % n

    def choice(self, seq):
        return seq[self.randbelow(len(seq))]


class EntropyPool(object):
    def __init__(self):
        require_urandom()
        self.clear()

    def clear(self):
        self._mouse = hashlib.sha256()
        self._mouse_n = 0

    def absorb_mouse(self, samples):
        if not samples:
            return self._mouse_n
        for sample in samples:
            if isinstance(sample, dict):
                t = sample.get("t", 0)
                x = sample.get("x", 0)
                y = sample.get("y", 0)
            else:
                t, x, y = sample[0], sample[1], sample[2]
            self._mouse.update(("%s,%s,%s\n" % (t, x, y)).encode("utf-8"))
            self._mouse_n += 1
        return self._mouse_n

    def mix(self, dice="", cards="", nbytes=256):
        require_urandom()
        os_bytes = os.urandom(32)
        dice_n = parse_dice(dice)
        cards_n = parse_cards(cards)
        parts = []
        if self._mouse_n:
            parts.append(self._mouse.digest())
        if dice_n:
            parts.append(dice_n.encode("utf-8"))
        if cards_n:
            parts.append(cards_n.encode("utf-8"))
        if parts:
            salt = hashlib.sha256(b"".join(parts)).digest()
            return hkdf_sha256(os_bytes, salt, INFO, nbytes)
        return os.urandom(nbytes)

    @property
    def mouse_samples(self):
        return self._mouse_n

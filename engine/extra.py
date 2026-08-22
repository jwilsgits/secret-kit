from engine.charset import CharsetError
from engine.wordlist import english_words

CODE_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"


def generate_hex(source, nbytes=32):
    if nbytes not in (16, 32, 64):
        raise CharsetError("hex key length must be 16, 32, or 64 bytes")
    return source.need(nbytes).hex()


def generate_uuid(source):
    raw = bytearray(source.need(16))
    raw[6] = (raw[6] & 0x0F) | 0x40
    raw[8] = (raw[8] & 0x3F) | 0x80
    h = raw.hex()
    return "%s-%s-%s-%s-%s" % (h[0:8], h[8:12], h[12:16], h[16:20], h[20:32])


def generate_codes(source, count=8):
    if count < 4 or count > 20:
        raise CharsetError("backup code count must be 4-20")
    codes = []
    for _ in range(count):
        body = "".join(source.choice(CODE_ALPHABET) for _ in range(10))
        codes.append(body[:5] + "-" + body[5:])
    return codes


def generate_diceware(source, words=6):
    if words < 4 or words > 8:
        raise CharsetError("diceware phrase must be 4-8 words")
    pool = list(english_words())
    picked = []
    for _ in range(words):
        word = source.choice(pool)
        pool.remove(word)
        picked.append(word)
    return " ".join(picked)

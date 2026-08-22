import hashlib
import unicodedata

from engine.charset import CharsetError
from engine.wordlist import english_words


def mnemonic_from_entropy(entropy, words=None):
    if words is None:
        words = english_words()
    if len(entropy) not in (16, 32):
        raise CharsetError("BIP-39 entropy must be 16 or 32 bytes")
    if len(words) != 2048:
        raise CharsetError("wordlist must have 2048 entries")
    ent_bits = len(entropy) * 8
    cs_bits = ent_bits // 32
    digest = hashlib.sha256(entropy).digest()
    checksum = int.from_bytes(digest, "big") >> (256 - cs_bits)
    bits = (int.from_bytes(entropy, "big") << cs_bits) | checksum
    total_bits = ent_bits + cs_bits
    out = []
    for i in range(total_bits // 11):
        shift = total_bits - 11 * (i + 1)
        idx = (bits >> shift) & 0x7FF
        out.append(words[idx])
    return " ".join(out)


def generate_mnemonic(source, word_count=12):
    if word_count not in (12, 24):
        raise CharsetError("BIP-39 word count must be 12 or 24")
    nbytes = 16 if word_count == 12 else 32
    entropy = source.need(nbytes)
    return mnemonic_from_entropy(entropy)


def validate_mnemonic(phrase, words=None):
    if words is None:
        words = english_words()
    parts = phrase.strip().split()
    if len(parts) not in (12, 24):
        return False
    index = {w: i for i, w in enumerate(words)}
    try:
        idxs = [index[w] for w in parts]
    except KeyError:
        return False
    word_count = len(parts)
    ent_bits = {12: 128, 24: 256}[word_count]
    cs_bits = ent_bits // 32
    total_bits = ent_bits + cs_bits
    bits = 0
    for idx in idxs:
        bits = (bits << 11) | idx
    checksum = bits & ((1 << cs_bits) - 1)
    entropy_int = bits >> cs_bits
    entropy = entropy_int.to_bytes(ent_bits // 8, "big")
    digest = hashlib.sha256(entropy).digest()
    expected = int.from_bytes(digest, "big") >> (256 - cs_bits)
    return checksum == expected


def mnemonic_to_seed(phrase, passphrase=""):
    mnemonic = unicodedata.normalize("NFKD", " ".join(phrase.split()))
    salt = unicodedata.normalize("NFKD", "mnemonic" + (passphrase or ""))
    return hashlib.pbkdf2_hmac(
        "sha512",
        mnemonic.encode("utf-8"),
        salt.encode("utf-8"),
        2048,
    )

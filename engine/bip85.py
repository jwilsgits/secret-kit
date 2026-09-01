import hmac
import hashlib

from engine.bip32 import Node
from engine.bip39 import mnemonic_from_entropy, mnemonic_to_seed, validate_mnemonic
from engine.charset import CharsetError
from engine.secp256k1 import SecpError

BIP85_HMAC_KEY = b"bip-entropy-from-k"
WARNING = "The master seed can recreate this child."


def _path(words, index):
    return "m/83696968'/39'/0'/%d'/%d'" % (words, index)


def mnemonic_from_node(root, words, index):
    if words not in (12, 24):
        raise CharsetError("BIP-85 word count must be 12 or 24")
    index = int(index)
    if index < 0 or index > 999:
        raise CharsetError("BIP-85 index must be 0–999")
    try:
        child = root.derive(_path(words, index))
    except SecpError as exc:
        raise CharsetError("invalid BIP-85 child; try the next index") from exc
    if child.priv is None:
        raise CharsetError("BIP-85 needs a private key")
    digest = hmac.new(BIP85_HMAC_KEY, child.priv, hashlib.sha512).digest()
    nbytes = 16 if words == 12 else 32
    return mnemonic_from_entropy(digest[:nbytes])


def derive_bip85_mnemonic(mnemonic, passphrase, words, index):
    phrase = " ".join((mnemonic or "").split())
    if not validate_mnemonic(phrase):
        raise CharsetError("not a valid BIP-39 English mnemonic")
    words = int(words)
    index = int(index)
    seed = mnemonic_to_seed(phrase, passphrase or "")
    root = Node.from_seed(seed)
    child = mnemonic_from_node(root, words, index)
    return {
        "path": _path(words, index),
        "index": index,
        "words": words,
        "language": "english",
        "warning": WARNING,
        "mnemonic": child,
    }

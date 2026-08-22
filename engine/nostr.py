import hmac

from engine.bech32 import BECH32, decode_data, encode_data
from engine.bip32 import Node
from engine.bip39 import mnemonic_to_seed, validate_mnemonic
from engine.charset import CharsetError
from engine.entropy import ByteSource
from engine.secp256k1 import is_valid_priv, priv_to_pub

NIP06_PATH = "m/44'/1237'/0'/0/0"


def _pack(priv32):
    pub33 = priv_to_pub(priv32)
    return {
        "path": NIP06_PATH,
        "method": "NIP-06 %s" % NIP06_PATH,
        "npub": encode_data("npub", pub33[1:], BECH32),
        "nsec": encode_data("nsec", priv32, BECH32),
        "pubkey": pub33[1:].hex(),
    }


def nostr_from_mnemonic(mnemonic, passphrase=""):
    phrase = " ".join((mnemonic or "").split())
    if not validate_mnemonic(phrase):
        raise CharsetError("not a valid BIP-39 English mnemonic")
    seed = mnemonic_to_seed(phrase, passphrase or "")
    node = Node.from_seed(seed).derive(NIP06_PATH)
    return _pack(node.priv)


def nostr_fresh(source):
    if not isinstance(source, ByteSource):
        raise CharsetError("fresh Nostr keys need an entropy source")
    for _ in range(8):
        priv = source.need(32)
        if is_valid_priv(priv):
            return _pack(priv)
    raise CharsetError("could not draw a valid Nostr secret")


def inspect_nsec(nsec, expected_npub=""):
    try:
        priv = decode_data("nsec", nsec)
    except ValueError as exc:
        raise CharsetError("not a valid nsec: %s" % exc)
    if len(priv) != 32:
        raise CharsetError("nsec must decode to 32 bytes")
    packed = _pack(priv)
    expected = (expected_npub or "").strip()
    match = None
    if expected:
        try:
            want = decode_data("npub", expected)
        except ValueError as exc:
            raise CharsetError("not a valid npub: %s" % exc)
        match = hmac.compare_digest(want, bytes.fromhex(packed["pubkey"]))
    return {
        "method": "inspect nsec → npub (no seed words)",
        "path": "",
        "npub": packed["npub"],
        "pubkey": packed["pubkey"],
        "match": match,
    }

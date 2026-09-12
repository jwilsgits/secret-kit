"""age X25519 identity + recipient (Bech32), generate only."""

from engine.bech32 import BECH32, decode_data, encode_data
from engine.charset import CharsetError
from engine.ed25519 import generate_x25519_keypair, x25519
from engine.entropy import ByteSource

BASE = bytes([9] + [0] * 31)


def recipient_from_public(public32):
    return encode_data("age", public32, BECH32)


def identity_from_scalar(scalar32):
    return encode_data("age-secret-key-", scalar32, BECH32).upper()


def public_from_identity(identity):
    scalar = decode_data("age-secret-key-", (identity or "").lower())
    if len(scalar) != 32:
        raise CharsetError("age identity must decode to 32 bytes")
    return x25519(scalar, BASE)


def generate_age_x25519(source):
    """Return {recipient, identity, type, public, private} for age X25519."""
    if not isinstance(source, ByteSource):
        raise CharsetError("age generate needs an entropy source")
    pair = generate_x25519_keypair(source)
    recipient = recipient_from_public(pair["public"])
    identity = identity_from_scalar(pair["scalar"])
    if public_from_identity(identity) != pair["public"]:
        raise CharsetError("age identity/recipient mismatch")
    return {
        "recipient": recipient,
        "identity": identity,
        "type": "age",
        "public": recipient,
        "private": identity,
    }

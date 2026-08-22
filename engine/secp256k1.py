"""secp256k1 via the ecdsa package (pure Python, air-gap friendly)."""

from ecdsa import SECP256k1, SigningKey, VerifyingKey
from ecdsa.ellipticcurve import INFINITY
from ecdsa.util import number_to_string, string_to_number

CURVE = SECP256k1
N = CURVE.order
G = CURVE.generator


class SecpError(ValueError):
    pass


def _priv_int(priv32):
    if len(priv32) != 32:
        raise SecpError("private key must be 32 bytes")
    k = string_to_number(priv32)
    if k <= 0 or k >= N:
        raise SecpError("private key out of range")
    return k


def priv_to_pub(priv32):
    sk = SigningKey.from_string(priv32, curve=CURVE)
    return sk.verifying_key.to_string("compressed")


def add_tweak_priv(priv32, tweak32):
    k = (_priv_int(priv32) + string_to_number(tweak32)) % N
    if k == 0:
        raise SecpError("derived key is zero")
    return number_to_string(k, N)


def tweak_add_pub(pub33, tweak32):
    t = string_to_number(tweak32)
    if t >= N:
        raise SecpError("tweak out of range")
    parent = VerifyingKey.from_string(pub33, curve=CURVE)
    added = parent.pubkey.point + (t * G)
    if added == INFINITY:
        raise SecpError("derived point at infinity")
    return VerifyingKey.from_public_point(added, curve=CURVE).to_string("compressed")


def is_valid_priv(priv32):
    try:
        _priv_int(priv32)
        return True
    except SecpError:
        return False

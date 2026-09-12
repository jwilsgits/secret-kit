"""RFC 8032 Ed25519 and RFC 7748 X25519. Pure Python; hashlib only."""

from __future__ import division

import hashlib

from engine.charset import CharsetError
from engine.entropy import ByteSource

# Ed25519 curve parameters (RFC 8032)
_P = 2**255 - 19
_L = 2**252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, _P - 2, _P) % _P
_I = pow(2, (_P - 1) // 4, _P)
_BY = 4 * pow(5, _P - 2, _P) % _P
_BX = 15112221349535400772501151409588531511454012693041857206046113283949847762202
_B = (_BX % _P, _BY % _P)


def _inv(x):
    return pow(x, _P - 2, _P)


def _xrecover(y):
    xx = (y * y - 1) * _inv(_D * y * y + 1)
    x = pow(xx, (_P + 3) // 8, _P)
    if (x * x - xx) % _P != 0:
        x = (x * _I) % _P
    if x % 2 != 0:
        x = _P - x
    return x


def _ed_add(p, q):
    x1, y1 = p
    x2, y2 = q
    x3 = (x1 * y2 + x2 * y1) * _inv(1 + _D * x1 * x2 * y1 * y2)
    y3 = (y1 * y2 + x1 * x2) * _inv(1 - _D * x1 * x2 * y1 * y2)
    return (x3 % _P, y3 % _P)


def _ed_scale(point, scalar):
    result = (0, 1)
    for i in range(256):
        if (scalar >> i) & 1:
            result = _ed_add(result, point)
        point = _ed_add(point, point)
    return result


def _encode_point(point):
    x, y = point
    out = bytearray(y.to_bytes(32, "little"))
    if x & 1:
        out[31] |= 0x80
    return bytes(out)


def _sha512(data):
    return hashlib.sha512(data).digest()


def ed25519_public_from_seed(seed32):
    """Return the 32-byte Ed25519 public key for a 32-byte secret seed."""
    if len(seed32) != 32:
        raise CharsetError("Ed25519 seed must be 32 bytes")
    h = bytearray(_sha512(seed32))
    h[0] &= 248
    h[31] &= 63
    h[31] |= 64
    a = int.from_bytes(h[:32], "little")
    return _encode_point(_ed_scale(_B, a))


def _clamp_scalar(raw32):
    k = bytearray(raw32)
    k[0] &= 248
    k[31] &= 127
    k[31] |= 64
    return bytes(k)


def x25519(scalar32, u_bytes):
    """RFC 7748 X25519(k, u). Returns 32-byte little-endian u-coordinate."""
    if len(scalar32) != 32 or len(u_bytes) != 32:
        raise CharsetError("X25519 needs 32-byte scalar and u")
    k = bytearray(_clamp_scalar(scalar32))
    # decode u with unused high bit cleared
    u_arr = bytearray(u_bytes)
    u_arr[31] &= 127
    x1 = int.from_bytes(u_arr, "little") % _P
    x2, z2 = 1, 0
    x3, z3 = x1, 1
    swap = 0
    for t in range(255, -1, -1):
        kt = (k[t >> 3] >> (t & 7)) & 1
        swap ^= kt
        if swap:
            x2, x3 = x3, x2
            z2, z3 = z3, z2
        swap = kt
        a = (x2 + z2) % _P
        aa = (a * a) % _P
        b = (x2 - z2) % _P
        bb = (b * b) % _P
        e = (aa - bb) % _P
        c = (x3 + z3) % _P
        d = (x3 - z3) % _P
        da = (d * a) % _P
        cb = (c * b) % _P
        x3 = pow((da + cb) % _P, 2, _P)
        z3 = (x1 * pow((da - cb) % _P, 2, _P)) % _P
        x2 = (aa * bb) % _P
        z2 = (e * (aa + 121665 * e)) % _P
    if swap:
        x2, x3 = x3, x2
        z2, z3 = z3, z2
    out = (x2 * _inv(z2)) % _P
    return out.to_bytes(32, "little")


def generate_ed25519_keypair(source):
    """Draw a usable Ed25519 seed from ByteSource. Returns seed + public."""
    if not isinstance(source, ByteSource):
        raise CharsetError("Ed25519 generate needs an entropy source")
    for _ in range(8):
        seed = source.need(32)
        if seed != b"\x00" * 32:
            public = ed25519_public_from_seed(seed)
            return {"seed": seed, "public": public}
    raise CharsetError("could not draw a usable Ed25519 seed")


def generate_x25519_keypair(source):
    """Draw a usable X25519 scalar from ByteSource. Returns scalar + public."""
    if not isinstance(source, ByteSource):
        raise CharsetError("X25519 generate needs an entropy source")
    base = bytes([9] + [0] * 31)
    for _ in range(8):
        scalar = source.need(32)
        if scalar == b"\x00" * 32:
            continue
        public = x25519(scalar, base)
        if public != b"\x00" * 32:
            return {"scalar": scalar, "public": public}
    raise CharsetError("could not draw a usable X25519 scalar")

"""RIPEMD-160. Apple's Python 3.9 hashlib often omits this algorithm."""

import struct

_KL = (
    [0x00000000] * 16
    + [0x5A827999] * 16
    + [0x6ED9EBA1] * 16
    + [0x8F1BBCDC] * 16
    + [0xA953FD4E] * 16
)
_KR = (
    [0x50A28BE6] * 16
    + [0x5C4DD124] * 16
    + [0x6D703EF3] * 16
    + [0x7A6D76E9] * 16
    + [0x00000000] * 16
)
_RL = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    7, 4, 13, 1, 10, 6, 15, 3, 12, 0, 9, 5, 2, 14, 11, 8,
    3, 10, 14, 4, 9, 15, 8, 1, 2, 7, 0, 6, 13, 11, 5, 12,
    1, 9, 11, 10, 0, 8, 12, 4, 13, 3, 7, 15, 14, 5, 6, 2,
    4, 0, 5, 9, 7, 12, 2, 10, 14, 1, 3, 8, 11, 6, 15, 13,
]
_RR = [
    5, 14, 7, 0, 9, 2, 11, 4, 13, 6, 15, 8, 1, 10, 3, 12,
    6, 11, 3, 7, 0, 13, 5, 10, 14, 15, 8, 12, 4, 9, 1, 2,
    15, 5, 1, 3, 7, 14, 6, 9, 11, 8, 12, 2, 10, 0, 4, 13,
    8, 6, 4, 1, 3, 11, 15, 0, 5, 12, 2, 13, 9, 7, 10, 14,
    12, 15, 10, 4, 1, 5, 8, 7, 6, 2, 13, 14, 0, 3, 9, 11,
]
_SL = [
    11, 14, 15, 12, 5, 8, 7, 9, 11, 13, 14, 15, 6, 7, 9, 8,
    7, 6, 8, 13, 11, 9, 7, 15, 7, 12, 15, 9, 11, 7, 13, 12,
    11, 13, 6, 7, 14, 9, 13, 15, 14, 8, 13, 6, 5, 12, 7, 5,
    11, 12, 14, 15, 14, 15, 9, 8, 9, 14, 5, 6, 8, 6, 5, 12,
    9, 15, 5, 11, 6, 8, 13, 12, 5, 12, 13, 14, 11, 8, 5, 6,
]
_SR = [
    8, 9, 9, 11, 13, 15, 15, 5, 7, 7, 8, 11, 14, 14, 12, 6,
    9, 13, 15, 7, 12, 8, 9, 11, 7, 7, 12, 7, 6, 15, 13, 11,
    9, 7, 15, 11, 8, 6, 6, 14, 12, 13, 5, 14, 13, 13, 7, 5,
    15, 5, 8, 11, 14, 14, 6, 14, 6, 9, 12, 9, 12, 5, 15, 8,
    8, 5, 12, 9, 12, 5, 14, 6, 8, 13, 6, 5, 15, 13, 11, 11,
]


def _rol(x, n):
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF


def _f(j, x, y, z):
    if j < 16:
        return x ^ y ^ z
    if j < 32:
        return (x & y) | (~x & z)
    if j < 48:
        return (x | ~y) ^ z
    if j < 64:
        return (x & z) | (y & ~z)
    return x ^ (y | ~z)


def ripemd160(data):
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("ripemd160 expects bytes")
    ml = len(data) * 8
    data = bytes(data) + b"\x80"
    data += b"\x00" * ((56 - (len(data) % 64)) % 64)
    data += struct.pack("<Q", ml)

    h0, h1, h2, h3, h4 = (
        0x67452301,
        0xEFCDAB89,
        0x98BADCFE,
        0x10325476,
        0xC3D2E1F0,
    )
    for offset in range(0, len(data), 64):
        x = list(struct.unpack("<16I", data[offset : offset + 64]))
        al = ar = h0
        bl = br = h1
        cl = cr = h2
        dl = dr = h3
        el = er = h4
        for j in range(80):
            tl = (_rol((al + _f(j, bl, cl, dl) + x[_RL[j]] + _KL[j]) & 0xFFFFFFFF, _SL[j]) + el) & 0xFFFFFFFF
            al, bl, cl, dl, el = el, tl, bl, _rol(cl, 10), dl
            tr = (_rol((ar + _f(79 - j, br, cr, dr) + x[_RR[j]] + _KR[j]) & 0xFFFFFFFF, _SR[j]) + er) & 0xFFFFFFFF
            ar, br, cr, dr, er = er, tr, br, _rol(cr, 10), dr
        h0, h1, h2, h3, h4 = (
            (h1 + cl + dr) & 0xFFFFFFFF,
            (h2 + dl + er) & 0xFFFFFFFF,
            (h3 + el + ar) & 0xFFFFFFFF,
            (h4 + al + br) & 0xFFFFFFFF,
            (h0 + bl + cr) & 0xFFFFFFFF,
        )
    return struct.pack("<5I", h0, h1, h2, h3, h4)

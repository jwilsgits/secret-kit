"""Bech32 (BIP-173) and Bech32m (BIP-350)."""

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
GEN = (0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3)
BECH32 = 1
BECH32M = 0x2BC830A3


def _polymod(values):
    chk = 1
    for value in values:
        top = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ value
        for i in range(5):
            if (top >> i) & 1:
                chk ^= GEN[i]
    return chk


def _hrp_expand(hrp):
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]


def _create_checksum(hrp, data, spec):
    values = _hrp_expand(hrp) + data
    polymod = _polymod(values + [0, 0, 0, 0, 0, 0]) ^ spec
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def encode(hrp, witver, witprog, spec=BECH32):
    data = [witver] + convertbits(witprog, 8, 5)
    combined = data + _create_checksum(hrp, data, spec)
    return hhrp(hrp) + "1" + "".join(CHARSET[d] for d in combined)


def encode_data(hrp, payload, spec=BECH32):
    """Encode raw bytes (Nostr nsec/npub) with no witness version."""
    data = convertbits(payload, 8, 5)
    combined = data + _create_checksum(hrp, data, spec)
    return hhrp(hrp) + "1" + "".join(CHARSET[d] for d in combined)


def hhrp(hrp):
    return hrp.lower()


def convertbits(data, from_bits, to_bits, pad=True):
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << to_bits) - 1
    max_acc = (1 << (from_bits + to_bits - 1)) - 1
    for value in data:
        if value < 0 or (value >> from_bits):
            raise ValueError("invalid convertbits value")
        acc = ((acc << from_bits) | value) & max_acc
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (to_bits - bits)) & maxv)
    elif bits >= from_bits or ((acc << (to_bits - bits)) & maxv):
        raise ValueError("invalid padding")
    return ret


def decode_data(hrp, encoded):
    """Decode a raw bech32 string (nsec/npub) into payload bytes."""
    encoded = (encoded or "").strip().lower()
    pos = encoded.rfind("1")
    if pos < 1:
        raise ValueError("invalid bech32")
    if encoded[:pos] != hrp.lower():
        raise ValueError("wrong hrp")
    data = [CHARSET.find(c) for c in encoded[pos + 1 :]]
    if any(d == -1 for d in data) or len(data) < 6:
        raise ValueError("invalid bech32 char")
    if _polymod(_hrp_expand(hrp.lower()) + data) != BECH32:
        raise ValueError("bad bech32 checksum")
    return bytes(convertbits(data[:-6], 5, 8, False))


def decode_segwit(hrp, addr):
    addr = addr.lower()
    if addr.rfind("1") < 1:
        raise ValueError("invalid bech32")
    pos = addr.rfind("1")
    if addr[:pos] != hrp:
        raise ValueError("wrong hrp")
    data = [CHARSET.find(c) for c in addr[pos + 1 :]]
    if any(d == -1 for d in data):
        raise ValueError("invalid bech32 char")
    spec = _polymod(_hrp_expand(hrp) + data)
    if spec not in (BECH32, BECH32M):
        raise ValueError("bad bech32 checksum")
    decoded = convertbits(data[:-6][1:], 5, 8, False)
    return data[0], bytes(decoded)

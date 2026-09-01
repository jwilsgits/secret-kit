import hashlib
import hmac
import struct

from engine.ripemd160 import ripemd160
from engine.secp256k1 import N, SecpError, add_tweak_priv, is_valid_priv, priv_to_pub, tweak_add_pub

HARDENED = 0x80000000
XPRV = bytes.fromhex("0488ADE4")
XPUB = bytes.fromhex("0488B21E")
ZPRV = bytes.fromhex("04B2430C")
ZPUB = bytes.fromhex("04B24746")
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def hash160(data):
    return ripemd160(hashlib.sha256(data).digest())


def _b58encode(raw):
    n = int.from_bytes(raw, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = B58[r] + out
    pad = 0
    for byte in raw:
        if byte == 0:
            pad += 1
        else:
            break
    return ("1" * pad) + (out or "1")


def _b58decode(text):
    n = 0
    for ch in text:
        idx = B58.find(ch)
        if idx < 0:
            raise SecpError("invalid base58")
        n = n * 58 + idx
    pad = 0
    for ch in text:
        if ch == "1":
            pad += 1
        else:
            break
    if n == 0:
        raw = b""
    else:
        raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return (b"\x00" * pad) + raw


def base58check(payload):
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return _b58encode(payload + checksum)


class Node(object):
    def __init__(self, priv, pub, chain, depth, fingerprint, index):
        self.priv = priv
        self.pub = pub
        self.chain = chain
        self.depth = depth
        self.fingerprint = fingerprint
        self.index = index

    @classmethod
    def from_extended(cls, text):
        raw = _b58decode((text or "").strip())
        if len(raw) < 82:
            raise SecpError("invalid extended key")
        payload, check = raw[:-4], raw[-4:]
        if hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4] != check:
            raise SecpError("invalid extended key checksum")
        ver = payload[0:4]
        depth = payload[4]
        fingerprint = payload[5:9]
        index = struct.unpack(">I", payload[9:13])[0]
        chain = payload[13:45]
        key = payload[45:78]
        if ver == XPRV:
            if key[0] != 0:
                raise SecpError("invalid xprv")
            priv = key[1:]
            if not is_valid_priv(priv):
                raise SecpError("invalid master key")
            pub = priv_to_pub(priv)
        elif ver == XPUB:
            priv = None
            pub = key
        else:
            raise SecpError("unsupported extended key version")
        return cls(priv, pub, chain, depth, fingerprint, index)

    @classmethod
    def from_seed(cls, seed):
        i = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
        il, ir = i[:32], i[32:]
        if not is_valid_priv(il):
            raise SecpError("invalid master key")
        return cls(il, priv_to_pub(il), ir, 0, b"\x00\x00\x00\x00", 0)

    def _child(self, index):
        hardened = index >= HARDENED
        if hardened:
            if self.priv is None:
                raise SecpError("cannot derive hardened child from public key")
            data = b"\x00" + self.priv + struct.pack(">I", index)
        else:
            data = self.pub + struct.pack(">I", index)
        i = hmac.new(self.chain, data, hashlib.sha512).digest()
        il, ir = i[:32], i[32:]
        if int.from_bytes(il, "big") >= N:
            raise SecpError("invalid child tweak")
        fp = hash160(self.pub)[:4]
        if self.priv is not None:
            priv = add_tweak_priv(self.priv, il)
            pub = priv_to_pub(priv)
        else:
            priv = None
            pub = tweak_add_pub(self.pub, il)
        return Node(priv, pub, ir, self.depth + 1, fp, index)

    def derive(self, path):
        node = self
        text = path.strip()
        if text.startswith("m/"):
            text = text[2:]
        elif text == "m":
            return node
        if not text:
            return node
        for part in text.split("/"):
            hardened = part.endswith("'") or part.endswith("h")
            num = int(part[:-1] if hardened else part)
            if hardened:
                num |= HARDENED
            node = node._child(num)
        return node

    def extended(self, private, version=None):
        if private:
            if self.priv is None:
                raise SecpError("no private key")
            ver = version or XPRV
            key = b"\x00" + self.priv
        else:
            ver = version or XPUB
            key = self.pub
        payload = (
            ver
            + bytes([self.depth])
            + self.fingerprint
            + struct.pack(">I", self.index)
            + self.chain
            + key
        )
        return base58check(payload)

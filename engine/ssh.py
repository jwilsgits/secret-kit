"""OpenSSH Ed25519 keypair generation (unencrypted private key)."""

import base64
import os
import struct

from engine.charset import CharsetError
from engine.ed25519 import ed25519_public_from_seed, generate_ed25519_keypair
from engine.entropy import ByteSource

COMMENT = "secret-kit"
KEY_TYPE = b"ssh-ed25519"


def _ssh_string(data):
    data = bytes(data)
    return struct.pack(">I", len(data)) + data


def _ssh_u32(n):
    return struct.pack(">I", n)


def public_wire(public32):
    return _ssh_string(KEY_TYPE) + _ssh_string(public32)


def public_line(public32, comment=COMMENT):
    blob = base64.b64encode(public_wire(public32)).decode("ascii")
    return "ssh-ed25519 %s %s" % (blob, comment)


def _pad_block(payload, block=8):
    pad_len = block - (len(payload) % block)
    if pad_len == 0:
        pad_len = block
    return payload + bytes(range(1, pad_len + 1))


def private_pem(seed32, public32, comment=COMMENT):
    """Build an unencrypted openssh-key-v1 PEM for Ed25519."""
    if len(seed32) != 32 or len(public32) != 32:
        raise CharsetError("Ed25519 seed/public must be 32 bytes")
    pub_blob = public_wire(public32)
    check = os.urandom(4)
    private64 = seed32 + public32
    private_inner = b"".join(
        [
            check,
            check,
            _ssh_string(KEY_TYPE),
            _ssh_string(public32),
            _ssh_string(private64),
            _ssh_string(comment.encode("utf-8")),
        ]
    )
    private_inner = _pad_block(private_inner, 8)
    body = b"".join(
        [
            b"openssh-key-v1\x00",
            _ssh_string(b"none"),
            _ssh_string(b"none"),
            _ssh_string(b""),
            _ssh_u32(1),
            _ssh_string(pub_blob),
            _ssh_string(private_inner),
        ]
    )
    b64 = base64.b64encode(body).decode("ascii")
    lines = ["-----BEGIN OPENSSH PRIVATE KEY-----"]
    for i in range(0, len(b64), 70):
        lines.append(b64[i : i + 70])
    lines.append("-----END OPENSSH PRIVATE KEY-----")
    return "\n".join(lines) + "\n"


def parse_public_from_private_pem(pem):
    """Recover the 32-byte public key from our unencrypted private PEM."""
    text = (pem or "").strip()
    lines = [
        ln.strip()
        for ln in text.splitlines()
        if ln.strip() and not ln.startswith("-----")
    ]
    raw = base64.b64decode("".join(lines))
    if not raw.startswith(b"openssh-key-v1\x00"):
        raise CharsetError("not openssh-key-v1")
    i = len(b"openssh-key-v1\x00")

    def read_string(buf, idx):
        if idx + 4 > len(buf):
            raise CharsetError("truncated private key")
        (n,) = struct.unpack_from(">I", buf, idx)
        idx += 4
        if idx + n > len(buf):
            raise CharsetError("truncated private key")
        return buf[idx : idx + n], idx + n

    cipher, i = read_string(raw, i)
    kdf, i = read_string(raw, i)
    _kdfopts, i = read_string(raw, i)
    if cipher != b"none" or kdf != b"none":
        raise CharsetError("encrypted OpenSSH keys are not supported")
    if i + 4 > len(raw):
        raise CharsetError("truncated private key")
    (nkeys,) = struct.unpack_from(">I", raw, i)
    i += 4
    if nkeys != 1:
        raise CharsetError("expected one key")
    pub_blob, i = read_string(raw, i)
    _typ, j = read_string(pub_blob, 0)
    public32, j = read_string(pub_blob, j)
    if len(public32) != 32:
        raise CharsetError("bad public key length")
    return public32


def generate_ssh_ed25519(source):
    """Return {public, private, type, comment} for an OpenSSH Ed25519 key."""
    if not isinstance(source, ByteSource):
        raise CharsetError("SSH generate needs an entropy source")
    pair = generate_ed25519_keypair(source)
    seed = pair["seed"]
    public = pair["public"]
    if ed25519_public_from_seed(seed) != public:
        raise CharsetError("Ed25519 public mismatch")
    return {
        "public": public_line(public, COMMENT),
        "private": private_pem(seed, public, COMMENT),
        "type": "ssh",
        "comment": COMMENT,
    }

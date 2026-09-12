"""Detached OpenPGP v4 verify. No GnuPG, no cryptography, no network."""

import base64
import binascii
import hashlib
import hmac
import struct
import time

from engine.hashcheck import CHUNK

HASH_ERROR = "This signature uses a hash Secret Kit will not accept."
ISSUER_ERROR = "This signature was not made by the key file you supplied."
REVOKED_ERROR = "This key file marks the key as revoked."
ARMOR_ERROR = "unreadable armor"

HASH_IDS = {8: "sha256", 10: "sha512"}
RSA_ALGOS = frozenset((1, 3))
ED25519_ALGOS = frozenset((22, 27))
SIGN_ALGOS = RSA_ALGOS | ED25519_ALGOS

DIGESTINFO = {
    "sha256": bytes.fromhex("3031300d060960864801650304020105000420"),
    "sha512": bytes.fromhex("3051300d060960864801650304020305000440"),
}

try:
    from engine.ed25519 import verify as _ed25519_verify_ext
except ImportError:
    _ed25519_verify_ext = None


def _fail(error, **extra):
    row = {
        "ok": False,
        "good": False,
        "error": error,
        "fingerprint": "",
        "user_id": "",
        "subkey_id": "",
        "hash_algo": "",
        "expired": False,
        "revoked": False,
    }
    row.update(extra)
    return row


def _ok(good, **extra):
    row = {
        "ok": True,
        "good": bool(good),
        "error": None,
        "fingerprint": "",
        "user_id": "",
        "subkey_id": "",
        "hash_algo": "",
        "expired": False,
        "revoked": False,
    }
    row.update(extra)
    return row


def _crc24(data):
    crc = 0xB704CE
    for byte in data:
        crc ^= byte << 16
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= 0x1864CFB
    return crc & 0xFFFFFF


def _unarmor(data):
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    stripped = data.lstrip()
    if not stripped.startswith(b"-----BEGIN PGP"):
        return data
    try:
        text = stripped.decode("ascii")
    except UnicodeDecodeError:
        raise ValueError(ARMOR_ERROR)
    lines = text.replace("\r\n", "\n").split("\n")
    start = None
    for i, line in enumerate(lines):
        if line.startswith("-----BEGIN PGP"):
            start = i
            break
    if start is None:
        raise ValueError(ARMOR_ERROR)
    i = start + 1
    while i < len(lines) and lines[i].strip() != "":
        i += 1
    if i >= len(lines):
        raise ValueError(ARMOR_ERROR)
    i += 1
    chunks = []
    crc_b64 = None
    ended = False
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if line.startswith("-----END PGP"):
            ended = True
            break
        if line.startswith("=") and len(line) == 5:
            crc_b64 = line[1:]
            continue
        if line:
            chunks.append(line)
    if not ended:
        raise ValueError(ARMOR_ERROR)
    try:
        raw = base64.b64decode("".join(chunks), validate=True)
    except (ValueError, binascii.Error):
        raise ValueError(ARMOR_ERROR)
    if crc_b64 is not None:
        try:
            expect = int.from_bytes(base64.b64decode(crc_b64), "big")
        except (ValueError, binascii.Error):
            raise ValueError(ARMOR_ERROR)
        if _crc24(raw) != expect:
            raise ValueError(ARMOR_ERROR)
    return raw


def _new_body(data, i):
    chunks = []
    partial = True
    n = len(data)
    while partial:
        if i >= n:
            raise ValueError("truncated packet")
        first = data[i]
        i += 1
        if first < 192:
            ln = first
            partial = False
        elif first < 224:
            if i >= n:
                raise ValueError("truncated packet")
            ln = ((first - 192) << 8) + data[i] + 192
            i += 1
            partial = False
        elif first == 255:
            if i + 4 > n:
                raise ValueError("truncated packet")
            ln = struct.unpack(">I", data[i : i + 4])[0]
            i += 4
            partial = False
        else:
            ln = 1 << (first & 0x1F)
            partial = True
        if i + ln > n:
            raise ValueError("truncated packet")
        chunks.append(data[i : i + ln])
        i += ln
    return b"".join(chunks), i


def parse_packets(data):
    packets = []
    i = 0
    n = len(data)
    while i < n:
        first = data[i]
        if first & 0x80 == 0:
            raise ValueError("invalid OpenPGP packet")
        if first & 0x40:
            tag = first & 0x3F
            i += 1
            body, i = _new_body(data, i)
        else:
            tag = (first >> 2) & 0x0F
            len_type = first & 0x03
            i += 1
            if len_type == 0:
                if i >= n:
                    raise ValueError("truncated packet")
                ln = data[i]
                i += 1
            elif len_type == 1:
                if i + 2 > n:
                    raise ValueError("truncated packet")
                ln = struct.unpack(">H", data[i : i + 2])[0]
                i += 2
            elif len_type == 2:
                if i + 4 > n:
                    raise ValueError("truncated packet")
                ln = struct.unpack(">I", data[i : i + 4])[0]
                i += 4
            else:
                ln = n - i
            if i + ln > n:
                raise ValueError("truncated packet")
            body = data[i : i + ln]
            i += ln
        packets.append((tag, body))
    return packets


def _read_mpi(data, i):
    if i + 2 > len(data):
        raise ValueError("truncated MPI")
    bits = struct.unpack(">H", data[i : i + 2])[0]
    i += 2
    nbytes = (bits + 7) // 8
    if i + nbytes > len(data):
        raise ValueError("truncated MPI")
    raw = data[i : i + nbytes]
    i += nbytes
    value = int.from_bytes(raw, "big") if raw else 0
    return value, raw, i


def _fingerprint_v4(body):
    return hashlib.sha1(b"\x99" + struct.pack(">H", len(body)) + body).digest()


def _ed_point(mpi_raw):
    if mpi_raw.startswith(b"\x40") and len(mpi_raw) >= 33:
        return mpi_raw[1:33]
    if len(mpi_raw) >= 32:
        return mpi_raw[-32:]
    raise ValueError("bad Ed25519 public key")


def parse_key_material(body):
    if not body or body[0] != 4:
        raise ValueError("only OpenPGP v4 keys are supported")
    if len(body) < 6:
        raise ValueError("truncated public key")
    created = struct.unpack(">I", body[1:5])[0]
    algo = body[5]
    i = 6
    key = {
        "version": 4,
        "created": created,
        "algo": algo,
        "body": body,
        "unsupported": algo not in SIGN_ALGOS,
        "n": None,
        "e": None,
        "ed25519": None,
    }
    if algo in (1, 2, 3):
        n, _raw, i = _read_mpi(body, i)
        e, _raw, i = _read_mpi(body, i)
        key["n"] = n
        key["e"] = e
        if algo == 2:
            key["unsupported"] = True
    elif algo == 22:
        if i >= len(body):
            raise ValueError("truncated Ed25519 key")
        oid_len = body[i]
        i += 1
        i += oid_len
        _value, raw, i = _read_mpi(body, i)
        key["ed25519"] = _ed_point(raw)
    elif algo == 27:
        if i + 32 > len(body):
            raise ValueError("truncated Ed25519 key")
        key["ed25519"] = body[i : i + 32]
    fp = _fingerprint_v4(body)
    key["fingerprint"] = fp.hex().upper()
    key["key_id"] = fp[-8:].hex().upper()
    return key


def _parse_subpackets(blob):
    i = 0
    out = []
    n = len(blob)
    while i < n:
        first = blob[i]
        i += 1
        if first < 192:
            ln = first
        elif first < 255:
            if i >= n:
                raise ValueError("truncated subpacket")
            ln = ((first - 192) << 8) + blob[i] + 192
            i += 1
        else:
            if i + 4 > n:
                raise ValueError("truncated subpacket")
            ln = struct.unpack(">I", blob[i : i + 4])[0]
            i += 4
        if i + ln > n:
            raise ValueError("truncated subpacket")
        data = blob[i : i + ln]
        i += ln
        if not data:
            continue
        out.append((data[0], data[1:]))
    return out


def parse_signature(body):
    if not body or body[0] != 4:
        raise ValueError("only OpenPGP v4 signatures are supported")
    if len(body) < 6:
        raise ValueError("truncated signature")
    sig_type = body[1]
    pub_algo = body[2]
    hash_algo = body[3]
    hashed_len = struct.unpack(">H", body[4:6])[0]
    i = 6
    if i + hashed_len > len(body):
        raise ValueError("truncated signature")
    hashed = body[i : i + hashed_len]
    prefix = body[: i + hashed_len]
    i += hashed_len
    if i + 2 > len(body):
        raise ValueError("truncated signature")
    unhashed_len = struct.unpack(">H", body[i : i + 2])[0]
    i += 2
    if i + unhashed_len + 2 > len(body):
        raise ValueError("truncated signature")
    unhashed = body[i : i + unhashed_len]
    i += unhashed_len
    left16 = body[i : i + 2]
    i += 2
    hashed_subs = _parse_subpackets(hashed)
    unhashed_subs = _parse_subpackets(unhashed)
    issuer_id = ""
    issuer_fpr = ""
    created = None
    sig_expire = None
    for typ, data in hashed_subs + unhashed_subs:
        if typ == 2 and len(data) == 4 and created is None:
            created = struct.unpack(">I", data)[0]
        elif typ == 3 and len(data) == 4:
            sig_expire = struct.unpack(">I", data)[0]
        elif typ == 16 and len(data) >= 8 and not issuer_id:
            issuer_id = data[:8].hex().upper()
        elif typ == 33 and len(data) >= 21 and data[0] == 4 and not issuer_fpr:
            issuer_fpr = data[1:21].hex().upper()
            if not issuer_id:
                issuer_id = data[13:21].hex().upper()
    mpis = []
    mpi_raws = []
    while i < len(body):
        value, raw, i = _read_mpi(body, i)
        mpis.append(value)
        mpi_raws.append(raw)
    return {
        "type": sig_type,
        "pub_algo": pub_algo,
        "hash_algo": hash_algo,
        "prefix": prefix,
        "left16": left16,
        "issuer_id": issuer_id,
        "issuer_fpr": issuer_fpr,
        "created": created,
        "sig_expire": sig_expire,
        "hashed_subs": hashed_subs,
        "mpis": mpis,
        "mpi_raws": mpi_raws,
    }


def _apply_key_sig(key, sig):
    for typ, data in sig["hashed_subs"]:
        if typ == 9 and len(data) == 4:
            key["expires"] = key["created"] + struct.unpack(">I", data)[0]
        elif typ == 27 and data:
            key["flags"] = data[0]


def parse_certificate(data):
    packets = parse_packets(data)
    keys = []
    primary = None
    current_sub = None
    for tag, body in packets:
        if tag == 6:
            primary = parse_key_material(body)
            primary.update(
                is_subkey=False,
                user_id="",
                flags=None,
                expires=None,
                revoked=False,
                primary=None,
            )
            current_sub = None
            keys.append(primary)
        elif tag == 14:
            if primary is None:
                continue
            current_sub = parse_key_material(body)
            current_sub.update(
                is_subkey=True,
                user_id="",
                flags=None,
                expires=None,
                revoked=False,
                primary=primary,
            )
            keys.append(current_sub)
        elif tag == 13:
            current_sub = None
            if primary is not None and not primary["user_id"]:
                primary["user_id"] = body.decode("utf-8", "replace")
        elif tag == 2:
            try:
                sig = parse_signature(body)
            except ValueError:
                continue
            if sig["type"] == 0x20 and primary is not None:
                primary["revoked"] = True
            elif sig["type"] == 0x28 and current_sub is not None:
                current_sub["revoked"] = True
            elif sig["type"] in (0x10, 0x11, 0x12, 0x13, 0x1F) and primary is not None and current_sub is None:
                _apply_key_sig(primary, sig)
            elif sig["type"] == 0x18 and current_sub is not None:
                _apply_key_sig(current_sub, sig)
    return keys


def _stream_hash(payload, hash_name, trailer):
    digest = hashlib.new(hash_name)
    if hasattr(payload, "read") and not isinstance(payload, (bytes, bytearray)):
        handle = payload
        close = False
    else:
        handle = open(payload, "rb")
        close = True
    try:
        while True:
            chunk = handle.read(CHUNK)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        if close:
            handle.close()
    digest.update(trailer)
    return digest.digest()


def _rsa_verify(n, e, sig_int, digest, hash_name):
    if e < 3 or n.bit_length() < 2048:
        raise ValueError("RSA key is smaller than 2048 bits or has a weak exponent")
    k = (n.bit_length() + 7) // 8
    if sig_int <= 0 or sig_int >= n:
        return False
    em = pow(sig_int, e, n).to_bytes(k, "big")
    info = DIGESTINFO[hash_name]
    tval = info + digest
    ps_len = k - 3 - len(tval)
    if ps_len < 8:
        return False
    expected = b"\x00\x01" + (b"\xff" * ps_len) + b"\x00" + tval
    return hmac.compare_digest(em, expected)


_P = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_D = (-121665 * pow(121666, _P - 2, _P)) % _P
_I = pow(2, (_P - 1) // 4, _P)


def _ed_recover_x(y, sign):
    y2 = (y * y) % _P
    x2 = ((y2 - 1) * pow((_D * y2 + 1) % _P, _P - 2, _P)) % _P
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P != 0:
        x = (x * _I) % _P
    if (x * x - x2) % _P != 0:
        return None
    if x & 1 != sign:
        x = _P - x
    return x


def _ed_point_add(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    den_x = (1 + _D * x1 * x2 * y1 * y2) % _P
    den_y = (1 - _D * x1 * x2 * y1 * y2) % _P
    x3 = ((x1 * y2 + x2 * y1) * pow(den_x, _P - 2, _P)) % _P
    y3 = ((y1 * y2 + x1 * x2) * pow(den_y, _P - 2, _P)) % _P
    return x3, y3


def _ed_scalarmult(point, n):
    acc = (0, 1)
    q = point
    while n:
        if n & 1:
            acc = _ed_point_add(acc, q)
        q = _ed_point_add(q, q)
        n >>= 1
    return acc


def _ed_decode(s):
    if len(s) != 32:
        return None
    y = int.from_bytes(s, "little")
    sign = (y >> 255) & 1
    y &= (1 << 255) - 1
    x = _ed_recover_x(y, sign)
    if x is None:
        return None
    return x, y


def _ed_encode(pt):
    x, y = pt
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


_By = (4 * pow(5, _P - 2, _P)) % _P
_Bx = _ed_recover_x(_By, 0)
_B = (_Bx, _By)


def _ed25519_verify_twin(public, signature, message):
    if len(public) != 32 or len(signature) != 64:
        return False
    A = _ed_decode(public)
    R = _ed_decode(signature[:32])
    if A is None or R is None:
        return False
    s = int.from_bytes(signature[32:], "little")
    if s >= _L:
        return False
    h = hashlib.sha512(signature[:32] + public + message).digest()
    k = int.from_bytes(h, "little") % _L
    sB = _ed_scalarmult(_B, s)
    kA = _ed_scalarmult(A, k)
    return _ed_encode(sB) == _ed_encode(_ed_point_add(R, kA))


def _ed25519_verify(public, signature, message):
    if _ed25519_verify_ext is not None:
        return _ed25519_verify_ext(public, signature, message)
    return _ed25519_verify_twin(public, signature, message)


def _pad32(raw):
    if len(raw) > 32:
        raw = raw[-32:]
    return raw.rjust(32, b"\x00")


def _sig_ed25519_bytes(sig):
    raws = sig["mpi_raws"]
    if len(raws) >= 2:
        return _pad32(raws[0]) + _pad32(raws[1])
    return None


def _find_issuer(keys, sig):
    issuer_fpr = sig["issuer_fpr"]
    issuer_id = sig["issuer_id"]
    matched = []
    for key in keys:
        if issuer_fpr and key["fingerprint"] == issuer_fpr:
            matched.append(key)
        elif issuer_id and key["key_id"] == issuer_id:
            matched.append(key)
    return matched


def _expired(key, sig, now):
    if key.get("expires") and now > key["expires"]:
        return True
    primary = key.get("primary")
    if primary and primary.get("expires") and now > primary["expires"]:
        return True
    if sig["created"] is not None and sig["sig_expire"]:
        if now > sig["created"] + sig["sig_expire"]:
            return True
    return False


def verify_detached(payload, signature, public_key):
    try:
        sig_raw = _unarmor(signature)
        key_raw = _unarmor(public_key)
        sig_packets = [body for tag, body in parse_packets(sig_raw) if tag == 2]
        if not sig_packets:
            return _fail("no signature packet")
        sig = None
        for body in sig_packets:
            parsed = parse_signature(body)
            if parsed["type"] == 0x00:
                sig = parsed
                break
        if sig is None:
            sig = parse_signature(sig_packets[0])
        hash_name = HASH_IDS.get(sig["hash_algo"])
        if not hash_name:
            return _fail(HASH_ERROR)
        if sig["pub_algo"] not in SIGN_ALGOS:
            return _fail("This signature uses a public-key algorithm Secret Kit will not accept.")
        keys = parse_certificate(key_raw)
        matched = _find_issuer(keys, sig)
        if not matched:
            return _fail(ISSUER_ERROR)
        signing = matched[0]
        if signing.get("unsupported") or signing["algo"] not in SIGN_ALGOS:
            return _fail("This signature uses a public-key algorithm Secret Kit will not accept.")
        if signing.get("flags") is not None and not (signing["flags"] & 0x02) and signing["is_subkey"]:
            return _fail(ISSUER_ERROR)
        primary = signing["primary"] if signing["is_subkey"] else signing
        fingerprint = primary["fingerprint"]
        user_id = primary.get("user_id") or ""
        subkey_id = signing["key_id"] if signing["is_subkey"] else ""
        revoked = bool(signing.get("revoked") or primary.get("revoked"))
        if revoked:
            return _fail(
                REVOKED_ERROR,
                fingerprint=fingerprint,
                user_id=user_id,
                subkey_id=subkey_id,
                hash_algo=hash_name,
                revoked=True,
            )
        now = int(time.time())
        expired = _expired(signing, sig, now)
        trailer = sig["prefix"] + bytes([0x04, 0xFF]) + struct.pack(">I", len(sig["prefix"]))
        digest = _stream_hash(payload, hash_name, trailer)
        good = False
        if signing["algo"] in RSA_ALGOS and sig["pub_algo"] in RSA_ALGOS:
            if not sig["mpis"]:
                good = False
            else:
                good = _rsa_verify(signing["n"], signing["e"], sig["mpis"][0], digest, hash_name)
        elif signing["algo"] in ED25519_ALGOS and sig["pub_algo"] in ED25519_ALGOS:
            blob = _sig_ed25519_bytes(sig)
            if blob is None or signing["ed25519"] is None:
                good = False
            else:
                good = _ed25519_verify(signing["ed25519"], blob, digest)
        else:
            return _fail("This signature uses a public-key algorithm Secret Kit will not accept.")
        return _ok(
            good,
            fingerprint=fingerprint,
            user_id=user_id,
            subkey_id=subkey_id,
            hash_algo=hash_name,
            expired=expired,
            revoked=False,
        )
    except (ValueError, OSError, struct.error, TypeError, IndexError) as exc:
        msg = str(exc) or "could not parse OpenPGP data"
        return _fail(msg)

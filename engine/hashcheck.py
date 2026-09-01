import hashlib
import hmac
import os
import re
import stat

from engine.charset import CharsetError

ALGOS = {
    "md5": {"length": 32, "legacy": True},
    "sha1": {"length": 40, "legacy": True},
    "sha256": {"length": 64, "legacy": False},
    "sha512": {"length": 128, "legacy": False},
}
_LEN_TO_ALGO = {info["length"]: name for name, info in ALGOS.items()}
CHUNK = 1024 * 1024
MAX_TREE_FILES = 5000
MAX_TREE_BYTES = 512 * 1024 * 1024


def normalize_hex(text):
    if text is None:
        raise CharsetError("paste a hex checksum")
    compact = re.sub(r"[\s:]", "", str(text)).strip()
    if compact.lower().startswith("0x"):
        compact = compact[2:]
    compact = compact.lower()
    if not compact:
        raise CharsetError("paste a hex checksum")
    if not re.fullmatch(r"[0-9a-f]+", compact):
        raise CharsetError("checksum must be hexadecimal")
    return compact


def detect_algo(hex_digest):
    return _LEN_TO_ALGO.get(len(hex_digest))


def hash_blob(data, algo):
    if algo not in ALGOS:
        raise CharsetError("unknown hash algorithm: %s" % algo)
    digest = hashlib.new(algo)
    digest.update(data)
    return digest.hexdigest()


def hash_file(path, algo):
    if algo not in ALGOS:
        raise CharsetError("unknown hash algorithm: %s" % algo)
    digest = hashlib.new(algo)
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(CHUNK)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path, expected_hex, algo=None):
    expected = normalize_hex(expected_hex)
    detected = detect_algo(expected)
    auto = algo in (None, "", "auto")
    if auto:
        if not detected:
            raise CharsetError(
                "could not detect algorithm from hash length (%d hex chars)"
                % len(expected)
            )
        algo = detected
    elif algo not in ALGOS:
        raise CharsetError("unknown hash algorithm: %s" % algo)
    digest = hash_file(path, algo)
    return _verify_result(digest, expected, algo, detected, auto)


def verify_blob(data, expected_hex, algo=None):
    expected = normalize_hex(expected_hex)
    detected = detect_algo(expected)
    auto = algo in (None, "", "auto")
    if auto:
        if not detected:
            raise CharsetError(
                "could not detect algorithm from hash length (%d hex chars)"
                % len(expected)
            )
        algo = detected
    elif algo not in ALGOS:
        raise CharsetError("unknown hash algorithm: %s" % algo)
    digest = hash_blob(data, algo)
    return _verify_result(digest, expected, algo, detected, auto)


def _verify_result(digest, expected, algo, detected, auto):
    return {
        "ok": True,
        "match": hmac.compare_digest(digest, expected),
        "algo": algo,
        "detected": detected,
        "auto": auto,
        "legacy": ALGOS[algo]["legacy"],
        "digest": digest,
        "expected": expected,
    }


def _compare_result(digest_a, digest_b, algo):
    return {
        "ok": True,
        "match": hmac.compare_digest(digest_a, digest_b),
        "algo": algo,
        "legacy": ALGOS[algo]["legacy"],
        "digest_a": digest_a,
        "digest_b": digest_b,
    }


def compare_files(path_a, path_b, algo="sha256"):
    if algo not in ALGOS:
        raise CharsetError("unknown hash algorithm: %s" % algo)
    return _compare_result(hash_file(path_a, algo), hash_file(path_b, algo), algo)


def compare_blobs(data_a, data_b, algo="sha256"):
    if algo not in ALGOS:
        raise CharsetError("unknown hash algorithm: %s" % algo)
    return _compare_result(hash_blob(data_a, algo), hash_blob(data_b, algo), algo)


def hash_tree(root, algo="sha256"):
    if algo not in ALGOS:
        raise CharsetError("unknown hash algorithm: %s" % algo)
    if not os.path.isdir(root):
        raise CharsetError("not a folder")
    files = []
    total = 0
    for dirpath, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for name in sorted(names):
            if name.startswith("."):
                continue
            path = os.path.join(dirpath, name)
            try:
                info = os.lstat(path)
            except OSError:
                continue
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                continue
            total += info.st_size
            if len(files) >= MAX_TREE_FILES or total > MAX_TREE_BYTES:
                raise CharsetError(
                    "folder too large to hash (max %d files or %d bytes)"
                    % (MAX_TREE_FILES, MAX_TREE_BYTES)
                )
            rel = os.path.relpath(path, root).replace("\\", "/")
            files.append({"path": rel, "digest": hash_file(path, algo)})
    return {
        "ok": True,
        "algo": algo,
        "legacy": ALGOS[algo]["legacy"],
        "count": len(files),
        "files": files,
    }

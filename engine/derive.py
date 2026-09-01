from engine.bip85 import derive_bip85_mnemonic
from engine.btc import derive_btc
from engine.charset import CharsetError
from engine.entropy import ByteSource, EntropyError, EntropyPool
from engine.nostr import inspect_nsec, nostr_fresh, nostr_from_mnemonic


def _btc(spec, pool):
    return derive_btc(
        spec.get("mnemonic") or "",
        spec.get("passphrase") or "",
        receive=int(spec.get("receive") or 5),
        change=int(spec.get("change") if spec.get("change") is not None else 5),
        taproot=bool(spec.get("taproot")),
    )


def _bip85(spec, pool):
    return derive_bip85_mnemonic(
        spec.get("mnemonic") or "",
        spec.get("passphrase") or "",
        spec.get("words") or 12,
        spec.get("index") if spec.get("index") is not None else 0,
    )


def _nostr_mnemonic(spec, pool):
    return nostr_from_mnemonic(spec.get("mnemonic") or "", spec.get("passphrase") or "")


def _nostr_inspect(spec, pool):
    return inspect_nsec(spec.get("nsec") or "", spec.get("npub") or "")


def _nostr_fresh(spec, pool):
    data = pool.mix(
        dice=spec.get("dice") or "",
        cards=spec.get("cards") or "",
        nbytes=64,
    )
    value = nostr_fresh(ByteSource(data))
    value["method"] = "fresh os.urandom (not from a mnemonic)"
    value["path"] = ""
    pool.clear()
    return value


NOSTR_MODES = {
    "mnemonic": _nostr_mnemonic,
    "inspect": _nostr_inspect,
    "fresh": _nostr_fresh,
}


def _nostr(spec, pool):
    mode = spec.get("mode") or "mnemonic"
    handler = NOSTR_MODES.get(mode)
    if handler is None:
        raise CharsetError("unknown nostr mode")
    return handler(spec, pool)


HANDLERS = {
    "btc": _btc,
    "bip85": _bip85,
    "nostr": _nostr,
}


def derive(spec, pool=None):
    """Stateless. Callers must drop the spec after use."""
    if pool is None:
        pool = EntropyPool()
    try:
        kind = (spec or {}).get("kind")
        handler = HANDLERS.get(kind)
        if handler is None:
            raise CharsetError("unknown derive kind")
        value = handler(spec, pool)
        return {"ok": True, "value": value, "error": None}
    except (CharsetError, EntropyError, ValueError, OSError) as exc:
        return {"ok": False, "value": None, "error": str(exc)}

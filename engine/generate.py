from engine.age import generate_age_x25519
from engine.bip39 import generate_mnemonic, validate_mnemonic
from engine.charset import CharsetError
from engine.entropy import ByteSource, EntropyError, EntropyPool
from engine.extra import generate_codes, generate_diceware, generate_hex, generate_uuid
from engine.memorable import generate_memorable
from engine.password import generate_password
from engine.persona import FIELD_KEYS, generate_persona
from engine.pin import generate_pin
from engine.ssh import generate_ssh_ed25519


def _pin(source, spec):
    pin_spec = spec.get("pin") or {}
    value = generate_pin(
        source,
        pin_spec.get("charset") or "numeric",
        int(pin_spec.get("length") or 6),
        bool(pin_spec.get("avoid_lookalikes")),
    )
    return value, {"type": "pin", "length": len(value)}


def _password(source, spec):
    value = generate_password(source, spec.get("password") or {})
    return value, {"type": "password", "length": len(value)}


def _memorable(source, spec):
    mem = spec.get("memorable") or {}
    value = generate_memorable(
        source,
        int(mem.get("groups") or 3),
        mem.get("separator") or "-",
    )
    return value, {"type": "memorable", "length": len(value)}


def _diceware(source, spec):
    dw = spec.get("diceware") or {}
    value = generate_diceware(source, int(dw.get("words") or 6))
    return value, {"type": "diceware", "words": len(value.split())}


def _hex(source, spec):
    hx = spec.get("hex") or {}
    value = generate_hex(source, int(hx.get("bytes") or 32))
    return value, {"type": "hex", "bytes": len(value) // 2, "length": len(value)}


def _uuid(source, spec):
    value = generate_uuid(source)
    return value, {"type": "uuid"}


def _codes(source, spec):
    cd = spec.get("codes") or {}
    value = generate_codes(source, int(cd.get("count") or 8))
    return value, {"type": "codes", "count": len(value)}


def _seed(source, spec):
    seed = spec.get("seed") or {}
    value = generate_mnemonic(source, int(seed.get("words") or 12))
    return value, {
        "type": "seed",
        "words": len(value.split()),
        "checksum_valid": validate_mnemonic(value),
    }


def _persona(source, spec):
    persona = spec.get("persona") or {}
    value = generate_persona(source, persona)
    fields = persona.get("fields") or {}
    count = sum(1 for key in FIELD_KEYS if fields.get(key))
    return value, {
        "type": "persona",
        "mode": persona.get("mode") or "full",
        "field_count": count,
    }


def _ssh(source, spec):
    value = generate_ssh_ed25519(source)
    return value, {"type": "ssh", "comment": value.get("comment")}


def _age(source, spec):
    value = generate_age_x25519(source)
    return value, {"type": "age"}


HANDLERS = {
    "pin": _pin,
    "password": _password,
    "memorable": _memorable,
    "diceware": _diceware,
    "hex": _hex,
    "uuid": _uuid,
    "codes": _codes,
    "seed": _seed,
    "persona": _persona,
    "ssh": _ssh,
    "age": _age,
}


def generate(spec, pool=None):
    """Return {ok, value, meta, error}. Never writes to disk."""
    if pool is None:
        pool = EntropyPool()
    try:
        kind = (spec or {}).get("type")
        handler = HANDLERS.get(kind)
        if handler is None:
            raise CharsetError("unknown type")
        data = pool.mix(
            dice=spec.get("dice") or "",
            cards=spec.get("cards") or "",
            nbytes=512,
        )
        value, meta = handler(ByteSource(data), spec)
        pool.clear()
        return {"ok": True, "value": value, "meta": meta, "error": None}
    except (CharsetError, EntropyError, ValueError) as exc:
        return {"ok": False, "value": None, "meta": {}, "error": str(exc)}

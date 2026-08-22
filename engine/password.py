from engine.charset import PRESETS, password_alphabet, CharsetError


def resolve_password_options(spec):
    preset = spec.get("preset") or None
    if preset:
        if preset not in PRESETS:
            raise CharsetError("unknown password preset: %s" % preset)
        opts = dict(PRESETS[preset])
        if spec.get("avoid_lookalikes"):
            opts["avoid_lookalikes"] = True
        else:
            opts["avoid_lookalikes"] = False
        return opts
    opts = {
        "lower": bool(spec.get("lower")),
        "upper": bool(spec.get("upper")),
        "digits": bool(spec.get("digits")),
        "symbols": bool(spec.get("symbols")),
        "length": int(spec.get("length") or 20),
        "avoid_lookalikes": bool(spec.get("avoid_lookalikes")),
    }
    if not (opts["lower"] or opts["upper"] or opts["digits"] or opts["symbols"]):
        opts.update({k: PRESETS["simple"][k] for k in ("lower", "upper", "digits", "symbols", "length")})
    return opts


def generate_password(source, spec):
    opts = resolve_password_options(spec)
    length = opts["length"]
    if length < 8 or length > 64:
        raise CharsetError("password length must be 8-64")
    alphabet, classes = password_alphabet(
        opts["lower"],
        opts["upper"],
        opts["digits"],
        opts["symbols"],
        opts.get("avoid_lookalikes", False),
    )
    if length < len(classes):
        raise CharsetError("password is shorter than the number of required classes")
    chars = [source.choice(alphabet) for _ in range(length)]
    positions = list(range(length))
    for cls in classes:
        idx = source.randbelow(len(positions))
        pos = positions.pop(idx)
        chars[pos] = source.choice(cls)
    return "".join(chars)

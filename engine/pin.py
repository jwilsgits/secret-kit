from engine.charset import pin_alphabet, CharsetError


def generate_pin(source, kind, length, avoid_lookalikes=False):
    if length < 4 or length > 32:
        raise CharsetError("PIN length must be 4-32")
    alphabet = pin_alphabet(kind, avoid_lookalikes)
    return "".join(source.choice(alphabet) for _ in range(length))

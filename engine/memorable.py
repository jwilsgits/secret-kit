from engine.charset import CharsetError
from engine.wordlist import english_words


def generate_memorable(source, groups=3, separator="-"):
    if groups not in (3, 4, 5):
        raise CharsetError("memorable password must use 3, 4, or 5 words")
    if separator not in ("-", ".", "_"):
        raise CharsetError("separator must be - . or _")
    words = list(english_words())
    picked = []
    for _ in range(groups):
        word = source.choice(words)
        words.remove(word)
        picked.append(word)
    parts = []
    for word in picked:
        digits = "%02d" % source.randbelow(100)
        parts.append(word + digits)
    return separator.join(parts)

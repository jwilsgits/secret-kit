from pathlib import Path

_WORDS = None


def english_words():
    global _WORDS
    if _WORDS is None:
        path = Path(__file__).resolve().parent.parent / "data" / "english.txt"
        words = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if len(words) != 2048:
            raise RuntimeError(
                "BIP-39 English wordlist must contain 2048 words, found %d"
                % len(words)
            )
        _WORDS = words
    return _WORDS

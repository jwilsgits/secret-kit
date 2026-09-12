"""UI twin for Keys write-down answers. Not used on the generate/HTTP path."""


def answers_match(mnemonic, answers):
    """Return True if every answer matches the mnemonic word at index (1-based).

    Match rule: trim, collapse internal whitespace, lowercase; must equal the
    full BIP-39 word (no prefix). Empty word fails. All-or-nothing.
    """
    words = (mnemonic or "").split()
    if not answers:
        return False
    for item in answers:
        try:
            index = int(item.get("index"))
        except (TypeError, ValueError, AttributeError):
            return False
        if index < 1 or index > len(words):
            return False
        raw = item.get("word")
        if raw is None:
            return False
        normalized = " ".join(str(raw).split()).lower()
        if not normalized or normalized != words[index - 1].lower():
            return False
    return True

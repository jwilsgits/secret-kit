import unittest

from engine.bip39 import mnemonic_from_entropy, validate_mnemonic
from engine.generate import generate
from engine.wordlist import english_words


VECTORS_12 = [
    (
        "00000000000000000000000000000000",
        "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
    ),
    (
        "7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f",
        "legal winner thank year wave sausage worth useful legal winner thank yellow",
    ),
    (
        "80808080808080808080808080808080",
        "letter advice cage absurd amount doctor acoustic avoid letter advice cage above",
    ),
    (
        "ffffffffffffffffffffffffffffffff",
        "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong",
    ),
]

VECTORS_24 = [
    (
        "0000000000000000000000000000000000000000000000000000000000000000",
        "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art",
    ),
]


class WordlistTests(unittest.TestCase):
    def test_length_and_ends(self):
        words = english_words()
        self.assertEqual(len(words), 2048)
        self.assertEqual(words[0], "abandon")
        self.assertEqual(words[-1], "zoo")


class VectorTests(unittest.TestCase):
    def test_twelve(self):
        for ent_hex, mnemonic in VECTORS_12:
            got = mnemonic_from_entropy(bytes.fromhex(ent_hex))
            self.assertEqual(got, mnemonic)
            self.assertTrue(validate_mnemonic(got))

    def test_twenty_four(self):
        for ent_hex, mnemonic in VECTORS_24:
            got = mnemonic_from_entropy(bytes.fromhex(ent_hex))
            self.assertEqual(got, mnemonic)
            self.assertTrue(validate_mnemonic(got))

    def test_invalid_checksum(self):
        good = VECTORS_12[0][1]
        parts = good.split()
        parts[-1] = "zoo" if parts[-1] != "zoo" else "abandon"
        self.assertFalse(validate_mnemonic(" ".join(parts)))

    def test_unknown_word(self):
        self.assertFalse(validate_mnemonic("notaword " * 12))


class GenerateSeedTests(unittest.TestCase):
    def test_generate_twelve_valid(self):
        result = generate({"type": "seed", "seed": {"words": 12}})
        self.assertTrue(result["ok"], result.get("error"))
        self.assertEqual(len(result["value"].split()), 12)
        self.assertTrue(result["meta"]["checksum_valid"])
        self.assertTrue(validate_mnemonic(result["value"]))

    def test_generate_twenty_four_valid(self):
        result = generate({"type": "seed", "seed": {"words": 24}})
        self.assertTrue(result["ok"], result.get("error"))
        self.assertEqual(len(result["value"].split()), 24)
        self.assertTrue(validate_mnemonic(result["value"]))


if __name__ == "__main__":
    unittest.main()

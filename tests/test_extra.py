import re
import unittest

from engine.entropy import ByteSource
from engine.extra import generate_codes, generate_diceware, generate_hex, generate_uuid
from engine.generate import generate
from engine.wordlist import english_words


def src():
    return ByteSource(bytes((i * 23 + 11) % 256 for i in range(512)))


class ExtraGenTests(unittest.TestCase):
    def test_hex_lengths(self):
        self.assertEqual(len(generate_hex(src(), 16)), 32)
        self.assertEqual(len(generate_hex(src(), 32)), 64)
        self.assertTrue(re.fullmatch(r"[0-9a-f]+", generate_hex(src(), 32)))

    def test_uuid_v4(self):
        value = generate_uuid(src())
        self.assertRegex(value, r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")

    def test_codes(self):
        codes = generate_codes(src(), 8)
        self.assertEqual(len(codes), 8)
        self.assertEqual(len(set(codes)), 8)
        for code in codes:
            self.assertRegex(code, r"^[a-kmnp-z2-9]{5}-[a-kmnp-z2-9]{5}$")

    def test_diceware(self):
        phrase = generate_diceware(src(), 6)
        parts = phrase.split(" ")
        self.assertEqual(len(parts), 6)
        self.assertEqual(len(set(parts)), 6)
        words = set(english_words())
        self.assertTrue(set(parts) <= words)

    def test_generate_dispatch(self):
        hexed = generate({"type": "hex", "hex": {"bytes": 32}})
        self.assertTrue(hexed["ok"], hexed.get("error"))
        self.assertEqual(len(hexed["value"]), 64)
        uid = generate({"type": "uuid"})
        self.assertTrue(uid["ok"])
        self.assertEqual(uid["value"].count("-"), 4)
        codes = generate({"type": "codes", "codes": {"count": 10}})
        self.assertTrue(codes["ok"])
        self.assertEqual(len(codes["value"]), 10)
        dw = generate({"type": "diceware", "diceware": {"words": 5}})
        self.assertTrue(dw["ok"])
        self.assertEqual(len(dw["value"].split()), 5)

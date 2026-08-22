import unittest

from engine.entropy import (
    ALL_CARDS,
    EntropyError,
    EntropyPool,
    hkdf_sha256,
    parse_cards,
    parse_dice,
    require_urandom,
)


class HkdfTests(unittest.TestCase):
    def test_deterministic(self):
        a = hkdf_sha256(b"ikm-one", b"salt-a", b"secret-kit-v1", 32)
        b = hkdf_sha256(b"ikm-one", b"salt-a", b"secret-kit-v1", 32)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 32)

    def test_salt_changes_output(self):
        ikm = b"same-ikm-bytes-here-please!!!!"
        a = hkdf_sha256(ikm, b"salt-a", b"secret-kit-v1", 32)
        b = hkdf_sha256(ikm, b"salt-b", b"secret-kit-v1", 32)
        self.assertNotEqual(a, b)

    def test_ikm_required_to_differ(self):
        salt = b"user-digest"
        a = hkdf_sha256(b"ikm-aaaaaaaaaaaaaaaaaaaaaaaaaaaa", salt, b"secret-kit-v1", 32)
        b = hkdf_sha256(b"ikm-bbbbbbbbbbbbbbbbbbbbbbbbbbbb", salt, b"secret-kit-v1", 32)
        self.assertNotEqual(a, b)

    def test_rfc5869_a1(self):
        okm = hkdf_sha256(
            bytes.fromhex("0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b"),
            bytes.fromhex("000102030405060708090a0b0c"),
            bytes.fromhex("f0f1f2f3f4f5f6f7f8f9"),
            42,
        )
        self.assertEqual(
            okm,
            bytes.fromhex(
                "3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf34007208d5b887185865"
            ),
        )

    def test_rfc5869_a3_empty_salt(self):
        okm = hkdf_sha256(
            bytes.fromhex("0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b"),
            b"",
            b"",
            42,
        )
        self.assertEqual(
            okm,
            bytes.fromhex(
                "8da4e775a563c18f715f802a063c5a31b8a11f5c5ee1879ec3454e5f3c738d2d9d201395faa4b61a96c8"
            ),
        )


class DiceTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(parse_dice(""), "")
        self.assertEqual(parse_dice("   "), "")
        self.assertEqual(parse_dice(None), "")

    def test_valid(self):
        self.assertEqual(parse_dice("1 2 3 4 5 6"), "123456")

    def test_rejects_zero_and_seven(self):
        with self.assertRaises(EntropyError):
            parse_dice("7")
        with self.assertRaises(EntropyError):
            parse_dice("120")


class CardTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(parse_cards(""), "")

    def test_complete_deck(self):
        text = " ".join(ALL_CARDS)
        self.assertEqual(parse_cards(text), text)

    def test_rejects_short(self):
        with self.assertRaises(EntropyError):
            parse_cards("AS KH")

    def test_rejects_duplicate(self):
        cards = ALL_CARDS[:]
        cards[-1] = cards[0]
        with self.assertRaises(EntropyError):
            parse_cards(" ".join(cards))


class PoolTests(unittest.TestCase):
    def test_urandom_works(self):
        self.assertEqual(len(require_urandom()), 32)

    def test_mix_length_without_user(self):
        pool = EntropyPool()
        out = pool.mix(nbytes=64)
        self.assertEqual(len(out), 64)

    def test_mix_with_mouse_and_dice(self):
        pool = EntropyPool()
        n = pool.absorb_mouse([{"t": 1, "x": 2, "y": 3}, {"t": 4, "x": 5, "y": 6}])
        self.assertEqual(n, 2)
        out = pool.mix(dice="123456", nbytes=48)
        self.assertEqual(len(out), 48)


if __name__ == "__main__":
    unittest.main()

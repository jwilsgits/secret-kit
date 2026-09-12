"""age X25519 identity / recipient tests."""

import unittest

from engine.age import generate_age_x25519, public_from_identity, recipient_from_public
from engine.ed25519 import x25519
from engine.entropy import ByteSource

RFC7748_ALICE = bytes.fromhex(
    "77076d0a7318a57d3c16c17251b26645df4c2f87ebc0992ab177fba51db92c2a"
)
RFC7748_ALICE_PUB = bytes.fromhex(
    "8520f0098930a754748b7ddcb43ef75a0dbf3a0d26381af4eba4a98eaa9b4e6a"
)


class AgeTests(unittest.TestCase):
    def test_fixed_scalar_recipient(self):
        self.assertEqual(x25519(RFC7748_ALICE, bytes([9] + [0] * 31)), RFC7748_ALICE_PUB)
        rec = recipient_from_public(RFC7748_ALICE_PUB)
        self.assertTrue(rec.startswith("age1"))
        self.assertEqual(rec, rec.lower())

    def test_generate_roundtrip(self):
        src = ByteSource(RFC7748_ALICE + b"\x22" * 32)
        out = generate_age_x25519(src)
        self.assertEqual(out["type"], "age")
        self.assertTrue(out["recipient"].startswith("age1"))
        self.assertTrue(out["identity"].startswith("AGE-SECRET-KEY-1"))
        self.assertEqual(out["identity"], out["identity"].upper())
        self.assertEqual(out["public"], out["recipient"])
        self.assertEqual(out["private"], out["identity"])
        self.assertEqual(public_from_identity(out["identity"]), RFC7748_ALICE_PUB)
        self.assertEqual(out["recipient"], recipient_from_public(RFC7748_ALICE_PUB))


if __name__ == "__main__":
    unittest.main()

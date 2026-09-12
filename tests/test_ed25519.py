"""RFC 8032 Ed25519 and RFC 7748 X25519 (pure Python, hashlib only)."""

import hashlib
import unittest

from engine.charset import CharsetError
from engine.ed25519 import (
    ed25519_public_from_seed,
    generate_ed25519_keypair,
    generate_x25519_keypair,
    x25519,
)
from engine.entropy import ByteSource


# RFC 8032 §7.1 TEST 1
RFC8032_SECRET = bytes.fromhex(
    "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
)
RFC8032_PUBLIC = bytes.fromhex(
    "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
)

# RFC 7748 §6.1 Alice
RFC7748_ALICE = bytes.fromhex(
    "77076d0a7318a57d3c16c17251b26645df4c2f87ebc0992ab177fba51db92c2a"
)
RFC7748_ALICE_PUB = bytes.fromhex(
    "8520f0098930a754748b7ddcb43ef75a0dbf3a0d26381af4eba4a98eaa9b4e6a"
)


class Ed25519Tests(unittest.TestCase):
    def test_rfc8032_test1_public(self):
        self.assertEqual(ed25519_public_from_seed(RFC8032_SECRET), RFC8032_PUBLIC)

    def test_generate_ed25519_uses_source(self):
        src = ByteSource(RFC8032_SECRET + b"\x00" * 32)
        out = generate_ed25519_keypair(src)
        self.assertEqual(out["seed"], RFC8032_SECRET)
        self.assertEqual(out["public"], RFC8032_PUBLIC)

    def test_rfc7748_alice(self):
        self.assertEqual(x25519(RFC7748_ALICE, bytes([9] + [0] * 31)), RFC7748_ALICE_PUB)

    def test_generate_x25519_uses_source(self):
        src = ByteSource(RFC7748_ALICE + b"\x00" * 32)
        out = generate_x25519_keypair(src)
        self.assertEqual(out["scalar"], RFC7748_ALICE)
        self.assertEqual(out["public"], RFC7748_ALICE_PUB)

    def test_rejects_non_source(self):
        with self.assertRaises(CharsetError):
            generate_ed25519_keypair(b"\x00" * 32)


if __name__ == "__main__":
    unittest.main()

"""OpenSSH Ed25519 generate tests (no ssh-keygen)."""

import base64
import unittest

from engine.ed25519 import ed25519_public_from_seed
from engine.entropy import ByteSource
from engine.ssh import COMMENT, generate_ssh_ed25519, parse_public_from_private_pem, public_line


RFC8032_SECRET = bytes.fromhex(
    "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
)


class SshTests(unittest.TestCase):
    def test_public_line_format(self):
        pub = ed25519_public_from_seed(RFC8032_SECRET)
        line = public_line(pub)
        self.assertTrue(line.startswith("ssh-ed25519 "))
        self.assertTrue(line.endswith(" " + COMMENT))
        parts = line.split()
        self.assertEqual(len(parts), 3)
        wire = base64.b64decode(parts[1])
        self.assertTrue(wire.endswith(pub))

    def test_private_roundtrip_public(self):
        src = ByteSource(RFC8032_SECRET + b"\x11" * 32)
        out = generate_ssh_ed25519(src)
        self.assertEqual(out["type"], "ssh")
        self.assertEqual(out["comment"], COMMENT)
        self.assertIn("BEGIN OPENSSH PRIVATE KEY", out["private"])
        recovered = parse_public_from_private_pem(out["private"])
        want = ed25519_public_from_seed(RFC8032_SECRET)
        self.assertEqual(recovered, want)
        wire = base64.b64decode(out["public"].split()[1])
        self.assertTrue(wire.endswith(want))


if __name__ == "__main__":
    unittest.main()

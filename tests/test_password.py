import string
import unittest

from engine.charset import LOOKALIKES, SYMBOLS
from engine.entropy import ByteSource
from engine.password import generate_password, resolve_password_options


def src():
    return ByteSource(os_urandom_like())


def os_urandom_like():
    return bytes((i * 17 + 31) % 256 for i in range(512))


class PasswordTests(unittest.TestCase):
    def test_simple_preset(self):
        opts = resolve_password_options({"preset": "simple"})
        self.assertEqual(opts["length"], 16)
        self.assertFalse(opts["symbols"])
        pw = generate_password(src(), {"preset": "simple"})
        self.assertEqual(len(pw), 16)
        self.assertTrue(any(c.islower() for c in pw))
        self.assertTrue(any(c.isupper() for c in pw))
        self.assertTrue(any(c.isdigit() for c in pw))
        self.assertTrue(all(c in string.ascii_letters + string.digits for c in pw))

    def test_strong_and_paranoid_length(self):
        self.assertEqual(len(generate_password(src(), {"preset": "strong"})), 20)
        self.assertEqual(len(generate_password(src(), {"preset": "paranoid"})), 32)

    def test_class_guarantee_symbols(self):
        pw = generate_password(src(), {"preset": "strong"})
        self.assertTrue(any(c in SYMBOLS for c in pw))

    def test_advanced_length(self):
        pw = generate_password(
            src(),
            {
                "lower": True,
                "upper": False,
                "digits": True,
                "symbols": False,
                "length": 12,
            },
        )
        self.assertEqual(len(pw), 12)
        self.assertTrue(any(c.islower() for c in pw))
        self.assertTrue(any(c.isdigit() for c in pw))

    def test_lookalikes_off_path_still_works(self):
        pw = generate_password(src(), {"preset": "simple", "avoid_lookalikes": True})
        self.assertTrue(LOOKALIKES.isdisjoint(pw))


if __name__ == "__main__":
    unittest.main()

import unittest

from engine.charset import LOOKALIKES
from engine.entropy import ByteSource
from engine.pin import generate_pin


def src():
    return ByteSource(bytes(range(256)) * 4)


class PinTests(unittest.TestCase):
    def test_length_and_numeric(self):
        pin = generate_pin(src(), "numeric", 6)
        self.assertEqual(len(pin), 6)
        self.assertTrue(pin.isdigit())

    def test_letters_only(self):
        pin = generate_pin(src(), "letters", 8)
        self.assertEqual(len(pin), 8)
        self.assertTrue(pin.isalpha())

    def test_lookalikes_flag(self):
        pin = generate_pin(src(), "alphanumeric", 16, avoid_lookalikes=True)
        self.assertTrue(LOOKALIKES.isdisjoint(pin))

    def test_custom_length(self):
        pin = generate_pin(src(), "numeric", 12)
        self.assertEqual(len(pin), 12)

    def test_rejects_short(self):
        with self.assertRaises(Exception):
            generate_pin(src(), "numeric", 3)


if __name__ == "__main__":
    unittest.main()

import unittest

from engine.charset import (
    CharsetError,
    LOOKALIKES,
    password_alphabet,
    pin_alphabet,
)


class PinAlphabetTests(unittest.TestCase):
    def test_numeric(self):
        self.assertEqual(pin_alphabet("numeric"), "0123456789")

    def test_letters_has_no_digits(self):
        alpha = pin_alphabet("letters")
        self.assertTrue(all(ch.isalpha() for ch in alpha))

    def test_lookalikes_stripped(self):
        alpha = pin_alphabet("alphanumeric", avoid_lookalikes=True)
        self.assertTrue(LOOKALIKES.isdisjoint(alpha))
        self.assertIn("2", alpha)
        self.assertIn("A", alpha)

    def test_unknown(self):
        with self.assertRaises(CharsetError):
            pin_alphabet("hex")


class PasswordAlphabetTests(unittest.TestCase):
    def test_requires_a_class(self):
        with self.assertRaises(CharsetError):
            password_alphabet(False, False, False, False)

    def test_classes_match_toggles(self):
        alphabet, classes = password_alphabet(True, False, True, False)
        self.assertEqual(len(classes), 2)
        self.assertTrue(set(alphabet) >= set(classes[0] + classes[1]))


if __name__ == "__main__":
    unittest.main()

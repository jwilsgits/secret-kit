import unittest

from engine.entropy import ByteSource
from engine.memorable import generate_memorable
from engine.wordlist import english_words


def src():
    return ByteSource(bytes((i * 13 + 7) % 256 for i in range(512)))


class MemorableTests(unittest.TestCase):
    def test_default_three_dash(self):
        value = generate_memorable(src(), 3, "-")
        parts = value.split("-")
        self.assertEqual(len(parts), 3)
        words = english_words()
        seen = []
        for part in parts:
            self.assertRegex(part, r"^[a-z]+[0-9]{2}$")
            word, digits = part[:-2], part[-2:]
            self.assertIn(word, words)
            self.assertTrue(digits.isdigit())
            seen.append(word)
        self.assertEqual(len(set(seen)), 3)
        self.assertEqual(len(value), sum(len(p) for p in parts) + 2)

    def test_four_dot_and_five_underscore(self):
        four = generate_memorable(src(), 4, ".")
        self.assertEqual(len(four.split(".")), 4)
        five = generate_memorable(src(), 5, "_")
        self.assertEqual(len(five.split("_")), 5)

    def test_rejects_bad_groups(self):
        with self.assertRaises(Exception):
            generate_memorable(src(), 2, "-")


if __name__ == "__main__":
    unittest.main()

"""Match-rule twin for the Keys write-down check (UI owns the real gate)."""

import unittest

from engine.seedcheck import answers_match


# Fixed BIP-39 English words for tests only (not a live wallet).
MNEMONIC_12 = (
    "abandon ability able about above absent absorb abstract absurd abuse access accident"
)


class SeedCheckTests(unittest.TestCase):
    def test_happy_path_exact_words(self):
        answers = [
            {"index": 1, "word": "abandon"},
            {"index": 7, "word": "absorb"},
            {"index": 12, "word": "accident"},
        ]
        self.assertTrue(answers_match(MNEMONIC_12, answers))

    def test_wrong_word_fails(self):
        answers = [
            {"index": 1, "word": "abandon"},
            {"index": 7, "word": "wrong"},
            {"index": 12, "word": "accident"},
        ]
        self.assertFalse(answers_match(MNEMONIC_12, answers))

    def test_prefix_fails(self):
        answers = [{"index": 1, "word": "aban"}]
        self.assertFalse(answers_match(MNEMONIC_12, answers))

    def test_mixed_case_passes(self):
        answers = [{"index": 1, "word": "Abandon"}]
        self.assertTrue(answers_match(MNEMONIC_12, answers))

    def test_empty_word_fails(self):
        answers = [{"index": 1, "word": ""}]
        self.assertFalse(answers_match(MNEMONIC_12, answers))

    def test_whitespace_trimmed(self):
        answers = [{"index": 2, "word": "  Ability  "}]
        self.assertTrue(answers_match(MNEMONIC_12, answers))

    def test_internal_whitespace_collapsed(self):
        # Collapsed empty still must equal the exact word — spaces-only fails.
        answers = [{"index": 1, "word": "   "}]
        self.assertFalse(answers_match(MNEMONIC_12, answers))

    def test_out_of_range_index_fails(self):
        answers = [{"index": 99, "word": "abandon"}]
        self.assertFalse(answers_match(MNEMONIC_12, answers))

    def test_index_zero_fails(self):
        answers = [{"index": 0, "word": "abandon"}]
        self.assertFalse(answers_match(MNEMONIC_12, answers))


if __name__ == "__main__":
    unittest.main()

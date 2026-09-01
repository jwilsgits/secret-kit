import unittest

from engine.bip32 import Node
from engine.bip85 import derive_bip85_mnemonic, mnemonic_from_node
from engine.charset import CharsetError

VECTOR_XPRV = (
    "xprv9s21ZrQH143K2LBWUUQRFXhucrQqBpKdRRxNVq2zBqsx8HVqFk2uYo8kmbaLLHRdqtQpUm98u"
    "Kfu3vca1LqdGhUtyoFnCNkfmXRyPXLjbKb"
)
CHILD_12 = "girl mad pet galaxy egg matter matrix prison refuse sense ordinary nose"
CHILD_24 = (
    "puppy ocean match cereal symbol another shed magic wrap hammer bulb intact "
    "gadget divorce twin tonight reason outdoor destroy simple truth cigar social volcano"
)


class Bip85VectorTests(unittest.TestCase):
    def test_12_english_index_0(self):
        node = Node.from_extended(VECTOR_XPRV)
        self.assertEqual(mnemonic_from_node(node, 12, 0), CHILD_12)

    def test_24_english_index_0(self):
        node = Node.from_extended(VECTOR_XPRV)
        self.assertEqual(mnemonic_from_node(node, 24, 0), CHILD_24)


class Bip85MnemonicTests(unittest.TestCase):
    def test_rejects_bad_mnemonic(self):
        with self.assertRaises(CharsetError):
            derive_bip85_mnemonic("not a real seed phrase at all extra", "", 12, 0)

    def test_rejects_index_out_of_range(self):
        phrase = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        with self.assertRaises(CharsetError):
            derive_bip85_mnemonic(phrase, "", 12, -1)
        with self.assertRaises(CharsetError):
            derive_bip85_mnemonic(phrase, "", 12, 1000)

    def test_12_and_24_differ(self):
        phrase = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        a = derive_bip85_mnemonic(phrase, "", 12, 0)
        b = derive_bip85_mnemonic(phrase, "", 24, 0)
        self.assertNotEqual(a["mnemonic"], b["mnemonic"])
        self.assertEqual(a["path"], "m/83696968'/39'/0'/12'/0'")
        self.assertEqual(b["words"], 24)

import unittest

from engine.bip32 import Node, XPRV
from engine.secp256k1 import SecpError

VECTOR_XPRV = (
    "xprv9s21ZrQH143K2LBWUUQRFXhucrQqBpKdRRxNVq2zBqsx8HVqFk2uYo8kmbaLLHRdqtQpUm98u"
    "Kfu3vca1LqdGhUtyoFnCNkfmXRyPXLjbKb"
)


class ExtendedKeyTests(unittest.TestCase):
    def test_from_extended_xprv_roundtrip(self):
        node = Node.from_extended(VECTOR_XPRV)
        self.assertIsNotNone(node.priv)
        self.assertEqual(node.extended(True, XPRV), VECTOR_XPRV)

    def test_from_extended_rejects_garbage(self):
        with self.assertRaises((ValueError, SecpError, Exception)):
            Node.from_extended("not-an-xprv")

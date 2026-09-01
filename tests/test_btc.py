import unittest

from engine.bip39 import mnemonic_to_seed
from engine.btc import derive_btc
from engine.ripemd160 import ripemd160

ABANDON = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"


class RipemdTests(unittest.TestCase):
    def test_abc(self):
        # RIPEMD-160("abc")
        self.assertEqual(
            ripemd160(b"abc").hex(),
            "8eb208f7e05d987a9b044a8e98c6b087f15a0bfc",
        )


class SeedTests(unittest.TestCase):
    def test_empty_passphrase_abandon(self):
        seed = mnemonic_to_seed(ABANDON, "")
        self.assertEqual(
            seed.hex(),
            "5eb00bbddcf069084889a8ab9155568165f5c453ccb85e70811aaed6f6da5fc19a5ac40b389cd370d086206dec8aa6c43daea6690f20ad3d8d48b2d2ce9e38e4",
        )

    def test_trezor_passphrase(self):
        seed = mnemonic_to_seed(ABANDON, "TREZOR")
        self.assertEqual(
            seed.hex(),
            "c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e53495531f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04",
        )


class Bip84Tests(unittest.TestCase):
    def test_first_address_and_zpub(self):
        out = derive_btc(ABANDON, "", receive=2, change=1)
        self.assertEqual(out["address"], "bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu")
        self.assertEqual(
            out["zpub"],
            "zpub6rFR7y4Q2AijBEqTUquhVz398htDFrtymD9xYYfG1m4wAcvPhXNfE3EfH1r1ADqtfSdVCToUG868RvUUkgDKf31mGDtKsAYz2oz2AGutZYs",
        )
        self.assertEqual(out["path_address"], "m/84'/0'/0'/0/0")
        self.assertEqual(
            out["zprv"],
            "zprvAdG4iTXWBoARxkkzNpNh8r6Qag3irQB8PzEMkAFeTRXxHpbF9z4QgEvBRmfvqWvGp42t42nvgGpNgYSJA9iefm1yYNZKEm7z6qUWCroSQnE",
        )
        self.assertEqual(len(out["receive"]), 2)
        self.assertEqual(len(out["change"]), 1)
        self.assertEqual(out["receive"][1]["address"], "bc1qnjg0jd8228aq7egyzacy8cys3knf9xvrerkf9g")
        self.assertIsNone(out["taproot"])

    def test_bip86_first_address(self):
        out = derive_btc(ABANDON, "", receive=1, change=0, taproot=True)
        self.assertEqual(
            out["taproot"]["address"],
            "bc1p5cyxnuxmeuwuvkwfem96lqzszd02n6xdcjrs20cac6yqjjwudpxqkedrcr",
        )

    def test_rejects_bad_mnemonic(self):
        with self.assertRaises(Exception):
            derive_btc("not a real seed phrase at all extra", "")


class DescriptorTests(unittest.TestCase):
    def test_wpkh_receive_abandon(self):
        out = derive_btc(ABANDON, "", receive=1, change=0)
        desc = out["descriptor_receive"]
        self.assertTrue(desc.startswith("wpkh(["))
        self.assertIn("/84h/0h/0h]", desc)
        self.assertTrue(desc.endswith("/0/*)"))
        self.assertNotIn("zpub", desc)
        self.assertIsNone(out["descriptor_change"])
        self.assertEqual(out["address"], "bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu")

    def test_tr_when_taproot(self):
        out = derive_btc(ABANDON, "", receive=1, change=1, taproot=True)
        self.assertTrue(out["taproot"]["descriptor_receive"].startswith("tr(["))
        self.assertIn("/86h/0h/0h]", out["taproot"]["descriptor_receive"])
        self.assertTrue(out["descriptor_change"].endswith("/1/*)"))

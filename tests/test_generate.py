import unittest

from engine.generate import generate


class GenerateDispatchTests(unittest.TestCase):
    def test_pin(self):
        result = generate({"type": "pin", "pin": {"charset": "numeric", "length": 6}})
        self.assertTrue(result["ok"], result.get("error"))
        self.assertEqual(len(result["value"]), 6)
        self.assertTrue(result["value"].isdigit())

    def test_password_preset(self):
        result = generate({"type": "password", "password": {"preset": "strong"}})
        self.assertTrue(result["ok"], result.get("error"))
        self.assertEqual(len(result["value"]), 20)

    def test_memorable(self):
        result = generate(
            {"type": "memorable", "memorable": {"groups": 3, "separator": "-"}}
        )
        self.assertTrue(result["ok"], result.get("error"))
        self.assertEqual(len(result["value"].split("-")), 3)

    def test_bad_dice(self):
        result = generate({"type": "pin", "dice": "7"})
        self.assertFalse(result["ok"])
        self.assertIn("dice", result["error"])

    def test_unknown_type(self):
        result = generate({"type": "widget"})
        self.assertFalse(result["ok"])


class WorkbenchDeriveTests(unittest.TestCase):
    def test_btc_abandon(self):
        from engine.derive import derive

        result = derive(
            {
                "kind": "btc",
                "mnemonic": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
            }
        )
        self.assertTrue(result["ok"], result.get("error"))
        self.assertEqual(result["value"]["address"], "bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu")

    def test_check_mnemonic(self):
        from engine.bip39 import validate_mnemonic

        self.assertTrue(
            validate_mnemonic(
                "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
            )
        )
        self.assertFalse(validate_mnemonic("abandon " * 12))

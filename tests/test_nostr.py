import unittest

from engine.entropy import ByteSource
from engine.nostr import nostr_fresh, nostr_from_mnemonic
from engine.derive import derive

NIP06_MNEMONIC = (
    "leader monkey parrot ring guide accident before fence cannon height naive bean"
)
NIP06_PRIV = "7f7ff03d123792d6ac594bfa67bf6d0c0ab55b6b1fdb6249303fe861f1ccba9a"


class Nip06Tests(unittest.TestCase):
    def test_known_vector(self):
        out = nostr_from_mnemonic(NIP06_MNEMONIC, "")
        self.assertEqual(out["path"], "m/44'/1237'/0'/0/0")
        # nsec payload is the 32-byte private key
        self.assertTrue(out["nsec"].startswith("nsec1"))
        self.assertTrue(out["npub"].startswith("npub1"))
        from engine.bech32 import CHARSET

        # Cross-check private key hex via re-deriving
        self.assertEqual(
            _nsec_to_hex(out["nsec"]),
            NIP06_PRIV,
        )

    def test_fresh_pair(self):
        src = ByteSource(bytes((i * 19 + 3) % 256 for i in range(64)))
        out = nostr_fresh(src)
        self.assertTrue(out["npub"].startswith("npub1"))
        self.assertTrue(out["nsec"].startswith("nsec1"))

    def test_fresh_skips_invalid_scalar(self):
        valid = bytes.fromhex(NIP06_PRIV)
        out = nostr_fresh(ByteSource(b"\x00" * 32 + valid))
        self.assertEqual(_nsec_to_hex(out["nsec"]), NIP06_PRIV)

    def test_workbench_dispatch(self):
        result = derive({"kind": "nostr", "mode": "mnemonic", "mnemonic": NIP06_MNEMONIC})
        self.assertTrue(result["ok"], result.get("error"))
        self.assertEqual(_nsec_to_hex(result["value"]["nsec"]), NIP06_PRIV)

    def test_inspect_nsec(self):
        from engine.nostr import inspect_nsec

        pair = nostr_from_mnemonic(NIP06_MNEMONIC, "")
        out = inspect_nsec(pair["nsec"])
        self.assertEqual(out["npub"], pair["npub"])
        self.assertNotIn("nsec", out)
        matched = inspect_nsec(pair["nsec"], pair["npub"])
        self.assertTrue(matched["match"])
        other = nostr_fresh(ByteSource(bytes(range(64))))
        mismatch = inspect_nsec(pair["nsec"], other["npub"])
        self.assertFalse(mismatch["match"])

    def test_inspect_rejects_garbage(self):
        result = derive({"kind": "nostr", "mode": "inspect", "nsec": "not-an-nsec"})
        self.assertFalse(result["ok"])


def _nsec_to_hex(nsec):
    from engine.bech32 import CHARSET, convertbits

    pos = nsec.rfind("1")
    data = [CHARSET.find(c) for c in nsec[pos + 1 :]]
    payload = bytes(convertbits(data[:-6], 5, 8, False))
    return payload.hex()


if __name__ == "__main__":
    unittest.main()

import os
import tempfile
import unittest
from pathlib import Path

from engine.openpgp import verify_detached

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "openpgp"
RSA_FINGERPRINT = "0ABDF4E185B4E211D9AD05417DC374A96E063FCE"
ED25519_FINGERPRINT = "91A2D067F20A067118E95E2771017E321F51CA10"
ISSUER_ERROR = "This signature was not made by the key file you supplied."
HASH_ERROR = "This signature uses a hash Secret Kit will not accept."


def _read(name):
    return (FIXTURES / name).read_bytes()


class OpenPgpVerifyTests(unittest.TestCase):
    def test_good_rsa_sha256(self):
        result = verify_detached(
            str(FIXTURES / "payload.bin"),
            _read("good.asc"),
            _read("key.asc"),
        )
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["good"], result)
        self.assertIsNone(result["error"])
        self.assertEqual(result["fingerprint"], RSA_FINGERPRINT)
        self.assertEqual(result["user_id"], "Secret Kit Test RSA <test@example.invalid>")
        self.assertEqual(result["subkey_id"], "")
        self.assertEqual(result["hash_algo"], "sha256")
        self.assertFalse(result["expired"])
        self.assertFalse(result["revoked"])

    def test_wrong_payload_is_bad_not_error(self):
        handle, path = tempfile.mkstemp()
        os.write(handle, b"this is not the signed payload\n")
        os.close(handle)
        try:
            result = verify_detached(path, _read("good.asc"), _read("key.asc"))
        finally:
            os.remove(path)
        self.assertTrue(result["ok"], result)
        self.assertFalse(result["good"])
        self.assertIsNone(result["error"])
        self.assertEqual(result["fingerprint"], RSA_FINGERPRINT)

    def test_wrong_key_issuer_error(self):
        result = verify_detached(
            str(FIXTURES / "payload.bin"),
            _read("good.asc"),
            _read("other_key.asc"),
        )
        self.assertFalse(result["ok"])
        self.assertFalse(result["good"])
        self.assertEqual(result["error"], ISSUER_ERROR)

    def test_sha1_rejected(self):
        result = verify_detached(
            str(FIXTURES / "payload.bin"),
            _read("sha1.asc"),
            _read("key.asc"),
        )
        self.assertFalse(result["ok"])
        self.assertFalse(result["good"])
        self.assertEqual(result["error"], HASH_ERROR)

    def test_streams_payload_larger_than_chunk(self):
        payload = _read("payload.bin")
        handle, path = tempfile.mkstemp()
        os.write(handle, payload)
        os.close(handle)
        try:
            import engine.openpgp as openpgp

            self.assertGreater(len(payload), 16)
            old = openpgp.CHUNK
            openpgp.CHUNK = 16
            try:
                result = verify_detached(path, _read("good.asc"), _read("key.asc"))
            finally:
                openpgp.CHUNK = old
        finally:
            os.remove(path)
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["good"], result)

    def test_good_ed25519(self):
        result = verify_detached(
            str(FIXTURES / "payload.bin"),
            _read("ed25519_good.asc"),
            _read("ed25519_key.asc"),
        )
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["good"], result)
        self.assertEqual(result["fingerprint"], ED25519_FINGERPRINT)
        self.assertEqual(result["hash_algo"], "sha256")


class ApiPgpTests(unittest.TestCase):
    def test_desktop_paths(self):
        from app import Api

        result = Api(http_mode=False).verify_pgp({
            "path": str(FIXTURES / "payload.bin"),
            "path_sig": str(FIXTURES / "good.asc"),
            "path_key": str(FIXTURES / "key.asc"),
        })
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["good"], result)
        self.assertEqual(result["fingerprint"], RSA_FINGERPRINT)

    def test_http_mode_refuses_paths(self):
        from app import Api, HTTP_UPLOAD

        result = Api(http_mode=True).verify_pgp({
            "path": str(FIXTURES / "payload.bin"),
            "path_sig": str(FIXTURES / "good.asc"),
            "path_key": str(FIXTURES / "key.asc"),
        })
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], HTTP_UPLOAD)

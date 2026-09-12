import http.client
import json
import os
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import Api, main
from engine.http_server import serve

PIN = [{"type": "pin", "pin": {"charset": "numeric", "length": 6}}]


class HttpBindTests(unittest.TestCase):
    def test_refuses_lan_without_flag(self):
        self.assertEqual(main(["--http", "0.0.0.0:9"]), 2)


class HttpApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app as appmod

        cls.httpd_thread = threading.Thread(
            target=serve,
            args=(Api(http_mode=True), appmod.ROOT / "ui", "127.0.0.1", 18765),
            daemon=True,
        )
        cls.httpd_thread.start()
        import time

        for _ in range(50):
            try:
                urlopen("http://127.0.0.1:18765/", timeout=0.2).read()
                break
            except Exception:
                time.sleep(0.05)
        else:
            raise RuntimeError("http server did not start")

    def test_index_and_generate(self):
        page = urlopen("http://127.0.0.1:18765/").read()
        self.assertIn(b"Secret Kit", page)
        req = Request(
            "http://127.0.0.1:18765/api/generate",
            data=json.dumps([{"type": "pin", "pin": {"charset": "numeric", "length": 6}}]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        body = json.loads(urlopen(req).read().decode("utf-8"))
        self.assertTrue(body["ok"], body)
        self.assertEqual(len(body["value"]), 6)
        self.assertTrue(body["value"].isdigit())

    def test_unknown_api(self):
        req = Request(
            "http://127.0.0.1:18765/api/not-a-method",
            data=b"[]",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req)
        self.assertEqual(ctx.exception.code, 404)

    def test_derive_bip85(self):
        req = Request(
            "http://127.0.0.1:18765/api/derive",
            data=json.dumps([{
                "kind": "bip85",
                "mnemonic": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
                "words": 12,
                "index": 0,
            }]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        body = json.loads(urlopen(req).read().decode("utf-8"))
        self.assertTrue(body["ok"], body)
        self.assertEqual(body["value"]["path"], "m/83696968'/39'/0'/12'/0'")

    def test_rejects_non_loopback_host(self):
        req = Request(
            "http://127.0.0.1:18765/",
            headers={"Host": "example.com"},
            method="GET",
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req)
        self.assertEqual(ctx.exception.code, 403)

    def test_rejects_foreign_origin(self):
        req = Request(
            "http://127.0.0.1:18765/api/generate",
            data=json.dumps(PIN).encode(),
            headers={
                "Content-Type": "application/json",
                "Origin": "http://evil.example",
            },
            method="POST",
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req)
        self.assertEqual(ctx.exception.code, 403)

    def test_allows_loopback_origin(self):
        req = Request(
            "http://127.0.0.1:18765/api/generate",
            data=json.dumps(PIN).encode(),
            headers={
                "Content-Type": "application/json",
                "Origin": "http://127.0.0.1:18765",
            },
            method="POST",
        )
        body = json.loads(urlopen(req).read().decode("utf-8"))
        self.assertTrue(body["ok"], body)

    def _post_generate(self, origin, body=None):
        req = Request(
            "http://127.0.0.1:18765/api/generate",
            data=json.dumps(body if body is not None else PIN).encode(),
            headers={
                "Content-Type": "application/json",
                "Origin": origin,
            },
            method="POST",
        )
        return urlopen(req)

    def test_allows_ide_origin_when_loopback_bound(self):
        origin = "vscode-webview://webview-panel"
        resp = self._post_generate(origin)
        body = json.loads(resp.read().decode("utf-8"))
        self.assertTrue(body["ok"], body)
        self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), origin)

    def test_allows_null_origin_when_loopback_bound(self):
        resp = self._post_generate("null")
        body = json.loads(resp.read().decode("utf-8"))
        self.assertTrue(body["ok"], body)
        self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "null")

    def test_allows_cursor_origin_when_loopback_bound(self):
        origin = "cursor://file"
        resp = self._post_generate(origin)
        body = json.loads(resp.read().decode("utf-8"))
        self.assertTrue(body["ok"], body)
        self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), origin)

    def test_options_preflight_ide_origin(self):
        conn = http.client.HTTPConnection("127.0.0.1", 18765, timeout=2)
        try:
            conn.putrequest("OPTIONS", "/api/generate")
            conn.putheader("Origin", "vscode-webview://webview-panel")
            conn.putheader("Access-Control-Request-Method", "POST")
            conn.putheader("Access-Control-Request-Headers", "content-type")
            conn.endheaders()
            resp = conn.getresponse()
            status = resp.status
            allow_origin = resp.getheader("Access-Control-Allow-Origin")
            allow_headers = (resp.getheader("Access-Control-Allow-Headers") or "").lower()
        finally:
            conn.close()
        self.assertEqual(status, 204)
        self.assertEqual(allow_origin, "vscode-webview://webview-panel")
        self.assertIn("content-type", allow_headers)

    def test_lan_bind_still_rejects_foreign_origin(self):
        from engine.http_server import KitHandler

        old = KitHandler.bind_loopback
        KitHandler.bind_loopback = False
        try:
            req = Request(
                "http://127.0.0.1:18765/api/generate",
                data=json.dumps(PIN).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Origin": "http://evil.example",
                },
                method="POST",
            )
            with self.assertRaises(HTTPError) as ctx:
                urlopen(req)
            self.assertEqual(ctx.exception.code, 403)
        finally:
            KitHandler.bind_loopback = old

    def test_generate_persona(self):
        spec = [{
            "type": "persona",
            "persona": {
                "mode": "full",
                "gender": "any",
                "age": "any",
                "fields": {
                    "name": True,
                    "dob": True,
                    "gender": True,
                    "street": True,
                    "location": True,
                    "phone": True,
                    "username": True,
                },
            },
        }]
        req = Request(
            "http://127.0.0.1:18765/api/generate",
            data=json.dumps(spec).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        body = json.loads(urlopen(req).read().decode("utf-8"))
        self.assertTrue(body["ok"], body)
        self.assertEqual(body["meta"]["type"], "persona")
        self.assertIn("Full name:", body["value"])

    def test_rejects_bad_content_length(self):
        conn = http.client.HTTPConnection("127.0.0.1", 18765, timeout=2)
        try:
            conn.putrequest("POST", "/api/generate")
            conn.putheader("Content-Type", "application/json")
            conn.putheader("Content-Length", "nope")
            conn.endheaders()
            conn.send(b"[]")
            status = conn.getresponse().status
        finally:
            conn.close()
        self.assertEqual(status, 400)

    def test_rejects_negative_content_length(self):
        conn = http.client.HTTPConnection("127.0.0.1", 18765, timeout=2)
        try:
            conn.putrequest("POST", "/api/generate")
            conn.putheader("Content-Type", "application/json")
            conn.putheader("Content-Length", "-1")
            conn.endheaders()
            status = conn.getresponse().status
        finally:
            conn.close()
        self.assertEqual(status, 400)

    def test_hash_file_refused_in_http_mode(self):
        handle, path = tempfile.mkstemp()
        os.write(handle, b"secret-kit-http-fixture\n")
        os.close(handle)
        try:
            req = Request(
                "http://127.0.0.1:18765/api/hash_file",
                data=json.dumps([{
                    "path": path,
                    "expected": "0" * 64,
                    "algo": "sha256",
                }]).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            body = json.loads(urlopen(req).read().decode("utf-8"))
        finally:
            os.remove(path)
        self.assertFalse(body["ok"])
        self.assertNotIn("digest", body)

    def test_compare_bytes(self):
        import base64

        same = base64.b64encode(b"abc").decode("ascii")
        other = base64.b64encode(b"xyz").decode("ascii")
        req = Request(
            "http://127.0.0.1:18765/api/compare_bytes",
            data=json.dumps([{
                "content_a": same,
                "content_b": same,
                "algo": "sha256",
            }]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        match = json.loads(urlopen(req).read().decode("utf-8"))
        self.assertTrue(match["ok"], match)
        self.assertTrue(match["match"])
        req = Request(
            "http://127.0.0.1:18765/api/compare_bytes",
            data=json.dumps([{
                "content_a": same,
                "content_b": other,
                "algo": "sha256",
            }]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        diff = json.loads(urlopen(req).read().decode("utf-8"))
        self.assertTrue(diff["ok"], diff)
        self.assertFalse(diff["match"])

    def test_verify_pgp_upload(self):
        import base64
        from pathlib import Path

        fixtures = Path(__file__).resolve().parent / "fixtures" / "openpgp"
        req = Request(
            "http://127.0.0.1:18765/api/verify_pgp",
            data=json.dumps([{
                "content_payload": base64.b64encode(
                    (fixtures / "payload.bin").read_bytes()
                ).decode("ascii"),
                "content_sig": base64.b64encode(
                    (fixtures / "good.asc").read_bytes()
                ).decode("ascii"),
                "content_key": base64.b64encode(
                    (fixtures / "key.asc").read_bytes()
                ).decode("ascii"),
            }]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        body = json.loads(urlopen(req).read().decode("utf-8"))
        self.assertTrue(body["ok"], body)
        self.assertTrue(body["good"], body)
        self.assertEqual(body["fingerprint"], "0ABDF4E185B4E211D9AD05417DC374A96E063FCE")

    def test_verify_pgp_path_refused_in_http_mode(self):
        req = Request(
            "http://127.0.0.1:18765/api/verify_pgp",
            data=json.dumps([{
                "path": "/tmp/payload.bin",
                "path_sig": "/tmp/good.asc",
                "path_key": "/tmp/key.asc",
            }]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        body = json.loads(urlopen(req).read().decode("utf-8"))
        self.assertFalse(body["ok"])
        self.assertIn("use an upload in HTTP mode", body["error"])

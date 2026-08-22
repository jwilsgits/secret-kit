import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import Api, main
from engine.http_server import serve


class HttpBindTests(unittest.TestCase):
    def test_refuses_lan_without_flag(self):
        self.assertEqual(main(["--http", "0.0.0.0:9"]), 2)


class HttpApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app as appmod

        cls.httpd_thread = threading.Thread(
            target=serve,
            args=(Api(), appmod.ROOT / "ui", "127.0.0.1", 18765),
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

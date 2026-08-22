"""Loopback HTTP UI for containers. No secrets on disk."""

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

LOOPBACK = frozenset(("127.0.0.1", "localhost", "::1"))
API_METHODS = frozenset((
    "generate",
    "absorb_mouse",
    "clear_user_entropy",
    "check_mnemonic",
    "hash_file",
    "pick_file",
    "pick_folder",
    "compare_files",
    "hash_folder",
    "derive",
    "hash_bytes",
))
MAX_BODY = 32 * 1024 * 1024


class KitHandler(BaseHTTPRequestHandler):
    api = None
    ui_root = None

    def log_message(self, fmt, *args):
        return

    def _host_ok(self):
        host = (self.headers.get("Host") or "").split(":")[0].strip().lower()
        return host in LOOPBACK or host == ""

    def do_GET(self):
        if not self._host_ok():
            self.send_error(403, "loopback only")
            return
        path = urlparse(self.path).path
        if path == "/":
            path = "/index.html"
        path = path.lstrip("/")
        if ".." in path.split("/"):
            self.send_error(400)
            return
        target = (self.ui_root / path).resolve()
        try:
            target.relative_to(self.ui_root.resolve())
        except ValueError:
            self.send_error(403)
            return
        if not target.is_file():
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if not self._host_ok():
            self.send_error(403, "loopback only")
            return
        parsed = urlparse(self.path).path
        if not parsed.startswith("/api/"):
            self.send_error(404)
            return
        name = parsed[len("/api/") :]
        if name not in API_METHODS:
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            self.send_error(413)
            return
        raw = self.rfile.read(length) if length else b"[]"
        try:
            args = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.send_error(400, "invalid json")
            return
        if not isinstance(args, list):
            args = [args]
        method = getattr(self.api, name)
        try:
            result = method(*args)
        except Exception as exc:
            result = {"ok": False, "error": str(exc)}
        payload = json.dumps(result).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)


def serve(api, ui_root, host, port):
    KitHandler.api = api
    KitHandler.ui_root = Path(ui_root)
    httpd = ThreadingHTTPServer((host, port), KitHandler)
    httpd.serve_forever()

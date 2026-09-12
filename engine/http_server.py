"""Loopback HTTP UI for containers. No secrets on disk."""

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

LOOPBACK = frozenset(("127.0.0.1", "localhost", "::1"))
IDE_ORIGINS = frozenset(("vscode-webview", "vscode-file", "cursor"))
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
    "compare_bytes",
    "verify_pgp",
))
MAX_BODY = 32 * 1024 * 1024


class KitHandler(BaseHTTPRequestHandler):
    api = None
    ui_root = None
    bind_loopback = True

    def log_message(self, fmt, *args):
        return

    def _host_ok(self):
        host = (self.headers.get("Host") or "").split(":")[0].strip().lower()
        if host.startswith("[") and host.endswith("]"):
            host = host[1:-1]
        return host in LOOPBACK or host == ""

    def _peer_ok(self):
        if not self.bind_loopback:
            return True
        peer = (self.client_address[0] or "").strip().lower()
        if peer.startswith("::ffff:"):
            peer = peer[7:]
        return peer in LOOPBACK

    def _parsed_origin(self):
        origin = (self.headers.get("Origin") or "").strip()
        if not origin:
            return "", None
        return origin, urlparse(origin)

    def _origin_ok(self):
        origin, parsed = self._parsed_origin()
        if not origin:
            return True
        host = (parsed.hostname or "").strip().lower()
        if host in LOOPBACK:
            return True
        if not self.bind_loopback:
            return False
        if origin.lower() == "null":
            return True
        return parsed.scheme in IDE_ORIGINS

    def _cors_origin(self):
        origin, parsed = self._parsed_origin()
        if not origin or not self._origin_ok():
            return None
        host = (parsed.hostname or "").strip().lower()
        if host in LOOPBACK or origin.lower() == "null" or parsed.scheme in IDE_ORIGINS:
            return origin
        return None

    def _add_cors(self):
        allow = self._cors_origin()
        if not allow:
            return
        self.send_header("Access-Control-Allow-Origin", allow)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Vary", "Origin")

    def _access_ok(self):
        return self._host_ok() and self._peer_ok() and self._origin_ok()

    def do_OPTIONS(self):
        if not self._access_ok():
            self.send_error(403, "loopback only")
            return
        self.send_response(204)
        self._add_cors()
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_GET(self):
        if not self._access_ok():
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
        self._add_cors()
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if not self._access_ok():
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
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except (TypeError, ValueError):
            self.send_error(400, "bad content-length")
            return
        if length < 0:
            self.send_error(400, "bad content-length")
            return
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
        except Exception:
            result = {"ok": False, "error": "request failed"}
        payload = json.dumps(result).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self._add_cors()
        self.end_headers()
        self.wfile.write(payload)


def serve(api, ui_root, host, port):
    KitHandler.api = api
    KitHandler.ui_root = Path(ui_root)
    KitHandler.bind_loopback = host in LOOPBACK
    httpd = ThreadingHTTPServer((host, port), KitHandler)
    httpd.serve_forever()

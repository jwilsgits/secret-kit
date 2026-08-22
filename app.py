#!/usr/bin/env python3
"""Secret Kit. Native window or loopback HTTP. Secrets stay in memory."""

import argparse
import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.bip39 import validate_mnemonic
from engine.charset import CharsetError
from engine.derive import derive as engine_derive
from engine.entropy import EntropyError, EntropyPool, require_urandom
from engine.generate import generate as engine_generate
from engine.hashcheck import compare_files, hash_tree, verify_blob, verify_file
from engine.http_server import LOOPBACK, serve as serve_http


class Api(object):
    def __init__(self):
        self.pool = EntropyPool()

    def generate(self, spec):
        return engine_generate(spec, self.pool)

    def absorb_mouse(self, samples):
        n = self.pool.absorb_mouse(samples)
        return {"bytes_collected": n}

    def clear_user_entropy(self):
        self.pool.clear()
        return {"ok": True}

    def check_mnemonic(self, phrase):
        text = " ".join((phrase or "").split())
        return {
            "ok": True,
            "valid": bool(text) and validate_mnemonic(text),
            "words": len(text.split()) if text else 0,
        }

    def hash_file(self, spec):
        spec = spec or {}
        try:
            return verify_file(spec.get("path"), spec.get("expected"), spec.get("algo"))
        except (CharsetError, OSError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}

    def hash_bytes(self, spec):
        spec = spec or {}
        try:
            data = base64.b64decode(spec.get("content") or b"")
            return verify_blob(data, spec.get("expected"), spec.get("algo"))
        except (CharsetError, OSError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}

    def _dialog(self, folder=False):
        try:
            import webview
        except ImportError:
            return {"ok": False, "path": None, "error": "webview unavailable"}
        if not webview.windows:
            return {"ok": False, "path": None, "error": "no window"}
        dialog = getattr(webview, "FileDialog", None)
        if folder:
            mode = dialog.FOLDER if dialog is not None else getattr(webview, "FOLDER_DIALOG", None)
        else:
            mode = dialog.OPEN if dialog is not None else getattr(webview, "OPEN_DIALOG", None)
        result = webview.windows[0].create_file_dialog(mode)
        if not result:
            return {"ok": True, "path": None}
        path = result[0] if isinstance(result, (list, tuple)) else result
        return {"ok": True, "path": path}

    def pick_file(self):
        return self._dialog(False)

    def pick_folder(self):
        return self._dialog(True)

    def compare_files(self, spec):
        spec = spec or {}
        try:
            return compare_files(
                spec.get("path_a"), spec.get("path_b"), spec.get("algo") or "sha256"
            )
        except (CharsetError, OSError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}

    def hash_folder(self, spec):
        spec = spec or {}
        try:
            return hash_tree(spec.get("path"), spec.get("algo") or "sha256")
        except (CharsetError, OSError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}

    def derive(self, spec):
        return engine_derive(spec, self.pool)


def _parse_http(value):
    if ":" not in value:
        raise ValueError("use --http HOST:PORT")
    host, port_s = value.rsplit(":", 1)
    return host, int(port_s)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Secret Kit")
    parser.add_argument("--http", metavar="HOST:PORT", help="serve UI on loopback HTTP")
    parser.add_argument(
        "--i-understand-lan",
        action="store_true",
        help="allow a non-loopback bind (used inside Docker; map to 127.0.0.1 on the host)",
    )
    args = parser.parse_args(argv)

    try:
        require_urandom()
    except EntropyError as exc:
        sys.stderr.write("Cannot start: %s\n" % exc)
        return 1

    ui = (ROOT / "ui").resolve()
    if not (ui / "index.html").is_file():
        sys.stderr.write("UI file missing: %s\n" % (ui / "index.html"))
        return 1

    api = Api()
    if args.http:
        try:
            host, port = _parse_http(args.http)
        except ValueError as exc:
            sys.stderr.write("%s\n" % exc)
            return 2
        if host not in LOOPBACK and not args.i_understand_lan:
            sys.stderr.write(
                "Refusing to bind %s. Use 127.0.0.1, or pass --i-understand-lan "
                "only when the host publishes 127.0.0.1 (Docker/OrbStack).\n" % host
            )
            return 2
        sys.stderr.write("Secret Kit http://%s:%s\n" % (host, port))
        serve_http(api, ui, host, port)
        return 0

    try:
        import webview
    except ImportError:
        sys.stderr.write(
            "Missing pywebview. For a browser UI:\n"
            "  python3 app.py --http 127.0.0.1:8765\n"
            "For a native window: python3 -m pip install -r requirements-desktop.txt\n"
        )
        return 1

    webview.create_window(
        "Secret Kit",
        (ui / "index.html").as_uri(),
        js_api=api,
        width=800,
        height=820,
        min_size=(680, 600),
        text_select=True,
    )
    webview.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())

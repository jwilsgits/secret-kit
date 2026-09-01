# Secret Kit

Local air-gap secret generator. Python owns all randomness. On macOS it is a small native window; in Docker/OrbStack/LXC it is a loopback web UI. Nothing is saved to disk. Nothing is sent anywhere.

Four tabs:

- **Passwords** — PIN, random password, memorable BIP-39-word password, Diceware phrase
- **Keys** — BIP-39 12/24, hex key, UUID v4, backup-code list. Reveal / copy / print, or **Send to Derive** (moves a seed, then clears this tab). BIP-39 passphrases are entered on Derive only.
- **Verify** — vendor file checksum (autodetect), compare two files, hash a folder, BIP-39 phrase check
- **Derive** — Bitcoin BIP-84 address lists (optional BIP-86 taproot); Nostr fresh pair or NIP-06. Public first; private behind Reveal. Copy-per-field. **Clear words only** does not wipe the public result.

Nothing is saved. Leaving a tab or clicking Clear wipes that tab. After Derive, the mnemonic field is emptied. There is no in-app vault.

## Run on macOS

```bash
python3 -m pip install --user -r requirements-desktop.txt
python3 app.py
```

Or double-click `Start Secret Kit.command`.

Browser (no pywebview):

```bash
python3 -m pip install --user -r requirements-engine.txt
python3 app.py --http 127.0.0.1:8765
```

Docker, OrbStack, Podman, LXC, and pocket builds: see **[PACKAGING.md](PACKAGING.md)**. After a feature change, rebuild everything this host can with `bash scripts/build-all.sh` and hand off `dist/secret-kit-<VERSION>-*`.

Requires Python 3.9+. This PoC is pinned to `pywebview==5.3.2` and `pyobjc==11.1` because newer pyobjc 12.x does not build on Apple’s Command Line Tools Python 3.9.

## Offline copy (macOS → another Mac)

1. On a networked Mac: double-click `Prepare Offline Wheels.command`.
2. Copy the whole folder (including `vendor/`) to the offline Mac.
3. Double-click `Start Secret Kit.command`. It builds a local `.venv` from `vendor/` and does not call PyPI.

Do not put this project on GitHub or any network share that you do not control.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Security notes

- Entropy is `os.urandom`. Optional mouse / dice / card input is mixed in with HKDF-SHA256 and cannot replace the OS CSPRNG.
- Secrets live in memory for the session. Closing the window forgets them.
- The clipboard copy is cleared after 60 seconds.
- Wallet passphrases are not stored and are not printed.
- Bitcoin derivation is BIP-84 (`m/84'/0'/0'`) with a receive/change list. Optional BIP-86 taproot (`bc1p…`). Nostr from a seed is NIP-06 only. Private material is not copied unless you reveal it and copy it yourself.
- File hashes are computed locally. MD5 and SHA-1 are labeled legacy match only.
- secp256k1 uses the `ecdsa` package (pure Python).

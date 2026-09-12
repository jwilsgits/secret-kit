# Secret Kit — SSH Ed25519 and age keys on Keys

**Date:** 2026-09-11  
**Status:** written for review; implement after the seed write-down check ships  
**Depends on:** [2026-09-11-seed-write-down-check-design.md](2026-09-11-seed-write-down-check-design.md) (Keys result layout). This feature must not weaken that gate for BIP-39.  
**Constraints:** no vault, nothing saved, loopback-only, `os.urandom` remains the CSPRNG, clipboard still clears after 60s. After ship: `bash scripts/build-all.sh`. AppImage site-packages stay small: **do not add `cryptography` or PyNaCl**.

## Goal

Add two generate types on the Keys tab, next to hex / UUID / backup codes:

1. **SSH Ed25519** — OpenSSH public line immediately; private key behind Reveal.
2. **age** — X25519 recipient (`age1…`) immediately; identity (`AGE-SECRET-KEY-1…`) behind Reveal.

Same job as the rest of Keys: make a secret once on an air-gapped machine, copy or print what you need, wipe. No Send to Derive.

## Non-goals (this pass)

- RSA, DSA, ECDSA-on-NIST, or `ssh-rsa`.
- Passphrase-encrypted OpenSSH keys (`aes256-ctr` + bcrypt KDF).
- WireGuard configs (later).
- SSH certificates, authorized_keys management, or writing `~/.ssh/`.
- age file encrypt/decrypt in the UI (generate identity + recipient only).
- BIP-85 application 32 (hex) or any “derive SSH from a seed” path.
- Seed write-down quiz on SSH/age (those are not BIP-39).
- Embedding CPython, Windows `.exe`, or Apple notarization.

---

## 1. Keys dropdown

In [ui/index.html](ui/index.html) `#key-type`, after backup codes:

```html
<option value="ssh">SSH Ed25519</option>
<option value="age">age identity</option>
```

No extra option cards (no comment field, no cipher menu). Hint under the dropdown when `ssh` or `age` is selected, in the existing opts area:

- SSH: `OpenSSH Ed25519. Public line is safe to paste into authorized_keys. Private stays behind Reveal.`
- age: `X25519 recipient you can publish. The AGE-SECRET-KEY stays behind Reveal. This does not encrypt a file.`

Entropy pad (`#entropy-keys`) stays; mix-in still cannot replace `os.urandom`.

`SK.switchKeyType` shows no pin-style option card for these types (like UUID today).

---

## 2. Public first, private behind Reveal

Reuse the Keys result chrome, not a new tab.

After generate:

| Region | SSH | age |
| --- | --- | --- |
| Always visible | `ssh-ed25519 AAAA… secret-kit` | `age1…` (lowercase) |
| Behind Reveal | OpenSSH private key PEM block (`-----BEGIN OPENSSH PRIVATE KEY-----` …) | `AGE-SECRET-KEY-1…` (uppercase) |

`#seed-gate` copy when `lastKind` is `ssh` or `age`: `Private material is hidden. It is as sensitive as a wallet seed.` Button label stays **Reveal** (or **Reveal private** — pick **Reveal private** for these two so BIP-39 can keep **Reveal words**).

Numbered `<ol>` stays hidden. Public text goes in `#keys-result-text` (or a dedicated `#keys-public-text` if the private PEM would overwrite it — prefer a second `<pre id="keys-private-text">` inside `#seed-body`, shown only after reveal).

**Send to Derive** stays hidden (`#seed-send-wrap`).

**Write-down check** (`#seed-wrote` / `#seed-confirm`) stays hidden. SSH/age do not use `SK.keys.confirmed`.

Copy / Print:

- **Copy** before reveal: copies **public** only.
- **Copy** after reveal: still copies **public** only (novice default). Add a second button **Copy private** next to Hide, visible only after reveal, that copies the private block and starts the 60s clipboard clear.
- **Print**: public sheet only (same rule as Derive’s print public). After reveal, Print still does not include private. Private is copy-only, like Derive nsec.

Hide after reveal toggles the private `<pre>` only; public stays visible.

Clear / leave tab: existing `wipeKeys`.

---

## 3. Engine

### 3.1 Ed25519 / X25519 (`engine/ed25519.py`)

Pure Python. SHA-512 via `hashlib`. No extra pip package.

Implement:

- RFC 8032 secret-from-32-bytes, public point, optional sign (needed only if OpenSSH encoding requires the 64-byte `seed || public` form — it does; signing other messages is not a UI feature).
- RFC 7748 X25519: clamp 32-byte scalar, base-point multiply → 32-byte u-coordinate.

Tests must pin **RFC vectors**, not a live `ssh-keygen` on the build host:

- RFC 8032 TEST 1: secret `9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703b632675ced7c5` → public `d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a`.
- RFC 7748 §6.1 Alice: scalar `77076d0e731627a626c1178fd4141aac77bb56c8e98827f3929e3376db28903b` → `X25519(a, 9)` = `8520f0098930a754748b7ddcb43ef75a0dbf3a0d26381af4eba4a98eaa9b4e6a`.

Invalid / all-zero handling: if a draw is unusable, retry from `ByteSource` up to 8 times (same pattern as [engine/nostr.py](engine/nostr.py) `nostr_fresh`). Surface `CharsetError` if still unusable.

### 3.2 SSH (`engine/ssh.py`)

`generate_ssh_ed25519(source) -> {public, private, type, comment}`

- 32-byte seed from `source.need(32)`.
- Public OpenSSH line: `ssh-ed25519 <base64(wire)> secret-kit`
  - wire = `string "ssh-ed25519" || string pubkey_32`
- Private: unencrypted `openssh-key-v1` (`ciphername` `none`, `kdfname` `none`, one key, comment `secret-kit`).
- Comment is always `secret-kit` (not the OS username, not a hostname).

Round-trip test: parse our private blob enough to recover the 32-byte public key and check it matches the public line. Do not shell out to `ssh-keygen`.

### 3.3 age (`engine/age.py`)

`generate_age_x25519(source) -> {recipient, identity, type}`

- 32-byte scalar from `source.need(32)`, X25519 public = scalar · base.
- Recipient: Bech32 HRP `age`, payload = 32-byte public, **lowercase** (`age1…`). Reuse [engine/bech32.py](engine/bech32.py) `encode_data`.
- Identity: Bech32 HRP `age-secret-key-`, payload = 32-byte scalar, then **uppercase** the whole string (`AGE-SECRET-KEY-1…`). `encode_data` lowercases the HRP internally; uppercasing the result is required for age’s display convention.

Test: generate → decode identity HRP/payload → X25519 → encode recipient; must match the returned recipient. Include one fixed scalar vector.

### 3.4 Generate dispatch

In [engine/generate.py](engine/generate.py):

```python
HANDLERS["ssh"] = _ssh
HANDLERS["age"] = _age
```

JSON `value` is an object, not a string (Keys JS already special-cases `codes` as a list):

```json
{
  "ok": true,
  "value": {
    "public": "ssh-ed25519 AAAA… secret-kit",
    "private": "-----BEGIN OPENSSH PRIVATE KEY-----\n…"
  },
  "meta": { "type": "ssh" }
}
```

```json
{
  "ok": true,
  "value": {
    "public": "age1…",
    "private": "AGE-SECRET-KEY-1…"
  },
  "meta": { "type": "age" }
}
```

HTTP `/api/generate` already returns `value` opaque; no server change beyond the handlers. Add `tests/test_http.py` generate cases for `type=ssh` and `type=age` (200, public present, private present).

---

## 4. Help copy (locked)

**`keys.generate.ssh`**  
What: Makes an OpenSSH Ed25519 keypair. The public line is what a server’s `authorized_keys` wants.  
Why: Generate it offline, then copy only the public line to the machine that should let you in. The private block can sign in as you.

**`keys.generate.age`**  
What: Makes an age X25519 identity. The `age1…` line is the recipient others encrypt to.  
Why: You can publish the recipient. Anyone with the `AGE-SECRET-KEY` can decrypt. This screen does not encrypt a file.

**`keys.reveal`** — keep BIP-39 wording. Add **`keys.reveal.private`** for ssh/age:  
What: Shows the private key on screen.  
Why: Anyone who sees it can use the SSH key or decrypt age files. Hide it when you are done looking.

Bind `#key-type` help through existing `data-help-from="#key-type"` (`keys.generate.ssh` / `keys.generate.age`).

---

## 5. Files (expected)

| File | Role |
| --- | --- |
| `engine/ed25519.py` | RFC 8032 + RFC 7748 |
| `engine/ssh.py` | OpenSSH public line + unencrypted private |
| `engine/age.py` | recipient + identity |
| `engine/generate.py` | `ssh` / `age` handlers |
| `tests/test_ed25519.py` | RFC vectors |
| `tests/test_ssh.py` | format + public/private consistency |
| `tests/test_age.py` | bech32 round-trip + vector |
| `tests/test_http.py` | generate ssh/age |
| `ui/index.html` | options, private `<pre>`, Copy private |
| `ui/js/keys.js` | types, public/private split, no quiz |
| `ui/js/help.js` | copy above |
| `README.md` | Keys line adds SSH Ed25519 and age |

`requirements-engine.txt` stays `ecdsa==0.19.2` only. Docker already `COPY engine/` and `COPY ui/`.

---

## 6. Acceptance

- Keys → SSH Ed25519 → Generate: public `ssh-ed25519` line visible; no private PEM on screen; Copy copies the public line; Print is public only.
- Reveal private: PEM visible; Copy private copies PEM; 60s clipboard clear still runs.
- Keys → age → Generate: `age1` visible, `AGE-SECRET-KEY` hidden until Reveal private.
- BIP-39 still requires the write-down check before Copy / Print / Send. SSH/age never show that quiz.
- Send to Derive is not shown for ssh/age.
- `python3 -m unittest discover -s tests` includes RFC 8032 and RFC 7748 vectors.
- AppImage / Docker rebuild: site-packages still no `cryptography` / PyNaCl.
- After merge: `bash scripts/build-all.sh`.

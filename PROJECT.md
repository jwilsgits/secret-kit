# Secret Kit

Local air-gap kit for passwords, crypto identity, and general cryptography. Make or check a secret **once**, on a machine that need not be on a network, then forget it.

Not a wallet. Not a password manager. Not GnuPG-on-disk. There is no vault.

## What it is

Three pillars:

1. **Passwords** — human secrets for logins and disposable signup personas.
2. **Crypto identity** — seeds, Bitcoin/Nostr (and later other) addresses, SSH/age/OpenPGP/WireGuard identities.
3. **General cryptography** — checksums, signatures, session encrypt/decrypt, paper-split backups.

Session-only ops are in scope: encrypt, decrypt, sign, split, mint extra identity types. Outputs you copy, print, or save are yours. Leaving a tab wipes RAM.

How to run: [README.md](README.md).

## What it is today

Version **0.1.0-dev**. Python owns all secrets. Four tabs:

- **Passwords** — PIN, random password, memorable, Diceware, random persona (no email).
- **Keys** — BIP-39 12/24 with write-down check before Copy / Print / Send; hex, UUID v4, backup codes; SSH Ed25519 and age identity (public first, private behind Reveal). Send seed to Derive.
- **Verify** — vendor checksum, in-app OpenPGP detached verify (user-supplied key), compare files, hash folder, BIP-39 checksum.
- **Derive** — Bitcoin BIP-84 + optional BIP-86 + BIP-380 descriptors, BIP-85 English child mnemonics, Nostr fresh or NIP-06. Public first; private behind Reveal.

The live UI is already generate → derive → verify → wipe. The README still reads like a generator because that is how the loop started.

The real product risk is not “missing another coin.” It is generating a seed or key with **no vault** and walking away with a bad paper copy.

Honest gaps:

- OpenPGP **verify** shipped; generate, sign, and encrypt did not.
- Age **identity** shipped; age **file encrypt** did not.
- No Protect tab yet (encrypt / sign / decrypt still unbuilt).

## Constraints that do not move

- No vault. Nothing saved by the app.
- Loopback-only. Nothing is sent anywhere.
- Entropy is `os.urandom`. Optional mouse / dice / card mix-in cannot replace the OS CSPRNG.
- Clipboard copy clears after 60 seconds.
- Pocket engine stays stdlib + small pure-Python (as `engine/openpgp.py` does). No `cryptography`, PyNaCl, or OpenSSL unless a later spec explicitly accepts that cost.

Packaging leftovers (Windows `.exe`, Apple notarization, embed CPython) are distribution, not this roadmap.

## Tab rule

Keep four tabs until the first encrypt / sign / decrypt ships, then add **Protect**.

- **Verify** stays read-only: check a file or phrase.
- **Keys** stays mint identity.
- **Protect** is do something to bytes this session: encrypt, decrypt, sign, split.

Do not dump those onto Verify.

## Roadmap

Each Now / Next item still gets its own spec before build.

### Now

Shipped Keys work (write-down check, SSH, age) lives in those specs. Next build slices:

- Persona per-field copy (today the persona result is one blob).
- Spec then ship **age encrypt / decrypt a file** on Protect: recipient you paste or just generated; ciphertext you choose to save; plaintext never kept. This is the first Protect tab.

### Next

Session ops and identity the pillars already imply.

- **OpenPGP generate + detached sign** (verify already exists). User supplies or mints a key this session; no keyring, no keyservers, no bundled vendor keys.
- **TOTP secret** on Passwords or Keys: `otpauth://` string + printable URI; no authenticator vault.
- **QR encode** for addresses, npubs, age recipients, otpauth (air-gap move to a phone). Decode later if useful; generate first.
- **WireGuard** keypair (same public-first pattern as SSH/age).

### Later

Same product, more formats.

- BIP-85 apps parked on purpose: WIF, hex, xprv, passwords.
- Ethereum / BIP-44 coin `60'` receive list (second chain identity, not a full dapp wallet).
- SLIP-39 / Shamir split of a seed or arbitrary secret this session; shares are paper; app forgets.
- Encoding toolbox: hex / base64 / bech32 / base58check (no new entropy, fewer footguns when moving keys).
- minisign / signify (simple Ed25519 signatures; thinner than OpenPGP).
- PSBT inspect, then maybe sign: air-gap Bitcoin tooling, only after the seed write-down check exists. High misuse cost; its own spec.

### Parked

Capability, but not this product.

- In-app vault, cloud, accounts, telemetry, keyservers, WKD.
- Persona email / SSN-shaped IDs / extra countries.
- Full GnuPG, web of trust, SSH CA, writing `~/.ssh/` or `~/.age/`.
- Hardware-wallet protocols (HWI), Lightning node, Monero (different crypto; blows the `ecdsa`-only engine).
- Steganography. Password-strength scoring as a product.

## How we decide a new item

A capability belongs here if all of these hold:

- It works air-gapped (no network lookup, no keyserver, no cloud).
- RAM is wiped when you leave the tab; the app is not a store.
- Identity is public-first; private stays behind Reveal.
- Verify and decrypt use keys the user supplies this session, never a bundled vendor key.
- It does not need a new heavy crypto dependency unless a spec accepts that cost.

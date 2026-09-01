# Secret Kit — BIP-85, descriptors, and novice help

**Date:** 2026-08-31  
**Status:** approved in conversation; implement after this spec is reviewed  
**Constraints:** no vault, nothing saved, loopback-only, `os.urandom` remains the CSPRNG, clipboard still clears after 60s. After ship: `bash scripts/build-all.sh`.

## Goal

1. Teach a novice **what the current control does** and **why it matters**, with a `?` that updates when the selected option changes.
2. Add **BIP-85** child BIP-39 mnemonics (English 12 or 24) on Derive.
3. Add **BIP-380 descriptor** lines on the existing Bitcoin public result (native segwit; taproot when that checkbox is on).

## Non-goals (this pass)

- BIP-85 applications other than English BIP-39 mnemonics (WIF, hex, xprv, passwords, dice).
- Languages other than English (`language' = 0'`).
- 18-word BIP-85 (Keys already only offer 12/24).
- In-app vault, cloud, accounts, telemetry.
- Changing entropy policy (mouse/dice still cannot replace `os.urandom`).
- Embedding CPython in the macOS `.app`.
- Windows `.exe` or Apple notarization.

---

## 1. Help control

### Behavior

- A `?` control sits **next to the choice that changes meaning** (dropdown, segment group, or checkbox), not next to Generate / Copy / Clear.
- **Hover** (pointer devices): show the popover.
- **Click / tap:** toggle the same popover (required for the AppImage browser and pywebview).
- **Escape** or click outside: hide.
- **When the bound option changes** (select `change`, segment click, checkbox): the open popover **rewrites in place** to the new key. It does not stay on stale copy.
- Help text is not a secret: not printed, not copied with results, not sent to the clipboard helper.
- First sentence is plain language. BIP/NIP numbers may appear in a last line for the curious.
- Two beats in every body: **What it does.** **Why it matters.**

### Implementation shape

- New `ui/js/help.js` loaded before tab scripts. Copy lives in `SK.HELP` (plain object keyed by string).
- Markup: `<button type="button" class="help-q" data-help="passwords.generate" aria-label="What is this"></button>` with optional `data-help-from="#type"` meaning: resolve key as `passwords.generate.` + select value.
- One shared popover element (`#help-pop`) positioned near the active `?`.
- CSS in `ui/app.css`: small circular `?`, popover max-width ~20rem, readable on the cream theme. Must work in the native window and in loopback HTTP.
- Keyboard: `?` is a real button (tab stop). Do not use `title=` as the only help.

### Keys that rebind from a menu

| `data-help-from` | Key prefix | Values |
| --- | --- | --- |
| `#type` | `passwords.generate.` | `pin`, `password`, `memorable`, `diceware` |
| `#key-type` | `keys.generate.` | `seed`, `hex`, `uuid`, `codes` |
| `#derive-kind` | `derive.kind.` | `btc`, `bip85`, `nostr` |
| `#nostr-mode` | `derive.nostr.` | `mnemonic`, `fresh`, `inspect` |
| `#hash-algo` | `verify.algo.` | `auto`, `sha256`, `sha512`, `sha1`, `md5` |

Segment groups (PIN charset, 12/24 words, receive count, BIP-85 12/24, BIP-85 index) use a `data-help` on the fieldset `?` whose getter reads the current segment value.

---

## 2. Help copy (locked)

Keep wording close to this. Do not add “store this in a password manager in the cloud.” Paper/offline is allowed; digital vaults are not a product feature.

### Header

**`app.offline`**  
What: This program does not keep an account or a file of your secrets. Close the window or tab and they are gone.  
Why: So a stolen laptop copy of Secret Kit is not a stolen wallet.

### Passwords — Generate (`passwords.generate.*`)

**`pin`**  
What: Makes a short code from digits and/or letters, like a device PIN.  
Why: PINs are for locks and devices, not as your only login password on the internet.

**`password`**  
What: Makes a random string of letters and numbers (symbols if you ask).  
Why: A long mixed password is hard to guess. Use a different one per site.

**`memorable`**  
What: Makes BIP-39 English words plus two digits per group (example shape: `catalog01-planet04-student77`).  
Why: Easier to type than a random password. It is still a password, not a Bitcoin wallet.

**`diceware`**  
What: Makes several real BIP-39 English words separated by spaces.  
Why: Easier to write down than a random password. Longer lists are stronger.

**`passwords.lookalikes`**  
What: Skips characters that look alike (0/O, 1/l/I).  
Why: Fewer mistakes when you copy by hand. Slightly fewer possible codes.

**`passwords.preset`**  
What: Simple / Strong / Paranoid set length and character classes for you. Advanced lets you override.  
Why: Defaults that are “good enough” without needing to know entropy math.

**`entropy.extra`**  
What: Optional mouse timing, dice, or a card shuffle mixed into the next generate.  
Why: The operating system random generator is already enough. Extra input cannot replace it; it only mixes in.

### Keys — Generate (`keys.generate.*`)

**`seed`**  
What: Makes a new BIP-39 wallet seed (12 or 24 English words).  
Why: Those words can spend coins. Treat them like cash. A passphrase, if you use one, is typed later on Derive, not here.

**`hex`**  
What: Makes raw random bytes shown in hexadecimal.  
Why: Some tools want hex, not words. This is not a Bitcoin address.

**`uuid`**  
What: Makes a UUID v4, a random identifier.  
Why: Unique IDs are not wallet keys. Safe to paste into software that asks for a UUID.

**`codes`**  
What: Makes a list of look-alike-free backup codes.  
Why: For sites that say “save these recovery codes.” Each line is one code.

**`keys.words`**  
What: 12 words is the usual wallet backup. 24 words is a longer backup of the same kind.  
Why: Both are BIP-39. 24 words is more entropy; 12 is easier to write. Either can spend funds.

**`keys.reveal`**  
What: Shows the seed words on screen.  
Why: Anyone who sees them can spend. Hide them when you are done looking.

**`keys.send`**  
What: Moves this seed into Derive for this session, then clears Keys.  
Why: So you do not leave the same words sitting on two tabs.

### Verify

**`verify.checksum`**  
What: Hashes a file on this machine and compares it to the vendor’s hex digest.  
Why: You can check a download without sending the file anywhere.

**`verify.algo.sha256` / `sha512`**  
What: Modern checksums. SHA-256 is 64 hex characters; SHA-512 is 128.  
Why: This is what most vendors publish today.

**`verify.algo.sha1` / `md5`**  
What: Old checksums. Secret Kit will match them but labels them legacy.  
Why: A match only proves the file equals that old hash. It is not a modern integrity bar.

**`verify.compare`**  
What: Hashes two files the same way and says if the bytes match.  
Why: Confirm a copy without opening either file.

**`verify.folder`**  
What: SHA-256 of every non-hidden file in a folder.  
Why: An inventory of what is on disk. It is not the “paste vendor hash” flow.

**`verify.bip39`**  
What: Checks that 12 or 24 English words have a valid BIP-39 checksum.  
Why: Catches typos. A valid checksum does **not** mean the wallet is safe or that you own those funds.

### Derive — kind (`derive.kind.*`)

**`btc`**  
What: Turns a BIP-39 seed into Bitcoin receive (and optional change) addresses: native segwit `bc1q…` (BIP-84).  
Why: Those addresses are what you give people to pay you. The seed stays as sensitive as before.

**`bip85`**  
What: From one **master** seed, makes a **child** 12- or 24-word seed for another wallet. Same master, same index, same child, always.  
Why: One backup can create many wallets. The master can recreate every child — do not use the master as a daily-driver wallet.

**`nostr`**  
What: Nostr keys. See the Nostr-source help for which method.  
Why: Nostr identity is a secret key. Treat `nsec` like a seed.

**`derive.nostr.mnemonic`**  
What: Derives the NIP-06 key at `m/44'/1237'/0'/0/0` from the words (and optional passphrase).  
Why: Recoverable Nostr identity from the same kind of backup as a Bitcoin wallet.

**`derive.nostr.fresh`**  
What: New 32-byte secret from the OS random generator. Not tied to a mnemonic.  
Why: A one-shot identity. If you lose it, it is gone. Extra entropy still cannot replace the OS generator.

**`derive.nostr.inspect`**  
What: Shows the `npub` for an `nsec`. Cannot produce seed words.  
Why: Check that a key matches a public identity without pretending you can reverse a seed.

**`derive.taproot`**  
What: Also lists BIP-86 taproot addresses (`bc1p…`) from the same seed.  
Why: Some wallets prefer taproot. Same seed, different address format.

**`derive.receive` / `derive.change`**  
What: How many receive or change addresses to list.  
Why: More rows to write down or check. This does not create a new seed.

**`derive.passphrase`**  
What: Optional BIP-39 passphrase (sometimes called a 25th word). Empty and “password” are different wallets.  
Why: A passphrase you forget loses the coins that used it. Secret Kit does not store it.

**`derive.descriptor`**  
What: A BIP-380 string that describes the address formula (xpub + path + script type).  
Why: Another wallet can **watch** the same receive chain without the mnemonic. It is not the seed. Do not paste the descriptor into a hot website.

**`derive.bip85.words`**  
What: Length of the **child** mnemonic (12 or 24).  
Why: Same meaning as on Keys. The master seed length is independent.

**`derive.bip85.index`**  
What: Which child (0, 1, 2, …).  
Why: Index 0 is the first child wallet, 1 is the next, and so on. Write down the index with the child words.

---

## 3. BIP-85 (Derive)

### UI

- Derive kind segments become **three**: `Bitcoin · BIP-84` | `BIP-85` | `Nostr` (same segment control as today, one more button).
- When BIP-85 is selected: hide BTC receive/change/taproot; hide Nostr modes. Show master mnemonic + optional passphrase (same widgets as BTC). Show:
  - Child length: 12 / 24 (default 12).
  - Index: integer field, default `0`, allowed **0–999**. Out of range → error, no derive.
- Primary button still says **Derive**.
- Result: **public first** — path (`m/83696968'/39'/0'/{12|24}'/{index}'`), index, child word count, short warning that the master can recreate this child. **Child words behind Reveal private** (same gate as zprv / nsec). Copy-per-field. Print public sheet does **not** include child words.
- Wiping: same as other Derive — leaving the tab or Clear wipes. **Clear words only** does not wipe the public path/index result (same rule as today’s BTC public list).

### Engine

- New `engine/bip85.py` + `derive` kind `bip85`.
- Master: BIP-39 English mnemonic → seed (passphrase as today) → BIP32 root.
- Path: `m/83696968'/39'/0'/{12|24}'/{index}'` (all hardened).
- `k` = derived private key bytes (32). Entropy = `HMAC-SHA512(key=b"bip-entropy-from-k", msg=k)` then truncate to 16 bytes (12 words) or 32 bytes (24 words). Feed that entropy into existing BIP-39 encode (same wordlist as Keys).
- Do not implement other app numbers.
- Invalid curve child: surface as a derive error asking the user to try the next index (BIP-32/BIP-85 hard-fail rule).

### Tests

Must match [BIP-85](https://github.com/bitcoin/bips/blob/master/bip-0085.mediawiki) English vectors from master xprv  
`xprv9s21ZrQH143K2LBWUUQRFXhucrQqBpKdRRxNVq2zBqsx8HVqFk2uYo8kmbaLLHRdqtQpUm98uKfu3vca1LqdGhUtyoFnCNkfmXRyPXLjbKb`:

| Path | Child mnemonic |
| --- | --- |
| `m/83696968'/39'/0'/12'/0'` | `girl mad pet galaxy egg matter matrix prison refuse sense ordinary nose` |
| `m/83696968'/39'/0'/24'/0'` | `puppy ocean match cereal symbol another shed magic wrap hammer bulb intact gadget divorce twin tonight reason outdoor destroy simple truth cigar social volcano` |

Tests may parse that xprv in the engine (add `Node.from_extended` if missing) rather than a mnemonic that happens to match. Also test: bad mnemonic error; index -1 and 1000 rejected; 12 vs 24 produce different phrases. HTTP `derive` kind `bip85` may include `mnemonic` in `value` (same as today’s `zprv` on Bitcoin). The **UI** must still put path/index/words/warning in the public list and `mnemonic` only after Reveal.

HTTP JSON shape:

```json
{
  "ok": true,
  "value": {
    "path": "m/83696968'/39'/0'/12'/0'",
    "index": 0,
    "words": 12,
    "language": "english",
    "warning": "The master seed can recreate this child.",
    "mnemonic": "<child words, private>"
  }
}
```

UI places `path`, `index`, `words`, `warning` in the public `dl`; `mnemonic` only after Reveal.

---

## 4. Bitcoin descriptors

On a successful **Bitcoin** derive only (not BIP-85, not Nostr):

Public rows (in addition to today’s addresses / zpub):

- `Receive descriptor` — BIP-380: `wpkh([FPR/84h/0h/0h]XPUB/0/*)`  
- `Change descriptor` — same with `/1/*` if change count > 0.

If taproot is on, also:

- `Taproot receive descriptor` — `tr([FPR/86h/0h/0h]XPUB/0/*)`  
- `Taproot change descriptor` — `/1/*` when change count > 0.

Rules:

- `FPR` is the **master fingerprint**: first 4 bytes of `HASH160(master compressed pubkey)`, lowercase hex.
- `XPUB` is a **standard BIP-32 xpub** (version `0488B21E`) of the **account** node (`m/84'/0'/0'` or `m/86'/0'/0'`). Do **not** put SLIP-132 `zpub` inside the descriptor (Bitcoin Core / Sparrow expect xpub in `wpkh()` / `tr()`). Keep showing `zpub` as today for humans who want it.
- Origin path uses `h` (or `'`) consistently; pick `h` in the string.
- Public only. Account `zprv` / xprv stay behind Reveal, unchanged.
- `?` on the descriptor label uses `derive.descriptor`.
- Unit test: known mnemonic `abandon` ×11 + `about`, empty passphrase, receive=1, change=0 — descriptor starts with `wpkh([` and contains `/84h/0h/0h]`, and the first listed receive address still matches current BIP-84 tests.

---

## 5. Files (expected)

| File | Role |
| --- | --- |
| `ui/js/help.js` | Popover, rebind, `SK.HELP` |
| `ui/app.css` | `?` and popover |
| `ui/index.html` | `?` buttons, BIP-85 controls, third derive kind, `#help-pop` |
| `ui/js/derive.js` | BIP-85 form, public/private split, descriptor rows |
| `ui/js/passwords.js` / `keys.js` / `verify.js` / `boot.js` | Wire help; boot includes `help.js` |
| `engine/bip85.py` | HMAC + path + mnemonic |
| `engine/derive.py` | kind `bip85` |
| `engine/btc.py` / `bip32.py` | xpub + fingerprint + descriptor strings |
| `tests/test_bip85.py` | Official vectors |
| `tests/test_btc.py` | Descriptor strings |
| `tests/test_http.py` | `bip85` API |
| `README.md` | One line: BIP-85 + descriptors + `?` help |

No new persistence. No changes to Docker bind policy.

---

## 6. Acceptance

- Changing Passwords Generate from PIN → Diceware while the `?` popover is open shows Diceware copy without a second click.
- AppImage/HTTP: click `?` opens and closes the popover (hover may no-op; click must work).
- BIP-85 index 0 / 12 words matches the official child mnemonic from the published xprv test.
- Bitcoin derive shows a `wpkh(` receive descriptor; with taproot on, also `tr(`.
- Child BIP-85 words and xprv are not in the public `dl` and not on the public print sheet.
- `python3 -m unittest discover -s tests` stays green.
- After merge: run `bash scripts/build-all.sh` on a machine that can build (not required to pass this spec’s unit tests).

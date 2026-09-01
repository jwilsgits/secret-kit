window.SK = window.SK || {};

SK.HELP = {
  "app.offline": {
    what: "This program does not keep an account or a file of your secrets. Close the window or tab and they are gone.",
    why: "So a stolen laptop copy of Secret Kit is not a stolen wallet.",
  },
  "passwords.generate.pin": {
    what: "Makes a short code from digits and/or letters, like a device PIN.",
    why: "PINs are for locks and devices, not as your only login password on the internet.",
  },
  "passwords.generate.password": {
    what: "Makes a random string of letters and numbers (symbols if you ask).",
    why: "A long mixed password is hard to guess. Use a different one per site.",
  },
  "passwords.generate.memorable": {
    what: "Makes BIP-39 English words plus two digits per group (example shape: catalog01-planet04-student77).",
    why: "Easier to type than a random password. It is still a password, not a Bitcoin wallet.",
  },
  "passwords.generate.diceware": {
    what: "Makes several real BIP-39 English words separated by spaces.",
    why: "Easier to write down than a random password. Longer lists are stronger.",
  },
  "passwords.lookalikes": {
    what: "Skips characters that look alike (0/O, 1/l/I).",
    why: "Fewer mistakes when you copy by hand. Slightly fewer possible codes.",
  },
  "passwords.preset": {
    what: "Simple / Strong / Paranoid set length and character classes for you. Advanced lets you override.",
    why: "Defaults that are “good enough” without needing to know entropy math.",
  },
  "entropy.extra": {
    what: "Optional mouse timing, dice, or a card shuffle mixed into the next generate.",
    why: "The operating system random generator is already enough. Extra input cannot replace it; it only mixes in.",
  },
  "keys.generate.seed": {
    what: "Makes a new BIP-39 wallet seed (12 or 24 English words).",
    why: "Those words can spend coins. Treat them like cash. A passphrase, if you use one, is typed later on Derive, not here.",
  },
  "keys.generate.hex": {
    what: "Makes raw random bytes shown in hexadecimal.",
    why: "Some tools want hex, not words. This is not a Bitcoin address.",
  },
  "keys.generate.uuid": {
    what: "Makes a UUID v4, a random identifier.",
    why: "Unique IDs are not wallet keys. Safe to paste into software that asks for a UUID.",
  },
  "keys.generate.codes": {
    what: "Makes a list of look-alike-free backup codes.",
    why: "For sites that say “save these recovery codes.” Each line is one code.",
  },
  "keys.words": {
    what: "12 words is the usual wallet backup. 24 words is a longer backup of the same kind.",
    why: "Both are BIP-39. 24 words is more entropy; 12 is easier to write. Either can spend funds.",
  },
  "keys.reveal": {
    what: "Shows the seed words on screen.",
    why: "Anyone who sees them can spend. Hide them when you are done looking.",
  },
  "keys.send": {
    what: "Moves this seed into Derive for this session, then clears Keys.",
    why: "So you do not leave the same words sitting on two tabs.",
  },
  "verify.checksum": {
    what: "Hashes a file on this machine and compares it to the vendor’s hex digest.",
    why: "You can check a download without sending the file anywhere.",
  },
  "verify.algo.auto": {
    what: "Detect the algorithm from the hex length.",
    why: "You do not have to know which hash the vendor used.",
  },
  "verify.algo.sha256": {
    what: "Modern checksums. SHA-256 is 64 hex characters; SHA-512 is 128.",
    why: "This is what most vendors publish today.",
  },
  "verify.algo.sha512": {
    what: "Modern checksums. SHA-256 is 64 hex characters; SHA-512 is 128.",
    why: "This is what most vendors publish today.",
  },
  "verify.algo.sha1": {
    what: "Old checksums. Secret Kit will match them but labels them legacy.",
    why: "A match only proves the file equals that old hash. It is not a modern integrity bar.",
  },
  "verify.algo.md5": {
    what: "Old checksums. Secret Kit will match them but labels them legacy.",
    why: "A match only proves the file equals that old hash. It is not a modern integrity bar.",
  },
  "verify.compare": {
    what: "Hashes two files the same way and says if the bytes match.",
    why: "Confirm a copy without opening either file.",
  },
  "verify.folder": {
    what: "SHA-256 of every non-hidden file in a folder.",
    why: "An inventory of what is on disk. It is not the “paste vendor hash” flow.",
  },
  "verify.bip39": {
    what: "Checks that 12 or 24 English words have a valid BIP-39 checksum.",
    why: "Catches typos. A valid checksum does not mean the wallet is safe or that you own those funds.",
  },
  "derive.kind.btc": {
    what: "Turns a BIP-39 seed into Bitcoin receive (and optional change) addresses: native segwit bc1q… (BIP-84).",
    why: "Those addresses are what you give people to pay you. The seed stays as sensitive as before.",
  },
  "derive.kind.bip85": {
    what: "From one master seed, makes a child 12- or 24-word seed for another wallet. Same master, same index, same child, always.",
    why: "One backup can create many wallets. The master can recreate every child — do not use the master as a daily-driver wallet.",
  },
  "derive.kind.nostr": {
    what: "Nostr keys. See the Nostr-source help for which method.",
    why: "Nostr identity is a secret key. Treat nsec like a seed.",
  },
  "derive.nostr.mnemonic": {
    what: "Derives the NIP-06 key at m/44'/1237'/0'/0/0 from the words (and optional passphrase).",
    why: "Recoverable Nostr identity from the same kind of backup as a Bitcoin wallet.",
  },
  "derive.nostr.fresh": {
    what: "New 32-byte secret from the OS random generator. Not tied to a mnemonic.",
    why: "A one-shot identity. If you lose it, it is gone. Extra entropy still cannot replace the OS generator.",
  },
  "derive.nostr.inspect": {
    what: "Shows the npub for an nsec. Cannot produce seed words.",
    why: "Check that a key matches a public identity without pretending you can reverse a seed.",
  },
  "derive.taproot": {
    what: "Also lists BIP-86 taproot addresses (bc1p…) from the same seed.",
    why: "Some wallets prefer taproot. Same seed, different address format.",
  },
  "derive.receive": {
    what: "How many receive or change addresses to list.",
    why: "More rows to write down or check. This does not create a new seed.",
  },
  "derive.change": {
    what: "How many receive or change addresses to list.",
    why: "More rows to write down or check. This does not create a new seed.",
  },
  "derive.passphrase": {
    what: "Optional BIP-39 passphrase (sometimes called a 25th word). Empty and “password” are different wallets.",
    why: "A passphrase you forget loses the coins that used it. Secret Kit does not store it.",
  },
  "derive.descriptor": {
    what: "A BIP-380 string that describes the address formula (xpub + path + script type).",
    why: "Another wallet can watch the same receive chain without the mnemonic. It is not the seed. Do not paste the descriptor into a hot website.",
  },
  "derive.bip85.words": {
    what: "Length of the child mnemonic (12 or 24).",
    why: "Same meaning as on Keys. The master seed length is independent.",
  },
  "derive.bip85.index": {
    what: "Which child (0, 1, 2, …).",
    why: "Index 0 is the first child wallet, 1 is the next, and so on. Write down the index with the child words.",
  },
};

SK.helpKey = function (btn) {
  var base = btn.getAttribute("data-help") || "";
  var from = btn.getAttribute("data-help-from");
  if (from) {
    var el = document.querySelector(from);
    return base + "." + (el ? el.value : "");
  }
  return base;
};

SK.helpFill = function (key) {
  var entry = SK.HELP[key];
  var pop = SK.$("help-pop");
  if (!entry) {
    SK.helpHide();
    return false;
  }
  pop.querySelector(".help-what").textContent = entry.what;
  pop.querySelector(".help-why").textContent = entry.why;
  return true;
};

SK.helpShow = function (btn) {
  var pop = SK.$("help-pop");
  var key = SK.helpKey(btn);
  if (!SK.HELP[key]) {
    SK.helpHide();
    return;
  }
  SK._helpBtn = btn;
  SK.helpFill(key);
  var rect = btn.getBoundingClientRect();
  pop.style.left = rect.left + window.scrollX + "px";
  pop.style.top = rect.bottom + window.scrollY + 6 + "px";
  SK.show(pop, true);
};

SK.helpHide = function () {
  SK.show(SK.$("help-pop"), false);
  SK._helpBtn = null;
};

SK.refreshHelp = function () {
  if (SK._helpBtn) SK.helpShow(SK._helpBtn);
};

SK.initHelp = function () {
  var pop = SK.$("help-pop");
  SK._helpBtn = null;
  SK._helpPinned = false;
  document.addEventListener("click", function (ev) {
    var q = ev.target.closest(".help-q");
    if (q) {
      ev.preventDefault();
      if (SK._helpPinned && SK._helpBtn === q) {
        SK.helpHide();
        SK._helpPinned = false;
      } else {
        SK._helpPinned = true;
        SK.helpShow(q);
      }
      return;
    }
    if (!ev.target.closest("#help-pop")) {
      if (ev.target.closest(".seg button") || ev.target.closest("select")) {
        return;
      }
      SK._helpPinned = false;
      SK.helpHide();
    }
  });
  document.addEventListener("mouseover", function (ev) {
    var q = ev.target.closest(".help-q");
    if (q && !SK._helpPinned) SK.helpShow(q);
  });
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") {
      SK._helpPinned = false;
      SK.helpHide();
    }
  });
  document.querySelectorAll("select[id]").forEach(function (sel) {
    sel.addEventListener("change", SK.refreshHelp);
  });
};

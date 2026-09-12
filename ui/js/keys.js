SK.keys = {
  keyType: "seed",
  seedWords: 12,
  hexBytes: 32,
  codeCount: 8,
  last: "",
  private: "",
  lastKind: "seed",
  revealed: false,
  hidden: false,
  confirmed: false,
  challenge: null,
  confirming: false,
};

SK.isAsymmetricKey = function (kind) {
  return kind === "ssh" || kind === "age";
};

SK.shuffleIndexes = function (n, k) {
  var pool = [];
  var i;
  for (i = 1; i <= n; i++) pool.push(i);
  var buf = new Uint32Array(pool.length);
  crypto.getRandomValues(buf);
  for (i = pool.length - 1; i > 0; i--) {
    var j = buf[i] % (i + 1);
    var tmp = pool[i];
    pool[i] = pool[j];
    pool[j] = tmp;
  }
  return pool.slice(0, k);
};

SK.seedAnswersMatch = function (mnemonic, answers) {
  var words = String(mnemonic || "").split(/\s+/).filter(Boolean);
  if (!answers || !answers.length) return false;
  for (var i = 0; i < answers.length; i++) {
    var index = Number(answers[i].index);
    if (!index || index < 1 || index > words.length) return false;
    var normalized = String(answers[i].word == null ? "" : answers[i].word)
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
    if (!normalized || normalized !== words[index - 1].toLowerCase()) return false;
  }
  return true;
};

SK.setSeedExportEnabled = function (on) {
  ["seed-copy", "seed-print", "seed-send"].forEach(function (id) {
    var el = SK.$(id);
    if (el) el.disabled = !on;
  });
};

SK.clearSeedConfirmUi = function () {
  SK.$("seed-confirm-fields").innerHTML = "";
  SK.show(SK.$("seed-confirm"), false);
  SK.show(SK.$("error-seed-confirm"), false);
  SK.$("error-seed-confirm").textContent = "";
  SK.show(SK.$("seed-wrote"), false);
};

SK.renderSeedConfirmFields = function (indexes) {
  var hold = SK.$("seed-confirm-fields");
  hold.innerHTML = "";
  indexes.forEach(function (idx, i) {
    var label = document.createElement("label");
    label.className = "field";
    var span = document.createElement("span");
    span.textContent = "Word " + idx;
    var input = document.createElement("input");
    input.type = "text";
    input.autocomplete = "off";
    input.spellcheck = false;
    input.setAttribute("data-challenge-index", String(idx));
    label.appendChild(span);
    label.appendChild(input);
    hold.appendChild(label);
    if (i === indexes.length - 1) {
      input.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter") {
          ev.preventDefault();
          SK.$("seed-confirm-run").click();
        }
      });
    }
  });
  var first = hold.querySelector("input");
  if (first) first.focus();
};

SK.syncKeysConfirmUi = function () {
  var isSeed = SK.keys.lastKind === "seed";
  var asym = SK.isAsymmetricKey(SK.keys.lastKind);
  var confirming = isSeed && SK.keys.confirming;
  var needsConfirm = isSeed && SK.keys.revealed && !SK.keys.confirmed && !confirming;
  var canExport = !isSeed || SK.keys.confirmed;

  SK.show(SK.$("seed-wrote"), needsConfirm);
  SK.show(SK.$("seed-confirm"), confirming);
  SK.show(SK.$("seed-actions"), !confirming || !isSeed);
  SK.show(SK.$("seed-hide"), !confirming);
  SK.setSeedExportEnabled(canExport && (isSeed ? SK.keys.revealed : true));

  if (isSeed && SK.keys.revealed && !confirming) {
    SK.show(SK.$("seed-words-list"), !SK.keys.hidden);
  }
  if (confirming) {
    SK.show(SK.$("seed-words-list"), false);
  }

  if (asym) {
    SK.show(SK.$("keys-result-text"), true);
    SK.show(SK.$("keys-private-text"), SK.keys.revealed && !SK.keys.hidden);
    SK.show(SK.$("seed-copy-private"), SK.keys.revealed);
    SK.show(SK.$("seed-wrote"), false);
    SK.show(SK.$("seed-confirm"), false);
  } else {
    SK.show(SK.$("seed-copy-private"), false);
    SK.show(SK.$("keys-private-text"), false);
  }
};

SK.wipeKeys = function () {
  SK.keys.last = "";
  SK.keys.private = "";
  SK.keys.revealed = false;
  SK.keys.hidden = false;
  SK.keys.confirmed = false;
  SK.keys.challenge = null;
  SK.keys.confirming = false;
  SK.$("seed-words-list").innerHTML = "";
  SK.$("keys-result-text").textContent = "";
  SK.$("keys-private-text").textContent = "";
  SK.show(SK.$("result-keys"), false);
  SK.show(SK.$("seed-gate"), true);
  SK.show(SK.$("seed-body"), false);
  SK.show(SK.$("error-keys"), false);
  SK.$("seed-clip").textContent = "";
  SK.clearPrint();
  SK.clearSeedConfirmUi();
  SK.setSeedExportEnabled(false);
  SK.$("seed-hide").textContent = "Hide";
  SK.show(SK.$("seed-actions"), true);
  SK.show(SK.$("seed-hide"), true);
  SK.show(SK.$("seed-copy-private"), false);
  SK.$("seed-gate-copy").textContent =
    "This is a wallet seed. Anyone who sees it can spend the funds.";
  SK.$("seed-reveal").textContent = "Reveal words";
};
SK.wipes.keys = SK.wipeKeys;

SK.switchKeyType = function (type) {
  SK.keys.keyType = type;
  SK.show(SK.$("opts-seed"), type === "seed");
  SK.show(SK.$("opts-hex"), type === "hex");
  SK.show(SK.$("opts-codes"), type === "codes");
  SK.show(SK.$("opts-ssh"), type === "ssh");
  SK.show(SK.$("opts-age"), type === "age");
  if (SK.refreshHelp) SK.refreshHelp();
};

SK.initKeys = function () {
  SK.$("key-type").addEventListener("change", function (ev) {
    SK.switchKeyType(ev.target.value);
  });
  SK.bindSeg("seed-words", "data-words", function (v) {
    SK.keys.seedWords = v;
    SK.setSeg(SK.$("seed-words"), "data-words", v);
  });
  SK.bindSeg("hex-bytes", "data-bytes", function (v) {
    SK.keys.hexBytes = v;
    SK.setSeg(SK.$("hex-bytes"), "data-bytes", v);
  });
  SK.bindSeg("code-count", "data-count", function (v) {
    SK.keys.codeCount = v;
    SK.setSeg(SK.$("code-count"), "data-count", v);
  });
  SK.$("gen-seed").addEventListener("click", function () {
    var extra = SK.activeEntropy();
    var spec = { type: SK.keys.keyType, dice: extra.dice, cards: extra.cards };
    if (SK.keys.keyType === "seed") spec.seed = { words: Number(SK.keys.seedWords) };
    if (SK.keys.keyType === "hex") spec.hex = { bytes: Number(SK.keys.hexBytes) };
    if (SK.keys.keyType === "codes") spec.codes = { count: Number(SK.keys.codeCount) };
    SK.runGenerate(spec, "error-keys").then(function (result) {
      if (!result) return;
      var asym = SK.isAsymmetricKey(SK.keys.keyType);
      var value;
      SK.keys.private = "";
      if (SK.keys.keyType === "codes") {
        value = result.value.join("\n");
      } else if (asym) {
        value = result.value.public;
        SK.keys.private = result.value.private;
      } else {
        value = result.value;
      }
      SK.keys.last = value;
      SK.keys.lastKind = SK.keys.keyType;
      SK.keys.revealed = SK.keys.keyType !== "seed" && !asym;
      SK.keys.hidden = false;
      SK.keys.confirmed = SK.keys.keyType !== "seed";
      SK.keys.challenge = null;
      SK.keys.confirming = false;
      SK.clearSeedConfirmUi();
      SK.$("keys-result-label").textContent = {
        seed: "Wallet seed",
        hex: "Hex key",
        uuid: "UUID v4",
        codes: "Backup codes",
        ssh: "SSH Ed25519",
        age: "age identity",
      }[SK.keys.keyType];
      SK.$("seed-meta").textContent = result.meta.checksum_valid
        ? "checksum valid"
        : result.meta.bytes
          ? result.meta.bytes + " bytes"
          : result.meta.count
            ? result.meta.count + " codes"
            : "";
      SK.fillWords(SK.$("seed-words-list"), SK.keys.keyType === "seed" ? value : "");
      SK.$("keys-result-text").textContent = value;
      SK.$("keys-private-text").textContent = SK.keys.private || "";
      SK.show(SK.$("result-keys"), true);
      if (SK.keys.keyType === "seed") {
        SK.$("seed-gate-copy").textContent =
          "This is a wallet seed. Anyone who sees it can spend the funds.";
        SK.$("seed-reveal").textContent = "Reveal words";
        SK.show(SK.$("seed-gate"), true);
        SK.show(SK.$("seed-body"), false);
        SK.show(SK.$("seed-words-list"), true);
        SK.show(SK.$("keys-result-text"), false);
      } else if (asym) {
        SK.$("seed-gate-copy").textContent =
          "Private material is hidden. It is as sensitive as a wallet seed.";
        SK.$("seed-reveal").textContent = "Reveal private";
        var revealHelp = SK.$("seed-reveal").parentNode.querySelector('[data-help="keys.reveal"],[data-help="keys.reveal.private"]');
        if (revealHelp) revealHelp.setAttribute("data-help", "keys.reveal.private");
        SK.show(SK.$("seed-gate"), true);
        SK.show(SK.$("seed-body"), true);
        SK.show(SK.$("seed-words-list"), false);
        SK.show(SK.$("keys-result-text"), true);
        SK.show(SK.$("keys-private-text"), false);
      } else {
        var revealHelpSeed = SK.$("seed-reveal").parentNode.querySelector('[data-help]');
        if (revealHelpSeed) revealHelpSeed.setAttribute("data-help", "keys.reveal");
        SK.show(SK.$("seed-gate"), false);
        SK.show(SK.$("seed-body"), true);
        SK.show(SK.$("seed-words-list"), false);
        SK.show(SK.$("keys-result-text"), true);
      }
      SK.show(SK.$("seed-send-wrap"), SK.keys.keyType === "seed");
      SK.$("seed-hide").textContent = "Hide";
      SK.syncKeysConfirmUi();
    });
  });
  SK.$("seed-reveal").addEventListener("click", function () {
    SK.keys.revealed = true;
    SK.keys.hidden = false;
    if (SK.keys.lastKind === "seed") {
      SK.keys.confirmed = false;
      SK.keys.confirming = false;
      SK.keys.challenge = null;
      SK.show(SK.$("seed-gate"), false);
      SK.show(SK.$("seed-body"), true);
      SK.show(SK.$("seed-words-list"), true);
    } else if (SK.isAsymmetricKey(SK.keys.lastKind)) {
      SK.show(SK.$("seed-gate"), false);
      SK.show(SK.$("keys-private-text"), true);
    }
    SK.syncKeysConfirmUi();
  });
  SK.$("seed-wrote").addEventListener("click", function () {
    if (SK.keys.lastKind !== "seed" || !SK.keys.revealed || SK.keys.confirmed) return;
    var words = SK.keys.last.split(/\s+/).filter(Boolean);
    var count = words.length >= 24 ? 4 : 3;
    SK.keys.challenge = SK.shuffleIndexes(words.length, count);
    SK.keys.confirming = true;
    SK.keys.hidden = false;
    SK.show(SK.$("error-seed-confirm"), false);
    SK.$("error-seed-confirm").textContent = "";
    SK.renderSeedConfirmFields(SK.keys.challenge);
    SK.syncKeysConfirmUi();
  });
  SK.$("seed-show-again").addEventListener("click", function () {
    SK.keys.confirming = false;
    SK.keys.challenge = null;
    SK.keys.confirmed = false;
    SK.keys.hidden = false;
    SK.clearSeedConfirmUi();
    SK.show(SK.$("seed-words-list"), true);
    SK.syncKeysConfirmUi();
  });
  SK.$("seed-confirm-run").addEventListener("click", function () {
    if (!SK.keys.confirming || !SK.keys.challenge) return;
    var answers = [];
    var inputs = SK.$("seed-confirm-fields").querySelectorAll("input");
    for (var i = 0; i < inputs.length; i++) {
      answers.push({
        index: Number(inputs[i].getAttribute("data-challenge-index")),
        word: inputs[i].value,
      });
    }
    if (!SK.seedAnswersMatch(SK.keys.last, answers)) {
      SK.fail("error-seed-confirm", "Those words do not match. Check your notes and try again.");
      return;
    }
    SK.keys.confirmed = true;
    SK.keys.confirming = false;
    SK.keys.challenge = null;
    SK.keys.hidden = false;
    SK.clearSeedConfirmUi();
    SK.show(SK.$("seed-words-list"), true);
    SK.syncKeysConfirmUi();
  });
  SK.$("seed-hide").addEventListener("click", function () {
    if (SK.keys.confirming) return;
    SK.keys.hidden = !SK.keys.hidden;
    if (SK.keys.lastKind === "seed") {
      SK.show(SK.$("seed-words-list"), !SK.keys.hidden);
    } else if (SK.isAsymmetricKey(SK.keys.lastKind)) {
      SK.show(SK.$("keys-private-text"), SK.keys.revealed && !SK.keys.hidden);
    } else {
      SK.$("keys-result-text").textContent = SK.keys.hidden ? "••••••••" : SK.keys.last;
    }
    SK.$("seed-hide").textContent = SK.keys.hidden ? "Show" : "Hide";
  });
  SK.$("seed-copy").addEventListener("click", function () {
    if (SK.keys.lastKind === "seed" && !SK.keys.confirmed) return;
    if (SK.isAsymmetricKey(SK.keys.lastKind)) {
      SK.copyText(SK.keys.last, SK.$("seed-clip"));
      return;
    }
    if (SK.keys.revealed && !SK.keys.hidden) SK.copyText(SK.keys.last, SK.$("seed-clip"));
  });
  SK.$("seed-copy-private").addEventListener("click", function () {
    if (!SK.isAsymmetricKey(SK.keys.lastKind) || !SK.keys.revealed || !SK.keys.private) return;
    SK.copyText(SK.keys.private, SK.$("seed-clip"));
  });
  SK.$("seed-send").addEventListener("click", function () {
    if (!SK.keys.last) return;
    if (SK.keys.lastKind === "seed" && !SK.keys.confirmed) return;
    if (SK.keys.lastKind !== "seed") return;
    var words = SK.keys.last;
    SK.wipeKeys();
    SK.switchTab("derive");
    SK.$("derive-mnemonic").value = words;
    SK.derive.kind = "btc";
    SK.setSeg(SK.$("derive-kind"), "data-kind", "btc");
    SK.syncDeriveForm();
  });
  SK.$("seed-print").addEventListener("click", function () {
    if (!SK.keys.last) return;
    if (SK.keys.lastKind === "seed" && !SK.keys.confirmed) return;
    if (SK.keys.lastKind === "seed") {
      var lines = SK.keys.last.split(/\s+/).map(function (w, i) {
        var n = (i + 1 < 10 ? "0" : "") + (i + 1);
        return n + "  " + w;
      });
      SK.printSheet("BIP-39 wallet mnemonic", lines.join("\n"), true);
    } else {
      SK.printSheet(SK.$("keys-result-label").textContent, SK.keys.last, false);
    }
  });
  SK.$("seed-clear").addEventListener("click", SK.wipeKeys);
  SK.switchKeyType("seed");
  SK.setSeedExportEnabled(false);
};

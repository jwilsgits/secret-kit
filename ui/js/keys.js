SK.keys = {
  keyType: "seed",
  seedWords: 12,
  hexBytes: 32,
  codeCount: 8,
  last: "",
  lastKind: "seed",
  revealed: false,
  hidden: false,
};

SK.wipeKeys = function () {
  SK.keys.last = "";
  SK.keys.revealed = false;
  SK.keys.hidden = false;
  SK.$("seed-words-list").innerHTML = "";
  SK.$("keys-result-text").textContent = "";
  SK.show(SK.$("result-keys"), false);
  SK.show(SK.$("seed-gate"), true);
  SK.show(SK.$("seed-body"), false);
  SK.show(SK.$("error-keys"), false);
  SK.$("seed-clip").textContent = "";
  SK.clearPrint();
};
SK.wipes.keys = SK.wipeKeys;

SK.switchKeyType = function (type) {
  SK.keys.keyType = type;
  SK.show(SK.$("opts-seed"), type === "seed");
  SK.show(SK.$("opts-hex"), type === "hex");
  SK.show(SK.$("opts-codes"), type === "codes");
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
      var value = SK.keys.keyType === "codes" ? result.value.join("\n") : result.value;
      SK.keys.last = value;
      SK.keys.lastKind = SK.keys.keyType;
      SK.keys.revealed = SK.keys.keyType !== "seed";
      SK.keys.hidden = false;
      SK.$("keys-result-label").textContent = {
        seed: "Wallet seed",
        hex: "Hex key",
        uuid: "UUID v4",
        codes: "Backup codes",
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
      SK.show(SK.$("result-keys"), true);
      SK.show(SK.$("seed-gate"), SK.keys.keyType === "seed");
      SK.show(SK.$("seed-body"), SK.keys.keyType !== "seed");
      SK.show(SK.$("seed-words-list"), SK.keys.keyType === "seed");
      SK.show(SK.$("keys-result-text"), SK.keys.keyType !== "seed");
      SK.show(SK.$("seed-send-wrap"), SK.keys.keyType === "seed");
    });
  });
  SK.$("seed-reveal").addEventListener("click", function () {
    SK.keys.revealed = true;
    SK.show(SK.$("seed-gate"), false);
    SK.show(SK.$("seed-body"), true);
  });
  SK.$("seed-hide").addEventListener("click", function () {
    SK.keys.hidden = !SK.keys.hidden;
    if (SK.keys.lastKind === "seed") SK.show(SK.$("seed-words-list"), !SK.keys.hidden);
    else SK.$("keys-result-text").textContent = SK.keys.hidden ? "••••••••" : SK.keys.last;
    SK.$("seed-hide").textContent = SK.keys.hidden ? "Show" : "Hide";
  });
  SK.$("seed-copy").addEventListener("click", function () {
    if (SK.keys.revealed && !SK.keys.hidden) SK.copyText(SK.keys.last, SK.$("seed-clip"));
  });
  SK.$("seed-send").addEventListener("click", function () {
    if (!SK.keys.last) return;
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
};

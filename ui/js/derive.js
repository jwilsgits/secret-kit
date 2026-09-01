SK.derive = {
  kind: "btc",
  nostrMode: "mnemonic",
  btcRecv: 5,
  btcChg: 5,
  last: null,
  lastPublic: "",
};

SK.wipeDeriveForm = function () {
  SK.$("derive-mnemonic").value = "";
  SK.$("derive-pass").value = "";
  SK.$("inspect-nsec").value = "";
  SK.$("inspect-npub").value = "";
};

SK.wipeDeriveResult = function () {
  SK.derive.last = null;
  SK.derive.lastPublic = "";
  SK.$("derive-public").innerHTML = "";
  SK.$("derive-private").innerHTML = "";
  SK.show(SK.$("result-derive"), false);
  SK.show(SK.$("derive-priv-gate"), true);
  SK.show(SK.$("derive-private"), false);
  SK.show(SK.$("error-derive"), false);
  SK.$("derive-clip").textContent = "";
  SK.clearPrint();
};

SK.wipeDerive = function () {
  SK.wipeDeriveForm();
  SK.wipeDeriveResult();
};
SK.wipes.derive = SK.wipeDerive;

SK.syncDeriveForm = function () {
  var nostr = SK.derive.kind === "nostr";
  var fresh = nostr && SK.derive.nostrMode === "fresh";
  var inspect = nostr && SK.derive.nostrMode === "inspect";
  SK.show(SK.$("nostr-mode-wrap"), nostr);
  SK.show(SK.$("btc-opts"), !nostr);
  SK.show(SK.$("taproot-wrap"), !nostr);
  SK.show(SK.$("derive-words-wrap"), !fresh && !inspect);
  SK.show(SK.$("inspect-wrap"), inspect);
  if (nostr) {
    var hints = {
      mnemonic: "NIP-06 path m/44'/1237'/0'/0/0",
      fresh: "Fresh 32-byte secret from the OS CSPRNG. Not recoverable from a seed.",
      inspect: "Shows the npub for this nsec. Cannot recover seed words.",
    };
    SK.$("nostr-method-hint").textContent = hints[SK.derive.nostrMode] || hints.mnemonic;
  }
  var hk = SK.$("help-derive-kind");
  if (hk) hk.setAttribute("data-help", "derive.kind." + SK.derive.kind);
  var hn = SK.$("help-nostr-mode");
  if (hn) hn.setAttribute("data-help", "derive.nostr." + SK.derive.nostrMode);
  if (SK.refreshHelp) SK.refreshHelp();
};

SK.kv = function (dl, rows) {
  dl.innerHTML = "";
  rows.forEach(function (row) {
    var wrap = document.createElement("div");
    var dt = document.createElement("dt");
    var dd = document.createElement("dd");
    dt.textContent = row[0];
    dd.textContent = row[1];
    wrap.appendChild(dt);
    wrap.appendChild(dd);
    if (row[2]) {
      var btn = document.createElement("button");
      btn.textContent = "Copy";
      btn.addEventListener("click", function () {
        SK.copyText(row[1], SK.$("derive-clip"));
      });
      wrap.appendChild(btn);
    }
    dl.appendChild(wrap);
  });
};

SK.addrTable = function (title, rows) {
  if (!rows || !rows.length) return "";
  var html = "<p class=\"hint\">" + title + "</p><table class=\"addr-table\"><tr><th>#</th><th>Address</th><th></th></tr>";
  rows.forEach(function (row) {
    html += "<tr><td>" + row.index + "</td><td>" + row.address + "</td><td><button type=\"button\" data-copy=\"" + row.address + "\">Copy</button></td></tr>";
  });
  return html + "</table>";
};

SK.renderBtc = function (value) {
  SK.$("derive-label").textContent = "Bitcoin · BIP-84";
  SK.$("derive-meta").textContent = value.path_address;
  SK.kv(SK.$("derive-public"), [
    ["First", value.address, true],
    ["zpub", value.zpub, true],
    ["Path", value.path_account, false],
  ]);
  var extra = SK.addrTable("Receive", value.receive) + SK.addrTable("Change", value.change);
  if (value.taproot) {
    extra += "<p class=\"hint\">BIP-86 taproot · " + value.taproot.path_account + "</p>";
    extra += SK.addrTable("Taproot receive", value.taproot.receive);
    extra += SK.addrTable("Taproot change", value.taproot.change);
  }
  var hold = document.createElement("div");
  hold.innerHTML = extra;
  SK.$("derive-public").appendChild(hold);
  hold.querySelectorAll("button[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      SK.copyText(btn.getAttribute("data-copy"), SK.$("derive-clip"));
    });
  });
  var privRows = [["zprv", value.zprv, true]];
  if (value.taproot) privRows.push(["xprv (86')", value.taproot.xprv, true]);
  SK.kv(SK.$("derive-private"), privRows);
  var lines = ["address " + value.address, "zpub " + value.zpub, value.path_account];
  value.receive.forEach(function (row) {
    lines.push("recv " + row.index + " " + row.address);
  });
  value.change.forEach(function (row) {
    lines.push("chg " + row.index + " " + row.address);
  });
  if (value.taproot) {
    lines.push("taproot " + value.taproot.address);
    value.taproot.receive.forEach(function (row) {
      lines.push("tr " + row.index + " " + row.address);
    });
  }
  SK.derive.lastPublic = lines.join("\n");
  SK.show(SK.$("derive-priv-gate"), true);
  SK.show(SK.$("derive-private"), false);
};

SK.renderNostr = function (value) {
  SK.$("derive-label").textContent = "Nostr";
  SK.$("derive-meta").textContent = value.method;
  SK.kv(SK.$("derive-public"), [["npub", value.npub, true]]);
  if (SK.derive.nostrMode === "inspect") {
    SK.show(SK.$("derive-priv-gate"), false);
    SK.show(SK.$("derive-private"), false);
    if (value.match === true) SK.$("derive-meta").textContent = "npub matches";
    else if (value.match === false) SK.$("derive-meta").textContent = "npub does not match";
  } else {
    SK.kv(SK.$("derive-private"), [["nsec", value.nsec, true]]);
    SK.show(SK.$("derive-priv-gate"), true);
    SK.show(SK.$("derive-private"), false);
  }
  SK.derive.lastPublic = "npub " + value.npub + "\n" + value.method;
};

SK.initDerive = function () {
  SK.bindSeg("btc-recv", "data-n", function (v) {
    SK.derive.btcRecv = v;
    SK.setSeg(SK.$("btc-recv"), "data-n", v);
  });
  SK.bindSeg("btc-chg", "data-n", function (v) {
    SK.derive.btcChg = v;
    SK.setSeg(SK.$("btc-chg"), "data-n", v);
  });
  SK.bindSeg("derive-kind", "data-kind", function (v) {
    SK.derive.kind = v;
    SK.setSeg(SK.$("derive-kind"), "data-kind", v);
    SK.wipeDeriveResult();
    SK.syncDeriveForm();
  });
  SK.bindSeg("nostr-mode", "data-mode", function (v) {
    SK.derive.nostrMode = v;
    SK.setSeg(SK.$("nostr-mode"), "data-mode", v);
    SK.wipeDeriveResult();
    SK.syncDeriveForm();
  });
  SK.bindToggle("derive-pass-toggle", "derive-pass");
  SK.bindDrop(SK.$("derive-drop"), function (text) {
    SK.$("derive-mnemonic").value = text.trim();
  });
  SK.$("derive-run").addEventListener("click", function () {
    SK.show(SK.$("error-derive"), false);
    if (!SK.state.ready) return SK.fail("error-derive", "Window is still starting.");
    var spec = {
      kind: SK.derive.kind,
      mode: SK.derive.nostrMode,
      receive: Number(SK.derive.btcRecv),
      change: Number(SK.derive.btcChg),
      taproot: SK.$("btc-taproot").checked,
    };
    if (SK.derive.kind === "nostr" && SK.derive.nostrMode === "inspect") {
      spec.nsec = SK.$("inspect-nsec").value;
      spec.npub = SK.$("inspect-npub").value;
    } else if (!(SK.derive.kind === "nostr" && SK.derive.nostrMode === "fresh")) {
      spec.mnemonic = SK.$("derive-mnemonic").value;
      spec.passphrase = SK.$("derive-pass").value;
    }
    var call = SK.derive.kind === "nostr" && SK.derive.nostrMode === "fresh"
      ? SK.flushMouse().then(function () { return SK.api.derive(spec); })
      : SK.api.derive(spec);
    call.then(function (result) {
      if (!result || !result.ok) {
        SK.fail("error-derive", (result && result.error) || "Derive failed.");
        return;
      }
      SK.wipeDeriveForm();
      SK.derive.last = result.value;
      SK.show(SK.$("result-derive"), true);
      if (SK.derive.kind === "btc") SK.renderBtc(result.value);
      else SK.renderNostr(result.value);
    }).catch(function (err) {
      SK.fail("error-derive", String(err));
    });
  });
  SK.$("derive-reveal-priv").addEventListener("click", function () {
    SK.show(SK.$("derive-priv-gate"), false);
    SK.show(SK.$("derive-private"), true);
  });
  SK.$("derive-copy-pub").addEventListener("click", function () {
    SK.copyText(SK.derive.lastPublic, SK.$("derive-clip"));
  });
  SK.$("derive-print").addEventListener("click", function () {
    if (SK.derive.lastPublic) SK.printSheet(SK.$("derive-label").textContent, SK.derive.lastPublic, false);
  });
  SK.$("derive-clear").addEventListener("click", SK.wipeDerive);
  SK.$("derive-clear-words").addEventListener("click", SK.wipeDeriveForm);
};

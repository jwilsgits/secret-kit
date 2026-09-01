SK.verify = {
  hashPath: "",
  uploaded: false,
  cmpA: "",
  cmpB: "",
  cmpAContent: null,
  cmpBContent: null,
  folderPath: "",
  lastHashDigest: "",
  lastFolderText: "",
};

SK.wipeVerify = function () {
  SK.$("hash-expected").value = "";
  SK.$("hash-algo").value = "auto";
  SK.$("hash-file-label").textContent = "Choose a file, or drop one here";
  SK.$("hash-detect").textContent = "Paste a hash to detect MD5 / SHA-1 / SHA-256 / SHA-512";
  SK.$("mn-check").value = "";
  SK.verify.hashPath = "";
  SK.verify.uploaded = false;
  SK._upload = null;
  SK.verify.cmpA = "";
  SK.verify.cmpB = "";
  SK.verify.cmpAContent = null;
  SK.verify.cmpBContent = null;
  SK.verify.folderPath = "";
  SK.verify.lastHashDigest = "";
  SK.verify.lastFolderText = "";
  SK.$("cmp-a-label").textContent = "none";
  SK.$("cmp-b-label").textContent = "none";
  SK.$("folder-label").textContent = "none";
  SK.$("cmp-detail").textContent = "";
  SK.$("folder-detail").textContent = "";
  SK.show(SK.$("hash-algo-wrap"), false);
  SK.show(SK.$("hash-result"), false);
  SK.show(SK.$("mn-verdict"), false);
  SK.show(SK.$("error-hash"), false);
  SK.show(SK.$("error-mn"), false);
  SK.show(SK.$("error-cmp"), false);
  SK.show(SK.$("cmp-verdict"), false);
  SK.show(SK.$("cmp-detail"), false);
  SK.show(SK.$("error-folder"), false);
  SK.show(SK.$("folder-detail"), false);
  SK.show(SK.$("folder-copy"), false);
};
SK.wipes.verify = SK.wipeVerify;

SK.initVerify = function () {
  if (SK.isHttpMode()) {
    SK.show(SK.$("folder-card"), false);
  }

  function updateHashDetect() {
    var hex = (SK.$("hash-expected").value || "").replace(/[\s:]/g, "");
    if (/^0x/i.test(hex)) hex = hex.slice(2);
    var map = {
      32: "MD5 (legacy match only)",
      40: "SHA-1 (legacy match only)",
      64: "SHA-256",
      128: "SHA-512",
    };
    var label = map[hex.length];
    if (label) {
      SK.$("hash-detect").textContent = "Detected: " + label;
      SK.show(SK.$("hash-algo-wrap"), false);
      SK.$("hash-algo").value = "auto";
    } else if (hex.length) {
      SK.$("hash-detect").textContent = "Length " + hex.length + " is not a known digest. Pick an algorithm.";
      SK.show(SK.$("hash-algo-wrap"), true);
    } else {
      SK.$("hash-detect").textContent = "Paste a hash to detect MD5 / SHA-1 / SHA-256 / SHA-512";
      SK.show(SK.$("hash-algo-wrap"), false);
    }
    if (SK.refreshHelp) SK.refreshHelp();
  }

  function pickInto(setter, label) {
    if (!SK.state.ready) return;
    SK.api.pick_file().then(function (res) {
      if (res && res.path) {
        setter(res);
        SK.$(label).textContent = SK.basename(res.path);
      }
    });
  }

  SK.$("hash-expected").addEventListener("input", updateHashDetect);
  SK.$("hash-pick").addEventListener("click", function () {
    if (!SK.state.ready) return;
    SK.api.pick_file().then(function (res) {
      if (res && res.path) {
        SK.verify.hashPath = res.path;
        SK.verify.uploaded = !!res.uploaded;
        SK._upload = res.uploaded ? { name: res.path, content: res.content } : null;
        SK.$("hash-file-label").textContent = SK.basename(res.path);
      }
    });
  });
  SK.$("hash-run").addEventListener("click", function () {
    SK.show(SK.$("error-hash"), false);
    SK.show(SK.$("hash-result"), false);
    if (!SK.verify.hashPath) return SK.fail("error-hash", "Choose a file first.");
    var spec = {
      path: SK.verify.hashPath,
      expected: SK.$("hash-expected").value,
      algo: SK.$("hash-algo-wrap").classList.contains("hidden") ? "auto" : SK.$("hash-algo").value,
    };
    var hashCall = SK.verify.uploaded
      ? SK.api.hash_bytes({ content: SK._upload && SK._upload.content, expected: spec.expected, algo: spec.algo })
      : SK.api.hash_file(spec);
    hashCall.then(function (result) {
      if (!result || !result.ok) return SK.fail("error-hash", (result && result.error) || "Hash failed.");
      var verdict = SK.$("hash-verdict");
      verdict.textContent = result.match ? "Match" : "Mismatch";
      verdict.className = "verdict " + (result.match ? "good" : "bad");
      var extra = result.legacy
        ? "\nLegacy algorithm — a match only means the bytes equal the vendor string."
        : "";
      SK.$("hash-detail").textContent =
        "Algorithm: " + result.algo.toUpperCase() +
        "\nExpected:  " + result.expected +
        "\nComputed:  " + result.digest + extra;
      SK.verify.lastHashDigest = result.digest;
      SK.show(SK.$("hash-result"), true);
    }).catch(function (err) {
      SK.fail("error-hash", String(err));
    });
  });
  SK.$("hash-copy").addEventListener("click", function () {
    SK.copyText(SK.verify.lastHashDigest, SK.$("hash-detect"));
  });
  SK.$("mn-run").addEventListener("click", function () {
    SK.show(SK.$("error-mn"), false);
    SK.show(SK.$("mn-verdict"), false);
    SK.api.check_mnemonic(SK.$("mn-check").value).then(function (result) {
      var el = SK.$("mn-verdict");
      if (!result || !result.ok) return SK.fail("error-mn", (result && result.error) || "Check failed.");
      if (!result.words) {
        el.textContent = "Enter a phrase first.";
        el.className = "verdict bad";
      } else if (result.valid) {
        el.textContent = "Checksum valid · " + result.words + " words";
        el.className = "verdict good";
      } else {
        el.textContent = "Invalid BIP-39 checksum or unknown words";
        el.className = "verdict bad";
      }
      SK.show(el, true);
    }).catch(function (err) {
      SK.fail("error-mn", String(err));
    });
  });
  SK.$("verify-clear").addEventListener("click", SK.wipeVerify);
  SK.$("cmp-pick-a").addEventListener("click", function () {
    pickInto(function (res) {
      SK.verify.cmpA = res.path;
      SK.verify.cmpAContent = res.uploaded ? res.content : null;
    }, "cmp-a-label");
  });
  SK.$("cmp-pick-b").addEventListener("click", function () {
    pickInto(function (res) {
      SK.verify.cmpB = res.path;
      SK.verify.cmpBContent = res.uploaded ? res.content : null;
    }, "cmp-b-label");
  });
  SK.$("cmp-run").addEventListener("click", function () {
    SK.show(SK.$("error-cmp"), false);
    if (!SK.verify.cmpA || !SK.verify.cmpB) return SK.fail("error-cmp", "Choose both files.");
    var cmpCall = (SK.verify.cmpAContent != null && SK.verify.cmpBContent != null)
      ? SK.api.compare_bytes({
          content_a: SK.verify.cmpAContent,
          content_b: SK.verify.cmpBContent,
          algo: "sha256",
        })
      : SK.api.compare_files({
          path_a: SK.verify.cmpA,
          path_b: SK.verify.cmpB,
          algo: "sha256",
        });
    cmpCall.then(function (result) {
      if (!result || !result.ok) return SK.fail("error-cmp", (result && result.error) || "Compare failed.");
      var el = SK.$("cmp-verdict");
      el.textContent = result.match ? "Files match" : "Files differ";
      el.className = "verdict " + (result.match ? "good" : "bad");
      SK.$("cmp-detail").textContent = "A " + result.digest_a + "\nB " + result.digest_b;
      SK.show(el, true);
      SK.show(SK.$("cmp-detail"), true);
    }).catch(function (err) {
      SK.fail("error-cmp", String(err));
    });
  });
  SK.$("folder-pick").addEventListener("click", function () {
    if (!SK.state.ready) return;
    SK.api.pick_folder().then(function (res) {
      if (res && res.path) {
        SK.verify.folderPath = res.path;
        SK.$("folder-label").textContent = SK.basename(res.path);
      }
    });
  });
  SK.$("folder-run").addEventListener("click", function () {
    SK.show(SK.$("error-folder"), false);
    if (!SK.verify.folderPath) return SK.fail("error-folder", "Choose a folder first.");
    SK.api.hash_folder({ path: SK.verify.folderPath, algo: "sha256" }).then(function (result) {
      if (!result || !result.ok) return SK.fail("error-folder", (result && result.error) || "Hash failed.");
      var lines = result.files.map(function (row) {
        return row.digest + "  " + row.path;
      });
      SK.verify.lastFolderText = lines.join("\n");
      SK.$("folder-detail").textContent = result.count + " files\n" + SK.verify.lastFolderText;
      SK.show(SK.$("folder-detail"), true);
      SK.show(SK.$("folder-copy"), true);
    }).catch(function (err) {
      SK.fail("error-folder", String(err));
    });
  });
  SK.$("folder-copy").addEventListener("click", function () {
    SK.copyText(SK.verify.lastFolderText, SK.$("folder-label"));
  });
  SK.bindDrop(SK.$("hash-drop"), null, function (path) {
    SK.verify.hashPath = path;
    SK.verify.uploaded = false;
    SK._upload = null;
    SK.$("hash-file-label").textContent = SK.basename(path);
  }, function (file) {
    SK.readBrowserFile(file).then(function (res) {
      if (!res || !res.path) return;
      SK.verify.hashPath = res.path;
      SK.verify.uploaded = true;
      SK._upload = { name: res.path, content: res.content };
      SK.$("hash-file-label").textContent = SK.basename(res.path);
    });
  });
  SK.bindDrop(SK.$("mn-drop"), function (text) {
    SK.$("mn-check").value = text.trim();
  });
};

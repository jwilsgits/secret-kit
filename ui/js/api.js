SK.apiCall = function (name, args) {
  if (window.pywebview && window.pywebview.api && window.pywebview.api[name]) {
    return window.pywebview.api[name].apply(window.pywebview.api, args);
  }
  return fetch("/api/" + name, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(args),
  }).then(function (r) {
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  });
};

SK.api = {
  generate: function (spec) { return SK.apiCall("generate", [spec]); },
  absorb_mouse: function (samples) { return SK.apiCall("absorb_mouse", [samples]); },
  clear_user_entropy: function () { return SK.apiCall("clear_user_entropy", []); },
  check_mnemonic: function (phrase) { return SK.apiCall("check_mnemonic", [phrase]); },
  hash_file: function (spec) { return SK.apiCall("hash_file", [spec]); },
  hash_bytes: function (spec) { return SK.apiCall("hash_bytes", [spec]); },
  derive: function (spec) { return SK.apiCall("derive", [spec]); },
  compare_files: function (spec) { return SK.apiCall("compare_files", [spec]); },
  hash_folder: function (spec) { return SK.apiCall("hash_folder", [spec]); },
  pick_folder: function () { return SK.apiCall("pick_folder", []); },
  pick_file: function () {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.pick_file) {
      return window.pywebview.api.pick_file();
    }
    return SK.pickBrowserFile();
  },
};

SK.pickBrowserFile = function () {
  return new Promise(function (resolve) {
    var input = document.createElement("input");
    input.type = "file";
    input.onchange = function () {
      var file = input.files && input.files[0];
      if (!file) {
        resolve({ ok: true, path: null });
        return;
      }
      var reader = new FileReader();
      reader.onload = function () {
        var bytes = new Uint8Array(reader.result);
        var bin = "";
        for (var i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
        SK._upload = {
          name: file.name,
          content: btoa(bin),
        };
        resolve({ ok: true, path: file.name, uploaded: true });
      };
      reader.onerror = function () {
        resolve({ ok: false, path: null, error: "could not read file" });
      };
      reader.readAsArrayBuffer(file);
    };
    input.click();
  });
};

SK.isHttpMode = function () {
  return !(window.pywebview && window.pywebview.api);
};

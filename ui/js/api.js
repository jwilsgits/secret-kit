SK.HTTP_API = "http://127.0.0.1:8765";
SK.HTTP_HINT = "Start with python3 app.py --http 127.0.0.1:8765";

SK.isLoopbackHttpPage = function () {
  try {
    var loc = window.location;
    var host = (loc.hostname || "").toLowerCase();
    var loopback = host === "127.0.0.1" || host === "localhost" || host === "[::1]" || host === "::1";
    return (loc.protocol === "http:" || loc.protocol === "https:") && loopback;
  } catch (e) {
    return false;
  }
};

SK.httpApiUrl = function (name) {
  var path = "/api/" + name;
  return SK.isLoopbackHttpPage() ? path : SK.HTTP_API + path;
};

SK.isNetworkFetchError = function (err) {
  var msg = String((err && err.message) || err || "");
  return (err && err.name === "TypeError") || /Failed to fetch|NetworkError|Load failed/i.test(msg);
};

SK.postJson = function (url, args) {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(args),
  }).then(function (r) {
    if (!r.ok) {
      var err = new Error("HTTP " + r.status);
      err.status = r.status;
      throw err;
    }
    return r.json();
  });
};

SK.apiCall = function (name, args) {
  if (window.pywebview && window.pywebview.api && window.pywebview.api[name]) {
    return window.pywebview.api[name].apply(window.pywebview.api, args);
  }
  var primary = SK.httpApiUrl(name);
  var fallback = SK.HTTP_API + "/api/" + name;
  return SK.postJson(primary, args)
    .catch(function (err) {
      if (primary !== fallback && (SK.isNetworkFetchError(err) || err.status === 404)) {
        return SK.postJson(fallback, args);
      }
      throw err;
    })
    .catch(function (err) {
      if (SK.isNetworkFetchError(err)) throw new Error(SK.HTTP_HINT);
      throw err;
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
  compare_bytes: function (spec) { return SK.apiCall("compare_bytes", [spec]); },
  hash_folder: function (spec) { return SK.apiCall("hash_folder", [spec]); },
  pick_folder: function () { return SK.apiCall("pick_folder", []); },
  pick_file: function () {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.pick_file) {
      return window.pywebview.api.pick_file();
    }
    return SK.pickBrowserFile();
  },
};

SK.readBrowserFile = function (file) {
  return new Promise(function (resolve) {
    if (!file) {
      resolve({ ok: true, path: null });
      return;
    }
    var reader = new FileReader();
    reader.onload = function () {
      var bytes = new Uint8Array(reader.result);
      var bin = "";
      for (var i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
      resolve({
        ok: true,
        path: file.name,
        uploaded: true,
        content: btoa(bin),
      });
    };
    reader.onerror = function () {
      resolve({ ok: false, path: null, error: "could not read file" });
    };
    reader.readAsArrayBuffer(file);
  });
};

SK.pickBrowserFile = function () {
  return new Promise(function (resolve) {
    var input = document.createElement("input");
    input.type = "file";
    input.onchange = function () {
      SK.readBrowserFile(input.files && input.files[0]).then(resolve);
    };
    input.click();
  });
};

SK.isHttpMode = function () {
  return !(window.pywebview && window.pywebview.api);
};

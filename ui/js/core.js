window.SK = window.SK || {};

SK.state = {
  ready: false,
  busy: false,
  tab: "passwords",
  mouseQueue: [],
  mouseCount: 0,
  copyUsedFallback: false,
  clipTimer: null,
  clipLeft: 0,
  clipNote: null,
  _flushing: null,
};

SK.wipes = {};

SK.$ = function (id) {
  return document.getElementById(id);
};

SK.show = function (el, on) {
  if (el) el.classList.toggle("hidden", !on);
};

SK.setSeg = function (container, attr, value) {
  var buttons = container.querySelectorAll("button");
  for (var i = 0; i < buttons.length; i++) {
    buttons[i].classList.toggle("on", buttons[i].getAttribute(attr) === String(value));
  }
};

SK.bindSeg = function (id, attr, onPick) {
  SK.$(id).addEventListener("click", function (ev) {
    var btn = ev.target.closest("button");
    if (btn) onPick(btn.getAttribute(attr));
  });
};

SK.fail = function (id, msg) {
  SK.$(id).textContent = msg;
  SK.show(SK.$(id), true);
};

SK.basename = function (path) {
  if (!path) return "";
  var parts = String(path).split(/[/\\]/);
  return parts[parts.length - 1] || path;
};

SK.bindDrop = function (el, onText, onPath) {
  el.addEventListener("dragover", function (ev) {
    ev.preventDefault();
    el.classList.add("over");
  });
  el.addEventListener("dragleave", function () {
    el.classList.remove("over");
  });
  el.addEventListener("drop", function (ev) {
    ev.preventDefault();
    el.classList.remove("over");
    var file = ev.dataTransfer && ev.dataTransfer.files && ev.dataTransfer.files[0];
    if (!file) return;
    if (file.path && onPath) {
      onPath(file.path);
      return;
    }
    if (onText) {
      var reader = new FileReader();
      reader.onload = function () {
        onText(String(reader.result || ""));
      };
      reader.readAsText(file);
    }
  });
};

SK.bindToggle = function (btnId, inputId) {
  SK.$(btnId).addEventListener("click", function () {
    var input = SK.$(inputId);
    var showPw = input.type === "password";
    input.type = showPw ? "text" : "password";
    SK.$(btnId).textContent = showPw ? "Hide" : "Show";
  });
};

SK.clearPrint = function () {
  SK.$("print-value").textContent = "";
  SK.$("print-type").textContent = "";
  SK.$("print-when").textContent = "";
  SK.show(SK.$("print-pass-line"), false);
};

SK.printSheet = function (kind, body, passLine) {
  SK.$("print-type").textContent = "Type: " + kind;
  SK.$("print-when").textContent = "Generated locally: " + new Date().toString();
  SK.$("print-value").textContent = body;
  SK.show(SK.$("print-pass-line"), !!passLine);
  window.print();
  SK.clearPrint();
};

SK.fillWords = function (ol, phrase) {
  ol.innerHTML = "";
  if (!phrase) return;
  phrase.split(/\s+/).forEach(function (word) {
    var li = document.createElement("li");
    li.textContent = word;
    ol.appendChild(li);
  });
};

SK.switchTab = function (tab) {
  if (tab === SK.state.tab) return;
  if (SK.wipes[SK.state.tab]) SK.wipes[SK.state.tab]();
  SK.clearPrint();
  SK.state.tab = tab;
  ["passwords", "keys", "verify", "derive"].forEach(function (name) {
    SK.show(SK.$("panel-" + name), name === tab);
  });
  SK.setSeg(SK.$("tabs"), "data-tab", tab);
  if (SK.state.ready) SK.api.clear_user_entropy();
  SK.resetEntropyUi();
};

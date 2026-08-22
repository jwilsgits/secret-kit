SK.mountEntropy();
SK.initPasswords();
SK.initKeys();
SK.initVerify();
SK.initDerive();

SK.$("tabs").addEventListener("click", function (ev) {
  var btn = ev.target.closest("button");
  if (btn) SK.switchTab(btn.getAttribute("data-tab"));
});

setInterval(function () {
  if (!SK.state.busy) SK.flushMouse();
}, 250);

function markReady() {
  SK.state.ready = true;
  SK.$("ready-pill").textContent = "Offline";
  SK.$("ready-pill").classList.add("ok");
}

if (window.pywebview && window.pywebview.api) {
  markReady();
} else {
  window.addEventListener("pywebviewready", markReady);
  if (SK.isHttpMode()) markReady();
}

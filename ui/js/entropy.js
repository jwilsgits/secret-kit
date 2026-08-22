SK.mountEntropy = function () {
  var tpl = SK.$("entropy-template");
  ["entropy-passwords", "entropy-keys"].forEach(function (id) {
    var host = SK.$(id);
    host.innerHTML = "";
    host.appendChild(tpl.content.cloneNode(true));
  });
  document.querySelectorAll(".mouse-pad").forEach(function (pad) {
    pad.addEventListener("mousemove", function (ev) {
      var rect = pad.getBoundingClientRect();
      SK.state.mouseQueue.push({
        t: Date.now(),
        x: Math.round(ev.clientX - rect.left),
        y: Math.round(ev.clientY - rect.top),
      });
      if (SK.state.mouseQueue.length > 80) SK.flushMouse();
    });
  });
};

SK.activeEntropy = function () {
  var host = SK.state.tab === "keys" ? SK.$("entropy-keys") : SK.$("entropy-passwords");
  return {
    dice: host.querySelector(".dice").value,
    cards: host.querySelector(".cards").value,
  };
};

SK.resetEntropyUi = function () {
  document.querySelectorAll(".mouse-status").forEach(function (el) {
    el.textContent = "Mouse pad unused — OS CSPRNG is enough";
  });
  document.querySelectorAll(".mouse-pad").forEach(function (el) {
    el.classList.remove("active");
  });
  document.querySelectorAll(".dice, .cards").forEach(function (el) {
    el.value = "";
  });
  SK.state.mouseCount = 0;
  SK.state.mouseQueue = [];
};

SK.flushMouse = function () {
  if (SK.state._flushing) return SK.state._flushing;
  if (!SK.state.ready || !SK.state.mouseQueue.length) return Promise.resolve(null);
  var batch = SK.state.mouseQueue.splice(0, SK.state.mouseQueue.length);
  SK.state._flushing = SK.api.absorb_mouse(batch).then(function (res) {
    SK.state.mouseCount = res.bytes_collected || SK.state.mouseCount;
    document.querySelectorAll(".mouse-status").forEach(function (el) {
      el.textContent = SK.state.mouseCount + " mouse samples mixed into the next generate";
    });
    document.querySelectorAll(".mouse-pad").forEach(function (el) {
      el.classList.add("active");
    });
    return res;
  }).catch(function () {
    return null;
  }).then(function (res) {
    SK.state._flushing = null;
    return res;
  });
  return SK.state._flushing;
};

SK.runGenerate = function (spec, errId) {
  if (!SK.state.ready) {
    SK.fail(errId, "Window is still starting.");
    return Promise.resolve(null);
  }
  SK.show(SK.$(errId), false);
  SK.state.busy = true;
  return SK.flushMouse()
    .then(function () {
      return SK.api.generate(spec);
    })
    .then(function (result) {
      if (!result || !result.ok) {
        SK.fail(errId, (result && result.error) || "Generate failed.");
        return null;
      }
      SK.resetEntropyUi();
      return result;
    })
    .catch(function (err) {
      SK.fail(errId, String(err));
      return null;
    })
    .then(function (result) {
      SK.state.busy = false;
      return result;
    });
};

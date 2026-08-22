SK.fallbackCopy = function (text) {
  var ta = document.createElement("textarea");
  ta.value = text;
  document.body.appendChild(ta);
  ta.select();
  var ok = false;
  try {
    ok = document.execCommand("copy");
  } catch (e) {
    ok = false;
  }
  document.body.removeChild(ta);
  return ok;
};

SK.copyText = function (text, noteEl) {
  if (!text) return;
  SK.state.copyUsedFallback = false;
  function done() {
    SK.startClipCountdown(noteEl);
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done).catch(function () {
      SK.state.copyUsedFallback = true;
      SK.fallbackCopy(text);
      done();
    });
  } else {
    SK.state.copyUsedFallback = true;
    SK.fallbackCopy(text);
    done();
  }
};

SK.clearClipboard = function () {
  if (SK.state.copyUsedFallback) {
    return Promise.resolve(SK.fallbackCopy(""));
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText("");
  }
  return Promise.resolve(SK.fallbackCopy(""));
};

SK.startClipCountdown = function (noteEl) {
  if (SK.state.clipTimer) clearInterval(SK.state.clipTimer);
  SK.state.clipNote = noteEl;
  SK.state.clipLeft = 60;
  noteEl.textContent = "Copied. Clipboard clears in 60s.";
  SK.state.clipTimer = setInterval(function () {
    SK.state.clipLeft -= 1;
    if (SK.state.clipLeft > 0) {
      if (SK.state.clipNote) {
        SK.state.clipNote.textContent = "Copied. Clipboard clears in " + SK.state.clipLeft + "s.";
      }
      return;
    }
    clearInterval(SK.state.clipTimer);
    SK.state.clipTimer = null;
    SK.clearClipboard().then(function (ok) {
      if (SK.state.clipNote) {
        SK.state.clipNote.textContent =
          ok === false
            ? "Could not clear clipboard. Overwrite it yourself."
            : "Clipboard cleared.";
      }
    }).catch(function () {
      if (SK.state.clipNote) {
        SK.state.clipNote.textContent = "Could not clear clipboard. Overwrite it yourself.";
      }
    });
  }, 1000);
};

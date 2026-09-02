SK.passwords = {
  type: "pin",
  pinLen: 6,
  pwPreset: "simple",
  memGroups: 3,
  memSep: "-",
  dwWords: 6,
  personaMode: "full",
  personaGender: "any",
  personaAge: "any",
  last: "",
  hidden: false,
};

SK.wipePasswords = function () {
  SK.passwords.last = "";
  SK.passwords.hidden = false;
  SK.show(SK.$("result-passwords"), false);
  SK.show(SK.$("error-passwords"), false);
  SK.$("pw-result-text").textContent = "";
  SK.$("pw-clip").textContent = "";
  SK.clearPrint();
};
SK.wipes.passwords = SK.wipePasswords;

SK.syncPersonaOpts = function () {
  var partial = SK.passwords.personaMode === "partial";
  SK.show(SK.$("persona-partial"), partial);
  SK.show(SK.$("persona-age-wrap"), partial && SK.passwords.personaAge === "target");
};

SK.switchType = function (type) {
  SK.passwords.type = type;
  SK.show(SK.$("opts-pin"), type === "pin");
  SK.show(SK.$("opts-password"), type === "password");
  SK.show(SK.$("opts-memorable"), type === "memorable");
  SK.show(SK.$("opts-diceware"), type === "diceware");
  SK.show(SK.$("opts-persona"), type === "persona");
  if (type === "persona") SK.syncPersonaOpts();
  if (SK.refreshHelp) SK.refreshHelp();
};

SK.buildPwSpec = function () {
  var extra = SK.activeEntropy();
  var spec = { type: SK.passwords.type, dice: extra.dice, cards: extra.cards };
  var p = SK.passwords;
  if (p.type === "pin") {
    spec.pin = {
      charset: SK.$("pin-charset").value,
      length: p.pinLen === "other" ? Number(SK.$("pin-other").value) : Number(p.pinLen),
      avoid_lookalikes: SK.$("pin-lookalikes").checked,
    };
  } else if (p.type === "password") {
    var advancedOpen = SK.$("opts-password").querySelector("details").open;
    spec.password = {
      preset: advancedOpen ? null : p.pwPreset,
      lower: SK.$("pw-lower").checked,
      upper: SK.$("pw-upper").checked,
      digits: SK.$("pw-digits").checked,
      symbols: SK.$("pw-symbols").checked,
      length: Number(SK.$("pw-length").value),
      avoid_lookalikes: SK.$("pw-lookalikes").checked,
    };
  } else if (p.type === "memorable") {
    spec.memorable = { groups: Number(p.memGroups), separator: p.memSep };
  } else if (p.type === "diceware") {
    spec.diceware = { words: Number(p.dwWords) };
  } else if (p.type === "persona") {
    spec.persona = {
      mode: p.personaMode,
      gender: p.personaGender,
      age: p.personaMode === "partial" && p.personaAge === "target"
        ? Number(SK.$("persona-age-input").value)
        : "any",
      fields: {
        name: SK.$("persona-field-name").checked,
        dob: SK.$("persona-field-dob").checked,
        gender: SK.$("persona-field-gender").checked,
        street: SK.$("persona-field-street").checked,
        location: SK.$("persona-field-location").checked,
        phone: SK.$("persona-field-phone").checked,
        username: SK.$("persona-field-username").checked,
      },
    };
  }
  return spec;
};

SK.initPasswords = function () {
  SK.$("type").addEventListener("change", function (ev) {
    SK.switchType(ev.target.value);
  });
  SK.bindSeg("pin-length-seg", "data-len", function (v) {
    SK.passwords.pinLen = v;
    SK.setSeg(SK.$("pin-length-seg"), "data-len", v);
    SK.show(SK.$("pin-other-wrap"), v === "other");
  });
  SK.bindSeg("pw-presets", "data-preset", function (v) {
    SK.passwords.pwPreset = v;
    SK.setSeg(SK.$("pw-presets"), "data-preset", v);
    var map = {
      simple: [true, true, true, false, 16],
      strong: [true, true, true, true, 20],
      paranoid: [true, true, true, true, 32],
    };
    var row = map[v];
    if (!row) return;
    SK.$("pw-lower").checked = row[0];
    SK.$("pw-upper").checked = row[1];
    SK.$("pw-digits").checked = row[2];
    SK.$("pw-symbols").checked = row[3];
    SK.$("pw-length").value = row[4];
  });
  SK.bindSeg("mem-groups", "data-groups", function (v) {
    SK.passwords.memGroups = v;
    SK.setSeg(SK.$("mem-groups"), "data-groups", v);
  });
  SK.bindSeg("mem-sep", "data-sep", function (v) {
    SK.passwords.memSep = v;
    SK.setSeg(SK.$("mem-sep"), "data-sep", v);
  });
  SK.bindSeg("dw-words", "data-dw", function (v) {
    SK.passwords.dwWords = v;
    SK.setSeg(SK.$("dw-words"), "data-dw", v);
  });
  SK.bindSeg("persona-mode", "data-mode", function (v) {
    SK.passwords.personaMode = v;
    SK.setSeg(SK.$("persona-mode"), "data-mode", v);
    SK.syncPersonaOpts();
  });
  SK.bindSeg("persona-gender", "data-gender", function (v) {
    SK.passwords.personaGender = v;
    SK.setSeg(SK.$("persona-gender"), "data-gender", v);
  });
  SK.bindSeg("persona-age", "data-age", function (v) {
    SK.passwords.personaAge = v;
    SK.setSeg(SK.$("persona-age"), "data-age", v);
    SK.syncPersonaOpts();
  });
  SK.$("generate").addEventListener("click", function () {
    SK.runGenerate(SK.buildPwSpec(), "error-passwords").then(function (result) {
      if (!result) return;
      SK.passwords.last = result.value;
      SK.passwords.hidden = false;
      SK.$("pw-result-label").textContent = {
        pin: "PIN",
        password: "Password",
        memorable: "Memorable password",
        diceware: "Diceware phrase",
        persona: "Random persona",
      }[SK.passwords.type];
      SK.$("pw-result-meta").textContent = result.meta.field_count
        ? result.meta.field_count + " fields"
        : result.meta.words
          ? result.meta.words + " words"
          : result.meta.length
            ? result.meta.length + " characters"
            : "";
      SK.$("pw-result-text").textContent = result.value;
      SK.$("pw-hide").textContent = "Hide";
      SK.$("pw-clip").textContent = "";
      SK.show(SK.$("result-passwords"), true);
    });
  });
  SK.$("pw-hide").addEventListener("click", function () {
    if (!SK.passwords.last) return;
    SK.passwords.hidden = !SK.passwords.hidden;
    SK.$("pw-result-text").textContent = SK.passwords.hidden ? "••••••••" : SK.passwords.last;
    SK.$("pw-hide").textContent = SK.passwords.hidden ? "Show" : "Hide";
  });
  SK.$("pw-copy").addEventListener("click", function () {
    if (!SK.passwords.hidden) SK.copyText(SK.passwords.last, SK.$("pw-clip"));
  });
  SK.$("pw-print").addEventListener("click", function () {
    if (SK.passwords.last) SK.printSheet(SK.$("pw-result-label").textContent, SK.passwords.last, false);
  });
  SK.$("pw-clear").addEventListener("click", SK.wipePasswords);
  SK.switchType("pin");
};

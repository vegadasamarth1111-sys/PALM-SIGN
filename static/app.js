(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  const els = {
    stream: $("stream"),
    streamFallback: $("stream-fallback"),
    cameraPill: $("camera-pill"),
    cameraPillText: $("camera-pill-text"),
    videoClock: $("video-clock"),
    frameIndex: $("frame-index"),
    motionDirection: $("motion-direction"),
    motionValue: $("motion-value"),
    fps: $("fps"),
    handFound: $("hand-found"),
    handArea: $("hand-area"),
    fingerCount: $("finger-count"),
    solidity: $("solidity"),
    modeTag: $("mode-tag"),
    readingLabel: $("reading-label"),
    readingKicker: $("reading-kicker"),
    readingDetail: $("reading-detail"),
    confidenceValue: $("confidence-value"),
    confidenceBar: $("confidence-bar"),
    holdLabel: $("hold-label"),
    holdTime: $("hold-time"),
    holdBar: $("hold-bar"),
    readingNote: $("reading-note"),
    transcript: $("transcript"),
    charCount: $("char-count"),
    wordCount: $("word-count"),
    modelState: $("model-state"),
    modelCopy: $("model-copy"),
    toast: $("toast"),
    lab: $("lab"),
    presets: $("presets"),
    applySkin: $("apply-skin"),
    signGrid: $("sign-grid"),
    signSummary: $("sign-summary"),
    collectLabel: $("collect-label"),
    collectTarget: $("collect-target"),
    collectStart: $("collect-start"),
    collectStop: $("collect-stop"),
    captureMeter: $("capture-meter"),
    captureLabel: $("capture-label"),
    captureCount: $("capture-count"),
    captureBar: $("capture-bar"),
    trainModel: $("train-model"),
    resetLab: $("reset-lab"),
    trainStatus: $("train-status"),
  };

  let state = null;
  let lastNoticeId = 0;
  let toastTimer = 0;
  let presetsReady = false;
  let skinDirty = false;
  let stageTimer = 0;
  let streamReady = false;
  let pollTimer = 0;
  let polling = false;
  let signSignature = "";
  let labelSuggested = false;

  const SIGN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
  const SIGN_LABEL_RE = /^[A-Z0-9]{1,3}$/;

  const skinInputs = {
    lowerH: $("lower-h"),
    upperH: $("upper-h"),
    lowerS: $("lower-s"),
    upperS: $("upper-s"),
    lowerV: $("lower-v"),
    upperV: $("upper-v"),
  };
  const skinOutputs = {
    lowerH: $("lower-h-out"),
    upperH: $("upper-h-out"),
    lowerS: $("lower-s-out"),
    upperS: $("upper-s-out"),
    lowerV: $("lower-v-out"),
    upperV: $("upper-v-out"),
  };

  // ------------------------------------------------------------------ utility
  const pad = (value, width) => String(value).padStart(width, "0");

  function toast(message, kind = "quiet") {
    if (!message) return;
    window.clearTimeout(toastTimer);
    els.toast.textContent = message;
    els.toast.classList.toggle("is-error", kind === "error");
    els.toast.classList.add("is-visible");
    toastTimer = window.setTimeout(() => {
      els.toast.classList.remove("is-visible");
    }, kind === "error" ? 5200 : 3600);
  }

  async function requestJSON(url, options = {}) {
    const response = await fetch(url, {
      cache: "no-store",
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });
    let data = null;
    try {
      data = await response.json();
    } catch (_) {
      data = null;
    }
    if (!response.ok || (data && data.ok === false)) {
      throw new Error((data && data.error) || `Request failed (${response.status})`);
    }
    return data;
  }

  function setBusy(button, busy, label) {
    if (!button) return;
    if (busy) {
      button.dataset.previous = button.textContent;
      button.textContent = label || "Working…";
      button.disabled = true;
    } else {
      if (button.dataset.previous) button.textContent = button.dataset.previous;
      delete button.dataset.previous;
      button.disabled = false;
    }
  }

  function updateClock() {
    const now = new Date();
    els.videoClock.textContent = now.toLocaleTimeString([], { hour12: false });
  }

  window.setInterval(updateClock, 1000);
  updateClock();

  // ------------------------------------------------------------------ stream
  function hideStreamFallback() {
    streamReady = true;
    els.streamFallback.classList.add("is-hidden");
  }

  function showStreamFallback(title, detail) {
    const strong = els.streamFallback.querySelector("strong");
    const span = els.streamFallback.querySelector("span:last-child");
    if (strong) strong.textContent = title;
    if (span) span.textContent = detail;
    els.streamFallback.classList.remove("is-hidden");
  }

  els.stream.addEventListener("load", hideStreamFallback);
  els.stream.addEventListener("error", () => {
    streamReady = false;
    showStreamFallback("Stage disconnected", "Trying the camera again…");
    window.setTimeout(() => {
      if (!streamReady) els.stream.src = `/video_feed?t=${Date.now()}`;
    }, 3500);
  });

  // --------------------------------------------------------------- rendering
  function renderCamera(current) {
    const live = Boolean(current.camera_ok);
    els.cameraPill.classList.toggle("is-live", live);
    els.cameraPill.classList.toggle("is-offline", !live);
    els.cameraPillText.textContent = live ? "CAMERA LIVE" : "CAMERA OFFLINE";
    els.cameraPill.title = current.camera_error || "";
    if (live) hideStreamFallback();
    else if (!streamReady) hideStreamFallback();
  }

  function renderReading(current) {
    const modelMode = current.mode === "model";
    els.modeTag.textContent = modelMode ? "MODEL" : "SHAPE";
    els.modeTag.classList.toggle("is-model", modelMode);

    const label = current.reading.label;
    const display = label === null || label === undefined || label === "" ? "—" : String(label);
    if (els.readingLabel.textContent !== display) {
      els.readingLabel.textContent = display;
    }
    els.readingLabel.classList.toggle("is-long", display.length > 3 && display.length <= 8);
    els.readingLabel.classList.toggle("is-label", display.length > 8);

    let kicker = "WAITING FOR HAND";
    if (!current.camera_ok) kicker = "CAMERA OFFLINE";
    else if (current.geometry.hand_found && modelMode) kicker = "READING THE HAND";
    else if (current.geometry.hand_found) kicker = "SHAPE MEASURED";

    els.readingKicker.textContent = kicker;
    els.readingDetail.textContent =
      !current.camera_ok && current.camera_error
        ? current.camera_error
        : current.reading.detail;

    const confidence = current.reading.confidence;
    els.confidenceValue.textContent =
      confidence === null || confidence === undefined ? "—" : `${Math.round(confidence * 100)}%`;
    els.confidenceBar.style.width =
      confidence === null || confidence === undefined ? "0%" : `${Math.max(2, confidence * 100)}%`;

    const progress = Number(current.reading.stable_progress || 0);
    els.holdBar.style.width = `${Math.round(progress * 100)}%`;
    if (modelMode) {
      els.holdLabel.textContent = "Hold to write";
      els.holdTime.textContent = `${Number(current.reading.hold_seconds || 1.5).toFixed(1)} s`;
    } else {
      els.holdLabel.textContent = "Shape mode";
      els.holdTime.textContent = "—";
    }

    if (modelMode) {
      const labels = current.model.labels || [];
      const accuracy = current.model.accuracy;
      els.readingNote.textContent =
        `Writing from ${labels.length} trained sign${labels.length === 1 ? "" : "s"}` +
        (accuracy !== null && accuracy !== undefined
          ? ` · held-out accuracy ${(accuracy * 100).toFixed(1)}%.`
          : ".");
    } else {
      els.readingNote.textContent =
        "No classifier yet. The desk is reading hand shape.";
    }
  }

  function renderReadouts(current) {
    els.motionDirection.textContent = current.motion.direction || "STILL";
    els.motionValue.textContent = `dx ${Number(current.motion.dx || 0).toFixed(2)} · dy ${Number(
      current.motion.dy || 0
    ).toFixed(2)}`;
    const fps = Number(current.fps || 0);
    els.fps.innerHTML = `${fps.toFixed(1)}<span>fps</span>`;
    els.handFound.textContent = current.geometry.hand_found ? "YES" : "NO";
    els.fingerCount.textContent =
      current.geometry.fingers === null || current.geometry.fingers === undefined
        ? "—"
        : String(current.geometry.fingers);
    els.solidity.textContent =
      current.geometry.solidity === null || current.geometry.solidity === undefined
        ? "solidity —"
        : `solidity ${Number(current.geometry.solidity).toFixed(2)}`;
    els.handArea.textContent =
      current.geometry.area === null || current.geometry.area === undefined
        ? "area —"
        : `area ${Math.round(current.geometry.area).toLocaleString()} px`;
    els.frameIndex.textContent = `FRAME ${pad(current.frame_seq || 0, 6)}`;
  }

  function renderTranscript(text, previousText) {
    const value = text || "";
    if (value !== previousText && previousText !== undefined) {
      const panel = els.transcript.closest(".transcript-panel");
      panel.classList.remove("is-written");
      void panel.offsetWidth;
      panel.classList.add("is-written");
      window.setTimeout(() => panel.classList.remove("is-written"), 340);
    }
    els.transcript.textContent = value;
    els.charCount.textContent = `${value.length} CHARACTER${value.length === 1 ? "" : "S"}`;
    const words = value.trim() ? value.trim().split(/\s+/).length : 0;
    els.wordCount.textContent = `${words} WORD${words === 1 ? "" : "S"}`;
  }

  function renderModel(current) {
    const loaded = Boolean(current.model.loaded);
    els.modelState.textContent = loaded
      ? `MODEL / ${current.model.labels.length} SIGN${current.model.labels.length === 1 ? "" : "S"}`
      : "SHAPE MODE";
    if (loaded) {
      const accuracy =
        current.model.accuracy === null
          ? "—"
          : `${(current.model.accuracy * 100).toFixed(1)}% held out`;
      els.modelCopy.textContent = `${accuracy} · ${current.model.samples} frames. Trained signs: ${current.model.labels.join(
        " "
      )}.`;
    } else if (current.model.error) {
      els.modelCopy.textContent = current.model.error;
    } else {
      els.modelCopy.textContent =
        "No trained model yet. The hand geometry readout keeps working.";
    }
  }

  function renderState(current) {
    renderCamera(current);
    renderReading(current);
    renderReadouts(current);
    renderTranscript(current.text, state ? state.text : undefined);
    renderModel(current);
    renderLabState(current);

    if (current.notice && current.notice.id > lastNoticeId) {
      lastNoticeId = current.notice.id;
      if (current.notice.text) toast(current.notice.text, current.notice.kind);
    }
  }

  // --------------------------------------------------------------------- lab
  function renderPresets(current) {
    if (presetsReady) return;
    const presets = current.settings && current.settings.presets;
    if (!presets) return;
    presetsReady = true;
    const fragment = document.createDocumentFragment();
    for (const [key, preset] of Object.entries(presets)) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "preset";
      button.dataset.preset = key;
      button.textContent = preset.label;
      button.addEventListener("click", () => applyPreset(key));
      fragment.appendChild(button);
    }
    els.presets.appendChild(fragment);
  }

  function syncSkinControls(settings) {
    if (!settings || skinDirty) return;
    const { lower, upper, preset } = settings;
    skinInputs.lowerH.value = lower[0];
    skinInputs.upperH.value = upper[0];
    skinInputs.lowerS.value = lower[1];
    skinInputs.upperS.value = upper[1];
    skinInputs.lowerV.value = lower[2];
    skinInputs.upperV.value = upper[2];
    for (const key of Object.keys(skinInputs)) {
      const outputKey = key;
      skinOutputs[outputKey].textContent = skinInputs[key].value;
    }
    for (const button of els.presets.querySelectorAll(".preset")) {
      button.classList.toggle("is-active", button.dataset.preset === preset);
    }
  }

  function renderLabState(current) {
    renderPresets(current);
    syncSkinControls(current.settings);
    renderSigns(current);
    renderTraining(current);
  }

  async function applyPreset(preset) {
    try {
      const data = await requestJSON("/api/settings/skin", {
        method: "POST",
        body: JSON.stringify({ preset }),
      });
      skinDirty = false;
      syncSkinControls(data.settings);
      toast("Skin range updated.");
    } catch (error) {
      toast(error.message, "error");
    }
  }

  async function applySliderRange() {
    const lower = [
      Number(skinInputs.lowerH.value),
      Number(skinInputs.lowerS.value),
      Number(skinInputs.lowerV.value),
    ];
    const upper = [
      Number(skinInputs.upperH.value),
      Number(skinInputs.upperS.value),
      Number(skinInputs.upperV.value),
    ];
    if (!(lower[0] < upper[0] && lower[1] < upper[1] && lower[2] < upper[2])) {
      toast("Each low value must be smaller than its high value.", "error");
      return;
    }
    setBusy(els.applySkin, true, "Applying…");
    try {
      const data = await requestJSON("/api/settings/skin", {
        method: "POST",
        body: JSON.stringify({ lower, upper }),
      });
      skinDirty = false;
      syncSkinControls(data.settings);
      toast("Custom skin range applied.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(els.applySkin, false);
    }
  }

  // ------------------------------------------------------------- sign library
  function signRows(current) {
    const counts = (current.dataset && current.dataset.classes) || {};
    const modelCounts = (current.model && current.model.class_counts) || {};
    const perClass = (current.model && current.model.metrics && current.model.metrics.per_class) || {};
    const extras = new Set();
    for (const label of [
      ...Object.keys(counts),
      ...Object.keys(modelCounts),
      ...((current.model && current.model.labels) || []),
    ]) {
      if (!SIGN_LETTERS.includes(label)) extras.add(label);
    }
    return [...SIGN_LETTERS, ...[...extras].sort()].map((label) => {
      const count = Number(counts[label] ?? modelCounts[label] ?? 0);
      const metric = perClass[label];
      const recall = current.model && current.model.loaded && metric ? Number(metric.recall) : null;
      return { label, count, recall };
    });
  }

  function renderSigns(current) {
    const rows = signRows(current);
    const total = Number((current.dataset && current.dataset.total) || 0);
    const loaded = Boolean(current.model && current.model.loaded);
    const accuracy = current.model ? current.model.accuracy : null;
    els.signSummary.textContent = loaded
      ? `${rows.length} signs · ${total.toLocaleString()} frames · ${(accuracy * 100).toFixed(1)}% held-out`
      : `${rows.length} signs · ${total.toLocaleString()} frames · model not trained`;

    const signature = rows
      .map((row) => `${row.label}:${row.count}:${row.recall === null ? "" : row.recall.toFixed(3)}`)
      .join("|");
    if (signature === signSignature) return;
    signSignature = signature;

    const fragment = document.createDocumentFragment();
    for (const row of rows) {
      const tile = document.createElement("div");
      tile.className = "sign-tile" + (row.count === 0 ? " is-empty" : "");
      tile.setAttribute("role", "listitem");
      tile.title =
        row.recall === null
          ? `${row.label} · ${row.count} frames`
          : `${row.label} · ${row.count} frames · ${(row.recall * 100).toFixed(1)}% accuracy`;

      const letter = document.createElement("span");
      letter.className = "sign-letter";
      letter.textContent = row.label;

      const count = document.createElement("span");
      count.className = "sign-count";
      count.textContent = `${row.count.toLocaleString()} frame${row.count === 1 ? "" : "s"}`;

      const accuracyEl = document.createElement("span");
      const low = row.recall !== null && row.recall < 0.85;
      accuracyEl.className = "sign-acc" + (low ? " is-low" : "");
      accuracyEl.textContent = row.recall === null ? "— acc" : `${Math.round(row.recall * 100)}% acc`;

      const bar = document.createElement("span");
      bar.className = "sign-bar";
      const fill = document.createElement("i");
      if (row.recall !== null) fill.style.width = `${Math.max(2, row.recall * 100)}%`;
      if (low) fill.className = "is-low";
      bar.appendChild(fill);

      tile.append(letter, count, accuracyEl, bar);
      fragment.appendChild(tile);
    }
    els.signGrid.replaceChildren(fragment);
  }

  // ---------------------------------------------------------------- training
  function renderTraining(current) {
    const collect = current.collect || {};
    const active = Boolean(collect.active);
    els.captureMeter.hidden = !active;
    els.collectStart.disabled = active;
    els.collectStop.disabled = !active;
    if (active) {
      const have = Number(collect.have || 0);
      const target = Number(collect.target || 0);
      els.captureLabel.textContent = `Capturing ${collect.label}`;
      els.captureCount.textContent = `${have} / ${target}`;
      els.captureBar.style.width = `${Math.round(Number(collect.progress || 0) * 100)}%`;
    }

    if (!labelSuggested) {
      const counts = (current.dataset && current.dataset.classes) || {};
      const next =
        SIGN_LETTERS.find((letter) => !counts[letter]) ||
        SIGN_LETTERS.reduce(
          (best, letter) => (Number(counts[letter] || 0) < Number(counts[best] || 0) ? letter : best),
          "A"
        );
      els.collectLabel.value = next;
      labelSuggested = true;
    }

    const dataset = current.dataset || {};
    const model = current.model || {};
    const parts = [
      `${Number(dataset.label_count || 0)} signs · ${Number(dataset.total || 0).toLocaleString()} frames captured`,
    ];
    parts.push(
      model.loaded
        ? `model ${(Number(model.accuracy) * 100).toFixed(1)}% held out`
        : "model not trained"
    );
    els.trainStatus.textContent = parts.join(" · ");
  }

  async function startCapture() {
    const label = els.collectLabel.value.trim().toUpperCase();
    if (!SIGN_LABEL_RE.test(label)) {
      toast("Sign label must be 1–3 letters or numbers.", "error");
      return;
    }
    const target = Math.min(300, Math.max(20, Number(els.collectTarget.value) || 80));
    els.collectLabel.value = label;
    els.collectTarget.value = String(target);
    els.collectStart.disabled = true;
    try {
      await requestJSON("/api/collect", {
        method: "POST",
        body: JSON.stringify({ action: "start", label, target }),
      });
      toast(`Capturing ${label}. Keep one hand in the scan box.`);
    } catch (error) {
      els.collectStart.disabled = false;
      toast(error.message, "error");
    }
  }

  async function stopCapture() {
    els.collectStop.disabled = true;
    try {
      await requestJSON("/api/collect", {
        method: "POST",
        body: JSON.stringify({ action: "cancel" }),
      });
    } catch (error) {
      toast(error.message, "error");
    }
  }

  async function trainModel() {
    setBusy(els.trainModel, true, "Training…");
    try {
      const data = await requestJSON("/api/train", { method: "POST", body: "{}" });
      const report = data.report || {};
      signSignature = "";
      toast(
        `Trained ${(report.labels || []).length} signs on ${Number(report.samples || 0).toLocaleString()} frames · ` +
          `${(Number(report.accuracy || 0) * 100).toFixed(1)}% held-out accuracy.`
      );
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(els.trainModel, false);
    }
  }

  async function resetLab() {
    if (
      !window.confirm(
        "Reset removes every captured frame and the trained model. This cannot be undone. Continue?"
      )
    ) {
      return;
    }
    setBusy(els.resetLab, true, "Resetting…");
    try {
      await requestJSON("/api/reset", {
        method: "POST",
        body: JSON.stringify({ confirm: "RESET" }),
      });
      signSignature = "";
      labelSuggested = false;
      toast("Lab reset. Captures and the trained model were removed.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(els.resetLab, false);
    }
  }

  // ------------------------------------------------------------- transcript
  async function doAction(action) {
    try {
      const data = await requestJSON("/api/action", {
        method: "POST",
        body: JSON.stringify({ action }),
      });
      renderTranscript(data.text, state ? state.text : undefined);
      if (state) state.text = data.text;
    } catch (error) {
      toast(error.message, "error");
    }
  }

  function speakText() {
    if (!("speechSynthesis" in window)) {
      toast("This browser does not support speech output.", "error");
      return;
    }
    const text = (state && state.text) || "";
    if (!text.trim()) {
      toast("Nothing to read yet.");
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
    toast("Reading the transcript aloud.");
  }

  async function copyText() {
    const text = (state && state.text) || "";
    if (!text) {
      toast("Nothing to copy yet.");
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      toast("Transcript copied.");
    } catch (_) {
      const area = document.createElement("textarea");
      area.value = text;
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      area.remove();
      toast("Transcript copied.");
    }
  }

  function saveFrame() {
    const link = document.createElement("a");
    link.href = `/api/snapshot.jpg?t=${Date.now()}`;
    link.download = "";
    document.body.appendChild(link);
    link.click();
    link.remove();
    toast("Current stage frame saved.");
  }

  // --------------------------------------------------------------------- lab
  function openLab() {
    if (!els.lab.open) els.lab.showModal();
    els.lab.scrollTop = 0;
    window.requestAnimationFrame(() => {
      els.lab.scrollTop = 0;
      const close = document.getElementById("close-lab");
      if (close) close.focus({ preventScroll: true });
    });
    refreshStages();
    window.clearInterval(stageTimer);
    stageTimer = window.setInterval(refreshStages, 1400);
  }

  function closeLab() {
    if (els.lab.open) els.lab.close();
  }

  function refreshStages() {
    if (!els.lab.open) return;
    const stamp = Date.now();
    for (const img of document.querySelectorAll("[data-stage]")) {
      img.src = `/api/stage/${img.dataset.stage}.jpg?t=${stamp}`;
    }
  }

  // ------------------------------------------------------------------- setup
  for (const button of document.querySelectorAll("[data-action]")) {
    button.addEventListener("click", () => doAction(button.dataset.action));
  }

  for (const [key, input] of Object.entries(skinInputs)) {
    input.addEventListener("input", () => {
      skinDirty = true;
      skinOutputs[key].textContent = input.value;
    });
  }

  $("open-lab").addEventListener("click", openLab);
  $("open-lab-2").addEventListener("click", openLab);
  $("close-lab").addEventListener("click", closeLab);
  els.lab.addEventListener("close", () => {
    window.clearInterval(stageTimer);
    stageTimer = 0;
  });
  els.lab.addEventListener("click", (event) => {
    if (event.target === els.lab) closeLab();
  });

  els.applySkin.addEventListener("click", applySliderRange);
  els.collectStart.addEventListener("click", startCapture);
  els.collectStop.addEventListener("click", stopCapture);
  els.trainModel.addEventListener("click", trainModel);
  els.resetLab.addEventListener("click", resetLab);
  for (const input of [els.collectLabel, els.collectTarget]) {
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        startCapture();
      }
    });
  }
  $("speak").addEventListener("click", speakText);
  $("copy").addEventListener("click", copyText);
  $("save-frame").addEventListener("click", saveFrame);

  document.addEventListener("keydown", (event) => {
    if (els.lab.open) return;
    const tag = event.target && event.target.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "BUTTON" || tag === "SUMMARY") return;
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.code === "Space") {
      event.preventDefault();
      doAction("space");
    } else if (event.key === "Backspace") {
      event.preventDefault();
      doAction("backspace");
    } else if (event.key.toLowerCase() === "c") {
      doAction("clear");
    } else if (event.key.toLowerCase() === "s") {
      speakText();
    }
  });

  // -------------------------------------------------------------------- poll
  async function poll() {
    if (polling) return;
    polling = true;
    try {
      const response = await fetch("/api/state", { cache: "no-store" });
      if (!response.ok) throw new Error(`State request failed (${response.status})`);
      const next = await response.json();
      const previous = state;
      state = next;
      hideStreamFallback();
      renderState(state);
      if (previous && previous.text !== state.text) {
        renderTranscript(state.text, previous.text);
      }
    } catch (error) {
      els.cameraPill.classList.remove("is-live");
      els.cameraPill.classList.add("is-offline");
      els.cameraPillText.textContent = "DESK OFFLINE";
      if (!streamReady) {
        showStreamFallback("Desk not responding", "Start app.py, then this screen will reconnect.");
      }
    } finally {
      polling = false;
      const delay = document.hidden ? 1100 : 430;
      pollTimer = window.setTimeout(poll, delay);
    }
  }

  renderTranscript("", undefined);
  poll();
})();

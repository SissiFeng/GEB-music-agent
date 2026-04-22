(() => {
  // -- refs ------------------------------------------------------------------
  const deck            = document.getElementById("deck");
  const clockLed        = document.getElementById("clockLed");
  const clockWeekdayEl  = document.getElementById("clockWeekday");
  const clockDateEl     = document.getElementById("clockDate");
  const stationIdEl     = document.getElementById("stationId");

  const slotSwitcher    = document.getElementById("slotSwitcher");
  const swPrev          = document.getElementById("swPrev");
  const swNext          = document.getElementById("swNext");
  const swNameEl        = document.getElementById("swName");
  const swTimeEl        = document.getElementById("swTime");
  const swBody          = slotSwitcher ? slotSwitcher.querySelector(".sw-body") : null;

  const statusLineEl    = document.getElementById("statusLine");
  const statusDotEl     = statusLineEl.querySelector(".status-dot");
  const statusTextEl    = statusLineEl.querySelector(".status-text");
  const sinceTimer      = document.getElementById("sinceTimer");

  const audio           = document.getElementById("audio");
  const playerEl        = document.getElementById("player");
  const plTitle         = document.getElementById("plTitle");
  const plState         = document.getElementById("plState");
  const plPrev          = document.getElementById("plPrev");
  const plPlayPause     = document.getElementById("plPlayPause");
  const plNext          = document.getElementById("plNext");
  const plStop          = document.getElementById("plStop");
  const plRegen         = document.getElementById("plRegen");
  const plVol           = document.getElementById("plVol");
  const plTrack         = document.getElementById("plTrack");
  const plFill          = document.getElementById("plFill");
  const plCurTime       = document.getElementById("plCurTime");
  const plTotalTime     = document.getElementById("plTotalTime");

  const queuePanel      = document.getElementById("queuePanel");
  const queueList       = document.getElementById("queueList");
  const queueCount      = document.getElementById("queueCount");

  const goLive          = document.getElementById("goLive");
  const ttButtons       = document.querySelectorAll(".tt-btn");

  // -- state -----------------------------------------------------------------
  let slots = [];
  let selectedIdx = 0;      // index into `slots` shown in the switcher
  let queue = [];
  let queueIndex = -1;
  let activeSlotId = null;
  let liveStartedAt = null;
  const slotCache = {};     // slotId -> resolved tracks
  const slotLoading = {};   // slotId -> bool

  // =========================================================================
  // LED digit patterns (5 cols × 7 rows)
  // =========================================================================
  const DIGITS = {
    "0": [
      "01110",
      "10001",
      "10011",
      "10101",
      "11001",
      "10001",
      "01110",
    ],
    "1": [
      "00100",
      "01100",
      "00100",
      "00100",
      "00100",
      "00100",
      "01110",
    ],
    "2": [
      "01110",
      "10001",
      "00001",
      "00010",
      "00100",
      "01000",
      "11111",
    ],
    "3": [
      "11110",
      "00001",
      "00001",
      "01110",
      "00001",
      "00001",
      "11110",
    ],
    "4": [
      "00010",
      "00110",
      "01010",
      "10010",
      "11111",
      "00010",
      "00010",
    ],
    "5": [
      "11111",
      "10000",
      "11110",
      "00001",
      "00001",
      "10001",
      "01110",
    ],
    "6": [
      "00110",
      "01000",
      "10000",
      "11110",
      "10001",
      "10001",
      "01110",
    ],
    "7": [
      "11111",
      "00001",
      "00010",
      "00100",
      "00100",
      "01000",
      "01000",
    ],
    "8": [
      "01110",
      "10001",
      "10001",
      "01110",
      "10001",
      "10001",
      "01110",
    ],
    "9": [
      "01110",
      "10001",
      "10001",
      "01111",
      "00001",
      "00010",
      "01100",
    ],
  };

  function buildDigit(char) {
    const wrap = document.createElement("div");
    wrap.className = "digit";
    wrap.dataset.digit = char;
    const pattern = DIGITS[char];
    for (let row = 0; row < 7; row++) {
      for (let col = 0; col < 5; col++) {
        const cell = document.createElement("span");
        if (pattern && pattern[row][col] === "1") cell.classList.add("on");
        wrap.appendChild(cell);
      }
    }
    return wrap;
  }

  function buildColon() {
    const wrap = document.createElement("div");
    wrap.className = "colon-dots";
    wrap.appendChild(document.createElement("span"));
    wrap.appendChild(document.createElement("span"));
    return wrap;
  }

  function initClockDOM() {
    clockLed.innerHTML = "";
    for (let i = 0; i < 2; i++) clockLed.appendChild(buildDigit("0"));
    clockLed.appendChild(buildColon());
    for (let i = 0; i < 2; i++) clockLed.appendChild(buildDigit("0"));
  }

  function setClockDigits(str) {
    // str is "HHMM" (4 chars)
    const digitEls = clockLed.querySelectorAll(".digit");
    for (let i = 0; i < 4; i++) {
      const el = digitEls[i];
      if (!el) continue;
      const want = str[i];
      if (el.dataset.digit === want) continue;
      el.dataset.digit = want;
      const pattern = DIGITS[want] || DIGITS["0"];
      const cells = el.querySelectorAll("span");
      for (let row = 0; row < 7; row++) {
        for (let col = 0; col < 5; col++) {
          cells[row * 5 + col].classList.toggle("on", pattern[row][col] === "1");
        }
      }
    }
  }

  // =========================================================================
  // theme
  // =========================================================================
  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("claudio-theme", theme);
    ttButtons.forEach((b) => b.classList.toggle("active", b.getAttribute("data-theme") === theme));
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = theme === "light" ? "#e6e8ee" : "#0b0f1a";
  }
  ttButtons.forEach((b) => b.addEventListener("click", () => applyTheme(b.getAttribute("data-theme"))));
  applyTheme(localStorage.getItem("claudio-theme") || "dark");

  // =========================================================================
  // time helpers
  // =========================================================================
  const pad = (n) => String(n).padStart(2, "0");
  const toMinutes = (hhmm) => {
    const [h, m] = hhmm.split(":").map(Number);
    return h * 60 + m;
  };
  const nowMinutes = () => { const d = new Date(); return d.getHours() * 60 + d.getMinutes(); };

  function fmtTime(seconds) {
    if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${pad(s)}`;
  }

  function tickClock() {
    const d = new Date();
    setClockDigits(`${pad(d.getHours())}${pad(d.getMinutes())}`);
    const WK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    const MO = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
    clockWeekdayEl.textContent = WK[d.getDay()];
    clockDateEl.textContent = `${pad(d.getDate())} ${MO[d.getMonth()]} ${d.getFullYear()}`;

    // broadcasting-since timer
    if (liveStartedAt) {
      const elapsed = Math.floor((Date.now() - liveStartedAt) / 1000);
      sinceTimer.textContent = `T+ ${pad(Math.floor(elapsed / 60))}:${pad(elapsed % 60)}`;
    }
  }

  function currentSlotIdx(slotList) {
    const n = nowMinutes();
    for (let i = 0; i < slotList.length; i++) {
      const s = slotList[i];
      const a = toMinutes(s.time_start);
      const b = toMinutes(s.time_end);
      if (a <= b ? n >= a && n < b : n >= a || n < b) return i;
    }
    return 0;
  }

  const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));

  // =========================================================================
  // slot switcher
  // =========================================================================
  function renderSwitcher() {
    if (!slots.length) {
      slotSwitcher.hidden = true;
      return;
    }
    slotSwitcher.hidden = false;
    const s = slots[selectedIdx];
    swNameEl.textContent = s.name;
    swTimeEl.textContent = `${s.time_start} – ${s.time_end}`;
    stationIdEl.textContent = `CLAUDIO / ${s.name.toUpperCase()}`;
  }

  function selectSlot(idx, autoplay = true) {
    if (!slots.length) return;
    selectedIdx = ((idx % slots.length) + slots.length) % slots.length;
    renderSwitcher();
    if (autoplay) playSelected();
  }

  swPrev.addEventListener("click", () => selectSlot(selectedIdx - 1));
  swNext.addEventListener("click", () => selectSlot(selectedIdx + 1));
  if (swBody) swBody.addEventListener("click", () => playSelected());
  goLive.addEventListener("click", () => playSelected());

  function setIdleStatus(text) {
    statusDotEl.className = "status-dot idle";
    statusTextEl.textContent = text;
    deck.classList.remove("live");
    sinceTimer.hidden = true;
    liveStartedAt = null;
    goLive.hidden = false;
  }

  function setLiveStatus() {
    statusDotEl.className = "status-dot live";
    statusTextEl.textContent = "ON AIR";
    deck.classList.add("live");
    sinceTimer.hidden = false;
    liveStartedAt = Date.now();
    goLive.hidden = true;
  }

  function setLoadingStatus(msg) {
    statusDotEl.className = "status-dot idle";
    statusTextEl.textContent = msg;
    goLive.hidden = true;
  }

  // =========================================================================
  // queue rendering
  // =========================================================================
  function renderQueue() {
    if (!queue.length) {
      queuePanel.hidden = true;
      return;
    }
    queuePanel.hidden = false;
    queueCount.textContent = `${queue.length} TRACKS`;
    queueList.innerHTML = queue.map((t, i) => {
      const now = i === queueIndex;
      const label = now ? "▶" : String(i + 1);
      return `
        <li class="queue-item${now ? " now" : ""}" data-idx="${i}">
          <span class="qi-num">${label}</span>
          <span class="qi-title">${escapeHtml(t.title)}</span>
          <span class="qi-artist">${escapeHtml(t.artist || "")}</span>
        </li>`;
    }).join("");
    queueList.querySelectorAll(".queue-item").forEach((el) => {
      el.addEventListener("click", () => {
        queueIndex = parseInt(el.getAttribute("data-idx"), 10);
        playCurrent();
      });
    });
  }

  // =========================================================================
  // playback
  // =========================================================================
  const LOADING_MESSAGES = [
    { after: 0,     text: "KIMI · PICKING SONGS…" },
    { after: 3500,  text: "PULLING AUDIO FROM YOUTUBE…" },
    { after: 9000,  text: "ALMOST THERE…" },
    { after: 15000, text: "SLOW NETWORK — HANG TIGHT" },
  ];

  async function playSelected(opts = {}) {
    if (!slots.length) return;
    const slot = slots[selectedIdx];
    const slotId = slot.id;
    const { refresh = false } = opts;

    if (!refresh && slotCache[slotId]) {
      startPlayback(slot, slotCache[slotId]);
      return;
    }
    if (slotLoading[slotId]) return;

    slotLoading[slotId] = true;
    setLoadingStatus(LOADING_MESSAGES[0].text);

    const startedAt = Date.now();
    const rotator = setInterval(() => {
      const elapsed = Date.now() - startedAt;
      const stage = [...LOADING_MESSAGES].reverse().find((m) => elapsed >= m.after);
      if (stage) setLoadingStatus(stage.text);
    }, 500);

    try {
      const url = `/api/schedule/${encodeURIComponent(slotId)}/resolve${refresh ? "?refresh=1" : ""}`;
      const r = await fetch(url, { method: "POST" });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || `resolve failed: ${r.status}`);

      if (!data.tracks || !data.tracks.length) {
        setIdleStatus(data.error || "NOTHING PLAYABLE FOUND");
        return;
      }
      slotCache[slotId] = data.tracks;
      startPlayback(slot, data.tracks);
    } catch (e) {
      console.error(e);
      setIdleStatus((e.message || "FAILED").toUpperCase());
    } finally {
      clearInterval(rotator);
      slotLoading[slotId] = false;
    }
  }

  async function regenSelected() {
    if (!slots.length) return;
    const slot = slots[selectedIdx];
    delete slotCache[slot.id];  // drop in-memory cache
    // Stop current audio while regenerating
    audio.pause();
    setPlayPauseGlyph(false);
    await playSelected({ refresh: true });
  }

  function startPlayback(slot, tracks) {
    activeSlotId = slot.id;
    queue = tracks;
    queueIndex = 0;
    playerEl.hidden = false;
    setLiveStatus();
    playCurrent();
    renderQueue();
  }

  function setPlayPauseGlyph(isPlaying) {
    plPlayPause.textContent = isPlaying ? "❚❚" : "▶";
    plState.textContent = isPlaying ? "PLAYING" : "PAUSED";
    plState.classList.toggle("paused", !isPlaying);
    playerEl.classList.toggle("paused", !isPlaying);
    if (isPlaying) deck.classList.add("live"); // keep glow
  }

  function playCurrent() {
    const t = queue[queueIndex];
    if (!t) return;
    audio.src = t.url;
    audio.play().catch((e) => console.warn("autoplay blocked?", e));

    plTitle.textContent = `${t.title} — ${t.artist || ""}`;
    setPlayPauseGlyph(true);
    plFill.style.width = "0%";
    plCurTime.textContent = "0:00";
    plTotalTime.textContent = fmtTime((t.duration_ms || 0) / 1000);
    renderQueue();
  }

  function nextTrack() {
    if (queueIndex < 0) return;
    queueIndex = (queueIndex + 1) % queue.length;
    playCurrent();
  }
  function prevTrack() {
    if (queueIndex < 0) return;
    queueIndex = (queueIndex - 1 + queue.length) % queue.length;
    playCurrent();
  }
  function togglePlay() {
    if (audio.paused) {
      audio.play();
      setPlayPauseGlyph(true);
    } else {
      audio.pause();
      setPlayPauseGlyph(false);
    }
  }
  function stop() {
    audio.pause();
    audio.currentTime = 0;
    setPlayPauseGlyph(false);
    playerEl.hidden = true;
    queuePanel.hidden = true;
    queueIndex = -1;
    setIdleStatus("IDLE · TAP ▶ TO GO ON AIR");
  }

  plPrev.addEventListener("click", prevTrack);
  plNext.addEventListener("click", nextTrack);
  plPlayPause.addEventListener("click", togglePlay);
  plStop.addEventListener("click", stop);
  plRegen.addEventListener("click", regenSelected);

  // Auto-advance with safety nets.
  // - On natural end: just go next.
  // - On media error (dead URL, network): skip to next, rate-limited so a broken
  //   queue can't spin the CPU by instantly blasting past every track.
  // - Counter resets when a track actually starts playing successfully.
  let consecutiveErrors = 0;
  const MAX_ERRORS = Math.max(8, queue.length || 8);

  function safeAdvance(reason) {
    if (queueIndex < 0 || !queue.length) return;
    console.log(`[audio] advancing (${reason}), idx=${queueIndex}`);
    nextTrack();
  }

  audio.addEventListener("ended", () => safeAdvance("ended"));
  audio.addEventListener("error", () => {
    consecutiveErrors++;
    const me = audio.error;
    console.warn(`[audio] error on track ${queueIndex}:`,
      me ? `code=${me.code} ${me.message || ""}` : "unknown");
    if (consecutiveErrors >= (queue.length || MAX_ERRORS)) {
      console.error("[audio] whole queue errored, stopping");
      consecutiveErrors = 0;
      setIdleStatus("ALL TRACKS FAILED · REGEN?");
      return;
    }
    setTimeout(() => safeAdvance("error"), 400);
  });
  audio.addEventListener("stalled", () => {
    console.warn(`[audio] stalled on track ${queueIndex}`);
  });

  audio.addEventListener("play",    () => setPlayPauseGlyph(true));
  audio.addEventListener("pause",   () => setPlayPauseGlyph(false));
  audio.addEventListener("playing", () => { consecutiveErrors = 0; });
  audio.addEventListener("timeupdate", () => {
    const dur = audio.duration || 0;
    const cur = audio.currentTime || 0;
    const pct = dur > 0 ? (cur / dur) * 100 : 0;
    plFill.style.width = `${pct}%`;
    plCurTime.textContent = fmtTime(cur);
    if (dur > 0) plTotalTime.textContent = fmtTime(dur);
  });

  plTrack.addEventListener("click", (e) => {
    const rect = plTrack.getBoundingClientRect();
    const pct = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
    if (audio.duration) audio.currentTime = pct * audio.duration;
  });

  audio.volume = parseFloat(plVol.value) / 100;
  plVol.addEventListener("input", () => { audio.volume = parseFloat(plVol.value) / 100; });

  // =========================================================================
  // init
  // =========================================================================
  async function init() {
    initClockDOM();
    tickClock();
    setInterval(tickClock, 1000);

    try {
      const r = await fetch("/api/schedule");
      const data = await r.json();
      slots = data.slots || [];
      if (slots.length) {
        selectedIdx = currentSlotIdx(slots);
        renderSwitcher();
        setIdleStatus("IDLE · TAP ▶ TO GO ON AIR");
      } else {
        setIdleStatus("NO SLOTS CONFIGURED");
      }
    } catch (e) {
      setIdleStatus(`FAILED TO LOAD SCHEDULE`);
      console.error(e);
    }
  }

  init();
})();

// One script for both pages. Everything is one fetch loop against /api/status plus a
// few buttons -- small enough to read out loud during the session.
//
//   /          the guestbook: who answered, and a form. Nothing else.
//   /details   the machinery: copies, log, settings, break-it buttons.

const PAGE = document.body.dataset.page; // "home" | "details"
const POLL_MS = 1500;
const LOG_LIMIT = 40;

// Returns null on the page that does not have the element, so every updater below
// checks before it writes.
const $ = (id) => document.getElementById(id);
const set = (id, text) => { const el = $(id); if (el) el.textContent = text; };

const state = {
  pods: new Map(), // hostname -> how many replies it gave us
  requests: 0,
  lastPod: null,
  lastVersion: null,
  timer: null,
};

const escape = (s) =>
  String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );

function uptime(seconds) {
  if (seconds == null) return "—";
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  if (m < 60) return `${m}m ${seconds % 60}s`;
  return `${Math.floor(m / 60)}h ${m % 60}m`;
}

// ---------------------------------------------------------------- status poll

async function pollStatus() {
  try {
    // cache: "no-store" matters: without it the browser answers from cache and the
    // pod name never changes, which quietly ruins the load-balancing demo.
    const res = await fetch("/api/status", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    render(await res.json());
  } catch (err) {
    setHealth("bad", "no reply");
    addLog({ error: err.message });
  }
  tick();
}

function render(s) {
  state.requests++;
  state.pods.set(s.pod, (state.pods.get(s.pod) || 0) + 1);

  const podChanged = state.lastPod && state.lastPod !== s.pod;
  const versionChanged = state.lastVersion && state.lastVersion !== s.version;
  state.lastPod = s.pod;
  state.lastVersion = s.version;

  set("pod-name", s.pod);
  if (podChanged) flash($("hero"));

  set("version-badge", s.version);
  if (versionChanged) flash($("version-badge"));

  renderCheckpoint(s.checkpoint);

  set("meta-uptime", uptime(s.uptimeSeconds));
  set("meta-requests", state.requests);
  set("meta-pods", state.pods.size);
  set("meta-visits", s.totalVisits ?? "—");

  if (!s.healthy) setHealth("bad", "reporting itself sick");
  else if (!s.db.ok) setHealth("stale", "database unreachable");
  else setHealth("ok", `healthy · database ${s.db.latencyMs}ms`);

  if ($("fail-health")) $("fail-health").checked = !s.healthy;

  renderPods();
  renderConfig(s.config);
  addLog(s);
}

// "Checkpoint 3 · Compose + Postgres · in a Docker container" -- the app works out
// where it is running from its own environment, which is a small lesson by itself.
function renderCheckpoint(cp) {
  const el = $("checkpoint-chip");
  if (!el || !cp) return;
  el.innerHTML = cp.label
    ? `<b>${escape(cp.label)}</b><span>${escape(cp.runtime)}</span>`
    : `<span>${escape(cp.runtime)}</span>`;
  el.title = cp.hint || "";
}

function setHealth(kind, text) {
  const pill = $("health-pill");
  if (pill) pill.className = `pill ${kind}`;
  set("health-text", text);
}

function flash(el) {
  if (!el) return;
  el.classList.remove("changed");
  void el.offsetWidth; // restart the CSS animation
  el.classList.add("changed");
}

function renderPods() {
  const list = $("pod-list");
  if (!list) return;

  const entries = [...state.pods.entries()].sort((a, b) => b[1] - a[1]);
  const max = Math.max(...entries.map(([, n]) => n), 1);

  list.innerHTML = entries
    .map(([pod, hits]) => {
      const share = Math.round((hits / state.requests) * 100);
      return `<li class="${pod === state.lastPod ? "current" : ""}">
        <div class="pod-row"><b>${escape(pod)}</b><span>${hits} · ${share}%</span></div>
        <div class="bar"><span style="width:${(hits / max) * 100}%"></span></div>
      </li>`;
    })
    .join("");
}

function renderConfig(config) {
  const body = $("config-body");
  if (!body || !config) return;
  body.innerHTML = Object.entries(config)
    .map(
      ([k, v]) =>
        `<tr class="${k === "DB_PASSWORD" ? "secret" : ""}"><td>${escape(k)}</td><td>${escape(v)}</td></tr>`
    )
    .join("");
}

function addLog(s) {
  const list = $("log");
  if (!list) return;

  const empty = list.querySelector(".empty");
  if (empty) empty.remove();

  const time = new Date().toLocaleTimeString();
  const li = document.createElement("li");
  if (s.error) {
    li.className = "err";
    li.innerHTML = `<time>${time}</time><span>no reply — ${escape(s.error)}</span>`;
  } else {
    li.innerHTML = `<time>${time}</time><span class="ver">${escape(s.version)}</span>
      <span class="pod">${escape(s.pod)}</span>`;
  }

  list.prepend(li);
  while (list.children.length > LOG_LIMIT) list.lastElementChild.remove();
}

// ------------------------------------------------------------------ guestbook

async function loadVisits(highlight = false) {
  const list = $("visit-list");
  if (!list) return;

  try {
    const rows = await (await fetch("/api/visits", { cache: "no-store" })).json();

    list.innerHTML = rows.length
      ? rows
          .map(
            (r) => `<li><b>${escape(r.name)}</b><br>
              answered by <code>${escape(r.served_by)}</code>
              · ${new Date(r.created_at).toLocaleTimeString()}</li>`
          )
          .join("")
      : `<li class="empty">nobody has signed yet</li>`;

    list.classList.toggle("new-row", highlight);
  } catch {
    list.innerHTML = `<li class="empty">could not load the guestbook</li>`;
  }
}

// --------------------------------------------------------------------- wiring

function on(id, event, handler) {
  const el = $(id);
  if (el) el.addEventListener(event, handler);
}

on("sign-form", "submit", async (e) => {
  e.preventDefault();
  const input = $("name-input");
  const name = input.value.trim();
  if (!name) return;

  input.value = "";
  await fetch("/api/visits", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  await Promise.all([loadVisits(true), pollStatus()]);
  input.focus();
});

// Ten quick requests: the fastest way to show a Service spreading traffic over copies.
on("ping-btn", "click", async (e) => {
  e.target.disabled = true;
  for (let i = 0; i < 10; i++) {
    await pollStatus();
    await new Promise((r) => setTimeout(r, 120));
  }
  e.target.disabled = false;
});

on("reset-pods", "click", () => {
  state.pods.clear();
  state.requests = 0;
  $("pod-list").innerHTML = `<li class="empty">waiting for the first reply…</li>`;
  $("log").innerHTML = `<li class="empty">nothing yet</li>`;
});

on("reveal-secret", "click", async (e) => {
  const { DB_PASSWORD } = await (await fetch("/api/config/secret")).json();
  document.querySelector("tr.secret td:last-child").textContent = DB_PASSWORD;
  e.target.disabled = true;
});

// Note whose copy you are breaking: with several running, the click may well land on a
// different one than the name shown above.
on("fail-health", "change", async (e) => {
  await fetch("/api/chaos/health", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fail: e.target.checked }),
  });
  pollStatus();
});

on("crash-btn", "click", async () => {
  if (!confirm("Stop the app that answers this click?")) return;
  await fetch("/api/chaos/crash", { method: "POST" }).catch(() => {});
  addLog({ error: "crash requested" });
});

// ----------------------------------------------------------------- poll timer

// The guestbook page checks once a second or so too, so the name at the top still
// changes while you talk -- it just has no Live switch to think about.
function liveWanted() {
  const toggle = $("live-toggle");
  return toggle ? toggle.checked : PAGE === "home";
}

function tick() {
  clearTimeout(state.timer);
  if (!liveWanted()) return;

  const tickDot = $("live-tick");
  if (tickDot) {
    tickDot.classList.add("on");
    setTimeout(() => tickDot.classList.remove("on"), 200);
  }
  state.timer = setTimeout(pollStatus, POLL_MS);
}

on("live-toggle", "change", () => {
  clearTimeout(state.timer);
  if (liveWanted()) pollStatus();
});

pollStatus();
loadVisits();

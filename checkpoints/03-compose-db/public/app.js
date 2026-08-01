// No framework, no build step, no CDN. Everything here is one fetch loop against
// /api/status plus a few buttons -- small enough to read out loud during the session.

const POLL_MS = 1500;
const LOG_LIMIT = 40;

const $ = (id) => document.getElementById(id);

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

  $("pod-name").textContent = s.pod;
  if (podChanged) flash($("hero"));

  $("version-badge").textContent = s.version;
  if (versionChanged) flash($("version-badge"));

  $("meta-uptime").textContent = uptime(s.uptimeSeconds);
  $("meta-requests").textContent = state.requests;
  $("meta-pods").textContent = state.pods.size;
  $("meta-visits").textContent = s.totalVisits ?? "—";

  if (!s.healthy) setHealth("bad", "reporting itself sick");
  else if (!s.db.ok) setHealth("stale", "database unreachable");
  else setHealth("ok", `healthy · database ${s.db.latencyMs}ms`);

  $("fail-health").checked = !s.healthy;

  renderPods();
  renderConfig(s.config);
  addLog(s);
}

function setHealth(kind, text) {
  $("health-pill").className = `pill ${kind}`;
  $("health-text").textContent = text;
}

function flash(el) {
  el.classList.remove("changed");
  void el.offsetWidth; // restart the CSS animation
  el.classList.add("changed");
}

function renderPods() {
  const entries = [...state.pods.entries()].sort((a, b) => b[1] - a[1]);
  const max = Math.max(...entries.map(([, n]) => n), 1);

  $("pod-list").innerHTML = entries
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
  $("config-body").innerHTML = Object.entries(config)
    .map(
      ([k, v]) =>
        `<tr class="${k === "DB_PASSWORD" ? "secret" : ""}"><td>${escape(k)}</td><td>${escape(v)}</td></tr>`
    )
    .join("");
}

function addLog(s) {
  const list = $("log");
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
  try {
    const rows = await (await fetch("/api/visits", { cache: "no-store" })).json();
    const list = $("visit-list");

    list.innerHTML = rows.length
      ? rows
          .map(
            (r) => `<li><b>${escape(r.name)}</b><br>
              served by <code>${escape(r.served_by)}</code>
              · ${new Date(r.created_at).toLocaleTimeString()}</li>`
          )
          .join("")
      : `<li class="empty">nobody has signed yet</li>`;

    list.classList.toggle("new-row", highlight);
  } catch {
    $("visit-list").innerHTML = `<li class="empty">could not load visits</li>`;
  }
}

$("sign-form").addEventListener("submit", async (e) => {
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

$("clear-visits").addEventListener("click", async () => {
  if (!confirm("Delete every guestbook entry?")) return;
  await fetch("/api/visits", { method: "DELETE" });
  loadVisits();
});

// -------------------------------------------------------------------- buttons

// Ten quick requests: the fastest way to show a Service spreading traffic over replicas.
$("ping-btn").addEventListener("click", async (e) => {
  e.target.disabled = true;
  for (let i = 0; i < 10; i++) {
    await pollStatus();
    await new Promise((r) => setTimeout(r, 120));
  }
  e.target.disabled = false;
});

$("reset-pods").addEventListener("click", () => {
  state.pods.clear();
  state.requests = 0;
  $("pod-list").innerHTML = `<li class="empty">waiting for the first reply…</li>`;
  $("log").innerHTML = `<li class="empty">nothing yet</li>`;
});

$("reveal-secret").addEventListener("click", async (e) => {
  const { DB_PASSWORD } = await (await fetch("/api/config/secret")).json();
  document.querySelector("tr.secret td:last-child").textContent = DB_PASSWORD;
  e.target.disabled = true;
});

// Note whose pod you are breaking: with several replicas the Service may well route
// this POST to a different one than the toggle you just read.
$("fail-health").addEventListener("change", async (e) => {
  await fetch("/api/chaos/health", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fail: e.target.checked }),
  });
  pollStatus();
});

$("crash-btn").addEventListener("click", async () => {
  if (!confirm("Kill the process serving this request?")) return;
  await fetch("/api/chaos/crash", { method: "POST" }).catch(() => {});
  addLog({ error: "crash requested" });
});

// ----------------------------------------------------------------- poll timer

function tick() {
  clearTimeout(state.timer);
  if (!$("live-toggle").checked) return;
  $("live-tick").classList.add("on");
  setTimeout(() => $("live-tick").classList.remove("on"), 200);
  state.timer = setTimeout(pollStatus, POLL_MS);
}

$("live-toggle").addEventListener("change", () => {
  clearTimeout(state.timer);
  if ($("live-toggle").checked) pollStatus();
});

pollStatus();
loadVisits();

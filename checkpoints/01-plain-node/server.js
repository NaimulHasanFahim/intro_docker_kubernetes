const express = require("express");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { Pool } = require("pg");

const PORT = Number(process.env.PORT || 3000);
const VERSION = process.env.APP_VERSION || "v1";
const STARTED_AT = Date.now();

// Which checkpoint is this? Set by the Dockerfile, Compose file or k8s manifest that
// started us. The navbar prints it so nobody in the room loses their place.
const CHECKPOINT_NAMES = {
  1: "Checkpoint 1 · plain Node, no Docker",
  2: "Checkpoint 2 · one container",
  3: "Checkpoint 3 · Compose + Postgres",
  4: "Checkpoint 4 · first Kubernetes deploy",
  5: "Checkpoint 5 · scale, heal, update",
};

// The app can also work out where it is running, with no configuration at all.
function detectRuntime() {
  if (process.env.KUBERNETES_SERVICE_HOST) return "in a Kubernetes pod";
  if (fs.existsSync("/.dockerenv")) return "in a Docker container";
  return "straight on the machine";
}

// Flipped from the "Break this pod" panel in the UI. When true /healthz answers 500,
// which is exactly what a failing liveness/readiness probe looks like to Kubernetes.
let failHealth = false;

// Every one of these is a knob that changes per environment.
// Remember this list -- it is the whole reason ConfigMaps and Secrets exist.
const DB = {
  host: process.env.DB_HOST || "localhost",
  port: Number(process.env.DB_PORT || 5432),
  user: process.env.DB_USER || "nsu",
  password: process.env.DB_PASSWORD || "nsu_password",
  database: process.env.DB_NAME || "nsu_demo",
};

const pool = new Pool(DB);

async function initDb() {
  // Postgres is almost never ready the instant our app starts.
  // In Docker Compose we solve this with a healthcheck, in Kubernetes with probes.
  for (let attempt = 1; attempt <= 20; attempt++) {
    try {
      await pool.query(`
        CREATE TABLE IF NOT EXISTS visits (
          id        SERIAL PRIMARY KEY,
          name      TEXT NOT NULL,
          served_by TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
      `);
      console.log("[db] connected and ready");
      return;
    } catch (err) {
      console.log(`[db] not ready (attempt ${attempt}/20): ${err.message}`);
      await new Promise((r) => setTimeout(r, 2000));
    }
  }
  throw new Error("could not reach the database, giving up");
}

const app = express();
app.use(express.urlencoded({ extended: false }));
app.use(express.json());

// The whole UI is a handful of static files. No build step, no CDN -- a lecture hall
// never has the wifi you were promised. `extensions` lets /details serve details.html.
app.use(express.static(path.join(__dirname, "public"), { extensions: ["html"] }));

// Liveness/readiness target. Kubernetes will call this constantly.
app.get("/healthz", async (_req, res) => {
  if (failHealth) {
    return res
      .status(500)
      .json({ status: "failing on purpose", pod: os.hostname(), version: VERSION });
  }
  try {
    await pool.query("SELECT 1");
    res.status(200).json({ status: "ok", pod: os.hostname(), version: VERSION });
  } catch (err) {
    res.status(500).json({ status: "degraded", error: err.message });
  }
});

// One call powers the whole dashboard: who served you, which version, is the DB up,
// and what config this replica was handed.
//
// `Connection: close` is the important line. A Kubernetes Service load-balances per TCP
// CONNECTION, not per request, and browsers keep one connection alive for minutes -- so
// without this every poll comes back from the same pod and the whole scaling demo looks
// broken. Closing the connection forces the next poll to be balanced again.
app.get("/api/status", async (_req, res) => {
  res.set("Connection", "close");
  const startedQuery = Date.now();
  let db = { ok: false, latencyMs: null, error: null };
  let totalVisits = null;

  try {
    const { rows } = await pool.query("SELECT COUNT(*)::int AS count FROM visits");
    totalVisits = rows[0].count;
    db = { ok: true, latencyMs: Date.now() - startedQuery, error: null };
  } catch (err) {
    db = { ok: false, latencyMs: null, error: err.message };
  }

  res.json({
    pod: os.hostname(),
    version: VERSION,
    checkpoint: {
      label: CHECKPOINT_NAMES[process.env.CHECKPOINT] || null,
      runtime: detectRuntime(),
      hint: "Set with the CHECKPOINT environment variable; the runtime is detected.",
    },
    healthy: !failHealth,
    uptimeSeconds: Math.round((Date.now() - STARTED_AT) / 1000),
    servedAt: new Date().toISOString(),
    db,
    totalVisits,
    config: {
      APP_VERSION: VERSION,
      CHECKPOINT: process.env.CHECKPOINT || "(not set)",
      PORT: String(PORT),
      DB_HOST: DB.host,
      DB_PORT: String(DB.port),
      DB_USER: DB.user,
      DB_NAME: DB.database,
      DB_PASSWORD: "••••••••",
    },
  });
});

// Deliberately insecure, and that is the lesson. A Secret is base64, not encryption,
// and any code running in the pod can simply read it -- so can anyone with `kubectl exec`.
app.get("/api/config/secret", (_req, res) => {
  res.json({ DB_PASSWORD: DB.password });
});

app.get("/api/visits", async (_req, res) => {
  res.set("Connection", "close");   // same reason as /api/status
  const { rows } = await pool.query(
    "SELECT id, name, served_by, created_at FROM visits ORDER BY id DESC LIMIT 10"
  );
  res.json(rows);
});

app.post("/api/visits", async (req, res) => {
  const name = (req.body.name || "anonymous").toString().slice(0, 60);
  const { rows } = await pool.query(
    "INSERT INTO visits (name, served_by) VALUES ($1, $2) RETURNING id, name, served_by, created_at",
    [name, os.hostname()]
  );

  // The UI posts JSON and stays on the page. A plain <form> submit (the no-JavaScript
  // fallback, and `curl -d name=...`) still gets the old redirect-home behaviour.
  if (!req.is("application/json")) return res.redirect("/");
  res.status(201).json(rows[0]);
});

// Reset between runs so the guestbook starts empty in front of the room.
app.delete("/api/visits", async (_req, res) => {
  await pool.query("DELETE FROM visits");
  res.json({ cleared: true, pod: os.hostname() });
});

// --- Chaos, on purpose -------------------------------------------------------
// Two buttons that let you break this replica live and watch the platform react.

// Make the probes fail without killing the process: readiness pulls this pod out of
// the Service, then liveness restarts it. Docker will not notice at all.
app.post("/api/chaos/health", (req, res) => {
  failHealth = Boolean(req.body.fail);
  console.log(`[chaos] health checks now ${failHealth ? "FAILING" : "passing"}`);
  res.json({ healthy: !failHealth, pod: os.hostname() });
});

// Kill the process outright. Under Kubernetes a replacement pod appears in seconds;
// under `docker run` the container is simply gone until you restart it.
app.post("/api/chaos/crash", (_req, res) => {
  console.log("[chaos] crashing on request");
  res.json({ crashing: true, pod: os.hostname() });
  setTimeout(() => process.exit(1), 100);
});

initDb()
  .then(() => {
    app.listen(PORT, "0.0.0.0", () => {
      console.log(`[app] ${VERSION} listening on :${PORT} as ${os.hostname()}`);
    });
  })
  .catch((err) => {
    console.error(err.message);
    process.exit(1);
  });

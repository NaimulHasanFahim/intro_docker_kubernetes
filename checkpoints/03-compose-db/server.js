const express = require("express");
const os = require("os");
const { Pool } = require("pg");

const PORT = Number(process.env.PORT || 3000);
const VERSION = process.env.APP_VERSION || "v1";

// Every one of these is a knob that changes per environment.
// Remember this list -- it is the whole reason ConfigMaps and Secrets exist.
const pool = new Pool({
  host: process.env.DB_HOST || "localhost",
  port: Number(process.env.DB_PORT || 5432),
  user: process.env.DB_USER || "nsu",
  password: process.env.DB_PASSWORD || "nsu_password",
  database: process.env.DB_NAME || "nsu_demo",
});

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

// Liveness/readiness target. Kubernetes will call this constantly.
app.get("/healthz", async (_req, res) => {
  try {
    await pool.query("SELECT 1");
    res.status(200).json({ status: "ok", pod: os.hostname(), version: VERSION });
  } catch (err) {
    res.status(500).json({ status: "degraded", error: err.message });
  }
});

app.get("/api/visits", async (_req, res) => {
  const { rows } = await pool.query(
    "SELECT name, served_by, created_at FROM visits ORDER BY id DESC LIMIT 10"
  );
  res.json(rows);
});

app.post("/api/visits", async (req, res) => {
  const name = (req.body.name || "anonymous").toString().slice(0, 60);
  await pool.query("INSERT INTO visits (name, served_by) VALUES ($1, $2)", [
    name,
    os.hostname(),
  ]);
  res.redirect("/");
});

app.get("/", async (_req, res) => {
  const { rows } = await pool.query(
    "SELECT name, served_by, created_at FROM visits ORDER BY id DESC LIMIT 10"
  );
  const { rows: countRows } = await pool.query("SELECT COUNT(*) FROM visits");

  res.send(`<!doctype html>
<meta charset="utf-8">
<title>NSU Container Demo</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 640px; margin: 3rem auto; padding: 0 1rem; }
  .host { font-size: 2rem; font-weight: 700; }
  .badge { display:inline-block; background:#111; color:#fff; border-radius:999px; padding:.15rem .7rem; font-size:.8rem; }
  li { margin:.3rem 0; }
  input, button { font-size:1rem; padding:.5rem; }
</style>
<p class="badge">${VERSION}</p>
<p class="host">Served by ${os.hostname()}</p>
<p>${countRows[0].count} total visits recorded in Postgres.</p>
<form method="POST" action="/api/visits">
  <input name="name" placeholder="your name" required>
  <button type="submit">Sign the guestbook</button>
</form>
<h3>Last 10 visits</h3>
<ul>
${rows
  .map(
    (r) =>
      `<li><b>${r.name}</b> &mdash; served by <code>${r.served_by}</code></li>`
  )
  .join("\n")}
</ul>`);
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

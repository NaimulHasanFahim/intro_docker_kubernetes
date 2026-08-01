# Docker & Kubernetes — 90 Minute Intro Session

Slides, a demo app and five checkpoints for teaching Docker + Kubernetes to students
who can code but have never touched ops.

```
intro_docker_kubernetes/
├── CHEATSHEET.md              ← one-page handout for attendees
├── slides/                    ← the deck (see slides/README if you want to edit it)
└── checkpoints/
    ├── 01-plain-node/         ← run the app with no Docker (the pain)
    ├── 02-docker-single/      ← Dockerfile, build, run, exec
    ├── 03-compose-db/         ← app + Postgres via Compose, volumes
    ├── 04-k8s-first-deploy/   ← kind cluster, Namespace/Deployment/Service
    └── 05-k8s-scale-update/   ← ConfigMap, Secret, PVC, probes, scale, heal, rollout
```

Each checkpoint is self-contained with its own README of exact commands.

---

## See it working right now

If Docker is installed, this is the whole thing in one command:

```bash
docker compose -f checkpoints/03-compose-db/docker-compose.yml up --build
```

Open <http://localhost:8080>. Stop it with `Ctrl-C`, then clean up with:

```bash
docker compose -f checkpoints/03-compose-db/docker-compose.yml down -v
```

---

## The demo app

A guestbook — Express + Postgres — with a dashboard UI at `/` that is the demo surface
for the whole session. No build step, no CDN: three static files in `public/`.

| Panel | What it teaches |
|---|---|
| **This page was answered by** | The `os.hostname()` of whatever replied — container ID under Docker, pod name under Kubernetes. Flashes when it changes. |
| **Who answered** | Counts replies per replica with bars — scale to 5 and watch traffic split. `Send 10 requests` does it in one click. |
| **Request log** | Time · version · pod for every poll. During a rollout you see v1 and v2 interleave, then only v2. |
| **Guestbook** | Signs without a page reload; every row records which pod wrote it, all into one Postgres. |
| **Settings this copy was given** | The env vars this pod was handed, plus a `Reveal the password` button — the ConfigMap/Secret lesson. |
| **Break this copy** | Report itself sick (probes) or crash outright (self-healing), on buttons. |

A `Live` toggle in the top bar polls every 1.5s, so scaling and rollouts animate on the
projector without anyone touching the keyboard.

| Route | Does |
|---|---|
| `GET /` | The dashboard |
| `GET /api/status` | Pod, version, uptime, DB health, visit count, config — powers the UI |
| `GET \| POST \| DELETE /api/visits` | List / add / clear guestbook entries |
| `GET /healthz` | Checks the DB — the target for liveness/readiness probes |
| `POST /api/chaos/health` | `{"fail":true}` makes `/healthz` return 500 |
| `POST /api/chaos/crash` | Exits the process with code 1 |

Config comes entirely from env vars (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`,
`DB_NAME`, `APP_VERSION`), which is what makes the ConfigMap/Secret lesson land.

---

## Instructor prep — the day before

```bash
docker --version            # 20.10+; prepared against Docker 29
kubectl version --client
kind --version

# Pre-pull every image so the workshop does not fight the wifi
docker pull node:18-alpine
docker pull postgres:16-alpine
docker pull kindest/node:v1.31.0

# Pre-build the app image and create the cluster (the slow part — 1-3 min)
docker build -t nsu-guestbook:v1 checkpoints/03-compose-db
kind create cluster --config checkpoints/04-k8s-first-deploy/kind-config.yaml
kind load docker-image nsu-guestbook:v1 --name nsu

# Full dry run
kubectl apply -f checkpoints/05-k8s-scale-update/k8s/
kubectl get pods -n nsu-demo -w        # all Running? open http://localhost:8080
kubectl delete namespace nsu-demo
```

Leave the cluster created. Recreating it live in front of 40 people costs 10 minutes.

If `kubectl` or `kind` are missing:

```bash
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
sudo install -o root -g root -m 0755 kind /usr/local/bin/kind
```

**Tell attendees to install:** Docker Desktop or Docker Engine (the only hard
requirement), plus `kubectl` and `kind` for the second half. Node 18+ is optional and
only for Checkpoint 1. A third of the room will not have done it — plan for pairing.

---

## Teaching notes that matter

- **Run the checkpoints as demos, not as a type-along.** You cannot fit this much
  theory and five hands-on labs into 90 minutes. Project your screen and point them at
  the repo to redo it at home. With 3 hours, let the room type along at every one.
- **Never cut** the layer-cache slide, `localhost`-inside-a-container, stateless vs
  stateful, the control loop, labels and selectors, or CP5. Those six carry the session.
- **Define every word the first time you say it.** Server, deploy, environment,
  dependency, kernel, daemon. A student who loses the vocabulary in minute six is lost
  for the remaining eighty-four and will not tell you.
- **"A container is a process that has been lied to."** Say this twice. Everything in
  Part 2 hangs off it.
- **Ask before you reveal.** Several slides pose a question the room can answer. The
  answer they produce beats the answer you supply.
- **Let CP2 fail.** The `ECONNREFUSED 127.0.0.1:5432` moment teaches network isolation
  better than any slide.
- **The hostname line is your best demo.** Keep the dashboard on the projector with
  `Live` on during CP5 and let them watch it change.
- **`kubectl describe` is the highest-value command you can leave them with.** Most
  beginner debugging ends in the Events section.
- **Be honest about scope.** Most projects do not need Kubernetes, and databases
  usually belong outside the cluster. Students remember the person who tells them that.

---

## Cleanup after the session

```bash
kubectl delete namespace nsu-demo
kind delete cluster --name nsu
docker compose -f checkpoints/03-compose-db/docker-compose.yml down -v
docker system prune -af
```

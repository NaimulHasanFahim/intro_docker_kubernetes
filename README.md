# Docker & Kubernetes — 90 Minute Intro Session

Everything needed to run an introductory Docker + Kubernetes session for university
students who can code but have never touched ops.

```
intro_docker_kubernetes/
├── README.md                  ← you are here (instructor guide)
├── CHEATSHEET.md              ← one-page handout for attendees
├── slides/
│   ├── docker-k8s-intro.pptx  ← upload this to Google Slides (62 slides + notes)
│   ├── docker-k8s-intro-lean.pptx  ← the 46-slide cut for a tight 90 minutes
│   ├── content.py             ← ALL slide content — the single source of truth
│   ├── build_pptx.py          ← renders content.py to both outputs (stdlib only)
│   └── deck.md / deck-lean.md ← generated Marp markdown; do not hand-edit
└── checkpoints/
    ├── 01-plain-node/         ← run the app with no Docker (the pain)
    ├── 02-docker-single/      ← Dockerfile, build, run, exec
    ├── 03-compose-db/         ← app + Postgres via Docker Compose, volumes
    ├── 04-k8s-first-deploy/   ← kind cluster, Namespace/Deployment/Service
    └── 05-k8s-scale-update/   ← ConfigMap, Secret, PVC, probes, scale, heal, rollout
```

Each checkpoint folder is **self-contained** and has its own README with the exact
commands. Students can `cd` into one and work, or diff two folders to see what changed.

---

## The demo app

A guestbook — Express + Postgres, ~120 lines. It carries the whole session because of
one design choice: **the page prints `os.hostname()`**. In Docker that is a container
ID; in Kubernetes it is a pod name, and refreshing the page while 5 replicas are
running makes load balancing visible without a single diagram.

| Route | Does |
|---|---|
| `GET /` | HTML page: served-by hostname, version badge, visit count, last 10 names |
| `POST /api/visits` | Writes a name to Postgres |
| `GET /api/visits` | JSON, last 10 |
| `GET /healthz` | Checks the DB — the target for liveness/readiness probes |

Config comes entirely from env vars (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`,
`DB_NAME`, `APP_VERSION`), which is what makes the ConfigMap/Secret lesson land.

---

## The deck is theory-led

Built for an audience with **no prior knowledge**. Every concept gets a *what is it*
and a *why does it exist* before a single command appears. Structure:

| Part | Covers |
|---|---|
| 1 — Why containers exist | The six layers an app actually needs · why environments differ · the three attempts (docs, VMs, containers) · namespaces, cgroups and layered filesystems · myths |
| 2 — Docker | The Docker/OCI stack · image vs container · registries and tags · the Dockerfile and layer caching · container lifecycle · ports · the `localhost` trap · volumes and stateless vs stateful · Compose · where Docker stops |
| 3 — Kubernetes | What orchestration is · declarative vs imperative · the control loop · cluster architecture · objects and YAML anatomy · Deployment→ReplicaSet→Pod · pod statuses · labels and selectors · Services · Ingress · ConfigMap and Secret · storage · probes · scale/heal/rollout · when *not* to use it |
| 4 — Seeing it work | The five checkpoints, one slide each |
| Wrap-up | One-slide summary · Compose↔K8s mapping · two glossary slides · five things to remember |

### Two builds, one source

```bash
python3 slides/build_pptx.py          # 62 slides -> docker-k8s-intro.pptx + deck.md
python3 slides/build_pptx.py --lean   # 46 slides -> *-lean.pptx + deck-lean.md
```

| | Slides | Diagrams | Gags | Checkpoints | Glossary/summary |
|---|---|---|---|---|---|
| **Full** | 62 | 14 | 14 | 5 | 5 |
| **`--lean`** | 46 | 10 | 6 | 5 | 3 |

This was condensed from a 114-slide draft. Almost nothing was deleted — related
slides were **merged**, so one slide now carries what three used to. For example
"what IS a container" was four slides (the claim, namespaces, cgroups, layers) and
is now one three-row table plus the layers diagram.

**A note on the 45-slide target.** Protecting all four categories in full comes to
37 slides on its own (14 diagrams + 14 gags + 5 checkpoints + 4 glossary/summary),
and with a title, five dividers and a Q&A slide that is 43 before a single line of
teaching content. 62 is the honest floor with everything protected. `--lean` reaches
46 by giving up the least essential of the four — it drops 8 gag slides, both
glossaries, and four depth slides. Every one of them is still in the full deck, so
nothing is lost; flip a `"lean": False` in `content.py` to change what goes.

### Session outline (90 minutes)

| Time | Block |
|---|---|
| 0:00–0:05 | Framing: what this session is, the two questions, ground rules |
| 0:05–0:20 | **Part 1** — why containers exist (VMs, the insight, the comparison) |
| 0:20–0:32 | **Part 2** — what a container actually is (namespaces, cgroups, layers) |
| 0:32–0:36 | **CP1 + CP2 demo** — the old way fails, the image works |
| 0:36–0:55 | **Part 3** — Docker concepts (images, Dockerfile, caching, networking, volumes) |
| 0:55–0:58 | **CP3 demo** — Compose, and the volume lesson |
| 0:58–1:02 | Where Docker stops → what orchestration means |
| 1:02–1:20 | **Part 4** — Kubernetes (control loop, architecture, Pod/Deployment/Service, config, probes) |
| 1:20–1:26 | **CP4 + CP5 demo** — deploy, scale, self-heal, rolling update |
| 1:26–1:30 | Five things to remember · where to go next · Q&A |

**Run the checkpoints as demos, not as a type-along.** With true beginners you cannot
fit both this much theory and five hands-on labs into 90 minutes. Project your screen,
run the commands yourself, and point them at the repo to redo it at home. Every
checkpoint README is written to be followed alone.

**If you have 3 hours** instead, run the same deck including the non-core slides and let
the room type along at every checkpoint. That is the version this material really wants.

### If you are running behind

Present the `--lean` build, or skip slides marked `"lean": False` on the fly — the
glossaries, the myths table, `kubectl get pods` statuses, Ingress, storage, the
container lifecycle, registries, and eight of the jokes.

**Never cut:** the layer-cache slide, `localhost`-inside-a-container, stateless vs
stateful, the control loop, labels and selectors, and CP5. Those six carry the session.

### The jokes are load-bearing

14 full-bleed gag slides sit right after the heaviest concepts (6 survive `--lean`). They
are not decoration: beginners lose focus roughly every eight minutes, and each punchline
restates the concept in plain language, so anyone who missed it gets a second chance.

They are ordinary `{"type": "gag", "emoji": ..., "punchline": ...}` entries sitting inline
in `SLIDES`, right after the slide they comment on — move, edit or delete them freely.

---

## Instructor prep — do this the day before

```bash
# 1. Tooling on YOUR machine
docker --version            # 20.10+; this repo was prepared against Docker 29
kubectl version --client
kind --version

# 2. Pre-pull every image so the workshop does not fight the wifi
docker pull node:18-alpine
docker pull postgres:16-alpine
docker pull kindest/node:v1.31.0

# 3. Pre-build the app image
docker build -t nsu-guestbook:v1 checkpoints/03-compose-db

# 4. Create the cluster and load the image (this is the slow part — 1-3 min)
kind create cluster --config checkpoints/04-k8s-first-deploy/kind-config.yaml
kind load docker-image nsu-guestbook:v1 --name nsu

# 5. Full dry run, end to end
kubectl apply -f checkpoints/05-k8s-scale-update/k8s/
kubectl get pods -n nsu-demo -w        # all Running?
# open http://localhost:8080
kubectl delete namespace nsu-demo
```

Leave the cluster created. Recreating it live in front of 40 people is how sessions
lose 10 minutes.

### Missing tools on this machine

`kubectl` and `kind` were not installed when this repo was generated. Install with:

```bash
# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
sudo install -o root -g root -m 0755 kind /usr/local/bin/kind
```

`npm` is also absent here — it is only needed for Checkpoint 1 (`npm install`).
Everything from Checkpoint 2 onward runs inside Docker and needs no local Node at all.

---

## What to tell attendees to install beforehand

Send this a few days ahead, and again the morning of:

- **Docker Desktop** (macOS/Windows) or **Docker Engine** (Linux) — the only hard requirement
- **kubectl** and **kind** — for the second half
- Node 18+ *(optional, only for Checkpoint 1)*
- Run `docker pull node:18-alpine postgres:16-alpine` at home on good wifi

Realistically a third of the room will not have done it. Plan for pair-programming:
"if Docker is not working, sit with someone whose is."

---

## Teaching notes that matter

- **Define every word the first time you say it.** Server, deploy, environment,
  dependency, kernel, daemon. Assume nothing. A student who loses the vocabulary in
  minute six is lost for the remaining eighty-four and will not tell you.
- **"A container is a process that has been lied to."** Say this sentence twice. It is
  the highest-value line in the deck; everything in Part 2 hangs off it.
- **Ask before you reveal.** The deck is written so several slides pose a question the
  room can answer — why the container cannot reach the database, why the pod came back.
  Let someone get it. The answer they produce beats the answer you supply.
- **Let CP2 fail.** The `ECONNREFUSED 127.0.0.1:5432` moment teaches container network
  isolation better than any slide.
- **The hostname line is your best demo.** Refresh the page during CP5 scaling and let
  them watch it change. That single observation makes Services and replicas concrete.
- **`kubectl describe` is the highest-value command you can leave them with.** Say so
  explicitly. Most beginner debugging ends in the Events section.
- **Be honest about scope.** Say out loud that most projects do not need Kubernetes,
  and that databases usually belong outside the cluster. Students remember the person
  who told them the boring truth.

---

## Slides

### Google Slides / PowerPoint — `slides/docker-k8s-intro.pptx`

62 slides, speaker notes included (46 in the `-lean` build). Upload it:

1. <https://drive.google.com> → **New ▸ File upload** → pick the `.pptx`
2. Right-click the uploaded file → **Open with ▸ Google Slides**
3. **File ▸ Save as Google Slides** if you want a native copy

Or just double-click it — PowerPoint, Keynote and LibreOffice open it directly.

### Design

Follows the SUST CSE Carnival 2026 site:

| Element | Value |
|---|---|
| Page background | `#F6F3E7` warm cream |
| Ink | `#1D3A1C` deep forest green |
| Accent (lead lines) | `#3E6B33` |
| Sage (rules, pills, bullets) | `#7F9169` |
| Code blocks | `#EAE6D5` |
| Dividers & gag slides | Inverted: cream on forest green |

Plus the site's motifs: uppercase letter-spaced monospace pills, sage underline rules,
and faint scattered code tokens in the background. All of it is constants at the top of
`build_pptx.py` — change six hex values and the whole deck reskins.

**The background tokens are not random.** They walk a spectrum
(`_FOUNDATION → _DOCKER → _KUBERNETES`, 89 terms) in two directions at once:

- **Across the deck** — early slides show `syscall`, `namespaces`, `chroot`; the middle
  shows `docker compose up -d`, `.dockerignore`; the end shows `kubectl apply -f k8s/`,
  `kube-scheduler`, `OOMKilled`
- **Up each slide** — within one slide the tokens near the floor are Docker-flavoured and
  those near the ceiling are Kubernetes-flavoured

Dividers and gag slides carry 16 tokens; ordinary slides carry 3, in the gutters only, so
nothing ever sits behind the reading text.

**Diagrams are real vector shapes**, not ASCII art — rounded boxes, sage connector lines
and arrowheads, laid out by a small engine in `build_pptx.py`. Three kinds cover the deck:

| Kind | Shape | Used for |
|---|---|---|
| `flow` | Ranks of boxes joined by arrows, `dir: down` or `right` | The dependency stack, the Docker stack, Deployment→ReplicaSet→Pods, Service→pods, Ingress, storage, registry push/pull, port mapping, container lifecycle, the cluster, the summary slide |
| `compare` | Two labelled stacks side by side | Virtual machines vs containers |
| `cycle` | Four boxes in a loop | The reconciliation control loop |

14 slides use them. In `deck.md` the same specs are emitted as Mermaid.

Body text is Arial rather than a monospace face: the site's all-mono look is striking on
a web page but hard to read as paragraphs from the back of a lecture hall. Monospace is
kept for code, labels and the background tokens.

### Regenerating both outputs

```bash
python3 slides/build_pptx.py     # writes docker-k8s-intro.pptx AND deck.md
```

Pure standard library — no `pip install`, no Node. All content lives in
`slides/content.py`; `deck.md` is generated from it, so the markdown and the .pptx can
never drift apart. Each slide is a dict:

```python
{"title": "...",          # required
 "lead": "...",           # framing line, accent green
 "bullets": [...],        # bullet list
 "code": "...",           # monospace block: commands, YAML, terminal output
 "diagram": {...},        # flowchart — see below
 "table": [[...], ...],   # row 0 is the header
 "footnote": "...",       # small italic line at the bottom
 "notes": "...",          # speaker notes
 "core": True}            # part of the 90-minute path?
```

`{"type": "section"}` makes a divider, `{"type": "gag", "emoji": "🐳", "punchline": ...}`
makes a joke slide. A diagram looks like this — `s` picks the box style
(`ink`, `sage`, `alt`, or omit for plain):

```python
"diagram": {"kind": "flow", "labels": ["creates and manages"], "ranks": [
    {"boxes": [{"t": "Deployment", "s": "ink"}], "note": "the part you write"},
    {"boxes": [{"t": "Pod"}, {"t": "Pod"}, {"t": "Pod"}]},
]}
```

> **Verification note:** the deck's OOXML was validated structurally — every part is
> well-formed XML, every relationship resolves, every part is declared in
> `[Content_Types].xml`, and no slide's content overflows its frame. It was **not**
> opened in a renderer, because LibreOffice on this machine cannot load *any* file
> (it fails on a plain `.txt` too). Open it once yourself before the session:
> `soffice --headless --convert-to pdf slides/docker-k8s-intro.pptx`, or just upload
> it to Drive.

### Markdown — `slides/deck.md`

The same deck in [Marp](https://marp.app) format, same palette. **Generated** — edit
`content.py` and re-run the build rather than editing it by hand. Preview with the
*Marp for VS Code* extension, or export:

```bash
npx @marp-team/marp-cli slides/deck.md -o slides/deck.html
npx @marp-team/marp-cli slides/deck.md --pdf
```

---

## Cleanup after the session

```bash
kubectl delete namespace nsu-demo
kind delete cluster --name nsu
docker compose -f checkpoints/03-compose-db/docker-compose.yml down -v
docker system prune -af
```

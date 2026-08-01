# -*- coding: utf-8 -*-
"""
Deck content for the NSU Docker & Kubernetes intro session.

Single source of truth: slides/build_pptx.py renders this to both
docker-k8s-intro.pptx and deck.md, so the two can never drift.

Slide keys
----------
type      "title" | "section" | "gag" | omitted for a normal content slide
title     required
lead      one-line framing sentence, shown in accent green above the body
bullets   list of strings
code      preformatted block (commands, YAML, terminal output) in monospace
diagram   a real flowchart -- see build_pptx.py for the three kinds
table     list of rows; row 0 is the header
footnote  small italic line pinned to the bottom of the slide
notes     speaker notes (exported to the pptx notes pane)
lean      set False to drop this slide from the `--lean` build

Condensed from a 114-slide draft. Almost nothing was deleted outright: related
slides were merged, so one slide now carries what three used to. Kept in full:
all 14 flowchart diagrams, all gag slides, all 5 checkpoints, and the
glossary/summary slides.
"""

SLIDES = [

# ═════════════════════════════════════════════════════════════════════════════
# Framing
# ═════════════════════════════════════════════════════════════════════════════
 {"type": "title",
  "title": "Docker & Kubernetes",
  "subtitle": "What containers are, why they exist, and how clusters run them\nNorth South University · Introductory Session",
  "notes": "Assume zero background. Nobody here has deployed anything. Say that out loud so people relax: 'if you have never heard any of these words, you are exactly who this is for.'"},

 {"title": "What we are actually answering today",
  "lead": "A vocabulary and mental-model session, not a command tutorial.",
  "table": [["Question", "The answer we will build up to"],
            ["Why is shipping software hard?", "An app is code PLUS a whole environment"],
            ["What is a container?", "A process the kernel isolates, so it carries its environment with it"],
            ["What is Docker?", "The tool that builds and runs containers"],
            ["Why is one machine not enough?", "It fails, it fills up, and it cannot be updated without downtime"],
            ["What is Kubernetes?", "A system that keeps containers running correctly across many machines"]],
  "col_ratio": [0.33, 0.67],
  "footnote": "No question is too basic — stop me the moment a word is unfamiliar. Everything is in the repo; you never need to copy from a slide.",
  "notes": "Show of hands: who has heard of Docker, who has run it, who has touched Kubernetes. Calibrate from there."},

# ═════════════════════════════════════════════════════════════════════════════
# PART 1 — Why containers exist
# ═════════════════════════════════════════════════════════════════════════════
 {"type": "section",
  "title": "Part 1 — Why containers exist",
  "subtitle": "The problem, and the idea that solved it"},

 {"title": "First: what does “running an app” actually need?",
  "lead": "Your code is the smallest part of what has to be correct.",
  "diagram": {"kind": "flow", "ranks": [
      {"boxes": [{"t": "YOUR CODE", "sub": "server.js", "s": "ink"}],
       "note": "the part you wrote"},
      {"boxes": [{"t": "LIBRARIES", "sub": "express, pg"}],
       "note": "code other people wrote"},
      {"boxes": [{"t": "RUNTIME", "sub": "Node 18"}],
       "note": "the thing that executes it"},
      {"boxes": [{"t": "SYSTEM LIBRARIES", "sub": "glibc, OpenSSL"}],
       "note": "the OS's shared plumbing"},
      {"boxes": [{"t": "OPERATING SYSTEM", "sub": "Linux", "s": "alt"}],
       "note": "files, processes, network"},
      {"boxes": [{"t": "HARDWARE  /  VM", "s": "alt"}]},
  ]},
  "footnote": "Change any one layer and the app can break. \"It works\" means all six happen to agree.",
  "notes": "Draw this on the board if you can. Everything hangs off it — a container is literally a way to ship the middle four layers together."},

 {"title": "The oldest sentence in software",
  "lead": "“But it works on my machine.”",
  "bullets": ["Rakib writes it on Ubuntu, Node 20, Postgres 16 — works perfectly",
              "Nusrat pulls the same code on macOS with Node 16 — crashes on startup",
              "The university server has Node 18 and no database — every request 500s",
              "What differs: OS version, runtime version, system libraries, installed services, environment variables, file paths, locale, timezone"],
  "footnote": "Nobody wrote bad code. Your app is not just your code — it is your code plus everything it assumes about the machine.",
  "notes": "Ask who has lost an evening to a setup problem that was not their code. Almost every hand goes up. That is the hook."},

 {"type": "gag", "emoji": "💻",
  "title": "“It works on my machine.”",
  "punchline": "Fine. Then we will ship your machine.\n\nThat sentence is, almost literally, what a container is."},

 {"title": "Three attempts at fixing it",
  "lead": "Write it down → ship the whole computer → ship only the part that differs.",
  "diagram": {"kind": "compare",
    "left": {"title": "VIRTUAL MACHINES", "caption": "gigabytes · minutes to boot",
             "rows": [["App", "App", "App"],
                      ["Libs", "Libs", "Libs"],
                      [{"t": "Guest OS", "s": "alt"}, {"t": "Guest OS", "s": "alt"},
                       {"t": "Guest OS", "s": "alt"}],
                      [{"t": "Hypervisor", "s": "sage"}],
                      ["Host OS"],
                      [{"t": "Hardware", "s": "alt"}]]},
    "right": {"title": "CONTAINERS", "caption": "megabytes · under a second",
              "rows": [["App", "App", "App"],
                       ["Libs", "Libs", "Libs"],
                       [{"t": "Container runtime", "s": "sage"}],
                       [{"t": "Host OS  —  ONE kernel, shared by all", "s": "ink"}],
                       [{"t": "Hardware", "s": "alt"}]]}},
  "footnote": "A README goes stale in a week. A VM duplicates an entire operating system per app. Containers delete one row from that picture — and that row is worth gigabytes and minutes.",
  "notes": "Name all three attempts out loud: documentation (fails), VMs (works, far too heavy), containers. The insight: two Linux apps already share a kernel, so stop copying it."},

 {"type": "gag", "emoji": "🗄️   📦",
  "title": "Same job, very different luggage",
  "punchline": "A VM packs its own kitchen, bathroom and roof.\nA container packs a toothbrush and uses yours."},

 {"title": "So what IS a container?",
  "lead": "Not a small virtual machine. An ordinary Linux process the kernel has fenced in.",
  "table": [["Ingredient", "What the kernel does with it"],
            ["namespaces", "A private view of one resource each: its own process list (PID), its own network and IP (NET), its own filesystem tree (MNT), its own hostname (UTS). It cannot see yours."],
            ["cgroups", "A cap on what it may USE: half a core, 512 MB of memory, so much disk and network. Without this, one container starves every other one."],
            ["layered filesystem", "Its own root filesystem, assembled from stacked read-only layers plus one thin writable layer on top."]],
  "col_ratio": [0.2, 0.8],
  "footnote": "Namespaces decide what it can SEE. cgroups decide what it can USE. Run `ps aux` on the host and the container's process is sitting right there in the list.",
  "notes": "The single most valuable sentence of the session: 'a container is a process that has been lied to.' Say it twice."},

 {"type": "gag", "emoji": "🪞",
  "title": "A container is a process that has been lied to",
  "punchline": "The kernel tells it that it is alone in the universe:\nits own processes, its own network, its own filesystem.\nIt believes every word."},

 {"title": "The layered filesystem",
  "lead": "Why images are small to store and instant to start.",
  "diagram": {"kind": "flow", "ranks": [
      {"boxes": [{"t": "WRITABLE LAYER", "sub": "files changed while running",
                  "s": "sage"}],
       "note": "this container only — deleted when it dies"},
      {"boxes": [{"t": "layer 4  ·  your source code"}]},
      {"boxes": [{"t": "layer 3  ·  npm packages"}],
       "note": "read-only, and SHARED by every container built from this image"},
      {"boxes": [{"t": "layer 2  ·  Node 18 runtime"}]},
      {"boxes": [{"t": "layer 1  ·  Alpine Linux files", "s": "alt"}]},
  ]},
  "footnote": "Ten containers from one image share the read-only layers, stored once. Starting one copies nothing — it just adds a new top layer. And when it dies, that top layer dies with it."},

 {"title": "Consequences, and three myths",
  "lean": False,
  "table": [["Myth", "Reality"],
            ["A container is a lightweight VM", "It is a process. There is no second kernel."],
            ["Containers are automatically secure", "Weaker isolation than a VM. Root inside can be dangerous."],
            ["Docker invented containers", "The kernel features predate it. Docker made them usable."]],
  "col_ratio": [0.38, 0.62],
  "bullets": ["Containers are a Linux thing — on macOS or Windows, Docker quietly runs a small Linux VM for you",
              "Which is exactly why Docker feels slower on a Mac: there is a VM underneath it"],
  "footnote": "So a \"lightweight alternative to VMs\" sometimes runs inside a VM. Say it out loud; it is funny, and it is true."},

# ═════════════════════════════════════════════════════════════════════════════
# PART 2 — Docker
# ═════════════════════════════════════════════════════════════════════════════
 {"type": "section",
  "title": "Part 2 — Docker",
  "subtitle": "The tool that builds and runs containers"},

 {"title": "What is Docker, precisely?",
  "lead": "Docker did not invent containers. It made them usable by ordinary people.",
  "diagram": {"kind": "flow", "labels": ["over a socket", "", "", ""], "ranks": [
      {"boxes": [{"t": "docker CLI", "s": "ink"}], "note": "the command you type"},
      {"boxes": [{"t": "dockerd"}], "note": "background service, does the real work"},
      {"boxes": [{"t": "containerd"}], "note": "manages the container lifecycle"},
      {"boxes": [{"t": "runc"}], "note": "actually talks to the kernel"},
      {"boxes": [{"t": "Linux kernel", "sub": "namespaces + cgroups", "s": "alt"}]},
  ]},
  "footnote": "You only ever touch the top box. The lower three follow the OCI standard — which is why Podman, containerd and Kubernetes can all run the same images.",
  "notes": "Someone always asks 'is Docker dead?' — Kubernetes stopped using dockerd internally in 2022. You still build Docker images. The image format is a standard."},

 {"type": "gag", "emoji": "🐳", "lean": False,
  "title": "Why is it a whale?",
  "punchline": "Because it carries containers. That is the whole joke.\nThe branding meeting finished early that day."},

 {"title": "The two words people mix up forever",
  "table": [["Image", "Container"],
            ["A file. Sits on disk doing nothing.", "A running process."],
            ["Read-only, frozen. Built once.", "Has live state, memory, logs."],
            ["Like a class in your code.", "Like an object created from that class."],
            ["Like a recipe.", "Like the meal you cooked from it."],
            ["`nsu-guestbook:v1`", "the thing listed by `docker ps`"]],
  "footnote": "One image can produce a thousand identical containers. That single fact is the entire scaling story later.",
  "notes": "If they remember one table from the whole session, make it this one."},

 {"title": "Registries — build once, run anywhere", "lean": False,
  "diagram": {"kind": "flow", "dir": "right", "labels": ["push", "pull"], "ranks": [
      {"boxes": [{"t": "YOUR LAPTOP", "sub": "docker build"}]},
      {"boxes": [{"t": "REGISTRY", "sub": "Docker Hub · GHCR · ECR", "s": "ink"}]},
      {"boxes": [{"t": "ANY MACHINE", "sub": "docker run"}]},
  ]},
  "code": "  docker.io / library / postgres : 16-alpine\n"
          "  ---------   -------   --------   ----------\n"
          "  registry    namespace repository tag",
  "footnote": "A tag is a movable nickname; a digest (sha256:…) is permanent. `latest` is NOT the newest version — it is just the default tag name, and deploying it means you cannot say what is in production."},

 {"title": "The Dockerfile, and the one habit that matters",
  "lead": "A recipe. Each instruction becomes a cached layer.",
  "code": "FROM node:18-alpine          # base image                  <- cached\n"
          "WORKDIR /app                 # cd, inside the image        <- cached\n"
          "\n"
          "COPY package.json ./         # ONLY the dependency list    <- cached\n"
          "RUN npm install --omit=dev   # the slow one, 60 seconds    <- cached\n"
          "\n"
          "COPY . .                     # now the source          <- REBUILDS\n"
          "\n"
          "EXPOSE 3000                  # documents the port\n"
          "USER node                    # do not run as root. free win.\n"
          'CMD ["node", "server.js"]    # what runs WHEN IT STARTS',
  "footnote": "Copy package.json and install BEFORE the source, or every code change reinstalls every dependency. Once one layer is invalidated, everything after it rebuilds too.",
  "notes": "RUN happens once, at build time. CMD happens every time a container starts. That distinction trips up everyone."},

 {"type": "gag", "emoji": "⏱️", "lean": False,
  "title": "3 seconds versus 3 minutes",
  "punchline": "Times forty rebuilds a day. Times the rest of your career.\nThis is the highest-paid two-line reordering you will ever do."},

 {"title": "The life of a container", "lean": False,
  "lead": "A container lives exactly as long as its main process.",
  "diagram": {"kind": "flow", "dir": "right",
    "labels": ["docker start", "docker stop", "docker rm"], "ranks": [
      {"boxes": [{"t": "CREATED", "sub": "docker create"}]},
      {"boxes": [{"t": "RUNNING", "sub": "your process is alive", "s": "ink"}]},
      {"boxes": [{"t": "STOPPED / EXITED", "sub": "logs still readable", "s": "alt"}]},
      {"boxes": [{"t": "REMOVED", "sub": "gone for good"}]},
  ]},
  "footnote": "\"My container exits immediately\" almost always means the program finished. A container is not a machine you log into — it is a process you wrapped."},

 {"title": "Ports — how the outside gets in",
  "diagram": {"kind": "flow", "dir": "right", "ranks": [
      {"boxes": [{"t": "BROWSER", "sub": "localhost:8080"}]},
      {"boxes": [{"t": "YOUR MACHINE", "sub": "port 8080 published", "s": "sage"}]},
      {"boxes": [{"t": "CONTAINER", "sub": "port 3000", "s": "ink"}]},
      {"boxes": [{"t": "YOUR APP", "sub": "listening"}]},
  ]},
  "code": "  docker run -p 8080:3000 myapp\n"
          "               ----  ----\n"
          "                 |      +-- port INSIDE the container\n"
          "                 +--------- port on YOUR machine",
  "footnote": "EXPOSE in the Dockerfile only documents intent — `-p` is what actually opens the door. \"It runs but I cannot open it in the browser\" is nearly always a missing -p."},

 {"title": "The networking mistake everyone makes",
  "lead": "Inside a container, `localhost` means THAT CONTAINER. Not your laptop.",
  "code": "DB_HOST=localhost   # wrong inside a container -- it means itself\n"
          "DB_HOST=db          # right -- the NAME of the other container",
  "bullets": ["Each container gets its own network namespace and its own IP address",
              "Two containers on the same user-defined network reach each other by NAME",
              "Docker runs a small DNS server that resolves those names to IPs"],
  "footnote": "We will hit this live in Checkpoint 2, on purpose. Learn the shape of the error: ECONNREFUSED 127.0.0.1:5432",
  "notes": "Ask the room WHY before you explain. Somebody will get it, and that moment beats the slide."},

 {"type": "gag", "emoji": "↩️", "lean": False,
  "title": "Calling “localhost” from inside a container",
  "punchline": "“Hello, database?”\n“No. This is you. You called yourself. Nobody else lives here.”"},

 {"title": "Storage, and the idea everything rests on",
  "lead": "Nothing written inside a container survives the container.",
  "table": [["Stateless", "Stateful"],
            ["Keeps nothing important in itself", "Owns data that must survive"],
            ["Any copy can serve any request", "Copies are not interchangeable"],
            ["Kill it, restart it, nothing is lost", "Kill it carelessly and you lose data"],
            ["Trivial to run ten of", "Hard to run more than one correctly"],
            ["Your API, web server, worker", "Postgres, MySQL, Redis, file storage"]],
  "bullets": ["A volume is storage Docker manages OUTSIDE the container — use it for real data",
              "A bind mount maps a folder from your machine in — use it to live-edit code"],
  "footnote": "Containers are cattle, volumes are pets. Docker and Kubernetes are brilliant at stateless things and merely adequate at stateful ones.",
  "notes": "This slide explains, in advance, why scaling the API to 5 replicas later is easy and why we never scale Postgres."},

 {"type": "gag", "emoji": "🗑️", "lean": False,
  "title": "docker compose down -v",
  "punchline": "The -v stands for volumes.\nIt also stands for several other words you will say immediately afterwards."},

 {"title": "Docker Compose — several containers, one command",
  "lead": "Real apps are more than one container. Typing `docker run` for each is not a plan.",
  "code": "services:\n"
          "  db:\n"
          "    image: postgres:16-alpine\n"
          "    volumes: [ db_data:/var/lib/postgresql/data ]\n"
          "    healthcheck:\n"
          '      test: ["CMD-SHELL", "pg_isready -U nsu -d nsu_demo"]\n'
          "  api:\n"
          "    build: .\n"
          '    ports: [ "8080:3000" ]\n'
          "    environment: { DB_HOST: db }    # <- the service NAME, not an IP\n"
          "    depends_on: { db: { condition: service_healthy } }\n"
          "volumes: { db_data: }",
  "footnote": "Compose puts every service on one network and gives each a DNS name equal to its service name. Hold on to that — Kubernetes Services work the same way, for the same reason."},

 {"title": "Where Docker stops",
  "lead": "You launch tonight. Real users. What does Docker not do for you?",
  "bullets": ["It runs on ONE machine — getting to two is entirely your problem",
              "Your app crashes at 3 a.m. and nothing restarts it",
              "Deploying a new version means stopping the old one: downtime",
              "A container that hangs without exiting keeps receiving traffic",
              "No rollback button when the new version turns out to be broken",
              "No way to spread containers across machines by available capacity"],
  "footnote": "Docker BUILDS and RUNS containers. It does not OPERATE them. That gap has a name: orchestration.",
  "notes": "This is the hinge of the session. Do not rush it — every Kubernetes feature answers one of these bullets."},

 {"type": "gag", "emoji": "🌙", "lean": False,
  "title": "3:00 AM. Your app just crashed.",
  "punchline": "Docker's plan for this moment: none.\nDocker is also asleep. Docker has no idea anything happened."},

# ═════════════════════════════════════════════════════════════════════════════
# PART 3 — Kubernetes
# ═════════════════════════════════════════════════════════════════════════════
 {"type": "section",
  "title": "Part 3 — Kubernetes",
  "subtitle": "Operating containers, across many machines, without you watching"},

 {"title": "What Kubernetes is, and what it is not",
  "lead": "40 containers, 6 machines. Somebody must decide what runs where — and fix it when it breaks.",
  "table": [["It IS", "It is NOT"],
            ["A system that keeps containers running", "A thing that writes or builds your app"],
            ["A scheduler that places them on machines", "A replacement for Docker images"],
            ["A self-healing controller", "Automatic — you still describe what you want"],
            ["A stable naming and load-balancing layer", "Simple — the learning curve is real"],
            ["Portable across clouds and on-premises", "Necessary for most small projects"]],
  "footnote": "Google ran containers internally for a decade on a system called Borg; Kubernetes is the 2014 open-source redesign of those ideas. Greek for \"helmsman\" — hence the ship's wheel. \"K8s\" is K, eight letters, s."},

 {"title": "The one idea: declare, do not command",
  "code": "  IMPERATIVE  (Docker)        \"start a container\"\n"
          "                              You said WHAT TO DO, once.\n"
          "                              If it dies later, that is your problem.\n"
          "\n"
          "  DECLARATIVE (Kubernetes)    \"I want 3 healthy copies of this image\"\n"
          "                              You said WHAT SHOULD BE TRUE, always.\n"
          "                              Something works continuously to keep it true.",
  "footnote": "You stop giving orders and start describing the desired end state. Everything else in this session follows from that one shift.",
  "notes": "The analogy that lands: a thermostat. You do not switch the heater on and off all night. You say 22 degrees, and it works out the rest."},

 {"title": "How that works: the control loop",
  "diagram": {"kind": "cycle", "centre": "forever,\nevery few seconds", "nodes": [
      {"t": "OBSERVE", "sub": "what is actually running?"},
      {"t": "COMPARE", "sub": "against what you asked for", "s": "sage"},
      {"t": "ACT", "sub": "create · delete · restart", "s": "ink"},
      {"t": "REPEAT", "sub": "nothing is ever 'done'"},
  ]},
  "footnote": "A \"controller\" is just a program running this loop for one kind of object. Desired: 3 pods. Actual: 2. Action: create 1. Loop again. That is reconciliation, and it is all of Kubernetes."},

 {"type": "gag", "emoji": "🌡️",
  "title": "Kubernetes is a thermostat",
  "punchline": "You do not switch the heater on and off all night.\nYou say “22 degrees”, and it argues with reality on your behalf, forever."},

 {"title": "What a cluster is made of",
  "diagram": {"kind": "flow", "ranks": [
      {"boxes": [{"t": "CONTROL PLANE  —  the brain", "s": "ink"}]},
      {"boxes": [{"t": "API server", "sub": "front door"},
                 {"t": "scheduler", "sub": "placement"},
                 {"t": "controllers", "sub": "the loops"},
                 {"t": "etcd", "sub": "the memory", "s": "alt"}]},
      {"boxes": [{"t": "NODE 1", "sub": "kubelet · kube-proxy · pods", "s": "sage"},
                 {"t": "NODE 2", "sub": "kubelet · kube-proxy · pods", "s": "sage"},
                 {"t": "NODE 3", "sub": "kubelet · kube-proxy · pods", "s": "sage"}]},
  ]},
  "footnote": "A node is just a machine that has agreed to run pods. `kubectl` talks only to the API server; the scheduler picks nodes; `kubelet` starts the containers; etcd remembers everything.",
  "notes": "If etcd is lost, the cluster's memory is lost — which is why production clusters run three or five copies of it."},

 {"title": "Everything is an object, and they all look the same",
  "code": "apiVersion: apps/v1      # which API group and version\n"
          "kind: Deployment         # WHAT TYPE of object this is\n"
          "metadata:\n"
          "  name: api              # its name\n"
          "  namespace: nsu-demo    # which folder it lives in\n"
          "spec:                    # WHAT YOU WANT   <- you write this\n"
          "  replicas: 3\n"
          "status:                  # WHAT IS TRUE    <- Kubernetes writes this\n"
          "  readyReplicas: 3",
  "bullets": ["Namespace = a folder · Pod = the smallest running unit · Deployment = keeps N pods alive",
              "Service = a stable name in front of pods · ConfigMap and Secret = config · PVC = disk",
              "StatefulSet (databases) · DaemonSet (one per node) · Job and CronJob (batch work)"],
  "footnote": "spec is your wish, status is reality, and a controller's whole job is dragging status towards spec."},

 {"title": "Why you never write a Pod by hand",
  "lead": "Create a bare pod, delete it, and it is simply gone. Nothing brings it back.",
  "diagram": {"kind": "flow", "labels": ["creates and manages", "creates and manages", ""],
    "ranks": [
      {"boxes": [{"t": "Deployment", "s": "ink"}],
       "note": "\"3 copies, and update them safely\" — the only part you write"},
      {"boxes": [{"t": "ReplicaSet", "s": "sage"}],
       "note": "\"there must be exactly 3 pods with this label\""},
      {"boxes": [{"t": "Pod"}, {"t": "Pod"}, {"t": "Pod"}],
       "note": "one or more containers sharing an IP and storage"},
      {"boxes": [{"t": "Container", "s": "alt"}, {"t": "Container", "s": "alt"},
                 {"t": "Container", "s": "alt"}],
       "note": "your image, running"},
  ]},
  "footnote": "Pods are mortal: deleted, rescheduled, and the replacement gets a new IP. You write the Deployment; everything below it is created and repaired for you."},

 {"title": "Reading `kubectl get pods`",
  "lean": False,
  "table": [["Status", "What it means"],
            ["Pending", "Accepted, not started — no node fits, or the image is still pulling."],
            ["ContainerCreating", "Node chosen, image pulled, container starting."],
            ["Running", "At least one container is up. Not necessarily ready for traffic."],
            ["CrashLoopBackOff", "It keeps starting and dying. Read the logs — this is your bug."],
            ["ImagePullBackOff", "Cannot fetch the image. Wrong name, wrong tag, or no credentials."],
            ["OOMKilled", "It exceeded its memory limit. Raise the limit, or fix the leak."]],
  "col_ratio": [0.26, 0.74],
  "footnote": "Two statuses cover most beginner pain: CrashLoopBackOff means your app is broken; ImagePullBackOff means your image name is wrong."},

 {"type": "gag", "emoji": "🔁", "lean": False,
  "title": "CrashLoopBackOff",
  "punchline": "Your app starts. Your app dies. Repeat.\nKubernetes waits a little longer between attempts — politely, and forever."},

 {"title": "Labels — how everything is wired together",
  "lead": "Nothing is connected by name or IP. Everything is connected by label.",
  "code": "# The Deployment stamps every pod it creates:\n"
          "template:\n"
          "  metadata:\n"
          "    labels: { app: api }\n"
          "\n"
          "# The ReplicaSet counts pods matching:\n"
          "selector:\n"
          "  matchLabels: { app: api }\n"
          "\n"
          "# The Service sends traffic to pods matching:\n"
          "selector: { app: api }",
  "footnote": "A label is a key=value sticker; a selector is a query over stickers.",
  "notes": "The #1 beginner bug in the entire ecosystem: labels and selector disagree, so the Service has zero endpoints and the page just hangs. Check it with `kubectl get endpoints`."},

 {"title": "Service — why pod IPs are useless",
  "lead": "Pods are replaced constantly, and every replacement has a different IP.",
  "diagram": {"kind": "flow", "ranks": [
      {"boxes": [{"t": "everything else", "sub": "connects to the name \"api\""}]},
      {"boxes": [{"t": "Service  \"api\"", "sub": "one name · one stable IP", "s": "ink"}],
       "note": "never changes"},
      {"boxes": [{"t": "Pod", "sub": "10.1.3.7"},
                 {"t": "Pod", "sub": "10.1.6.4  (was 10.1.5.2)", "s": "alt"},
                 {"t": "Pod", "sub": "10.1.2.8  (was 10.1.4.9)", "s": "alt"}],
       "note": "replaced constantly, new IP every time"},
  ]},
  "footnote": "ClusterIP (internal only, the default) · NodePort (a fixed port on every node, fine for demos) · LoadBalancer (asks the cloud for a real one). Inside the cluster it is simply the hostname `api`."},

 {"title": "Ingress — one entrance for many services", "lean": False,
  "diagram": {"kind": "flow", "labels": ["", "by hostname / path"], "ranks": [
      {"boxes": [{"t": "INTERNET", "s": "alt"}]},
      {"boxes": [{"t": "Ingress", "sub": "TLS termination + routing", "s": "ink"}],
       "note": "one entry point for the whole cluster"},
      {"boxes": [{"t": "Service", "sub": "api.nsu.edu"},
                 {"t": "Service", "sub": "www.nsu.edu"}]},
  ]},
  "footnote": "Without it, every public service needs its own cloud load balancer. We are not deploying one today — but every real cluster has one, and it needs a controller installed (nginx, Traefik, or the cloud's)."},

 {"title": "ConfigMap and Secret — config outside the image",
  "lead": "The same image must run in dev, staging and production. Only the values change.",
  "code": "kind: ConfigMap          # boring config\n"
          "data: { DB_HOST: postgres, DB_NAME: nsu_demo }\n"
          "---\n"
          "kind: Secret             # config that would get you fired\n"
          "stringData: { DB_PASSWORD: nsu_password }\n"
          "\n"
          "$ kubectl get secret db-secret -o jsonpath='{.data.DB_PASSWORD}' | base64 -d\n"
          "nsu_password",
  "footnote": "A Secret is base64-encoded, NOT encrypted. The real protections are RBAC and encryption-at-rest in etcd. The genuine win here is separation: the credential is not baked into the image.",
  "notes": "Run the base64 -d command live. Five seconds, remembered for years. Plenty of professionals believe Secrets are encrypted."},

 {"type": "gag", "emoji": "🔓",
  "title": "“It’s a Secret, so it’s encrypted”",
  "punchline": "base64 is not encryption. base64 is a hat.\nA very small hat, on a very recognisable password."},

 {"title": "Storage in Kubernetes", "lean": False,
  "diagram": {"kind": "flow",
    "labels": ["matched or provisioned automatically", "created on demand from a"],
    "ranks": [
      {"boxes": [{"t": "PersistentVolumeClaim", "s": "ink"}],
       "note": "\"I need 1 GB that survives my pod\" — the only part you write"},
      {"boxes": [{"t": "PersistentVolume"}],
       "note": "an actual disk: cloud volume, NFS, local path"},
      {"boxes": [{"t": "StorageClass", "s": "alt"}],
       "note": "\"fast SSD\", \"cheap HDD\" — the menu of options"},
  ]},
  "footnote": "Your pod asks for storage; it never names a specific disk. Same lesson as Docker volumes: data must live outside the thing that keeps being replaced."},

 {"title": "Probes — how the cluster knows your app is healthy",
  "lead": "\"The process is running\" and \"the app works\" are not the same statement.",
  "table": [["Probe", "Question", "If it fails"],
            ["liveness", "Are you alive?", "Restart the container"],
            ["readiness", "Ready for traffic?", "Remove from the Service — do not restart"],
            ["startup", "Finished booting?", "Hold the other probes off a while longer"]],
  "col_ratio": [0.18, 0.32, 0.5],
  "code": "readinessProbe:\n"
          "  httpGet: { path: /healthz, port: 3000 }\n"
          "  periodSeconds: 5",
  "footnote": "Readiness is what makes zero-downtime deployment possible: a new pod receives traffic only once it says it is ready."},

 {"title": "The three tricks that justify all of this",
  "table": [["Trick", "What you do", "What Kubernetes does"],
            ["Scale", "`kubectl scale --replicas=5`", "The ReplicaSet sees 3 of 5 and creates 2. The Service picks them up automatically — you configured no load balancer."],
            ["Self-heal", "Nothing. Something breaks.", "Container crashes → restarted. Pod deleted → recreated. Node dies → rescheduled elsewhere."],
            ["Rolling update", "Change the image or an env var", "New pod up → passes readiness → THEN an old one goes. `maxUnavailable: 0` means no downtime."]],
  "col_ratio": [0.15, 0.27, 0.58],
  "footnote": "Regret it? `kubectl rollout undo`. Each change created a new ReplicaSet and kept the old ones at zero — so rolling back is just scaling one of them back up.",
  "notes": "Tie scaling back to the stateless/stateful slide: this only works because the API is stateless. Try it on Postgres and you corrupt data."},

 {"type": "gag", "emoji": "♻️",
  "title": "You deleted the pod. The pod came back.",
  "punchline": "You deleted it again. It came back again.\nYou are not in charge here. The Deployment is in charge here."},

 {"title": "When NOT to use Kubernetes",
  "lead": "The most useful slide in this deck, and the one most sessions leave out.",
  "bullets": ["A student project or a portfolio site — a single container is plenty",
              "One small app with modest traffic — a VM plus Docker Compose is fine",
              "Nobody on the team who can debug it at 3 a.m.",
              "You want a database — use managed Postgres unless you have a real reason",
              "A cluster you did not need still needs upgrading, securing and paying for"],
  "footnote": "Kubernetes solves problems of scale. Adopt it when you have those problems, not because it appears on job descriptions."},

 {"type": "gag", "emoji": "🏗️", "lean": False,
  "title": "A nine-node cluster for your portfolio site",
  "punchline": "Congratulations! You now have a highly available,\nauto-scaling, self-healing platform. And one visitor. Your mother."},

# ═════════════════════════════════════════════════════════════════════════════
# PART 4 — Seeing it work
# ═════════════════════════════════════════════════════════════════════════════
 {"type": "section",
  "title": "Part 4 — Seeing it work",
  "subtitle": "Five checkpoints · run them with me, or later from the repo"},

 {"title": "Checkpoint 1 — run it with no Docker at all",
  "lead": "A guestbook: Express + Postgres, ~120 lines. Every page prints who served it.",
  "code": "cd checkpoints/01-plain-node\n"
          "node --version               # must be 18 or newer\n"
          "npm install\n"
          "sudo apt-get install -y postgresql\n"
          "sudo -u postgres psql -c \"CREATE USER nsu WITH PASSWORD 'nsu_password';\"\n"
          "sudo -u postgres psql -c \"CREATE DATABASE nsu_demo OWNER nsu;\"\n"
          "export DB_HOST=localhost DB_USER=nsu DB_PASSWORD=nsu_password DB_NAME=nsu_demo\n"
          "npm start",
  "footnote": "Count the ways this fails: wrong Node, failed install, no Postgres, wrong password, port in use, wrong OS. Eight failure modes, for 120 lines of code.",
  "notes": "The hostname line — os.hostname() — is the trick of the session. In Docker it prints a container ID; in Kubernetes, a pod name. If the Postgres install is slow, narrate it instead; the struggle IS the content."},

 {"title": "Checkpoint 2 — build an image, run a container",
  "code": "cd checkpoints/02-docker-single\n"
          "docker build -t nsu-guestbook:v1 .     # build twice: the second is instant\n"
          "docker run --rm -p 8080:3000 nsu-guestbook:v1\n"
          "\n"
          "[db] not ready: connect ECONNREFUSED 127.0.0.1:5432    <- expected!\n"
          "\n"
          "docker exec -it gb sh                  # look around inside\n"
          "  cat /etc/os-release                  # Alpine... on your Ubuntu laptop\n"
          "  whoami                               # node, not root",
  "footnote": "It fails on purpose. `localhost` inside the container IS the container — the networking slide, made real.",
  "notes": "Ask the room WHY it failed before you explain it."},

 {"title": "Checkpoint 3 — two containers, one command",
  "code": "cd checkpoints/03-compose-db\n"
          "docker compose up --build      # -> http://localhost:8080\n"
          "\n"
          "# the volume lesson -- do this live:\n"
          "docker compose down            # containers destroyed\n"
          "docker compose up -d           # brand new containers\n"
          "#   refresh: your guestbook entries are STILL THERE\n"
          "docker compose down -v         # -v also deletes the volume\n"
          "#   refresh: now they are gone",
  "footnote": "The app finally works, on any machine, with one command. And the data outlives the container that wrote it."},

 {"title": "Checkpoint 4 — the same image on a cluster",
  "code": "kind create cluster --config kind-config.yaml   # Kubernetes IN Docker\n"
          "kubectl get nodes                              # 1 control-plane, 2 workers\n"
          "docker ps                                      # the nodes ARE containers\n"
          "\n"
          "kind load docker-image nsu-guestbook:v1 --name nsu   # its own image store\n"
          "kubectl apply -f k8s/\n"
          "kubectl get all -n nsu-demo",
  "footnote": "Identical image. Namespace, Deployment, Service — the objects from Part 3, now real. Skip the `kind load` line and you get ImagePullBackOff, which is worth demoing on purpose.",
  "notes": "CREATE THE CLUSTER BEFORE THE SESSION. It takes 1-3 minutes on good wifi and much longer on bad wifi."},

 {"title": "Checkpoint 5 — scale, heal, ship",
  "code": "# 1. SCALE -- then refresh the browser and watch \"Served by\" change\n"
          "kubectl scale deploy/api --replicas=5 -n nsu-demo\n"
          "\n"
          "# 2. SELF-HEAL -- kill them all; replacements appear in seconds\n"
          "kubectl delete pods -n nsu-demo -l app=api\n"
          "\n"
          "# 3. ROLLING UPDATE -- refresh throughout; it never errors\n"
          "kubectl set env deploy/api APP_VERSION=v2 -n nsu-demo\n"
          "kubectl rollout undo deploy/api -n nsu-demo",
  "footnote": "Three commands. Everything Part 3 promised, visible in ninety seconds. Keep localhost:8080 on the projector throughout.",
  "notes": "The 'Served by' hostname changing as you refresh is the single best demo in the session. Let it run."},

# ═════════════════════════════════════════════════════════════════════════════
# Wrap-up
# ═════════════════════════════════════════════════════════════════════════════
 {"title": "The entire session on one slide",
  "diagram": {"kind": "flow",
    "labels": ["Dockerfile", "push / pull", "\"3 healthy copies\"", "", ""],
    "ranks": [
      {"boxes": [{"t": "your code + its environment"}]},
      {"boxes": [{"t": "IMAGE", "s": "ink"}]},
      {"boxes": [{"t": "REGISTRY", "s": "alt"}]},
      {"boxes": [{"t": "Deployment  →  ReplicaSet", "s": "sage"}]},
      {"boxes": [{"t": "Pod"}, {"t": "Pod"}, {"t": "Pod"}]},
      {"boxes": [{"t": "Service \"api\"  →  users", "s": "ink"}]},
  ]},
  "footnote": "One image. Many identical pods. One stable name. A controller that never stops checking."},

 {"title": "Compose and Kubernetes are the same ideas, renamed",
  "table": [["Docker Compose", "Kubernetes"],
            ["service", "Deployment + Service"],
            ["docker compose up", "kubectl apply -f"],
            ["container", "Pod (which contains containers)"],
            ["service name as hostname", "Service name as hostname"],
            ["named volume", "PersistentVolumeClaim"],
            ["environment:", "ConfigMap and Secret"],
            ["healthcheck:", "liveness and readiness probes"],
            ["(not available)", "replicas, self-healing, rolling updates, scheduling"]],
  "footnote": "You already understood most of Kubernetes by the end of Part 2. It just used different words."},

 {"title": "Glossary — the Docker half", "lean": False,
  "table": [["Term", "One line"],
            ["Image", "A read-only package of an app and everything it needs."],
            ["Container", "A running instance of an image; an isolated process."],
            ["Layer", "One cached step of an image build."],
            ["Dockerfile", "The recipe used to build an image."],
            ["Registry", "A server that stores and serves images."],
            ["Tag", "A movable nickname for a version of an image."],
            ["Volume", "Storage that outlives the container."],
            ["Bind mount", "A folder from your machine, mapped into a container."],
            ["Compose", "A file and a command for running several containers together."]],
  "col_ratio": [0.2, 0.8],
  "bullet_size": 1250},

 {"title": "Glossary — the Kubernetes half", "lean": False,
  "table": [["Term", "One line"],
            ["Cluster / Node", "Machines managed together as one pool / one machine in it."],
            ["Control plane", "The brain: API server, etcd, scheduler, controllers."],
            ["Pod", "The smallest deployable unit; wraps containers."],
            ["Deployment", "Keeps N pods alive and updates them safely."],
            ["ReplicaSet", "Counts pods, creating or deleting to hit the number."],
            ["Service", "A stable name and IP in front of changing pods."],
            ["Label / selector", "Sticker and query — how objects find each other."],
            ["ConfigMap / Secret", "Configuration and credentials injected at runtime."],
            ["PVC", "A request for storage that outlives the pod."],
            ["Namespace", "A folder separating groups of objects."]],
  "col_ratio": [0.2, 0.8],
  "bullet_size": 1250},

 {"title": "If you remember only five things",
  "bullets": ["An app is code PLUS its environment — that is why shipping code alone fails",
              "A container is a normal process the kernel has isolated. Not a small VM",
              "An image is the frozen recipe; a container is a running instance of it",
              "Kubernetes compares desired state with actual state, forever",
              "Anything you care about keeping must live OUTSIDE the container"],
  "footnote": "Next: containerise one project of your own this week — that is the whole homework. Then kubernetes.io/docs/tutorials/kubernetes-basics, then Ingress, then Helm. Learn `kubectl describe` before anything else.",
  "notes": "The Events section at the bottom of `kubectl describe pod` answers nine out of ten 'why will it not start' questions. Say so explicitly."},

 {"type": "gag", "emoji": "🎓", "lean": False,
  "title": "That is genuinely all of it",
  "punchline": "Everything else is detail, documentation, and YAML.\nMostly YAML."},

 {"type": "section",
  "title": "Questions?",
  "subtitle": "Slides, checkpoints and a cheat sheet are all in the repo — thank you"},
]


# Small icons beside the text on ordinary slides, purely as a visual anchor.
# Skipped automatically on slides carrying a diagram, code block or table,
# which need the full width.
EMOJI = {
 "The oldest sentence in software": "🧩",
 "So what IS a container?": "🪞",
 "Consequences, and three myths": "🐧",
 "Where Docker stops": "🛑",
 "When NOT to use Kubernetes": "🚫",
 "If you remember only five things": "⭐",
}


def _weave(slides):
    unknown = set(EMOJI) - {s.get("title") for s in slides}
    assert not unknown, f"EMOJI keys match no slide: {sorted(unknown)}"
    out = []
    for s in slides:
        title = s.get("title")
        if title in EMOJI and not (s.get("code") or s.get("table")
                                   or s.get("diagram")):
            s = dict(s, emoji=EMOJI[title])
        out.append(s)
    return out


SLIDES = _weave(SLIDES)

# Checkpoint 2 — Your first image and container (≈12 min)

**Goal:** build an image, run a container, and prove it is isolated.
The app will *fail* to reach a database here. That failure is scheduled.

## Build

```bash
cd checkpoints/02-docker-single

docker build -t nsu-guestbook:v1 .
```

`-t` names the image `nsu-guestbook` and tags it `v1`; the `.` is the folder Docker
reads the `Dockerfile` and source from.

Run it a second time — the whole thing is cached, near-instant. Now edit one
character in `server.js` and rebuild: only the last layers rerun. That is the
`COPY package.json` trick from the Dockerfile paying off.

```bash
docker images | head            # your image is in the local library
docker history nsu-guestbook:v1 # the layers, largest first
```

## Run

```bash
docker run --rm -p 8080:3000 nsu-guestbook:v1
```

Watch the logs (the text the app prints as it runs): `[db] not ready (attempt 1/20)`.
The page will not open at all — the app refuses to start until it can reach a database.
**Ask the room why.**

Answer: the container has its own network namespace. `localhost` inside the
container means *the container itself*, not your laptop. There is no Postgres in
there. One container = one process = one job.

Stop it with `Ctrl-C`, then in a second terminal explore a running container:

```bash
docker run -d --name gb -p 8080:3000 nsu-guestbook:v1

docker ps                       # what is running
docker logs -f gb               # stream logs
docker exec -it gb sh           # get a shell INSIDE the container
  # try: ls, whoami, cat /etc/os-release, node --version, exit
docker stop gb && docker rm gb  # containers are disposable
```

`cat /etc/os-release` inside the container says **Alpine Linux** even though your
laptop is Ubuntu. That is the demo that lands. Same kernel, different userland.

## Port mapping, out loud

```
-p 8080:3000
   ↑     ↑
   |     port INSIDE the container (what the app listens on)
   port on YOUR machine (what your browser hits)
```

## Vocabulary check before moving on

| Term | Meaning |
|---|---|
| Image | The frozen recipe result. Read-only. Like a class. |
| Container | A running instance of an image. Like an object. |
| Layer | One cached step of the build. |
| Registry | Where images live (Docker Hub, GHCR). |

Next: the app needs a database, so we need a second container.

---

← [Back: Run it the old way](../01-plain-node/)  ·  **[Next: Two containers that talk →](../03-compose-db/)**  ·  Stuck? The [cheat sheet](../../CHEATSHEET.md) has a *When it breaks* table.

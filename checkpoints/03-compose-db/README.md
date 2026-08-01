# Checkpoint 3 — Two containers that talk (≈12 min)

**Goal:** the app finally works, end to end, on any machine, with one command.

## The hard way first (show, do not make them type it)

Two containers cannot see each other by default. By hand you would need:

```bash
docker network create nsu-net
docker run -d --name db --network nsu-net \
  -e POSTGRES_USER=nsu -e POSTGRES_PASSWORD=nsu_password -e POSTGRES_DB=nsu_demo \
  postgres:16-alpine
docker run -d --name api --network nsu-net -p 8080:3000 \
  -e DB_HOST=db -e DB_USER=nsu -e DB_PASSWORD=nsu_password -e DB_NAME=nsu_demo \
  nsu-guestbook:v1
```

Six lines you must retype in the right order, every time, forever. Nobody does this.

## The real way

```bash
cd checkpoints/03-compose-db

docker compose up --build
```

Open <http://localhost:8080>, sign the guestbook a few times.

```bash
docker compose ps        # both services
docker compose logs -f api
docker compose down      # stop and delete containers
```

## The volume lesson — do this live, it is the best 60 seconds of the Docker half

```bash
docker compose up -d
# add two names in the browser

docker compose down            # containers are GONE
docker compose up -d           # brand new containers
# refresh the browser -- your names are still there
```

The container was destroyed. The data was not, because it lived in the `db_data`
volume, not in the container's writable layer.

Now delete the volume too and watch the data vanish for real:

```bash
docker compose down -v
docker compose up -d           # empty guestbook
```

**Rule to remember: containers are cattle, volumes are pets.**

## Where Docker runs out of road

Ask the room: "we are going live tonight, 50,000 users. What breaks?"

- One laptop. One machine. What happens when it needs to be two?
- `docker compose up` on a server — who restarts it when the process crashes at 3am?
- Deploy a new version = downtime while it rebuilds.
- No health-based routing, no autoscaling, no rollback button.
- The DB password is sitting in a YAML file in git.

Every one of those is a bullet on the Kubernetes feature list. That is the bridge.
